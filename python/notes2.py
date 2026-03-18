#!/usr/bin/env python3
"""
Future Proof Notes Manager - Version Two (CLI)
A personal notes manager using text files with YAML headers.
Command-line interface version with 'list' and 'read' commands.

SETUP REMINDER:
Before running the 'list' or 'read' commands, copy the test notes to your notes directory:
    cp -r test-notes/* ~/.notes/
or create the directory structure:
    mkdir -p ~/.notes/notes
    cp test-notes/*.md ~/.notes/notes/
"""

import sys
from pathlib import Path


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


def show_help():
    """Display help information."""
    help_text = """
Future Proof Notes Manager v0.2

Usage: notes2.py [command] [arguments]

Available commands:
  help         - Display this help information
  list         - List all notes with their index numbers
  read <n>     - Display the full contents of note number <n>
                 (index numbers are based on sorted filename order
                  and may change when notes are added or removed)

Notes directory: {}

Setup:
  To test the commands, copy sample notes:
    mkdir -p ~/.notes/notes
    cp test-notes/*.md ~/.notes/notes/

Examples:
  notes2.py list
  notes2.py read 1
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
        print("Usage: notes2.py [command]", file=sys.stderr)
        print("Try 'notes2.py help' for more information.", file=sys.stderr)
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
            print("Usage: notes2.py read <n>", file=sys.stderr)
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
    else:
        print(f"Error: Unknown command '{command}'", file=sys.stderr)
        print("Try 'notes2.py help' for more information.", file=sys.stderr)
        finish(1)


if __name__ == "__main__":
    main()
