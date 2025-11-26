import tkinter as tk
from ui import ScriptManagerUI
from logic import ScriptManagerController

def main():
    root = tk.Tk()
    
    # Initialize Controller
    controller = ScriptManagerController()
    
    # Initialize UI, passing the controller
    app = ScriptManagerUI(root, controller)
    
    # Connect UI back to Controller
    controller.set_ui(app)
    
    root.mainloop()

if __name__ == "__main__":
    main()
