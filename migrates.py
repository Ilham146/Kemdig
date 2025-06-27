import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()

# Tambahkan kolom is_deleted jika belum ada
try:
    c.execute("ALTER TABLE note ADD COLUMN is_deleted BOOLEAN DEFAULT 0")
    print("Kolom is_deleted berhasil ditambahkan.")
except sqlite3.OperationalError:
    print("Kolom is_deleted sudah ada.")

# Tambahkan kolom deleted_at jika belum ada
try:
    c.execute("ALTER TABLE note ADD COLUMN deleted_at TEXT")
    print("Kolom deleted_at berhasil ditambahkan.")
except sqlite3.OperationalError:
    print("Kolom deleted_at sudah ada.")

conn.commit()
conn.close()