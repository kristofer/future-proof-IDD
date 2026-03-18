#!/usr/bin/env python3
"""
Future Proof Notes Manager - Version Three (CLI)
A personal notes manager using text files with YAML headers.
Command-line interface version with 'list', 'read', and 'create' commands.

SETUP REMINDER:
Before running the 'list' or 'read' commands, copy the test notes to your notes directory:
    cp -r test-notes/* ~/.notes/
or create the directory structure:
    mkdir -p ~/.notes/notes
    cp test-notes/*.md ~/.notes/notes/
"""

import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


# Path to the YAML note template (relative to this script's parent directory)
TEMPLATE_PATH = Path(__file__).parent.parent / "docs" / "note-template.md"


def setup():
    """Initialize the notes application."""
    # Define the notes directory in HOME
    notes_dir = Path.home() / ".notes"

    # Check if notes directory exists
    if not notes_dir.exists():
        # For CLI version, we don't automatically create it
        pass

    return notes_dir


def parse_yaml_header(file_path):
    """
    Parse YAML front matter from a note file.
    Returns a tuple of (metadata dict, body text).
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Check if file starts with YAML front matter
        if not lines or lines[0].strip() != '---':
            return {'title': file_path.name, 'file': file_path.name}, ''.join(lines)

        # Find the closing ---
        yaml_end = -1
        for i in range(1, len(lines)):
            if lines[i].strip() == '---':
                yaml_end = i
                break

        if yaml_end == -1:
            return {'title': file_path.name, 'file': file_path.name}, ''.join(lines)

        # Parse YAML lines (simple parsing for basic key: value pairs)
        metadata = {'file': file_path.name}
        for line in lines[1:yaml_end]:
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                metadata[key] = value

        body = ''.join(lines[yaml_end + 1:])
        return metadata, body

    except Exception as e:
        return {'title': file_path.name, 'file': file_path.name, 'error': str(e)}, ''


def get_note_files(notes_dir):
    """Return a sorted list of note files from the notes directory."""
    if not notes_dir.exists():
        return None

    notes_subdir = notes_dir / "notes"
    search_dirs = [notes_subdir] if notes_subdir.exists() else [notes_dir]

    note_files = []
    for search_dir in search_dirs:
        note_files.extend(search_dir.glob("*.md"))
        note_files.extend(search_dir.glob("*.note"))
        note_files.extend(search_dir.glob("*.txt"))

    return sorted(note_files)


def list_notes(notes_dir):
    """List all notes in the notes directory."""
    if not notes_dir.exists():
        print(f"Error: Notes directory does not exist: {notes_dir}", file=sys.stderr)
        print("Create it with: mkdir -p ~/.notes/notes", file=sys.stderr)
        print("Then copy test notes: cp test-notes/*.md ~/.notes/notes/", file=sys.stderr)
        return False

    note_files = get_note_files(notes_dir)

    if not note_files:
        print(f"No notes found in {notes_dir}")
        print("Copy test notes with: cp test-notes/*.md ~/.notes/", file=sys.stderr)
        return True

    print(f"Notes in {notes_dir}:")
    print("=" * 60)

    for idx, note_file in enumerate(note_files, start=1):
        metadata, _ = parse_yaml_header(note_file)
        title = metadata.get('title', note_file.name)
        created = metadata.get('created', 'N/A')
        tags = metadata.get('tags', '')

        print(f"\n[{idx}] {note_file.name}")
        print(f"  Title: {title}")
        if created != 'N/A':
            print(f"  Created: {created}")
        if tags:
            print(f"  Tags: {tags}")

    print(f"\n{len(note_files)} note(s) found.")
    return True


def read_note(notes_dir, note_number):
    """Display the full contents of a note identified by its list index."""
    if not notes_dir.exists():
        print(f"Error: Notes directory does not exist: {notes_dir}", file=sys.stderr)
        print("Create it with: mkdir -p ~/.notes/notes", file=sys.stderr)
        print("Then copy test notes: cp test-notes/*.md ~/.notes/notes/", file=sys.stderr)
        return False

    note_files = get_note_files(notes_dir)

    if not note_files:
        print(f"No notes found in {notes_dir}", file=sys.stderr)
        return False

    if note_number < 1 or note_number > len(note_files):
        print(
            f"Error: Note number {note_number} is out of range. "
            f"There are {len(note_files)} note(s) available.",
            file=sys.stderr,
        )
        return False

    note_file = note_files[note_number - 1]
    metadata, body = parse_yaml_header(note_file)

    # ── Header ────────────────────────────────────────────────────────────────
    print("=" * 60)
    print(f"  Note #{note_number}: {metadata.get('title', note_file.name)}")
    print("=" * 60)

    # Metadata fields to show (in order), skipping 'file' (internal only)
    meta_fields = [
        ('File',     'file'),
        ('Author',   'author'),
        ('Created',  'created'),
        ('Modified', 'modified'),
        ('Tags',     'tags'),
        ('Status',   'status'),
        ('Priority', 'priority'),
    ]
    for label, key in meta_fields:
        value = metadata.get(key)
        if value:
            print(f"  {label}: {value}")

    print("-" * 60)

    # ── Body ──────────────────────────────────────────────────────────────────
    stripped = body.strip()
    if stripped:
        print(stripped)
    else:
        print("(no content)")

    print("=" * 60)
    return True


def _load_template(timestamp):
    """
    Load the YAML note template and substitute the current timestamp.
    Falls back to an inline template if the template file is not found.
    """
    if TEMPLATE_PATH.exists():
        content = TEMPLATE_PATH.read_text(encoding='utf-8')
        content = content.replace('{{created}}', timestamp)
        content = content.replace('{{modified}}', timestamp)
        return content

    # Inline fallback template
    return (
        "---\n"
        "title: Untitled\n"
        "author: \n"
        f"created: {timestamp}\n"
        f"modified: {timestamp}\n"
        "tags: []\n"
        "status: draft\n"
        "priority: 3\n"
        "---\n"
        "\n"
        "(Write your note here...)\n"
    )


def _slugify(text):
    """Convert a title string into a filename-safe slug."""
    slug = ''.join(c if c.isalnum() or c == ' ' else '-' for c in text.lower())
    # Collapse runs of hyphens/spaces into a single hyphen
    import re
    slug = re.sub(r'[-\s]+', '-', slug).strip('-')
    return slug or 'untitled'


def create_note(notes_dir):
    """
    Create a new note by launching $EDITOR with a YAML template pre-loaded.
    The finished note is saved to the notes directory with a date-based filename.
    """
    # Resolve the editor to use
    editor = os.environ.get('EDITOR') or os.environ.get('VISUAL') or 'vi'

    # Build template content with the current UTC timestamp
    now = datetime.now(timezone.utc)
    timestamp = now.strftime('%Y-%m-%dT%H:%M:%SZ')
    date_str = now.strftime('%Y-%m-%d')

    template_content = _load_template(timestamp)

    # Write the template to a temporary file
    tmp_fd, tmp_path_str = tempfile.mkstemp(suffix='.md', prefix='note-')
    tmp_path = Path(tmp_path_str)
    try:
        with os.fdopen(tmp_fd, 'w', encoding='utf-8') as tmp_file:
            tmp_file.write(template_content)

        # Launch the editor
        try:
            result = subprocess.run([editor, tmp_path_str])
        except FileNotFoundError:
            print(
                f"Error: Editor '{editor}' not found. "
                "Set the EDITOR environment variable.",
                file=sys.stderr,
            )
            return False

        if result.returncode != 0:
            print(
                f"Editor exited with non-zero status ({result.returncode}).",
                file=sys.stderr,
            )
            return False

        # Read what the user saved
        saved_content = tmp_path.read_text(encoding='utf-8')

        # Discard if nothing was changed
        if saved_content == template_content:
            print("Note discarded (no changes made).")
            return True

        # Parse the title for the new filename
        metadata, _ = parse_yaml_header(tmp_path)
        title = metadata.get('title', 'untitled')
        slug = _slugify(title)

        # Ensure the notes subdirectory exists
        notes_subdir = notes_dir / "notes"
        notes_subdir.mkdir(parents=True, exist_ok=True)

        # Choose a unique filename
        filename = f"{date_str}-{slug}.md"
        note_path = notes_subdir / filename
        counter = 1
        while note_path.exists():
            filename = f"{date_str}-{slug}-{counter}.md"
            note_path = notes_subdir / filename
            counter += 1

        # Move the temp file into the notes directory
        shutil.move(tmp_path_str, note_path)
        print(f"Note saved: {note_path}")
        return True

    finally:
        # Clean up the temp file if it still exists (e.g. on error paths above)
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def show_help():
    """Display help information."""
    help_text = """
Future Proof Notes Manager v0.3

Usage: notes3.py [command] [arguments]

Available commands:
  help         - Display this help information
  list         - List all notes with their index numbers
  read <n>     - Display the full contents of note number <n>
                 (index numbers are based on sorted filename order
                  and may change when notes are added or removed)
  create       - Launch $EDITOR with a YAML template to write a new note;
                 saves the result to the notes directory

Notes directory: {}

Setup:
  To test the commands, copy sample notes:
    mkdir -p ~/.notes/notes
    cp test-notes/*.md ~/.notes/notes/

Examples:
  notes3.py list
  notes3.py read 1
  notes3.py create
    """.format(Path.home() / ".notes")
    print(help_text.strip())


def finish(exit_code=0):
    """Clean up and exit the application."""
    sys.exit(exit_code)


def main():
    """Main entry point for the notes CLI application."""
    notes_dir = setup()

    if len(sys.argv) < 2:
        print("Error: No command provided.", file=sys.stderr)
        print("Usage: notes3.py [command]", file=sys.stderr)
        print("Try 'notes3.py help' for more information.", file=sys.stderr)
        finish(1)

    command = sys.argv[1].lower()

    if command == "help":
        show_help()
        finish(0)
    elif command == "list":
        success = list_notes(notes_dir)
        finish(0 if success else 1)
    elif command == "read":
        if len(sys.argv) < 3:
            print("Error: 'read' requires a note number.", file=sys.stderr)
            print("Usage: notes3.py read <n>", file=sys.stderr)
            finish(1)
        try:
            note_number = int(sys.argv[2])
        except ValueError:
            print(
                f"Error: '{sys.argv[2]}' is not a valid note number. Please provide an integer.",
                file=sys.stderr,
            )
            finish(1)
        success = read_note(notes_dir, note_number)
        finish(0 if success else 1)
    elif command == "create":
        success = create_note(notes_dir)
        finish(0 if success else 1)
    else:
        print(f"Error: Unknown command '{command}'", file=sys.stderr)
        print("Try 'notes3.py help' for more information.", file=sys.stderr)
        finish(1)


if __name__ == "__main__":
    main()
