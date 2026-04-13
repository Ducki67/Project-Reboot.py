import sys
import win32api

if len(sys.argv) < 2:
    print("Usage: detect_ver.py <path to FortniteClient-Win64-Shipping.exe>")
    sys.exit(1)

exe = sys.argv[1]
info = win32api.GetFileVersionInfo(exe, '\\')
ms = info['FileVersionMS']
ls = info['FileVersionLS']
print(f"{ms >> 16}.{ms & 0xFFFF}.{ls >> 16}.{ls & 0xFFFF}")
try:
    lang, codepage = win32api.GetFileVersionInfo(exe, '\\VarFileInfo\\Translation')[0]
    strInfo = u'\\StringFileInfo\\%04X%04X\\%s' % (lang, codepage, "ProductVersion")
    print(win32api.GetFileVersionInfo(exe, strInfo))
except Exception as e:
    print(e)