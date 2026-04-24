import sqlite3

def get_prompts():
    db_path = 'backend/experiments.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT instrument_type, name, prompt_template FROM instrument_templates WHERE instrument_type IN ('0', '1', '2', '3') ORDER BY instrument_type")
    rows = cursor.fetchall()

    for row in rows:
        f_id = f"F{row['instrument_type']}"
        print(f"\n[{f_id} · {row['name']}]")
        print("-" * 50)
        print(row['prompt_template'])
        print("-" * 50)

    conn.close()

if __name__ == "__main__":
    get_prompts()
