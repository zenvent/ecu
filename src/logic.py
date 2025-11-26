import os
import subprocess
import threading
import time

class ScriptManagerController:
    def __init__(self):
        self.ui = None
        self.scripts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts')
        self.scripts = {} # Map name -> full path
        self.current_process = None

    def set_ui(self, ui):
        self.ui = ui
        self.scan_scripts()

    def scan_scripts(self):
        self.scripts = {}
        if os.path.exists(self.scripts_dir):
            for f in os.listdir(self.scripts_dir):
                if f.endswith('.ps1') or f.endswith('.sh') or f.endswith('.bat') or f.endswith('.py'):
                    self.scripts[f] = os.path.join(self.scripts_dir, f)
        
        if self.ui:
            # UI update is now handled via get_scripts_metadata usually, 
            # but we can keep this or update it to call a new UI method if needed.
            # For now, let's assume the UI calls get_scripts_metadata on refresh/init.
            pass

    def get_scripts_metadata(self):
        metadata = []
        # self.scan_scripts() # Optional: auto-scan? Let's assume scan is called before or we call it here.
        # To be safe:
        if not self.scripts:
            self.scan_scripts()

        for filename, path in self.scripts.items():
            display_name = self._format_script_name(filename)
            description = self.get_script_description(filename)
            metadata.append((filename, display_name, description))
        return metadata

    def _format_script_name(self, filename):
        # Remove extension
        name = os.path.splitext(filename)[0]
        # Replace underscores with spaces
        name = name.replace('_', ' ')
        # Title Case
        return name.title()

    def get_script_description(self, script_name):
        script_path = self.scripts.get(script_name)
        if not script_path:
            return "Unknown Script"
        
        try:
            with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Read first few lines to find description
                for _ in range(10):
                    line = f.readline()
                    if not line:
                        break
                    if "Description:" in line:
                        # Extract text after "Description:"
                        return line.split("Description:", 1)[1].strip()
        except Exception:
            pass

        # Fallback if no description found
        ext = os.path.splitext(script_name)[1]
        if ext == '.ps1':
            return "PowerShell Script"
        elif ext == '.sh':
            return "Shell Script (Bash)"
        elif ext == '.py':
            return "Python Script"
        return "Executable Script"

    def abort_script(self):
        if self.current_process and self.current_process.poll() is None:
            try:
                self.current_process.terminate() # Try nice termination first
                # self.current_process.kill() # Force kill if needed (maybe after timeout)
                if self.ui:
                    self.ui.append_log("\n!!! Script aborted by user !!!\n", 'error')
            except Exception as e:
                if self.ui:
                    self.ui.append_log(f"Error aborting script: {str(e)}\n", 'error')
        else:
            if self.ui:
                self.ui.append_log("No running script to abort.\n", 'info')

    def send_input(self, text):
        if self.current_process and self.current_process.poll() is None:
            try:
                if self.current_process.stdin:
                    self.current_process.stdin.write(text + "\n")
                    self.current_process.stdin.flush()
            except Exception as e:
                if self.ui:
                    self.ui.append_log(f"Error sending input: {str(e)}\n", 'error')

    def run_script(self, script_name):
        script_path = self.scripts.get(script_name)
        if not script_path:
            return

        # Add separator
        if self.ui:
            self.ui.append_log(f"\n{'='*50}\nRunning {script_name} at {time.strftime('%H:%M:%S')}\n{'='*50}\n", 'info')

        # Run in a separate thread to keep UI responsive
        thread = threading.Thread(target=self._execute_script_thread, args=(script_name, script_path))
        thread.start()

    def _execute_script_thread(self, script_name, script_path):
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

            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE, # Enable stdin
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            process = self.current_process

            # Read output line by line
            for line in process.stdout:
                if self.ui:
                    self.ui.root.after(0, self.ui.append_log, line)
            
            for line in process.stderr:
                if self.ui:
                    self.ui.root.after(0, self.ui.append_log, line, 'error')

            process.wait()
            
            # Reset current process if it matches
            if self.current_process == process:
                self.current_process = None

            if self.ui:
                self.ui.root.after(0, self.ui.append_log, f"\nScript finished with code {process.returncode}\n", 'info')
                self.ui.root.after(0, self.ui.on_script_finished)

        except Exception as e:
            if self.ui:
                self.ui.root.after(0, self.ui.append_log, f"Error running script: {str(e)}\n", 'error')

    def refresh_actuators(self):
        # Mock data for now as requested
        # "Actuator tells me the git version / branch of the artifact and allows me to compare the same apps across regions."
        mock_data = [
            ('UserAuthService', 'us-east-1', 'v1.2.3', 'main', 'Healthy'),
            ('UserAuthService', 'eu-west-1', 'v1.2.3', 'main', 'Healthy'),
            ('PaymentGateway', 'us-east-1', 'v2.0.1', 'feature/new-pay', 'Warning'),
            ('InventoryService', 'us-east-1', 'v1.0.0', 'main', 'Healthy'),
        ]
        if self.ui:
            self.ui.update_actuator_table(mock_data)
