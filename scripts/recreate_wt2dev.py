import pandas as pd
import re
from sqlalchemy import text
from app.repositories.db import engine

cols_csv = r"c:\Users\JayantTatipamula\Projects\Winfo_Test_AI\winfotest-ai\Data for project\data-1786949262440.csv"
fks_csv = r"c:\Users\JayantTatipamula\Projects\Winfo_Test_AI\winfotest-ai\Data for project\data-1786949296925.csv"

df_cols = pd.read_csv(cols_csv)
df_fks = pd.read_csv(fks_csv)

with engine.connect() as conn:
    # 1. Create schema
    print("Creating wt2dev schema...")
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS wt2dev;"))
    conn.commit()

    # 2. Create tables
    tables = df_cols['table_name'].unique()
    for table in tables:
        cols_df = df_cols[df_cols['table_name'] == table]
        col_defs = []
        for idx, row in cols_df.iterrows():
            col_name = row['column_name']
            data_type = row['data_type']
            nullable = "NULL" if row['is_nullable'] == "YES" else "NOT NULL"
            
            # Handle primary keys (we can infer them if they end with _id or id)
            pk = ""
            if col_name == f"{table}_id" or col_name == "id" or (table == "account" and col_name == "account_id"):
                pk = "PRIMARY KEY"
                
            default_val = ""
            if pd.notna(row['column_default']):
                raw_default = str(row['column_default'])
                # Skip sequence defaults for simplicity, or handle them
                if "nextval" in raw_default:
                    # Let's convert to serial or identity
                    data_type = "SERIAL"
                    nullable = ""
                else:
                    default_val = f"DEFAULT {raw_default}"
                    
            # Avoid duplicate primary keys if data type is SERIAL
            if "SERIAL" in data_type:
                col_defs.append(f'"{col_name}" {data_type} {pk}')
            else:
                col_defs.append(f'"{col_name}" {data_type} {nullable} {default_val} {pk}')
                
        create_sql = f'CREATE TABLE IF NOT EXISTS wt2dev."{table}" (\n  ' + ",\n  ".join(col_defs) + "\n);"
        print(f"Creating table {table}...")
        try:
            conn.execute(text(create_sql))
            conn.commit()
        except Exception as e:
            print(f"Error creating table {table}: {e}")
            conn.rollback()

    # 3. Add foreign keys
    print("\nAdding foreign key constraints...")
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
            # Foreign keys might already exist or referenced table key might mismatch, handle gracefully
            conn.rollback()
            
    print("\nLocal wt2dev schema setup complete!")
