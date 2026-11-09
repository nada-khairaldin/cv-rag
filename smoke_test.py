from cvrag import config, db, drive

print("1) config")
print("   port:", config.POSTGRES_PORT)
print("   key file:", config.GOOGLE_APPLICATION_CREDENTIALS)

print("2) database")
with db.get_connection() as conn:
    print("   connected to:", conn.execute("SELECT current_database(), current_user").fetchone())
    print("   pgvector:", conn.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'").fetchone())

print("3) drive: list files")
files = drive.list_files()
print("   found:", len(files))
for f in files:
    print("   -", f["name"], "|", f["mimeType"])

print("4) drive: download first file")
first = files[0]
data = drive.download_file(first["id"])
print("  ", first["name"], "|", len(data), "bytes | starts with", data[:5])