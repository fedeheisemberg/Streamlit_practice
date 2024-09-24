import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import pytz
import ta

##################################################################################
## PARTE 1: Definir Funciones para Obtener, Procesar y Crear Indicadores Técnicos ##
##################################################################################

# Obtener datos de acciones según el símbolo, el período y el intervalo
def fetch_stock_data(ticker, period, interval):
    end_date = datetime.now()
    if period == '1wk':
        start_date = end_date - timedelta(days=7)
    else:
        data = yf.download(ticker, period=period, interval=interval)
        return data

# Procesar los datos para que estén en la zona horaria correcta y tengan el formato adecuado
def process_data(data):
    if data.index.tzinfo is None:
        data.index = data.index.tz_localize('UTC')
    data.index = data.index.tz_convert('US/Eastern')
    data.reset_index(inplace=True)
    data.rename(columns={'Date': 'Datetime'}, inplace=True)
    return data

# Calcular métricas básicas a partir de los datos de acciones
def calculate_metrics(data):
    last_close = data['Close'].iloc[-1]
    prev_close = data['Close'].iloc[0]
    change = last_close - prev_close
    pct_change = (change / prev_close) * 100
    high = data['High'].max()
    low = data['Low'].min()
    volume = data['Volume'].sum()
    return last_close, change, pct_change, high, low, volume

# Agregar indicadores técnicos simples (SMA y EMA)
def add_technical_indicators(data):
    data['SMA_20'] = ta.trend.sma_indicator(data['Close'], window=20)
    data['EMA_20'] = ta.trend.ema_indicator(data['Close'], window=20)
    return data

##################################################################################
## PARTE 2: Crear la Interfaz Gráfica de la Aplicación del Panel de Control      ##
##################################################################################

# Configurar la página de Streamlit
st.set_page_config(layout="wide")
st.title('Panel de Control de Acciones en Tiempo Real')

# 2A: PARÁMETROS DE LA BARRA LATERAL ##############

# Barra lateral para los parámetros de usuario
st.sidebar.header('Parámetros del Gráfico')
ticker = st.sidebar.text_input('Símbolo', 'AAPL')
time_period = st.sidebar.selectbox('Período', ['1d', '1wk', '1mo', '1y', 'max'])
chart_type = st.sidebar.selectbox('Tipo de Gráfico', ['Vela', 'Línea'])
indicators = st.sidebar.multiselect('Indicadores Técnicos', ['SMA 20', 'EMA 20'])

# Mapeo de períodos a intervalos de datos
interval_mapping = {
    '1d': '1m',
    '1wk': '30m',
    '1mo': '1d',
    '1y': '1wk',
    'max': '1wk'
}

# 2B: ÁREA DE CONTENIDO PRINCIPAL ##############

# Actualizar el panel de control según la entrada del usuario
if st.sidebar.button('Actualizar'):
    data = fetch_stock_data(ticker, time_period, interval_mapping[time_period])
    data = process_data(data)
    data = add_technical_indicators(data)

    last_close, change, pct_change, high, low, volume = calculate_metrics(data)

    # Mostrar las métricas principales
    st.metric(label=f"{ticker} Último Precio", value=f"{last_close:.2f} USD", delta=f"{change:.2f} ({pct_change:.2f}%)")

    col1, col2, col3 = st.columns(3)
    col1.metric("Alto", f"{high:.2f} USD")
    col2.metric("Bajo", f"{low:.2f} USD")
    col3.metric("Volumen", f"{volume:,}")

    # Graficar los datos históricos y los indicadores técnicos
    fig = go.Figure()
    if chart_type == 'Vela':
        fig.add_trace(go.Candlestick(x=data['Datetime'], open=data['Open'], high=data['High'], low=data['Low'], close=data['Close']))
    else:
        fig = px.line(data, x='Datetime', y='Close')

    if 'SMA 20' in indicators:
        fig.add_trace(go.Scatter(x=data['Datetime'], y=data['SMA_20'], name='SMA 20'))
    if 'EMA 20' in indicators:
        fig.add_trace(go.Scatter(x=data['Datetime'], y=data['EMA_20'], name='EMA 20'))

    fig.update_layout(title=f"Gráfico de {ticker}", xaxis_title='Tiempo', yaxis_title='Precio (USD)', height=600)
    st.plotly_chart(fig, use_container_width=True)

# Sección de información de la barra lateral
st.sidebar.subheader('About')
st.sidebar.info('Este panel de control proporciona datos de acciones e indicadores técnicos para varios períodos de tiempo. Utilice la barra lateral para personalizar su vista.')