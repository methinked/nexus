#!/usr/bin/env python3
import sqlite3
import os

SOURCE_DB = "/home/methinked/nexus-core/data/nexus.db"
TARGET_DB = "/mnt/data/nexus_salvaged.db"

# Critical tables we need to keep
TABLES_TO_KEEP = ["nodes", "jobs", "metrics"]

print(f"Salvaging database from {SOURCE_DB} to {TARGET_DB}...")

# Create/connect to target
if os.path.exists(TARGET_DB):
    os.remove(TARGET_DB)
    
source_conn = sqlite3.connect(SOURCE_DB)
target_conn = sqlite3.connect(TARGET_DB)

# Copy schema and tables
try:
    source_cur = source_conn.cursor()
    target_cur = target_conn.cursor()
    
    # 1. Get all table schemas
    source_cur.execute("SELECT type, name, sql FROM sqlite_master WHERE type='table'")
    tables = source_cur.fetchall()
    
    for _, name, sql in tables:
        if name == "sqlite_sequence":
            continue
            
        print(f"Creating table '{name}'...")
        if sql:
            target_cur.execute(sql)
            
        # 2. Extract data (Skip the corrupted ones)
        if name in TABLES_TO_KEEP or name == "alembic_version":
            print(f"  Extracting rows from '{name}'...")
            try:
                # Use a larger page size to pull data aggressively but chunk by chunk to avoid loading it all in RAM
                source_cur.execute(f"SELECT * FROM {name}")
                while True:
                    rows = source_cur.fetchmany(1000)
                    if not rows:
                        break
                    
                    # Create the inserts dynamically
                    placeholders = ",".join(["?"] * len(rows[0]))
                    target_cur.executemany(f"INSERT INTO {name} VALUES ({placeholders})", rows)
                    target_conn.commit()
                print(f"  ✓ Extracted '{name}' successfully.")
            except sqlite3.DatabaseError as e:
                print(f"  X Failed to extract '{name}' due to SD card error: {e}")
                target_conn.rollback()
        else:
            print(f"  Skipping rows for '{name}' to save space/avoid errors.")

except Exception as e:
    print(f"Script error: {e}")

finally:
    target_conn.close()
    source_conn.close()
    print("Salvage complete!")
