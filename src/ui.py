import tkinter as tk
from tkinter import ttk
import tkinter.scrolledtext as scrolledtext
import winreg

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
        self.root.geometry("1000x800")
        self.root.overrideredirect(True) # Hide default title bar
        
        # Main Container (Border Effect)
        self.main_container = tk.Frame(root)
        self.main_container.pack(fill='both', expand=True, padx=1, pady=1)
        
        # Custom Title Bar
        self.title_bar = tk.Frame(self.main_container, bg=THEMES['dark']['bg'], relief='flat')
        self.title_bar.pack(fill='x', side='top')
        
        # Title Label
        self.title_label = tk.Label(self.title_bar, text="Script Manager", font=("Segoe UI", 10), bg=THEMES['dark']['bg'], fg=THEMES['dark']['fg'])
        self.title_label.pack(side='left', padx=10, pady=5)
        
        # Window Controls Frame
        controls_frame = tk.Frame(self.title_bar, bg=THEMES['dark']['bg'])
        controls_frame.pack(side='right')

        # Close Button
        self.close_button = tk.Button(controls_frame, text="✕", command=self.root.destroy, bd=0, padx=10, pady=5, bg=THEMES['dark']['bg'], fg=THEMES['dark']['fg'], activebackground='red', activeforeground='white')
        self.close_button.pack(side='right')
        
        # Maximize Button
        self.max_button = tk.Button(controls_frame, text="□", command=self._toggle_maximize, bd=0, padx=10, pady=5, bg=THEMES['dark']['bg'], fg=THEMES['dark']['fg'], activebackground=THEMES['dark']['select_bg'])
        self.max_button.pack(side='right')
        
        # Minimize Button
        self.min_button = tk.Button(controls_frame, text="─", command=self._minimize_window, bd=0, padx=10, pady=5, bg=THEMES['dark']['bg'], fg=THEMES['dark']['fg'], activebackground=THEMES['dark']['select_bg'])
        self.min_button.pack(side='right')

        # Theme Toggle
        self.current_theme = self._get_system_theme()
        theme_icon = "☀" if self.current_theme == 'dark' else "🌙"
        self.theme_button = tk.Button(controls_frame, text=theme_icon, command=self._toggle_theme, bd=0, padx=10, pady=5, bg=THEMES['dark']['bg'], fg=THEMES['dark']['fg'], activebackground=THEMES['dark']['select_bg'])
        self.theme_button.pack(side='right')
        
        # Drag Logic
        self.title_bar.bind('<Button-1>', self._start_move)
        self.title_bar.bind('<B1-Motion>', self._on_move)
        self.title_label.bind('<Button-1>', self._start_move)
        self.title_label.bind('<B1-Motion>', self._on_move)
        
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        # Tabs
        self.scripts_tab = ttk.Frame(self.notebook)
        self.actuators_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.scripts_tab, text='Scripts')
        self.notebook.add(self.actuators_tab, text='Actuators')

        self._setup_scripts_tab()
        self._setup_actuators_tab()

        # Apply Theme - Call this LAST so all widgets exist
        self.colors = THEMES[self.current_theme]
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
        # self.abort_button.pack(side='left', padx=5) # Don't pack initially

        

        # Search Controls (Right aligned in action_bar)
        ttk.Button(action_bar, text="Find", command=lambda: self._find_text(self.output_text, self.console_search_entry.get())).pack(side='right')
        self.console_search_entry = ttk.Entry(action_bar, width=20)
        self.console_search_entry.pack(side='right', padx=5)
        ttk.Label(action_bar, text="Find:").pack(side='right')

        # Terminal Output (No Header)
        # Replaced ScrolledText with Text + ttk.Scrollbar for better theming
        terminal_frame = ttk.Frame(console_tab)
        terminal_frame.pack(expand=True, fill='both')
        
        self.output_text = tk.Text(terminal_frame, state='normal', height=10, font=("Consolas", 10))
        output_scrollbar = ttk.Scrollbar(terminal_frame, orient=tk.VERTICAL, command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=output_scrollbar.set)
        
        self.output_text.pack(side='left', expand=True, fill='both')
        output_scrollbar.pack(side='right', fill='y')
        
        # Input Field
        self.input_entry = tk.Entry(console_tab, font=("Consolas", 10))
        self.input_entry.pack(fill='x', pady=(5, 0))
        self.input_entry.bind('<Return>', self._on_input_return)
        self.input_entry.bind('<FocusIn>', self._stop_flash)
        self.is_flashing = False
        
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

        self.history_text = tk.Text(history_preview_frame, state='disabled', height=10, font=("Consolas", 10))
        history_text_scrollbar = ttk.Scrollbar(history_preview_frame, orient=tk.VERTICAL, command=self.history_text.yview)
        self.history_text.configure(yscrollcommand=history_text_scrollbar.set)
        
        self.history_text.pack(side='left', expand=True, fill='both')
        history_text_scrollbar.pack(side='right', fill='y')
        
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
            self.clear_log()
            script_name = selection[0]
            self.append_log(f"Running {script_name}...\n", 'info')
            
            # Update UI state
            self.run_button.config(state='disabled')
            self.abort_button.config(state='normal')
            self.abort_button.pack(side='left', padx=5, after=self.run_button) # Show abort button
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
        if not tag:
            lower_text = message.lower()
            if "error" in lower_text or "exception" in lower_text or "critical" in lower_text:
                tag = 'error'
            elif "warn" in lower_text:
                tag = 'warning'
            elif "info" in lower_text:
                tag = 'info'
            
            # Heuristic for input prompt
            stripped = message.strip()
            if stripped and (stripped.endswith(':') or stripped.endswith('?') or "enter" in lower_text or "input" in lower_text):
                self.start_flash()

        self.output_text.config(state='normal')
        
        # Check if placeholder is present
        if self.output_text.get("1.0", "end-1c") == "Terminal Output...":
            self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, message, tag)
        self.output_text.see(tk.END)
        self.output_text.config(state='disabled')

    def start_flash(self):
        if not self.is_flashing:
            self.is_flashing = True
            self._pulse_step(0)

    def _stop_flash(self, event=None):
        if self.is_flashing:
            self.is_flashing = False
            # Restore original color immediately
            c = self.colors
            self.input_entry.configure(bg=c['input_bg'])

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

    def _start_move(self, event):
        self.x = event.x
        self.y = event.y

    def _on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def _toggle_maximize(self):
        if self.root.state() == 'zoomed':
            self.root.state('normal')
        else:
            self.root.state('zoomed')

    def _minimize_window(self):
        # For overrideredirect windows, standard iconify can be tricky.
        # Simple approach: withdraw and create a dummy window or just use state('iconic')
        # Windows supports state('iconic') even for overrideredirect in some cases, but often it disappears.
        # A robust workaround is complex. For now, we'll try standard iconify.
        # If it fails to restore, user can Alt-Tab.
        self.root.overrideredirect(False) # Temporarily restore to allow minimization
        self.root.iconify()
        self.root.bind('<FocusIn>', self._on_restore)

    def _on_restore(self, event):
        if self.root.state() == 'normal':
            self.root.overrideredirect(True)
            self.root.unbind('<FocusIn>')

    def _apply_theme(self):
        style = ttk.Style()
        style.theme_use('clam') # 'clam' allows easier color customization than 'vista'

        c = self.colors
        
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
            # History might not use tags yet, but good to have if we add them
        if hasattr(self, 'history_listbox'):
            self.history_listbox.configure(bg=c['tree_bg'], fg=c['tree_fg'], selectbackground=c['select_bg'], selectforeground=c['select_fg'])
        
        if hasattr(self, 'input_entry'):
            self.input_entry.configure(bg=c['input_bg'], fg=c['input_fg'], insertbackground=c['fg'])

        # Title Bar Updates
        if hasattr(self, 'title_bar'):
            self.title_bar.configure(bg=c['bg'])
            self.title_label.configure(bg=c['bg'], fg=c['fg'])
            # Controls
            for btn in [self.close_button, self.max_button, self.min_button, self.theme_button]:
                btn.configure(bg=c['bg'], fg=c['fg'], activebackground=c['select_bg'], activeforeground=c['select_fg'])
            self.close_button.configure(activebackground='red', activeforeground='white')
        
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
        
        # Notebook
        style.configure('TNotebook', background=c['bg'], tabposition='nw', borderwidth=1, bordercolor=c['border'], lightcolor=c['border'], darkcolor=c['border'], tabmargins=[2, 0, 0, 0])
        style.configure('TNotebook.Tab', background=c['btn_bg'], foreground=c['btn_fg'], padding=[10, 5], borderwidth=1, bordercolor=c['border'], lightcolor=c['border'], darkcolor=c['border'])
        style.map('TNotebook.Tab', background=[('selected', c['bg'])], foreground=[('selected', c['fg'])], bordercolor=[('selected', c['border'])], lightcolor=[('selected', c['border'])], darkcolor=[('selected', c['border'])], padding=[('selected', [10, 5])])
        style.configure('TNotebook.client', background=c['bg'], borderwidth=0)
        
        # Treeview
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
