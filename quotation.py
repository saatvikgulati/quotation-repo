import streamlit as st
import pandas as pd
import display
import helper
import utility

def main():
    st.title('Quotation Management System')
    page = st.sidebar.radio('Main Menu',['Flood db','Bulk Delete','Summary'])
    utility.tables()
    if page == 'Flood db':
        table_name = st.text_input('Enter table name')
        file_uploader = st.file_uploader('Upload CSV or Excel')
        if file_uploader is not None:
            if file_uploader.name.endswith('.csv'):
                df = pd.read_csv(file_uploader)
            elif file_uploader.name.endswith('.xlsx'):
                df = pd.read_excel(file_uploader)
            for column in df.columns:
                if df[column].dtype == 'object' and any(
                        (df[column].str.match(r'\d{4}-\d{2}-\d{2}')|
                        pd.to_datetime(df[column],format='%Y-%m-%d',errors='coerce').notnull())
                ):
                    df[column] = pd.to_datetime(df[column],format='%Y-%m-%d',errors='coerce')
            columns = df.columns.tolist()
            st.write('Uploaded Data: ')
            st.dataframe(df)
            if table_name:
                table_data = (table_name,)
                utility.init_db(table_name, columns, df)
                if st.button('Flood db'):
                    utility.insert_data('tables', ['table_name'], table_data)
                    utility.bulk_insert(df,table_name)
                    st.rerun()
    elif page == 'Bulk Delete':
        st.subheader('Bulk Delete')
        df = utility.fetch_data('tables')
        if not df.empty:
            table_name = st.selectbox('Select table name',df['table_name'].tolist())
            delete_from_file = st.file_uploader('Upload CSV or Excel to delete')
            if delete_from_file is not None:
                if table_name and delete_from_file.name.endswith('.csv'):
                    df1 = pd.read_csv(delete_from_file)
                elif table_name and delete_from_file.name.endswith('.xlsx'):
                    df1 = pd.read_excel(delete_from_file)
                id_column = st.selectbox('Select ID column from file',df1.columns.tolist())
                if st.button('Bulk Delete'):
                    utility.bulk_delete(df1,table_name,id_column)
                    helper.reset_auto_increment(table_name)
                    utility.delete_data('tables','table_name=?',(table_name,))
                    helper.reset_auto_increment('tables')
                    st.rerun()
        else:
            st.info('No data')
    elif page == 'Summary':
        st.subheader('Summary')
        df1 = utility.fetch_data('tables')
        if not df1.empty:
            table_name = st.selectbox('Select table name',df1['table_name'].tolist())
            df = utility.fetch_data(table_name)
            df = df.drop('id',axis=1)
            if not df.empty:
                chart = st.radio('Chart',['Pie Chart','Bar Chart'],index=0)
                column = df.columns.tolist()
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