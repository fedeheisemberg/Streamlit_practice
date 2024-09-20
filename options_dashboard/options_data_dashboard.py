import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

stock='NU'

st.title(f'Panel de Opciones para {stock}')

# Obtener datos de GGAL.BA
ticker = yf.Ticker(stock)

# Obtener precio actual de la acción
precio_actual = ticker.history(period="1d")['Close'].iloc[-1]

st.write(f"Precio actual de {stock}: ${precio_actual:.2f}")

# Obtener datos de opciones
opciones = ticker.options

if not opciones:
    st.error("No hay datos de opciones disponibles para {stock}")
else:
    # Permitir al usuario seleccionar la fecha de vencimiento
    vencimiento = st.selectbox("Seleccionar Fecha de Vencimiento", opciones)

    # Obtener cadena de opciones
    cadena_opciones = ticker.option_chain(vencimiento)

    # Mostrar tablas de calls y puts
    st.subheader("Calls")
    st.dataframe(cadena_opciones.calls)

    st.subheader("Puts")
    st.dataframe(cadena_opciones.puts)

    # Graficar sonrisa de volatilidad implícita usando Seaborn
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.scatterplot(x='strike', y='impliedVolatility', data=cadena_opciones.calls, label='Calls', ax=ax)
    sns.scatterplot(x='strike', y='impliedVolatility', data=cadena_opciones.puts, label='Puts', ax=ax)
    
    ax.set_title('Sonrisa de Volatilidad Implícita')
    ax.set_xlabel('Precio de Ejercicio')
    ax.set_ylabel('Volatilidad Implícita')
    ax.legend()

    st.pyplot(fig)

    # Gráfico de precio histórico
    fecha_fin = datetime.now()
    fecha_inicio = fecha_fin - timedelta(days=365)
    datos_hist = ticker.history(start=fecha_inicio, end=fecha_fin)

    fig_precio, ax_precio = plt.subplots(figsize=(10, 6))
    sns.lineplot(x=datos_hist.index, y=datos_hist['Close'], ax=ax_precio)
    ax_precio.set_title(f'Precio Histórico de {stock} (Último Año)')
    ax_precio.set_xlabel('Fecha')
    ax_precio.set_ylabel('Precio')
    st.pyplot(fig_precio)

    # Estrategia de Cono Comprado (Long Straddle)
    st.subheader("Estrategia de Cono Comprado")
    capital_inicial = st.number_input("Capital Inicial ($)", min_value=100, value=1000, step=100)

    call_atm = cadena_opciones.calls[cadena_opciones.calls['inTheMoney'] == False].iloc[0]
    put_atm = cadena_opciones.puts[cadena_opciones.puts['inTheMoney'] == False].iloc[-1]

    costo_cono = call_atm['lastPrice'] + put_atm['lastPrice']
    num_conos = capital_inicial // (costo_cono * 100)

    st.write(f"Número de conos: {num_conos}")
    st.write(f"Precio de ejercicio: ${call_atm['strike']:.2f}")
    st.write(f"Costo total: ${(costo_cono * num_conos * 100):.2f}")

    # Gráfico de Ganancias/Pérdidas
    strikes = pd.concat([cadena_opciones.calls['strike'], cadena_opciones.puts['strike']]).unique()
    strikes.sort()

    ganancias = []
    for strike in strikes:
        ganancia = num_conos * (max(0, strike - call_atm['strike']) + max(0, put_atm['strike'] - strike) - costo_cono) * 100
        ganancias.append(ganancia)

    fig_pl, ax_pl = plt.subplots(figsize=(10, 6))
    sns.lineplot(x=strikes, y=ganancias, ax=ax_pl)
    ax_pl.axhline(y=0, linestyle='--', color='red')
    ax_pl.axvline(x=precio_actual, linestyle='--', color='green')
    ax_pl.text(precio_actual, ax_pl.get_ylim()[1], 'Precio Actual', rotation=90, va='top')
    ax_pl.set_title('Ganancia/Pérdida del Cono Comprado al Vencimiento')
    ax_pl.set_xlabel('Precio de la Acción')
    ax_pl.set_ylabel('Ganancia/Pérdida ($)')
    st.pyplot(fig_pl)