import streamlit as st
import pandas as pd
import display
import helper
import utility

pd.set_option('display.float_format', lambda x: '%.3f' % x)
if 'confirm_delete_all' not in st.session_state:
    st.session_state.confirm_delete_all = False

def main():
    st.title('Management System')
    page = st.sidebar.radio('Main Menu',['Flood db','Bulk Delete','Summary'])
    utility.tables()
    if page == 'Flood db':
        table_name = st.text_input('Enter table name')
        tables = utility.fetch_data('tables')
        if not tables.empty:
            st.subheader('Tables')
            st.dataframe(tables['table_name'])
        file_uploader = st.file_uploader('Upload CSV or Excel',type=['csv','xlsx'])
        if file_uploader is not None:
            if file_uploader.name.endswith('.csv'):
                df = pd.read_csv(file_uploader)
            elif file_uploader.name.endswith('.xlsx'):
                xlsx = pd.ExcelFile(file_uploader)
                sheet_name = st.selectbox('Enter sheet name',xlsx.sheet_names)
                if sheet_name:
                    df = xlsx.parse(sheet_name)
                else:
                    df = xlsx.parse(0)
            if 'df' in locals():
                if not df.empty:
                    df = helper.detect_and_convert_dates(df)
                    df.columns = [helper.sanitize_column_name(col) for col in df.columns]
                    if df['location'].isin(['TOTAL','Total','total']).any():
                        df = df.iloc[:-1, :]
                st.write('Uploaded Data: ')
                st.dataframe(df)
                if table_name:
                    table_data = (table_name,)
                    utility.init_db(table_name, df.columns, df)
                    if st.button('Flood db'):
                        utility.insert_data('tables', ['table_name'], table_data)
                        utility.bulk_insert(df,table_name)
                        st.rerun()
    elif page == 'Bulk Delete':
        st.subheader('Bulk Delete')
        df = utility.fetch_data('tables')
        if not df.empty:
            table_name = st.selectbox('Select table name',df['table_name'].tolist())
            df1 = utility.fetch_data(table_name)
            null_counts = df1.isnull().sum()
            empty_counts = df1.apply(lambda col: (col == '').sum())

            # Combine the statistics
            stats = pd.DataFrame({
                'Column': df1.columns,
                'Null values': null_counts,
                'Empty strings': empty_counts
            })

            # Identify columns with null or empty values
            columns_with_issues = stats[(stats['Null values'] > 0) | (stats['Empty strings'] > 0)]
            col1, col2 = st.columns(2)
            with col1:
                if not columns_with_issues.empty:
                    st.write("Columns with Null or Empty Values:")
                    st.dataframe(columns_with_issues,hide_index=True)
                else:
                    st.info("No columns with null or empty values found.")
            with col2:
                # Display preview of rows where columns have null or empty values
                if not columns_with_issues.empty:
                    st.write("Preview of Rows with null or empty values:")
                    preview_df = df1[columns_with_issues['Column']]
                    st.dataframe(preview_df)
                else:
                    st.info("No columns with null or empty values found.")
            st.subheader('Column deletion')
            column = st.multiselect('Select column to drop',columns_with_issues['Column'])
            if st.button('Delete Columns'):
                utility.bulk_delete_column(df1,table_name,column)
                st.rerun()
            st.subheader('Delete all tables')
            tables = utility.fetch_data('tables')
            if not st.session_state.confirm_delete_all:
                if st.button('Delete all tables'):
                    st.session_state.confirm_delete_all = True
                    st.rerun()
            else:
                st.warning("⚠️ Are you sure you want to delete all tables? This action cannot be undone.")
                col1,col2 = st.columns(2)
                with col1:
                    if st.button('Confirm Delete All'):
                        utility.drop_tables(tables['table_name'])
                        utility.drop_tables(['tables'])
                        st.session_state.confirm_delete_all = False
                        st.success('All tables have been successfully deleted.')
                        st.rerun()
                with col2:
                    if st.button('Cancel'):
                        st.session_state.confirm_delete_all = False
                        st.info('Nothing was deleted')
                        st.rerun()

        else:
            st.info('No data')
    elif page == 'Summary':
        st.subheader('Summary')
        df1 = utility.fetch_data('tables')
        if not df1.empty:
            table_name = st.selectbox('Select table name',df1['table_name'].tolist())
            df = utility.fetch_data(table_name)
            st.dataframe(df,hide_index=True)
            if not df.empty:
                chart = st.radio('Chart',['Pie Chart','Bar Chart'],index=0)
                column = df.columns
                select_column = st.multiselect('Select a column from csv for pictorial representation',column)
                if chart == 'Pie Chart' and select_column:
                    display.pie_chart(df,select_column)
                elif chart == 'Bar Chart' and select_column:
                    display.bar_chart(df,select_column)
                else:
                    st.info('No column selected pls select a column')
            else:
                st.info('No data')
        else:
            st.info('No data to display')


if __name__ == '__main__':
    main()