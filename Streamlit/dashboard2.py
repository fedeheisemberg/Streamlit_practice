import streamlit as st
import yfinance as yf
import pandas as pd

# Título de la aplicación
st.title('Precios Históricos de Acciones de Tecnología (Últimos 10 Años)')

# Lista de los tickers de las empresas
tickers = ['TSM', 'NVDA', 'INTC', 'AAPL']  # Samsung es '005930.KS'

# Múltiple selección de los tickers
dropdown = st.multiselect('Selecciona tus activos: ', tickers, default=tickers)

# Seleccionar el rango de fechas
start = st.date_input('Fecha de inicio', value=pd.to_datetime('2013-09-01'))
end = st.date_input('Fecha de fin', value=pd.to_datetime('today'))

# Si se seleccionan tickers, obtener los datos
if len(dropdown) > 0:
    # Descargar los precios ajustados de cierre
    df = yf.download(dropdown, start, end)['Adj Close']

    # Mostrar los precios históricos
    st.header('Precios Históricos de {}'.format(', '.join(dropdown)))
    st.line_chart(df)

