"""One-time migration: add the geometry_json column to the existing 'routes' table.

Run this once against the PRODUCTION database (same way you ran seed_admin.py):
  set DATABASE_URL=<paste the Render external database URL>
  python add_geometry_column.py
  set DATABASE_URL=

Safe to run more than once - it only adds the column if it isn't already there.
"""
from sqlalchemy import text
from app.db.session import engine

with engine.begin() as conn:
    conn.execute(text("ALTER TABLE routes ADD COLUMN IF NOT EXISTS geometry_json TEXT"))

print("Done: routes.geometry_json is ready.")
