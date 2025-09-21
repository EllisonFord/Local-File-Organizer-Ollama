import os
import re
import datetime  # Import datetime for date operations
import difflib
from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn

def sanitize_filename(name, max_length=50, max_words=5):
    """Sanitize the filename by removing unwanted words and characters."""
    # Remove file extension if present
    name = os.path.splitext(name)[0]
    # Remove unwanted words and data type words
    name = re.sub(
        r'\b(jpg|jpeg|png|gif|bmp|txt|md|pdf|docx|xls|xlsx|csv|ppt|pptx|image|picture|photo|this|that|these|those|here|there|'
        r'please|note|additional|notes|folder|name|sure|heres|a|an|the|and|of|in|'
        r'to|for|on|with|your|answer|should|be|only|summary|summarize|text|category)\b',
        '',
        name,
        flags=re.IGNORECASE
    )
    # Remove non-word characters except underscores
    sanitized = re.sub(r'[^\w\s]', '', name).strip()
    # Replace multiple underscores or spaces with a single underscore
    sanitized = re.sub(r'[\s_]+', '_', sanitized)
    # Convert to lowercase
    sanitized = sanitized.lower()
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    # Split into words and limit the number of words
    words = sanitized.split('_')
    limited_words = [word for word in words if word]  # Remove empty strings
    limited_words = limited_words[:max_words]
    limited_name = '_'.join(limited_words)
    # Limit length
    return limited_name[:max_length] if limited_name else 'untitled'


def _list_existing_relative_dirs(root_dir: str):
    """Return a list of existing subdirectory relative paths under root_dir.
    If the root does not exist yet, returns an empty list.
    """
    rel_dirs = []
    if not os.path.isdir(root_dir):
        return rel_dirs
    for dirpath, dirnames, _ in os.walk(root_dir):
        if dirpath == root_dir:
            for d in dirnames:
                rel_dirs.append(d)
            continue
        rel = os.path.relpath(dirpath, root_dir)
        if rel != ".":
            rel_dirs.append(rel)
    return sorted(set(rel_dirs))


def _normalize_token(tok: str) -> str:
    t = tok.lower()
    synonyms = {
        'images': 'image', 'image': 'image', 'photos': 'image', 'pics': 'image', 'pictures': 'image',
        'texts': 'text', 'text': 'text', 'documents': 'doc', 'document': 'doc', 'docs': 'doc',
        'pdfs': 'pdf', 'pdf': 'pdf', 'xls': 'xls', 'xlsx': 'xls', 'spreadsheets': 'xls',
        'powerpoint': 'ppt', 'presentations': 'ppt', 'presentation': 'ppt', 'pptx': 'ppt', 'ppt': 'ppt',
        'ebooks': 'ebook', 'ebook': 'ebook', 'books': 'ebook', 'book': 'ebook',
        'others': 'other', 'other': 'other'
    }
    return synonyms.get(t, t.rstrip('s'))


def _tokenize_path(rel_path: str) -> set:
    s = rel_path.replace('\\', '/').lower()
    s = re.sub(r'[^a-z0-9/]+', '_', s)
    parts = [p for p in s.split('/') if p]
    tokens = []
    for p in parts:
        for tok in re.split(r'[_\-]+', p):
            if tok:
                tokens.append(_normalize_token(tok))
    return set(tokens)


def _similarity_score(rel_a: str, rel_b: str) -> float:
    a_norm = re.sub(r'[^a-z0-9]+', '_', rel_a.lower())
    b_norm = re.sub(r'[^a-z0-9]+', '_', rel_b.lower())
    ratio = difflib.SequenceMatcher(None, a_norm, b_norm).ratio()
    ta = _tokenize_path(rel_a)
    tb = _tokenize_path(rel_b)
    jacc = (len(ta & tb) / len(ta | tb)) if (ta or tb) else 0.0
    return max(ratio, jacc)


def find_best_existing_subdir(output_path: str, desired_rel_path: str, existing_rel_dirs: list | None = None, threshold: float = 0.62) -> str:
    """Map a desired relative subdirectory to the most similar already existing
    subdirectory under output_path. Returns desired_rel_path unchanged if no
    candidate meets the similarity threshold.
    """
    desired_abs = os.path.join(output_path, desired_rel_path)
    if os.path.isdir(desired_abs):
        return desired_rel_path

    existing_rel_dirs = existing_rel_dirs if existing_rel_dirs is not None else _list_existing_relative_dirs(output_path)
    if not existing_rel_dirs:
        return desired_rel_path

    best = None
    best_score = -1.0
    for cand in existing_rel_dirs:
        score = _similarity_score(desired_rel_path, cand)
        if score > best_score:
            best_score = score
            best = cand
    if best is not None and best_score >= threshold:
        return best
    return desired_rel_path

def process_files_by_date(file_paths, output_path, dry_run=False, silent=False, log_file=None, link_type: str = 'hardlink'):
    """Process files to organize them by date.
    If the output directory already contains a similar year/month structure,
    reuse it instead of creating near-duplicate folders.
    """
    operations = []
    existing_rel_dirs = _list_existing_relative_dirs(output_path)
    for file_path in file_paths:
        # Get the modification time
        mod_time = os.path.getmtime(file_path)
        # Convert to datetime
        mod_datetime = datetime.datetime.fromtimestamp(mod_time)
        year = mod_datetime.strftime('%Y')
        month = mod_datetime.strftime('%B')  # e.g., 'January', or use '%m' for month number
        # Determine desired relative path and align with existing structure
        desired_rel = os.path.join(year, month)
        mapped_rel = find_best_existing_subdir(output_path, desired_rel, existing_rel_dirs)
        # Create directory path
        dir_path = os.path.join(output_path, mapped_rel)
        # Prepare new file path
        new_file_name = os.path.basename(file_path)
        new_file_path = os.path.join(dir_path, new_file_name)
        # Record the operation
        operation = {
            'source': file_path,
            'destination': new_file_path,
            'link_type': link_type,
        }
        operations.append(operation)
    return operations

def process_files_by_type(file_paths, output_path, dry_run=False, silent=False, log_file=None, link_type: str = 'hardlink'):
    """Process files to organize them by type, first separating into text-based and image-based files.
    If the output directory already contains similar folders, reuse them.
    """
    operations = []

    # Define extensions
    image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')
    text_extensions = ('.txt', '.md', '.docx', '.doc', '.pdf', '.xls', '.xlsx', '.epub', '.mobi', '.azw', '.azw3')

    existing_rel_dirs = _list_existing_relative_dirs(output_path)

    for file_path in file_paths:
        # Exclude hidden files (additional safety)
        if os.path.basename(file_path).startswith('.'):
            continue

        # Get the file extension
        ext = os.path.splitext(file_path)[1].lower()

        # Check if it's an image file
        if ext in image_extensions:
            # Image-based files
            top_folder = 'image_files'
            # You can add subcategories here if needed
            desired_rel = top_folder

        elif ext in text_extensions:
            # Text-based files
            top_folder = 'text_files'
            # Map extensions to subfolders
            if ext in ('.txt', '.md'):
                sub_folder = 'plain_text_files'
            elif ext in ('.doc', '.docx'):
                sub_folder = 'doc_files'
            elif ext == '.pdf':
                sub_folder = 'pdf_files'
            elif ext in ('.xls', '.xlsx'):
                sub_folder = 'xls_files'
            elif ext in ('.epub', '.mobi', '.azw', '.azw3'):
                sub_folder = 'ebooks'
            else:
                sub_folder = 'others'
            desired_rel = os.path.join(top_folder, sub_folder)

        else:
            # Other types
            desired_rel = 'others'

        # Map to best existing folder, if any
        mapped_rel = find_best_existing_subdir(output_path, desired_rel, existing_rel_dirs)

        # Create directory path
        dir_path = os.path.join(output_path, mapped_rel)
        # Prepare new file path
        new_file_name = os.path.basename(file_path)
        new_file_path = os.path.join(dir_path, new_file_name)
        # Record the operation
        operation = {
            'source': file_path,
            'destination': new_file_path,
            'link_type': link_type,
        }
        operations.append(operation)

    return operations

def compute_operations(data_list, new_path, renamed_files, processed_files, link_type: str = 'hardlink'):
    """Compute the file operations based on generated metadata.
    Align AI-suggested folder names with any existing subfolders in the target directory.
    """
    operations = []
    existing_rel_dirs = _list_existing_relative_dirs(new_path)
    for data in data_list:
        file_path = data['file_path']
        if file_path in processed_files:
            continue
        processed_files.add(file_path)

        # Prepare folder name and file name
        original_folder_name = data['foldername']
        mapped_folder_name = find_best_existing_subdir(new_path, original_folder_name, existing_rel_dirs)
        new_file_name = data['filename'] + os.path.splitext(file_path)[1]

        # Prepare new file path
        dir_path = os.path.join(new_path, mapped_folder_name)
        new_file_path = os.path.join(dir_path, new_file_name)

        # Handle duplicates
        counter = 1
        original_new_file_name = new_file_name
        while new_file_path in renamed_files:
            new_file_name = f"{data['filename']}_{counter}" + os.path.splitext(file_path)[1]
            new_file_path = os.path.join(dir_path, new_file_name)
            counter += 1

        # Record the operation
        operation = {
            'source': file_path,
            'destination': new_file_path,
            'link_type': link_type,
            'folder_name': mapped_folder_name,
            'original_folder_name': original_folder_name,
            'new_file_name': new_file_name
        }
        operations.append(operation)
        renamed_files.add(new_file_path)

    return operations  # Return the list of operations for display or further processing

def execute_operations(operations, dry_run=False, silent=False, log_file=None):
    """Execute the file operations.
    Attempts hardlink/symlink first; on failure, falls back to copying the file (copy2).
    """
    import shutil
    total_operations = len(operations)

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        transient=True
    ) as progress:
        task = progress.add_task("Organizing Files...", total=total_operations)
        for operation in operations:
            source = operation['source']
            destination = operation['destination']
            link_type = operation['link_type']
            dir_path = os.path.dirname(destination)

            if dry_run:
                message = f"Dry run: would create {link_type} from '{source}' to '{destination}'"
            else:
                # Ensure the directory exists before performing the operation
                os.makedirs(dir_path, exist_ok=True)

                try:
                    if link_type == 'hardlink':
                        os.link(source, destination)
                        message = f"Created {link_type} from '{source}' to '{destination}'"
                    elif link_type == 'symlink':
                        os.symlink(source, destination)
                        message = f"Created {link_type} from '{source}' to '{destination}'"
                    else:
                        # Unknown link_type -> copy
                        shutil.copy2(source, destination)
                        message = f"Copied file from '{source}' to '{destination}'"
                except Exception as e:
                    # Fallback to copying the file if linking fails
                    try:
                        shutil.copy2(source, destination)
                        message = f"Link failed ({e}); copied file from '{source}' to '{destination}' instead"
                    except Exception as copy_err:
                        message = f"Error saving file to '{destination}': {copy_err} (original link error: {e})"

            progress.advance(task)

            # Silent mode handling
            if silent:
                if log_file:
                    with open(log_file, 'a') as f:
                        f.write(message + '\n')
            else:
                print(message)