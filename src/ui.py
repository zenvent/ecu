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

        # Bottom Frame (Action Bar + Terminal)
        bottom_frame = ttk.Frame(paned_window)
        paned_window.add(bottom_frame, weight=3)

        # Action Bar (Moved to top of bottom frame)
        action_bar = ttk.Frame(bottom_frame)
        action_bar.pack(fill='x', pady=5)
        
        self.run_button = ttk.Button(action_bar, text="▶ Run Selected Script", command=self._on_run_clicked, state='disabled')
        self.run_button.pack(side='left')

        self.abort_button = ttk.Button(action_bar, text="⏹ Abort Script", command=self._on_abort_clicked, state='disabled')
        self.abort_button.pack(side='left', padx=5)

        self.refresh_button = ttk.Button(action_bar, text="⟳ Refresh Scripts", command=self._refresh_script_list)
        self.refresh_button.pack(side='left', padx=5)
        
        # Clear Button
        ttk.Button(action_bar, text="🗑 Clear Terminal", command=self.clear_log).pack(side='right')

        # Terminal Output (No Header)
        self.output_text = scrolledtext.ScrolledText(bottom_frame, state='normal', height=10)
        self.output_text.pack(expand=True, fill='both')
        
        # Input Field
        self.input_entry = ttk.Entry(bottom_frame)
        self.input_entry.pack(fill='x', pady=(5, 0))
        self.input_entry.bind('<Return>', self._on_input_return)
        
        # Configure tags
        self.output_text.tag_config('error', foreground='red')
        self.output_text.tag_config('info', foreground='blue')
        self.output_text.tag_config('placeholder', foreground='gray')

        # Initial Placeholder
        self.clear_log() # Sets placeholder

        # Initial Load
        self._refresh_script_list()
        
        # Set Sash Position (approx 25% of 800 height = 200)
        # We need to wait for visibility or just try setting it. 
        # Since geometry is 1000x800, 25% is 200.
        # Note: sashpos is 0-indexed.
        # We can't set it immediately if window isn't drawn, but we can try update_idletasks
        # self.root.update_idletasks() # Might be risky in constructor
        # Let's just rely on weights or set it after a delay if needed.
        # Actually, panedwindow sash setting is tricky before mainloop.
        # We'll use a delayed call.
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
            self.run_button.config(state='normal')
        else:
            self.run_button.config(state='disabled')

    def _on_run_clicked(self):
        selection = self.script_tree.selection()
        if selection:
            item = self.script_tree.item(selection[0])
            # The filename is hidden or we need to map back. 
            # Let's store filename in values or find a way to map.
            # Actually, let's store filename as the item ID or in a hidden column?
            # Or just store it in the values and retrieve it.
            # Wait, I didn't add a hidden column.
            # Let's assume I can get it from the controller or I should have stored it.
            # Better approach: Store filename in the item tags or values.
            # Let's use the 'tags' or just look it up.
            # Simplest: Store filename as the item iid (id).
            script_name = selection[0] 
            self.append_log(f"Running {script_name}...\n", 'info')
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
        # State update will happen when script finishes (or we can force it here, but waiting for callback is safer)

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

    def _refresh_script_list(self):
        # Clear
        for item in self.script_tree.get_children():
            self.script_tree.delete(item)
        
        # Get data
        scripts_metadata = self.controller.get_scripts_metadata()
        for filename, display_name, description in scripts_metadata:
            # Use filename as the item ID so we can retrieve it easily
            self.script_tree.insert('', tk.END, iid=filename, values=(display_name, description))

    # Public methods for Controller to call
    def update_script_list(self, scripts):
        # Deprecated by _refresh_script_list but kept for compatibility if needed
        pass

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
