import sqlite3

def check_f2():
    db_path = 'backend/experiments.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM experiment_readings WHERE field_key = 'F2' ORDER BY id DESC LIMIT 5")
    rows = cursor.fetchall()
    
    print("Recent F2 Readings:")
    for row in rows:
        print(f"ID: {row['id']}, Value: {row['value']}, OCR_DATA: {row['ocr_data']}, Path: {row['image_path']}, Time: {row['timestamp']}")

    conn.close()

if __name__ == "__main__":
    check_f2()
