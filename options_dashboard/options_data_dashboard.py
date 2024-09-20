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
    st.set_page_config(page_title="Panel de Opciones", layout="wide")
    st.title("📈 Mercados de Opciones y Estrategias")

    stock = st.text_input("Selecciona el ticker del activo subyacente", value="GGAL")

    st.header(f'📊 Panel de Opciones para {stock}')

    ticker = yf.Ticker(stock)

    st.subheader("📊 Ratios Financieros")
    ratios_financieros = ticker.info
    if 'priceToBook' in ratios_financieros:
        st.write(f"**P/E Ratio**: {ratios_financieros.get('trailingPE', 'No disponible')}")
        st.write(f"**P/B Ratio**: {ratios_financieros.get('priceToBook', 'No disponible')}")
        st.write(f"**Dividendo (%)**: {ratios_financieros.get('dividendYield', 'No disponible') * 100 if ratios_financieros.get('dividendYield') else 'No disponible'}")
        st.write(f"**Beta**: {ratios_financieros.get('beta', 'No disponible')}")

    precio_actual = ticker.history(period="1d")['Close'].iloc[-1]
    st.write(f"Precio actual de {stock}: ${precio_actual:.2f}")

    opciones = ticker.options

    if not opciones:
        st.error(f"No hay datos de opciones disponibles para {stock}")
    else:
        vencimiento = st.selectbox("📅 Seleccionar Fecha de Vencimiento", opciones)

        cadena_opciones = ticker.option_chain(vencimiento)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📈 Calls")
            st.dataframe(cadena_opciones.calls)

        with col2:
            st.subheader("📉 Puts")
            st.dataframe(cadena_opciones.puts)

        fig_vol = go.Figure()
        fig_vol.add_trace(go.Scatter(x=cadena_opciones.calls['strike'], y=cadena_opciones.calls['impliedVolatility'], mode='markers', name='Calls'))
        fig_vol.add_trace(go.Scatter(x=cadena_opciones.puts['strike'], y=cadena_opciones.puts['impliedVolatility'], mode='markers', name='Puts'))
        fig_vol.update_layout(title='📊 Sonrisa de Volatilidad Implícita', xaxis_title='Precio de Ejercicio', yaxis_title='Volatilidad Implícita')
        st.plotly_chart(fig_vol, use_container_width=True)

        fecha_fin = datetime.now()
        fecha_inicio = fecha_fin - timedelta(days=365)
        datos_hist = ticker.history(start=fecha_inicio, end=fecha_fin)

        fig_precio = go.Figure()
        fig_precio.add_trace(go.Scatter(x=datos_hist.index, y=datos_hist['Close'], mode='lines', name='Precio'))
        fig_precio.update_layout(title=f'📆 Precio Histórico de {stock} (Último Año)', xaxis_title='Fecha', yaxis_title='Precio')
        st.plotly_chart(fig_precio, use_container_width=True)

        st.subheader("📉 MACD")
        macd, signal_line, histograma = calcular_macd(datos_hist)
        fig_macd = go.Figure()
        fig_macd.add_trace(go.Scatter(x=datos_hist.index, y=macd, mode='lines', name='MACD'))
        fig_macd.add_trace(go.Scatter(x=datos_hist.index, y=signal_line, mode='lines', name='Línea de Señal'))
        fig_macd.add_trace(go.Bar(x=datos_hist.index, y=histograma, name='Histograma'))
        fig_macd.update_layout(title=f'MACD para {stock}', xaxis_title='Fecha', yaxis_title='MACD')
        st.plotly_chart(fig_macd, use_container_width=True)

        st.subheader("💡 Selecciona una Estrategia de Opciones")
        estrategia = st.selectbox("Elige la Estrategia", ["Cono Comprado (Long Straddle)", "Cono Vendido (Short Straddle)", "Collar", "Bull Call Spread", "Bear Put Spread", "Mariposa (Butterfly Spread)"])

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
            
            strikes = pd.concat([cadena_opciones.calls['strike'], cadena_opciones.puts['strike']]).unique()
            strikes.sort()

            ganancias = [num_conos * (max(0, strike - call_atm['strike']) + max(0, put_atm['strike'] - strike) - costo_cono) * 100 for strike in strikes]

            fig_pl = go.Figure()
            fig_pl.add_trace(go.Scatter(x=strikes, y=ganancias, mode='lines', name='Ganancia/Pérdida'))
            fig_pl.add_hline(y=0, line_dash="dash", line_color="red")
            fig_pl.add_vline(x=precio_actual, line_dash="dash", line_color="green", annotation_text="Precio Actual", annotation_position="top right")
            fig_pl.update_layout(title='Ganancia/Pérdida del Cono Comprado al Vencimiento', xaxis_title='Precio de la Acción', yaxis_title='Ganancia/Pérdida ($)')
            st.plotly_chart(fig_pl, use_container_width=True)
        
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

            strikes = pd.concat([cadena_opciones.calls['strike'], cadena_opciones.puts['strike']]).unique()
            strikes.sort()

            ganancias = [num_conos * (costo_cono - max(0, strike - call_atm['strike']) - max(0, put_atm['strike'] - strike)) * 100 for strike in strikes]

            fig_pl = go.Figure()
            fig_pl.add_trace(go.Scatter(x=strikes, y=ganancias, mode='lines', name='Ganancia/Pérdida'))
            fig_pl.add_hline(y=0, line_dash="dash", line_color="red")
            fig_pl.add_vline(x=precio_actual, line_dash="dash", line_color="green", annotation_text="Precio Actual", annotation_position="top right")
            fig_pl.update_layout(title='Ganancia/Pérdida del Cono Vendido al Vencimiento', xaxis_title='Precio de la Acción', yaxis_title='Ganancia/Pérdida ($)')
            st.plotly_chart(fig_pl, use_container_width=True)
        
        elif estrategia == "Collar":
            st.subheader("📐 Estrategia Collar")
            capital_inicial = st.number_input("Capital Inicial ($)", min_value=100, value=1000, step=100)
            num_acciones = int(capital_inicial // precio_actual)
            
            call_otm = cadena_opciones.calls[cadena_opciones.calls['strike'] > precio_actual].iloc[0]
            put_otm = cadena_opciones.puts[cadena_opciones.puts['strike'] < precio_actual].iloc[-1]
            
            costo_collar = call_otm['lastPrice'] - put_otm['lastPrice']
            
            st.write(f"Número de acciones: {num_acciones}")
            st.write(f"Precio de ejercicio Call (venta): ${call_otm['strike']:.2f}")
            st.write(f"Precio de ejercicio Put (compra): ${put_otm['strike']:.2f}")
            st.write(f"Costo/Ingreso neto del collar: ${(costo_collar * num_acciones * 100):.2f}")
            
            strikes = pd.concat([cadena_opciones.calls['strike'], cadena_opciones.puts['strike']]).unique()
            strikes.sort()
            
            ganancias = [num_acciones * (min(call_otm['strike'], max(put_otm['strike'], strike)) - precio_actual) - costo_collar * num_acciones * 100 for strike in strikes]
            
            fig_pl = go.Figure()
            fig_pl.add_trace(go.Scatter(x=strikes, y=ganancias, mode='lines', name='Ganancia/Pérdida'))
            fig_pl.add_hline(y=0, line_dash="dash", line_color="red")
            fig_pl.add_vline(x=precio_actual, line_dash="dash", line_color="green", annotation_text="Precio Actual", annotation_position="top right")
            fig_pl.update_layout(title='Ganancia/Pérdida del Collar al Vencimiento', xaxis_title='Precio de la Acción', yaxis_title='Ganancia/Pérdida ($)')
            st.plotly_chart(fig_pl, use_container_width=True)

        elif estrategia == "Bull Call Spread":
            st.subheader("📐 Estrategia Bull Call Spread")
            capital_inicial = st.number_input("Capital Inicial ($)", min_value=100, value=1000, step=100)
            
            call_buy = cadena_opciones.calls[cadena_opciones.calls['strike'] >= precio_actual].iloc[0]
            call_sell = cadena_opciones.calls[cadena_opciones.calls['strike'] > call_buy['strike']].iloc[0]
            
            costo_spread = call_buy['lastPrice'] - call_sell['lastPrice']
            num_spreads = int(capital_inicial // (costo_spread * 100))
            
            st.write(f"Número de spreads: {num_spreads}")
            st.write(f"Precio de ejercicio Call (compra): ${call_buy['strike']:.2f}")
            st.write(f"Precio de ejercicio Call (venta): ${call_sell['strike']:.2f}")
            st.write(f"Costo total del spread: ${(costo_spread * num_spreads * 100):.2f}")
            
            strikes = pd.concat([cadena_opciones.calls['strike'], cadena_opciones.puts['strike']]).unique()
            strikes.sort()
            
            ganancias = [num_spreads * (min(call_sell['strike'], max(call_buy['strike'], strike)) - call_buy['strike'] - costo_spread) * 100 for strike in strikes]
            
            fig_pl = go.Figure()
            fig_pl.add_trace(go.Scatter(x=strikes, y=ganancias, mode='lines', name='Ganancia/Pérdida'))
            fig_pl.add_hline(y=0, line_dash="dash", line_color="red")
            fig_pl.add_vline(x=precio_actual, line_dash="dash", line_color="green", annotation_text="Precio Actual", annotation_position="top right")
            fig_pl.update_layout(title='Ganancia/Pérdida del Bull Call Spread al Vencimiento', xaxis_title='Precio de la Acción', yaxis_title='Ganancia/Pérdida ($)')
            st.plotly_chart(fig_pl, use_container_width=True)

        elif estrategia == "Bear Put Spread":
            st.subheader("📐 Estrategia Bear Put Spread")
            capital_inicial = st.number_input("Capital Inicial ($)", min_value=100, value=1000, step=100)
            
            put_buy = cadena_opciones.puts[cadena_opciones.puts['strike'] <= precio_actual].iloc[-1]
            put_sell = cadena_opciones.puts[cadena_opciones.puts['strike'] < put_buy['strike']].iloc[-1]
            
            costo_spread = put_buy['lastPrice'] - put_sell['lastPrice']
            costo_spread = put_buy['lastPrice'] - put_sell['lastPrice']
            num_spreads = int(capital_inicial // (costo_spread * 100))

            
            st.write(f"Número de spreads: {num_spreads}")
            st.write(f"Precio de ejercicio Put (compra): ${put_buy['strike']:.2f}")
            st.write(f"Precio de ejercicio Put (venta): ${put_sell['strike']:.2f}")
            st.write(f"Costo total del spread: ${(costo_spread * num_spreads * 100):.2f}")
            
            strikes = pd.concat([cadena_opciones.calls['strike'], cadena_opciones.puts['strike']]).unique()
            strikes.sort()
            
            ganancias = [num_spreads * (put_buy['strike'] - max(put_sell['strike'], min(put_buy['strike'], strike)) - costo_spread) * 100 for strike in strikes]
            
            fig_pl = go.Figure()
            fig_pl.add_trace(go.Scatter(x=strikes, y=ganancias, mode='lines', name='Ganancia/Pérdida'))
            fig_pl.add_hline(y=0, line_dash="dash", line_color="red")
            fig_pl.add_vline(x=precio_actual, line_dash="dash", line_color="green", annotation_text="Precio Actual", annotation_position="top right")
            fig_pl.update_layout(title='Ganancia/Pérdida del Bear Put Spread al Vencimiento', xaxis_title='Precio de la Acción', yaxis_title='Ganancia/Pérdida ($)')
            st.plotly_chart(fig_pl, use_container_width=True)

        elif estrategia == "Mariposa (Butterfly Spread)":
            st.subheader("📐 Estrategia Mariposa (Butterfly Spread)")
            capital_inicial = st.number_input("Capital Inicial ($)", min_value=100, value=1000, step=100)
            
            call_buy_low = cadena_opciones.calls[cadena_opciones.calls['strike'] <= precio_actual].iloc[-1]
            call_sell_mid = cadena_opciones.calls[cadena_opciones.calls['strike'] > call_buy_low['strike']].iloc[0]
            call_buy_high = cadena_opciones.calls[cadena_opciones.calls['strike'] > call_sell_mid['strike']].iloc[0]
            
            costo_mariposa = call_buy_low['lastPrice'] - 2 * call_sell_mid['lastPrice'] + call_buy_high['lastPrice']
            num_mariposas = int(capital_inicial // (abs(costo_mariposa) * 100))
            
            st.write(f"Número de mariposas: {num_mariposas}")
            st.write(f"Precio de ejercicio Call (compra bajo): ${call_buy_low['strike']:.2f}")
            st.write(f"Precio de ejercicio Call (venta medio): ${call_sell_mid['strike']:.2f}")
            st.write(f"Precio de ejercicio Call (compra alto): ${call_buy_high['strike']:.2f}")
            st.write(f"Costo total de la mariposa: ${(costo_mariposa * num_mariposas * 100):.2f}")
            
            strikes = pd.concat([cadena_opciones.calls['strike'], cadena_opciones.puts['strike']]).unique()
            strikes.sort()
            
            ganancias = [num_mariposas * (max(0, strike - call_buy_low['strike']) - 2 * max(0, strike - call_sell_mid['strike']) + max(0, strike - call_buy_high['strike']) - costo_mariposa) * 100 for strike in strikes]
            
            fig_pl = go.Figure()
            fig_pl.add_trace(go.Scatter(x=strikes, y=ganancias, mode='lines', name='Ganancia/Pérdida'))
            fig_pl.add_hline(y=0, line_dash="dash", line_color="red")
            fig_pl.add_vline(x=precio_actual, line_dash="dash", line_color="green", annotation_text="Precio Actual", annotation_position="top right")
            fig_pl.update_layout(title='Ganancia/Pérdida de la Mariposa al Vencimiento', xaxis_title='Precio de la Acción', yaxis_title='Ganancia/Pérdida ($)')
            st.plotly_chart(fig_pl, use_container_width=True)

if __name__ == "__main__":
    main()