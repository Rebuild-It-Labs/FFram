"""CLI entry point."""

import sys
import os

# Force UTF-8 encoding on Windows
if os.name == "nt":
    os.system("chcp 65001 > NUL 2>&1")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    os.environ["PYTHONIOENCODING"] = "utf-8"

import argparse
from pathlib import Path
from InquirerPy import inquirer

from ffram.ui.console import console, print_banner
from ffram.ui.menu import (
    show_main_menu,
    show_category_operations,
    show_search_menu,
    show_gpu_info,
    execute_operation,
)


def main():
    """Main loop."""
    parser = argparse.ArgumentParser(description="ffram - Fast FFmpeg Renderer for Audio and Moving-pictures")
    parser.add_argument("--file", "-f", help="Direct input file path")
    args, _ = parser.parse_known_args()

    preselected_file = None
    if args.file:
        candidate = Path(args.file.strip('"').strip("'"))
        if candidate.exists():
            preselected_file = candidate

    try:
        os.system("cls" if os.name == "nt" else "clear")
        print_banner()

        if preselected_file:
            console.print(f"  [dim]Pre-selected file:[/dim] [path]{preselected_file}[/path]\n")

        while True:
            try:
                category = show_main_menu()

                if category == "__EXIT__":
                    console.print("\n  [dim]Goodbye![/dim]\n")
                    break

                elif category == "__SEARCH__":
                    op_id = show_search_menu()
                    if op_id and op_id != "__BACK__":
                        execute_operation(op_id, initial_file=preselected_file)
                        preselected_file = None

                elif category == "__GPU_INFO__":
                    show_gpu_info()
                    inquirer.text(message="Press Enter to return to main menu...", default="").execute()

                else:
                    # User picked a category from the 18 categories
                    while True:
                        op_id = show_category_operations(category)
                        if not op_id or op_id == "__BACK__":
                            break
                        execute_operation(op_id, initial_file=preselected_file)
                        preselected_file = None
                        break  # Return to main menu after running the operation
                
            except KeyboardInterrupt:
                console.print("\n  [warning]Returning to main menu...[/warning]")
                continue

    except KeyboardInterrupt:
        console.print("\n  [dim]Goodbye![/dim]\n")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n  [error]Fatal Error: {e}[/error]\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
