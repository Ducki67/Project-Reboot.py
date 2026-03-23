import customtkinter as ctk
import os, json, time, threading, psutil, subprocess
from tkinter import filedialog, messagebox

class RebootLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Ducki67's Python FN Launcher (External Inj)")
        self.geometry("850x550")
        self.config_path = "config.json"
        self.load_settings()
        self.setup_ui()

    def load_settings(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f: self.settings = json.load(f)
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
        ctk.CTkButton(self.main_frame, text="LAUNCH FORTNITE", fg_color="#3b82f6", height=55, width=280, font=("Segoe UI", 16, "bold"), command=self.handle_launch).pack(pady=40)

    def browse(self):
        f = filedialog.askdirectory()
        if f:
            exe = os.path.join(f, "FortniteGame/Binaries/Win64/FortniteClient-Win64-Shipping.exe").replace("/", os.sep)
            self.path_entry.delete(0, 'end'); self.path_entry.insert(0, exe)

    def handle_launch(self):
        self.settings.update({"email": self.email_entry.get(), "password": self.pass_entry.get(), "path": self.path_entry.get()})
        with open(self.config_path, "w") as f: json.dump(self.settings, f)

        full_exe_path = self.settings["path"]
        bin_dir = os.path.dirname(full_exe_path)
        exe_name = os.path.basename(full_exe_path)

        # Batch Argumentumok 1:1
        args = f'-epicapp=Fortnite -epicenv=Prod -epiclocale=en-us -epicportal -nobe -fromfl=eac -fltoken=h1cdhchd10150221h130eB56 -skippatchcheck -AUTH_LOGIN={self.settings["email"]} -AUTH_PASSWORD={self.settings["password"]} -AUTH_TYPE=epic'

        # Játék indítása a saját mappájából (Munkakönyvtár fix)
        subprocess.Popen(f'"{exe_name}" {args}', cwd=bin_dir, shell=True)
        
        threading.Thread(target=self.monitor_external, args=(exe_name,), daemon=True).start()
        messagebox.showinfo("Launched", "Játék elindítva! Injektálás 8 mp múlva a BasicInjectorral.")

    def monitor_external(self, exe_name):
        print("[+] Waiting for process...")
        target_pid = None
        while not target_pid:
            for p in psutil.process_iter(['pid', 'name']):
                if p.info['name'] == exe_name:
                    target_pid = p.info['pid']; break
            time.sleep(0.5)

        print(f"[+] Process found: {target_pid}. Waiting 8s...")
        time.sleep(8) 
        
        # --- JAVÍTOTT ÚTVONALAK A KÉPED ALAPJÁN ---
        # A BasicInjector.exe az 'assets' mappában van
        injector_path = os.path.abspath("assets/BasicInjector.exe")
        
        # A Starfall.dll a 'dlls' mappában van (ami a main.py mellett van)
        dll_path = os.path.abspath("dlls/Starfall.dll")
        
        if os.path.exists(injector_path) and os.path.exists(dll_path):
            print(f"[+] Starting External Injection: {injector_path}")
            # FONTOS: A BasicInjector-nak a PID-et vagy az EXE nevet kell átadni? 
            # A Batch fájlod szerint az EXE nevet:
            subprocess.Popen(f'"{injector_path}" "{exe_name}" "{dll_path}"', shell=True)
            print("[+] Külső injector elindítva!")
        else:
            print(f"[!] HIBA: Valami még mindig nincs a helyén!")
            print(f"Ezt kerestem (Injector): {injector_path}")
            print(f"Ezt kerestem (DLL): {dll_path}")
            # Kiírjuk mi van a mappákban, hogy lásd a hibát
            if not os.path.exists(injector_path): print("-> Az 'assets/BasicInjector.exe' NEM LÉTEZIK!")
            if not os.path.exists(dll_path): print("-> A 'dlls/Starfall.dll' NEM LÉTEZIK!")
            
if __name__ == "__main__":
    app = RebootLauncher()
    app.mainloop()
