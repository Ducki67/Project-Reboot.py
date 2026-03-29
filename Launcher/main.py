import customtkinter as ctk
import sys, os, json, time, threading, psutil, subprocess
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

    def connect(self):
        if HAS_RPC and not self.is_connected:
            try:
                self.rpc = Presence(self.client_id)
                self.rpc.connect()
                self.is_connected = True
            except Exception:
                self.is_connected = False

    def disconnect(self):
        if self.rpc and self.is_connected:
            try:
                self.rpc.clear()
                self.rpc.close()
            except Exception: pass
            self.is_connected = False
            self.rpc = None

    def update_state(self, state, details, large_image="rebootlogo", small_image=None, small_text=None, large_text="Project Reboot"):
        if hasattr(self, 'is_connected') and self.is_connected and self.rpc:
            try:
                btns = [
                    {"label": "Reboot Discord", "url": "https://discord.gg/rebootmp"},
                    {"label": "Launcher src code", "url": "https://github.com/Ducki67/Project-Reboot.py"}
                ]
                kwargs = {
                    "state": state,
                    "details": details,
                    "start": self.start_time,
                    "large_image": large_image,
                    "large_text": large_text,
                    "buttons": btns
                }
                if small_image: kwargs["small_image"] = small_image
                if small_text: kwargs["small_text"] = small_text
                self.rpc.update(**kwargs)
            except Exception as e: print('RPC Error:', e)

    def clear_state(self):
        if hasattr(self, 'is_connected') and self.is_connected and self.rpc:
            try:
                self.rpc.clear()
            except Exception as e: print('RPC Error:', e)

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
        self.title("Reboot.py")
        
        # When compiled, look for assets next to the .exe. When running from Python, look next to main.py
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))
            
        icon_path = os.path.join(self.base_dir, "assets", "icons", "reboot.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)
            
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
        self.backend_port_var = ctk.StringVar(value=self.settings.get("backend_port", "3551"))
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
            if getattr(self, 'game_running', False):
                return
            if self.rpc_enabled_var.get():
                self.discord.connect()
                self.discord.update_state("In Launcher", "Browsing menus")      
            else:
                self.discord.disconnect()

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
                self.local_port_tile.pack_forget()
                self.backend_path_tile.pack_forget()
                self.start_backend_tile.pack_forget()
                self.autostart_backend_tile.pack_forget()
                
                # Then pack in correct order based on type
                if btype == "Remote":
                    self.remote_url_tile.pack(fill="x", pady=6)
                elif btype == "Local":
                    self.local_port_tile.pack(fill="x", pady=6)
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
            except Exception as e: print('RPC Error:', e)

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
        self.settings["backend_port"] = self.backend_port_var.get()
        self.settings["backend_path"] = self.backend_path_var.get()
        self.settings["backend_autostart"] = self.backend_autostart_var.get()   
        self.settings["rpc_enabled"] = self.rpc_enabled_var.get()
        # Update sidebar dynamically
        self.user_lbl.configure(text=self.username_var.get())
        self.email_lbl.configure(text=self.email_var.get())
        
        try:
            with open(CONFIG_PATH, "w") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e: print('RPC Error:', e)

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color="#121212")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(8, weight=1)

        # Profile area (Matches original precisely)
        self.profile_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.profile_frame.pack(pady=(20,10), padx=20, fill="x")

        # Avatar (user.png if available, else placeholder)
        user_img_path = os.path.join(self.base_dir, "assets", "images", "user.png")
        if HAS_PIL and os.path.exists(user_img_path):
            user_image = ctk.CTkImage(light_image=Image.open(user_img_path), size=(45, 45))
            avatar_lbl = ctk.CTkLabel(self.profile_frame, text="", image=user_image)
            avatar_lbl.pack(side="left", padx=(0, 10))
        else:
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
        nav_items = ["Play", "Download", "Host", "Backend", "Info", "Settings"]
        for item in nav_items:
            img_path = os.path.join(self.base_dir, "assets", "images", f"{item.lower()}.png")
            if HAS_PIL and os.path.exists(img_path):
                btn_img = ctk.CTkImage(light_image=Image.open(img_path), size=(20, 20))
                btn = ctk.CTkButton(self.sidebar, text=f"  {item}", image=btn_img, anchor="w", fg_color="transparent", 
                                    hover_color="#1e1e1e", font=("Segoe UI", 14), corner_radius=6, height=38,
                                    command=lambda n=item: self.show_page(n))
            else:
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
        for name in ["Play", "Download", "ClientOptions", "Host", "HostInformation", "HostOptions", "HostShare", "Backend", "Info", "Settings", "AccountSettings", "InternalFiles"]:
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
            elif not getattr(self, 'game_running', False):
                user = self.username_var.get() if hasattr(self, 'username_var') else "PythonPlayer"
                self.discord.update_state(f"Viewing {active_nav} tab", f"Logged in as {user}")

    # --- PAGES ---

    def build_play_page(self, parent):
        ctk.CTkLabel(parent, text="Play", font=("Segoe UI", 32, "bold"), text_color="white", anchor="w").pack(fill="x", pady=(0, 20))
        SettingTile(parent, "Installation directory", "Opens the installation directory", button_text="Browse", show_entry=True, entry_var=self.path_var, button_command=self.browse_game_dir)
        SettingTile(parent, "Client Options", "Override engine arguments", button_text=">", is_subpage=True, button_command=lambda: self.show_page("ClientOptions"))
        
        self.launch_btn = ctk.CTkButton(parent, text="Play", fg_color="#3b82f6", font=("Segoe UI", 18, "bold"), height=55, hover_color="#2563eb", command=self.handle_launch)
        self.launch_btn.pack(pady=40, fill="x")

    def build_download_page(self, parent):
        ctk.CTkLabel(parent, text="Download Builds", font=("Segoe UI", 32, "bold"), text_color="white", anchor="w").pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(parent, text="Note: Links only work up to v10.31! Newer versions will not download.", text_color="#ef4444", anchor="w").pack(fill="x", pady=(0, 5))

        controls_frame = ctk.CTkFrame(parent, fg_color="transparent")
        controls_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(controls_frame, text="Sort By:", text_color="#a1a1aa", font=("Segoe UI", 14)).pack(side="left", padx=(0, 10))
        sort_var = ctk.StringVar(value="Oldest to Latest (Low - High)")
        
        view_var = ctk.StringVar(value="List View")
        
        self.downloads_container = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self.downloads_container.pack(fill="both", expand=True)

        loading_lbl = ctk.CTkLabel(self.downloads_container, text="Loading versions...", text_color="#a1a1aa")
        loading_lbl.pack(pady=20)
        
        data_result = {}
        error_result = []
        
        def fetch_versions():
            try:
                import urllib.request
                req = urllib.request.Request('https://builds.rebootfn.org/versions.json', headers={'User-Agent': 'Mozilla/5.0'})
                data = json.loads(urllib.request.urlopen(req).read())
                data_result['data'] = data
            except Exception as e:
                error_result.append(str(e))
                
        def get_version_tuple(url):
            import urllib.parse
            filename = url.split('/')[-1]
            filename = urllib.parse.unquote(filename)
            version_str = filename.replace('.zip','').replace('.rar','').replace('vFortnite ', '').replace('vFortnite', '').replace('Fortnite ', '').replace('Fortnite', '').strip()
            return tuple(int(x) for x in version_str.split('.') if x.isdigit())

        def render_versions(*args):
            # Show a busy cursor or hide the container temporarily
            self.downloads_container.pack_forget()
            
            # Clear container first
            for widget in self.downloads_container.winfo_children():
                widget.destroy()
                
            versions = data_result.get('data', [])
            if not versions:
                self.downloads_container.pack(fill="both", expand=True)
                return
                
            sort_order = sort_var.get()
            view_mode = view_var.get()
            
            # Sort the versions based on the option menu
            is_descending = ("High - Low" in sort_order)
            sorted_versions = sorted(versions, key=get_version_tuple, reverse=is_descending)
            
            # If Blocks view, configure columns
            columns = 3
            if view_mode == "Blocks View":
                for i in range(columns):
                    self.downloads_container.grid_columnconfigure(i, weight=1)
            else:
                self.downloads_container.grid_columnconfigure((0, 1, 2), weight=0)

            for idx, url in enumerate(sorted_versions):
                import urllib.parse
                filename = url.split('/')[-1]
                filename = urllib.parse.unquote(filename)
                version_str = filename.replace('.zip','').replace('.rar','').replace('vFortnite ', '').replace('vFortnite', '').replace('Fortnite ', '').replace('Fortnite', '').strip()
                
                parts = get_version_tuple(url)
                is_valid = True
                if parts:
                    if parts[0] > 10 or (parts[0] == 10 and len(parts) > 1 and parts[1] > 31):
                        is_valid = False

                tile_frame = ctk.CTkFrame(self.downloads_container, fg_color="#1E1E1E", corner_radius=8)
                
                import webbrowser
                def make_cmd(u=url): return lambda: webbrowser.open(u)
                
                if view_mode == "List View":
                    tile_frame.pack(fill="x", pady=4, padx=5)
                    
                    lbl = ctk.CTkLabel(tile_frame, text=f"Version {version_str}", font=("Segoe UI", 15, "bold"), text_color="white" if is_valid else "#52525b")
                    lbl.pack(side="left", padx=15, pady=15)
                    
                    if is_valid:
                        btn = ctk.CTkButton(tile_frame, text="Download", width=100, fg_color="#2563eb", hover_color="#1d4ed8", command=make_cmd())
                        btn.pack(side="right", padx=15)
                    else:
                        btn = ctk.CTkButton(tile_frame, text="Unsupported", width=100, fg_color="#3f3f46", hover_color="#3f3f46", state="disabled")
                        btn.pack(side="right", padx=15)
                else:
                    # Blocks View
                    r = idx // columns
                    c = idx % columns
                    tile_frame.grid(row=r, column=c, padx=5, pady=5, sticky="nsew")
                    
                    lbl = ctk.CTkLabel(tile_frame, text=f"v{version_str}", font=("Segoe UI", 18, "bold"), text_color="white" if is_valid else "#52525b")
                    lbl.pack(pady=(15, 5))
                    
                    if is_valid:
                        btn = ctk.CTkButton(tile_frame, text="Download", width=100, fg_color="#2563eb", hover_color="#1d4ed8", command=make_cmd())
                        btn.pack(pady=(5, 15))
                    else:
                        btn = ctk.CTkButton(tile_frame, text="Unsupported", width=100, fg_color="#3f3f46", hover_color="#3f3f46", state="disabled")
                        btn.pack(pady=(5, 15))

            self.downloads_container.pack(fill="both", expand=True)

        def check_data():
            if 'data' in data_result:
                render_versions()
            elif error_result:
                loading_lbl.configure(text=f"Failed to load versions: {error_result[0]}")
            else:
                self.after(100, check_data)

        sort_menu = ctk.CTkOptionMenu(controls_frame, variable=sort_var, values=["Latest to Oldest (High - Low)", "Oldest to Latest (Low - High)"], command=render_versions, fg_color="#1e1e1e", button_color="#252526", button_hover_color="#2d2d30")
        sort_menu.pack(side="left")
        
        view_toggle = ctk.CTkSegmentedButton(controls_frame, values=["List View", "Blocks View"], variable=view_var, command=render_versions, selected_color="#2563eb", unselected_color="#1e1e1e")
        view_toggle.pack(side="right", padx=(10, 0))

        threading.Thread(target=fetch_versions, daemon=True).start()
        self.after(100, check_data)

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

        self.host_btn = ctk.CTkButton(parent, text="Host Server", fg_color="#3b82f6", font=("Segoe UI", 18, "bold"), height=55, hover_color="#2563eb", command=lambda: self.handle_launch(is_host=True))
        self.host_btn.pack(pady=40, fill="x")

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
        self.local_port_tile = SettingTile(parent, "Local Port", "Port of the local backend", show_entry=True, entry_var=self.backend_port_var)
        self.backend_path_tile = SettingTile(parent, "Backend executable path", "Executable path to local backend", button_text="Browse", show_entry=True, entry_var=self.backend_path_var, button_command=lambda: self.browse_backend())
        
        self.start_backend_tile = SettingTile(parent, "Start backend", "Run the backend manually or check remote", button_text_var=self.backend_action_text, button_command=self.start_backend)
        self.autostart_backend_tile = SettingTile(parent, "Auto-start backend", "Automatically launch the backend on open", is_switch=True, switch_var=self.backend_autostart_var)

        self.update_backend_action_text()

    def build_info_page(self, parent):
        ctk.CTkLabel(parent, text="Info", font=("Segoe UI", 32, "bold"), text_color="white", anchor="w").pack(fill="x", pady=(0, 20))
        
        info_frame = ctk.CTkFrame(parent, fg_color="#1E1E1E", corner_radius=10)
        info_frame.pack(fill="x", pady=5)
        
        # Banner/Header area inside the info frame
        ctk.CTkLabel(info_frame, text="Reboot.py", font=("Segoe UI", 24, "bold"), text_color="#3b82f6").pack(pady=(20, 5))
        ctk.CTkLabel(info_frame, text="The most lightweight way to play legacy Fortnite.", font=("Segoe UI", 12), text_color="#a1a1aa").pack(pady=(0, 20))
        
        import webbrowser
        def open_discord(): webbrowser.open("https://discord.gg/rebootmp")
        def open_github(): webbrowser.open("https://github.com/Project-Reboot")
        
        btn_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        btn_frame.pack(pady=(0, 20))
        
        ctk.CTkButton(btn_frame, text="Discord", fg_color="#5865F2", hover_color="#4752C4", width=120, command=open_discord).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="GitHub", fg_color="#333333", hover_color="#222222", width=120, command=open_github).pack(side="left", padx=10)

        # Tiles matching Reboot aesthetic
        SettingTile(parent, "Project Reboot Python Clone", "A completely native 1:1 recreation of the original Reboot Launcher.", button_text="Read")
        SettingTile(parent, "Version", "Release - v1.0", button_text="Check for updates")
        SettingTile(parent, "Special Thanks", "To the amazing community of developers enabling legacy gameplay.", button_text="Contributors")
        
        ctk.CTkLabel(parent, text="Reboot.py is not affiliated with Epic Games.\npowered by CustomTkinter.", text_color="#52525b", font=("Segoe UI", 11)).pack(side="bottom", pady=40)

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
                port = self.backend_port_var.get().strip()
                url = f"http://127.0.0.1:{port}"
            
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

    def get_game_version(self, exe_path):
        build, cl = "Unknown", "Unknown"
        try:
            import win32api
            lang, codepage = win32api.GetFileVersionInfo(exe_path, '\\VarFileInfo\\Translation')[0]
            strInfo = u'\\StringFileInfo\\%04X%04X\\%s' % (lang, codepage, "ProductVersion")
            prod = win32api.GetFileVersionInfo(exe_path, strInfo)
            cl = prod.split('-')[1].split('+')[0]
            build = prod.split('Release-')[1]
            return build, cl
        except Exception: pass
        try:
            import re
            with open(exe_path, 'rb') as f:
                data = f.read(1000000) # Read only first MBs as fallback
                data_no_nulls = data.replace(b'\x00', b'')
                match = re.search(rb'\d+\.\d+\.\d+-(\d+)\+\+\+Fortnite\+Release-([a-zA-Z0-9\.]+)', data_no_nulls)
                if match: return match.group(2).decode('utf-8'), match.group(1).decode('utf-8')
        except Exception: pass
        return build, cl

    def patch_headless(self, exe_path):
        import mmap
        orig_bytes = bytes([45, 0, 105, 0, 110, 0, 118, 0, 105, 0, 116, 0, 101, 0, 115, 0, 101, 0, 115, 0, 115, 0, 105, 0, 111, 0, 110, 0, 32, 0, 45, 0, 105, 0, 110, 0, 118, 0, 105, 0, 116, 0, 101, 0, 102, 0, 114, 0, 111, 0, 109, 0, 32, 0, 45, 0, 112, 0, 97, 0, 114, 0, 116, 0, 121, 0, 95, 0, 106, 0, 111, 0, 105, 0, 110, 0, 105, 0, 110, 0, 102, 0, 111, 0, 95, 0, 116, 0, 111, 0, 107, 0, 101, 0, 110, 0, 32, 0, 45, 0, 114, 0, 101, 0, 112, 0, 108, 0, 97, 0, 121, 0])
        patched_bytes = bytes([45, 0, 108, 0, 111, 0, 103, 0, 32, 0, 45, 0, 110, 0, 111, 0, 115, 0, 112, 0, 108, 0, 97, 0, 115, 0, 104, 0, 32, 0, 45, 0, 110, 0, 111, 0, 115, 0, 111, 0, 117, 0, 110, 0, 100, 0, 32, 0, 45, 0, 110, 0, 117, 0, 108, 0, 108, 0, 114, 0, 104, 0, 105, 0, 32, 0, 45, 0, 117, 0, 115, 0, 101, 0, 111, 0, 108, 0, 100, 0, 105, 0, 116, 0, 101, 0, 109, 0, 99, 0, 97, 0, 114, 0, 100, 0, 115, 0, 32, 0, 32, 0, 32, 0, 32, 0, 32, 0, 32, 0, 32, 0])
        try:
            with open(exe_path, 'r+b') as f:
                mm = mmap.mmap(f.fileno(), 0)
                pos = mm.find(orig_bytes)
                if pos != -1:
                    print(f"[*] Applying game executable headless byte-patch to {exe_path}...")
                    mm.seek(pos)
                    mm.write(patched_bytes)
                    mm.flush()
                mm.close()
        except Exception as e:
            print(f"[-] Could not patch headless mode binary: {e}")

    def handle_launch(self, is_host=False):
        # Stop process if already running
        if is_host:
            if hasattr(self, 'host_process') and self.host_process and self.host_process.poll() is None:
                self.host_process.kill()
                return
        else:
            if hasattr(self, 'game_process') and self.game_process and self.game_process.poll() is None:
                self.game_process.kill()
                return

        self.save_config()
        exe_path = self.path_var.get()
        if not os.path.exists(exe_path):
            messagebox.showerror("Error", "Game executable not found in path!")
            return

        bin_dir = os.path.dirname(exe_path)
        exe_name = os.path.basename(exe_path)

        # Remove Aftermath crash DLL if it exists
        aftermath_dll = os.path.join(bin_dir, "GFSDK_Aftermath_Lib.x64.dll")
        if os.path.exists(aftermath_dll):
            try:
                os.remove(aftermath_dll)
                print(f"[+] Deleted {aftermath_dll} to prevent game server crashes.")
            except Exception as e:
                print(f"[-] Could not delete {aftermath_dll}: {e}")

        if is_host:
            if self.host_headless_var.get():
                self.patch_headless(exe_path)
            
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
            bufsize=1,
            encoding='utf-8',
            errors='replace'
        )

        if is_host:
            self.host_process = proc
            if hasattr(self, 'host_btn'):
                self.host_btn.configure(text="Stop Server", fg_color="#ef4444", hover_color="#dc2626")
        else:
            self.game_process = proc
            if hasattr(self, 'launch_btn'):
                self.launch_btn.configure(text="Stop Client", fg_color="#ef4444", hover_color="#dc2626")

        # Determine the precise discord running state
        is_headless = self.host_headless_var.get() if hasattr(self, 'host_headless_var') else False
        
        if is_host and is_headless:
            state_msg = "Running GameServer host"
        elif is_host and not is_headless:
            state_msg = "Running: Client and GameServer"
        else:
            state_msg = "Running Client"
            
        self.game_running = True

        if hasattr(self, 'rpc_enabled_var') and self.rpc_enabled_var.get():
            display_name = self.host_username_var.get() if is_host else self.username_var.get()
            
            # Fetch Build and CL
            build_ver, cl_ver = self.get_game_version(exe_path)
            large_text = "Project Reboot"
            if build_ver != "Unknown":
                large_text = f"Build: {build_ver} | CL: {cl_ver}"
                
            self.discord.update_state(
                state=state_msg,
                details=f"Logged in as {display_name}",
                large_image="fortnitelogo",
                small_image="rebootlogo",
                small_text="Reboot.py",
                large_text=large_text
            )
            
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
        
        try:
            for line in iter(proc.stdout.readline, ''):
                if not line:
                    break
                
                print("[UE4] " + line.strip())

                # In Dart, they checked if the line specifically contained ALL keywords to know if it logged in
                if not logged_in and ("[UOnlineAccountCommon::ContinueLoggingIn]" in line and "(Completed)" in line):
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
                                
        except Exception as e:
            print(f"[-] Error parsing log stream: {e}")

        # Revert Visuals and Discord RPC to menu state after game exits
        if is_host:
            self.host_process = None
            if hasattr(self, 'host_btn'):
                self.host_btn.configure(text="Host Server", fg_color="#3b82f6", hover_color="#2563eb")
        else:
            self.game_process = None
            if hasattr(self, 'launch_btn'):
                self.launch_btn.configure(text="Play", fg_color="#3b82f6", hover_color="#2563eb")

        # Determine if any game processes are still actively running
        any_running = False
        if hasattr(self, 'host_process') and self.host_process and self.host_process.poll() is None:
            any_running = True
        if hasattr(self, 'game_process') and self.game_process and self.game_process.poll() is None:
            any_running = True
            
        if not any_running:
            self.game_running = False
            self.after(500, self.update_discord_rpc_state)
            
if __name__ == "__main__":
    app = RebootLauncherApp()
    app.mainloop()