import streamlit as st
import helper


def bar_chart(df,select_column):
    col1,col2 = st.columns(2)
    for i,column in enumerate(select_column):
        if i%2==0:
            with col1:
                fig = helper.generate_chart(df,column,'bar')
                st.plotly_chart(fig)
        else:
            with col2:
                fig = helper.generate_chart(df,column,'bar')
                st.plotly_chart(fig)

def pie_chart(df,select_column):
    col1,col2 = st.columns(2)
    for i,column in enumerate(select_column):
        if i%2==0:
            with col1:
                fig = helper.generate_chart(df,column,'pie')
                st.plotly_chart(fig)
        else:
            with col2:
                fig = helper.generate_chart(df,column,'pie')
                st.plotly_chart(fig)