import tkinter as tk
from tkinter import ttk
import os
from tabs.script_tab import ScriptsTab
from tabs.actuator_tab import ActuatorsTab

class ScriptManagerUI:
    def __init__(self, root):
        self.root = root
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
        self.scripts_tab = ScriptsTab(self.notebook, self.root)
        self.actuators_tab = ActuatorsTab(self.notebook)

        self.notebook.add(self.scripts_tab, text='Scripts')
        self.notebook.add(self.actuators_tab, text='Actuators')

        # Apply Theme
        self._apply_theme()

    def _apply_theme(self):
        theme_path = os.path.join(os.path.dirname(__file__), "theme", "sv.tcl")
        if os.path.exists(theme_path):
            self.root.tk.call("source", theme_path)
            style = ttk.Style()
            style.theme_use("sun-valley-dark")

if __name__ == "__main__":
    root = tk.Tk()
    app = ScriptManagerUI(root)
    root.mainloop()
