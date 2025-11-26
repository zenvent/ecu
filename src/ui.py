import tkinter as tk
from tkinter import ttk
import tkinter.scrolledtext as scrolledtext
import winreg
import ctypes

THEMES = {
    'dark': {
        'bg': '#1e1e1e', 'fg': '#d4d4d4',
        'input_bg': '#252526', 'input_fg': '#cccccc',
        'select_bg': '#094771', 'select_fg': '#ffffff',
        'tree_bg': '#252526', 'tree_fg': '#d4d4d4',
        'btn_bg': '#333333', 'btn_fg': '#ffffff',
        'border': '#454545', # Dark Grey
        'highlight': '#f1c40f', # Yellowish
        'info_fg': '#569cd6', # VS Code Blue (Lighter)
        'warning_fg': '#cca700', # Darker Yellow/Orange
        'error_fg': '#f48771' # VS Code Red (Lighter)
    },
    'light': {
        'bg': '#f3f3f3', 'fg': '#000000',
        'input_bg': '#ffffff', 'input_fg': '#000000',
        'select_bg': '#0078d7', 'select_fg': '#ffffff',
        'tree_bg': '#ffffff', 'tree_fg': '#000000',
        'btn_bg': '#e1e1e1', 'btn_fg': '#000000',
        'border': '#cccccc',
        'highlight': '#ffff00',
        'info_fg': '#0000ff', # Standard Blue
        'warning_fg': '#806000', # Dark Yellow
        'error_fg': '#cd3131' # VS Code Red
    }
}

class ScriptManagerUI:
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        self.root.title("Script Manager")
        
        # Calculate 80% of screen size and center the window
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)
        x_position = int((screen_width - window_width) / 2)
        y_position = int((screen_height - window_height) / 2)
        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

        # Main Container
        self.main_container = tk.Frame(root)
        self.main_container.pack(fill='both', expand=True)
        
        # Theme Toggle (Top Right)
        self.current_theme = self._get_system_theme()
        theme_icon = "☀" if self.current_theme == 'dark' else "🌙"
        self.theme_button = tk.Button(self.main_container, text=theme_icon, command=self._toggle_theme, bd=0, padx=10, pady=5)
        self.theme_button.place(relx=1.0, x=-10, y=10, anchor='ne')
        
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=40) # Add top padding for theme button

        # Tabs
        self.scripts_tab = ttk.Frame(self.notebook)
        self.actuators_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.scripts_tab, text='Scripts')
        self.notebook.add(self.actuators_tab, text='Actuators')

        self._setup_scripts_tab()
        self._setup_actuators_tab()

        # Apply Theme - Call this LAST so all widgets exist
        self.colors = THEMES[self.current_theme]
        # Delay application slightly to ensure window handle is ready for DWM
        self.root.after(10, self._apply_theme)

    def _setup_scripts_tab(self):
        # Layout: Top (Table), Bottom (Terminal)
        paned_window = ttk.PanedWindow(self.scripts_tab, orient=tk.VERTICAL)
        paned_window.pack(expand=True, fill='both', padx=5, pady=5)

        # Top Frame (Script Table)
        top_frame = ttk.Frame(paned_window)
        paned_window.add(top_frame, weight=1) # Will adjust sash later

        # Script Table with Scrollbar
        table_frame = ttk.Frame(top_frame)
        table_frame.pack(expand=True, fill='both')
        
        columns = ('name', 'description')
        self.script_tree = ttk.Treeview(table_frame, columns=columns, show='headings')
        self.script_tree.heading('name', text='Script Name')
        self.script_tree.heading('description', text='Description')
        self.script_tree.column('name', width=200)
        self.script_tree.column('description', width=400)
        
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.script_tree.yview)
        self.script_tree.configure(yscrollcommand=scrollbar.set)
        
        self.script_tree.pack(side='left', expand=True, fill='both')
        scrollbar.pack(side='right', fill='y')
        
        self.script_tree.bind('<<TreeviewSelect>>', self._on_script_selected)

        # Bottom Frame (Tabs: Console, History)
        bottom_frame = ttk.Frame(paned_window)
        paned_window.add(bottom_frame, weight=3)
        
        self.bottom_notebook = ttk.Notebook(bottom_frame)
        self.bottom_notebook.pack(expand=True, fill='both')
        
        # --- Console Tab ---
        console_tab = ttk.Frame(self.bottom_notebook)
        self.bottom_notebook.add(console_tab, text="Console")

        # Action Bar (Moved to top of console tab)
        action_bar = ttk.Frame(console_tab)
        action_bar.pack(fill='x', pady=5)
        
        self.run_button = ttk.Button(action_bar, text="❯ Run Selected Script", command=self._on_run_clicked, state='disabled')
        self.run_button.pack(side='left', padx=5)

        self.abort_button = ttk.Button(action_bar, text="⏹ Abort Script", command=self._on_abort_clicked, state='disabled')
        # self.abort_button.pack(side='left', padx=5) # Don't pack initially

        

        # Terminal Output (No Gutter)
        terminal_frame = ttk.Frame(console_tab)
        terminal_frame.pack(expand=True, fill='both', padx=5, pady=5)
        
        self.output_text = tk.Text(terminal_frame, borderwidth=0, state='normal', height=10, font=("Consolas", 10))
        output_scrollbar = ttk.Scrollbar(terminal_frame, orient=tk.VERTICAL, command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=output_scrollbar.set)
        
        self.output_text.pack(side='left', expand=True, fill='both')
        output_scrollbar.pack(side='right', fill='y')

        # Search Controls (Right aligned in action_bar)
        # We need to create the search bar AFTER the text widget exists
        search_frame, self.console_search_entry = self._create_search_bar(action_bar, self.output_text)
        search_frame.pack(side='right')

        # Input Field
        self.input_entry = tk.Entry(console_tab, font=("Consolas", 10), borderwidth=0, highlightthickness=0)
        self.input_entry.pack(fill='x', padx=5, pady=(5, 0))
        self.input_entry.bind('<Return>', self._on_input_return)
        self.input_entry.bind('<FocusIn>', self._on_input_focus_in)
        self.input_entry.bind('<FocusOut>', self._on_input_focus_out)
        self.is_flashing = False
        
        # Set placeholder
        self.input_placeholder = "Input..."
        self.input_has_placeholder = True
        self.input_entry.insert(0, self.input_placeholder)
        self.input_entry.config(foreground='gray')
        
        # Configure tags
        self.output_text.tag_config('error', foreground='red')
        self.output_text.tag_config('info', foreground='blue')
        self.output_text.tag_config('placeholder', foreground='gray')
        self.output_text.tag_config('highlight', background='yellow', foreground='black')
        self.output_text.tag_config('current_match', background='orange', foreground='black')

        # --- History Tab ---
        history_tab = ttk.Frame(self.bottom_notebook)
        self.bottom_notebook.add(history_tab, text="History")
        
        history_paned = ttk.PanedWindow(history_tab, orient=tk.HORIZONTAL)
        history_paned.pack(expand=True, fill='both', padx=5, pady=5)
        
        # History List
        history_list_frame = ttk.Frame(history_paned)
        history_paned.add(history_list_frame, weight=1)
        
        self.history_listbox = tk.Listbox(history_list_frame, activestyle='none', borderwidth=0, highlightthickness=0)
        self.history_listbox.pack(side='left', expand=True, fill='both')
        history_scrollbar = ttk.Scrollbar(history_list_frame, orient=tk.VERTICAL, command=self.history_listbox.yview)
        self.history_listbox.configure(yscrollcommand=history_scrollbar.set)
        history_scrollbar.pack(side='right', fill='y')
        
        self.history_listbox.bind('<<ListboxSelect>>', self._on_history_selected)
        
        # History Preview
        history_preview_frame = ttk.Frame(history_paned)
        history_paned.add(history_preview_frame, weight=3)
        
        # History Search Bar
        history_search_frame = ttk.Frame(history_preview_frame)
        history_search_frame.pack(fill='x', pady=(0, 2))
        
        # History Text (with Gutter)
        history_container, self.history_text, self.history_gutter = self._create_text_with_gutter(history_preview_frame)
        history_container.pack(side='left', expand=True, fill='both')
        
        # Create search bar (using history_search_frame as parent)
        # Note: _create_search_bar packs items to the left, so we can just use it directly
        # But we want it right aligned? No, user said "consistent". 
        # In console it's in action bar (right aligned). Here it's a dedicated bar.
        # Let's make it fill the bar but aligned left as per _create_search_bar default.
        # Actually, let's just use the frame returned by _create_search_bar as the content of history_search_frame
        
        search_ui, self.history_search_entry = self._create_search_bar(history_search_frame, self.history_text)
        search_ui.pack(side='right')

        self.history_text.tag_config('highlight', background='yellow', foreground='black')
        self.history_text.tag_config('current_match', background='orange', foreground='black')

        # Initial Placeholder
        self.clear_log() # Sets placeholder

        # Initial Load
        self._refresh_script_list()
        
        # Set Sash Position (approx 25% of 800 height = 200)
        self.root.after(100, lambda: paned_window.sashpos(0, 200))

    def _setup_actuators_tab(self):
        # Layout: Top buttons, Bottom Table
        top_frame = ttk.Frame(self.actuators_tab)
        top_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(top_frame, text="Refresh Actuators", command=self._on_refresh_actuators).pack(side='left')

        # Table
        columns = ('app_name', 'region', 'version', 'branch', 'status')
        self.actuator_tree = ttk.Treeview(self.actuators_tab, columns=columns, show='headings')
        
        self.actuator_tree.heading('app_name', text='App Name')
        self.actuator_tree.heading('region', text='Region')
        self.actuator_tree.heading('version', text='Version')
        self.actuator_tree.heading('branch', text='Branch')
        self.actuator_tree.heading('status', text='Status')

        self.actuator_tree.pack(expand=True, fill='both', padx=5, pady=5)

    def _on_refresh_actuators(self):
        self.controller.refresh_actuators()

    def _on_script_selected(self, event):
        selection = self.script_tree.selection()
        if selection:
            script_name = selection[0]
            self.run_button.config(state='normal')
            
            # Update History Tab
            self._update_history_list(script_name)
        else:
            self.run_button.config(state='disabled')
            self.history_listbox.delete(0, tk.END)
            self._clear_history_preview()

    def _update_history_list(self, script_name):
        self.history_listbox.delete(0, tk.END)
        history = self.controller.get_script_history(script_name)
        for item in history:
            self.history_listbox.insert(tk.END, item)

    def _on_history_selected(self, event):
        selection = self.history_listbox.curselection()
        script_selection = self.script_tree.selection()
        if selection and script_selection:
            filename = self.history_listbox.get(selection[0])
            script_name = script_selection[0]
            content = self.controller.get_log_content(script_name, filename)
            
            self.history_text.config(state='normal')
            self.history_text.delete(1.0, tk.END)
            
            # Insert with tags
            for line in content.splitlines(keepends=True):
                tag = None
                lower_text = line.lower()
                if "error" in lower_text or "exception" in lower_text or "critical" in lower_text:
                    tag = 'error'
                elif "warn" in lower_text:
                    tag = 'warning'
                elif "info" in lower_text:
                    tag = 'info'
                self.history_text.insert(tk.END, line, tag)
            
            self.history_text.config(state='disabled')
            
            # Force update line numbers
            if hasattr(self, 'history_gutter'):
                self._update_line_numbers(self.history_text, self.history_gutter)
                
            # Reset Search State
            if hasattr(self.history_text, 'search_state'):
                # Clear previous matches
                self.history_text.tag_remove('highlight', '1.0', tk.END)
                self.history_text.tag_remove('current_match', '1.0', tk.END)
                
                # Re-run search if there is a query
                query = self.history_text.search_state['query']
                if query:
                    self._find_all(self.history_text, query)
                else:
                    # Just reset state
                    self.history_text.search_state['matches'] = []
                    self.history_text.search_state['current_index'] = -1
                    self.history_text.search_state['label'].config(text="0/0")
    def _on_run_clicked(self):
        selection = self.script_tree.selection()
        if selection:
            self.clear_log()
            script_name = selection[0]
            
            # Update UI state
            self.run_button.config(state='disabled')
            self.abort_button.config(state='normal')
            self.abort_button.pack(side='left', padx=5, after=self.run_button) # Show abort button
            self.script_tree.config(selectmode='none')
            
            self.controller.run_script(script_name)

    def _on_abort_clicked(self):
        self.controller.abort_script()

    def _on_input_return(self, event):
        # Don't send if placeholder is active
        if self.input_has_placeholder:
            return
            
        text = self.input_entry.get()
        if text:
            self.append_log(f"{text}\n", 'info') # Echo input to log
            self.controller.send_input(text)
            self.input_entry.delete(0, tk.END)

    def on_script_finished(self):
        self.run_button.config(state='normal')
        self.abort_button.config(state='disabled')
        self.abort_button.pack_forget() # Hide abort button
        self.script_tree.config(selectmode='browse')
        
        # Refresh history if the finished script is selected
        selection = self.script_tree.selection()
        if selection:
            self._update_history_list(selection[0])

    def _refresh_script_list(self):
        # Clear
        for item in self.script_tree.get_children():
            self.script_tree.delete(item)
        
        # Get data
        scripts_metadata = self.controller.get_scripts_metadata()
        for filename, display_name, description in scripts_metadata:
            # Use filename as the item ID so we can retrieve it easily
            self.script_tree.insert('', tk.END, iid=filename, values=(display_name, description))

    def append_log(self, message, tag=None):
        self.append_log_batch([message], tag)

    def append_log_batch(self, messages, tag=None, skip_search_update=False, skip_ui_updates=False):
        self.output_text.config(state='normal')
        
        # Check if placeholder is present (only on first batch)
        if not skip_ui_updates and self.output_text.get("1.0", "end-1c") == "Terminal Output...":
            self.output_text.delete("1.0", tk.END)
            
        for message in messages:
            current_tag = tag
            if not current_tag:
                lower_text = message.lower()
                if "error" in lower_text or "exception" in lower_text or "critical" in lower_text:
                    current_tag = 'error'
                elif "warn" in lower_text:
                    current_tag = 'warning'
                elif "info" in lower_text:
                    current_tag = 'info'
            
            self.output_text.insert(tk.END, message, current_tag)

        # Only do expensive UI updates if not skipped
        if not skip_ui_updates:
            # Heuristic for input prompt (check last message)
            if messages:
                last_msg = messages[-1]
                stripped = last_msg.strip()
                lower_last = last_msg.lower()
                if stripped and (stripped.endswith(':') or stripped.endswith('?') or "enter" in lower_last or "input" in lower_last):
                    self.start_flash()

            self.output_text.see(tk.END)
            
            # Update search only if requested (skip during high-volume batching)
            if not skip_search_update:
                if hasattr(self.output_text, 'search_state'):
                    query = self.output_text.search_state.get('query')
                    if query:
                        self._find_all(self.output_text, query)

        self.output_text.config(state='disabled')

    def start_flash(self):
        if not self.is_flashing:
            # Clear placeholder if present
            if self.input_has_placeholder:
                self.input_entry.delete(0, tk.END)
                self.input_entry.config(foreground=self.colors['input_fg'])
                self.input_has_placeholder = False
            
            self.is_flashing = True
            self._pulse_step(0)

    def _stop_flash(self, event=None):
        if self.is_flashing:
            self.is_flashing = False
            # Restore original color immediately
            c = self.colors
            self.input_entry.configure(bg=c['input_bg'])
    
    def _on_input_focus_in(self, event=None):
        # Stop flashing
        self._stop_flash()
        
        # Remove placeholder
        if self.input_has_placeholder:
            self.input_entry.delete(0, tk.END)
            self.input_entry.config(foreground=self.colors['input_fg'])
            self.input_has_placeholder = False
    
    def _on_input_focus_out(self, event=None):
        # Add placeholder if empty
        if not self.input_entry.get():
            self.input_entry.insert(0, self.input_placeholder)
            self.input_entry.config(foreground='gray')
            self.input_has_placeholder = True

    def _pulse_step(self, step):
        if not self.is_flashing:
            return

        c = self.colors
        # Slow pulse: 800ms per state change
        if step % 2 == 0:
            new_bg = c['select_bg']
        else:
            new_bg = c['input_bg']
            
        self.input_entry.configure(bg=new_bg)
        self.root.after(800, lambda: self._pulse_step(step + 1))

    def clear_log(self):
        self.output_text.config(state='normal')
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, "Terminal Output...", 'placeholder')
        self.output_text.config(state='disabled')

    def update_actuator_table(self, data):
        # Clear existing
        for item in self.actuator_tree.get_children():
            self.actuator_tree.delete(item)
        
        for row in data:
            self.actuator_tree.insert('', tk.END, values=row)

    def _find_text(self, text_widget, query):
        text_widget.tag_remove('highlight', '1.0', tk.END)
        if not query:
            return
            
        start_pos = '1.0'
        while True:
            start_pos = text_widget.search(query, start_pos, stopindex=tk.END)
            if not start_pos:
                break
            end_pos = f"{start_pos}+{len(query)}c"
            text_widget.tag_add('highlight', start_pos, end_pos)
            start_pos = end_pos
        
        # Scroll to first match
        first_match = text_widget.search(query, '1.0', stopindex=tk.END)
        if first_match:
            text_widget.see(first_match)

    def _get_system_theme(self):
        try:
            registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            key = winreg.OpenKey(registry, r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize')
            value, _ = winreg.QueryValueEx(key, 'AppsUseLightTheme')
            return 'light' if value == 1 else 'dark'
        except Exception:
            return 'dark'

    def _toggle_theme(self):
        self.current_theme = 'light' if self.current_theme == 'dark' else 'dark'
        self.colors = THEMES[self.current_theme]
        
        # Update button text
        new_icon = "☀" if self.current_theme == 'dark' else "🌙"
        if hasattr(self, 'theme_button'):
            self.theme_button.config(text=new_icon)
            
        self._apply_theme()


    def _create_search_bar(self, parent, text_widget):
        frame = ttk.Frame(parent)
        
        ttk.Label(frame, text="Find:").pack(side='left')
        entry = ttk.Entry(frame, width=30)
        entry.pack(side='left', padx=5)
        
        # Navigation Buttons
        ttk.Button(frame, text="▼", width=3, command=lambda: self._find_next(text_widget, entry)).pack(side='left', padx=1)
        ttk.Button(frame, text="▲", width=3, command=lambda: self._find_prev(text_widget, entry)).pack(side='left', padx=1)
        
        # Toggles
        case_var = tk.BooleanVar(value=False)
        regex_var = tk.BooleanVar(value=False)
        
        # Update search on toggle
        def on_toggle():
            self._find_all(text_widget, entry.get())

        ttk.Checkbutton(frame, text="Aa", variable=case_var, style='Toggle.TCheckbutton', command=on_toggle).pack(side='left', padx=2)
        ttk.Checkbutton(frame, text=".*", variable=regex_var, style='Toggle.TCheckbutton', command=on_toggle).pack(side='left', padx=2)

        # Result Count
        count_label = ttk.Label(frame, text="0/0")
        count_label.pack(side='left', padx=5)
        
        # Bind Enter key
        entry.bind('<Return>', lambda e: self._find_next(text_widget, entry))
        
        # Store state on the text widget
        text_widget.search_state = {
            'matches': [],
            'current_index': -1,
            'query': '',
            'label': count_label,
            'case_var': case_var,
            'regex_var': regex_var
        }
        
        return frame, entry

    def _find_all(self, text_widget, query):
        text_widget.tag_remove('highlight', '1.0', tk.END)
        text_widget.tag_remove('current_match', '1.0', tk.END)
        
        state = text_widget.search_state
        state['matches'] = []
        state['current_index'] = -1
        state['query'] = query
        
        if not query:
            state['label'].config(text="0/0")
            return
            
        # Get toggle states
        case_sensitive = state['case_var'].get()
        use_regex = state['regex_var'].get()
        
        start_pos = '1.0'
        while True:
            # Prepare search arguments
            kwargs = {'stopindex': tk.END}
            if not case_sensitive:
                kwargs['nocase'] = True
            if use_regex:
                kwargs['regexp'] = True
                
            try:
                start_pos = text_widget.search(query, start_pos, **kwargs)
            except tk.TclError:
                # Invalid regex
                break
                
            if not start_pos:
                break
                
            # Calculate end position
            if use_regex:
                # For regex, we need the match length. 
                # Tkinter search returns match length in 'count' variable if requested.
                # But search() wrapper in Python simplifies this.
                # Actually, text.search(..., count=var) is the way.
                # Let's re-implement with count for regex support.
                count_var = tk.IntVar()
                kwargs['count'] = count_var
                start_pos = text_widget.search(query, start_pos, **kwargs)
                if not start_pos: 
                    break
                match_len = count_var.get()
                if match_len == 0: match_len = 1 # Avoid infinite loop on empty match
            else:
                match_len = len(query)
                
            end_pos = f"{start_pos}+{match_len}c"
            text_widget.tag_add('highlight', start_pos, end_pos)
            state['matches'].append(start_pos)
            start_pos = end_pos
            
        count = len(state['matches'])
        if count > 0:
            state['current_index'] = 0
            self._highlight_current(text_widget)
        else:
            state['label'].config(text="0/0")

    def _highlight_current(self, text_widget):
        state = text_widget.search_state
        idx = state['current_index']
        matches = state['matches']
        
        if not matches:
            return
            
        # Update Label
        state['label'].config(text=f"{idx + 1}/{len(matches)}")
        
        # Highlight current
        text_widget.tag_remove('current_match', '1.0', tk.END)
        current_pos = matches[idx]
        end_pos = f"{current_pos}+{len(state['query'])}c"
        text_widget.tag_add('current_match', current_pos, end_pos)
        text_widget.see(current_pos)

    def _find_next(self, text_widget, entry):
        query = entry.get()
        state = text_widget.search_state
        
        if query != state['query']:
            self._find_all(text_widget, query)
            return

        if not state['matches']:
            return
            
        state['current_index'] = (state['current_index'] + 1) % len(state['matches'])
        self._highlight_current(text_widget)

    def _find_prev(self, text_widget, entry):
        query = entry.get()
        state = text_widget.search_state
        
        if query != state['query']:
            self._find_all(text_widget, query)
            return

        if not state['matches']:
            return
            
        state['current_index'] = (state['current_index'] - 1) % len(state['matches'])
        self._highlight_current(text_widget)
        if self.root.state() == 'normal':
            self.root.overrideredirect(True)
            self.root.unbind('<FocusIn>')

    def _create_text_with_gutter(self, parent, height=10):
        container = ttk.Frame(parent)
        
        # Gutter (Line Numbers)
        gutter = tk.Text(container, width=4, padx=4, takefocus=0, border=0, background='lightgray', state='disabled', font=("Consolas", 10))
        gutter.pack(side='left', fill='y')
        
        # Main Text
        text_widget = tk.Text(container, height=height, font=("Consolas", 10), wrap='none', borderwidth=0, highlightthickness=0)
        text_widget.pack(side='left', expand=True, fill='both')
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=lambda *args: self._on_text_scroll(text_widget, gutter, *args))
        text_widget.configure(yscrollcommand=lambda *args: self._on_scrollbar_scroll(scrollbar, gutter, *args))
        
        scrollbar.pack(side='right', fill='y')
        
        # Bind events for line number updates
        text_widget.bind('<KeyRelease>', lambda e: self._update_line_numbers(text_widget, gutter))
        text_widget.bind('<MouseWheel>', lambda e: self._update_line_numbers(text_widget, gutter))
        text_widget.bind('<Button-1>', lambda e: self._update_line_numbers(text_widget, gutter))
        text_widget.bind('<Configure>', lambda e: self._update_line_numbers(text_widget, gutter))
        
        # Store gutter reference on text widget for easy access
        text_widget.gutter = gutter
        
        return container, text_widget, gutter

    def _on_text_scroll(self, text_widget, gutter, *args):
        text_widget.yview(*args)
        gutter.yview(*args)

    def _on_scrollbar_scroll(self, scrollbar, other_widget, *args):
        scrollbar.set(*args)
        other_widget.yview_moveto(args[0])

    def _update_line_numbers(self, text_widget, gutter):
        lines = text_widget.get('1.0', 'end-1c').count('\n') + 1
        line_numbers = '\n'.join(str(i) for i in range(1, lines + 1))
        
        gutter.config(state='normal')
        gutter.delete('1.0', tk.END)
        gutter.insert('1.0', line_numbers)
        gutter.config(state='disabled')
        
        # Sync yview
        gutter.yview_moveto(text_widget.yview()[0])

    def _set_title_bar_color(self, color_mode):
        """
        Changes the Windows title bar color using DwmSetWindowAttribute.
        color_mode: 'dark' or 'light'
        """
        try:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            # DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            value = 1 if color_mode == 'dark' else 0
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(ctypes.c_int(value)), ctypes.sizeof(ctypes.c_int))
        except Exception as e:
            print(f"Failed to set title bar color: {e}")

    def _apply_theme(self):
        style = ttk.Style()
        style.theme_use('clam') # 'clam' allows easier color customization than 'vista'

        c = self.colors
        
        # Set Native Title Bar Color
        self._set_title_bar_color(self.current_theme)
        
        # Root (Border)
        self.root.configure(bg=c['border'])
        
        # Main Container
        if hasattr(self, 'main_container'):
            self.main_container.configure(bg=c['bg'])
            
        # Update existing TK widgets
        if hasattr(self, 'output_text'):
            self.output_text.configure(bg=c['input_bg'], fg=c['fg'], insertbackground=c['fg'])
            self.output_text.tag_config('info', foreground=c['info_fg'])
            self.output_text.tag_config('warning', foreground=c['warning_fg'])
            self.output_text.tag_config('error', foreground=c['error_fg'])
            

        if hasattr(self, 'history_text'):
            self.history_text.configure(bg=c['input_bg'], fg=c['fg'], insertbackground=c['fg'])
            self.history_text.tag_config('info', foreground=c['info_fg'])
            self.history_text.tag_config('warning', foreground=c['warning_fg'])
            self.history_text.tag_config('error', foreground=c['error_fg'])
            
        if hasattr(self, 'history_gutter'):
            self.history_gutter.configure(bg=c['btn_bg'], fg=c['fg'])

        if hasattr(self, 'history_listbox'):
            self.history_listbox.configure(bg=c['tree_bg'], fg=c['tree_fg'], selectbackground=c['select_bg'], selectforeground=c['select_fg'])
        
        if hasattr(self, 'input_entry'):
            self.input_entry.configure(bg=c['input_bg'], fg=c['input_fg'], insertbackground=c['fg'])

        # Theme Button
        if hasattr(self, 'theme_button'):
             self.theme_button.configure(bg=c['bg'], fg=c['fg'], activebackground=c['select_bg'], activeforeground=c['select_fg'])
        
        # TTK Styles
        style.configure('.', background=c['bg'], foreground=c['fg'], fieldbackground=c['input_bg'])
        style.configure('TFrame', background=c['bg'], borderwidth=0)
        style.configure('TLabel', background=c['bg'], foreground=c['fg'])
        
        # Buttons
        style.configure('TButton', background=c['btn_bg'], foreground=c['btn_fg'], borderwidth=0, focuscolor=c['select_bg'])
        style.map('TButton', background=[('active', c['select_bg'])], foreground=[('active', c['select_fg'])])
        
        # TEntry (for ttk.Entry)
        style.configure('TEntry', fieldbackground=c['input_bg'], foreground=c['input_fg'], borderwidth=1, relief='flat', bordercolor=c['border'], lightcolor=c['border'], darkcolor=c['border'])
        style.map('TEntry', fieldbackground=[('active', c['input_bg'])], foreground=[('active', c['input_fg'])], bordercolor=[('focus', c['select_bg'])])
        
        # TCombobox (Minimal override for text visibility)
        style.configure('TCombobox', foreground=c['input_fg'], fieldbackground=c['input_bg'])
        style.map('TCombobox', fieldbackground=[('readonly', c['input_bg'])], foreground=[('readonly', c['input_fg'])], selectbackground=[('readonly', c['select_bg'])], selectforeground=[('readonly', c['select_fg'])])
        
        # Toggle Checkbutton (looks like a button)
        style.configure('Toggle.TCheckbutton', background=c['btn_bg'], foreground=c['btn_fg'], padding=2)
        style.map('Toggle.TCheckbutton', background=[('selected', c['select_bg']), ('active', c['select_bg'])], foreground=[('selected', c['select_fg']), ('active', c['select_fg'])])

        # Notebook
        style.configure('TNotebook', background=c['bg'], tabposition='nw', borderwidth=1, bordercolor=c['border'], lightcolor=c['border'], darkcolor=c['border'], tabmargins=[2, 0, 0, 0])
        style.configure('TNotebook.Tab', background=c['btn_bg'], foreground=c['btn_fg'], padding=[10, 5], borderwidth=1, bordercolor=c['border'], lightcolor=c['border'], darkcolor=c['border'])
        style.map('TNotebook.Tab', background=[('selected', c['bg'])], foreground=[('selected', c['fg'])], bordercolor=[('selected', c['border'])], lightcolor=[('selected', c['border'])], darkcolor=[('selected', c['border'])], padding=[('selected', [10, 5])])
        style.configure('TNotebook.client', background=c['bg'], borderwidth=0)
        
        style.configure('Treeview', 
            background=c['tree_bg'], 
            foreground=c['tree_fg'], 
            fieldbackground=c['tree_bg'],
            borderwidth=0,
            relief='flat',
            bordercolor=c['bg'],
            lightcolor=c['bg'],
            darkcolor=c['bg']
        )
        style.map('Treeview', background=[('selected', c['select_bg'])], foreground=[('selected', c['select_fg'])])
        
        style.configure('Treeview.Heading', background=c['btn_bg'], foreground=c['btn_fg'], relief='flat', borderwidth=0)
        style.map('Treeview.Heading', background=[('active', c['select_bg'])])
        
        # Scrollbars (Clam theme specific)
        style.configure("Vertical.TScrollbar", gripcount=0,
                background=c['btn_bg'], darkcolor=c['bg'], lightcolor=c['bg'],
                troughcolor=c['bg'], bordercolor=c['bg'], arrowcolor=c['fg'])
        style.map("Vertical.TScrollbar", background=[('active', c['select_bg'])])
        
        style.configure("Horizontal.TScrollbar", gripcount=0,
                background=c['btn_bg'], darkcolor=c['bg'], lightcolor=c['bg'],
                troughcolor=c['bg'], bordercolor=c['bg'], arrowcolor=c['fg'])
        style.map("Horizontal.TScrollbar", background=[('active', c['select_bg'])])
        
        # PanedWindow
        style.configure("TPanedwindow", background=c['bg'], borderwidth=0)
        style.configure("Sash", sashthickness=2, sashpad=0, handlepad=0, handlesize=0, background=c['bg'])

        # Configure TK Widgets
        # Text Widget (Standard TK)
        self.root.option_add('*Text.background', c['input_bg'])
        self.root.option_add('*Text.foreground', c['fg'])
        self.root.option_add('*Text.relief', 'flat')
        self.root.option_add('*Text.highlightThickness', '1')
        self.root.option_add('*Text.highlightBackground', c['border'])
        self.root.option_add('*Text.highlightColor', c['select_bg'])

        # Listbox (Standard TK)
        self.root.option_add('*Listbox.background', c['tree_bg'])
        self.root.option_add('*Listbox.foreground', c['tree_fg'])
        self.root.option_add('*Listbox.selectBackground', c['select_bg'])
        self.root.option_add('*Listbox.selectForeground', c['select_fg'])
        self.root.option_add('*Listbox.relief', 'flat')
        self.root.option_add('*Listbox.highlightThickness', '1')
        self.root.option_add('*Listbox.highlightBackground', c['btn_bg'])

        # Scrollbar (Standard TK - used by ScrolledText)
        # Removed as we are now using ttk.Scrollbar everywhere

if __name__ == "__main__":
    from logic import ScriptManagerController
    
    root = tk.Tk()
    
    # Initialize Controller
    controller = ScriptManagerController()
    
    # Initialize UI, passing the controller
    app = ScriptManagerUI(root, controller)
    
    # Connect UI back to Controller
    controller.set_ui(app)
    
    root.mainloop()
