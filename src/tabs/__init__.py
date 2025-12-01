import tkinter as tk
from tkinter import ttk
import tkinter as tk
from tkinter import ttk
import os
import sys

# Add src to path so we can import logic
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_tab_standalone(TabClass):
    root = tk.Tk()
    root.title(f"{TabClass.__name__} Standalone")

    # Apply theme
    try:
        theme_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "theme", "sv.tcl")
        if os.path.exists(theme_path):
            root.tk.call("source", theme_path)
            style = ttk.Style()
            style.theme_use("sun-valley-dark")
    except Exception as e:
        print(f"Theme not loaded: {e}")

    # Instantiate Tab
    if TabClass.__name__ == 'ScriptsTab':
        tab = TabClass(root, root)
    else:
        tab = TabClass(root)
    
    tab.pack(fill='both', expand=True)
    
    root.mainloop()
