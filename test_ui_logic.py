import tkinter as tk
from src.ui import ScriptManagerUI
from src.logic import ScriptManagerController
import time

class MockController:
    def __init__(self):
        self.ui = None
    def set_ui(self, ui):
        self.ui = ui
    def get_scripts_metadata(self):
        return []
    def run_script(self, name, flags=None):
        print(f"MockController: Running script {name}")
    def send_input(self, text):
        print(f"MockController: Sending input '{text}'")
    def get_script_history(self, name):
        return []
    def get_script_details(self, name):
        return None, []

def test_flow():
    root = tk.Tk()
    controller = MockController()
    app = ScriptManagerUI(root, controller)
    controller.set_ui(app)
    
    # 1. Simulate Input Prompt
    print("\n--- Simulating Input Prompt ---")
    app.append_log_batch(["Please enter something: "])
    root.update()
    
    # Check border
    thickness = app.input_entry.cget('highlightthickness')
    print(f"Border Thickness after prompt: {thickness}")
    if int(thickness) == 2:
        print("PASS: Border turned ON")
    else:
        print("FAIL: Border did NOT turn ON")

    # 2. Simulate User Input
    print("\n--- Simulating User Input ---")
    app.input_entry.insert(0, "Test Input")
    app._on_input_return(None)
    root.update()
    
    # Check border
    thickness = app.input_entry.cget('highlightthickness')
    print(f"Border Thickness after input: {thickness}")
    if int(thickness) == 0:
        print("PASS: Border turned OFF")
    else:
        print("FAIL: Border did NOT turn OFF")

    # 3. Simulate Script Echo
    print("\n--- Simulating Script Echo ---")
    app.append_log_batch(['You entered: "test"\n'])
    root.update()
    
    # Check border
    thickness = app.input_entry.cget('highlightthickness')
    print(f"Border Thickness after echo: {thickness}")
    if int(thickness) == 0:
        print("PASS: Border remained OFF")
    else:
        print("FAIL: Border turned ON (Heuristic matched echo)")

    root.destroy()

if __name__ == "__main__":
    test_flow()
