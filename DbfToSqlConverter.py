# =================================================================
# 🤖 AI MAINTENANCE INSTRUCTIONS (KEEP THIS SECTION AT THE TOP)
# =================================================================
# When modifying this script, the AI must strictly follow these rules:
# 1. VERSIONING: Increment the VERSION variable and log changes in VERSION HISTORY.
# 2. LANGUAGE: Keep UI labels, buttons, and system logs in English.
# 3. PERFORMANCE: Do NOT remove 'fast_executemany = True' or the '.strip()' cleaning logic.
# 4. THREADING: Keep database operations inside 'threading.Thread' to prevent GUI freezing.
# 5. CODING STYLE: Follow the Segoe UI font settings. 
# 6. SILENT MODE: Do NOT use MessageBox popups. All feedback must go to the Operation Logs.
# 7. RESIZABLE UI: The window is resizable. Ensure 'System Logs' expands to fill space.
# 8. CONFIG: Use 'config.json' for server persistence. NO HARDCODED SECRETS.
#
# 📝 VERSION HISTORY & PACKAGING
# v1.7.0 - Error Handling: Enhanced dbfread import safety with detailed traceback logging for Windows Server 2016 compatibility.
# v1.6.9 - PyInstaller Fix: Changed to --onedir mode and added comprehensive hidden imports for dbfread.
# v1.6.8 - Version Bump: Advanced to next version.
# v1.6.6 - Packaging: Added --collect-all dbfread to resolve __import__ exception.
# v1.6.5 - Compatibility: Added dynamic ODBC driver detection (fallback to {SQL Server}).
#
# 📦 BUILD INSTRUCTION (Terminal):
# python -m PyInstaller --noconsole --onedir --collect-all dbfread --hidden-import=dbfread --hidden-import=dbfread.dbf --hidden-import=dbfread.field_parser --hidden-import=dbfread.ifiles --hidden-import=dbfread.exceptions --name "DBF_to_SQL_v1.7.0" DbfToSqlConverter.py -y
# =================================================================

import tkinter as tk
from tkinter import filedialog, ttk
import pyodbc
from datetime import datetime
import os
import threading
import time
import json

# --- Critical Fix for PyInstaller Import Error ---
try:
    import dbfread
    from dbfread import DBF
    import dbfread.dbf           # Force-loading sub-module
    import dbfread.field_parser   # Force-loading sub-module
    import dbfread.table          # Force-loading sub-module
    import dbfread.record         # Force-loading sub-module
    import dbfread.exceptions     # Force-loading sub-module
except ImportError as e:
    # This will show up in the console if the EXE fails to find the library
    print(f"Critical Import Failure: {e}")
    print(f"dbfread module path: {dbfread.__file__ if 'dbfread' in dir() else 'NOT FOUND'}")
    import traceback
    traceback.print_exc()
    import sys
    print(f"Python version: {sys.version}")
    print(f"sys.path: {sys.path}")

# --- Version & Constants ---
VERSION = "1.7.0"
CONFIG_FILE = "config.json"
APP_TITLE = "DBF-SQL-Converter"

# --- Styling ---
UI_FONT_BOLD = ("Segoe UI", 10, "bold")
UI_FONT_NORMAL = ("Segoe UI", 10)
LOG_FONT = ("Consolas", 10)

def log_message(message):
    current_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    full_msg = f"[{current_time}] {message}\n"
    state_log.config(state='normal')
    state_log.insert(tk.END, full_msg)
    state_log.see(tk.END)
    state_log.config(state='disabled')

def get_best_driver():
    installed_drivers = pyodbc.drivers()
    priorities = [
        "ODBC Driver 18 for SQL Server",
        "ODBC Driver 17 for SQL Server",
        "ODBC Driver 13 for SQL Server",
        "SQL Server Native Client 11.0",
        "SQL Server"
    ]
    for driver in priorities:
        if driver in installed_drivers:
            return f"{{{driver}}}"
    return "{SQL Server}"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_config():
    config = load_config()
    server = server_combo.get().strip()
    if server:
        servers = config.get("servers", [])
        if server not in servers:
            servers.append(server)
        config["servers"] = servers
        config["last_server"] = server
        config["auth_mode"] = auth_mode.get()
        config["last_user"] = user_entry.get() if auth_mode.get() == "SQL Auth" else ""
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)

def get_connection_string(database="master"):
    server = server_combo.get().strip()
    mode = auth_mode.get()
    driver = get_best_driver()
    
    if mode == "Windows Auth":
        return f"DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes;Connection Timeout=5;"
    elif mode == "SQL Auth":
        uid = user_entry.get()
        pwd = pwd_entry.get()
        return f"DRIVER={driver};SERVER={server};DATABASE={database};UID={uid};PWD={pwd};Connection Timeout=5;"
    elif mode == "Azure AD":
        return f"DRIVER={driver};SERVER={server};DATABASE={database};Authentication=ActiveDirectoryInteractive;Connection Timeout=5;"
    return ""

def on_db_dropdown_click():
    if not server_combo.get().strip():
        log_message("Error: Server Address is empty.")
        return
    root.config(cursor="watch")
    threading.Thread(target=get_databases, daemon=True).start()

def get_databases():
    conn_str = get_connection_string()
    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sys.databases WHERE database_id > 4 AND state = 0")
            db_names = [row.name for row in cursor.fetchall()]
            db_names.sort(key=str.lower)
            root.after(0, lambda: update_db_list(db_names))
    except Exception as e:
        root.after(0, lambda: root.config(cursor=""))
        log_message(f"Auth Error: {str(e).split(']')[-1]}")

def update_db_list(db_names):
    db_select['values'] = db_names
    root.config(cursor="")
    if db_names and db_select.get() == "Click to select database":
        db_select.current(0)

def toggle_auth_fields(event=None):
    mode = auth_mode.get()
    if mode == "SQL Auth":
        user_entry.config(state="normal")
        pwd_entry.config(state="normal")
    else:
        user_entry.config(state="normal")
        user_entry.delete(0, tk.END)
        user_entry.config(state="disabled")
        pwd_entry.config(state="normal")
        pwd_entry.delete(0, tk.END)
        pwd_entry.config(state="disabled")

def select_file():
    path = filedialog.askopenfilename(filetypes=[("DBF files", "*.dbf")])
    if path:
        file_label.set(path)
        pure_name = os.path.splitext(os.path.basename(path))[0]
        safe_name = "".join([c if c.isalnum() else "_" for c in pure_name])
        table_name_var.set(f"xxx_{safe_name}")
        log_message(f"Source: {os.path.basename(path)}")

def dbf_to_mssql_schema(field):
    mapping = {
        'C': f'NVARCHAR({field.length})', 
        'N': f'NUMERIC({field.length}, {field.decimal_count})' if field.decimal_count > 0 else 'INT', 
        'D': 'DATE', 'L': 'BIT', 'M': 'NVARCHAR(MAX)', 'F': 'FLOAT'
    }
    return mapping.get(field.type, f'NVARCHAR({field.length})')

def start_conversion_threaded():
    if not db_select.get() or db_select.get() == "Click to select database":
        log_message("Warning: Select a database first.")
        return
    save_config()
    btn_run.config(state='disabled')
    progress_bar['value'] = 0
    threading.Thread(target=process_conversion, daemon=True).start()

def process_conversion():
    db_name = db_select.get().strip()
    dbf_path = file_label.get().strip()
    target_table_name = table_name_var.get().strip()
    try:
        start_time = time.time()
        log_message(f">>> Task Started: [{target_table_name}]")
        
        # Safely import and load DBF
        try:
            from dbfread import DBF as DBFClass
            table = DBFClass(dbf_path, encoding='big5', load=True, ignore_missing_memofile=True)
        except Exception as import_err:
            log_message(f"❌ DBF Import Error: {import_err}")
            import traceback
            log_message(f"Traceback: {traceback.format_exc()}")
            return
        
        conn_str = get_connection_string(database=db_name)
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.fast_executemany = True 
            full_table_path = f"dbo.[{target_table_name}]"
            columns = [f"[{f.name}] {dbf_to_mssql_schema(f)}" for f in table.fields]
            cursor.execute(f"IF OBJECT_ID('{full_table_path}', 'U') IS NOT NULL DROP TABLE {full_table_path}")
            cursor.execute(f"CREATE TABLE {full_table_path} ({', '.join(columns)});")
            
            cleaned_data = [[val.strip() if isinstance(val, str) else val for val in record.values()] for record in table]
            placeholders = ', '.join(['?'] * len(table.fields))
            cursor.executemany(f"INSERT INTO {full_table_path} VALUES ({placeholders})", cleaned_data)
            conn.commit()
        
        duration = time.time() - start_time
        root.after(0, lambda: progress_bar.config(value=100))
        log_message(f"🎉 SUCCESS: {len(table)} rows in {duration:.2f}s")
    except Exception as e:
        import traceback
        log_message(f"❌ Error: {str(e)}")
        log_message(f"Details: {traceback.format_exc()}")
    finally:
        root.after(0, lambda: btn_run.config(state='normal'))

# --- UI Setup ---
root = tk.Tk()
root.title(f"{APP_TITLE} - v{VERSION}")
root.geometry("600x820")
root.minsize(580, 750)

config = load_config()

frame_top = tk.LabelFrame(root, text=" 1. SQL Server Connection ", font=UI_FONT_BOLD, padx=10, pady=10)
frame_top.pack(padx=15, pady=5, fill="x")

tk.Label(frame_top, text="Server Address:", font=UI_FONT_NORMAL).pack(anchor="w")
server_combo = ttk.Combobox(frame_top, values=config.get("servers", []), font=UI_FONT_NORMAL)
server_combo.set(config.get("last_server", ""))
server_combo.pack(fill="x", pady=2)

tk.Label(frame_top, text="Authentication:", font=UI_FONT_NORMAL).pack(anchor="w", pady=(5,0))
auth_mode = ttk.Combobox(frame_top, values=["Windows Auth", "SQL Auth", "Azure AD"], state="readonly", font=UI_FONT_NORMAL)
auth_mode.set(config.get("auth_mode", "Windows Auth"))
auth_mode.pack(fill="x", pady=2)
auth_mode.bind("<<ComboboxSelected>>", toggle_auth_fields)

auth_subframe = tk.Frame(frame_top)
auth_subframe.pack(fill="x", pady=5)
tk.Label(auth_subframe, text="User:", font=UI_FONT_NORMAL).grid(row=0, column=0, sticky="w")
user_entry = tk.Entry(auth_subframe, font=UI_FONT_NORMAL); user_entry.grid(row=0, column=1, sticky="ew", padx=5)
user_entry.insert(0, config.get("last_user", ""))
tk.Label(auth_subframe, text="Pass:", font=UI_FONT_NORMAL).grid(row=1, column=0, sticky="w")
pwd_entry = tk.Entry(auth_subframe, show="*", font=UI_FONT_NORMAL); pwd_entry.grid(row=1, column=1, sticky="ew", padx=5)
auth_subframe.columnconfigure(1, weight=1)

db_select = ttk.Combobox(frame_top, font=UI_FONT_NORMAL, state="readonly", postcommand=on_db_dropdown_click)
db_select.set("Click to select database"); db_select.pack(fill="x", pady=10)

toggle_auth_fields()

frame_file = tk.LabelFrame(root, text=" 2. Source Data Selection ", font=UI_FONT_BOLD, padx=10, pady=10)
frame_file.pack(padx=15, pady=5, fill="x")
file_label = tk.StringVar(value="No file selected")
tk.Button(frame_file, text="Select DBF File", font=UI_FONT_NORMAL, command=select_file).pack()
tk.Label(frame_file, textvariable=file_label, wraplength=500, fg="#555", font=("Segoe UI", 9, "italic")).pack()

frame_table = tk.LabelFrame(root, text=" 3. Destination Table Settings ", font=UI_FONT_BOLD, padx=10, pady=10)
frame_table.pack(padx=15, pady=5, fill="x")
table_name_var = tk.StringVar()
tk.Entry(frame_table, textvariable=table_name_var, width=45, font=("Consolas", 11, "bold"), fg="#D32F2F", justify="center").pack()

frame_action = tk.Frame(root, padx=15, pady=5)
frame_action.pack(fill="x")
progress_bar = ttk.Progressbar(frame_action, orient="horizontal", mode="determinate")
progress_bar.pack(fill="x", pady=5)
btn_run = tk.Button(frame_action, text="🚀 EXECUTE MIGRATION", bg="#005a9e", fg="white", font=("Segoe UI", 12, "bold"), height=2, command=start_conversion_threaded)
btn_run.pack(fill="x", pady=5)

frame_log = tk.LabelFrame(root, text=" Operation Logs ", font=UI_FONT_BOLD, padx=10, pady=10)
frame_log.pack(padx=15, pady=10, fill="both", expand=True)
state_log = tk.Text(frame_log, height=8, state='disabled', bg="#fdfdfd", font=LOG_FONT, borderwidth=0, wrap="none")
scrollbar_y = tk.Scrollbar(frame_log, orient="vertical", command=state_log.yview)
scrollbar_x = tk.Scrollbar(frame_log, orient="horizontal", command=state_log.xview)
state_log.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
state_log.grid(row=0, column=0, sticky="nsew")
scrollbar_y.grid(row=0, column=1, sticky="ns")
scrollbar_x.grid(row=1, column=0, sticky="ew")
frame_log.grid_rowconfigure(0, weight=1); frame_log.grid_columnconfigure(0, weight=1)

best_driver = get_best_driver()
log_message(f"Welcome to {APP_TITLE} v{VERSION}.")
log_message(f"Using Database Driver: {best_driver}")
root.mainloop()