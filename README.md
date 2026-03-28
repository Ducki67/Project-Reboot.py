# Project-Reboot.py
Project Reboot launcher in python |  just a tiny ass made when i was bored :P

This tiny project made for fun   and most of the code is kinda  AI made since i dont really know much python tbh with anyone  and i think i know more JS or Batch than this shit. :)
---

## 🛠️ Requirements

If you want to run the raw python code yourself:
- Python 3.10+
- Install dependencies: `pip install customtkinter pillow psutil pypresence`

## 📦 How to Build & Package

We have included automated batch scripts to do all the heavy lifting. You don't need to manually type any PyInstaller commands!

**Navigating the Build Scripts (Inside the `Launcher/` folder)**:

1. **`compile.bat`** (Quick Compile)
   - Automatically installs PyInstaller if you don't have it.
   - Compiles `main.py` into a portable Windows executable.
   - Output goes to: `Launcher/dist/Reboot.py.exe`.

2. **`production.bat`** (Full Release Builder)
   - Re-compiles the executable to ensure it's latest.
   - Bundles the `Reboot.py.exe` alongside the `assets/` and `dlls/` folders into a clean `ReleaseBuild/` folder.
   - **Prompts you:** "Do you want to ZIP the portable release?" (Uses Python to safely zip it into `Reboot.py_Portable.zip`).
   - **Prompts you:** "Do you want to build the Desktop Installer?" (Requires [Inno Setup 6](https://jrsoftware.org/isdl.php)). If yes, spits out a professional installer in the `Output/` folder!

## 🚀 Usage 

Once you compile the project, your friends and users **do not** need Python installed. 
Just send them the `Reboot.py_Portable.zip` or the Installer, and they can run the launcher right out of the box!