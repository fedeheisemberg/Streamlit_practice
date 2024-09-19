import streamlit as st
import yfinance as yf
import pandas as pd

st.title('Options Dashboard for Finance')

tickers=('GGAL.BA', 'PAMP.BA','AAPL','UNP','ORCL')

dropdown=st.multiselect('Selecciona tus activos: ', tickers)

start=st.date_input('Fecha de inicio',value=pd.to_datetime('2020-01-01'))
end=st.date_input('Fecha de fin',value=pd.to_datetime('today'))

def relativeret(df):
    rel=df.pct_change()
    cumret=(1+rel).cumprod()-1
    cumret=cumret.fillna(0)
    return cumret

if len(dropdown)>0:
    #df=yf.download(dropdown,start,end)['Adj Close']
    df=relativeret(yf.download(dropdown,start,end)['Adj Close'])
    st.header('Returns of {}'.format(dropdown))
    st.line_chart(df)
