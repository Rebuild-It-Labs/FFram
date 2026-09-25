"""
scripts/install_context_menu.py - Windows Explorer right-click context menu installer.

Adds "Process with ffram" to the right-click menu for:
  - All files (*)
  - Directories (folder background)

Requires Administrator privileges to modify the Windows Registry.
Run: python scripts/install_context_menu.py --install
      python scripts/install_context_menu.py --uninstall
"""

import sys
import os
import winreg
import argparse
from pathlib import Path


MENU_NAME = "ffram"
MENU_TEXT = "Process with ffram"
ICON_INDEX = 0  # Default icon

# Path to the Python executable and the run_ffram.py script
PYTHON_EXE = sys.executable
SCRIPT_PATH = str(Path(__file__).resolve().parent.parent / "run_ffram.py")


def get_command(file_arg: str = "%1") -> str:
    """Build the command string for the context menu."""
    return f'"{PYTHON_EXE}" "{SCRIPT_PATH}" --file "{file_arg}"'


def install_context_menu():
    """Install the context menu entries in the Windows Registry."""
    print(f"Installing '{MENU_TEXT}' context menu...")
    print(f"  Python: {PYTHON_EXE}")
    print(f"  Script: {SCRIPT_PATH}")

    # Register for all files (*)
    try:
        key_path = f"*\\shell\\{MENU_NAME}"
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path) as key:
            winreg.SetValue(key, "", winreg.REG_SZ, MENU_TEXT)
            winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, f"{PYTHON_EXE},{ICON_INDEX}")

        cmd_path = f"{key_path}\\command"
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, cmd_path) as key:
            winreg.SetValue(key, "", winreg.REG_SZ, get_command("%1"))

        print("  ✓ Registered for all files")
    except PermissionError:
        print("  ✗ Permission denied for files. Run as Administrator.")
        return False

    # Register for directory background
    try:
        key_path = f"Directory\\Background\\shell\\{MENU_NAME}"
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path) as key:
            winreg.SetValue(key, "", winreg.REG_SZ, f"{MENU_TEXT} (Batch)")
            winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, f"{PYTHON_EXE},{ICON_INDEX}")

        cmd_path = f"{key_path}\\command"
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, cmd_path) as key:
            winreg.SetValue(key, "", winreg.REG_SZ, get_command("%V"))

        print("  ✓ Registered for directory backgrounds")
    except PermissionError:
        print("  ✗ Permission denied for directories. Run as Administrator.")
        return False

    # Register for folders
    try:
        key_path = f"Directory\\shell\\{MENU_NAME}"
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path) as key:
            winreg.SetValue(key, "", winreg.REG_SZ, f"{MENU_TEXT} (Folder)")
            winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, f"{PYTHON_EXE},{ICON_INDEX}")

        cmd_path = f"{key_path}\\command"
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, cmd_path) as key:
            winreg.SetValue(key, "", winreg.REG_SZ, get_command("%1"))

        print("  ✓ Registered for folders")
    except PermissionError:
        print("  ✗ Permission denied for folders. Run as Administrator.")
        return False

    print("\n✓ Context menu installed successfully!")
    print("  Right-click any file or folder to see the new option.")
    return True


def uninstall_context_menu():
    """Remove the context menu entries from the Windows Registry."""
    print(f"Uninstalling '{MENU_TEXT}' context menu...")

    paths = [
        f"*\\shell\\{MENU_NAME}\\command",
        f"*\\shell\\{MENU_NAME}",
        f"Directory\\Background\\shell\\{MENU_NAME}\\command",
        f"Directory\\Background\\shell\\{MENU_NAME}",
        f"Directory\\shell\\{MENU_NAME}\\command",
        f"Directory\\shell\\{MENU_NAME}",
    ]

    for path in paths:
        try:
            winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, path)
            print(f"  ✓ Removed: {path}")
        except FileNotFoundError:
            pass  # Key doesn't exist
        except PermissionError:
            print(f"  ✗ Permission denied: {path}")

    print("\n✓ Context menu uninstalled.")


def main():
    parser = argparse.ArgumentParser(description="ffram Context Menu Installer")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--install", action="store_true", help="Install context menu")
    group.add_argument("--uninstall", action="store_true", help="Uninstall context menu")

    args = parser.parse_args()

    if args.install:
        install_context_menu()
    elif args.uninstall:
        uninstall_context_menu()


if __name__ == "__main__":
    main()
