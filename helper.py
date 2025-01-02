import plotly.express as px
import utility
import streamlit as st

def generate_chart(df, column, chart_type):
    """Helper function to generate either bar or pie chart."""
    column_counts = df[column].value_counts().reset_index()
    column_counts.columns = [column, 'count']

    if chart_type == 'bar':
        fig = px.bar(column_counts, x=column, y='count', color=column, title=f'{column} Distribution',
                     labels={column: column, 'count': 'Count'})
    elif chart_type == 'pie':
        fig = px.pie(column_counts, names=column, values='count', title=f'{column} Distribution')

    return fig

def reset_auto_increment(table_name):
    with utility.get_conn() as conn:
        try:
            cursor = conn.cursor()
            cursor.execute(f'delete from sqlite_sequence where name=\'{table_name}\'')
            conn.commit()
            st.success(f'Reset auto increment counter for {table_name} table')
        except Exception as e:
            st.error(f'Error resetting auto-increment for {table_name} table')
            st.error(e)