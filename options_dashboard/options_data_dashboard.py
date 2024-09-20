import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

def calcular_macd(data, fast=12, slow=26, signal=9):
    """Calcula el MACD, la señal y el histograma para los precios de cierre."""
    exp1 = data['Close'].ewm(span=fast, adjust=False).mean()
    exp2 = data['Close'].ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histograma = macd - signal_line
    return macd, signal_line, histograma

def main():
    st.set_page_config(page_title="Panel de Opciones", layout="wide")  # Título en la pestaña del navegador
    st.title("📈 Mercados de Opciones y Estrategias")

    # Selector de acciones (tickers)
    stock = st.text_input("Selecciona el ticker del activo subyacente", value="NU")

    st.header(f'📊 Panel de Opciones para {stock}')

    # Obtener datos de stock
    ticker = yf.Ticker(stock)

    # Mostrar ratios financieros
    st.subheader("📊 Ratios Financieros")
    ratios_financieros = ticker.info
    if 'priceToBook' in ratios_financieros:
        st.write(f"**P/E Ratio**: {ratios_financieros.get('trailingPE', 'No disponible')}")
        st.write(f"**P/B Ratio**: {ratios_financieros.get('priceToBook', 'No disponible')}")
        st.write(f"**Dividendo (%)**: {ratios_financieros.get('dividendYield', 'No disponible') * 100 if ratios_financieros.get('dividendYield') else 'No disponible'}")
        st.write(f"**Beta**: {ratios_financieros.get('beta', 'No disponible')}")

    # Obtener precio actual de la acción
    precio_actual = ticker.history(period="1d")['Close'].iloc[-1]
    st.write(f"Precio actual de {stock}: ${precio_actual:.2f}")

    # Obtener datos de opciones
    opciones = ticker.options

    if not opciones:
        st.error(f"No hay datos de opciones disponibles para {stock}")
    else:
        # Permitir al usuario seleccionar la fecha de vencimiento
        vencimiento = st.selectbox("📅 Seleccionar Fecha de Vencimiento", opciones)

        # Obtener cadena de opciones
        cadena_opciones = ticker.option_chain(vencimiento)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📈 Calls")
            st.dataframe(cadena_opciones.calls)

        with col2:
            st.subheader("📉 Puts")
            st.dataframe(cadena_opciones.puts)

        # Graficar sonrisa de volatilidad implícita usando Plotly
        fig_vol = go.Figure()
        fig_vol.add_trace(go.Scatter(x=cadena_opciones.calls['strike'], y=cadena_opciones.calls['impliedVolatility'], mode='markers', name='Calls'))
        fig_vol.add_trace(go.Scatter(x=cadena_opciones.puts['strike'], y=cadena_opciones.puts['impliedVolatility'], mode='markers', name='Puts'))
        fig_vol.update_layout(title='📊 Sonrisa de Volatilidad Implícita', xaxis_title='Precio de Ejercicio', yaxis_title='Volatilidad Implícita')
        st.plotly_chart(fig_vol, use_container_width=True)

        # Gráfico de precio histórico
        fecha_fin = datetime.now()
        fecha_inicio = fecha_fin - timedelta(days=365)
        datos_hist = ticker.history(start=fecha_inicio, end=fecha_fin)

        fig_precio = go.Figure()
        fig_precio.add_trace(go.Scatter(x=datos_hist.index, y=datos_hist['Close'], mode='lines', name='Precio'))
        fig_precio.update_layout(title=f'📆 Precio Histórico de {stock} (Último Año)', xaxis_title='Fecha', yaxis_title='Precio')
        st.plotly_chart(fig_precio, use_container_width=True)

        # Calcular y graficar MACD (colocado debajo del gráfico del precio)
        st.subheader("📉 MACD")
        macd, signal_line, histograma = calcular_macd(datos_hist)
        fig_macd = go.Figure()
        fig_macd.add_trace(go.Scatter(x=datos_hist.index, y=macd, mode='lines', name='MACD'))
        fig_macd.add_trace(go.Scatter(x=datos_hist.index, y=signal_line, mode='lines', name='Línea de Señal'))
        fig_macd.add_trace(go.Bar(x=datos_hist.index, y=histograma, name='Histograma'))
        fig_macd.update_layout(title=f'MACD para {stock}', xaxis_title='Fecha', yaxis_title='MACD')
        st.plotly_chart(fig_macd, use_container_width=True)

        # Selector de Estrategias de Opciones
        st.subheader("💡 Selecciona una Estrategia de Opciones")
        estrategia = st.selectbox("Elige la Estrategia", ["Cono Comprado (Long Straddle)", "Cono Vendido (Short Straddle)", "Collar", "Bull Call Spread", "Bear Put Spread", "Mariposa (Butterfly Spread)"])

        # Lógica para cada estrategia
        if estrategia == "Cono Comprado (Long Straddle)":
            st.subheader("📐 Estrategia de Cono Comprado")
            capital_inicial = st.number_input("Capital Inicial ($)", min_value=100, value=1000, step=100)
            call_atm = cadena_opciones.calls[cadena_opciones.calls['inTheMoney'] == False].iloc[0]
            put_atm = cadena_opciones.puts[cadena_opciones.puts['inTheMoney'] == False].iloc[-1]
            costo_cono = call_atm['lastPrice'] + put_atm['lastPrice']
            num_conos = int(capital_inicial // (costo_cono * 100))
            st.write(f"Número de conos: {num_conos}")
            st.write(f"Precio de ejercicio: ${call_atm['strike']:.2f}")
            st.write(f"Costo total: ${(costo_cono * num_conos * 100):.2f}")
        
        elif estrategia == "Cono Vendido (Short Straddle)":
            st.subheader("📐 Estrategia de Cono Vendido")
            capital_inicial = st.number_input("Capital Inicial ($)", min_value=100, value=1000, step=100)
            call_atm = cadena_opciones.calls[cadena_opciones.calls['inTheMoney'] == False].iloc[0]
            put_atm = cadena_opciones.puts[cadena_opciones.puts['inTheMoney'] == False].iloc[-1]
            costo_cono = call_atm['lastPrice'] + put_atm['lastPrice']
            num_conos = int(capital_inicial // (costo_cono * 100))
            st.write(f"Número de conos vendidos: {num_conos}")
            st.write(f"Precio de ejercicio: ${call_atm['strike']:.2f}")
            st.write(f"Ingreso total: ${(costo_cono * num_conos * 100):.2f}")
        
        elif estrategia == "Collar":
            st.subheader("📐 Estrategia Collar")
            st.write("Implementación de Collar... (Detalles a definir)")
        
        elif estrategia == "Bull Call Spread":
            st.subheader("📐 Estrategia Bull Call Spread")
            st.write("Implementación del Bull Call Spread... (Detalles a definir)")

        elif estrategia == "Bear Put Spread":
            st.subheader("📐 Estrategia Bear Put Spread")
            st.write("Implementación del Bear Put Spread... (Detalles a definir)")

        elif estrategia == "Mariposa (Butterfly Spread)":
            st.subheader("📐 Estrategia Mariposa (Butterfly Spread)")
            st.write("Implementación de la Mariposa... (Detalles a definir)")

if __name__ == "__main__":
    main()

