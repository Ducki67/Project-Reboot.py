import customtkinter as ctk
import os, json, time, threading, psutil, subprocess
from ctypes import *
from tkinter import filedialog, messagebox

# --- WINDOWS API ---
PROCESS_ALL_ACCESS = (0x000F0000 | 0x00100000 | 0xFFF)

class RebootLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Project Reboot - S3 1:1 Stable")
        self.geometry("850x550")
        self.config_path = "config.json"
        self.load_settings()
        self.setup_ui()

    def load_settings(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f: self.settings = json.load(f)
        else:
            self.settings = {"email": "ssd@gmail.com", "password": "1231212", "path": ""}

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
        
        ctk.CTkButton(self.main_frame, text="LAUNCH WITH COBALT", fg_color="#3b82f6", height=55, width=280, 
                        font=("Segoe UI", 16, "bold"), command=self.handle_launch).pack(pady=40)

    def browse(self):
        f = filedialog.askdirectory()
        if f:
            exe = os.path.join(f, "FortniteGame/Binaries/Win64/FortniteClient-Win64-Shipping.exe").replace("/", os.sep)
            self.path_entry.delete(0, 'end'); self.path_entry.insert(0, exe)

    def inject_dll(self, pid, dll_name):
        path = os.path.abspath(f"dlls/{dll_name}")
        if not os.path.exists(path): return False
        path_bytes = path.encode('ascii') + b'\x00'
        h_proc = windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
        if not h_proc: return False
        addr = windll.kernel32.VirtualAllocEx(h_proc, 0, len(path_bytes), 0x3000, 0x04)
        windll.kernel32.WriteProcessMemory(h_proc, addr, path_bytes, len(path_bytes), 0)
        h_load = windll.kernel32.GetProcAddress(windll.kernel32.GetModuleHandleA(b"kernel32.dll"), b"LoadLibraryA")
        thread = windll.kernel32.CreateRemoteThread(h_proc, None, 0, h_load, addr, 0, None)
        if thread:
            windll.kernel32.WaitForSingleObject(thread, 0xFFFFFFFF)
            windll.kernel32.CloseHandle(thread)
        windll.kernel32.CloseHandle(h_proc)
        print(f"[OK] {dll_name} injected!")
        return True

    def handle_launch(self):
        self.settings.update({"email": self.email_entry.get(), "password": self.pass_entry.get(), "path": self.path_entry.get()})
        with open(self.config_path, "w") as f: json.dump(self.settings, f)

        # 1. Backend Start
        backend = os.path.abspath("assets/backend/lawinv1.exe")
        if os.path.exists(backend):
            subprocess.Popen(backend, creationflags=0x08000000)

        # 2. Launch Game (Argumentumok a Cobalt-hoz)
        args = f'"{self.settings["path"]}" -log -NOSPLASH -windowed -AUTH_LOGIN={self.settings["email"]} -AUTH_PASSWORD={self.settings["password"]} -AUTH_TYPE=epic -epicapp=Fortnite -epicenv=Prod -EpicPortal'
        subprocess.Popen(args, shell=True)

        def monitor():
            print("[INFO] Várakozás a Fortnite folyamatra...")
            target_pid = None
            while not target_pid:
                for p in psutil.process_iter(['pid', 'name']):
                    if "FortniteClient-Win64-Shipping" in p.info['name']:
                        target_pid = p.info['pid']; break
                time.sleep(0.5)

            # --- S3 LOG-ALAPÚ DINAMIKUS IDŐZÍTÉS ---
            # A logod szerint a D3D11Device létrehozása után kell injektálni.
            # Ez kb. 6-8 másodperc a te gépeden.
            print(f"[INFO] PID {target_pid} megtalálva. Várakozás a grafikai motorra (8 mp)...")
            time.sleep(8) 
            
            # CSAK COBALT (Auth)
            self.inject_dll(target_pid, "Starfall.dll")
            
            # Console csak a Lobby-ban (25 mp múlva)
            #time.sleep(25)
            #self.inject_dll(target_pid, "console.dll")

        threading.Thread(target=monitor, daemon=True).start()
        messagebox.showinfo("Launched", "Játék elindítva! Injektálás 8 mp múlva történik.")

if __name__ == "__main__":
    app = RebootLauncher()
    app.mainloop()
