import customtkinter as ctk
import sys, os, json, time, threading, psutil, subprocess, re, zipfile, urllib.request
from ctypes import *
from ctypes import wintypes
from tkinter import filedialog, messagebox
import http.server, urllib.error, urllib.parse, configparser

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

k32   = WinDLL('kernel32', use_last_error=True)
ntdll = WinDLL('ntdll',   use_last_error=True)
ntdll.NtSuspendProcess.restype  = wintypes.LONG
ntdll.NtSuspendProcess.argtypes = [wintypes.HANDLE]
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
    "builds": [],
    "dll_console": os.path.join(os.getcwd(), "dlls", "console.dll"),
    "dll_auth": os.path.join(os.getcwd(), "dlls", "Tellurium.dll"),
    "dll_memory": os.path.join(os.getcwd(), "dlls", "memory.dll"),
    "dll_server": os.path.join(os.getcwd(), "dlls", "reboot.dll"),
    "dll_auth_choice": "Tellurium 3551",
    "dll_console_choice": "Console",
    "dll_server_choice": "Reboot",
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
    "launch_args": "-epicapp=Fortnite -epicenv=Prod -epiclocale=en-us -epicportal -skippatchcheck -nobe -fromfl=eac -fltoken=3db3ba5dcbd2e16703f3978d -caldera=eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2NvdW50X2lkIjoiYmU5ZGE1YzJmYmVhNDQwN2IyZjQwZWJhYWQ4NTlhZDQiLCJnZW5lcmF0ZWQiOjE2Mzg3MTcyNzgsImNhbGRlcmFHdWlkIjoiMzgxMGI4NjMtMmE2NS00NDU3LTliNTgtNGRhYjNiNDgyYTg2IiwiYWNQcm92aWRlciI6IkVhc3lBbnRpQ2hlYXQiLCJub3RlcyI6IiIsImZhbGxiYWNrIjpmYWxzZX0.VAWQB67RTxhiWOxx7DBjnzDnXyyEnX7OljJm-j2d88G_WgwQ9wrE6lwMEHZHjBd1ISJdUO1UVUqkfLdU5nofBQ",
    "rpc_enabled": True,
    "dll_large_pak": "",
    "use_large_pak": False,
    "theme": "Dark"
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
class SettingTile(ctk.CTkFrame):
    def __init__(self, parent, title, subtitle, button_text=None, button_command=None, show_entry=False, entry_var=None, is_subpage=False, is_switch=False, switch_var=None, is_option=False, option_var=None, options_list=None, button_text_var=None):
        super().__init__(parent, fg_color="transparent")
        self.pack(fill="x", pady=6)

        container = ctk.CTkFrame(self, fg_color=_T["tile"], corner_radius=5, height=78)
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
            opt = ctk.CTkOptionMenu(container, variable=option_var, values=options_list, fg_color=_T["muted"], button_color=_T["muted_hover"], button_hover_color=_T["muted_deep"], dropdown_fg_color=_T["muted"], width=120)
            opt.pack(side="right", padx=(0, 20))
        elif button_text or button_text_var:
            btn_width = 120
            btn_color = _T["muted"]
            btn_hover = _T["muted_hover"]
            if button_text == "Toggle":
                btn_color = _T["accent"]
                btn_hover = _T["accent_hover"]
            if is_subpage:
                btn_width = 40
                btn_color = "transparent"
                btn_hover = _T["nav_active"]

            btn = ctk.CTkButton(container, text=button_text if not button_text_var else button_text_var.get(), fg_color=btn_color, hover_color=btn_hover, text_color="white", font=("Segoe UI", 13, "bold"), width=btn_width, height=34, corner_radius=4, command=button_command)
            if button_text_var:
                btn.configure(textvariable=button_text_var)
            btn.pack(side="right", padx=(0, 20))

        if show_entry and entry_var is not None:
             ent = ctk.CTkEntry(container, fg_color=_T["tile_deep"], border_width=1, border_color=_T["border"], text_color="#ffffff", font=("Segoe UI", 13), height=34, corner_radius=4, textvariable=entry_var)
             ent.pack(side="right", fill="x", expand=True, padx=(20, 20))

# --- REBOOT CONSTANTS ---
# Newer builds (Ch4+, S20+) emit "LogOnline: Region " after login completes.
_LOGGED_IN_LINES   = ["[UOnlineAccountCommon::ContinueLoggingIn]", "(Completed)"]
_LOGGED_IN_REGION  = "LogOnline: Region "
_SHUTDOWN_LINE     = "FOnlineSubsystemGoogleCommon::Shutdown()"
_CORRUPTED_ERRORS  = ["Critical error", "when 0 bytes remain", "Pak chunk signature", "LogWindows:Error: Fatal error!"]
_CONNECT_ERRORS    = ["port 3551 failed: Connection refused", "Unable to login to Fortnite servers", "UOnlineAccountCommon::ForceLogout"]
_MATCH_END_LINE    = "TeamsLeft: 1"
_LAUNCHER_EXE      = "FortniteLauncher.exe"
_EAC_EXE           = "FortniteClient-Win64-Shipping_EAC.exe"
_REBOOT_DELAY_SECS = 10

_RPC_EXACT = {
    "18.30": "ch2s8_1830",   "18.40": "ch2s8_1840",
    "20.20": "ch3s2_2020",
    "21.00": "ch3s3_2100",   "21.40": "ch3s3_2140",
    "22.00": "ch3s4_2200",   "22.30": "ch3s4_2230",   "22.40": "ch3s4_2240",
    "23.10": "ch4s1_2310",
    "24.30": "ch4s2_2430",
    "25.20": "ch4s3_2520",
    "28.00": "ch5s1_2800",
    "29.40": "ch5s2_2940",
}

_RPC_MAJOR = {
    1:  "season1_to_season4",   2:  "season1_to_season4",
    3:  "season1_to_season4",   4:  "season1_to_season4",
    5:  "season5",
    12: "ch2s2",
    13: "chap2s3",
    14: "chap2s4",
    17: "chap2s7",
    18: "ch2s8",        # all Ch2S8 builds (18.30 and 18.40 have exact assets above)
    20: "ch3s2_20xx",   # all other Ch3S2 builds (not 20.20)
    21: "ch3s3",        # all Ch3S3 builds (21.00 and 21.40 have exact assets above)
    22: "ch3s4",        # all Ch3S4 builds (22.00, 22.30, 22.40 have exact assets above)
    23: "ch4s1",        # all Ch4S1 builds (23.10 has exact asset above)
    24: "ch4s2",        # all other Ch4S2 builds (not 24.30)
    25: "ch4s3",        # all other Ch4S3 builds (not 25.20)
    26: "ch4s4",
    27: "s27",
    28: "ch5s1",        # all other Ch5S1 builds (not 28.00)
    29: "ch5s2",        # all other Ch5S2 builds (not 29.40)
    30: "ch5s3",
}

def _rpc_image(build_ver: str) -> str:
    """Return the best-matching Discord RPC asset key for a given build version string."""
    if not build_ver or build_ver == "Unknown":
        return "fortnite_noseason"
    clean = re.sub(r'[-_]CL[-_]\d+', '', build_ver).strip().strip('-').strip()
    if clean in _RPC_EXACT:
        return _RPC_EXACT[clean]
    try:
        major = int(clean.split('.')[0])
        if major in _RPC_MAJOR:
            return _RPC_MAJOR[major]
    except Exception:
        pass
    return "fortnite_noseason"

_DLL_BASE_URL        = "https://github.com/Auties00/reboot_launcher/raw/master/gui/dependencies/dlls/"
_COBALT_URL          = _DLL_BASE_URL + "cobalt.dll"
_TELLURIUM_URL       = "http://r2.ploosh.dev/Tellurium.dll"
_REBOOT_DLL_URL      = "https://nightly.link/Milxnor/Project-Reboot-3.0/workflows/msbuild/master/Reboot.zip" # credits to Milxnor <3
_ERBIUM_URL          = "https://nightly.link/plooshi/Erbium/workflows/Build/main/Erbium.zip" # credits to plooshi <3
_ERBIUM_CLIENT_URL   = "https://nightly.link/plooshi/Erbium/workflows/Build/main/ErbiumClient.zip" # credits to plooshi <3
_LARGE_PAK_URL       = "https://raw.githubusercontent.com/cipherfps/ATLAS-Link/main/atlas_link_flutter/assets/dlls/LargePakPatch.dll" # credits to cipher <3

_DLL_AUTH_PRESETS = {
    "Cobalt":              ("cobalt.dll",              None,              _COBALT_URL,     False),
    "Tellurium 3551":      ("Tellurium.dll",            None,              _TELLURIUM_URL,  False),
    "Tellurium Push 3551": ("Tellurium.dll",            None,              _TELLURIUM_URL,  False),
}
_DLL_CONSOLE_PRESETS = {
    "Console":       ("console.dll",     None,              None,              False),
    "Erbium Client": ("ErbiumClient.dll", _ERBIUM_CLIENT_URL, None,             False),
}
_DLL_SERVER_PRESETS = {
    "Reboot": ("reboot.dll", _REBOOT_DLL_URL, None, False),
    "Erbium":  ("Erbium.dll", _ERBIUM_URL,     None, False),
}

_THEMES = {
    "Dark": {
        "bg": "#0b0b0b", "sidebar": "#121212", "content": "#0f0f0f",
        "tile": "#181818", "tile_deep": "#0e0e0e", "border": "#333333",
        "nav_active": "#1e1e1e", "muted": "#2d2d2d", "muted_hover": "#3d3d3d",
        "muted_deep": "#4d4d4d", "accent": "#3b82f6", "accent_hover": "#2563eb",
        "text": "#f4f4f5", "subtext": "#a1a1aa",
    },
    "Midnight": {
        "bg": "#05080f", "sidebar": "#0a0f1c", "content": "#080c18",
        "tile": "#0f1628", "tile_deep": "#0a0f1c", "border": "#1e3058",
        "nav_active": "#152040", "muted": "#1e3058", "muted_hover": "#263870",
        "muted_deep": "#2e4088", "accent": "#60a5fa", "accent_hover": "#3b82f6",
        "text": "#e2e8ff", "subtext": "#8da8d8",
    },
    "Storm": {
        "bg": "#080612", "sidebar": "#100d1e", "content": "#0c0a18",
        "tile": "#181428", "tile_deep": "#100d1e", "border": "#3b1f6b",
        "nav_active": "#241550", "muted": "#2d1f54", "muted_hover": "#3d2a70",
        "muted_deep": "#4d358c", "accent": "#a855f7", "accent_hover": "#9333ea",
        "text": "#f0ebff", "subtext": "#b09ad4",
    },
    "Chapter 1": {
        "bg": "#0a0800", "sidebar": "#130f00", "content": "#0e0b00",
        "tile": "#1c1700", "tile_deep": "#130f00", "border": "#503a00",
        "nav_active": "#2e2300", "muted": "#352a00", "muted_hover": "#453600",
        "muted_deep": "#554200", "accent": "#f59e0b", "accent_hover": "#d97706",
        "text": "#fffbeb", "subtext": "#c9a850",
    },
    "Battle Bus": {
        "bg": "#090900", "sidebar": "#111100", "content": "#0d0d00",
        "tile": "#1a1900", "tile_deep": "#111100", "border": "#4a4800",
        "nav_active": "#2c2b00", "muted": "#353400", "muted_hover": "#454300",
        "muted_deep": "#555200", "accent": "#fbbf24", "accent_hover": "#f59e0b",
        "text": "#fefce8", "subtext": "#c8b460",
    },
    "Tilted Towers": {
        "bg": "#0e0500", "sidebar": "#180800", "content": "#120600",
        "tile": "#220e00", "tile_deep": "#180800", "border": "#6b2200",
        "nav_active": "#3d1200", "muted": "#4d1800", "muted_hover": "#5d2000",
        "muted_deep": "#6d2800", "accent": "#f97316", "accent_hover": "#ea580c",
        "text": "#fff7ed", "subtext": "#d08860",
    },
    "Neo Tilted": {
        "bg": "#001414", "sidebar": "#001c1c", "content": "#001818",
        "tile": "#002424", "tile_deep": "#001c1c", "border": "#006666",
        "nav_active": "#003838", "muted": "#003d3d", "muted_hover": "#004d4d",
        "muted_deep": "#005d5d", "accent": "#06b6d4", "accent_hover": "#0891b2",
        "text": "#ecfeff", "subtext": "#67c8d8",
    },
    "Zero Point": {
        "bg": "#020a12", "sidebar": "#050f1a", "content": "#040d16",
        "tile": "#091624", "tile_deep": "#050f1a", "border": "#1a4a70",
        "nav_active": "#0f2a44", "muted": "#163550", "muted_hover": "#1e4060",
        "muted_deep": "#264b70", "accent": "#22d3ee", "accent_hover": "#06b6d4",
        "text": "#e0f8ff", "subtext": "#6bbad4",
    },
}
_T = dict(_THEMES["Dark"])

_proxy_server = None


def _parse_username(username):
    """Strip non-alphanumeric chars."""
    return re.sub(r'[^a-zA-Z0-9]', '', username) or "Player"


def _build_args(username, password, host, headless, custom_args=""):
    """Build launch args with case-insensitive deduplication."""
    if not password:
        username = f"{_parse_username(username)}@projectreboot.dev"
    password = password if password else "Rebooted"

    args = {}
    def _set(key, val=""):
        args[key.upper()] = (key, val)

    _set("-epicapp", "Fortnite")
    _set("-epicenv", "Prod")
    _set("-epiclocale", "en-us")
    _set("-epicportal")
    _set("-skippatchcheck")
    _set("-nobe")
    _set("-fromfl", "eac")
    _set("-fltoken", "3db3ba5dcbd2e16703f3978d")
    _set("-caldera", "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2NvdW50X2lkIjoiYmU5ZGE1YzJmYmVhNDQwN2IyZjQwZWJhYWQ4NTlhZDQiLCJnZW5lcmF0ZWQiOjE2Mzg3MTcyNzgsImNhbGRlcmFHdWlkIjoiMzgxMGI4NjMtMmE2NS00NDU3LTliNTgtNGRhYjNiNDgyYTg2IiwiYWNQcm92aWRlciI6IkVhc3lBbnRpQ2hlYXQiLCJub3RlcyI6IiIsImZhbGxiYWNrIjpmYWxzZX0.VAWQB67RTxhiWOxx7DBjnzDnXyyEnX7OljJm-j2d88G_WgwQ9wrE6lwMEHZHjBd1ISJdUO1UVUqkfLdU5nofBQ")
    _set("-AUTH_LOGIN", username)
    _set("-AUTH_PASSWORD", password)
    _set("-AUTH_TYPE", "epic")

    if host:
        _set("-nosplash")
        _set("-nosound")
        if headless:
            _set("-nullrhi")

    for token in custom_args.split():
        sep = token.find("=")
        if sep != -1:
            k, v = token[:sep], token[sep+1:]
        else:
            k, v = token, ""
        _set(k, v)

    result = []
    for (k, v) in args.values():
        result.append(f"{k}={v}" if v else k)
    return result


def _kill_port(port):
    """Kill any process listening on the given TCP port."""
    try:
        r = subprocess.run(['netstat', '-ano', '-p', 'TCP'], capture_output=True, text=True)
        for line in r.stdout.splitlines():
            if f':{port} ' in line or f':{port}\t' in line:
                parts = line.split()
                pid = parts[-1] if parts else "0"
                if pid.isdigit() and int(pid) > 4:
                    subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
    except Exception as e:
        print(f"[-] kill_port({port}): {e}")


def _nt_suspend_process(pid):
    """Atomically suspend every thread in a process via NtSuspendProcess)."""
    PROCESS_SUSPEND_RESUME = 0x0800
    h = k32.OpenProcess(PROCESS_SUSPEND_RESUME, False, pid)
    if not h:
        return False
    try:
        ntdll.NtSuspendProcess(h)
        return True
    except Exception:
        return False
    finally:
        k32.CloseHandle(h)


def _find_exe(directory, exe_name):
    """Recursively find an exe in a directory tree."""
    for root, _, files in os.walk(directory):
        for f in files:
            if f.lower() == exe_name.lower():
                return os.path.join(root, f)
    return None


def _write_matchmaker_config(base_dir, ip, port):
    """Write game server IP/port to assets/backend/Config/config.ini."""
    config_path = os.path.join(base_dir, "assets", "backend", "Config", "config.ini")
    try:
        cfg = configparser.RawConfigParser()
        if os.path.exists(config_path):
            cfg.read(config_path)
        if not cfg.has_section("GameServer"):
            cfg.add_section("GameServer")
        cfg.set("GameServer", "ip", ip)
        cfg.set("GameServer", "port", str(port))
        with open(config_path, "w") as f:
            cfg.write(f)
    except Exception as e:
        print(f"[-] write_matchmaker_config: {e}")


def _write_default_input(base_dir, console_key="F8"):
    """Write DefaultInput.ini with the configured console key."""
    ini_path = os.path.join(base_dir, "assets", "backend", "CloudStorage", "DefaultInput.ini")
    try:
        content = f"[/Script/Engine.InputSettings]\n+ConsoleKeys=Tilde\n+ConsoleKeys={console_key}\n"
        with open(ini_path, "w") as f:
            f.write(content)
    except Exception as e:
        print(f"[-] write_default_input: {e}")


class _ProxyHandler(http.server.BaseHTTPRequestHandler):
    target = ""

    def _forward(self, method):
        url = self.__class__.target + self.path
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length) if length else None
            hdrs = {k: v for k, v in self.headers.items()
                    if k.lower() not in ('host', 'connection', 'transfer-encoding')}
            req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
            with urllib.request.urlopen(req, timeout=30) as resp:
                self.send_response(resp.status)
                for k, v in resp.headers.items():
                    if k.lower() not in ('transfer-encoding', 'connection'):
                        self.send_header(k, v)
                self.end_headers()
                self.wfile.write(resp.read())
        except Exception:
            self.send_response(502)
            self.end_headers()

    def do_GET(self):    self._forward('GET')
    def do_POST(self):   self._forward('POST')
    def do_PUT(self):    self._forward('PUT')
    def do_DELETE(self): self._forward('DELETE')
    def do_PATCH(self):  self._forward('PATCH')
    def log_message(self, *a): pass


def _start_proxy(target_url):
    """Start a local HTTP forward proxy on 127.0.0.1:3551 → target_url."""
    global _proxy_server
    if _proxy_server:
        try:
            _proxy_server.shutdown()
        except Exception:
            pass
        _proxy_server = None

    class Handler(_ProxyHandler):
        pass
    Handler.target = target_url.rstrip('/')
    srv = http.server.HTTPServer(('127.0.0.1', 3551), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    _proxy_server = srv
    print(f"[+] Proxy started: 127.0.0.1:3551 → {target_url}")
    return srv


def _download_dll(name, dest_path, zip_url=None, direct_url=None):
    """Download a DLL from GitHub."""
    if os.path.exists(dest_path):
        return True
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    try:
        if zip_url:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tf:
                tmp = tf.name
            print(f"[*] Downloading {name} from nightly...")
            urllib.request.urlretrieve(zip_url, tmp)
            with zipfile.ZipFile(tmp, 'r') as z:
                for member in z.namelist():
                    if member.lower().endswith('.dll'):
                        z.extract(member, os.path.dirname(dest_path))
                        extracted = os.path.join(os.path.dirname(dest_path), member)
                        if extracted != dest_path:
                            os.rename(extracted, dest_path)
                        break
            os.remove(tmp)
        elif direct_url:
            print(f"[*] Downloading {name}...")
            urllib.request.urlretrieve(direct_url, dest_path)
        else:
            url = _DLL_BASE_URL + name
            print(f"[*] Downloading {name}...")
            urllib.request.urlretrieve(url, dest_path)
        print(f"[+] Downloaded {name}")
        return True
    except Exception as e:
        print(f"[-] Failed to download {name}: {e}")
        return False


class RebootLauncherApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.withdraw()  # Hide the window while initializing to prevent "piece-by-piece" loading
        self.title("Reboot.py")
        
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
        self.configure(fg_color=_T["bg"])

        self.settings = DEFAULT_CONFIG.copy()
        self.load_config()

        _saved_theme = self.settings.get("theme", "Dark")
        if _saved_theme in _THEMES:
            _T.update(_THEMES[_saved_theme])
        self.theme_var = ctk.StringVar(value=_saved_theme)

        self.builds = self.settings.get("builds", [])
        self.path_var = ctk.StringVar(value=self.settings.get("path", ""))
        self.dll_console_var = ctk.StringVar(value=self.settings.get("dll_console", ""))
        self.dll_auth_var = ctk.StringVar(value=self.settings.get("dll_auth", ""))
        self.dll_memory_var = ctk.StringVar(value=self.settings.get("dll_memory", ""))
        self.dll_server_var = ctk.StringVar(value=self.settings.get("dll_server", ""))
        self.dll_auth_choice_var    = ctk.StringVar(value=self.settings.get("dll_auth_choice", "Tellurium 3551"))
        self.dll_console_choice_var = ctk.StringVar(value=self.settings.get("dll_console_choice", "Console"))
        self.dll_server_choice_var  = ctk.StringVar(value=self.settings.get("dll_server_choice", "Reboot"))
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
        self.launch_args_var = ctk.StringVar(value=self.settings.get("launch_args", "-epicapp=Fortnite -epicenv=Prod -epiclocale=en-us -epicportal -skippatchcheck -nobe -fromfl=eac -fltoken=3db3ba5dcbd2e16703f3978d -caldera=eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2NvdW50X2lkIjoiYmU5ZGE1YzJmYmVhNDQwN2IyZjQwZWJhYWQ4NTlhZDQiLCJnZW5lcmF0ZWQiOjE2Mzg3MTcyNzgsImNhbGRlcmFHdWlkIjoiMzgxMGI4NjMtMmE2NS00NDU3LTliNTgtNGRhYjNiNDgyYTg2IiwiYWNQcm92aWRlciI6IkVhc3lBbnRpQ2hlYXQiLCJub3RlcyI6IiIsImZhbGxiYWNrIjpmYWxzZX0.VAWQB67RTxhiWOxx7DBjnzDnXyyEnX7OljJm-j2d88G_WgwQ9wrE6lwMEHZHjBd1ISJdUO1UVUqkfLdU5nofBQ"))
        self.backend_type_var = ctk.StringVar(value=self.settings.get("backend_type", "Local"))
        self.backend_action_text = ctk.StringVar(value="Start" if self.backend_type_var.get() == "Embedded" else "Ping")
        self.backend_type_var.trace_add("write", self.update_backend_action_text)

        self.backend_url_var = ctk.StringVar(value=self.settings.get("backend_url", "http://127.0.0.1:3551"))
        self.backend_port_var = ctk.StringVar(value=self.settings.get("backend_port", "3551"))
        self.backend_path_var = ctk.StringVar(value=self.settings.get("backend_path", "assets/backend/lawinserver.exe"))
        self.backend_autostart_var = ctk.BooleanVar(value=self.settings.get("backend_autostart", False))
        self.rpc_enabled_var = ctk.BooleanVar(value=self.settings.get("rpc_enabled", True))
        self.rpc_enabled_var.trace_add("write", self.update_discord_rpc_state)

        self.dll_large_pak_var = ctk.StringVar(value=self.settings.get("dll_large_pak", ""))
        self.use_large_pak_var = ctk.BooleanVar(value=self.settings.get("use_large_pak", False))

        self.discord = DiscordManager()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.setup_sidebar()
        self.setup_pages()

        self.show_page("Play")
        self.update_discord_rpc_state()
        
        if self.backend_autostart_var.get():
            self.start_backend()

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = int((screen_width / 2) - (950 / 2))
        y = int((screen_height / 2) - (650 / 2))
        self.geometry(f"950x650+{x}+{y}")
        
        self.after(50, self.deiconify)

    def update_discord_rpc_state(self, *args, active_nav=None):
        try:
            if not hasattr(self, 'rpc_enabled_var'):
                return

            is_client_running = hasattr(self, 'game_process') and self.game_process and self.game_process.poll() is None
            is_host_running = hasattr(self, 'host_process') and self.host_process and self.host_process.poll() is None
            
            was_already_running = getattr(self, 'game_running', False)
            self.game_running = bool(is_client_running or is_host_running)

            if not self.rpc_enabled_var.get():
                if hasattr(self.discord, 'clear_state'):
                    self.discord.clear_state()
                self.discord.disconnect()
                return

            self.discord.connect()

            if self.game_running:
                if active_nav is not None and was_already_running:
                    return

                selected_name = self.path_var.get()
                exe_path = selected_name
                for b in getattr(self, "builds", []):
                    if b.get("name") == selected_name or b.get("path") == selected_name:
                        exe_path = b.get("exe", b.get("path", ""))
                        break
                        
                build_ver = getattr(self, '_rpc_build_ver', None) or self.get_game_version(exe_path)[0]
                cl_ver    = getattr(self, '_rpc_cl_ver',    None) or self.get_game_version(exe_path)[1]
                clean_build = re.sub(r'[-_]CL[-_]\d+', '', build_ver).strip().strip('-').strip()
                if clean_build and clean_build != "Unknown":
                    cl_display = cl_ver if (cl_ver and cl_ver.isdigit()) else ""
                    large_text = f"v{clean_build}" + (f"  ·  CL {cl_display}" if cl_display else "")
                else:
                    large_text = "Project Reboot"

                large_image_key = _rpc_image(build_ver)

                p_name = self.username_var.get()
                h_name = self.host_username_var.get()
                is_headless = self.host_headless_var.get()
                
                server_dll_name = ""
                if hasattr(self, 'dll_server_var') and self.dll_server_var.get():
                    server_dll_name = f" ({os.path.basename(self.dll_server_var.get())})"
                
                if is_client_running and is_host_running:
                    state_msg = f"Running: Client and GameServer{server_dll_name}"
                    details = "Playing Fortnite"
                elif is_host_running:
                    if is_headless:
                        state_msg = f"Running: GameServer{server_dll_name}"
                        details = "Hosting Fortnite"
                    else:
                        state_msg = f"Running: Client and GameServer{server_dll_name}"
                        details = "Playing Fortnite"
                else:
                    state_msg = "Running: Client"
                    details = "Playing Fortnite"
                    
                self.discord.update_state(state=state_msg, details=details,
                                           large_image=large_image_key, small_image="rebootlogo",
                                           small_text="Reboot.py", large_text=large_text)
            else:
                if not active_nav:
                    active_nav = "Play"
                user = self.username_var.get() if hasattr(self, 'username_var') else "PythonPlayer"
                self.discord.update_state(state=f"Viewing {active_nav} tab", details=f"Logged in as {user}")
        except Exception as e:
            print(f"[-] RPC Crash: {e}")

    def update_backend_action_text(self, *args):
        if hasattr(self, 'backend_type_var') and hasattr(self, 'backend_action_text'):
            btype = self.backend_type_var.get()
            if btype in ["Remote", "Local"]:
                self.backend_action_text.set("Ping")
            else:
                self.backend_action_text.set("Start")
            
            if hasattr(self, 'remote_url_tile') and hasattr(self, 'backend_path_tile') and hasattr(self, 'start_backend_tile'):
                self.remote_url_tile.pack_forget()
                self.local_port_tile.pack_forget()
                self.backend_path_tile.pack_forget()
                self.start_backend_tile.pack_forget()
                self.autostart_backend_tile.pack_forget()
                
                if btype == "Remote":
                    self.remote_url_tile.pack(fill="x", pady=6)
                elif btype == "Local":
                    self.local_port_tile.pack(fill="x", pady=6)
                elif btype == "Embedded":
                    self.backend_path_tile.pack(fill="x", pady=6)
                    
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
        changed = False
        for b in self.settings.get("builds", []):
            name = b.get("name", "")
            if name.startswith("Fortnite v") and not name.startswith("Fortnite ("):
                continue
            m = re.search(r'(\d+\.\d+(?:\.\d+)?)', name)
            if m:
                b["name"] = f"Fortnite v{m.group(1)}"
                changed = True
            elif b.get("exe"):
                bv, _ = self.get_game_version(b["exe"])
                if bv != "Unknown":
                    b["name"] = f"Fortnite v{bv}"
                    changed = True
        if changed:
            try:
                with open(CONFIG_PATH, "w") as f:
                    json.dump(self.settings, f, indent=4)
            except Exception:
                pass

    def save_config(self):
        self.settings["path"] = self.path_var.get()
        self.settings["builds"] = getattr(self, "builds", [])
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
        self.settings["dll_large_pak"] = self.dll_large_pak_var.get()
        self.settings["use_large_pak"] = self.use_large_pak_var.get()
        self.settings["dll_auth_choice"]    = self.dll_auth_choice_var.get()
        self.settings["dll_console_choice"] = self.dll_console_choice_var.get()
        self.settings["dll_server_choice"]  = self.dll_server_choice_var.get()
        self.settings["theme"] = self.theme_var.get()
        self.user_lbl.configure(text=self.username_var.get())
        self.email_lbl.configure(text=self.email_var.get())
        
        try:
            with open(CONFIG_PATH, "w") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e: print('RPC Error:', e)

    def apply_theme(self, theme_name):
        """Live-swap theme — update colors and rebuild UI without restarting."""
        if theme_name not in _THEMES:
            return
        _T.update(_THEMES[theme_name])

        self.configure(fg_color=_T["bg"])

        self.sidebar.destroy()
        self.setup_sidebar()

        self.pages_frame.destroy()
        self.setup_pages()

        current = getattr(self, "_current_page", "Settings")
        self.show_page(current)

        self.save_config()

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=_T["sidebar"])
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(8, weight=1)

        self.profile_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.profile_frame.pack(pady=(20,10), padx=20, fill="x")

        user_img_path = os.path.join(self.base_dir, "assets", "images", "user.png")
        if HAS_PIL and os.path.exists(user_img_path):
            user_image = ctk.CTkImage(light_image=Image.open(user_img_path), size=(45, 45))
            avatar_lbl = ctk.CTkLabel(self.profile_frame, text="", image=user_image)
            avatar_lbl.pack(side="left", padx=(0, 10))
        else:
            avatar_canvas = ctk.CTkCanvas(self.profile_frame, width=45, height=45, bg=_T["sidebar"], highlightthickness=0)
            avatar_canvas.pack(side="left", padx=(0, 10))
            avatar_canvas.create_oval(2, 2, 43, 43, fill="#333333", outline="")
            avatar_canvas.create_text(22, 22, text="S", fill="white", font=("Segoe UI", 16, "bold"))

        info_frame = ctk.CTkFrame(self.profile_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True)

        self.user_lbl = ctk.CTkLabel(info_frame, text=self.settings.get("username", "Ssd"), font=("Segoe UI", 15, "bold"), anchor="w", text_color=_T["text"])
        self.user_lbl.pack(fill="x", pady=(2,0))
        self.email_lbl = ctk.CTkLabel(info_frame, text=self.settings.get("email", "ssd@gmail.com"), font=("Segoe UI", 11), text_color=_T["subtext"], anchor="w")
        self.email_lbl.pack(fill="x")

        search_f = ctk.CTkFrame(self.sidebar, fg_color=_T["nav_active"], corner_radius=6, height=35)
        search_f.pack(pady=15, padx=20, fill="x")
        search_f.pack_propagate(False)
        ctk.CTkEntry(search_f, placeholder_text="Find a setting", border_width=0, fg_color="transparent", text_color="#d4d4d8").pack(side="left", fill="both", expand=True, padx=5)

        self.nav_btns = {}
        nav_items = ["Play", "Download", "Host", "Backend", "Info", "Settings"]
        for item in nav_items:
            img_path = os.path.join(self.base_dir, "assets", "images", f"{item.lower()}.png")
            if HAS_PIL and os.path.exists(img_path):
                btn_img = ctk.CTkImage(light_image=Image.open(img_path), size=(20, 20))
                btn = ctk.CTkButton(self.sidebar, text=f"  {item}", image=btn_img, anchor="w", fg_color="transparent",
                                    hover_color=_T["nav_active"], font=("Segoe UI", 14), corner_radius=6, height=38,
                                    command=lambda n=item: self.show_page(n))
            else:
                btn = ctk.CTkButton(self.sidebar, text=f"   {item}", anchor="w", fg_color="transparent",
                                    hover_color=_T["nav_active"], font=("Segoe UI", 14), corner_radius=6, height=38,
                                    command=lambda n=item: self.show_page(n))
            
            btn.pack(fill="x", padx=15, pady=2)
            self.nav_btns[item] = btn

    def setup_pages(self):
        self.pages_frame = ctk.CTkFrame(self, fg_color=_T["content"], corner_radius=0)
        self.pages_frame.grid(row=0, column=1, sticky="nsew")
        self.pages_frame.grid_rowconfigure(0, weight=1)
        self.pages_frame.grid_columnconfigure(0, weight=1)

        self.pages = {}
        self._pages_built = set()
        self._all_page_names = ["Play", "Download", "ClientOptions", "Host", "HostInformation", "HostOptions", "HostShare", "Backend", "Info", "Settings", "AccountSettings", "InternalFiles"]
        _scrollable = {"Info", "Settings", "InternalFiles", "AccountSettings"}
        for name in self._all_page_names:
            if name in _scrollable:
                f = ctk.CTkScrollableFrame(
                    self.pages_frame,
                    fg_color="transparent",
                    scrollbar_button_color=_T["muted"],
                    scrollbar_button_hover_color=_T["muted_hover"],
                )
            else:
                f = ctk.CTkFrame(self.pages_frame, fg_color="transparent")
            self.pages[name] = f

    def _sync_button_states(self):
        """Re-apply Play/Host button visuals to match actual running process state.
        Called every time a page is shown so switching tabs never resets the button."""
        is_client  = hasattr(self, 'game_process') and self.game_process and self.game_process.poll() is None
        is_hosting = hasattr(self, 'host_process')  and self.host_process  and self.host_process.poll()  is None
        if hasattr(self, 'launch_btn'):
            if is_client:
                self.launch_btn.configure(text="Stop Client", fg_color="#ef4444", hover_color="#dc2626")
            else:
                self.launch_btn.configure(text="Play",        fg_color=_T["accent"], hover_color=_T["accent_hover"])
        if hasattr(self, 'host_btn'):
            if is_hosting:
                self.host_btn.configure(text="Stop Server", fg_color="#ef4444", hover_color="#dc2626")
            else:
                self.host_btn.configure(text="Host Server", fg_color=_T["accent"], hover_color=_T["accent_hover"])

    def show_page(self, name):
        self._current_page = name
        if name not in self._pages_built:
            getattr(self, f"build_{name.lower()}_page")(self.pages[name])
            self._pages_built.add(name)

        for page in self.pages.values():
            page.grid_forget()

        active_nav = name
        if name in ["InternalFiles", "AccountSettings"]:
            active_nav = "Settings"
        elif name in ["ClientOptions"]:
            active_nav = "Play"
        elif name.startswith("Host"):
            active_nav = "Host"

        for n, btn in self.nav_btns.items():
            btn.configure(fg_color=_T["nav_active"] if n == active_nav else "transparent")

        self.pages[name].grid(row=0, column=0, sticky="nsew", padx=40, pady=30)

        self._sync_button_states()

        self.save_config()
        self.update_discord_rpc_state(active_nav=active_nav)

    # --- PAGES ---

    def build_play_page(self, parent):
        ctk.CTkLabel(parent, text="Play", font=("Segoe UI", 32, "bold"), text_color="white", anchor="w").pack(fill="x", pady=(0, 20))
        
        builds_frame = ctk.CTkFrame(parent, fg_color=_T["tile"], corner_radius=5, height=78)
        builds_frame.pack(fill="x", pady=6)
        builds_frame.pack_propagate(False)

        text_frame = ctk.CTkFrame(builds_frame, fg_color="transparent")
        text_frame.pack(side="left", padx=20, fill="y", pady=15)
        
        ctk.CTkLabel(text_frame, text="Select Build", font=("Segoe UI", 15, "bold"), text_color=_T["text"], anchor="w").pack(fill="x", pady=(0, 2))
        ctk.CTkLabel(text_frame, text="Choose a Fortnite version to launch or add a new one", font=("Segoe UI", 12), text_color=_T["subtext"], anchor="w").pack(fill="x")

        add_btn = ctk.CTkButton(builds_frame, text="+", font=("Segoe UI", 18, "bold"), fg_color=_T["muted"], hover_color=_T["muted_hover"], text_color="white", width=34, height=34, corner_radius=4, command=self.add_build)
        add_btn.pack(side="right", padx=(5, 20))
        
        rem_btn = ctk.CTkButton(builds_frame, text="-", font=("Segoe UI", 20, "bold"), fg_color="#ef4444", hover_color="#dc2626", text_color="white", width=34, height=34, corner_radius=4, command=self.remove_build)
        rem_btn.pack(side="right", padx=(10, 5))
        
        self.build_option_menu = ctk.CTkOptionMenu(builds_frame, variable=self.path_var, values=[b.get("name", b.get("path")) for b in self.builds] if self.builds else ["No builds added"], fg_color=_T["muted"], button_color=_T["muted_hover"], button_hover_color=_T["muted_deep"], dropdown_fg_color=_T["muted"], width=250)
        self.build_option_menu.pack(side="right", padx=(0, 0))

        SettingTile(parent, "Client Options", "Override engine arguments", button_text=">", is_subpage=True, button_command=lambda: self.show_page("ClientOptions"))
        
        self.launch_btn = ctk.CTkButton(parent, text="Play", fg_color=_T["accent"], font=("Segoe UI", 18, "bold"), height=55, hover_color=_T["accent_hover"], command=self.handle_launch)
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
                req = urllib.request.Request('https://builds.rebootfn.org/versions.json', headers={'User-Agent': 'Mozilla/5.0'})
                data_result['data'] = json.loads(urllib.request.urlopen(req).read())
            except Exception as e:
                error_result.append(str(e))

        def get_version_tuple(url):
            filename = urllib.parse.unquote(url.split('/')[-1])
            version_str = filename.replace('.zip','').replace('.rar','').replace('vFortnite ','').replace('vFortnite','').replace('Fortnite ','').replace('Fortnite','').strip()
            return tuple(int(x) for x in version_str.split('.') if x.isdigit())

        def render_versions(*args):
            self.downloads_container.pack_forget()
            for w in self.downloads_container.winfo_children():
                w.destroy()
            versions = data_result.get('data', [])
            if not versions:
                self.downloads_container.pack(fill="both", expand=True)
                return
            is_descending = "High - Low" in sort_var.get()
            sorted_versions = sorted(versions, key=get_version_tuple, reverse=is_descending)
            view_mode = view_var.get()
            columns = 3
            if view_mode == "Blocks View":
                for i in range(columns):
                    self.downloads_container.grid_columnconfigure(i, weight=1)
            else:
                self.downloads_container.grid_columnconfigure((0, 1, 2), weight=0)

            for idx, url in enumerate(sorted_versions):
                filename    = urllib.parse.unquote(url.split('/')[-1])
                version_str = filename.replace('.zip','').replace('.rar','').replace('vFortnite ','').replace('vFortnite','').replace('Fortnite ','').replace('Fortnite','').strip()
                parts    = get_version_tuple(url)
                is_valid = not (parts and (parts[0] > 10 or (parts[0] == 10 and len(parts) > 1 and parts[1] > 31)))
                tile     = ctk.CTkFrame(self.downloads_container, fg_color=_T["nav_active"], corner_radius=8)

                if view_mode == "List View":
                    tile.pack(fill="x", pady=4, padx=5)
                    ctk.CTkLabel(tile, text=f"Version {version_str}", font=("Segoe UI", 15, "bold"),
                                 text_color="white" if is_valid else "#52525b").pack(side="left", padx=15, pady=15)
                    if is_valid:
                        info_frame = ctk.CTkFrame(tile, fg_color="transparent")
                        info_frame.pack(side="right", padx=15, fill="x", expand=True)
                        prog_bar  = ctk.CTkProgressBar(info_frame, width=180, height=8, progress_color=_T["accent_hover"], fg_color=_T["muted"])
                        prog_bar.set(0)
                        stat_lbl  = ctk.CTkLabel(info_frame, text="", font=("Segoe UI", 11), text_color="#a1a1aa")
                        dl_btn    = ctk.CTkButton(tile, text="Download", width=100,
                                                  fg_color=_T["accent_hover"], hover_color=_T["accent_hover"])
                        dl_btn.pack(side="right", padx=(0, 10))
                        dl_btn.configure(command=lambda u=url, vs=version_str, pb=prog_bar, sl=stat_lbl, b=dl_btn:
                                         self._start_download(u, vs, pb, sl, b))
                    else:
                        ctk.CTkButton(tile, text="Unsupported", width=100,
                                      fg_color="#3f3f46", hover_color="#3f3f46", state="disabled").pack(side="right", padx=15)
                else:
                    r, c = idx // columns, idx % columns
                    tile.grid(row=r, column=c, padx=5, pady=5, sticky="nsew")
                    ctk.CTkLabel(tile, text=f"v{version_str}", font=("Segoe UI", 18, "bold"),
                                 text_color="white" if is_valid else "#52525b").pack(pady=(15, 5))
                    if is_valid:
                        prog_bar = ctk.CTkProgressBar(tile, width=140, height=8, progress_color=_T["accent"], fg_color=_T["muted"])
                        prog_bar.set(0)
                        stat_lbl = ctk.CTkLabel(tile, text="", font=("Segoe UI", 10), text_color="#a1a1aa")
                        dl_btn   = ctk.CTkButton(tile, text="Download", width=100,
                                                 fg_color=_T["accent_hover"], hover_color=_T["accent_hover"])
                        dl_btn.pack(pady=(5, 15))
                        dl_btn.configure(command=lambda u=url, vs=version_str, pb=prog_bar, sl=stat_lbl, b=dl_btn:
                                         self._start_download(u, vs, pb, sl, b))
                    else:
                        ctk.CTkButton(tile, text="Unsupported", width=100,
                                      fg_color="#3f3f46", hover_color="#3f3f46", state="disabled").pack(pady=(5, 15))

            self.downloads_container.pack(fill="both", expand=True)

        def check_data():
            if 'data' in data_result:
                render_versions()
            elif error_result:
                loading_lbl.configure(text=f"Failed to load versions: {error_result[0]}")
            else:
                self.after(100, check_data)

        sort_menu = ctk.CTkOptionMenu(controls_frame, variable=sort_var,
                                      values=["Latest to Oldest (High - Low)", "Oldest to Latest (Low - High)"],
                                      command=render_versions, fg_color="#1e1e1e",
                                      button_color="#252526", button_hover_color="#2d2d30")
        sort_menu.pack(side="left")
        view_toggle = ctk.CTkSegmentedButton(controls_frame, values=["List View", "Blocks View"],
                                              variable=view_var, command=render_versions,
                                              selected_color="#2563eb", unselected_color="#1e1e1e")
        view_toggle.pack(side="right", padx=(10, 0))
        threading.Thread(target=fetch_versions, daemon=True).start()
        self.after(100, check_data)

    def _start_download(self, url, version_str, prog_bar, stat_lbl, dl_btn):
        """Download a build with progress, then offer to extract."""
        save_dir = filedialog.askdirectory(title=f"Choose folder to save Fortnite {version_str}")
        if not save_dir:
            return

        filename = urllib.parse.unquote(url.split('/')[-1])
        dest     = os.path.join(save_dir, filename)

        dl_btn.configure(state="disabled", text="Downloading…", fg_color="#1d4020")
        prog_bar.pack(pady=(0, 2))
        stat_lbl.pack()

        aria2c = os.path.join(self.base_dir, "assets", "build", "aria2c.exe")

        def run():
            cancelled = [False]

            if os.path.exists(aria2c):
                cmd = [
                    aria2c,
                    "-x", "16", "-s", "16", "-k", "1M",
                    "--dir", save_dir,
                    "--out", filename,
                    "--console-log-level=notice",
                    "--summary-interval=1",
                    url
                ]
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        text=True, encoding="utf-8", errors="replace")
                aria_re = re.compile(
                    r'\((\d+)%\).*DL:([\d\.]+\w+/s)(?:.*ETA:([\d]+s))?'
                )
                for line in proc.stdout:
                    m = aria_re.search(line)
                    if m:
                        pct  = int(m.group(1)) / 100
                        spd  = m.group(2)
                        eta  = m.group(3) or ""
                        txt  = f"{int(pct*100)}%  ·  {spd}" + (f"  ·  ETA {eta}" if eta else "")
                        self.after(0, lambda p=pct, t=txt: (prog_bar.set(p), stat_lbl.configure(text=t)))
                proc.wait()
                ok = proc.returncode == 0 and os.path.exists(dest)

            else:
                try:
                    req  = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                    resp = urllib.request.urlopen(req)
                    total = int(resp.headers.get("Content-Length", 0))
                    done  = 0
                    t0    = time.time()
                    chunk = 65536
                    with open(dest, "wb") as f:
                        while True:
                            buf = resp.read(chunk)
                            if not buf:
                                break
                            f.write(buf)
                            done += len(buf)
                            elapsed = max(time.time() - t0, 0.001)
                            spd  = done / elapsed
                            pct  = done / total if total else 0
                            def _upd(p=pct, d=done, t=total, s=spd):
                                prog_bar.set(p)
                                dmb = f"{d/1048576:.1f}"
                                tmb = f"{t/1048576:.1f}" if t else "?"
                                smb = f"{s/1048576:.1f}"
                                stat_lbl.configure(text=f"{dmb} / {tmb} MB  ·  {smb} MB/s")
                            self.after(0, _upd)
                    ok = True
                except Exception as e:
                    ok = False
                    self.after(0, lambda err=e: messagebox.showerror("Download Error", str(err)))

            if ok:
                self.after(0, lambda: _on_done(dest))
            else:
                self.after(0, lambda: (
                    dl_btn.configure(state="normal", text="Download", fg_color="#2563eb"),
                    prog_bar.set(0),
                    stat_lbl.configure(text="Failed.")
                ))

        def _on_done(dest_path):
            prog_bar.set(1.0)
            stat_lbl.configure(text="Done!")
            dl_btn.configure(state="normal", text="Done ✓", fg_color="#16a34a", hover_color="#15803d")

            if messagebox.askyesno("Download Complete",
                                   f"Downloaded:\n{os.path.basename(dest_path)}\n\nExtract now?"):
                extract_to = filedialog.askdirectory(title="Choose extraction folder")
                if extract_to:
                    self._extract_build(dest_path, extract_to, stat_lbl)

        threading.Thread(target=run, daemon=True).start()

    def _extract_build(self, archive_path, extract_to, stat_lbl=None):
        """Extract a zip/rar build archive using 7zip or winrar from assets/build."""
        sevenzip = os.path.join(self.base_dir, "assets", "build", "7zip.exe")
        winrar   = os.path.join(self.base_dir, "assets", "build", "winrar.exe")

        if archive_path.lower().endswith(".rar") and os.path.exists(winrar):
            cmd = [winrar, "x", "-y", archive_path, extract_to + "\\"]
        elif os.path.exists(sevenzip):
            cmd = [sevenzip, "x", archive_path, f"-o{extract_to}", "-y"]
        else:
            messagebox.showerror("Extract Error", "No extractor found in assets/build (7zip.exe / winrar.exe).")
            return

        if stat_lbl:
            self.after(0, lambda: stat_lbl.configure(text="Extracting…"))

        def run():
            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        text=True, encoding="utf-8", errors="replace")
                pct_re = re.compile(r'(\d+)%')
                for line in proc.stdout:
                    m = pct_re.search(line)
                    if m and stat_lbl:
                        pct = int(m.group(1)) / 100
                        self.after(0, lambda p=pct: stat_lbl.configure(text=f"Extracting… {int(p*100)}%"))
                proc.wait()
                if proc.returncode == 0:
                    self.after(0, lambda: (
                        stat_lbl.configure(text="Extracted!") if stat_lbl else None,
                        messagebox.showinfo("Done", f"Extracted to:\n{extract_to}")
                    ))
                else:
                    self.after(0, lambda: messagebox.showerror("Extract Error", "Extraction failed."))
            except Exception as e:
                self.after(0, lambda err=e: messagebox.showerror("Extract Error", str(err)))

        threading.Thread(target=run, daemon=True).start()

    def build_clientoptions_page(self, parent):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        back_btn = ctk.CTkButton(header, text="<", width=30, fg_color="transparent", font=("Segoe UI", 18), hover_color=_T["nav_active"], command=lambda: self.show_page("Play"))
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

        self.host_btn = ctk.CTkButton(parent, text="Host Server", fg_color=_T["accent"], font=("Segoe UI", 18, "bold"), height=55, hover_color=_T["accent_hover"], command=lambda: self.handle_launch(is_host=True))
        self.host_btn.pack(pady=40, fill="x")

    def build_hostinformation_page(self, parent):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        back_btn = ctk.CTkButton(header, text="<", width=30, fg_color="transparent", font=("Segoe UI", 18), hover_color=_T["nav_active"], command=lambda: self.show_page("Host"))
        back_btn.pack(side="left", padx=(0,10))
        ctk.CTkLabel(header, text="Host > Information", font=("Segoe UI", 28, "bold"), text_color="white", anchor="w").pack(side="left")

        SettingTile(parent, "Name", "Type a name for the game server, max 30 characters", show_entry=True, entry_var=self.host_name_var)
        SettingTile(parent, "Description", "Type a description for the game server", show_entry=True, entry_var=self.host_desc_var)
        SettingTile(parent, "Password", "Type a password for the game server, max 30 characters (ignored if not published)", show_entry=True, entry_var=self.host_pass_var)

    def build_hostoptions_page(self, parent):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        back_btn = ctk.CTkButton(header, text="<", width=30, fg_color="transparent", font=("Segoe UI", 18), hover_color=_T["nav_active"], command=lambda: self.show_page("Host"))
        back_btn.pack(side="left", padx=(0,10))
        ctk.CTkLabel(header, text="Host > Options", font=("Segoe UI", 28, "bold"), text_color="white", anchor="w").pack(side="left")

        SettingTile(parent, "Custom launch args", "These launch args will be injected to the game process", show_entry=True, entry_var=self.host_custom_args_var)
        SettingTile(parent, "Headless", "Create the game server as a background process", is_switch=True, switch_var=self.host_headless_var)
        SettingTile(parent, "Automatic Restart", "Automatically start the game server on exit", is_switch=True, switch_var=self.host_autorun_var)
        SettingTile(parent, "Game server port", "The port your server uses (Default: 7777)", show_entry=True, entry_var=self.host_port_var)

    def build_hostshare_page(self, parent):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        back_btn = ctk.CTkButton(header, text="<", width=30, fg_color="transparent", font=("Segoe UI", 18), hover_color=_T["nav_active"], command=lambda: self.show_page("Host"))
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
        import webbrowser
        ctk.CTkLabel(parent, text="Info", font=("Segoe UI", 32, "bold"), text_color="white", anchor="w").pack(fill="x", pady=(0, 20))

        # --- Hero banner ---
        hero = ctk.CTkFrame(parent, fg_color=_T["tile"], corner_radius=10)
        hero.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(hero, text="Reboot.py", font=("Segoe UI", 26, "bold"), text_color=_T["accent"]).pack(pady=(22, 2))
        ctk.CTkLabel(hero, text="v1.2  ·  The most lightweight way to play legacy Fortnite", font=("Segoe UI", 12), text_color="#71717a").pack()

        commit_lbl_var = ctk.StringVar(value="latest commit: fetching...")
        ctk.CTkLabel(hero, textvariable=commit_lbl_var, font=("Segoe UI", 11), text_color="#52525b").pack(pady=(2, 0))

        def _fetch_commit():
            try:
                req = urllib.request.Request(
                    "https://api.github.com/repos/Ducki67/Project-Reboot.py/commits/main",
                    headers={"Accept": "application/vnd.github+json", "User-Agent": "reboot.py-launcher"}
                )
                with urllib.request.urlopen(req, timeout=8) as r:
                    data = json.loads(r.read().decode())
                sha = data["sha"][:7]
                msg = data["commit"]["message"].splitlines()[0]
                commit_lbl_var.set(f"latest commit: #{sha} — {msg}")
            except Exception:
                commit_lbl_var.set("latest commit: unavailable")

        threading.Thread(target=_fetch_commit, daemon=True).start()
        btn_row = ctk.CTkFrame(hero, fg_color="transparent")
        btn_row.pack(pady=(14, 22))
        ctk.CTkButton(btn_row, text="Discord", fg_color="#5865F2", hover_color="#4752C4", width=110, height=32, corner_radius=6,
                      command=lambda: webbrowser.open("https://discord.gg/rebootmp")).pack(side="left", padx=8)
        ctk.CTkButton(btn_row, text="GitHub", fg_color="#24292e", hover_color="#1a1f24", width=110, height=32, corner_radius=6,
                      command=lambda: webbrowser.open("https://github.com/Ducki67/Project-Reboot.py")).pack(side="left", padx=8)

        # --- Changelog (links to GitHub Releases) ---
        ctk.CTkLabel(parent, text="Releases", font=("Segoe UI", 18, "bold"), text_color=_T["text"], anchor="w").pack(fill="x", pady=(8, 6))

        _RELEASES_BASE = "https://github.com/Ducki67/Project-Reboot.py/releases/tag/"
        releases = [
            ("v1.2", "Current", _T["accent"],   "Multi-theme system, DLL preset selection (Cobalt/Erbium), lazy page loading, scrollbar fixes"),
            ("v1.1", "",        "#71717a",       "Discord RPC, season-aware images, UE5 version detection, LargePakPatch, S20+ login fix"),
            ("v1.0", "",        "#52525b",       "Initial release — DLL injection, backend proxy, build downloader, headless server mode"),
        ]

        for tag, badge, accent, summary in releases:
            card = ctk.CTkFrame(parent, fg_color=_T["tile"], corner_radius=8)
            card.pack(fill="x", pady=5)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=16, pady=14)

            left = ctk.CTkFrame(inner, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True)

            title_row = ctk.CTkFrame(left, fg_color="transparent")
            title_row.pack(fill="x")

            dot = ctk.CTkFrame(title_row, fg_color=accent, width=10, height=10, corner_radius=5)
            dot.pack(side="left", padx=(0, 8), pady=3)
            dot.pack_propagate(False)

            ctk.CTkLabel(title_row, text=tag, font=("Segoe UI", 14, "bold"), text_color=_T["text"]).pack(side="left")

            if badge:
                badge_lbl = ctk.CTkLabel(title_row, text=f" {badge}", font=("Segoe UI", 11, "bold"),
                                         text_color=accent, fg_color="transparent")
                badge_lbl.pack(side="left", padx=(6, 0))

            ctk.CTkLabel(left, text=summary, font=("Segoe UI", 12), text_color=_T["subtext"],
                         anchor="w", wraplength=580, justify="left").pack(fill="x", pady=(4, 0))

            ctk.CTkButton(inner, text="View on GitHub", width=130, height=32, corner_radius=6,
                          fg_color=_T["muted"], hover_color=_T["muted_hover"], text_color=_T["text"],
                          font=("Segoe UI", 12),
                          command=lambda t=tag: webbrowser.open(_RELEASES_BASE + t)).pack(side="right")

        ctk.CTkLabel(parent, text="made by Ducki67  ·  Reboot.py is not affiliated with Epic Games  ·  powered by CustomTkinter",
                     text_color="#3f3f46", font=("Segoe UI", 11)).pack(pady=30)

    def build_settings_page(self, parent):
        ctk.CTkLabel(parent, text="Settings", font=("Segoe UI", 32, "bold"), text_color="white", anchor="w").pack(fill="x", pady=(0, 20))
        
        SettingTile(parent, "Account options", "Configure your mock username and password", button_text=">", is_subpage=True, button_command=lambda: self.show_page("AccountSettings"))
        SettingTile(parent, "Discord Activity", "Show your status playing Reboot on Discord", is_switch=True, switch_var=self.rpc_enabled_var)
        SettingTile(parent, "LargePakPatch", "Inject LargePakPatch.dll after login for custom mods — auto-downloads from Atlas Link", is_switch=True, switch_var=self.use_large_pak_var)
        SettingTile(parent, "Language", "Select the language to use inside the launcher", button_text="English")
        SettingTile(parent, "Theme", "Select the theme to use inside the launcher",
                    is_option=True, option_var=self.theme_var,
                    options_list=list(_THEMES.keys()))
        self.theme_var.trace_add("write", lambda *_: self.apply_theme(self.theme_var.get()))
        SettingTile(parent, "Internal files", "Configure the internal files used by the launcher", button_text=">", is_subpage=True, button_command=lambda: self.show_page("InternalFiles"))

    def build_internalfiles_page(self, parent):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        back_btn = ctk.CTkButton(header, text="<", width=30, fg_color="transparent", font=("Segoe UI", 18), hover_color=_T["nav_active"], command=lambda: self.show_page("Settings"))
        back_btn.pack(side="left", padx=(0,10))
        ctk.CTkLabel(header, text="Settings > Internal files", font=("Segoe UI", 28, "bold"), text_color="white", anchor="w").pack(side="left")

        SettingTile(parent, "Authentication patcher", "Redirects all HTTP requests to the backend — Tellurium (default), Cobalt for older builds",
                    is_option=True, option_var=self.dll_auth_choice_var,
                    options_list=list(_DLL_AUTH_PRESETS.keys()))
        SettingTile(parent, "Unreal engine patcher", "Unlocks the Unreal Engine Console — use Erbium Client for Ch3+",
                    is_option=True, option_var=self.dll_console_choice_var,
                    options_list=list(_DLL_CONSOLE_PRESETS.keys()))
        SettingTile(parent, "Game server", "The server DLL injected on launch — use Erbium for Ch3+",
                    is_option=True, option_var=self.dll_server_choice_var,
                    options_list=list(_DLL_SERVER_PRESETS.keys()))
        SettingTile(parent, "Memory patcher", "Prevents the client from crashing because of a memory leak", button_text="Browse", show_entry=True, entry_var=self.dll_memory_var, button_command=lambda: self.browse_dll(self.dll_memory_var))

        SettingTile(parent, "LargePakPatch DLL", "Custom path — leave blank to auto-download", button_text="Browse", show_entry=True, entry_var=self.dll_large_pak_var, button_command=lambda: self.browse_dll(self.dll_large_pak_var))

    def build_accountsettings_page(self, parent):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        back_btn = ctk.CTkButton(header, text="<", width=30, fg_color="transparent", font=("Segoe UI", 18), hover_color=_T["nav_active"], command=lambda: self.show_page("Settings"))
        back_btn.pack(side="left", padx=(0,10))
        ctk.CTkLabel(header, text="Settings > Account", font=("Segoe UI", 28, "bold"), text_color="white", anchor="w").pack(side="left")

        SettingTile(parent, "Username", "In-game display name", show_entry=True, entry_var=self.username_var)
        SettingTile(parent, "Email", "Account email", show_entry=True, entry_var=self.email_var)
        SettingTile(parent, "Password", "Account password", show_entry=True, entry_var=self.password_var)

        ctk.CTkLabel(parent, text="Host Account", font=("Segoe UI", 20, "bold"), text_color="white", anchor="w").pack(fill="x", pady=(20, 10))
        SettingTile(parent, "Host Username", "In-game display name for host", show_entry=True, entry_var=self.host_username_var)
        SettingTile(parent, "Host Email", "Account email for host", show_entry=True, entry_var=self.host_email_var)
        SettingTile(parent, "Host Password", "Account password for host", show_entry=True, entry_var=self.host_account_password_var)

    # --- ACTION LOGIC ---

    def remove_build(self):
        selected = self.path_var.get()
        if not selected or selected == "No builds added":
            return
            
        confirm = messagebox.askyesno("Remove Build", f"Are you sure you want to remove '{selected}' from the launcher?")
        if not confirm:
            return
            
        self.builds = [b for b in self.builds if b.get("name", b.get("path")) != selected]
        self.save_config()
        
        if hasattr(self, 'build_option_menu'):
            new_values = [b.get("name", b.get("path")) for b in self.builds]
            if not new_values:
                new_values = ["No builds added"]
                self.path_var.set("No builds added")
            else:
                self.path_var.set(new_values[0])
            self.build_option_menu.configure(values=new_values)

    def add_build(self):
        f = filedialog.askdirectory(title="Select Game Directory (e.g. Fortnite v3.6)")
        if f:
            exe = os.path.join(f, "FortniteGame/Binaries/Win64/FortniteClient-Win64-Shipping.exe").replace("/", os.sep)
            if not os.path.exists(exe):
                messagebox.showerror("Error", f"Could not find Fortnite executable at:\n{exe}")
                return
                
            build_name, cl = self.get_game_version(exe)
            if build_name != "Unknown":
                display_name = f"Fortnite v{build_name}"
            else:
                display_name = f"Fortnite ({os.path.basename(f)})"
            
            for b in self.builds:
                if b.get("exe") == exe:
                    self.path_var.set(b.get("name", display_name))
                    return
            
            new_build = {"name": display_name, "exe": exe}
            self.builds.append(new_build)
            self.save_config()
            
            if hasattr(self, 'build_option_menu'):
                self.build_option_menu.configure(values=[b.get("name", b.get("path")) for b in self.builds])
            
            self.path_var.set(display_name)

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
        _write_default_input(self.base_dir)

        backend_type = self.backend_type_var.get()

        if backend_type == "Embedded":
            bpath = self.settings.get("backend_path", "")
            bpath = os.path.join(self.base_dir, bpath) if not os.path.isabs(bpath) else bpath
            if not os.path.exists(bpath):
                messagebox.showerror("Error", "Embedded backend executable not found.")
                return

            _kill_port(3551)
            _kill_port(80)

            dir_name = os.path.dirname(bpath)
            if bpath.lower().endswith(".bat"):
                subprocess.Popen(["cmd.exe", "/c", bpath], cwd=dir_name,
                                  creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen([bpath], cwd=dir_name, creationflags=0x08000000)

            print("[+] Embedded backend started.")

        elif backend_type in ["Remote", "Local"]:
            if backend_type == "Remote":
                target_url = self.backend_url_var.get().strip()
                if not target_url.startswith("http"):
                    target_url = "http://" + target_url
            else:
                port = self.backend_port_var.get().strip()
                target_url = f"http://127.0.0.1:{port}"

            def ping_and_proxy():
                try:
                    req = urllib.request.Request(target_url, headers={"User-Agent": "RebootLauncher"})
                    urllib.request.urlopen(req, timeout=5)
                    reachable = True
                except urllib.error.HTTPError:
                    reachable = True   # HTTP error means server responded
                except Exception as e:
                    reachable = False
                    self.after(0, lambda err=e: messagebox.showerror(
                        "Error", f"Failed to reach {backend_type} backend:\n{err}"))

                if reachable:
                    needs_proxy = (backend_type == "Remote") or \
                                  (backend_type == "Local" and
                                   self.backend_port_var.get().strip() != "3551")
                    if needs_proxy:
                        _kill_port(3551)
                        _start_proxy(target_url)
                    self.after(0, lambda: messagebox.showinfo(
                        "Success", "Server is online" +
                        ("\nProxy running on 127.0.0.1:3551" if needs_proxy else "")))

            threading.Thread(target=ping_and_proxy, daemon=True).start()
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

    def get_cl_mapping(self, cl):
        if not hasattr(self, 'cl_mappings'):
            self.cl_mappings = {}
            mapping_file = os.path.join(self.base_dir, "cl_mapping.json")
            if os.path.exists(mapping_file):
                try:
                    with open(mapping_file, "r") as f:
                        self.cl_mappings = json.load(f)
                except Exception:
                    pass
            if cl and cl not in self.cl_mappings:
                try:
                    import urllib.request, re, json
                    req = urllib.request.Request('https://raw.githubusercontent.com/Helix-Dev-Q/fortnite-builds-archive/main/README.md', headers={'User-Agent': 'Mozilla/5.0'})
                    html = urllib.request.urlopen(req, timeout=3).read().decode('utf-8')
                    matches = re.findall(r'\|\s*([a-zA-Z0-9\.]+)(?:\s+\(.*?-CL-(\d+)\)|-CL-(\d+))\s*\|', html)
                    for m in matches:
                        v = m[0]
                        c = m[1] if m[1] else m[2]
                        if c:
                            self.cl_mappings[c] = v
                            
                    with open(mapping_file, "w") as f:
                        json.dump(self.cl_mappings, f, indent=4)
                except Exception as e:
                    print(f"Failed to fetch CL mappings: {e}")
        
        return self.cl_mappings.get(str(cl))

    def get_game_version(self, exe_path):
        """
: reads CrashReportClient.exe (not the
        shipping exe) because the shipping exe only stores the UE engine version
        (e.g. 4.25.0.0) while CrashReportClient has the full Fortnite build
        string like: 4.25.0-14702800+++Fortnite+Release-12.41
        """
        build, cl = "Unknown", "Unknown"
        bin_dir = os.path.dirname(exe_path)
        game_root = os.path.dirname(os.path.dirname(os.path.dirname(bin_dir)))  # up from Win64/Binaries/FortniteGame

        crc_exe = _find_exe(game_root, "CrashReportClient.exe") or \
                  _find_exe(bin_dir,   "CrashReportClient.exe")

        def _parse_prod_string(prod):
            """Extract (release_ver, cl) from a ProductVersion string."""
            b, c = None, None
            if "Release-" in prod:
                b = prod.split("Release-")[-1].split()[0].strip()
            if '-' in prod and '+' in prod:
                try:
                    c = prod.split('-')[1].split('+')[0]
                except Exception:
                    pass
            return b, c

        # --- Try win32api on CrashReportClient.exe first ---
        if crc_exe:
            try:
                import win32api
                lang, cp = win32api.GetFileVersionInfo(crc_exe, r'\VarFileInfo\Translation')[0]
                si = f'\\StringFileInfo\\{lang:04X}{cp:04X}\\ProductVersion'
                prod = win32api.GetFileVersionInfo(crc_exe, si) or ""
                b, c = _parse_prod_string(prod)
                if b: build = b
                if c: cl    = c
                if build != "Unknown":
                    mapped = self.get_cl_mapping(cl)
                    if mapped: build = mapped
                    return build, cl
            except Exception:
                pass


        for scan_path in filter(None, [crc_exe, exe_path]):
            try:
                with open(scan_path, 'rb') as f:
                    raw = f.read(8_000_000)  # 8 MB — covers larger UE5 binaries
                for data in (raw.replace(b'\x00', b''), raw):
                    m = re.search(
                        rb'\d+\.\d+\.\d+-(\d+)\+\+\+Fortnite\+Release-([a-zA-Z0-9\.]+)',
                        data
                    )
                    if m:
                        cl    = m.group(1).decode('utf-8', errors='ignore')
                        build = m.group(2).decode('utf-8', errors='ignore')
                        mapped = self.get_cl_mapping(cl)
                        if mapped: build = mapped
                        return build, cl
                    m2 = re.search(
                        rb'\+\+Fortnite\+Release-(\d+\.\d+)-CL-(\d+)',
                        data
                    )
                    if m2:
                        build = m2.group(1).decode('utf-8', errors='ignore')
                        cl    = m2.group(2).decode('utf-8', errors='ignore')
                        mapped = self.get_cl_mapping(cl)
                        if mapped: build = mapped
                        return build, cl
            except Exception:
                pass

        # --- Last resort: win32api on the shipping exe itself ---
        try:
            import win32api
            lang, cp = win32api.GetFileVersionInfo(exe_path, r'\VarFileInfo\Translation')[0]
            si = f'\\StringFileInfo\\{lang:04X}{cp:04X}\\ProductVersion'
            prod = win32api.GetFileVersionInfo(exe_path, si) or ""
            b, c = _parse_prod_string(prod)
            if b: build = b
            if c: cl    = c
            mapped = self.get_cl_mapping(cl)
            if mapped: build = mapped
        except Exception:
            pass

        # --- Path-based fallback: parse version from directory names in the exe path ---
        if build == "Unknown":
            for part in reversed(exe_path.replace('\\', '/').split('/')):
                m = re.search(r'(?:^|v|Fortnite[\s_]?v?)(\d+\.\d+(?:\.\d+)?)', part, re.IGNORECASE)
                if m:
                    build = m.group(1)
                    cl_m = re.search(r'CL[-_](\d+)', part)
                    if cl_m and cl == "Unknown":
                        cl = cl_m.group(1)
                    break

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
        # --- Toggle: stop if already running ---
        if is_host:
            if hasattr(self, 'host_process') and self.host_process and self.host_process.poll() is None:
                self.host_process.kill()
                return
        else:
            if hasattr(self, 'game_process') and self.game_process and self.game_process.poll() is None:
                self.game_process.kill()
                return

        self.save_config()

        # --- Resolve exe path from build list ---
        selected_name = self.path_var.get()
        exe_path = selected_name
        for b in getattr(self, "builds", []):
            if b.get("name") == selected_name or b.get("path") == selected_name:
                exe_path = b.get("exe", b.get("path", ""))
                break

        if not os.path.exists(exe_path):
            messagebox.showerror("Error", "Game executable not found in path!")
            return

        bin_dir = os.path.dirname(exe_path)

        # --- Port conflict check: game server port must not be 3551 ---
        game_port = self.host_port_var.get().strip()
        if is_host and game_port == "3551":
            messagebox.showerror("Error", "Game server port cannot be 3551 (conflicts with backend).\nChange it in Host > Options.")
            return

        # --- Headless binary patch ---
        if is_host and self.host_headless_var.get():
            self.patch_headless(exe_path)

        # --- Delete Aftermath crash DLL ---
        aftermath = os.path.join(bin_dir, "GFSDK_Aftermath_Lib.x64.dll")
        if os.path.exists(aftermath):
            try:
                os.remove(aftermath)
                print(f"[+] Deleted Aftermath DLL.")
            except Exception as e:
                print(f"[-] Could not delete Aftermath DLL: {e}")

        # --- Write matchmaking IP to config.ini when hosting ---
        if is_host:
            _write_matchmaker_config(self.base_dir, "127.0.0.1", game_port or "7777")

        # --- Detect game major version + cache build info for RPC ---
        _bv, _cl = self.get_game_version(exe_path)
        self._rpc_build_ver = _bv
        self._rpc_cl_ver    = _cl
        major_version = 0
        try:
            major_version = int(_bv.split('.')[0])
        except Exception:
            pass
        print(f"[*] Version detected: build={_bv}  CL={_cl}  major_version={major_version}  rpc_image={_rpc_image(_bv)}")

        # --- Auto-download missing DLLs ---
        dll_dir = os.path.join(self.base_dir, "dlls")
        def _ensure(var, name, zip_url=None, direct_url=None, no_download=False):
            p = var.get()
            if not p or not os.path.exists(p):
                default = os.path.join(dll_dir, name)
                if not no_download:
                    _download_dll(name, default, zip_url, direct_url)
                if os.path.exists(default):
                    var.set(default)
                    self.save_config()
                elif no_download:
                    print(f"[!] {name} not found — place it in the dlls folder manually")

        _auth_fn, _auth_zip, _auth_dir, _auth_nd = _DLL_AUTH_PRESETS.get(
            self.dll_auth_choice_var.get(), _DLL_AUTH_PRESETS["Tellurium 3551"])
        _ensure(self.dll_auth_var, _auth_fn, zip_url=_auth_zip, direct_url=_auth_dir, no_download=_auth_nd)

        _con_fn, _con_zip, _con_dir, _con_nd = _DLL_CONSOLE_PRESETS.get(
            self.dll_console_choice_var.get(), _DLL_CONSOLE_PRESETS["Console"])
        _ensure(self.dll_console_var, _con_fn, zip_url=_con_zip, direct_url=_con_dir, no_download=_con_nd)

        _ensure(self.dll_memory_var, "memory.dll")

        _srv_fn, _srv_zip, _srv_dir, _srv_nd = _DLL_SERVER_PRESETS.get(
            self.dll_server_choice_var.get(), _DLL_SERVER_PRESETS["Reboot"])
        _ensure(self.dll_server_var, _srv_fn, zip_url=_srv_zip, direct_url=_srv_dir, no_download=_srv_nd)

        if self.use_large_pak_var.get():
            _ensure(self.dll_large_pak_var, "LargePakPatch.dll", direct_url=_LARGE_PAK_URL)

        # --- Build auth args using Dart-identical logic ---
        if is_host:
            username = self.settings.get("host_username", "Host")
            password = self.settings.get("host_account_password", "")
        else:
            username = self.settings.get("username", "Player")
            password = self.settings.get("password", "")

        custom_args = self.host_custom_args_var.get() if is_host else ""
        if is_host:
            if game_port:
                custom_args += f" -port={game_port}"
            max_p = self.host_max_players_var.get().strip()
            if max_p:
                custom_args += f" -maxplayers={max_p}"

        args_list = _build_args(
            username, password,
            is_host, self.host_headless_var.get() if is_host else False,
            custom_args.strip()
        )

        launch_cmd = [exe_path] + args_list
        launch_env = os.environ.copy()
        launch_env["OPENSSL_ia32cap"] = "~0x20000000"   #
        # --- Start FortniteLauncher.exe and EAC exe SUSPENDED (bypass EAC) ---
        game_root = bin_dir
        for _ in range(4):
            game_root = os.path.dirname(game_root)

        paused_pids = []
        search_map = {
            _EAC_EXE:      [bin_dir],                              # always in Win64/
            _LAUNCHER_EXE: [game_root, os.path.dirname(bin_dir),   # root, Binaries/, Win64/
                            os.path.dirname(os.path.dirname(bin_dir)), bin_dir],
        }
        for suspended_name, search_dirs in search_map.items():
            sus_exe = None
            for d in search_dirs:
                sus_exe = _find_exe(d, suspended_name)
                if sus_exe:
                    break
            if not sus_exe:
                print(f"[!] {suspended_name} not found — skipping suspension")
                continue
            try:
                sus_proc = subprocess.Popen(
                    [sus_exe],
                    cwd=os.path.dirname(sus_exe),
                    env=launch_env,
                    creationflags=0x08000004
                )
                _nt_suspend_process(sus_proc.pid)
                paused_pids.append(sus_proc.pid)
                print(f"[+] Suspended {suspended_name} (pid={sus_proc.pid})")
            except Exception as e:
                print(f"[-] Could not suspend {suspended_name}: {e}")

        # --- Start the actual game process ---
        proc = subprocess.Popen(
            launch_cmd,
            cwd=bin_dir,
            shell=False,
            env=launch_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            encoding='utf-8',
            errors='replace'
        )
        print(f"[+] Game process started: pid={proc.pid}")

        if is_host:
            self.host_process = proc
            if hasattr(self, 'host_btn'):
                self.host_btn.configure(text="Stop Server", fg_color="#ef4444", hover_color="#dc2626")
        else:
            self.game_process = proc
            if hasattr(self, 'launch_btn'):
                self.launch_btn.configure(text="Stop Client", fg_color="#ef4444", hover_color="#dc2626")

        is_headless = self.host_headless_var.get() if is_host else False
        
        self.update_discord_rpc_state()

        threading.Thread(
            target=self.monitor_process,
            args=(proc, is_host, major_version, paused_pids, _bv),
            daemon=True
        ).start()

    def monitor_process(self, proc, is_host, major_version=0, paused_pids=None, build_ver="Unknown"):
        target_pid = proc.pid
        paused_pids = paused_pids or []

        dll_auth    = self.dll_auth_var.get()
        dll_server  = self.dll_server_var.get()
        dll_memory  = self.dll_memory_var.get()
        dll_console = self.dll_console_var.get()

        if dll_auth and os.path.exists(dll_auth):
            ok = self.python_injector(target_pid, dll_auth)
            print(f"[+] Auth inject: {'OK' if ok else 'FAILED'} ({os.path.basename(dll_auth)})")
            self.after(0, self.update_discord_rpc_state)

        logged_in  = False
        match_over = False

        try:
            for line in iter(proc.stdout.readline, ''):
                if not line:
                    break
                stripped = line.strip()
                if stripped:
                    print("[FN] " + stripped)

                # --- Graceful shutdown ---
                if _SHUTDOWN_LINE in line:
                    print("[*] Detected graceful shutdown.")
                    break

                # --- Corrupted build / crash ---
                if any(e in line for e in _CORRUPTED_ERRORS):
                    print("[-] Corrupted build or crash detected.")
                    self.after(0, lambda: messagebox.showerror(
                        "Build Error",
                        "The game crashed or the build is corrupted.\n"
                        "Try verifying your game files."))
                    break

                # --- Cannot connect to backend ---
                if any(e in line for e in _CONNECT_ERRORS):
                    print("[-] Backend connection error detected.")
                    self.after(0, lambda: messagebox.showerror(
                        "Connection Error",
                        "The game could not connect to the backend (port 3551).\n"
                        "Make sure your backend is running before launching."))
                    break

                # --- Login completed → late injections ---
                # Newer builds (Ch4+): "LogOnline: Region " after login
                if not logged_in and (all(k in line for k in _LOGGED_IN_LINES) or _LOGGED_IN_REGION in line):
                    logged_in = True
                    print("[+] Login detected — performing late injections...")

                    if major_version < 10 and dll_memory and os.path.exists(dll_memory):
                        ok = self.python_injector(target_pid, dll_memory)
                        print(f"[+] Memory inject: {'OK' if ok else 'FAILED'} ({os.path.basename(dll_memory)})")

                    if is_host:
                        port_str = self.host_port_var.get().strip()
                        if port_str.isdigit():
                            _kill_port(int(port_str))
                            print(f"[+] Cleared port {port_str} for game server.")
                        if dll_server and os.path.exists(dll_server):
                            ok = self.python_injector(target_pid, dll_server)
                            print(f"[+] Server DLL inject: {'OK' if ok else 'FAILED'} ({os.path.basename(dll_server)})")
                    else:
                        if dll_console and os.path.exists(dll_console):
                            ok = self.python_injector(target_pid, dll_console)
                            print(f"[+] Console inject: {'OK' if ok else 'FAILED'} ({os.path.basename(dll_console)})")

                    # --- LargePakPatch (custom mods) — only supported on builds >5.10 and <14.40 ---
                    if self.use_large_pak_var.get():
                        try:
                            parts = build_ver.split('.')
                            _pak_ver = float(f"{parts[0]}.{parts[1]}") if len(parts) >= 2 else float(parts[0])
                        except Exception:
                            _pak_ver = 0.0
                        if 5.10 < _pak_ver < 14.40:
                            dll_pak = self.dll_large_pak_var.get()
                            if dll_pak and os.path.exists(dll_pak):
                                ok = self.python_injector(target_pid, dll_pak)
                                print(f"[+] LargePakPatch inject: {'OK' if ok else 'FAILED'} ({os.path.basename(dll_pak)})")
                            else:
                                print("[-] LargePakPatch enabled but DLL not found — skipping.")
                        else:
                            print(f"[*] LargePakPatch skipped — only supported on builds >5.10 and <14.40 (this build: {build_ver})")

                # --- Match ended (host only) ---
                if is_host and _MATCH_END_LINE in line and not match_over:
                    match_over = True
                    print("[*] Match ended (TeamsLeft: 1).")
                    if self.host_autorun_var.get():
                        print(f"[*] Auto-restart in {_REBOOT_DELAY_SECS}s...")
                        time.sleep(_REBOOT_DELAY_SECS)
                        try:
                            proc.kill()
                        except Exception:
                            pass
                        self.after(0, lambda: self.handle_launch(is_host=True))
                        return  # monitor thread exits; new one will be created by handle_launch
                    else:
                        time.sleep(_REBOOT_DELAY_SECS)
                        try:
                            proc.kill()
                        except Exception:
                            pass
                        break

        except Exception as e:
            print(f"[-] Log stream error: {e}")

        try:
            proc.wait()
        except Exception:
            pass

        for pid in paused_pids:
            try:
                os.kill(pid, 9)
                print(f"[+] Killed suspended process pid={pid}")
            except Exception:
                pass

        def _revert():
            if is_host:
                self.host_process = None
                if hasattr(self, 'host_btn'):
                    self.host_btn.configure(text="Host Server", fg_color=_T["accent"], hover_color=_T["accent_hover"])
            else:
                self.game_process = None
                if hasattr(self, 'launch_btn'):
                    self.launch_btn.configure(text="Play", fg_color=_T["accent"], hover_color=_T["accent_hover"])

            any_running = (
                (hasattr(self, 'host_process') and self.host_process and self.host_process.poll() is None) or
                (hasattr(self, 'game_process') and self.game_process and self.game_process.poll() is None)
            )
            if not any_running:
                self.game_running = False
                
            self.after(500, self.update_discord_rpc_state)

        self.after(0, _revert)
            
if __name__ == "__main__":
    app = RebootLauncherApp()
    app.mainloop()
