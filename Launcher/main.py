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

k32 = WinDLL('kernel32', use_last_error=True)
k32.VirtualAllocEx.restype = c_void_p

class RebootLauncher(ctk.CTk):
    # ... (init és setup_ui marad a korábbi verzióból) ...

    def start_fake_eac(self):
        """BlackFN FakeAC logika: Elindítunk egy hamis folyamatot, amit a játék keres"""
        print("[+] Fake EAC indítása...")
        # Sokszor elég egy üres notepad.exe-t átnevezni vagy elindítani a háttérben
        # A BlackFN gyakran a háttérben futó backendet használja erre
        try:
            # Itt elindíthatunk egy minimális folyamatot, ha a Starfall kéri
            pass
        except: pass

    def inject_with_freeze(self, pid, dll_path):
        """BlackFN Freeze & Inject logika"""
        try:
            p = psutil.Process(pid)
            print(f"[+] FREEZE: Folyamat felfüggesztése (PID: {pid})...")
            p.suspend() # Megállítja az összes szálat
            
            time.sleep(1)
            
            # Injektálás (a már működő kódod)
            full_path = os.path.abspath(dll_path)
            path_bytes = full_path.encode('ascii') + b'\x00'
            h_proc = k32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
            
            if h_proc:
                loc = k32.VirtualAllocEx(h_proc, None, MAX_PATH, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE)
                k32.WriteProcessMemory(h_proc, loc, path_bytes, len(path_bytes), None)
                h_mod = k32.GetModuleHandleA(b"kernel32.dll")
                load_lib_addr = k32.GetProcAddress(h_mod, b"LoadLibraryA")
                h_thread = k32.CreateRemoteThread(h_proc, None, 0, load_lib_addr, loc, 0, None)
                
                if h_thread:
                    k32.WaitForSingleObject(h_thread, 5000)
                    k32.CloseHandle(h_thread)
                k32.CloseHandle(h_proc)

            print("[+] RESUME: Folyamat újraindítása...")
            p.resume() # Visszaengedi a játékot
            return True
        except Exception as e:
            print(f"[!] Hiba a fagyasztás során: {e}")
            return False

    def handle_launch(self):
        # ... (beállítások mentése ...)
        
        # 1. Fake EAC indítása
        self.start_fake_eac()

        # 2. Backend indítása
        backend = os.path.abspath("assets/backend/lawinv1.exe")
        if os.path.exists(backend): subprocess.Popen(backend, creationflags=0x08000000)

        # 3. Játék indítása Ch2+ argumentumokkal (BlackFN minta)
        exe_path = self.settings["path"]
        bin_dir = os.path.dirname(exe_path)
        exe_name = os.path.basename(exe_path)
        
        # Szigorúbb argumentumok az EAC/BE elkerülésére
        args = f'-epicapp=Fortnite -epicenv=Prod -epiclocale=en-us -epicportal -nobe -noeac -fromfl=eac -fltoken=h1cdhchd10150221h130eB56 -skippatchcheck -AUTH_LOGIN={self.settings["email"]} -AUTH_PASSWORD={self.settings["password"]} -AUTH_TYPE=epic'

        subprocess.Popen(f'"{exe_name}" {args}', cwd=bin_dir, shell=True)
        
        threading.Thread(target=self.monitor_process, args=(exe_name,), daemon=True).start()
        messagebox.showinfo("Launched", "Játék elindítva Ch2+ módban!")

    def monitor_process(self, exe_name):
        target_pid = None
        while not target_pid:
            for p in psutil.process_iter(['pid', 'name']):
                if p.info['name'] == exe_name:
                    target_pid = p.info['pid']; break
            time.sleep(0.5)

        # Ch2+ esetén megvárjuk az ablakot, majd FREEZE és INJECT
        print("[+] Várakozás az ablakra...")
        # ... (ablakfigyelő kód marad ...)
        
        time.sleep(2)
        self.inject_with_freeze(target_pid, "dlls/Starfall.dll")
