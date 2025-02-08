import streamlit as st
from contextlib import contextmanager
import helper
import sqlite3
import pandas as pd

@st.cache_resource
def get_init_conn():
    return sqlite3.connect('my_database.db',check_same_thread=False)

@contextmanager
def get_conn():
    conn = get_init_conn()
    try:
        yield conn
    finally:
        conn.commit()

def init_db(table_name,columns,df):
    with get_conn() as conn:
        cursor = conn.cursor()
        try:
            column_definitions = []
            for column in columns:
                if df[column].dtype == 'object':
                    column_definitions.append(f'{column} text')
                elif df[column].dtype == 'float64':
                    column_definitions.append(f'{column} real')
                elif df[column].dtype == 'datetime64[ns]':
                    column_definitions.append(f'{column} datetime')
                elif df[column].dtype == 'int64':
                    column_definitions.append(f'{column} integer')
                else:
                    column_definitions.append(f'{column} text')

            column_definitions_str = ',\n'.join(column_definitions)
            create_table_query = f'''
                                create table if not exists {table_name} (
                                id integer primary key autoincrement,
                                {column_definitions_str}
                                )'''
            cursor.execute(create_table_query)
            conn.commit()
        except Exception as e:
            st.error(f'Cannot create {table_name} table')
            st.error(e)

def bulk_insert(df,table_name):
    with get_conn() as conn:
        try:
            df.to_sql(table_name,conn,if_exists='append',index=False)
            st.success(f'Successfully inserted {len(df)} rows into db')
        except Exception as e:
            st.error(f'Error in bulk insert into {table_name} table')
            print(e)
            st.error(e)

def bulk_delete(table_name,column_name):
    with get_conn() as conn:
        cursor = conn.cursor()
        try:
            existing_df = fetch_data(table_name)
            if column_name in existing_df.columns:
                existing_df = existing_df.drop(columns=column_name,axis=1)
            existing_df.to_sql(f'{table_name}_new',conn,if_exists='replace',index=False,chunksize=1000)
            cursor.execute(f'drop table if exists {table_name};')
            cursor.execute(f'alter table {table_name}_new rename to {table_name};')
            conn.commit()
            st.success(f'Delete column {column_name} from {table_name} table. Remaining rows: {len(existing_df)}')
            helper.drop_empty_tables(cursor,conn,table_name)
            helper.drop_empty_tables(cursor, conn, 'tables')
        except Exception as e:
            conn.rollback()
            st.error(f'Error in bulk delete from {table_name} table')
            st.error(e)

def fetch_data(table_name):
    with get_conn() as conn:
        try:
            df = pd.read_sql_query(f'select * from {table_name}',conn)
        except Exception as e:
            st.error(f'Error retrieving data from {table_name} table')
            st.error(e)
        finally:
            return df

def tables():
    with get_conn() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(f'''create table if not exists tables (
                            id integer primary key autoincrement,
                            table_name text not null unique
                            )''')
            conn.commit()
        except Exception as e:
            st.error('Error cannot create tables table')
            st.error(e)

def insert_data(table_name,column_names,values):
    with get_conn() as conn:
        cursor = conn.cursor()
        try:
            safe_columns = [helper.sanitize_column_name(col) for col in column_names]
            placeholders = ','.join(['?' for _ in safe_columns])
            columns_str = ','.join(f'"{col}"' for col in safe_columns)
            query = f"insert into {table_name} ({columns_str}) values ({placeholders})"
            cursor.execute(query,values)
            conn.commit()
            st.success(f'Data inserted successfully to {table_name} table')
        except Exception as e:
            st.error(f'Error while inserting data into {table_name} table')
            st.error(e)

def delete_data(table_name,condition,condition_values):
    with get_conn() as conn:
        cursor = conn.cursor()
        try:
            condition_splits = condition.split('=')
            if len(condition_splits)==2:
                safe_column = helper.sanitize_column_name(condition_splits[0].strip())
                condition = f'"{safe_column}" = ?'
            query = f'delete from {table_name} where {condition}'
            cursor.execute(query,condition_values)
            conn.commit()
            st.success(f'Data deleted from {table_name} table')
        except Exception as e:
            st.error(f'Data could not be deleted from {table_name} table')
            st.error(e)