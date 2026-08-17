import os
import subprocess
import pandas as pd
from sqlalchemy import text
from app.repositories.db import engine

cols_csv = r"c:\Users\JayantTatipamula\Projects\Winfo_Test_AI\winfotest-ai\Data for project\data-1786949262440.csv"
fks_csv = r"c:\Users\JayantTatipamula\Projects\Winfo_Test_AI\winfotest-ai\Data for project\data-1786949296925.csv"
backup_file = r"c:\Users\JayantTatipamula\Projects\Winfo_Test_AI\winfotest-ai\Data for project\wt2devbackup1.sql"
pg_restore_path = r"C:\Program Files\PostgreSQL\18\bin\pg_restore.exe"

df_cols = pd.read_csv(cols_csv)
df_fks = pd.read_csv(fks_csv)

print("Step 1: Re-creating empty wt2dev schema tables...")
with engine.connect() as conn:
    conn.execute(text("DROP SCHEMA IF EXISTS wt2dev CASCADE;"))
    conn.execute(text("CREATE SCHEMA wt2dev;"))
    conn.commit()

    # Create tables under wt2dev
    tables = df_cols['table_name'].unique()
    for table in tables:
        cols_df = df_cols[df_cols['table_name'] == table]
        col_defs = []
        for idx, row in cols_df.iterrows():
            col_name = row['column_name']
            data_type = row['data_type']
            nullable = "NULL" if row['is_nullable'] == "YES" else "NOT NULL"
            
            # Handle primary keys
            pk = ""
            if col_name == f"{table}_id" or col_name == "id" or (table == "account" and col_name == "account_id"):
                pk = "PRIMARY KEY"
                
            default_val = ""
            if pd.notna(row['column_default']):
                raw_default = str(row['column_default'])
                # Skip sequence defaults for simplicity, or handle them
                if "nextval" in raw_default:
                    data_type = "SERIAL"
                    nullable = ""
                else:
                    default_val = f"DEFAULT {raw_default}"
                    
            # Avoid duplicate primary keys if data type is SERIAL
            if "SERIAL" in data_type:
                col_defs.append(f'"{col_name}" {data_type} {pk}')
            else:
                col_defs.append(f'"{col_name}" {data_type} {nullable} {default_val} {pk}')
                
        create_sql = f'CREATE TABLE wt2dev."{table}" (\n  ' + ",\n  ".join(col_defs) + "\n);"
        try:
            conn.execute(text(create_sql))
            conn.commit()
        except Exception as e:
            conn.rollback()

    # Add foreign keys under wt2dev
    for idx, row in df_fks.iterrows():
        local_tbl = row['local_table']
        local_col = row['local_column']
        ref_tbl = row['referenced_table']
        ref_col = row['referenced_column']
        
        fk_name = f"fk_{local_tbl}_{local_col}"
        alter_sql = f'ALTER TABLE wt2dev."{local_tbl}" ADD CONSTRAINT "{fk_name}" FOREIGN KEY ("{local_col}") REFERENCES wt2dev."{ref_tbl}" ("{ref_col}") ON DELETE CASCADE;'
        try:
            conn.execute(text(alter_sql))
            conn.commit()
        except Exception as e:
            conn.rollback()

print("\nStep 2: Restoring data into wt2dev schema using pg_restore...")
env = os.environ.copy()
env["PGPASSWORD"] = "pgadmin"

cmd = [
    pg_restore_path,
    "-h", "localhost",
    "-p", "5432",
    "-U", "postgres",
    "-d", "postgres",
    "--clean",
    "--no-owner",
    "--no-privileges",
    backup_file
]

try:
    result = subprocess.run(cmd, env=env, capture_output=True, text=True, errors="ignore")
    # Show output summaries to ensure it completed
    err_lines = [l for l in (result.stderr or "").splitlines() if "error" in l.lower()]
    print(f"pg_restore finished. Ignored errors: {len(err_lines)}")
except Exception as e:
    print("Failed to execute pg_restore:", e)

print("\nStep 3: Transferring tables from wt2dev to public schema...")
with engine.connect() as conn:
    # Get all tables in wt2dev
    res = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'wt2dev'"))
    tables = [r[0] for r in res.all()]
    print(f"Found {len(tables)} tables to move.")

    for table in tables:
        # Drop table in public first to prevent duplicate name error
        drop_sql = f'DROP TABLE IF EXISTS public."{table}" CASCADE;'
        move_sql = f'ALTER TABLE wt2dev."{table}" SET SCHEMA public;'
        try:
            conn.execute(text(drop_sql))
            conn.execute(text(move_sql))
            conn.commit()
            print(f"Moved table {table} to public schema")
        except Exception as e:
            print(f"Error moving table {table}: {e}")
            conn.rollback()

    # Drop wt2dev schema
    conn.execute(text("DROP SCHEMA IF EXISTS wt2dev CASCADE;"))
    conn.commit()

print("\nAll data successfully restored and moved to the public schema!")
