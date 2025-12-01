import tkinter as tk
from tkinter import ttk

class ActuatorsTab(ttk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        # Layout: Top buttons, Bottom Table
        top_frame = ttk.Frame(self)
        top_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(top_frame, text="Refresh Actuators", command=self._on_refresh_actuators).pack(side='left')

        # Table
        columns = ('app_name', 'region', 'version', 'branch', 'commit_id', 'status')
        self.actuator_tree = ttk.Treeview(self, columns=columns, show='headings')
        
        self.actuator_tree.heading('app_name', text='App Name')
        self.actuator_tree.heading('region', text='Region')
        self.actuator_tree.heading('version', text='Version')
        self.actuator_tree.heading('branch', text='Branch')
        self.actuator_tree.heading('commit_id', text='Commit ID')
        self.actuator_tree.heading('status', text='Status')

        self.actuator_tree.pack(expand=True, fill='both', padx=5, pady=5)

    def _on_refresh_actuators(self):
        self.refresh_actuators()

    def update_actuator_table(self, data):
        # Clear existing
        for item in self.actuator_tree.get_children():
            self.actuator_tree.delete(item)
        
        for row in data:
            self.actuator_tree.insert('', tk.END, values=row)

    def refresh_actuators(self):
        # Mock data for now as requested
        # "Actuator tells me the git version / branch of the artifact and allows me to compare the same apps across regions."
        mock_data = [
            ('UserAuthService', 'us-east-1', '1.2.3-SNAPSHOT', 'main', 'a1b2c3d', 'UP'),
            ('UserAuthService', 'eu-west-1', '1.2.3-SNAPSHOT', 'main', 'a1b2c3d', 'UP'),
            ('PaymentGateway', 'us-east-1', '2.0.1', 'feature/new-pay', 'f4e5d6c', 'DOWN'),
            ('InventoryService', 'us-east-1', '1.0.0', 'main', '9h8g7f6', 'UP'),
            ('OrderService', 'us-west-2', '0.9.5', 'develop', '1a2b3c4', 'OUT_OF_SERVICE'),
        ]
        self.update_actuator_table(mock_data)

if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from tabs import run_tab_standalone
    run_tab_standalone(ActuatorsTab)
