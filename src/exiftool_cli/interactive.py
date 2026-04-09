"""Interactive mode for exiftool-cli."""

import os
import subprocess
import sys
from pathlib import Path

from .core import ExifTool, ExifError
from .formatters import TableFormatter, JsonFormatter, CsvFormatter
from .utils import (
    Colors, success, error, warning, info, header, confirm,
    validate_file, validate_folder, get_image_files,
    ensure_directory, get_output_path, format_size, get_file_size_diff_str,
    SUPPORTED_EXTENSIONS
)

TKINTER_AVAILABLE = False

try:
    import tkinter as tk
    from tkinter import filedialog
    TKINTER_AVAILABLE = True
except ImportError:
    pass


class InteractiveMode:
    """Interactive menu-driven interface."""
    
    def __init__(self):
        self.current_dir = Path.cwd()
        self.exif_tool = ExifTool()
        self.selected_files = []
    
    def run(self):
        """Run the interactive menu loop."""
        self._show_banner()
        self.selected_files = []

        while True:
            self._select_photo()

            if not self.selected_files:
                break

            self._show_exif_preview()

            self._show_simple_menu()
    
    def _show_banner(self):
        """Display welcome banner."""
        banner = f"""
{Colors.BOLD}{Colors.CYAN}╔══════════════════════════════════════════╗{Colors.RESET}
{Colors.BOLD}{Colors.CYAN}║        EXIFTOOL-CLI v1.0.0              ║{Colors.RESET}
{Colors.BOLD}{Colors.CYAN}║   Extract, Export & Remove EXIF Data    ║{Colors.RESET}
{Colors.BOLD}{Colors.CYAN}╚══════════════════════════════════════════╝{Colors.RESET}
"""
        print(banner)
    
    def _show_main_menu(self):
        """Display main menu options."""
        menu = f"""
{Colors.BOLD}Main Menu{Colors.RESET}
{'─' * 40}
  {Colors.GREEN}[1]{Colors.RESET} Select photo
  {Colors.GREEN}[2]{Colors.RESET} Select folder
  {Colors.GREEN}[3]{Colors.RESET} Select files
  {Colors.GREEN}[4]{Colors.RESET} Extract EXIF
  {Colors.GREEN}[5]{Colors.RESET} Export EXIF
  {Colors.GREEN}[6]{Colors.RESET} Remove EXIF
  {Colors.GREEN}[7]{Colors.RESET} Show selected files ({len(self.selected_files)})
  {Colors.RED}[0]{Colors.RESET} Exit
"""
        print(menu)
    
    def _select_folder(self):
        """Select a folder and list images."""
        folder = input(f"{Colors.CYAN}Enter folder path (or Enter for current): {Colors.RESET}").strip()
        
        if not folder:
            folder_path = self.current_dir
        else:
            folder_path = Path(folder)
        
        is_valid, err_msg = validate_folder(folder_path)
        if not is_valid:
            error(err_msg)
            return
        
        files = get_image_files(folder_path, recursive=False)
        
        if not files:
            warning(f"No images found in {folder_path}")
            return
        
        info(f"Found {len(files)} images in {folder_path}")
        print(f"\n{Colors.BOLD}Images:{Colors.RESET}")
        
        for i, f in enumerate(files[:20], 1):
            print(f"  {Colors.YELLOW}[{i}]{Colors.RESET} {f.name}")
        
        if len(files) > 20:
            print(f"  {Colors.DIM}... and {len(files) - 20} more{Colors.RESET}")
        
        select = input(f"\n{Colors.CYAN}Select files (1-{min(20, len(files))}) or 'a' for all: {Colors.RESET}").strip().lower()
        
        if select == "a":
            self.selected_files = files
            success(f"Selected all {len(files)} files")
        else:
            try:
                indices = [int(x) for x in select.split(",")]
                self.selected_files = [files[i - 1] for i in indices if 1 <= i <= len(files)]
                success(f"Selected {len(self.selected_files)} files")
            except (ValueError, IndexError):
                warning("Invalid selection")
    
    def _select_files(self):
        """Select individual files."""
        path_input = input(f"{Colors.CYAN}Enter file paths (comma-separated): {Colors.RESET}").strip()
        
        if not path_input:
            warning("No files specified")
            return
        
        new_files = []
        for path_str in path_input.split(","):
            path = Path(path_str.strip())
            is_valid, err_msg = validate_file(path)
            if is_valid:
                new_files.append(path)
            else:
                warning(f"Skipped {path}: {err_msg}")
        
        if new_files:
            self.selected_files.extend(new_files)
            success(f"Added {len(new_files)} files (total: {len(self.selected_files)})")
    
    def _select_photo(self):
        """Select a photo using native file picker dialog or console input."""
        if TKINTER_AVAILABLE:
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)

            filetypes = []
            for ext in SUPPORTED_EXTENSIONS:
                filetypes.append((f"*{ext}", f"*{ext}"))

            file_paths = filedialog.askopenfilenames(
                parent=root,
                title="Select Photo(s)",
                filetypes=filetypes
            )

            root.destroy()

            if not file_paths:
                info("No files selected")
                return

            new_files = []
            for path_str in file_paths:
                path = Path(path_str)
                is_valid, err_msg = validate_file(path)
                if is_valid:
                    new_files.append(path)
                else:
                    warning(f"Skipped {path}: {err_msg}")

            if new_files:
                self.selected_files.extend(new_files)
                success(f"Added {len(new_files)} file(s) (total: {len(self.selected_files)})")
        elif sys.platform == "darwin":
            paths = self._open_file_dialog_applescript()
            if not paths:
                info("No files selected")
                return

            new_files = []
            for path in paths:
                is_valid, err_msg = validate_file(path)
                if is_valid:
                    new_files.append(path)
                else:
                    warning(f"Skipped {path}: {err_msg}")

            if new_files:
                self.selected_files.extend(new_files)
                success(f"Added {len(new_files)} file(s) (total: {len(self.selected_files)})")
        else:
            path_input = input(f"{Colors.CYAN}Enter file path: {Colors.RESET}").strip()
            if not path_input:
                warning("No file specified")
                return

            path = Path(path_input)
            is_valid, err_msg = validate_file(path)
            if is_valid:
                self.selected_files.append(path)
                success(f"Selected {path.name}")
            else:
                error(err_msg)

    def _open_file_dialog_applescript(self):
        """Open file dialog using AppleScript on macOS."""
        extensions = " ".join(f"*{ext}" for ext in SUPPORTED_EXTENSIONS)
        script = (
            f'set fileTypes to {{"{extensions}"}}\n'
            'set chosenFiles to (choose file of type fileTypes with multiple selections allowed)\n'
            'set chosenPaths to {{}}\n'
            'repeat with aFile in chosenFiles\n'
            '    set end of chosenPaths to POSIX path of aFile\n'
            'end repeat\n'
            'set AppleScript\'s text item delimiters to {"|"}\n'
            'chosenPaths as string'
        )
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0 and result.stdout.strip():
                paths = result.stdout.strip().split("|")
                return [Path(p.strip()) for p in paths if p.strip()]
        except Exception:
            pass
        return []
    
    def _show_selected_files(self):
        """Display currently selected files."""
        if not self.selected_files:
            warning("No files selected")
            return
        
        print(f"\n{Colors.BOLD}Selected Files ({len(self.selected_files)}):{Colors.RESET}")
        for i, f in enumerate(self.selected_files, 1):
            print(f"  {Colors.YELLOW}[{i}]{Colors.RESET} {f}")
    
    def _extract_selected(self):
        """Extract EXIF from selected files."""
        if not self.selected_files:
            warning("No files selected. Use options 1, 2, or 3 first.")
            return
        
        formatter = TableFormatter()
        
        for file_path in self.selected_files:
            try:
                exif_data = self.exif_tool.extract(file_path)
                output = formatter.format(exif_data, file_path.name)
                print(output)
            except ExifError as e:
                warning(f"Skipped {file_path.name}: {e}")
    
    def _export_selected(self):
        """Export EXIF from selected files."""
        if not self.selected_files:
            warning("No files selected. Use options 1, 2, or 3 first.")
            return
        
        fmt = input(f"{Colors.CYAN}Export format (json/csv) [json]: {Colors.RESET}").strip().lower() or "json"
        
        if fmt not in {"json", "csv"}:
            error("Invalid format. Use 'json' or 'csv'")
            return
        
        out_dir = input(f"{Colors.CYAN}Output directory [./]: {Colors.RESET}").strip()
        output_dir = Path(out_dir) if out_dir else Path("./")
        ensure_directory(output_dir)
        
        for file_path in self.selected_files:
            try:
                exif_data = self.exif_tool.extract(file_path)
                out_path = output_dir / f"{file_path.stem}.{fmt}"
                
                if fmt == "json":
                    formatter = JsonFormatter()
                    formatter.to_file(exif_data, file_path.name, out_path)
                else:
                    formatter = CsvFormatter()
                    formatter.to_file(exif_data, file_path.name, out_path)
                
                success(f"Exported {file_path.name} → {out_path}")
            except ExifError as e:
                warning(f"Failed {file_path.name}: {e}")
    
    def _remove_selected(self):
        """Remove EXIF from selected files."""
        if not self.selected_files:
            warning("No files selected. Use options 1, 2, or 3 first.")
            return
        
        keep_gps = confirm("Keep GPS data?", default=False)
        
        out_dir = input(f"{Colors.CYAN}Output directory [./]: {Colors.RESET}").strip()
        output_dir = Path(out_dir) if out_dir else Path("./")
        ensure_directory(output_dir)
        
        if not confirm(f"Remove EXIF from {len(self.selected_files)} files?", default=False):
            info("Cancelled")
            return
        
        for file_path in self.selected_files:
            try:
                out_path = output_dir / f"{file_path.stem}_clean{file_path.suffix}"
                self.exif_tool.remove(file_path, out_path, keep_gps=keep_gps)
                
                size_info = get_file_size_diff_str(file_path, out_path)
                success(f"Removed {file_path.name} → {out_path.name}")
                if size_info:
                    print(f"    {Colors.DIM}Size: {size_info}{Colors.RESET}")
            except ExifError as e:
                warning(f"Failed {file_path.name}: {e}")

    def _show_exif_preview(self):
        """Show EXIF preview for selected files."""
        formatter = TableFormatter()
        for file_path in self.selected_files:
            try:
                exif_data = self.exif_tool.extract(file_path)
                output = formatter.format(exif_data, file_path.name)
                print(output)
            except ExifError as e:
                warning(f"Skipped {file_path.name}: {e}")

    def _show_simple_menu(self):
        """Display simple menu after file selection."""
        print(f"""
{Colors.BOLD}What would you like to do?{Colors.RESET}
{'─' * 40}
  {Colors.GREEN}[1]{Colors.RESET} Select more photos
  {Colors.GREEN}[2]{Colors.RESET} Export EXIF (JSON/CSV)
  {Colors.GREEN}[3]{Colors.RESET} Remove EXIF
  {Colors.RED}[0]{Colors.RESET} Exit
""")
        choice = input(f"{Colors.CYAN}Select option: {Colors.RESET}").strip()

        if choice == "1":
            pass
        elif choice == "2":
            self._export_selected()
        elif choice == "3":
            self._remove_selected()
        else:
            info("Exiting...")
            self.selected_files = []
