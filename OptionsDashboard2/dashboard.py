import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import yfinance as yf
import time
import plotly.graph_objects as go
from typing import Tuple
from functools import lru_cache

@st.cache_data(show_spinner=False)
@lru_cache(maxsize=8)
def get_options_data(symbol: str) -> pd.DataFrame:
    """
    Descarga y combina los datos de opciones call y put para un símbolo dado.
    
    Parámetros:
    symbol (str): Símbolo del subyacente (ej: "AAPL")
    
    Devuelve:
    pandas.DataFrame: Datos de opciones call y put combinados
    """
    tk = yf.Ticker(symbol)
    expirations = tk.options
    data = pd.DataFrame()

    for exp_td_str in expirations:
        exp_data = _process_expiration(symbol, exp_td_str)
        data = pd.concat([data, exp_data], ignore_index=True)

    return data

def _process_expiration(symbol: str, exp_td_str: str) -> pd.DataFrame:
    """
    Descarga los datos de opciones call y put de Yahoo Finance
    para una fecha de expiración específica.
    
    Parámetros:
    symbol (str): Símbolo del subyacente (ej: "AAPL")
    exp_td_str (str): Fecha de expiración en formato "%Y-%m-%d"
    
    Devuelve:
    pandas.DataFrame: Datos de opciones call y put combinados
    """
    options = yf.Ticker(symbol).option_chain(exp_td_str)
    
    calls = options.calls
    puts = options.puts
    
    # Agregar columna de tipo de opción
    calls['optionType'] = 'C'
    puts['optionType'] = 'P'
    
    # Agregar columna de símbolo subyacente
    calls['underlyingSymbol'] = symbol
    puts['underlyingSymbol'] = symbol
    
    # Combinar calls y puts en un único DataFrame
    exp_data = pd.concat([calls, puts], ignore_index=True)
    
    return exp_data

def display_options_dashboard(options_data: pd.DataFrame):
    """
    Muestra un dashboard con análisis y visualizaciones de los datos de opciones.
    
    Parámetros:
    options_data (pandas.DataFrame): Datos de opciones call y put combinados
    """
    st.set_page_config(page_title="Opciones GGAL", layout="wide")
    st.title("Análisis de Opciones")

    symbol = options_data['underlyingSymbol'].unique()[0]
    st.subheader(f"Datos de Opciones de {symbol}")

    # Mostrar estadísticas descriptivas
    st.subheader("Estadísticas Descriptivas")
    st.write(options_data.describe())

    # Gráfico de volumen de opciones
    st.subheader("Volumen de Opciones")
    _plot_volume_chart(options_data)

    # Gráfico de probabilidad
    st.subheader("Análisis de Probabilidad")
    _plot_probability_chart(options_data)

    # Gráfico de velas del subyacente
    st.subheader("Precio del Subyacente")
    _plot_candlestick_chart(symbol)

    # Gráfico de relación de volatilidad call/put
    st.subheader("Relación de Volatilidad Call/Put")
    _plot_volatility_ratio_chart(options_data)

def _plot_volume_chart(data: pd.DataFrame):
    """
    Genera un gráfico de volumen de opciones.
    
    Parámetros:
    data (pandas.DataFrame): Datos de opciones
    """
    fig = go.Figure()
    fig.add_trace(go.Bar(x=data[data['optionType'] == 'C']['contractSymbol'], y=data[data['optionType'] == 'C']['volume'], name='Calls'))
    fig.add_trace(go.Bar(x=data[data['optionType'] == 'P']['contractSymbol'], y=data[data['optionType'] == 'P']['volume'], name='Puts'))
    fig.update_layout(title='Volumen de Opciones', xaxis_title='Símbolo de Opción', yaxis_title='Volumen')
    st.plotly_chart(fig, use_container_width=True)

def _plot_probability_chart(data: pd.DataFrame):
    """
    Genera un gráfico de probabilidad con Plotly.
    
    Parámetros:
    data (pandas.DataFrame): Datos de opciones
    """
    strikes = data['strike'].unique()
    calls_prob = (data[data['optionType'] == 'C']['openInterest'] / data[data['optionType'] == 'C']['volume']).reindex(strikes).fillna(0)
    puts_prob = (data[data['optionType'] == 'P']['openInterest'] / data[data['optionType'] == 'P']['volume']).reindex(strikes).fillna(0)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=strikes, y=calls_prob * 100, mode='lines', name='Calls'))
    fig.add_trace(go.Scatter(x=strikes, y=puts_prob * 100, mode='lines', name='Puts'))
    fig.update_layout(title='Curva de Probabilidad', xaxis_title='Strike', yaxis_title='Probabilidad (%)')
    st.plotly_chart(fig, use_container_width=True)

def _plot_candlestick_chart(symbol: str):
    """
    Genera un gráfico de velas (candlestick) del precio del subyacente.
    
    Parámetros:
    symbol (str): Símbolo del subyacente (ej: "AAPL")
    """
    tk = yf.Ticker(symbol)
    data = tk.history(period="1y")
    
    fig = go.Figure(data=[go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close']
    )])
    fig.update_layout(title=f"Precio de {symbol}", xaxis_title="Fecha", yaxis_title="Precio")
    st.plotly_chart(fig, use_container_width=True)

def _plot_volatility_ratio_chart(data: pd.DataFrame):
    """
    Genera un gráfico de la relación de volatilidad call/put.
    
    Parámetros:
    data (pandas.DataFrame): Datos de opciones
    """
    calls_iv = data[data['optionType'] == 'C']['impliedVolatility']
    puts_iv = data[data['optionType'] == 'P']['impliedVolatility']
    ratio = calls_iv / puts_iv
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data['strike'], y=ratio, mode='lines'))
    fig.update_layout(title='Relación de Volatilidad Call/Put', xaxis_title='Strike', yaxis_title='Ratio')
    st.plotly_chart(fig, use_container_width=True)

def main():
    symbol = st.text_input("Ingrese el símbolo del subyacente (ej: AAPL):", "AAPL")
    ggal_options = get_options_data(symbol)
    display_options_dashboard(ggal_options)

if __name__ == "__main__":
    main()