"""
Simple GUI helpers for Local File Organizer.
Uses the standard library Tkinter to gather input interactively when available.
"""
from __future__ import annotations

import os
from typing import Optional, Dict, Any


def is_gui_available() -> bool:
    """Return True if a GUI can be rendered using Tkinter.

    We try to import tkinter and briefly instantiate a root window. On
    headless systems (e.g., no DISPLAY), this will fail and we return False.
    """
    try:
        import tkinter as tk  # noqa: F401
    except Exception:
        return False

    # On Unix-like systems, DISPLAY must be set
    if os.name != "nt":
        if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
            return False

    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        root.update_idletasks()
        root.destroy()
        return True
    except Exception:
        return False


def prompt_user_for_config(defaults: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Show a small window to pick source/target folders and options.

    Returns a dict with keys: input_path, output_path, silent, dry_run, link, mode
    or None if the user cancels.
    """
    defaults = defaults or {}

    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox

    result: Dict[str, Any] = {}

    root = tk.Tk()
    root.title("Local File Organizer - Setup")
    root.geometry("560x280")
    root.resizable(False, False)

    # Variables
    src_var = tk.StringVar(value=str(defaults.get("input_path", "")))
    dst_var = tk.StringVar(value=str(defaults.get("output_path", "")))
    silent_var = tk.BooleanVar(value=bool(defaults.get("silent", False)))
    dryrun_var = tk.BooleanVar(value=bool(defaults.get("dry_run", True)))
    link_var = tk.StringVar(value=str(defaults.get("link", "hard")))
    mode_var = tk.StringVar(value=str(defaults.get("mode") or ""))

    def browse_src():
        path = filedialog.askdirectory(title="Choose source folder")
        if path:
            src_var.set(path)
            # If destination empty, suggest default under source
            if not dst_var.get().strip():
                dst_var.set(os.path.join(path, "organized_folder"))

    def browse_dst():
        path = filedialog.askdirectory(title="Choose target folder")
        if path:
            dst_var.set(path)

    def on_ok():
        src = src_var.get().strip()
        dst = dst_var.get().strip()
        if not src:
            messagebox.showerror("Missing Source", "Please choose a source folder.")
            return
        if not os.path.exists(src) or not os.path.isdir(src):
            messagebox.showerror("Invalid Source", "The source folder does not exist or is not a directory.")
            return
        if not dst:
            dst = os.path.join(src, "organized_folder")
        # Don't create here; just return
        result.update({
            "input_path": src,
            "output_path": dst,
            "silent": bool(silent_var.get()),
            "dry_run": bool(dryrun_var.get()),
            "link": link_var.get(),
            "mode": mode_var.get() or None,
        })
        root.destroy()

    def on_cancel():
        root.destroy()

    # Layout
    pad = {"padx": 8, "pady": 6}

    frm = ttk.Frame(root)
    frm.pack(fill=tk.BOTH, expand=True, **pad)

    # Source
    ttk.Label(frm, text="Source folder:").grid(row=0, column=0, sticky="w")
    src_entry = ttk.Entry(frm, textvariable=src_var, width=52)
    src_entry.grid(row=1, column=0, columnspan=2, sticky="we")
    ttk.Button(frm, text="Browse...", command=browse_src).grid(row=1, column=2, sticky="e")

    # Destination
    ttk.Label(frm, text="Target folder:").grid(row=2, column=0, sticky="w")
    dst_entry = ttk.Entry(frm, textvariable=dst_var, width=52)
    dst_entry.grid(row=3, column=0, columnspan=2, sticky="we")
    ttk.Button(frm, text="Browse...", command=browse_dst).grid(row=3, column=2, sticky="e")

    # Options row
    opts = ttk.Frame(frm)
    opts.grid(row=4, column=0, columnspan=3, sticky="we", pady=(8, 0))
    ttk.Checkbutton(opts, text="Silent mode", variable=silent_var).pack(side=tk.LEFT, padx=(0, 12))
    ttk.Checkbutton(opts, text="Dry run (preview only)", variable=dryrun_var).pack(side=tk.LEFT, padx=(0, 12))

    # Link strategy
    link_frame = ttk.Frame(frm)
    link_frame.grid(row=5, column=0, columnspan=3, sticky="w")
    ttk.Label(link_frame, text="Link strategy:").pack(side=tk.LEFT)
    link_cbx = ttk.Combobox(link_frame, textvariable=link_var, state="readonly", width=10,
                             values=["hard", "soft", "copy"])  # map later in main
    link_cbx.pack(side=tk.LEFT, padx=(6, 0))
    if link_var.get() not in ("hard", "soft", "copy"):
        link_var.set("hard")

    # Mode (optional)
    mode_frame = ttk.Frame(frm)
    mode_frame.grid(row=6, column=0, columnspan=3, sticky="w", pady=(6, 0))
    ttk.Label(mode_frame, text="Mode:").pack(side=tk.LEFT)
    for label, val in [("Content", "content"), ("Date", "date"), ("Type", "type"), ("Test", "test")]:
        ttk.Radiobutton(mode_frame, text=label, value=val, variable=mode_var).pack(side=tk.LEFT, padx=(8, 0))

    # Buttons
    btns = ttk.Frame(frm)
    btns.grid(row=7, column=0, columnspan=3, sticky="e", pady=(14, 0))
    ttk.Button(btns, text="Cancel", command=on_cancel).pack(side=tk.RIGHT, padx=(6, 0))
    ttk.Button(btns, text="Start", command=on_ok).pack(side=tk.RIGHT)

    # Focus and run
    src_entry.focus_set()
    root.mainloop()

    return result or None
