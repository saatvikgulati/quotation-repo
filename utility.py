import streamlit as st
from contextlib import contextmanager
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
            st.error(e)

def bulk_delete(df,table_name,column_name):
    with get_conn() as conn:
        cursor = conn.cursor()
        try:
            gen_ids = df[column_name].tolist()
            chunk_size = 999
            for i in range(0,len(gen_ids),chunk_size):
                chunk = gen_ids[i:i+chunk_size]
                placeholders = ','.join(['?']*len(chunk))
                query = f'delete from {table_name} where {column_name} in ({placeholders})'
                cursor.execute(query,chunk)
            conn.commit()
            st.success(f'Deleted {len(df)} rows from {table_name} table')
        except Exception as e:
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
            placeholders = ','.join(['?' for _ in column_names])
            query = f"insert into {table_name} ({','.join(column_names)}) values ({placeholders})"
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
            query = f'delete from {table_name} where {condition}'
            cursor.execute(query,condition_values)
            conn.commit()
            st.success(f'Data deleted from {table_name} table')
        except Exception as e:
            st.error(f'Data could not be deleted from {table_name} table')
            st.error(e)