import os
import time
import argparse
import json
from datetime import datetime

from file_utils import (
    display_directory_tree,
    collect_file_paths,
    separate_files_by_type,
    read_file_data
)

from data_processing_common import (
    compute_operations,
    execute_operations,
    process_files_by_date,
    process_files_by_type,
)

from text_data_processing import (
    process_text_files
)

from image_data_processing import (
    process_image_files
)

from output_filter import filter_specific_output  # Import the context manager
from ollama_client import OllamaVLMInference, OllamaTextInference  # Use Ollama wrappers

def ensure_nltk_data():
    """Ensure NLTK resources are available without forcing network downloads.
    Checks for required corpora/tokenizers and skips downloads by default to avoid SSL errors.
    If you explicitly want auto-downloads, set env var NLTK_AUTO_DOWNLOAD=1.
    """
    import os as _os
    import nltk
    from nltk.data import find

    resources = {
        'tokenizers/punkt': 'punkt',
        'corpora/stopwords': 'stopwords',
        'corpora/wordnet': 'wordnet',
    }

    missing = []
    for path, pkg in resources.items():
        try:
            find(path)
        except LookupError:
            missing.append(pkg)

    # By default, do not attempt network downloads; rely on offline fallbacks.
    if not missing:
        return

    if _os.environ.get('NLTK_AUTO_DOWNLOAD', '').lower() in ('1', 'true', 'yes'):  # optional
        for pkg in missing:
            try:
                nltk.download(pkg, quiet=True)
            except Exception:
                # Ignore any downloader errors; downstream code has fallbacks.
                pass

# Initialize models
image_inference = None
text_inference = None

def initialize_models(image_model: str | None = None, text_model: str | None = None, base_url: str | None = None):
    """Initialize the models if they haven't been initialized yet.
    Allows overriding model names and Ollama base URL.
    """
    global image_inference, text_inference
    if image_inference is None or text_inference is None:
        # Initialize the models (using Ollama models)
        image_model = image_model or "llava:7b"
        text_model = text_model or "llama3.2:3b"

        # Use the filter_specific_output context manager
        with filter_specific_output():
            # Initialize the image inference model (wrapper over Ollama vision model)
            image_inference = OllamaVLMInference(model=image_model, base_url=base_url)

            # Initialize the text inference model (wrapper over Ollama text model)
            text_inference = OllamaTextInference(model=text_model, base_url=base_url)
        print("**----------------------------------------------**")
        print("**       Ollama vision model initialized        **")
        print("**       Ollama text model initialized          **")
        print("**----------------------------------------------**")

def simulate_directory_tree(operations, base_path):
    """Simulate the directory tree based on the proposed operations."""
    tree = {}
    for op in operations:
        rel_path = os.path.relpath(op['destination'], base_path)
        parts = rel_path.split(os.sep)
        current_level = tree
        for part in parts:
            if part not in current_level:
                current_level[part] = {}
            current_level = current_level[part]
    return tree

def print_simulated_tree(tree, prefix=''):
    """Print the simulated directory tree."""
    pointers = ['├── '] * (len(tree) - 1) + ['└── '] if tree else []
    for pointer, key in zip(pointers, tree):
        print(prefix + pointer + key)
        if tree[key]:  # If there are subdirectories or files
            extension = '│   ' if pointer == '├── ' else '    '
            print_simulated_tree(tree[key], prefix + extension)

def get_yes_no(prompt):
    """Prompt the user for a yes/no response."""
    while True:
        response = input(prompt).strip().lower()
        if response in ('yes', 'y'):
            return True
        elif response in ('no', 'n'):
            return False
        elif response == '/exit':
            print("Exiting program.")
            exit()
        else:
            print("Please enter 'yes' or 'no'. To exit, type '/exit'.")

def get_mode_selection():
    """Prompt the user to select a mode."""
    while True:
        print("Please choose the mode to organize your files:")
        print("1. By Content")
        print("2. By Date")
        print("3. By Type")
        print("4. Test (simulate AI; organize by type only)")
        response = input("Enter 1, 2, 3, or 4 (or type '/exit' to exit): ").strip()
        if response == '/exit':
            print("Exiting program.")
            exit()
        elif response == '1':
            return 'content'
        elif response == '2':
            return 'date'
        elif response == '3':
            return 'type'
        elif response == '4':
            return 'test'
        else:
            print("Invalid selection. Please enter 1, 2, 3, or 4. To exit, type '/exit'.")

def parse_cli_and_config():
    parser = argparse.ArgumentParser(description="Local File Organizer (Ollama)")
    parser.add_argument("--mode", choices=["content", "date", "type", "test"], help="Organization mode")
    parser.add_argument("--input", dest="input_path", help="Input file or directory")
    parser.add_argument("--output", dest="output_path", help="Output directory")
    parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Preview only; do not make changes")
    parser.add_argument("--silent", dest="silent", action="store_true", help="Do not print to console; write logs only")
    parser.add_argument("--log-dir", dest="log_dir", help="Directory to store logs (default: logs/<timestamp>)")
    parser.add_argument("--log-file", dest="log_file", help="Explicit log file path (overrides log-dir)")
    parser.add_argument("--model-text", dest="model_text", help="Text model name (e.g., llama3.2:3b)")
    parser.add_argument("--model-image", dest="model_image", help="Image model name (e.g., llava:7b)")
    parser.add_argument("--ollama-url", dest="ollama_url", help="Base URL for Ollama (e.g., http://localhost:11434)")
    parser.add_argument("--link", choices=["hard", "soft", "copy"], help="Link strategy: hard=hardlink, soft=symlink, copy=copy files")
    parser.add_argument("--config", dest="config_path", help="Path to JSON config (optional)")
    args = parser.parse_args()

    cfg = {}
    # Load config from file if provided or default
    candidate_paths = []
    if args.config_path:
        candidate_paths.append(args.config_path)
    candidate_paths.append(os.path.join(os.getcwd(), "organizer.config.json"))
    for cp in candidate_paths:
        try:
            if cp and os.path.exists(cp):
                with open(cp, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                break
        except Exception:
            # Ignore config errors; proceed with defaults/CLI
            cfg = {}
            break
    return args, cfg


def make_log_file(suggested_dir: str | None, suggested_file: str | None):
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    if suggested_file:
        log_file = suggested_file
        log_dir = os.path.dirname(log_file) or os.path.join(os.getcwd(), "logs", timestamp)
    else:
        log_dir = suggested_dir or os.path.join(os.getcwd(), "logs", timestamp)
        log_file = os.path.join(log_dir, "operation.log")
    os.makedirs(log_dir, exist_ok=True)
    return log_file


def print_and_log(message: str, silent_mode: bool, log_file: str | None):
    if log_file:
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(message + '\n')
        except Exception:
            pass
    if not silent_mode:
        print(message)


def summarize_preview(operations, output_path, link_type: str):
    # Count files per destination folder and by extension; estimate disk usage for copy
    per_folder = {}
    by_ext = {}
    total_size = 0
    for op in operations:
        dest = op['destination']
        rel = os.path.relpath(os.path.dirname(dest), output_path)
        per_folder[rel] = per_folder.get(rel, 0) + 1
        ext = os.path.splitext(op['source'])[1].lower()
        by_ext[ext] = by_ext.get(ext, 0) + 1
        try:
            if link_type == 'copy':
                total_size += os.path.getsize(op['source'])
        except Exception:
            pass
    return per_folder, by_ext, total_size


def main():
    # Ensure NLTK data is downloaded efficiently and quietly
    ensure_nltk_data()

    # Parse CLI and config
    args, cfg = parse_cli_and_config()

    # Resolve settings with precedence: CLI > config > defaults
    silent_mode = bool(args.silent or cfg.get('silent', False))
    dry_run = bool(args.dry_run or cfg.get('dry_run', True))

    # Link strategy
    link_choice = (args.link or cfg.get('link', 'hard')).lower()
    link_map = {'hard': 'hardlink', 'soft': 'symlink', 'copy': 'copy'}
    link_type = link_map.get(link_choice, 'hardlink')

    # Models and base URL
    text_model = args.model_text or cfg.get('model_text') or "llama3.2:3b"
    image_model = args.model_image or cfg.get('model_image') or "llava:7b"
    ollama_url = args.ollama_url or cfg.get('ollama_url')

    # Logging setup (per-run)
    log_file = make_log_file(args.log_dir, args.log_file)
    print_and_log("-" * 50, silent_mode, log_file)
    print_and_log("Local File Organizer (Ollama) starting...", silent_mode, log_file)
    print_and_log(f"Silent mode: {'ON' if silent_mode else 'OFF'} | Dry run: {'ON' if dry_run else 'OFF'} | Link: {link_type}", silent_mode, log_file)
    print_and_log(f"Models => text: {text_model}, image: {image_model} | Ollama: {ollama_url or 'default'}", silent_mode, log_file)

    while True:
        # Paths configuration
        if not silent_mode:
            print("-" * 50)

        # Get input and output paths once per directory (CLI first, else prompt)
        input_path = args.input_path or cfg.get('input_path')
        if not input_path:
            if not silent_mode:
                print("-" * 50)
            input_path = input("Enter the path of the directory you want to organize: ").strip()
        while not os.path.exists(input_path):
            message = f"Input path {input_path} does not exist. Please enter a valid path."
            print_and_log(message, silent_mode, log_file)
            # If provided via CLI/config and invalid, abort to avoid infinite loop
            if args.input_path or cfg.get('input_path'):
                return
            input_path = input("Enter the path of the directory you want to organize: ").strip()

        # Confirm successful input path
        message = f"Input path successfully set: {input_path}"
        print_and_log(message, silent_mode, log_file)
        if not silent_mode:
            print("-" * 50)

        # Determine output path: CLI/config or default under input
        output_path = args.output_path or cfg.get('output_path')
        if not output_path:
            # Create 'organized_folder' inside the input directory (or alongside the input file)
            if os.path.isdir(input_path):
                output_path = os.path.join(input_path, 'organized_folder')
            else:
                output_path = os.path.join(os.path.dirname(input_path), 'organized_folder')
        message = f"Output path successfully set to: {output_path}"
        print_and_log(message, silent_mode, log_file)
        if not silent_mode:
            print("-" * 50)

        # Start processing files
        start_time = time.time()
        file_paths = collect_file_paths(input_path)
        end_time = time.time()

        message = f"Time taken to load file paths: {end_time - start_time:.2f} seconds"
        print_and_log(message, silent_mode, log_file)
        if not silent_mode:
            print("-" * 50)
            print("Directory tree before organizing:")
            display_directory_tree(input_path)
            print("*" * 50)

        # Loop for selecting sorting methods
        while True:
            mode = args.mode or cfg.get('mode') or get_mode_selection()

            if mode == 'content':
                # Proceed with content mode
                # Initialize models once
                if not silent_mode:
                    print("Checking if the model is already downloaded. If not, downloading it now.")
                initialize_models(image_model=image_model, text_model=text_model, base_url=ollama_url)

                if not silent_mode:
                    print("*" * 50)
                    print("The file upload was successful. Processing may take a few minutes.")
                    print("*" * 50)


                # Separate files by type
                image_files, text_files = separate_files_by_type(file_paths)

                # Prepare text tuples for processing
                text_tuples = []
                for fp in text_files:
                    # Use read_file_data to read the file content
                    text_content = read_file_data(fp)
                    if text_content is None:
                        message = f"Unsupported or unreadable text file format: {fp}"
                        if silent_mode:
                            with open(log_file, 'a') as f:
                                f.write(message + '\n')
                        else:
                            print(message)
                        continue  # Skip unsupported or unreadable files
                    text_tuples.append((fp, text_content))

                # Process files sequentially
                data_images = process_image_files(image_files, image_inference, text_inference, silent=silent_mode, log_file=log_file)
                data_texts = process_text_files(text_tuples, text_inference, silent=silent_mode, log_file=log_file)

                # Prepare for copying and renaming
                renamed_files = set()
                processed_files = set()

                # Combine all data
                all_data = data_images + data_texts

                # Compute the operations
                operations = compute_operations(
                    all_data,
                    output_path,
                    renamed_files,
                    processed_files,
                    link_type=link_type
                )

            elif mode == 'date':
                # Process files by date
                operations = process_files_by_date(file_paths, output_path, dry_run=dry_run, silent=silent_mode, log_file=log_file, link_type=link_type)
            elif mode == 'type':
                # Process files by type
                operations = process_files_by_type(file_paths, output_path, dry_run=dry_run, silent=silent_mode, log_file=log_file, link_type=link_type)
            elif mode == 'test':
                # Simulate AI activity but organize strictly by type without AI
                if not silent_mode:
                    print("Checking if the model is already downloaded. If not, downloading it now.")
                    print("**----------------------------------------------**")
                    print("**     Simulated vision model initialized      **")
                    print("**     Simulated text model initialized        **")
                    print("**----------------------------------------------**")
                    print("*" * 50)
                    print("The file upload was successful. Processing may take a few minutes.")
                    print("*" * 50)
                operations = process_files_by_type(file_paths, output_path, dry_run=dry_run, silent=silent_mode, log_file=log_file, link_type=link_type)
            else:
                print("Invalid mode selected.")
                return

            # Add operations to copy any unprocessed, non-hidden files into an 'unclassified' folder
            try:
                all_non_hidden = [fp for fp in file_paths if not os.path.basename(fp).startswith('.')]
                processed_sources = {op['source'] for op in operations}
                unprocessed_files = [fp for fp in all_non_hidden if fp not in processed_sources]
                if unprocessed_files:
                    unclassified_dir = os.path.join(output_path, 'unclassified')
                    for fp in unprocessed_files:
                        dest = os.path.join(unclassified_dir, os.path.basename(fp))
                        operations.append({
                            'source': fp,
                            'destination': dest,
                            'link_type': 'copy',  # always copy as-is per requirement
                            'unclassified': True
                        })
                        warn_msg = f"WARNING: File '{fp}' will be copied as-is to '{unclassified_dir}' without classification or renaming."
                        print_and_log(warn_msg, silent_mode, log_file)
            except Exception as _e:
                # Do not fail the run due to unclassified handling
                print_and_log(f"Note: Skipped adding unclassified operations due to: {_e}", silent_mode, log_file)

            # Simulate and display the proposed directory tree
            print_and_log("-" * 50, silent_mode, log_file)
            print_and_log("Proposed directory structure:", silent_mode, log_file)
            print_and_log(os.path.abspath(output_path), silent_mode, log_file)
            simulated_tree = simulate_directory_tree(operations, output_path)
            if not silent_mode:
                print_simulated_tree(simulated_tree)
            # Enhanced preview summary
            per_folder, by_ext, total_size = summarize_preview(operations, output_path, link_type)
            print_and_log("Summary:", silent_mode, log_file)
            print_and_log(f"  Total operations: {len(operations)}", silent_mode, log_file)
            print_and_log(f"  Folders to create: {len(per_folder)}", silent_mode, log_file)
            print_and_log("  Files per folder:", silent_mode, log_file)
            for folder, count in sorted(per_folder.items()):
                print_and_log(f"    {folder} : {count}", silent_mode, log_file)
            print_and_log("  Files by type:", silent_mode, log_file)
            for ext, count in sorted(by_ext.items()):
                print_and_log(f"    {ext or '[no ext]'} : {count}", silent_mode, log_file)
            if link_type == 'copy':
                print_and_log(f"  Estimated disk usage if copying: {total_size} bytes", silent_mode, log_file)
            print_and_log("-" * 50, silent_mode, log_file)

            # Proceed depending on dry_run and interactive/CLI mode
            if dry_run:
                print_and_log("Dry run mode: no changes were made.", silent_mode, log_file)
                break

            # Determine proceed behavior
            if args.mode or cfg.get('mode'):
                proceed = True  # non-interactive run proceeds automatically
            else:
                proceed = get_yes_no("Would you like to proceed with these changes? (yes/no): ")

            if proceed:
                # Create the output directory now
                os.makedirs(output_path, exist_ok=True)

                # Perform the actual file operations
                message = "Performing file operations..."
                print_and_log(message, silent_mode, log_file)
                execute_operations(
                    operations,
                    dry_run=False,
                    silent=silent_mode,
                    log_file=log_file
                )

                message = "The files have been organized successfully."
                print_and_log("-" * 50, silent_mode, log_file)
                print_and_log(message, silent_mode, log_file)
                print_and_log("-" * 50, silent_mode, log_file)
                break  # Exit the sorting method loop after successful operation
            else:
                # Ask if the user wants to try another sorting method
                another_sort = get_yes_no("Would you like to choose another sorting method? (yes/no): ")
                if another_sort:
                    continue  # Loop back to mode selection
                else:
                    print("Operation canceled by the user.")
                    break  # Exit the sorting method loop

        # Ask if the user wants to organize another directory (interactive only)
        if args.input_path or args.mode:
            break  # Non-interactive run: process once and exit
        another_directory = get_yes_no("Would you like to organize another directory? (yes/no): ")
        if not another_directory:
            break  # Exit the main loop


if __name__ == '__main__':
    main()
