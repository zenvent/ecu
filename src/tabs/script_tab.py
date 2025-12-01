import tkinter as tk
from tkinter import ttk
import os
import subprocess
import threading
import time
import queue
import re

class ScriptsTab(ttk.Frame):
    def __init__(self, parent, root):
        super().__init__(parent)
        self.root = root
        
        self.root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.scripts_dir = os.path.join(self.root_dir, 'scripts')
        self.logs_dir = os.path.join(self.root_dir, 'logs')
        self.scripts = {} # Map name -> full path
        self.current_process = None
        
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)
            
        self.scan_scripts()
        self._setup_ui()

    def _setup_ui(self):
        # Layout: Top (Table), Bottom (Terminal)
        paned_window = ttk.PanedWindow(self, orient=tk.VERTICAL)
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
        
        self.output_text = tk.Text(terminal_frame, state='normal', height=10, borderwidth=0)
        output_scrollbar = ttk.Scrollbar(terminal_frame, orient=tk.VERTICAL, command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=output_scrollbar.set)
        
        self.output_text.pack(side='left', expand=True, fill='both')
        output_scrollbar.pack(side='right', fill='y')

        # Search Controls (Right aligned in action_bar)
        search_frame, self.console_search_entry = self._create_search_bar(action_bar, self.output_text)
        search_frame.pack(side='right')

        # Input Field
        self.input_entry = tk.Entry(console_tab, font=("Consolas", 10), borderwidth=0)
        self.input_entry.pack(fill='x', padx=5, pady=5, ipady=2)
        self.input_entry.bind('<Return>', self._on_input_return)
        self.input_entry.bind('<FocusIn>', self._on_input_focus_in)
        self.input_entry.bind('<FocusOut>', self._on_input_focus_out)
        self.is_flashing = False
        
        # Set placeholder
        self.input_placeholder = "Input..."
        self.input_has_placeholder = True
        self.input_entry.insert(0, self.input_placeholder)
        
        # Configure tags - Order matters! First defined = Lowest priority
        self.output_text.tag_config('normal', foreground='#ffffff') # Explicitly white for visibility
        self.output_text.tag_config('error', foreground='#ff5555')
        self.output_text.tag_config('info', foreground='#57c8ff')
        self.output_text.tag_config('warning', foreground='#ffd700')
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
        
        self.history_listbox = tk.Listbox(history_list_frame, activestyle='none', borderwidth=0)
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
        # Using self.root.after to ensure geometry is calculated
        self.root.after(100, lambda: paned_window.sashpos(0, 200))

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
        history = self.get_script_history(script_name)
        for item in history:
            self.history_listbox.insert(tk.END, item)
            
    def _clear_history_preview(self):
        self.history_text.config(state='normal')
        self.history_text.delete(1.0, tk.END)
        self.history_text.config(state='disabled')
        if hasattr(self, 'history_gutter'):
            self._update_line_numbers(self.history_text, self.history_gutter)

    def _on_history_selected(self, event):
        selection = self.history_listbox.curselection()
        script_selection = self.script_tree.selection()
        if selection and script_selection:
            filename = self.history_listbox.get(selection[0])
            script_name = script_selection[0]
            content = self.get_log_content(script_name, filename)
            
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
            self.abort_script()
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

            self.run_script(script_name, flags=selected_flags)

    def _on_input_return(self, event):
        # Don't send if placeholder is active
        if self.input_has_placeholder:
            return
            
        text = self.input_entry.get()
        if text:
            self.append_log(f"{text}\n", 'info') # Echo input to log
            self.send_input(text)
            self.input_entry.delete(0, tk.END)
            self._reset_input_style()

    def _reset_input_style(self):
        self.input_entry.config(highlightthickness=0)

    def on_script_finished(self):
        self._reset_input_style()
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
        scripts_metadata = self.get_scripts_metadata()
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

            # Split multi-line messages into individual lines for proper tag detection
            lines = message.splitlines(keepends=True)
            for line in lines:
                line_tag = current_tag
                
                if not line_tag:
                    lower_text = line.lower().strip()
                    # Stricter tagging heuristics
                    if re.search(r'(^|\[)error($|\]|:)', lower_text) or "exception:" in lower_text or "critical" in lower_text:
                        line_tag = 'error'
                    elif re.search(r'(^|\[)warn(ing)?($|\]|:)', lower_text):
                        line_tag = 'warning'
                    elif re.search(r'(^|\[)info($|\]|:)', lower_text):
                        line_tag = 'info'
                
                # Use 'normal' tag to prevent inheritance
                tags = ['normal']
                if line_tag:
                    tags.append(line_tag)
                
                self.output_text.insert(tk.END, line, tuple(tags))

        # Heuristic for input prompt (check last message)
        # Check ALWAYS, even if skipping UI updates, to ensure we catch the prompt
        if messages:
            last_item = messages[-1]
            if isinstance(last_item, tuple):
                last_msg = last_item[0]
            else:
                last_msg = last_item
            
            stripped = last_msg.strip()
            # Stricter heuristic: Must end with common prompt characters
            if stripped and (stripped.endswith(':') or stripped.endswith('?') or stripped.endswith('>')):
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
            # self.input_entry.config(foreground='#fafafa') # Theme fg
            self.input_has_placeholder = False
    
    def _on_input_focus_out(self, event=None):
        # Add placeholder if empty
        if not self.input_entry.get():
            self.input_entry.insert(0, self.input_placeholder)
            # self.input_entry.config(foreground='gray')
            self.input_has_placeholder = True

    def clear_log(self):
        self.output_text.config(state='normal')
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, "Terminal Output...", 'placeholder')
        self.output_text.config(state='disabled')

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
        _, flags = self.get_script_details(script_name)
        
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
        gutter = tk.Text(container, width=4, padx=4, takefocus=0, border=0, state='disabled', font=("Consolas", 10))
        gutter.pack(side='left', fill='y')
        
        # Main Text
        text_widget = tk.Text(container, height=height, font=("Consolas", 10), wrap='none')
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
        # Efficiently get line count without reading all text
        try:
            lines = int(text_widget.index('end-1c').split('.')[0])
        except ValueError:
            lines = 1

        # Only update text if line count changed
        current_lines = getattr(text_widget, '_current_lines', 0)
        if lines != current_lines:
            line_numbers = '\n'.join(str(i) for i in range(1, lines + 1))
            
            gutter.config(state='normal')
            gutter.delete('1.0', tk.END)
            gutter.insert('1.0', line_numbers)
            gutter.config(state='disabled')
            
            text_widget._current_lines = lines
        
        # Always sync yview
        gutter.yview_moveto(text_widget.yview()[0])

    def scan_scripts(self):
        self.scripts = {}
        if os.path.exists(self.scripts_dir):
            for f in os.listdir(self.scripts_dir):
                if f.endswith('.ps1') or f.endswith('.sh') or f.endswith('.bat') or f.endswith('.py'):
                    self.scripts[f] = os.path.join(self.scripts_dir, f)

    def get_scripts_metadata(self):
        metadata = []
        if not self.scripts:
            self.scan_scripts()

        for filename, path in self.scripts.items():
            display_name = self._format_script_name(filename)
            description, flags = self.get_script_details(filename)
            metadata.append((filename, display_name, description, flags))
        return metadata

    def _format_script_name(self, filename):
        # Remove extension
        name = os.path.splitext(filename)[0]
        # Replace underscores with spaces
        name = name.replace('_', ' ')
        # Title Case
        return name.title()

    def get_script_details(self, script_name):
        script_path = self.scripts.get(script_name)
        description = "Unknown Script"
        flags = []
        
        if not script_path:
            return description, flags
        
        try:
            with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Read first few lines
                for _ in range(15):
                    line = f.readline()
                    if not line:
                        break
                    if "Description:" in line:
                        description = line.split("Description:", 1)[1].strip()
                    if "Flags:" in line:
                        flags_str = line.split("Flags:", 1)[1].strip()
                        flags = [f.strip() for f in flags_str.split(',') if f.strip()]
        except Exception:
            pass

        if description == "Unknown Script":
            # Fallback
            ext = os.path.splitext(script_name)[1]
            if ext == '.ps1':
                description = "PowerShell Script"
            elif ext == '.sh':
                description = "Shell Script (Bash)"
            elif ext == '.py':
                description = "Python Script"
            else:
                description = "Executable Script"
                
        return description, flags

    def abort_script(self):
        if self.current_process and self.current_process.poll() is None:
            try:
                self.current_process.terminate() # Try nice termination first
                self._reset_input_style()
                self.append_log("\n!!! Script aborted by user !!!\n", 'error')
            except Exception as e:
                self.append_log(f"Error aborting script: {str(e)}\n", 'error')
        else:
            self.append_log("No running script to abort.\n", 'info')

    def send_input(self, text):
        if self.current_process and self.current_process.poll() is None:
            try:
                if self.current_process.stdin:
                    self.current_process.stdin.write((text + "\r\n").encode('utf-8'))
                    self.current_process.stdin.flush()
            except Exception as e:
                self.append_log(f"Error sending input: {str(e)}\n", 'error')

    def run_script(self, script_name, flags=None):
        script_path = self.scripts.get(script_name)
        if not script_path:
            return

        # Add separator
        self.append_log(f"{'='*50}\nRunning {script_name} at {time.strftime('%H:%M:%S')}\n{'='*50}\n", 'info')

        # Run in a separate thread to keep UI responsive
        thread = threading.Thread(target=self._execute_script_thread, args=(script_name, script_path, flags))
        thread.start()

    def _execute_script_thread(self, script_name, script_path, flags=None):
        try:
            # Determine command based on extension
            if script_name.endswith('.ps1'):
                cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path]
            elif script_name.endswith('.sh'):
                # Try to find Git Bash on Windows
                git_bash_path = r"C:\Program Files\Git\bin\bash.exe"
                if os.path.exists(git_bash_path):
                    cmd = [git_bash_path, script_path]
                else:
                    # Fallback to system bash (might be WSL)
                    cmd = ["bash", script_path] 
            elif script_name.endswith('.py'):
                cmd = ["python", "-u", script_path] # -u for unbuffered output
            elif script_name.endswith('.bat'):
                cmd = ["cmd.exe", "/c", script_path]
            else:
                cmd = [script_path]
            
            # Append flags if any
            if flags:
                cmd.extend(flags)

            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE, # Enable stdin
                text=False, # Binary mode for unbuffered reading
                bufsize=0,  # Unbuffered
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            process = self.current_process
            
            # Logging Setup
            script_log_dir = os.path.join(self.logs_dir, script_name)
            if not os.path.exists(script_log_dir):
                os.makedirs(script_log_dir)
            
            timestamp = time.strftime('%Y-%m-%d_%H-%M-%S')
            log_file_path = os.path.join(script_log_dir, f"{timestamp}.log")
            
            # Open log file
            try:
                log_file = open(log_file_path, 'w', encoding='utf-8')
            except Exception as e:
                self.root.after(0, self.append_log, f"Error opening log file: {e}\n", 'error')
                log_file = None

            # Read output line by line with queue-based ordering
            output_queue = queue.Queue()
            buffer = []
            last_flush = time.time()
            
            def process_output_queue():
                """Process queued output in UI thread"""
                try:
                    nonlocal buffer, last_flush
                    
                    # Track last scroll time for periodic scrolling
                    if not hasattr(process_output_queue, 'last_scroll'):
                        process_output_queue.last_scroll = time.time()
                    
                    # Pull items from queue - process ALL available items
                    items_processed = 0
                    try:
                        while items_processed < 1000:  # Safety limit per iteration
                            item = output_queue.get_nowait()
                            # print(f"DEBUG: process_output_queue got item: {item}") # Uncomment if needed
                            if item is None:  # Sentinel for end
                                # Flush remaining buffer - final flush, DO update search
                                if buffer:
                                    if hasattr(self, 'append_log_batch'):
                                        self.append_log_batch(buffer, skip_search_update=False)
                                    else:
                                        for line, tag in buffer:
                                            self.append_log(line, tag)
                                return  # Done
                            
                            buffer.append(item)
                            items_processed += 1
                            
                            # Flush more aggressively: every 50 lines OR every 5ms
                            current_time = time.time()
                            if len(buffer) >= 50 or (current_time - last_flush) > 0.005:
                                if hasattr(self, 'append_log_batch'):
                                    # Force UI updates to prevent missing output
                                    self.append_log_batch(buffer, skip_search_update=True, skip_ui_updates=False)
                                else:
                                    for line, tag in buffer:
                                        self.append_log(line, tag)
                                buffer = []
                                last_flush = time.time()
                                
                    except queue.Empty:
                        # Flush any remaining buffer even if not full
                        if buffer:
                            current_time = time.time()
                            if (current_time - last_flush) > 0.005:  # 5ms
                                if hasattr(self, 'append_log_batch'):
                                    # Force UI updates to prevent missing output
                                    self.append_log_batch(buffer, skip_search_update=True, skip_ui_updates=False)
                                else:
                                    for line, tag in buffer:
                                        self.append_log(line, tag)
                                buffer = []
                                last_flush = time.time()
                    
                    # Periodic scroll to keep output visible (every 100ms)
                    current_time = time.time()
                    if (current_time - process_output_queue.last_scroll) > 0.1:
                        if hasattr(self, 'output_text'):
                            self.output_text.see("end")
                        process_output_queue.last_scroll = current_time
                    
                    # Schedule next check if process still running - check very frequently
                    if process.poll() is None or not output_queue.empty():
                        self.root.after(10, process_output_queue)  # Check every 10ms
                    else:
                        # Final flush - DO update search
                        if buffer:
                            if hasattr(self, 'append_log_batch'):
                                self.append_log_batch(buffer, skip_search_update=False)
                            else:
                                for line, tag in buffer:
                                    self.append_log(line, tag)
                except Exception as e:
                    print(f"Error in process_output_queue: {e}")
                    # Try to log to UI if possible
                    try:
                        self.output_text.config(state='normal')
                        self.output_text.insert(tk.END, f"\nUI Error: {e}\n", 'error')
                        self.output_text.config(state='disabled')
                    except:
                        pass
            
            def read_stream(stream, is_stderr=False):
                # Don't blindly tag stderr as error, check content
                default_tag = None
                fd = stream.fileno()
                while True:
                    try:
                        # Read raw bytes
                        data = os.read(fd, 1024)
                        if not data:
                            break
                        
                        # Decode
                        text = data.decode('utf-8', errors='replace')
                        
                        # We might get partial lines or just prompts without newlines
                        # The UI append_log handles this fine as it just inserts text
                        # We might get partial lines or just prompts without newlines
                        # The UI append_log handles this fine as it just inserts text
                        # print(f"DEBUG: read_stream putting '{text.strip()}' tag={default_tag}")
                        output_queue.put((text, default_tag))
                        
                        if log_file:
                            self._write_to_log(log_file, text, script_log_dir, timestamp)
                    except OSError:
                        break

            # Start output processor in UI thread
            self.root.after(0, process_output_queue)
            
            # Start stderr reader thread
            stderr_thread = threading.Thread(target=read_stream, args=(process.stderr, True))
            stderr_thread.start()
            
            # Read stdout in main thread
            read_stream(process.stdout, False)
            
            stderr_thread.join()
            process.wait()
            
            # Queue the completion message BEFORE the sentinel
            completion_msg = f"\nScript finished with code {process.returncode}\n"
            output_queue.put((completion_msg, 'info'))
            
            # Signal end of output
            output_queue.put(None)
            
            # Wait for queue to be fully processed
            time.sleep(0.3)
            
            if log_file:
                log_file.close()
                self._cleanup_logs(script_log_dir)
            
            # Reset current process if it matches
            if self.current_process == process:
                self.current_process = None

            self.root.after(0, self.on_script_finished)

        except Exception as e:
            self.root.after(0, self.append_log, f"Error running script: {str(e)}\n", 'error')

    def _write_to_log(self, log_file, content, log_dir, timestamp):
        try:
            # Check size (10MB limit)
            if log_file.tell() > 10 * 1024 * 1024:
                log_file.close()
                # Find next part number
                part = 1
                while os.path.exists(os.path.join(log_dir, f"{timestamp}_part{part}.log")):
                    part += 1
                new_path = os.path.join(log_dir, f"{timestamp}_part{part}.log")
                log_file = open(new_path, 'w', encoding='utf-8')
            
            log_file.write(content)
            log_file.flush()
        except Exception:
            pass # Ignore logging errors to keep script running

    def _cleanup_logs(self, log_dir):
        try:
            files = [os.path.join(log_dir, f) for f in os.listdir(log_dir) if f.endswith('.log')]
            files.sort(key=os.path.getmtime)
            
            # Keep last 10
            while len(files) > 10:
                os.remove(files[0])
                files.pop(0)
        except Exception:
            pass

    def get_script_history(self, script_name):
        log_dir = os.path.join(self.logs_dir, script_name)
        if not os.path.exists(log_dir):
            return []
        try:
            files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
            files.sort(reverse=True) # Newest first
            return files
        except Exception:
            return []

    def get_log_content(self, script_name, filename):
        path = os.path.join(self.logs_dir, script_name, filename)
        if not os.path.exists(path):
            return ""
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception:
            return "Error reading log file."

if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from tabs import run_tab_standalone
    run_tab_standalone(ScriptsTab)
