import tkinter as tk
from tkinter import ttk
import tkinter.scrolledtext as scrolledtext

class ScriptManagerUI:
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        self.root.title("Script Manager")
        self.root.geometry("1000x800")

        # Main Layout
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        # Tabs
        self.scripts_tab = ttk.Frame(self.notebook)
        self.actuators_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.scripts_tab, text='Scripts')
        self.notebook.add(self.actuators_tab, text='Actuators')

        self._setup_scripts_tab()
        self._setup_actuators_tab()

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
        
        self.run_button = ttk.Button(action_bar, text="▶ Run Selected Script", command=self._on_run_clicked, state='disabled')
        self.run_button.pack(side='left')

        self.abort_button = ttk.Button(action_bar, text="⏹ Abort Script", command=self._on_abort_clicked, state='disabled')
        self.abort_button.pack(side='left', padx=5)

        self.refresh_button = ttk.Button(action_bar, text="⟳ Refresh Scripts", command=self._refresh_script_list)
        self.refresh_button.pack(side='left', padx=5)
        
        # Clear Button
        ttk.Button(action_bar, text="🗑 Clear Terminal", command=self.clear_log).pack(side='right')

        # Console Search Bar
        console_search_frame = ttk.Frame(console_tab)
        console_search_frame.pack(fill='x', pady=(0, 2))
        ttk.Label(console_search_frame, text="Find:").pack(side='left')
        self.console_search_entry = ttk.Entry(console_search_frame)
        self.console_search_entry.pack(side='left', fill='x', expand=True, padx=5)
        ttk.Button(console_search_frame, text="Find", command=lambda: self._find_text(self.output_text, self.console_search_entry.get())).pack(side='left')

        # Terminal Output (No Header)
        self.output_text = scrolledtext.ScrolledText(console_tab, state='normal', height=10)
        self.output_text.pack(expand=True, fill='both')
        
        # Input Field
        self.input_entry = ttk.Entry(console_tab)
        self.input_entry.pack(fill='x', pady=(5, 0))
        self.input_entry.bind('<Return>', self._on_input_return)
        
        # Configure tags
        self.output_text.tag_config('error', foreground='red')
        self.output_text.tag_config('info', foreground='blue')
        self.output_text.tag_config('placeholder', foreground='gray')
        self.output_text.tag_config('highlight', background='yellow', foreground='black')

        # --- History Tab ---
        history_tab = ttk.Frame(self.bottom_notebook)
        self.bottom_notebook.add(history_tab, text="History")
        
        history_paned = ttk.PanedWindow(history_tab, orient=tk.HORIZONTAL)
        history_paned.pack(expand=True, fill='both', padx=5, pady=5)
        
        # History List
        history_list_frame = ttk.Frame(history_paned)
        history_paned.add(history_list_frame, weight=1)
        
        self.history_listbox = tk.Listbox(history_list_frame)
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
        ttk.Label(history_search_frame, text="Find:").pack(side='left')
        self.history_search_entry = ttk.Entry(history_search_frame)
        self.history_search_entry.pack(side='left', fill='x', expand=True, padx=5)
        ttk.Button(history_search_frame, text="Find", command=lambda: self._find_text(self.history_text, self.history_search_entry.get())).pack(side='left')

        self.history_text = scrolledtext.ScrolledText(history_preview_frame, state='disabled', height=10)
        self.history_text.pack(expand=True, fill='both')
        self.history_text.tag_config('highlight', background='yellow', foreground='black')

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
            self.history_text.insert(tk.END, content)
            self.history_text.config(state='disabled')

    def _clear_history_preview(self):
        self.history_text.config(state='normal')
        self.history_text.delete(1.0, tk.END)
        self.history_text.config(state='disabled')

    def _on_run_clicked(self):
        selection = self.script_tree.selection()
        if selection:
            script_name = selection[0]
            self.append_log(f"Running {script_name}...\n", 'info')
            
            # Update UI state
            self.run_button.config(state='disabled')
            self.abort_button.config(state='normal')
            self.refresh_button.config(state='disabled')
            self.script_tree.config(selectmode='none')
            
            self.controller.run_script(script_name)

    def _on_abort_clicked(self):
        self.controller.abort_script()

    def _on_input_return(self, event):
        text = self.input_entry.get()
        if text:
            self.append_log(f"{text}\n", 'info') # Echo input to log
            self.controller.send_input(text)
            self.input_entry.delete(0, tk.END)

    def on_script_finished(self):
        self.run_button.config(state='normal')
        self.abort_button.config(state='disabled')
        self.refresh_button.config(state='normal')
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
        self.output_text.config(state='normal')
        
        # Check if placeholder is present
        if self.output_text.get("1.0", "end-1c") == "Terminal Output...":
            self.output_text.delete("1.0", tk.END)
            
        self.output_text.insert(tk.END, message, tag)
        self.output_text.see(tk.END)
        self.output_text.config(state='disabled')

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
