import sqlite3

def check_f5():
    db_path = 'backend/experiments.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT prompt_template FROM instrument_templates WHERE instrument_type = '5'")
    row = cursor.fetchone()
    if row:
        print(row[0])
    else:
        print("F5 prompt not found.")
    conn.close()

if __name__ == "__main__":
    check_f5()
