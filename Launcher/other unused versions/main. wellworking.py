import customtkinter as ctk
import os, json, time, threading, psutil, subprocess
from ctypes import *
from ctypes import wintypes
from tkinter import filedialog, messagebox

# --- WINAPI KONSTANSOK ---
PROCESS_ALL_ACCESS = (0x000F0000 | 0x00100000 | 0xFFF)
MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000
PAGE_READWRITE = 0x04
MAX_PATH = 260
THREAD_SUSPEND_RESUME = 0x0002

# --- WINAPI DEFINÍCIÓK ---
k32 = WinDLL('kernel32', use_last_error=True)

k32.OpenProcess.restype = wintypes.HANDLE
k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]

k32.VirtualAllocEx.restype = c_void_p
k32.VirtualAllocEx.argtypes = [wintypes.HANDLE, c_void_p, c_size_t, wintypes.DWORD, wintypes.DWORD]

k32.WriteProcessMemory.restype = wintypes.BOOL
k32.WriteProcessMemory.argtypes = [wintypes.HANDLE, c_void_p, c_void_p, c_size_t, POINTER(c_size_t)]

k32.GetModuleHandleA.restype = wintypes.HANDLE
k32.GetModuleHandleA.argtypes = [c_char_p]

k32.GetProcAddress.restype = c_void_p
k32.GetProcAddress.argtypes = [wintypes.HANDLE, c_char_p]

k32.CreateRemoteThread.restype = wintypes.HANDLE
k32.CreateRemoteThread.argtypes = [wintypes.HANDLE, c_void_p, c_size_t, c_void_p, c_void_p, wintypes.DWORD, wintypes.LPDWORD]

class RebootLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Project Reboot - BlackFN Engine")
        self.geometry("850x550")
        self.config_path = "config.json"
        self.load_settings()
        self.setup_ui()

    def load_settings(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f: self.settings = json.load(f)
            except: self.settings = {"email": "Player@gmail.com", "password": "123", "path": ""}
        else:
            self.settings = {"email": "Player@gmail.com", "password": "123", "path": ""}

    def setup_ui(self):
        self.configure(fg_color="#0b0b0b")
        self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(0, weight=1)
        
        self.sidebar = ctk.CTkFrame(self, width=200, fg_color="#121212", corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self.sidebar, text="REBOOT", font=("Segoe UI", 28, "bold"), text_color="#3b82f6").pack(pady=40)
        
        self.main_frame = ctk.CTkFrame(self, corner_radius=20, fg_color="#0f0f0f")
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        self.email_entry = ctk.CTkEntry(self.main_frame, width=380, placeholder_text="Email Address")
        self.email_entry.insert(0, self.settings["email"]); self.email_entry.pack(pady=10)
        self.pass_entry = ctk.CTkEntry(self.main_frame, width=380, placeholder_text="Password", show="*")
        self.pass_entry.insert(0, self.settings["password"]); self.pass_entry.pack(pady=10)
        self.path_entry = ctk.CTkEntry(self.main_frame, width=380)
        self.path_entry.insert(0, self.settings["path"]); self.path_entry.pack(pady=5)
        
        ctk.CTkButton(self.main_frame, text="Browse Build", command=self.browse).pack(pady=5)
        ctk.CTkButton(self.main_frame, text="LAUNCH FORTNITE", fg_color="#3b82f6", height=55, width=280, 
                        font=("Segoe UI", 16, "bold"), command=self.handle_launch).pack(pady=40)

    def browse(self):
        f = filedialog.askdirectory()
        if f:
            exe = os.path.join(f, "FortniteGame/Binaries/Win64/FortniteClient-Win64-Shipping.exe").replace("/", os.sep)
            self.path_entry.delete(0, 'end'); self.path_entry.insert(0, exe)

    def set_process_state(self, pid, suspend=True):
        """BlackFN-féle szál-fagyasztás (Freeze/Resume)"""
        try:
            process = psutil.Process(pid)
            for thread in process.threads():
                h_thread = k32.OpenThread(THREAD_SUSPEND_RESUME, False, thread.id)
                if h_thread:
                    if suspend: k32.SuspendThread(h_thread)
                    else: k32.ResumeThread(h_thread)
                    k32.CloseHandle(h_thread)
            return True
        except: return False

    def python_injector(self, pid, dll_path):
        """Injektálás Freeze logikával a stabilitásért"""
        try:
            full_path = os.path.abspath(dll_path)
            path_bytes = full_path.encode('ascii') + b'\x00'

            # 1. Fagyasztás injektálás előtt
            self.set_process_state(pid, True)
            time.sleep(0.5)

            h_proc = k32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
            if not h_proc: 
                self.set_process_state(pid, False)
                return False

            loc = k32.VirtualAllocEx(h_proc, None, MAX_PATH, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE)
            if not loc:
                k32.CloseHandle(h_proc)
                self.set_process_state(pid, False)
                return False

            bytes_written = c_size_t(0)
            k32.WriteProcessMemory(h_proc, loc, path_bytes, len(path_bytes), byref(bytes_written))

            h_mod = k32.GetModuleHandleA(b"kernel32.dll")
            load_lib_addr = k32.GetProcAddress(h_mod, b"LoadLibraryA")

            h_thread = k32.CreateRemoteThread(h_proc, None, 0, load_lib_addr, loc, 0, None)
            
            if h_thread:
                k32.WaitForSingleObject(h_thread, 2000)
                k32.CloseHandle(h_thread)
                success = True
            else:
                success = False

            # 2. Újraindítás injektálás után
            time.sleep(0.5)
            self.set_process_state(pid, False)
            k32.CloseHandle(h_proc)
            return success
        except:
            return False

    def handle_launch(self):
        self.settings.update({"email": self.email_entry.get(), "password": self.pass_entry.get(), "path": self.path_entry.get()})
        with open(self.config_path, "w") as f: json.dump(self.settings, f)

        full_exe_path = self.settings["path"]
        if not os.path.exists(full_exe_path):
            messagebox.showerror("Hiba", "Az EXE nem található!")
            return

        bin_dir = os.path.dirname(full_exe_path)
        exe_name = os.path.basename(full_exe_path)

        # BlackFN-féle Fake EAC Argumentumok
        args = f'-epicapp=Fortnite -epicenv=Prod -epiclocale=en-us -epicportal -nobe -noeac -fromfl=eac -fltoken=h1cdhchd10150221h130eB56 -skippatchcheck -AUTH_LOGIN={self.settings["email"]} -AUTH_PASSWORD={self.settings["password"]} -AUTH_TYPE=epic'

        # Lawin Backend indítása (FakeAC célból is)
        backend = os.path.abspath("assets/backend/lawinv1.exe")
        if os.path.exists(backend):
            subprocess.Popen(backend, creationflags=0x08000000)

        # Indítás munkakönyvtárban
        subprocess.Popen(f'"{exe_name}" {args}', cwd=bin_dir, shell=True)
        
        threading.Thread(target=self.monitor_process, args=(exe_name,), daemon=True).start()
        messagebox.showinfo("Launched", "Játék elindítva BlackFN módban!")

    def monitor_process(self, exe_name):
        target_pid = None
        while not target_pid:
            for p in psutil.process_iter(['pid', 'name']):
                if p.info['name'] == exe_name:
                    target_pid = p.info['pid']; break
            time.sleep(0.5)

        # Várakozás az ablakra (UUU-logika)
        window_found = False
        while not window_found:
            def callback(hwnd, pid):
                nonlocal window_found
                if windll.user32.IsWindowVisible(hwnd):
                    lp_pid = wintypes.DWORD()
                    windll.user32.GetWindowThreadProcessId(hwnd, byref(lp_pid))
                    if lp_pid.value == pid: window_found = True
                return True
            windll.user32.EnumWindows(WINFUNCTYPE(c_bool, wintypes.HWND, wintypes.LPARAM)(callback), target_pid)
            time.sleep(0.5)

        print("[+] Ablak megtalálva. Freeze & Inject...")
        time.sleep(2) 
        
        dll_path = os.path.abspath("dlls/Starfall.dll")
        if self.python_injector(target_pid, dll_path):
            print("[SIKER] Injektálás kész.")
        else:
            print("[HIBA] Injektálás sikertelen.")

if __name__ == "__main__":
    app = RebootLauncher()
    app.mainloop()
