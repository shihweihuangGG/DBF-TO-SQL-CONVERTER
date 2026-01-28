# Copilot Instructions for DBF-SQL-Converter

This document outlines essential guidelines for AI coding agents working on the `DBF-SQL-Converter` codebase. Adhering to these instructions will ensure immediate productivity and maintain project standards.

## 1. Big Picture Architecture

The `DBF-SQL-Converter` is a Python-based desktop application designed to migrate data from `.dbf` files into SQL Server databases.

*   **GUI (tkinter):** Provides the user interface for connection details, file selection, and process initiation. All user interactions and feedback are managed through this component.
*   **Data Conversion Core (dbfread, pyodbc):** Handles reading DBF files and writing data to SQL Server.
*   **Configuration Management (config.json):** Persists user settings like server addresses and authentication modes across sessions.
*   **Threading:** Database operations are explicitly run in separate threads to prevent the GUI from freezing, ensuring a responsive user experience.

## 2. Critical Developer Workflows

### Building the Application

The application is packaged into a standalone executable using `PyInstaller`.
To build the application, execute the following command in the terminal:
```bash
python -m PyInstaller --noconsole --onedir --collect-all dbfread --hidden-import=dbfread --hidden-import=dbfread.dbf --hidden-import=dbfread.field_parser --hidden-import=dbfread.ifiles --hidden-import=dbfread.exceptions --name "DBF_to_SQL_v1.7.0" DbfToSqlConverter.py -y
```
*Note: Changed from `--onefile` to `--onedir` mode to resolve PyInstaller import resolution issues with dbfread. The executable will be in a folder with supporting files.*
*Note: The version in `--name` should match the `VERSION` variable in `DbfToSqlConverter.py`.*
*Note: Removed deprecated hidden imports (`dbfread.table`, `dbfread.record`, `dbfread._version`, `dbfread._compat`) and added `dbfread.ifiles` for better module resolution.*

### Running the Application

The application can be run directly as a Python script or via its compiled executable:
*   **From source:** `python DbfToSqlConverter.py`
*   **From executable:** `dist/DBF_to_SQL_v1.7.0/DBF_to_SQL_v1.7.0.exe` (path may vary based on PyInstaller output)

## 3. Project-Specific Conventions and Patterns

### AI Maintenance Guidelines

Strictly adhere to the `# AI MAINTENANCE INSTRUCTIONS` section at the top of `DbfToSqlConverter.py`. Key points include:
*   **Versioning:** Always increment the `VERSION` variable in `DbfToSqlConverter.py` and add an entry to the `VERSION HISTORY` comment for any functional changes.
*   **Language:** All UI text, labels, buttons, and system log messages must be in English.
*   **Performance:** Do NOT remove `cursor.fast_executemany = True` or any `.strip()` data cleaning logic during database insertions, as these are critical for performance.
*   **Threading:** All long-running database operations (e.g., `get_databases`, `process_conversion`) MUST be executed within a `threading.Thread` to maintain GUI responsiveness.
*   **Error Handling & Logging:** Avoid `MessageBox` popups. All operational feedback, warnings, and errors must be directed to the `Operation Logs` area using the `log_message()` function.
*   **Configuration Persistence:** Use `config.json` for storing and retrieving user-specific settings. Absolutely no hardcoded secrets or sensitive information within the code.

### UI Principles

*   **Dynamic UI Updates:** When updating the GUI from a background thread, use `root.after(0, lambda: ...)` to ensure thread-safe updates.
*   **Resizable Layout:** The UI is designed to be resizable. Ensure that the `Operation Logs` (`state_log`) component expands correctly to fill available space.

### Database Connectivity

*   **Dynamic Driver Selection:** The `get_best_driver()` function automatically detects and prioritizes available SQL Server ODBC drivers. Ensure this logic is preserved for maximum compatibility.
*   **Connection Strings:** The `get_connection_string()` function constructs connection strings based on user selections (Windows Auth, SQL Auth, Azure AD).

## 4. Key Files and Directories

*   `DbfToSqlConverter.py`: The main application script containing all logic and UI definitions.
*   `config.json`: (Generated at runtime) Stores application configuration and user preferences.
*   `build/`: Directory containing PyInstaller build artifacts and the compiled executable.
