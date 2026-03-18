import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.Instant;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Stream;

/**
 * Future Proof Notes Manager - Version Two (CLI)
 * A personal notes manager using text files with YAML headers.
 * Command-line interface version with 'list', 'read', and 'create' commands.
 *
 * SETUP REMINDER:
 * Before running the 'list' or 'read' commands, copy the test notes to your notes directory:
 *     cp -r test-notes/* ~/.notes/
 * or create the directory structure:
 *     mkdir -p ~/.notes/notes
 *     cp test-notes/*.md ~/.notes/notes/
 */
public class Notes2 {

    private static final Path NOTES_DIR = Path.of(System.getProperty("user.home"), ".notes");

    // Candidate locations for the YAML note template (tried in order)
    private static final Path[] TEMPLATE_SEARCH_PATHS = {
        Path.of("docs", "note-template.md"),
        Path.of("..", "docs", "note-template.md"),
    };

    /**
     * Initialize the notes application.
     */
    private static Path setup() {
        // For CLI version, we don't automatically create the notes directory
        return NOTES_DIR;
    }

    /**
     * Parse YAML front matter from a note file.
     * Returns a map with metadata.
     */
    private static Map<String, String> parseYamlHeader(Path filePath) {
        Map<String, String> metadata = new HashMap<>();
        metadata.put("file", filePath.getFileName().toString());

        try {
            List<String> lines = Files.readAllLines(filePath);

            // Check if file starts with YAML front matter
            if (lines.isEmpty() || !lines.get(0).trim().equals("---")) {
                metadata.put("title", filePath.getFileName().toString());
                return metadata;
            }

            // Find the closing ---
            int yamlEnd = -1;
            for (int i = 1; i < lines.size(); i++) {
                if (lines.get(i).trim().equals("---")) {
                    yamlEnd = i;
                    break;
                }
            }

            if (yamlEnd == -1) {
                metadata.put("title", filePath.getFileName().toString());
                return metadata;
            }

            // Parse YAML lines (simple parsing for basic key: value pairs)
            for (int i = 1; i < yamlEnd; i++) {
                String line = lines.get(i).trim();
                if (line.contains(":")) {
                    String[] parts = line.split(":", 2);
                    String key = parts[0].trim();
                    String value = parts[1].trim();
                    metadata.put(key, value);
                }
            }

        } catch (IOException e) {
            metadata.put("error", e.getMessage());
        }

        return metadata;
    }

    /**
     * Return a sorted list of note files from the notes directory.
     */
    private static List<Path> getNoteFiles(Path notesDir) throws IOException {
        Path notesSubdir = notesDir.resolve("notes");
        Path searchDir = Files.exists(notesSubdir) ? notesSubdir : notesDir;

        try (Stream<Path> paths = Files.walk(searchDir, 1)) {
            return paths
                    .filter(Files::isRegularFile)
                    .filter(p -> {
                        String name = p.getFileName().toString();
                        return name.endsWith(".md") || name.endsWith(".note") || name.endsWith(".txt");
                    })
                    .sorted()
                    .toList();
        }
    }

    /**
     * List all notes in the notes directory.
     */
    private static boolean listNotes(Path notesDir) {
        if (!Files.exists(notesDir)) {
            System.err.println("Error: Notes directory does not exist: " + notesDir);
            System.err.println("Create it with: mkdir -p ~/.notes/notes");
            System.err.println("Then copy test notes: cp test-notes/*.md ~/.notes/notes/");
            return false;
        }

        List<Path> noteFiles;
        try {
            noteFiles = getNoteFiles(notesDir);
        } catch (IOException e) {
            System.err.println("Error reading notes directory: " + e.getMessage());
            return false;
        }

        if (noteFiles.isEmpty()) {
            System.out.println("No notes found in " + notesDir);
            System.err.println("Copy test notes with: cp test-notes/*.md ~/.notes/");
            return true;
        }

        System.out.println("Notes in " + notesDir + ":");
        System.out.println("=".repeat(60));

        for (int i = 0; i < noteFiles.size(); i++) {
            Path noteFile = noteFiles.get(i);
            Map<String, String> metadata = parseYamlHeader(noteFile);
            String title = metadata.getOrDefault("title", noteFile.getFileName().toString());
            String created = metadata.getOrDefault("created", "N/A");
            String tags = metadata.getOrDefault("tags", "");

            System.out.println("\n[" + (i + 1) + "] " + noteFile.getFileName());
            System.out.println("  Title: " + title);
            if (!created.equals("N/A")) {
                System.out.println("  Created: " + created);
            }
            if (!tags.isEmpty()) {
                System.out.println("  Tags: " + tags);
            }
        }

        System.out.println("\n" + noteFiles.size() + " note(s) found.");
        return true;
    }

    /**
     * Display the full contents of a note identified by its list index.
     */
    private static boolean readNote(Path notesDir, int noteNumber) {
        if (!Files.exists(notesDir)) {
            System.err.println("Error: Notes directory does not exist: " + notesDir);
            System.err.println("Create it with: mkdir -p ~/.notes/notes");
            System.err.println("Then copy test notes: cp test-notes/*.md ~/.notes/notes/");
            return false;
        }

        List<Path> noteFiles;
        try {
            noteFiles = getNoteFiles(notesDir);
        } catch (IOException e) {
            System.err.println("Error reading notes directory: " + e.getMessage());
            return false;
        }

        if (noteFiles.isEmpty()) {
            System.err.println("No notes found in " + notesDir);
            return false;
        }

        if (noteNumber < 1 || noteNumber > noteFiles.size()) {
            System.err.println("Error: Note number " + noteNumber + " is out of range. "
                    + "There are " + noteFiles.size() + " note(s) available.");
            return false;
        }

        Path noteFile = noteFiles.get(noteNumber - 1);
        Map<String, String> metadata = parseYamlHeader(noteFile);

        // Read the full file to get the body
        String body = "";
        try {
            List<String> lines = Files.readAllLines(noteFile);
            int yamlEnd = -1;
            if (!lines.isEmpty() && lines.get(0).trim().equals("---")) {
                for (int i = 1; i < lines.size(); i++) {
                    if (lines.get(i).trim().equals("---")) {
                        yamlEnd = i;
                        break;
                    }
                }
            }
            if (yamlEnd >= 0) {
                body = String.join("\n", lines.subList(yamlEnd + 1, lines.size()));
            } else {
                body = String.join("\n", lines);
            }
        } catch (IOException e) {
            System.err.println("Error reading note: " + e.getMessage());
            return false;
        }

        // ── Header ────────────────────────────────────────────────────────────
        System.out.println("=".repeat(60));
        System.out.println("  Note #" + noteNumber + ": " + metadata.getOrDefault("title", noteFile.getFileName().toString()));
        System.out.println("=".repeat(60));

        // Metadata fields to show (in order)
        String[][] metaFields = {
            {"File",     "file"},
            {"Author",   "author"},
            {"Created",  "created"},
            {"Modified", "modified"},
            {"Tags",     "tags"},
            {"Status",   "status"},
            {"Priority", "priority"},
        };
        for (String[] field : metaFields) {
            String value = metadata.get(field[1]);
            if (value != null && !value.isEmpty()) {
                System.out.println("  " + field[0] + ": " + value);
            }
        }

        System.out.println("-".repeat(60));

        // ── Body ──────────────────────────────────────────────────────────────
        String stripped = body.strip();
        if (!stripped.isEmpty()) {
            System.out.println(stripped);
        } else {
            System.out.println("(no content)");
        }

        System.out.println("=".repeat(60));
        return true;
    }

    /**
     * Load the YAML note template and substitute the current timestamp.
     * Falls back to an inline template if the template file is not found.
     */
    private static String loadTemplate(String timestamp) {
        for (Path candidate : TEMPLATE_SEARCH_PATHS) {
            if (Files.exists(candidate)) {
                try {
                    String content = Files.readString(candidate);
                    content = content.replace("{{created}}", timestamp);
                    content = content.replace("{{modified}}", timestamp);
                    return content;
                } catch (IOException e) {
                    // Fall through to the next candidate or inline fallback
                }
            }
        }

        // Inline fallback template
        return "---\n"
                + "title: Untitled\n"
                + "author: \n"
                + "created: " + timestamp + "\n"
                + "modified: " + timestamp + "\n"
                + "tags: []\n"
                + "status: draft\n"
                + "priority: 3\n"
                + "---\n"
                + "\n"
                + "(Write your note here...)\n";
    }

    /**
     * Convert a title string into a filename-safe slug.
     */
    private static String slugify(String text) {
        String slug = text.toLowerCase()
                .chars()
                .mapToObj(c -> Character.isLetterOrDigit(c) ? String.valueOf((char) c) : "-")
                .collect(java.util.stream.Collectors.joining())
                .replaceAll("-+", "-")
                .replaceAll("^-|-$", "");
        return slug.isEmpty() ? "untitled" : slug;
    }

    /**
     * Create a new note by launching $EDITOR with a YAML template pre-loaded.
     * The finished note is saved to the notes directory with a date-based filename.
     */
    private static boolean createNote(Path notesDir) {
        // Resolve the editor to use
        String editor = System.getenv("EDITOR");
        if (editor == null || editor.isBlank()) {
            editor = System.getenv("VISUAL");
        }
        if (editor == null || editor.isBlank()) {
            editor = "vi";
        }

        // Build the current UTC timestamp
        Instant now = Instant.now();
        DateTimeFormatter isoFormatter = DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss'Z'")
                .withZone(ZoneOffset.UTC);
        String timestamp = isoFormatter.format(now);
        String dateStr = timestamp.substring(0, 10); // YYYY-MM-DD

        String templateContent = loadTemplate(timestamp);

        // Write the template to a temporary file
        Path tmpFile;
        try {
            tmpFile = Files.createTempFile("note-", ".md");
            Files.writeString(tmpFile, templateContent);
        } catch (IOException e) {
            System.err.println("Error creating temporary file: " + e.getMessage());
            return false;
        }

        // Launch the editor
        try {
            ProcessBuilder pb = new ProcessBuilder(editor, tmpFile.toString());
            pb.inheritIO();
            int exitCode = pb.start().waitFor();
            if (exitCode != 0) {
                System.err.println("Editor exited with non-zero status (" + exitCode + ").");
                Files.deleteIfExists(tmpFile);
                return false;
            }
        } catch (IOException e) {
            System.err.println("Error: Editor '" + editor + "' not found. "
                    + "Set the EDITOR environment variable.");
            try { Files.deleteIfExists(tmpFile); } catch (IOException ignored) { }
            return false;
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            try { Files.deleteIfExists(tmpFile); } catch (IOException ignored) { }
            return false;
        }

        // Read what the user saved
        String savedContent;
        try {
            savedContent = Files.readString(tmpFile);
        } catch (IOException e) {
            System.err.println("Error reading saved note: " + e.getMessage());
            return false;
        }

        // Discard if nothing was changed
        if (savedContent.equals(templateContent)) {
            System.out.println("Note discarded (no changes made).");
            try { Files.deleteIfExists(tmpFile); } catch (IOException ignored) { }
            return true;
        }

        // Parse the title for the new filename
        Map<String, String> metadata = parseYamlHeader(tmpFile);
        String title = metadata.getOrDefault("title", "untitled");
        String slug = slugify(title);

        // Ensure the notes subdirectory exists
        Path notesSubdir = notesDir.resolve("notes");
        try {
            Files.createDirectories(notesSubdir);
        } catch (IOException e) {
            System.err.println("Error creating notes directory: " + e.getMessage());
            return false;
        }

        // Choose a unique filename
        String filename = dateStr + "-" + slug + ".md";
        Path notePath = notesSubdir.resolve(filename);
        int counter = 1;
        while (Files.exists(notePath)) {
            filename = dateStr + "-" + slug + "-" + counter + ".md";
            notePath = notesSubdir.resolve(filename);
            counter++;
        }

        // Move the temp file into the notes directory
        try {
            Files.move(tmpFile, notePath, StandardCopyOption.REPLACE_EXISTING);
        } catch (IOException e) {
            System.err.println("Error saving note: " + e.getMessage());
            return false;
        }

        System.out.println("Note saved: " + notePath);
        return true;
    }

    /**
     * Display help information.
     */
    private static void showHelp() {
        String helpText = String.format("""
                Future Proof Notes Manager v0.2

                Usage: java Notes2 [command] [arguments]

                Available commands:
                  help         - Display this help information
                  list         - List all notes with their index numbers
                  read <n>     - Display the full contents of note number <n>
                                 (index numbers are based on sorted filename order
                                  and may change when notes are added or removed)
                  create       - Launch $EDITOR with a YAML template to write a new note;
                                 saves the result to the notes directory

                Notes directory: %s

                Setup:
                  To test the commands, copy sample notes:
                    mkdir -p ~/.notes/notes
                    cp test-notes/*.md ~/.notes/notes/

                Examples:
                  java Notes2 list
                  java Notes2 read 1
                  java Notes2 create
                """, NOTES_DIR);
        System.out.println(helpText.trim());
    }

    /**
     * Clean up and exit the application.
     */
    private static void finish(int exitCode) {
        System.exit(exitCode);
    }

    /**
     * Main entry point for the notes CLI application.
     */
    public static void main(String[] args) {
        Path notesDir = setup();

        if (args.length < 1) {
            System.err.println("Error: No command provided.");
            System.err.println("Usage: java Notes2 [command]");
            System.err.println("Try 'java Notes2 help' for more information.");
            finish(1);
            return;
        }

        String command = args[0].toLowerCase();

        switch (command) {
            case "help":
                showHelp();
                finish(0);
                break;
            case "list":
                finish(listNotes(notesDir) ? 0 : 1);
                break;
            case "read":
                if (args.length < 2) {
                    System.err.println("Error: 'read' requires a note number.");
                    System.err.println("Usage: java Notes2 read <n>");
                    finish(1);
                    return;
                }
                try {
                    int noteNumber = Integer.parseInt(args[1]);
                    finish(readNote(notesDir, noteNumber) ? 0 : 1);
                } catch (NumberFormatException e) {
                    System.err.println("Error: '" + args[1]
                            + "' is not a valid note number. Please provide an integer.");
                    finish(1);
                }
                break;
            case "create":
                finish(createNote(notesDir) ? 0 : 1);
                break;
            default:
                System.err.println("Error: Unknown command '" + command + "'");
                System.err.println("Try 'java Notes2 help' for more information.");
                finish(1);
        }
    }
}
