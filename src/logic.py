import os
import subprocess
import threading
import time

class ScriptManagerController:
    def __init__(self):
        self.ui = None
        self.scripts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts')
        self.logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        self.scripts = {} # Map name -> full path
        self.current_process = None
        
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)

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
            
            # Logging Setup
            script_log_dir = os.path.join(self.logs_dir, script_name)
            if not os.path.exists(script_log_dir):
                os.makedirs(script_log_dir)
            
            timestamp = time.strftime('%Y-%m-%d_%H-%M-%S')
            log_file_path = os.path.join(script_log_dir, f"{timestamp}.log")
            
            # Open log file
            try:
                log_file = open(log_file_path, 'w', encoding='utf-8')
            except Exception as e:
                if self.ui:
                    self.ui.root.after(0, self.ui.append_log, f"Error opening log file: {e}\n", 'error')
                log_file = None

            # Read output line by line with queue-based ordering
            import queue
            output_queue = queue.Queue()
            buffer = []
            last_flush = time.time()
            
            def process_output_queue():
                """Process queued output in UI thread"""
                nonlocal buffer, last_flush
                
                # Pull items from queue
                try:
                    while True:
                        item = output_queue.get_nowait()
                        if item is None:  # Sentinel for end
                            # Flush remaining buffer
                            if buffer and self.ui:
                                if hasattr(self.ui, 'append_log_batch'):
                                    self.ui.append_log_batch([line for line, _ in buffer])
                                else:
                                    for line, tag in buffer:
                                        self.ui.append_log(line, tag)
                            return  # Done
                        
                        buffer.append(item)
                        
                        # Flush if buffer is large enough or enough time passed
                        current_time = time.time()
                        if len(buffer) >= 100 or (current_time - last_flush) > 0.1:
                            if self.ui:
                                if hasattr(self.ui, 'append_log_batch'):
                                    self.ui.append_log_batch([line for line, _ in buffer])
                                else:
                                    for line, tag in buffer:
                                        self.ui.append_log(line, tag)
                            buffer = []
                            last_flush = time.time()
                            
                except queue.Empty:
                    pass
                
                # Schedule next check if process still running
                if process.poll() is None or not output_queue.empty():
                    self.ui.root.after(50, process_output_queue)
                else:
                    # Final flush
                    if buffer and self.ui:
                        if hasattr(self.ui, 'append_log_batch'):
                            self.ui.append_log_batch([line for line, _ in buffer])
                        else:
                            for line, tag in buffer:
                                self.ui.append_log(line, tag)
            
            def read_stream(stream, is_stderr=False):
                tag = 'error' if is_stderr else None
                for line in stream:
                    output_queue.put((line, tag))
                    if log_file:
                        self._write_to_log(log_file, line, script_log_dir, timestamp)

            # Start output processor in UI thread
            if self.ui:
                self.ui.root.after(0, process_output_queue)
            
            # Start stderr reader thread
            stderr_thread = threading.Thread(target=read_stream, args=(process.stderr, True))
            stderr_thread.start()
            
            # Read stdout in main thread
            read_stream(process.stdout, False)
            
            stderr_thread.join()
            process.wait()
            
            # Queue the completion message BEFORE the sentinel
            # This ensures it appears after all output
            if self.ui:
                completion_msg = f"\nScript finished with code {process.returncode}\n"
                output_queue.put((completion_msg, 'info'))
            
            # Signal end of output
            output_queue.put(None)
            
            # Wait for queue to be fully processed
            time.sleep(0.3)
            
            if log_file:
                log_file.close()
                self._cleanup_logs(script_log_dir)
            
            # Reset current process if it matches
            if self.current_process == process:
                self.current_process = None

            if self.ui:
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

    def _write_to_log(self, log_file, content, log_dir, timestamp):
        try:
            # Check size (10MB limit)
            if log_file.tell() > 10 * 1024 * 1024:
                log_file.close()
                # Find next part number
                part = 1
                while os.path.exists(os.path.join(log_dir, f"{timestamp}_part{part}.log")):
                    part += 1
                new_path = os.path.join(log_dir, f"{timestamp}_part{part}.log")
                log_file = open(new_path, 'w', encoding='utf-8')
            
            log_file.write(content)
            log_file.flush()
        except Exception:
            pass # Ignore logging errors to keep script running

    def _cleanup_logs(self, log_dir):
        try:
            files = [os.path.join(log_dir, f) for f in os.listdir(log_dir) if f.endswith('.log')]
            files.sort(key=os.path.getmtime)
            
            # Keep last 10
            while len(files) > 10:
                os.remove(files[0])
                files.pop(0)
        except Exception:
            pass

    def get_script_history(self, script_name):
        log_dir = os.path.join(self.logs_dir, script_name)
        if not os.path.exists(log_dir):
            return []
        try:
            files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
            files.sort(reverse=True) # Newest first
            return files
        except Exception:
            return []

    def get_log_content(self, script_name, filename):
        path = os.path.join(self.logs_dir, script_name, filename)
        if not os.path.exists(path):
            return ""
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception:
            return "Error reading log file."
