import streamlit as st
import pandas as pd
import display
import helper
import utility

pd.set_option('display.float_format', lambda x: '%.3f' % x)

def main():
    st.title('Management System')
    page = st.sidebar.radio('Main Menu',['Flood db','Bulk Delete','Summary'])
    utility.tables()
    if page == 'Flood db':
        table_name = st.text_input('Enter table name')
        file_uploader = st.file_uploader('Upload CSV or Excel',type=['csv','xlsx'])
        if file_uploader is not None:
            if file_uploader.name.endswith('.csv'):
                df = pd.read_csv(file_uploader)
            elif file_uploader.name.endswith('.xlsx'):
                sheet_name = st.text_input('Enter sheet name')
                if sheet_name:
                    df = pd.read_excel(file_uploader,sheet_name)
            if 'df' in locals():
                if not df.empty:
                    df = helper.detect_and_convert_dates(df)
                    df.columns = [helper.sanitize_column_name(col) for col in df.columns]
                    if 'Total' in df['location'].values:
                        df = df[df['location'] != 'Total']
                # if 'Job Type.1' in df.columns:
                #     df = df.drop(['Job Type.1'], axis=1)
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
            delete_from_file = st.file_uploader('Upload CSV or Excel to delete',type=['csv','xlsx'])
            if delete_from_file is not None:
                if table_name and delete_from_file.name.endswith('.csv'):
                    df1 = pd.read_csv(delete_from_file)
                elif table_name and delete_from_file.name.endswith('.xlsx'):
                    sheet_name = st.text_input('Enter sheet name')
                    if sheet_name:
                        df1 = pd.read_excel(delete_from_file,sheet_name)
                    else:
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
            st.dataframe(df)
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