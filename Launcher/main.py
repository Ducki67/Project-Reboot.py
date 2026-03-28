import customtkinter as ctk
import os, json, time, threading, psutil, subprocess
from ctypes import *
from ctypes import wintypes
from tkinter import filedialog, messagebox

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    from pypresence import Presence
    HAS_RPC = True
except ImportError:
    HAS_RPC = False

# --- WINAPI KONSTANSOK & DEFINICIÓK ---
PROCESS_ALL_ACCESS = (0x000F0000 | 0x00100000 | 0xFFF)
MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000
PAGE_READWRITE = 0x04
MAX_PATH = 260
THREAD_SUSPEND_RESUME = 0x0002

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

# --- APP CONFIG ---
CONFIG_PATH = "config.json"
DEFAULT_CONFIG = {
    "username": "PythonPlayer",
    "email": "player@projectreboot.py",
    "password": "12345678",
    "host_username": "PythonServer",
    "host_email": "server@projectreboot.py",
    "host_account_password": "HostPassword",
    "path": "",
    "dll_console": os.path.join(os.getcwd(), "dlls", "console.dll"),
    "dll_auth": os.path.join(os.getcwd(), "dlls", "Starfall.dll"),
    "dll_memory": os.path.join(os.getcwd(), "dlls", "memory.dll"),
    "dll_server": os.path.join(os.getcwd(), "dlls", "reboot.dll"),
    "backend_path": "assets/backend/lawinserver.exe",
    "backend_autostart": False,
    "host_port": "7777",
    "host_name": "Reboot Server",
    "host_desc": "A Project Reboot Server",
    "host_pass": "",
    "host_max_players": "100",
    "host_custom_args": "",
    "host_headless": False,
    "host_autorun": False,
    "launch_args": "-epicapp=Fortnite -epicenv=Prod -epiclocale=en-us -epicportal -nobe -noeac -fromfl=eac -fltoken=h1cdhchd10150221h130eB56 -skippatchcheck",
    "rpc_enabled": True
}

class DiscordManager:
    def __init__(self, client_id="1485699679529210106"):
        self.client_id = client_id
        self.rpc = None
        self.start_time = int(time.time())
        self.is_connected = False
        if HAS_RPC:
            try:
                self.rpc = Presence(self.client_id)
                self.rpc.connect()
                self.is_connected = True
                self.update_state("In Launcher", "Starting up...")
            except Exception:
                pass

    def update_state(self, state, details):
        if self.rpc and self.is_connected:
            try:
                self.rpc.update(state=state, details=details, start=self.start_time, large_image="rebootLogo", large_text="Project Reboot")
            except: pass

    def clear_state(self):
        if self.rpc and self.is_connected:
            try:
                self.rpc.clear()
            except: pass

# --- UI TILE COMPONENT ---
# Matches Fluent UI "SettingTile" look exactly
class SettingTile(ctk.CTkFrame):
    def __init__(self, parent, title, subtitle, button_text=None, button_command=None, show_entry=False, entry_var=None, is_subpage=False, is_switch=False, switch_var=None, is_option=False, option_var=None, options_list=None, button_text_var=None):
        super().__init__(parent, fg_color="transparent")
        self.pack(fill="x", pady=6)

        container = ctk.CTkFrame(self, fg_color="#181818", corner_radius=5, height=78)
        container.pack(fill="x")
        container.pack_propagate(False)

        text_frame = ctk.CTkFrame(container, fg_color="transparent")
        text_frame.pack(side="left", padx=20, fill="y", pady=15)

        ctk.CTkLabel(text_frame, text=title, font=("Segoe UI", 15, "bold"), text_color="#f4f4f5", anchor="w").pack(fill="x", pady=(0, 2))
        ctk.CTkLabel(text_frame, text=subtitle, font=("Segoe UI", 12), text_color="#a1a1aa", anchor="w").pack(fill="x")

        if is_switch:
            switch = ctk.CTkSwitch(container, text="", variable=switch_var, onvalue=True, offvalue=False, progress_color="#3b82f6", button_color="white", button_hover_color="#e4e4e7")
            switch.pack(side="right", padx=(0, 20))
        elif is_option and options_list:
            opt = ctk.CTkOptionMenu(container, variable=option_var, values=options_list, fg_color="#2d2d2d", button_color="#3d3d3d", button_hover_color="#4d4d4d", dropdown_fg_color="#2d2d2d", width=120)
            opt.pack(side="right", padx=(0, 20))
        elif button_text or button_text_var:
            btn_width = 120
            btn_color = "#2d2d2d"
            btn_hover = "#3d3d3d"
            if button_text == "Toggle":
                btn_color = "#3b82f6"
                btn_hover = "#2563eb"
            if is_subpage:
                btn_width = 40
                btn_color = "transparent"
                btn_hover = "#2d2d2d"

            btn = ctk.CTkButton(container, text=button_text if not button_text_var else button_text_var.get(), fg_color=btn_color, hover_color=btn_hover, text_color="white", font=("Segoe UI", 13, "bold"), width=btn_width, height=34, corner_radius=4, command=button_command)
            if button_text_var:
                btn.configure(textvariable=button_text_var)
            btn.pack(side="right", padx=(0, 20))

        if show_entry and entry_var is not None:
             ent = ctk.CTkEntry(container, fg_color="#121212", border_width=1, border_color="#333333", text_color="#ffffff", font=("Segoe UI", 13), height=34, corner_radius=4, textvariable=entry_var)
             ent.pack(side="right", fill="x", expand=True, padx=(20, 20))

class RebootLauncherApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.withdraw()  # Hide the window while initializing to prevent "piece-by-piece" loading
        self.title("Reboot Launcher")
        self.geometry("950x650")
        self.minsize(850, 550)
        ctk.set_appearance_mode("dark")
        self.configure(fg_color="#0b0b0b")

        self.settings = DEFAULT_CONFIG.copy()
        self.load_config()

        # Variables for settings
        self.path_var = ctk.StringVar(value=self.settings.get("path", ""))
        self.dll_console_var = ctk.StringVar(value=self.settings.get("dll_console", ""))
        self.dll_auth_var = ctk.StringVar(value=self.settings.get("dll_auth", ""))
        self.dll_memory_var = ctk.StringVar(value=self.settings.get("dll_memory", ""))
        self.dll_server_var = ctk.StringVar(value=self.settings.get("dll_server", ""))
        self.username_var = ctk.StringVar(value=self.settings.get("username", "PythonPlayer"))
        self.email_var = ctk.StringVar(value=self.settings.get("email", "player@projectreboot.py"))
        self.password_var = ctk.StringVar(value=self.settings.get("password", "12345678"))
        
        self.host_username_var = ctk.StringVar(value=self.settings.get("host_username", "PythonServer"))
        self.host_email_var = ctk.StringVar(value=self.settings.get("host_email", "server@projectreboot.py"))
        self.host_account_password_var = ctk.StringVar(value=self.settings.get("host_account_password", "HostPassword"))

        self.host_port_var = ctk.StringVar(value=self.settings.get("host_port", "7777"))
        self.host_name_var = ctk.StringVar(value=self.settings.get("host_name", "Reboot Server"))
        self.host_desc_var = ctk.StringVar(value=self.settings.get("host_desc", "A Project Reboot Server"))
        self.host_pass_var = ctk.StringVar(value=self.settings.get("host_pass", ""))
        self.host_max_players_var = ctk.StringVar(value=self.settings.get("host_max_players", "100"))
        self.host_custom_args_var = ctk.StringVar(value=self.settings.get("host_custom_args", ""))
        self.host_headless_var = ctk.BooleanVar(value=self.settings.get("host_headless", False))
        self.host_autorun_var = ctk.BooleanVar(value=self.settings.get("host_autorun", False))
        self.launch_args_var = ctk.StringVar(value=self.settings.get("launch_args", "-epicapp=Fortnite -epicenv=Prod -epiclocale=en-us -epicportal -nobe -noeac -fromfl=eac -fltoken=h1cdhchd10150221h130eB56 -skippatchcheck"))
        self.backend_type_var = ctk.StringVar(value=self.settings.get("backend_type", "Local"))
        self.backend_action_text = ctk.StringVar(value="Start" if self.backend_type_var.get() == "Embedded" else "Ping")
        self.backend_type_var.trace_add("write", self.update_backend_action_text)

        self.backend_url_var = ctk.StringVar(value=self.settings.get("backend_url", "http://127.0.0.1:3551"))
        self.backend_path_var = ctk.StringVar(value=self.settings.get("backend_path", "assets/backend/lawinserver.exe"))
        self.backend_autostart_var = ctk.BooleanVar(value=self.settings.get("backend_autostart", False))
        self.rpc_enabled_var = ctk.BooleanVar(value=self.settings.get("rpc_enabled", True))
        self.rpc_enabled_var.trace_add("write", self.update_discord_rpc_state)

        self.discord = DiscordManager()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.setup_sidebar()
        self.setup_pages()

        self.show_page("Play")
        self.update_discord_rpc_state()
        
        if self.backend_autostart_var.get():
            self.start_backend()

        # Center the window
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = int((screen_width / 2) - (950 / 2))
        y = int((screen_height / 2) - (650 / 2))
        self.geometry(f"950x650+{x}+{y}")
        
        # Show the window cleanly after a brief moment so the mainloop can catch up
        self.after(50, self.deiconify)

    def update_discord_rpc_state(self, *args):
        if hasattr(self, 'rpc_enabled_var'):
            if self.rpc_enabled_var.get():
                self.discord.update_state("In Launcher", "Browsing menus")
            else:
                self.discord.clear_state()
            # Try saving config if it's completely initialized
            if hasattr(self, 'path_var') and args:
                self.save_config()

    def update_backend_action_text(self, *args):
        if hasattr(self, 'backend_type_var') and hasattr(self, 'backend_action_text'):
            btype = self.backend_type_var.get()
            if btype in ["Remote", "Local"]:
                self.backend_action_text.set("Ping")
            else:
                self.backend_action_text.set("Start")
            
            # Hide/Show relevant tiles if they exist and maintain correct order
            if hasattr(self, 'remote_url_tile') and hasattr(self, 'backend_path_tile') and hasattr(self, 'start_backend_tile'):
                # First unpack everything
                self.remote_url_tile.pack_forget()
                self.backend_path_tile.pack_forget()
                self.start_backend_tile.pack_forget()
                self.autostart_backend_tile.pack_forget()
                
                # Then pack in correct order based on type
                if btype == "Remote":
                    self.remote_url_tile.pack(fill="x", pady=6)
                elif btype == "Embedded":
                    self.backend_path_tile.pack(fill="x", pady=6)
                    
                # Always pack these last so they are at the bottom
                self.start_backend_tile.pack(fill="x", pady=6)
                self.autostart_backend_tile.pack(fill="x", pady=6)
                    
            if hasattr(self, 'path_var') and args:
                self.save_config()

    def load_config(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r") as f:
                    self.settings.update(json.load(f))
            except: pass

    def save_config(self):
        self.settings["path"] = self.path_var.get()
        self.settings["dll_console"] = self.dll_console_var.get()
        self.settings["dll_auth"] = self.dll_auth_var.get()
        self.settings["dll_memory"] = self.dll_memory_var.get()
        self.settings["dll_server"] = self.dll_server_var.get()
        self.settings["username"] = self.username_var.get()
        self.settings["email"] = self.email_var.get()
        self.settings["password"] = self.password_var.get()
        self.settings["host_username"] = self.host_username_var.get()
        self.settings["host_email"] = self.host_email_var.get()
        self.settings["host_account_password"] = self.host_account_password_var.get()
        self.settings["host_port"] = self.host_port_var.get()
        self.settings["host_name"] = self.host_name_var.get()
        self.settings["host_desc"] = self.host_desc_var.get()
        self.settings["host_pass"] = self.host_pass_var.get()
        self.settings["host_max_players"] = self.host_max_players_var.get()
        self.settings["host_custom_args"] = self.host_custom_args_var.get()
        self.settings["host_headless"] = self.host_headless_var.get()
        self.settings["host_autorun"] = self.host_autorun_var.get()
        self.settings["launch_args"] = self.launch_args_var.get()
        self.settings["backend_type"] = self.backend_type_var.get()
        self.settings["backend_url"] = self.backend_url_var.get()
        self.settings["backend_path"] = self.backend_path_var.get()
        self.settings["backend_autostart"] = self.backend_autostart_var.get()   
        self.settings["rpc_enabled"] = self.rpc_enabled_var.get()
        # Update sidebar dynamically
        self.user_lbl.configure(text=self.username_var.get())
        self.email_lbl.configure(text=self.email_var.get())
        
        try:
            with open(CONFIG_PATH, "w") as f:
                json.dump(self.settings, f, indent=4)
        except: pass

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color="#121212")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(8, weight=1)

        # Profile area (Matches original precisely)
        self.profile_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.profile_frame.pack(pady=(20,10), padx=20, fill="x")

        # Avatar circle placeholder
        avatar_canvas = ctk.CTkCanvas(self.profile_frame, width=45, height=45, bg="#121212", highlightthickness=0)
        avatar_canvas.pack(side="left", padx=(0, 10))
        avatar_canvas.create_oval(2, 2, 43, 43, fill="#333333", outline="")
        avatar_canvas.create_text(22, 22, text="S", fill="white", font=("Segoe UI", 16, "bold"))

        info_frame = ctk.CTkFrame(self.profile_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True)

        self.user_lbl = ctk.CTkLabel(info_frame, text=self.settings.get("username", "Ssd"), font=("Segoe UI", 15, "bold"), anchor="w", text_color="#f4f4f5")
        self.user_lbl.pack(fill="x", pady=(2,0))
        self.email_lbl = ctk.CTkLabel(info_frame, text=self.settings.get("email", "ssd@gmail.com"), font=("Segoe UI", 11), text_color="#a1a1aa", anchor="w")
        self.email_lbl.pack(fill="x")

        # Search bar
        search_f = ctk.CTkFrame(self.sidebar, fg_color="#1e1e1e", corner_radius=6, height=35)
        search_f.pack(pady=15, padx=20, fill="x")
        search_f.pack_propagate(False)
        ctk.CTkEntry(search_f, placeholder_text="Find a setting", border_width=0, fg_color="transparent", text_color="#d4d4d8").pack(side="left", fill="both", expand=True, padx=5)

        # Nav Buttons list exactly from screenshot
        self.nav_btns = {}
        nav_items = ["Play", "Host", "Backend", "Info", "Settings"]
        for item in nav_items:
            btn = ctk.CTkButton(self.sidebar, text=f"   {item}", anchor="w", fg_color="transparent", 
                                hover_color="#1e1e1e", font=("Segoe UI", 14), corner_radius=6, height=38,
                                command=lambda n=item: self.show_page(n))
            btn.pack(fill="x", padx=15, pady=2)
            self.nav_btns[item] = btn

    def setup_pages(self):
        self.pages_frame = ctk.CTkFrame(self, fg_color="#0f0f0f", corner_radius=0)
        self.pages_frame.grid(row=0, column=1, sticky="nsew")
        self.pages_frame.grid_rowconfigure(0, weight=1)
        self.pages_frame.grid_columnconfigure(0, weight=1)

        self.pages = {}
        # We loop and create the main pages
        for name in ["Play", "ClientOptions", "Host", "HostInformation", "HostOptions", "HostShare", "Backend", "Info", "Settings", "AccountSettings", "InternalFiles"]:
            f = ctk.CTkScrollableFrame(self.pages_frame, fg_color="transparent")
            self.pages[name] = f
            getattr(self, f"build_{name.lower()}_page")(f)

    def show_page(self, name):
        for page in self.pages.values():
            page.grid_forget()

        # Handle subpages correctly to map back to sidebar parents
        active_nav = name
        if name in ["InternalFiles", "AccountSettings"]:
            active_nav = "Settings"
        elif name in ["ClientOptions"]:
            active_nav = "Play"
        elif name.startswith("Host"):
            active_nav = "Host"

        for n, btn in self.nav_btns.items():
            if n == active_nav:
                btn.configure(fg_color="#1e1e1e") # Active state bg
            else:
                btn.configure(fg_color="transparent")

        self.pages[name].grid(row=0, column=0, sticky="nsew", padx=40, pady=30)
        self.save_config()

        # Update Discord RPC with current tab
        if hasattr(self, 'discord') and self.discord:
            if hasattr(self, 'rpc_enabled_var') and not self.rpc_enabled_var.get():
                self.discord.clear_state()
            else:
                user = self.username_var.get() if hasattr(self, 'username_var') else "PythonPlayer"
                self.discord.update_state(f"Viewing {active_nav} tab", f"Logged in as {user}")

    # --- PAGES ---

    def build_play_page(self, parent):
        ctk.CTkLabel(parent, text="Play", font=("Segoe UI", 32, "bold"), text_color="white", anchor="w").pack(fill="x", pady=(0, 20))
        SettingTile(parent, "Installation directory", "Opens the installation directory", button_text="Browse", show_entry=True, entry_var=self.path_var, button_command=self.browse_game_dir)
        SettingTile(parent, "Client Options", "Override engine arguments", button_text=">", is_subpage=True, button_command=lambda: self.show_page("ClientOptions"))
        
        launch_btn = ctk.CTkButton(parent, text="Play", fg_color="#3b82f6", font=("Segoe UI", 18, "bold"), height=55, hover_color="#2563eb", command=self.handle_launch)
        launch_btn.pack(pady=40, fill="x")

    def build_clientoptions_page(self, parent):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        back_btn = ctk.CTkButton(header, text="<", width=30, fg_color="transparent", font=("Segoe UI", 18), hover_color="#1e1e1e", command=lambda: self.show_page("Play"))
        back_btn.pack(side="left", padx=(0,10))
        ctk.CTkLabel(header, text="Play > Client Options", font=("Segoe UI", 28, "bold"), text_color="white", anchor="w").pack(side="left")

        SettingTile(parent, "Custom arguments", "Overrides the default parameters for Unreal Engine", show_entry=True, entry_var=self.launch_args_var)
        SettingTile(parent, "Reset defaults", "Reset the game client configuration", button_text="Reset")

    def build_host_page(self, parent):
        ctk.CTkLabel(parent, text="Host", font=("Segoe UI", 32, "bold"), text_color="white", anchor="w").pack(fill="x", pady=(0, 20))
        
        SettingTile(parent, "Information", "Provide a name and a description for your game server", button_text=">", is_subpage=True, button_command=lambda: self.show_page("HostInformation"))
        SettingTile(parent, "Server Options", "Configure other options of the game server", button_text=">", is_subpage=True, button_command=lambda: self.show_page("HostOptions"))
        SettingTile(parent, "Share Link", "Share your server with other people online", button_text=">", is_subpage=True, button_command=lambda: self.show_page("HostShare"))
        SettingTile(parent, "Reset to defaults", "Restore the default settings for the game server", button_text="Reset")

        host_btn = ctk.CTkButton(parent, text="Host Server", fg_color="#3b82f6", font=("Segoe UI", 18, "bold"), height=55, hover_color="#2563eb", command=lambda: self.handle_launch(is_host=True))
        host_btn.pack(pady=40, fill="x")

    def build_hostinformation_page(self, parent):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        back_btn = ctk.CTkButton(header, text="<", width=30, fg_color="transparent", font=("Segoe UI", 18), hover_color="#1e1e1e", command=lambda: self.show_page("Host"))
        back_btn.pack(side="left", padx=(0,10))
        ctk.CTkLabel(header, text="Host > Information", font=("Segoe UI", 28, "bold"), text_color="white", anchor="w").pack(side="left")

        SettingTile(parent, "Name", "Type a name for the game server, max 30 characters", show_entry=True, entry_var=self.host_name_var)
        SettingTile(parent, "Description", "Type a description for the game server", show_entry=True, entry_var=self.host_desc_var)
        SettingTile(parent, "Password", "Type a password for the game server, max 30 characters (ignored if not published)", show_entry=True, entry_var=self.host_pass_var)

    def build_hostoptions_page(self, parent):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        back_btn = ctk.CTkButton(header, text="<", width=30, fg_color="transparent", font=("Segoe UI", 18), hover_color="#1e1e1e", command=lambda: self.show_page("Host"))
        back_btn.pack(side="left", padx=(0,10))
        ctk.CTkLabel(header, text="Host > Options", font=("Segoe UI", 28, "bold"), text_color="white", anchor="w").pack(side="left")

        SettingTile(parent, "Custom launch args", "These launch args will be injected to the game process", show_entry=True, entry_var=self.host_custom_args_var)
        SettingTile(parent, "Headless", "Create the game server as a background process", is_switch=True, switch_var=self.host_headless_var)
        SettingTile(parent, "Automatic Restart", "Automatically start the game server on exit", is_switch=True, switch_var=self.host_autorun_var)
        SettingTile(parent, "Game server port", "The port your server uses (Default: 7777)", show_entry=True, entry_var=self.host_port_var)

    def build_hostshare_page(self, parent):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        back_btn = ctk.CTkButton(header, text="<", width=30, fg_color="transparent", font=("Segoe UI", 18), hover_color="#1e1e1e", command=lambda: self.show_page("Host"))
        back_btn.pack(side="left", padx=(0,10))
        ctk.CTkLabel(header, text="Host > Share", font=("Segoe UI", 28, "bold"), text_color="white", anchor="w").pack(side="left")

        SettingTile(parent, "Link", "Copy a link to easily share your game server", button_text="Copy")
        SettingTile(parent, "IP", "Copy your IP to manually share your game server", button_text="Copy")

    def build_backend_page(self, parent):
        ctk.CTkLabel(parent, text="Backend", font=("Segoe UI", 32, "bold"), text_color="white", anchor="w").pack(fill="x", pady=(0, 20))

        SettingTile(parent, "Backend Type", "Choose how the backend is managed", is_option=True, option_var=self.backend_type_var, options_list=["Local", "Remote", "Embedded"])
        
        self.remote_url_tile = SettingTile(parent, "Remote URL", "Address for the remote backend", show_entry=True, entry_var=self.backend_url_var)
        self.backend_path_tile = SettingTile(parent, "Backend executable path", "Executable path to local backend", button_text="Browse", show_entry=True, entry_var=self.backend_path_var, button_command=lambda: self.browse_backend())
        
        self.start_backend_tile = SettingTile(parent, "Start backend", "Run the backend manually or check remote", button_text_var=self.backend_action_text, button_command=self.start_backend)
        self.autostart_backend_tile = SettingTile(parent, "Auto-start backend", "Automatically launch the backend on open", is_switch=True, switch_var=self.backend_autostart_var)

        self.update_backend_action_text()

    def build_info_page(self, parent):
        ctk.CTkLabel(parent, text="Info", font=("Segoe UI", 32, "bold"), text_color="white", anchor="w").pack(fill="x", pady=(0, 20))
        SettingTile(parent, "Project Reboot Python Clone", "A 1:1 recreation of the Reboot Launcher UI.")
        SettingTile(parent, "Version", "Alpha")

    def build_settings_page(self, parent):
        ctk.CTkLabel(parent, text="Settings", font=("Segoe UI", 32, "bold"), text_color="white", anchor="w").pack(fill="x", pady=(0, 20))
        
        SettingTile(parent, "Account options", "Configure your mock username and password", button_text=">", is_subpage=True, button_command=lambda: self.show_page("AccountSettings"))
        SettingTile(parent, "Discord Activity", "Show your status playing Reboot on Discord", is_switch=True, switch_var=self.rpc_enabled_var)
        SettingTile(parent, "Language", "Select the language to use inside the launcher", button_text="English")
        SettingTile(parent, "Theme", "Select the theme to use inside the launcher", button_text="Dark")
        
        # Clicking this navigates to the 'InternalFiles' page, replicating ">" list traversal
        SettingTile(parent, "Internal files", "Configure the internal files used by the launcher", button_text=">", is_subpage=True, button_command=lambda: self.show_page("InternalFiles"))

        SettingTile(parent, "Installation directory", "Opens the installation directory", button_text="Browse", show_entry=True, entry_var=self.path_var, button_command=self.browse_game_dir)

    def build_internalfiles_page(self, parent):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        # Back button
        back_btn = ctk.CTkButton(header, text="<", width=30, fg_color="transparent", font=("Segoe UI", 18), hover_color="#1e1e1e", command=lambda: self.show_page("Settings"))
        back_btn.pack(side="left", padx=(0,10))
        ctk.CTkLabel(header, text="Settings > Internal files", font=("Segoe UI", 28, "bold"), text_color="white", anchor="w").pack(side="left")

        SettingTile(parent, "Unreal engine patcher", "Unlocks the Unreal Engine Console", button_text="Browse", show_entry=True, entry_var=self.dll_console_var, button_command=lambda: self.browse_dll(self.dll_console_var))
        SettingTile(parent, "Authentication patcher", "Redirects all HTTP requests to the backend", button_text="Browse", show_entry=True, entry_var=self.dll_auth_var, button_command=lambda: self.browse_dll(self.dll_auth_var))
        SettingTile(parent, "Memory patcher", "Prevents the client from crashing because of a memory leak", button_text="Browse", show_entry=True, entry_var=self.dll_memory_var, button_command=lambda: self.browse_dll(self.dll_memory_var))
        SettingTile(parent, "Game server", "The file injected to create the game server", button_text="Browse", show_entry=True, entry_var=self.dll_server_var, button_command=lambda: self.browse_dll(self.dll_server_var))

    def build_accountsettings_page(self, parent):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        back_btn = ctk.CTkButton(header, text="<", width=30, fg_color="transparent", font=("Segoe UI", 18), hover_color="#1e1e1e", command=lambda: self.show_page("Settings"))
        back_btn.pack(side="left", padx=(0,10))
        ctk.CTkLabel(header, text="Settings > Account", font=("Segoe UI", 28, "bold"), text_color="white", anchor="w").pack(side="left")

        SettingTile(parent, "Username", "In-game display name", show_entry=True, entry_var=self.username_var)
        SettingTile(parent, "Email", "Account email", show_entry=True, entry_var=self.email_var)
        SettingTile(parent, "Password", "Account password", show_entry=True, entry_var=self.password_var)

        # Host Account settings
        ctk.CTkLabel(parent, text="Host Account", font=("Segoe UI", 20, "bold"), text_color="white", anchor="w").pack(fill="x", pady=(20, 10))
        SettingTile(parent, "Host Username", "In-game display name for host", show_entry=True, entry_var=self.host_username_var)
        SettingTile(parent, "Host Email", "Account email for host", show_entry=True, entry_var=self.host_email_var)
        SettingTile(parent, "Host Password", "Account password for host", show_entry=True, entry_var=self.host_account_password_var)

    # --- ACTION LOGIC ---

    def browse_game_dir(self):
        f = filedialog.askdirectory(title="Select Game Directory (e.g. Fortnite v3.6)")
        if f:
            exe = os.path.join(f, "FortniteGame/Binaries/Win64/FortniteClient-Win64-Shipping.exe").replace("/", os.sep)
            self.path_var.set(exe)
            self.save_config()

    def browse_dll(self, str_var):
        f = filedialog.askopenfilename(filetypes=[("DLL Files", "*.dll")])
        if f:
            str_var.set(f)
            self.save_config()

    def browse_backend(self):
        f = filedialog.askopenfilename(filetypes=[("Executable and Batch Files", "*.exe *.bat"), ("All Files", "*.*")])
        if f:
            self.backend_path_var.set(f)
            self.save_config()

    def start_backend(self):
        backend_type = self.backend_type_var.get()
        if backend_type == "Embedded":
            bpath = self.settings.get("backend_path", "")
            if os.path.exists(bpath):
                dir_name = os.path.dirname(bpath)
                if bpath.lower().endswith(".bat"):
                    subprocess.Popen(["cmd.exe", "/c", bpath], cwd=dir_name, creationflags=subprocess.CREATE_NEW_CONSOLE)
                else:
                    subprocess.Popen([bpath], cwd=dir_name, creationflags=0x08000000)
            else:
                messagebox.showerror("Error", "Embedded backend executable not found.")
        elif backend_type in ["Remote", "Local"]:
            import urllib.request
            import urllib.error
            import threading
            
            if backend_type == "Remote":
                url = self.backend_url_var.get().strip()
                if not url.startswith("http"):
                    url = "http://" + url
            else:
                url = "http://127.0.0.1:3551"
            
            def ping_thread():
                try:
                    response = urllib.request.urlopen(url, timeout=3)
                    self.after(0, lambda: messagebox.showinfo("Success", f"Server is online \nVersion: unknown"))
                except urllib.error.HTTPError as e:
                    # If we get an HTTP error like 404, the server is still reachable.
                    self.after(0, lambda: messagebox.showinfo("Success", f"Server is online \nVersion: unknown"))
                except urllib.error.URLError as e:
                    self.after(0, lambda: messagebox.showerror("Error", f"Failed to reach {backend_type} backend:\n{e.reason}"))
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror("Error", f"Failed to reach {backend_type} backend:\n{e}"))
            
            threading.Thread(target=ping_thread, daemon=True).start()
        else:
            messagebox.showerror("Error", "Backend not found!")

    def set_process_state(self, pid, suspend=True):
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
        if not dll_path or not os.path.exists(dll_path): return False
        try:
            full_path = os.path.abspath(dll_path)
            path_bytes = full_path.encode('ascii') + b'\x00'

            # 0x43A = PROCESS_CREATE_THREAD | PROCESS_VM_OPERATION | PROCESS_VM_WRITE | PROCESS_VM_READ | PROCESS_QUERY_INFORMATION
            h_proc = k32.OpenProcess(0x43A, False, pid)
            if not h_proc: 
                return False

            loc = k32.VirtualAllocEx(h_proc, None, MAX_PATH, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE)
            if not loc:
                k32.CloseHandle(h_proc)
                return False

            bytes_written = c_size_t(0)
            k32.WriteProcessMemory(h_proc, loc, path_bytes, len(path_bytes), byref(bytes_written))

            h_mod = k32.GetModuleHandleA(b"kernel32.dll")
            load_lib_addr = k32.GetProcAddress(h_mod, b"LoadLibraryA")

            h_thread = k32.CreateRemoteThread(h_proc, None, 0, load_lib_addr, loc, 0, None)
            success = False
            if h_thread:
                k32.WaitForSingleObject(h_thread, 0xFFFFFFFF) # INFINITE wait like Dart
                k32.CloseHandle(h_thread)
                success = True

            k32.CloseHandle(h_proc)
            return success
        except: return False

    def handle_launch(self, is_host=False):
        self.save_config()
        exe_path = self.path_var.get()
        if not os.path.exists(exe_path):
            messagebox.showerror("Error", "Game executable not found in path!")
            return

        bin_dir = os.path.dirname(exe_path)
        exe_name = os.path.basename(exe_path)
        if is_host:
            em = self.settings.get("host_email", "hostvprojectreboot.py")
            pw = self.settings.get("host_account_password", "12345678")
            un = self.settings.get("host_username", "Host")
        else:
            em = self.settings.get("email", "playervprojectreboot.py")
            pw = self.settings.get("password", "12345678")
            un = self.settings.get("username", "Player")

        # Arguments logic exactly matched to old codebase args
        # Append email/password to the custom arguments dynamically
        base_args = self.launch_args_var.get()
        if "-AUTH_LOGIN=" not in base_args:
             base_args += f' -AUTH_LOGIN={em} -AUTH_PASSWORD={pw} -AUTH_TYPE=epic'

        if is_host:
             base_args += ' -nosplash -nosound'

             if self.host_headless_var.get():
                 base_args += ' -nullrhi'

             port = self.host_port_var.get()
             if port:
                 base_args += f' -port={port}'

             custom_host_args = self.host_custom_args_var.get()
             if custom_host_args:
                 base_args += ' ' + custom_host_args

             max_players = self.host_max_players_var.get()
             if max_players:
                 base_args += f' -maxplayers={max_players}'

        import shlex
        args_list = shlex.split(base_args)
        launch_cmd = [exe_path] + args_list

        # Use shell=False and stdout=subprocess.PIPE to read log reliably
        proc = subprocess.Popen(
            launch_cmd, 
            cwd=bin_dir, 
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        state_msg = "Hosting Server" if is_host else "Playing Fortnite"
        if hasattr(self, 'rpc_enabled_var') and self.rpc_enabled_var.get():
            display_name = self.host_username_var.get() if is_host else self.username_var.get()
            self.discord.update_state(state_msg, f"Logged in as {display_name}")
        threading.Thread(target=self.monitor_process, args=(proc, is_host,), daemon=True).start()

    def monitor_process(self, proc, is_host):
        target_pid = proc.pid
        
        # 1. IMMEDIATE: Inject Auth right away
        dll_auth = self.dll_auth_var.get()
        if dll_auth and os.path.exists(dll_auth):
            if self.python_injector(target_pid, dll_auth):
                print(f"[+] Early Injection: {os.path.basename(dll_auth)} injected successfully.")
            else:
                print(f"[-] Early Injection failed for {os.path.basename(dll_auth)}.")

        # 2. LOG WATCHER: Wait for login success before injecting late DLLs (MemoryLeak, Console, Server)
        logged_in = False
        
        for line in iter(proc.stdout.readline, ''):
            if not line:
                 break
                 
            # Print to python console so user can see it
            print("[UE4] " + line.strip())
            
            # In Dart, they checked if the line specifically contained ANY of the keywords to know if it logged in
            if not logged_in and ("[UOnlineAccountCommon::ContinueLoggingIn]" in line or "(Completed)" in line):
                logged_in = True
                print("\n[+] Fortnite login completed! Initiating late DLL injections...")
                
                # Late Inject: Memory Leak patch (Usually for Chapter 1)
                dll_memory = self.dll_memory_var.get()
                if dll_memory and os.path.exists(dll_memory):
                    if self.python_injector(target_pid, dll_memory):
                        print(f"[+] Late Injection: {os.path.basename(dll_memory)} injected successfully.")
                    else:
                        print(f"[-] Late Injection failed for {os.path.basename(dll_memory)}.")

                # Late Inject: Console (Play) or Server (Host)
                if is_host:
                    try:
                        import subprocess
                        subprocess.run(f"FOR /F \"tokens=5\" %T IN ('netstat -a -n -o ^| findstr :7777') DO TaskKill.exe /PID %T /F", shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                        print("[+] Ensured port 7777 is clear prior to hosting.")
                    except:
                        pass

                    dll_server = self.dll_server_var.get()
                    if dll_server and os.path.exists(dll_server):
                        if self.python_injector(target_pid, dll_server):
                            print(f"[+] Late Injection: {os.path.basename(dll_server)} injected successfully.")
                        else:
                            print(f"[-] Late Injection failed for {os.path.basename(dll_server)}.")
                else:
                    dll_console = self.dll_console_var.get()
                    if dll_console and os.path.exists(dll_console):
                        if self.python_injector(target_pid, dll_console):
                            print(f"[+] Late Injection: {os.path.basename(dll_console)} injected successfully.")
                        else:
                            print(f"[-] Late Injection failed for {os.path.basename(dll_console)}.")
        # Revert Discord RPC to menu state after game exits
        self.after(500, self.update_discord_rpc_state)
if __name__ == "__main__":
    app = RebootLauncherApp()
    app.mainloop()