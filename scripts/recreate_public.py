import pandas as pd
import re
from sqlalchemy import text
from app.repositories.db import engine

cols_csv = r"c:\Users\JayantTatipamula\Projects\Winfo_Test_AI\winfotest-ai\Data for project\data-1786949262440.csv"
fks_csv = r"c:\Users\JayantTatipamula\Projects\Winfo_Test_AI\winfotest-ai\Data for project\data-1786949296925.csv"

df_cols = pd.read_csv(cols_csv)
df_fks = pd.read_csv(fks_csv)

with engine.connect() as conn:
    # We will create tables directly in public schema
    print("Creating tables in public schema...")
    
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
                
        # Drop table if exists to avoid conflicts, then recreate it
        drop_sql = f'DROP TABLE IF EXISTS public."{table}" CASCADE;'
        create_sql = f'CREATE TABLE public."{table}" (\n  ' + ",\n  ".join(col_defs) + "\n);"
        
        try:
            conn.execute(text(drop_sql))
            conn.execute(text(create_sql))
            conn.commit()
            print(f"Recreated table public.{table}")
        except Exception as e:
            print(f"Error creating table public.{table}: {e}")
            conn.rollback()

    # Add foreign keys
    print("\nAdding foreign key constraints in public schema...")
    for idx, row in df_fks.iterrows():
        local_tbl = row['local_table']
        local_col = row['local_column']
        ref_tbl = row['referenced_table']
        ref_col = row['referenced_column']
        
        fk_name = f"fk_{local_tbl}_{local_col}"
        alter_sql = f'ALTER TABLE public."{local_tbl}" ADD CONSTRAINT "{fk_name}" FOREIGN KEY ("{local_col}") REFERENCES public."{ref_tbl}" ("{ref_col}") ON DELETE CASCADE;'
        try:
            conn.execute(text(alter_sql))
            conn.commit()
        except Exception as e:
            conn.rollback()
            
    print("\nLocal public schema setup complete!")
