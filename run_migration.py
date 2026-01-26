#!/usr/bin/env python
"""
Simple script to add missing columns to the memos table.
Run with: railway run python run_migration.py
"""
import os
from sqlalchemy import create_engine, text

# Get DATABASE_URL from environment (Railway provides this)
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL environment variable not set")
    print("Run this with: railway run python run_migration.py")
    exit(1)

# Fix the URL format for SQLAlchemy
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

print(f"Connecting to database...")
engine = create_engine(DATABASE_URL)

# SQL to add the missing columns (IF NOT EXISTS for idempotency)
migrations = [
    """
    ALTER TABLE memos
    ADD COLUMN IF NOT EXISTS catalysts JSON;
    """,
    """
    ALTER TABLE memos
    ADD COLUMN IF NOT EXISTS conviction_breakdown JSON;
    """,
    """
    ALTER TABLE memos
    ADD COLUMN IF NOT EXISTS macro_context JSON;
    """,
    """
    ALTER TABLE memos
    ADD COLUMN IF NOT EXISTS position_sizing JSON;
    """,
]

with engine.connect() as conn:
    for sql in migrations:
        try:
            print(f"Running: {sql.strip()[:60]}...")
            conn.execute(text(sql))
            conn.commit()
            print("  OK")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                print(f"  Column already exists, skipping")
            else:
                print(f"  Error: {e}")

print("\nMigration complete!")
print("The following columns have been added to the 'memos' table:")
print("  - catalysts (JSON)")
print("  - conviction_breakdown (JSON)")
print("  - macro_context (JSON)")
print("  - position_sizing (JSON)")
