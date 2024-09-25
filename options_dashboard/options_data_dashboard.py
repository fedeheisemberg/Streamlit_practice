#options_data_dashboard.py
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import seaborn as sns
import matplotlib.pyplot as plt
from subscription_manager import subscribe_user, save_feedback

# Configuración de la página
st.set_page_config(page_title="Dashboard OptionsPro", layout="wide")

# Cargar logo en el header
st.image("options_dashboard/logo2.png")

# Crear título
st.title("Dashboard OptionsPro - Optima Consulting & Management LLC")

def calcular_macd(data, fast=12, slow=26, signal=9):
    """Calcula el MACD, la señal y el histograma para los precios de cierre."""
    exp1 = data['Close'].ewm(span=fast, adjust=False).mean()
    exp2 = data['Close'].ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histograma = macd - signal_line
    return macd, signal_line, histograma

def candlestick_chart(prices):
    fig = go.Figure(data=[go.Candlestick(x=prices.index,
                open=prices['Open'],
                high=prices['High'],
                low=prices['Low'],
                close=prices['Close'])])
    fig.update_layout(xaxis_rangeslider_visible=False)
    st.plotly_chart(fig,use_container_width=True)

def get_eps_data(ticker, company):
    url = f"https://www.macrotrends.net/stocks/charts/{ticker}/{company}/eps-earnings-per-share-diluted"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', class_='historical_data_table')
        dates = []
        eps_values = []
        for row in table.find_all('tr')[1:]:
            columns = row.find_all('td')
            date = columns[0].get_text(strip=True)
            eps = columns[1].get_text(strip=True)
            dates.append(date)
            eps_values.append(eps)
        data = {'Date': dates, 'EPS (Earnings Per Share)': eps_values}
        df = pd.DataFrame(data)
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    else:
        st.error(f"La solicitud no fue exitosa. Código de respuesta: {response.status_code}")
        return None

def main():
    stock = st.text_input("Selecciona el ticker del activo subyacente", value="GGAL")

    st.header(f'📊 Panel de Opciones para {stock}')

    ticker = yf.Ticker(stock)

    # Ratios Financieros
    st.subheader("📊 Ratios Financieros")
    ratios_financieros = ticker.info
    if 'priceToBook' in ratios_financieros:
        st.write(f"**P/E Ratio**: {ratios_financieros.get('trailingPE', 'No disponible')}")
        st.write(f"**P/B Ratio**: {ratios_financieros.get('priceToBook', 'No disponible')}")
        st.write(f"**Dividendo (%)**: {ratios_financieros.get('dividendYield', 'No disponible') * 100 if ratios_financieros.get('dividendYield') else 'No disponible'}")
        st.write(f"**Beta**: {ratios_financieros.get('beta', 'No disponible')}")

    precio_actual = ticker.history(period="1d")['Close'].iloc[-1]
    st.write(f"Precio actual de {stock}: ${precio_actual:.2f}")

    # Gráfico de precios históricos
    st.subheader("📈 Gráfico de precios históricos")
    period = st.selectbox('Seleccionar periodo', ['1 Año','1 Mes', '3 Meses', '5 Años','1 Semana'])

    end_date = datetime.today()
    if period == '1 Año':
        start_date = end_date - pd.DateOffset(years=1)
    elif period == '3 Meses':
        start_date = end_date - pd.DateOffset(months=3)
    elif period == '1 Mes':
        start_date = end_date - pd.DateOffset(months=1)
    elif period == '1 Semana':
        start_date = end_date - pd.DateOffset(weeks=1)
    else:
        start_date = end_date - pd.DateOffset(years=5)

    datos_hist = ticker.history(start=start_date, end=end_date)
    candlestick_chart(datos_hist)

    # MACD
    st.subheader("📉 MACD")
    macd, signal_line, histograma = calcular_macd(datos_hist)
    fig_macd = go.Figure()
    fig_macd.add_trace(go.Scatter(x=datos_hist.index, y=macd, mode='lines', name='MACD'))
    fig_macd.add_trace(go.Scatter(x=datos_hist.index, y=signal_line, mode='lines', name='Línea de Señal'))
    fig_macd.add_trace(go.Bar(x=datos_hist.index, y=histograma, name='Histograma'))
    fig_macd.update_layout(title=f'MACD para {stock}', xaxis_title='Fecha', yaxis_title='MACD')
    st.plotly_chart(fig_macd, use_container_width=True)

    # Opciones
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

        # Análisis de volatilidad implícita
        st.subheader("Análisis de Volatilidad Implícita")
        st.markdown("""
        La sonrisa de volatilidad implícita refleja cómo la volatilidad cambia con el strike price.
        Una sonrisa pronunciada indica mayor incertidumbre en los extremos del rango de precios del activo subyacente.
        Opciones at-the-money tienden a tener menor volatilidad implícita, mientras que las out-of-the-money (OTM) muestran mayor volatilidad debido al riesgo.
        """)

        # Sonrisa de Volatilidad Implícita
        fig_vol = go.Figure()
        fig_vol.add_trace(go.Scatter(x=cadena_opciones.calls['strike'], y=cadena_opciones.calls['impliedVolatility'], mode='markers', name='Calls'))
        fig_vol.add_trace(go.Scatter(x=cadena_opciones.puts['strike'], y=cadena_opciones.puts['impliedVolatility'], mode='markers', name='Puts'))
        fig_vol.update_layout(title='📊 Sonrisa de Volatilidad Implícita', xaxis_title='Precio de Ejercicio', yaxis_title='Volatilidad Implícita')
        st.plotly_chart(fig_vol, use_container_width=True)

    # Estrategias de Opciones
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

    # Descripción de Estrategias de Opciones
    st.subheader("📈 Descripción de Estrategias de Opciones")
    st.markdown("""
    ### Estrategias Comunes:
    1. **📊 Call Compra**: Usar cuando se espera un aumento significativo en el precio del activo subyacente.
    2. **🔻 Put Venta**: Estrategia defensiva para protegerse de una caída en el precio del subyacente.
    3. **⚖️ Cono Comprado (Long Straddle)**: Aprovechar la alta volatilidad, comprando una call y una put con el mismo strike y vencimiento.
    4. **🔒 Cono Vendido (Short Straddle)**: Beneficiarse de baja volatilidad, vendiendo una call y una put con el mismo strike y vencimiento.
    5. **🛡️ Collar**: Proteger una posición larga en acciones, vendiendo una call y comprando una put.
    6. **📈 Bull Call Spread**: Beneficiarse de un movimiento alcista limitado, comprando una call y vendiendo otra con strike más alto.
    7. **📉 Bear Put Spread**: Beneficiarse de un movimiento bajista limitado, comprando una put y vendiendo otra con strike más bajo.
    8. **🦋 Mariposa (Butterfly Spread)**: Beneficiarse de baja volatilidad o cuando se espera que el precio se mantenga en un rango estrecho.

    Cada estrategia tiene un nivel de riesgo y recompensa. La clave es seleccionar la adecuada en función de la volatilidad implícita y la tendencia del mercado.
    """)

    # Crecimiento de ingresos y beneficios
    st.subheader(f"💰 Ganancias por acción anuales para {stock}")
    eps_data = get_eps_data(stock, stock.lower())
    if eps_data is not None:
        st.dataframe(eps_data)
        
        # Crear la gráfica con Plotly
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=eps_data['Date'],
            y=eps_data['EPS (Earnings Per Share)'],
            mode='lines+markers',
            name='EPS'
        ))
        
        fig.update_layout(
            title=f'📅 Ganancias por Acción (EPS) Anuales para {stock}',
            xaxis_title='Fecha',
            yaxis_title='EPS (Earnings Per Share)',
            xaxis=dict(
                rangeslider=dict(visible=True),
                type='date'
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)

# Feedback
    st.subheader("📝 ¡Queremos escuchar tu opinión!")
    st.markdown("¿Qué más te gustaría ver en este proyecto? ¿Te interesaría un proyecto de opciones más complejo? ¡Tu feedback es muy importante para nosotros!")

    feedback = st.text_area("✍️ Deja tu comentario aquí:")
    email = st.text_input("📧 Deja tu email para que te contactemos (opcional)")

    if st.button("📨 Enviar Feedback"):
        if feedback:
            sheet_name = "StreamlitSuscriber"
            
            if email:
                if save_feedback(email, feedback, sheet_name):
                    st.success(f"🎉 ¡Gracias por tu feedback, {email}! Tu opinión es muy valiosa para nosotros.")
                else:
                    st.error("Hubo un problema al guardar tu feedback. Por favor, intenta de nuevo.")
            else:
                if save_feedback("", feedback, sheet_name):
                    st.success("🎉 ¡Gracias por tu feedback! Valoramos tu opinión.")
                else:
                    st.error("Hubo un problema al guardar tu feedback. Por favor, intenta de nuevo.")
        else:
            st.error("⚠️ Por favor, ingresa tu feedback.")



if __name__ == "__main__":
    main()
