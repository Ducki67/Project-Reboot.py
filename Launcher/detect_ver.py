import win32api
info = win32api.GetFileVersionInfo(r'D:\FortniteBuilds\Ch1\Fortnite v3.6\FortniteGame\Binaries\Win64\FortniteClient-Win64-Shipping.exe', '\\')
ms = info['FileVersionMS']
ls = info['FileVersionLS']
print (f"{ms >> 16}.{ms & 0xFFFF}.{ls >> 16}.{ls & 0xFFFF}")
try:
    # Try getting the exact strings
    lang, codepage = win32api.GetFileVersionInfo(r'D:\FortniteBuilds\Ch1\Fortnite v3.6\FortniteGame\Binaries\Win64\FortniteClient-Win64-Shipping.exe', '\\VarFileInfo\\Translation')[0]
    strInfo = u'\\StringFileInfo\\%04X%04X\\%s' % (lang, codepage, "ProductVersion")
    print(win32api.GetFileVersionInfo(r'D:\FortniteBuilds\Ch1\Fortnite v3.6\FortniteGame\Binaries\Win64\FortniteClient-Win64-Shipping.exe', strInfo))
except Exception as e:
    print(e)