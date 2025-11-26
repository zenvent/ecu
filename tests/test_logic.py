import sys
import os
import time
import unittest

# Add src to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from logic import ScriptManagerController

class MockUI:
    def __init__(self):
        self.root = self
        self.logs = []
        self.scripts = []
        self.actuator_data = []

    def after(self, delay, func, *args):
        # Mocking tkinter.after by calling immediately
        func(*args)

    def update_script_list(self, scripts):
        self.scripts = scripts

    def append_log(self, message, tag=None):
        self.logs.append(message)

    def update_actuator_table(self, data):
        self.actuator_data = data

    def on_script_finished(self):
        self.logs.append("SCRIPT_FINISHED_CALLBACK")

class TestLogic(unittest.TestCase):
    def setUp(self):
        self.controller = ScriptManagerController()
        self.ui = MockUI()
        self.controller.set_ui(self.ui)

    def test_scan_scripts(self):
        # Should find at least the 2 scripts we created
        # Note: UI update is no longer pushed, so we check controller state directly
        self.controller.scan_scripts()
        self.assertIn('test_powershell.ps1', self.controller.scripts)
        self.assertIn('test_shell.sh', self.controller.scripts)

    def test_get_scripts_metadata(self):
        metadata = self.controller.get_scripts_metadata()
        # Should be a list of tuples (filename, display_name, description)
        self.assertTrue(len(metadata) >= 2)
        
        # Check first item structure
        item = metadata[0]
        self.assertEqual(len(item), 3)
        
        # Check formatting
        # Find test_powershell.ps1
        ps_item = next((x for x in metadata if x[0] == 'test_powershell.ps1'), None)
        self.assertIsNotNone(ps_item)
        self.assertEqual(ps_item[1], 'Test Powershell')
        self.assertIn('A simple PowerShell test script', ps_item[2])

    def test_run_script(self):
        # Run the powershell script
        script_name = 'test_powershell.ps1'
        self.controller.run_script(script_name)
        
        # Wait a bit for thread
        time.sleep(3)
        
        # Check logs
        # We expect "Hello from PowerShell!" and the separator
        print("Logs:", self.ui.logs)
        self.assertTrue(len(self.ui.logs) > 0)
        
        # Check for separator
        separator_found = any('=====' in log for log in self.ui.logs)
        self.assertTrue(separator_found, "Separator not found in logs")
        
        # Check for finished callback
        self.assertIn("SCRIPT_FINISHED_CALLBACK", self.ui.logs)

    def test_abort_script(self):
        # Run long running script
        script_name = 'long_running.py'
        self.controller.run_script(script_name)
        
        # Wait a bit for it to start
        time.sleep(1)
        
        # Abort
        self.controller.abort_script()
        
        # Wait for thread to finish
        time.sleep(1)
        
        # Check logs for abort message
        abort_msg_found = any('Script aborted by user' in log for log in self.ui.logs)
        self.assertTrue(abort_msg_found, "Abort message not found in logs")

    def test_interactive_input(self):
        # Run interactive script
        script_name = 'interactive.bat'
        self.controller.run_script(script_name)
        
        # Wait for it to ask for input
        time.sleep(1)
        
        # Send input
        self.controller.send_input("TestUser")
        
        # Wait for response
        time.sleep(1)
        
        # Check logs for response
        # Note: batch file output might be buffered or tricky to capture exactly in real-time test without a real console,
        # but our logic captures stdout.
        # Expected output: "Nice to meet you, TestUser!"
        response_found = any('Nice to meet you, TestUser' in log for log in self.ui.logs)
        self.assertTrue(response_found, "Interactive response not found in logs")

    def test_refresh_actuators(self):
        self.controller.refresh_actuators()
        self.assertTrue(len(self.ui.actuator_data) > 0)
        self.assertEqual(self.ui.actuator_data[0][0], 'UserAuthService')

if __name__ == '__main__':
    unittest.main()
