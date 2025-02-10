import plotly.express as px
import utility
import pandas as pd
import streamlit as st

def sanitize_column_name(column_name):
    """Clean column names to be SQL-safe by replacing spaces and special characters."""
    # Replace spaces with underscores and remove/replace special characters
    column_name = column_name.strip()
    clean_name = column_name.replace(' ', '_')
    if '.' in clean_name:
        split_parts = clean_name.split('.')
        if len(split_parts) > 1 and split_parts[1].isdigit():
            clean_name = split_parts[0]+'_'+split_parts[1]
        elif len(split_parts) == 1:
            clean_name = split_parts[0]
    # Remove any non-alphanumeric characters except underscore
    clean_name = ''.join(char for char in clean_name if char.isalnum() or char == '_')
    clean_name = clean_name.lower()
    return clean_name

def detect_and_convert_dates(df):
    """Convert all datetime-eligible columns to datetime dtype."""
    date_formats = [
        '%d/%b/%Y',  # 15/Jan/2024
        '%Y-%m-%d',  # 2024-01-15
        '%d-%m-%Y',  # 15-01-2024
        '%d/%m/%Y',  # 15/01/2024
        '%m/%d/%Y',  # 01/15/2024
        '%Y/%m/%d'  # 2024/01/15
    ]

    for column in df.columns:
        if df[column].dtype == 'object':  # Only check object (string) columns
            for date_format in date_formats:
                try:
                    date_series = pd.to_datetime(df[column], format=date_format, errors='coerce')
                    valid_dates_ratio = 1 - (date_series.isna().sum() / len(date_series))

                    if valid_dates_ratio >= 0.7:  # If 70% or more values are valid dates
                        df[column] = date_series
                        break  # Stop trying other formats if successful
                except Exception as e:
                    st.error(e)
                    continue

    return df


def generate_chart(df, column, chart_type):
    """
    Helper function to generate either bar or pie chart using Plotly Express.

    Args:
        df (pandas.DataFrame): Input dataframe
        column (str): Column name to analyze
        chart_type (str): Type of chart ('bar' or 'pie')

    Returns:
        plotly.graph_objects.Figure: Generated chart
    """
    is_actual_revenue = column == 'actual_revenue'

    if is_actual_revenue and 'customer_name' in df.columns:
        # First, get total revenue by customer
        customer_revenue = df.groupby('sector_name')[column].sum().reset_index()
        customer_revenue.columns = ['Customer', 'Revenue']

        # Sort by revenue in descending order
        customer_revenue = customer_revenue.sort_values('Revenue', ascending=False)

        # Calculate cumulative percentage of total revenue
        total_revenue = customer_revenue['Revenue'].sum()
        customer_revenue['Revenue_Percentage'] = (customer_revenue['Revenue'] / total_revenue * 100).round(2)
        customer_revenue['Cumulative_Percentage'] = customer_revenue['Revenue_Percentage'].cumsum()

        # Select customers who contribute to the top 25% of revenue
        top_contributors = customer_revenue[customer_revenue['Cumulative_Percentage'] > 75].copy()

        # Calculate customer statistics for annotation
        total_customers = len(df['customer_name'].unique())
        top_customer_count = len(top_contributors)
        annotation_text = (f'{top_customer_count} out of {total_customers} customers '
                           f'({(top_customer_count / total_customers * 100):.1f}%) '
                           'contribute to top 25% of revenue')

        if chart_type == 'bar':
            fig = px.bar(
                top_contributors,
                x='Customer',
                y='Revenue',
                color='Customer',
                title='Customers Contributing to Top 25% of Total Revenue',
                labels={'Revenue': 'Revenue', 'Customer': 'Customer'}
            )
            fig.update_traces(
                hovertemplate='''<b>%{x}</b><br>
                                Revenue: %{y:,.2f}<br>
                                Contribution: %{customdata[0]:.2f}%<br>''',
                customdata=top_contributors[['Revenue_Percentage']]
            )

        else:  # pie chart
            fig = px.pie(
                top_contributors,
                values='Revenue',
                names='Customer',
                title='Customers Contributing to Top 25% of Total Revenue',
                hover_data=['Revenue_Percentage']
            )
            fig.update_traces(
                hovertemplate='''<b>%{label}</b><br>
                                Revenue: %{value:,.2f}<br>
                                Contribution: %{customdata[0]:.2f}%<br>'''
            )

    else:
        # Handle non-revenue columns
        column_counts = df[column].value_counts().reset_index()
        column_counts.columns = [column, 'count']

        if chart_type == 'bar':
            fig = px.bar(
                column_counts,
                x=column,
                y='count',
                color=column,
                title=f'{column} Distribution',
                labels={column: column, 'count': 'Count'}
            )
        else:  # pie chart
            fig = px.pie(
                column_counts,
                names=column,
                values='count',
                title=f'{column} Distribution'
            )

    # Add annotation after figure is created
    if is_actual_revenue and 'Customer Name' in df.columns:
        fig.add_annotation(
            text=annotation_text,
            xref="paper",
            yref="paper",
            x=0.5,
            y=-0.15,
            showarrow=False,
            font=dict(size=12)
        )

    return fig