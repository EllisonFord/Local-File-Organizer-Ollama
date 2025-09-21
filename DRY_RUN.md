# Dry Run mode in Local File Organizer (Ollama)

If you saw the phrase “run dry,” it refers to this program’s Dry Run mode. A dry run means the app previews what it would do without making any changes to your files. It’s a safety-first way to see the plan before committing.

## What Dry Run does
- Scans your input folder and computes the exact operations it would perform (where each file would go and how it would be linked or copied).
- Prints a simulated directory structure of the destination (no folders are actually created).
- Shows a summary by folder and by file type, and estimates disk usage when the link mode is copy.
- Writes all messages to a per‑run log file in the logs/<timestamp>/ folder (or a custom log path if you provide one).
- Skips any filesystem‑changing steps. No files are copied, linked, moved, or renamed.

In the console/log you’ll see lines like:
- "Proposed directory structure:" followed by a preview tree rooted at your output path
- "Summary:"
- "Dry run mode: no changes were made."

## How to turn Dry Run on/off
Dry Run is OFF by default unless you explicitly enable it. You can control it in three ways:

1) Command line
- Enable (preview only):
  - python main.py --mode type --input C:\path\to\data --output C:\path\to\organized --dry-run
- Disable (perform changes):
  - Omit the flag entirely. Example:
  - python main.py --mode type --input C:\path\to\data --output C:\path\to\organized

2) GUI (if available on your system)
- When the small window opens, use the checkbox "Dry run (preview only)".

3) JSON config (organizer.config.json)
- Place this file next to main.py or point to it with --config. Example:
  {
    "input_path": "C:\\path\\to\\data",
    "output_path": "C:\\path\\to\\organized",
    "dry_run": false,
    "link": "hard",            
    "mode": "type"             
  }
- Set dry_run to false to actually perform changes, or true to preview only.

Note: Precedence is CLI > config > defaults. That is, command‑line flags override config values.

## What happens under the hood
- The app collects files and computes a list of "operations" describing where each file would go and how it would be written (hardlink, symlink, or copy). See:
  - main.py (overall orchestration; preview and summary)
  - data_processing_common.py:
    - process_files_by_date/process_files_by_type (build operation lists)
    - execute_operations (actually applies operations)
- When dry_run is true, main.py stops before calling execute_operations, so:
  - No directories are created
  - No links or copies are made
  - You only get the simulated tree and the textual summary/logs

## Link strategies (what would happen on a real run)
- hard: Create hardlinks (default). Fast and space‑efficient but requires same filesystem/volume.
- soft: Create symlinks. May require elevated privileges on Windows depending on policy.
- copy: Copy files. Uses disk space; preview shows an estimated total size when copy is selected.

You choose the strategy with --link hard|soft|copy (or link in config). In dry run, the strategy only affects the preview text; it does not change the filesystem.

## Typical usage
- First preview safely:
  - python main.py --mode date --input C:\photos --output C:\photos\organized --dry-run
- If the plan looks good, run for real:
  - python main.py --mode date --input C:\photos --output C:\photos\organized

If you don’t pass --mode/--input/--output, the app can prompt interactively. In non‑dry‑run interactive mode, you’ll be asked to confirm before it performs changes. If you supply --mode (non‑interactive), it proceeds automatically after the preview step (unless dry‑run is still on).

## Where to see the preview
- Console output (unless you use --silent)
- Log file: logs/<timestamp>/operation.log (or your chosen path via --log-dir/--log-file)

## TL;DR
- "Run dry" = Dry Run = preview only; the program does not change your files.
- Default: OFF. Enable explicitly with --dry-run to preview without making changes.
- Use it to verify the proposed folder layout and file placements before committing.
