import tkinter as tk
from tkinter import ttk
import tkinter.scrolledtext as scrolledtext
import os

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
        
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        # Tabs
        self.scripts_tab = ttk.Frame(self.notebook)
        self.actuators_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.scripts_tab, text='Scripts')
        self.notebook.add(self.actuators_tab, text='Actuators')

        self._setup_scripts_tab()
        self._setup_actuators_tab()

        # Apply Theme
        self._apply_theme()

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
        self.script_tree.heading('name', text='Script Name', anchor='w')
        self.script_tree.heading('description', text='Description', anchor='w')
        self.script_tree.column('name', width=200, anchor='w')
        self.script_tree.column('description', width=300, anchor='w')
        
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

        # Flags Frame
        self.flags_frame = ttk.Frame(action_bar)
        self.flags_frame.pack(side='left', padx=10)

        # Terminal Output (No Gutter)
        terminal_frame = ttk.Frame(console_tab)
        terminal_frame.pack(expand=True, fill='both', padx=5, pady=5)
        
        self.output_text = tk.Text(terminal_frame, borderwidth=0, state='normal', height=10, font=("Consolas", 10), bg="#1c1c1c", fg="#fafafa", insertbackground="#fafafa", selectbackground="#2f60d8", selectforeground="#ffffff")
        output_scrollbar = ttk.Scrollbar(terminal_frame, orient=tk.VERTICAL, command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=output_scrollbar.set)
        
        self.output_text.pack(side='left', expand=True, fill='both')
        output_scrollbar.pack(side='right', fill='y')

        # Search Controls (Right aligned in action_bar)
        search_frame, self.console_search_entry = self._create_search_bar(action_bar, self.output_text)
        search_frame.pack(side='right')

        # Input Field
        self.input_entry = tk.Entry(console_tab, font=("Consolas", 10), borderwidth=0, highlightthickness=0, bg="#1c1c1c", fg="#fafafa", insertbackground="#fafafa", selectbackground="#2f60d8", selectforeground="#ffffff")
        self.input_entry.pack(fill='x', padx=5, pady=5, ipady=2)
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
        self.output_text.tag_config('error', foreground='#ff5555')
        self.output_text.tag_config('info', foreground='#57c8ff')
        self.output_text.tag_config('warning', foreground='#ffd700')
        self.output_text.tag_config('placeholder', foreground='#808080')
        self.output_text.tag_config('highlight', background='yellow', foreground='black')
        self.output_text.tag_config('current_match', background='orange', foreground='black')

        # --- History Tab ---
        history_tab = ttk.Frame(self.bottom_notebook)
        self.bottom_notebook.add(history_tab, text="History")
        
        history_paned = ttk.PanedWindow(history_tab, orient=tk.HORIZONTAL)
        history_paned.pack(expand=True, fill='both')
        
        # History List
        history_list_frame = ttk.Frame(history_paned)
        history_paned.add(history_list_frame, weight=1)
        
        self.history_listbox = tk.Listbox(history_list_frame, activestyle='none', borderwidth=0, highlightthickness=0, bg="#1c1c1c", fg="#fafafa", selectbackground="#2f60d8", selectforeground="#ffffff")
        self.history_listbox.pack(side='left', expand=True, fill='both', padx=(5, 0), pady=5)
        history_scrollbar = ttk.Scrollbar(history_list_frame, orient=tk.VERTICAL, command=self.history_listbox.yview)
        self.history_listbox.configure(yscrollcommand=history_scrollbar.set)
        history_scrollbar.pack(side='right', fill='y')
        
        self.history_listbox.bind('<<ListboxSelect>>', self._on_history_selected)
        
        # History Preview
        history_preview_frame = ttk.Frame(history_paned)
        history_paned.add(history_preview_frame, weight=3)
        
        # History Search Bar
        history_search_frame = ttk.Frame(history_preview_frame)
        history_search_frame.pack(fill='x', pady=5)
        
        # History Text (with Gutter)
        history_container, self.history_text, self.history_gutter = self._create_text_with_gutter(history_preview_frame)
        history_container.pack(side='left', expand=True, fill='both', padx=5, pady=5)
        
        # Create search bar
        search_ui, self.history_search_entry = self._create_search_bar(history_search_frame, self.history_text)
        search_ui.pack(side='right')

        self.history_text.tag_config('highlight', background='yellow', foreground='black')
        self.history_text.tag_config('current_match', background='orange', foreground='black')
        self.history_text.tag_config('error', foreground='#ff5555')
        self.history_text.tag_config('info', foreground='#57c8ff')
        self.history_text.tag_config('warning', foreground='#ffd700')

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
            
            # Update Flags
            self._update_flags_ui(script_name)
        else:
            self.run_button.config(state='disabled')
            self.history_listbox.delete(0, tk.END)
            self._clear_history_preview()
            self._clear_flags_ui()

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
                if "error" in lower_text or "exception" in lower_text or "critical" in lower_text or "stderr" in lower_text or "failure" in lower_text:
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
        if not selection:
            return

        current_text = self.run_button.cget('text')
        
        if "Stop" in current_text:
            # Stop Action
            self.controller.abort_script()
            self.run_button.config(state='disabled') # Disable until stopped
        else:
            # Run Action
            self.clear_log()
            script_name = selection[0]
            
            # Update UI state
            self.run_button.config(text="⏹ Stop Script")
            self.script_tree.config(selectmode='none')
            
            # Collect flags
            selected_flags = []
            if hasattr(self, 'flag_vars'):
                for flag, var in self.flag_vars.items():
                    if var.get():
                        selected_flags.append(flag)

            self.controller.run_script(script_name, flags=selected_flags)

    def _on_input_return(self, event):
        # Don't send if placeholder is active
        if self.input_has_placeholder:
            return
            
        text = self.input_entry.get()
        if text:
            self.append_log(f"{text}\n", 'info') # Echo input to log
            self.controller.send_input(text)
            self.input_entry.delete(0, tk.END)
            # Reset border
            self.input_entry.config(highlightthickness=0)

    def on_script_finished(self):
        self.run_button.config(state='normal', text="❯ Run Selected Script")
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
        for filename, display_name, description, flags in scripts_metadata:
            # Use filename as the item ID so we can retrieve it easily
            self.script_tree.insert('', tk.END, iid=filename, values=(display_name, description))

    def append_log(self, message, tag=None):
        self.append_log_batch([message], tag)

    def append_log_batch(self, messages, tag=None, skip_search_update=False, skip_ui_updates=False):
        self.output_text.config(state='normal')
        
        # Check if placeholder is present (only on first batch)
        if not skip_ui_updates and self.output_text.get("1.0", "end-1c") == "Terminal Output...":
            self.output_text.delete("1.0", tk.END)
            
        for item in messages:
            if isinstance(item, tuple):
                message, current_tag = item
            else:
                message = item
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

        # Heuristic for input prompt (check last message)
        # Check ALWAYS, even if skipping UI updates, to ensure we catch the prompt
        if messages:
            last_item = messages[-1]
            if isinstance(last_item, tuple):
                last_msg = last_item[0]
            else:
                last_msg = last_item
            
            stripped = last_msg.strip()
            lower_last = last_msg.lower()
            if stripped and (stripped.endswith(':') or stripped.endswith('?') or "enter" in lower_last or "input" in lower_last):
                self.notify_input_requested()

        # Only do expensive UI updates if not skipped
        if not skip_ui_updates:
            self.output_text.see(tk.END)
            
            # Update search only if requested (skip during high-volume batching)
            if not skip_search_update:
                if hasattr(self.output_text, 'search_state'):
                    query = self.output_text.search_state.get('query')
                    if query:
                        self._find_all(self.output_text, query)

        self.output_text.config(state='disabled')

    def notify_input_requested(self):
        # Visual notification (Orange border)
        self.input_entry.config(highlightthickness=2, highlightbackground='#b04a00', highlightcolor='#b04a00')
        self.input_entry.focus_set()

    def _on_input_focus_in(self, event=None):
        # Remove placeholder
        if self.input_has_placeholder:
            self.input_entry.delete(0, tk.END)
            self.input_entry.delete(0, tk.END)
            self.input_entry.config(foreground='#fafafa') # Theme fg
            self.input_has_placeholder = False
    
    def _on_input_focus_out(self, event=None):
        # Add placeholder if empty
        if not self.input_entry.get():
            self.input_entry.insert(0, self.input_placeholder)
            self.input_entry.config(foreground='gray')
            self.input_has_placeholder = True

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

    def _update_flags_ui(self, script_name):
        self._clear_flags_ui()
        
        self.flag_vars = {}
        
        # Get flags from controller
        _, flags = self.controller.get_script_details(script_name)
        
        if flags:
            ttk.Label(self.flags_frame, text="Flags:").pack(side='left', padx=(0, 5))
            for flag in flags:
                var = tk.BooleanVar()
                self.flag_vars[flag] = var
                ttk.Checkbutton(self.flags_frame, text=flag, variable=var, style='Toggle.TCheckbutton').pack(side='left', padx=2)

    def _clear_flags_ui(self):
        for widget in self.flags_frame.winfo_children():
            widget.destroy()
        self.flag_vars = {}

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
        gutter = tk.Text(container, width=4, padx=4, takefocus=0, border=0, background='#252526', foreground='#fafafa', state='disabled', font=("Consolas", 10))
        gutter.pack(side='left', fill='y')
        
        # Main Text
        text_widget = tk.Text(container, height=height, font=("Consolas", 10), wrap='none', borderwidth=0, highlightthickness=0, bg="#1c1c1c", fg="#fafafa", insertbackground="#fafafa", selectbackground="#2f60d8", selectforeground="#ffffff")
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

    def _apply_theme(self):
        theme_path = os.path.join(os.path.dirname(__file__), "theme", "sv.tcl")
        self.root.tk.call("source", theme_path)
        style = ttk.Style()
        style.theme_use("sun-valley-dark")


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
