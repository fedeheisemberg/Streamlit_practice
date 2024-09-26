import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import seaborn as sns
import matplotlib.pyplot as plt
from subscription_manager import save_feedback

# Configuración de la página con favicon
st.set_page_config(page_title="Dashboard OptionsPro", layout="wide", page_icon="options_dashboard/favicon.ico")

# Función para determinar el modo (oscuro o claro)
# def get_theme():
#    return st.get_option("theme.base")

# Cargar logo basado en el tema
#if get_theme() == "light":
#    st.image("options_dashboard/logo2.png")
#else:
 #   st.image("options_dashboard/logo1.png")

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

def display_improved_options_strategy(ticker, precio_actual):
    st.subheader("💡 Estrategia de Opciones Mejorada")
    
    # Selección de estrategia
    estrategia = st.selectbox("Elige la Estrategia", [
        "Cono Comprado (Long Straddle)",
        "Cono Vendido (Short Straddle)",
        "Collar",
        "Bull Call Spread",
        "Bear Put Spread",
        "Mariposa (Butterfly Spread)"
    ])
    
    # Selección de vencimiento
    vencimientos = ticker.options
    vencimiento = st.selectbox("📅 Seleccionar Fecha de Vencimiento", vencimientos)
    
    # Obtener opciones para el vencimiento seleccionado
    opciones = ticker.option_chain(vencimiento)
    
    if estrategia == "Cono Comprado (Long Straddle)":
        implementar_cono_comprado(opciones, precio_actual)
    elif estrategia == "Cono Vendido (Short Straddle)":
        implementar_cono_vendido(opciones, precio_actual)
    elif estrategia == "Collar":
        implementar_collar(opciones, precio_actual)
    elif estrategia == "Bull Call Spread":
        implementar_bull_call_spread(opciones, precio_actual)
    elif estrategia == "Bear Put Spread":
        implementar_bear_put_spread(opciones, precio_actual)
    elif estrategia == "Mariposa (Butterfly Spread)":
        implementar_mariposa(opciones, precio_actual)

def implementar_cono_comprado(opciones, precio_actual):
    st.write("### Cono Comprado (Long Straddle)")
    
    # Seleccionar opciones cerca del dinero
    call_atm = opciones.calls[opciones.calls['inTheMoney'] == False].iloc[0]
    put_atm = opciones.puts[opciones.puts['inTheMoney'] == False].iloc[-1]
    
    # Permitir al usuario ajustar la cantidad
    cantidad = st.number_input("Cantidad de conos", min_value=1, value=1, step=1)
    
    # Calcular costos y ganancias/pérdidas
    costo_total = (call_atm['lastPrice'] + put_atm['lastPrice']) * 100 * cantidad
    ganancia_maxima = float('inf')  # Teóricamente ilimitada para el lado alcista
    perdida_maxima = costo_total
    
    # Mostrar resumen
    st.write(f"Precio de ejercicio: ${call_atm['strike']:.2f}")
    st.write(f"Prima Call: ${call_atm['lastPrice']:.2f}")
    st.write(f"Prima Put: ${put_atm['lastPrice']:.2f}")
    st.write(f"Costo total: ${costo_total:.2f}")
    st.write(f"Ganancia máxima: Ilimitada")
    st.write(f"Pérdida máxima: ${perdida_maxima:.2f}")
    
    # Graficar perfil de ganancias/pérdidas
    strikes = pd.concat([opciones.calls['strike'], opciones.puts['strike']]).unique()
    strikes.sort()
    ganancias = [cantidad * (max(0, strike - call_atm['strike']) + max(0, put_atm['strike'] - strike) - (call_atm['lastPrice'] + put_atm['lastPrice'])) * 100 for strike in strikes]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=strikes, y=ganancias, mode='lines', name='Ganancia/Pérdida'))
    fig.add_hline(y=0, line_dash="dash", line_color="red")
    fig.add_vline(x=precio_actual, line_dash="dash", line_color="green", annotation_text="Precio Actual")
    fig.update_layout(title='Perfil de Ganancia/Pérdida del Cono Comprado', xaxis_title='Precio del Subyacente', yaxis_title='Ganancia/Pérdida ($)')
    st.plotly_chart(fig)

def implementar_cono_vendido(opciones, precio_actual):
    st.write("### Cono Vendido (Short Straddle)")
    
    call_atm = opciones.calls[opciones.calls['inTheMoney'] == False].iloc[0]
    put_atm = opciones.puts[opciones.puts['inTheMoney'] == False].iloc[-1]
    
    cantidad = st.number_input("Cantidad de conos vendidos", min_value=1, value=1, step=1)
    
    ingreso_total = (call_atm['lastPrice'] + put_atm['lastPrice']) * 100 * cantidad
    ganancia_maxima = ingreso_total
    perdida_maxima = float('inf')  # Teóricamente ilimitada
    
    st.write(f"Precio de ejercicio: ${call_atm['strike']:.2f}")
    st.write(f"Prima Call: ${call_atm['lastPrice']:.2f}")
    st.write(f"Prima Put: ${put_atm['lastPrice']:.2f}")
    st.write(f"Ingreso total: ${ingreso_total:.2f}")
    st.write(f"Ganancia máxima: ${ganancia_maxima:.2f}")
    st.write(f"Pérdida máxima: Ilimitada")
    
    strikes = pd.concat([opciones.calls['strike'], opciones.puts['strike']]).unique()
    strikes.sort()
    ganancias = [cantidad * ((call_atm['lastPrice'] + put_atm['lastPrice']) - max(0, strike - call_atm['strike']) - max(0, put_atm['strike'] - strike)) * 100 for strike in strikes]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=strikes, y=ganancias, mode='lines', name='Ganancia/Pérdida'))
    fig.add_hline(y=0, line_dash="dash", line_color="red")
    fig.add_vline(x=precio_actual, line_dash="dash", line_color="green", annotation_text="Precio Actual")
    fig.update_layout(title='Perfil de Ganancia/Pérdida del Cono Vendido', xaxis_title='Precio del Subyacente', yaxis_title='Ganancia/Pérdida ($)')
    st.plotly_chart(fig)

def implementar_collar(opciones, precio_actual):
    st.write("### Collar")
    
    cantidad_acciones = st.number_input("Cantidad de acciones", min_value=100, value=100, step=100)
    
    call_otm = opciones.calls[opciones.calls['strike'] > precio_actual].iloc[0]
    put_otm = opciones.puts[opciones.puts['strike'] < precio_actual].iloc[-1]
    
    costo_collar = call_otm['lastPrice'] - put_otm['lastPrice']
    costo_total = costo_collar * cantidad_acciones
    ganancia_maxima = (call_otm['strike'] - precio_actual) * cantidad_acciones - costo_total
    perdida_maxima = (precio_actual - put_otm['strike']) * cantidad_acciones + costo_total
    
    st.write(f"Precio actual: ${precio_actual:.2f}")
    st.write(f"Precio de ejercicio Call (venta): ${call_otm['strike']:.2f}")
    st.write(f"Precio de ejercicio Put (compra): ${put_otm['strike']:.2f}")
    st.write(f"Prima Call: ${call_otm['lastPrice']:.2f}")
    st.write(f"Prima Put: ${put_otm['lastPrice']:.2f}")
    st.write(f"Costo/Ingreso neto del collar: ${costo_total:.2f}")
    st.write(f"Ganancia máxima: ${ganancia_maxima:.2f}")
    st.write(f"Pérdida máxima: ${perdida_maxima:.2f}")
    
    strikes = pd.concat([opciones.calls['strike'], opciones.puts['strike']]).unique()
    strikes.sort()
    ganancias = [(min(call_otm['strike'], max(put_otm['strike'], strike)) - precio_actual) * cantidad_acciones - costo_total for strike in strikes]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=strikes, y=ganancias, mode='lines', name='Ganancia/Pérdida'))
    fig.add_hline(y=0, line_dash="dash", line_color="red")
    fig.add_vline(x=precio_actual, line_dash="dash", line_color="green", annotation_text="Precio Actual")
    fig.update_layout(title='Perfil de Ganancia/Pérdida del Collar', xaxis_title='Precio del Subyacente', yaxis_title='Ganancia/Pérdida ($)')
    st.plotly_chart(fig)

def implementar_bull_call_spread(opciones, precio_actual):
    st.write("### Bull Call Spread")
    
    call_buy = opciones.calls[opciones.calls['strike'] >= precio_actual].iloc[0]
    call_sell = opciones.calls[opciones.calls['strike'] > call_buy['strike']].iloc[0]
    
    cantidad = st.number_input("Cantidad de spreads", min_value=1, value=1, step=1)
    
    costo_spread = call_buy['lastPrice'] - call_sell['lastPrice']
    costo_total = costo_spread * 100 * cantidad
    ganancia_maxima = (call_sell['strike'] - call_buy['strike'] - costo_spread) * 100 * cantidad
    perdida_maxima = costo_total
    
    st.write(f"Precio de ejercicio Call (compra): ${call_buy['strike']:.2f}")
    st.write(f"Precio de ejercicio Call (venta): ${call_sell['strike']:.2f}")
    st.write(f"Prima Call (compra): ${call_buy['lastPrice']:.2f}")
    st.write(f"Prima Call (venta): ${call_sell['lastPrice']:.2f}")
    st.write(f"Costo total del spread: ${costo_total:.2f}")
    st.write(f"Ganancia máxima: ${ganancia_maxima:.2f}")
    st.write(f"Pérdida máxima: ${perdida_maxima:.2f}")
    
    strikes = pd.concat([opciones.calls['strike'], opciones.puts['strike']]).unique()
    strikes.sort()
    ganancias = [cantidad * (min(call_sell['strike'], max(call_buy['strike'], strike)) - call_buy['strike'] - costo_spread) * 100 for strike in strikes]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=strikes, y=ganancias, mode='lines', name='Ganancia/Pérdida'))
    fig.add_hline(y=0, line_dash="dash", line_color="red")
    fig.add_vline(x=precio_actual, line_dash="dash", line_color="green", annotation_text="Precio Actual")
    fig.update_layout(title='Perfil de Ganancia/Pérdida delBull Call Spread', xaxis_title='Precio del Subyacente', yaxis_title='Ganancia/Pérdida ($)')
    st.plotly_chart(fig)

def implementar_bear_put_spread(opciones, precio_actual):
    st.write("### Bear Put Spread")
    
    put_buy = opciones.puts[opciones.puts['strike'] <= precio_actual].iloc[-1]
    put_sell = opciones.puts[opciones.puts['strike'] < put_buy['strike']].iloc[-1]
    
    cantidad = st.number_input("Cantidad de spreads", min_value=1, value=1, step=1)
    
    costo_spread = put_buy['lastPrice'] - put_sell['lastPrice']
    costo_total = costo_spread * 100 * cantidad
    ganancia_maxima = (put_buy['strike'] - put_sell['strike'] - costo_spread) * 100 * cantidad
    perdida_maxima = costo_total
    
    st.write(f"Precio de ejercicio Put (compra): ${put_buy['strike']:.2f}")
    st.write(f"Precio de ejercicio Put (venta): ${put_sell['strike']:.2f}")
    st.write(f"Prima Put (compra): ${put_buy['lastPrice']:.2f}")
    st.write(f"Prima Put (venta): ${put_sell['lastPrice']:.2f}")
    st.write(f"Costo total del spread: ${costo_total:.2f}")
    st.write(f"Ganancia máxima: ${ganancia_maxima:.2f}")
    st.write(f"Pérdida máxima: ${perdida_maxima:.2f}")
    
    strikes = pd.concat([opciones.calls['strike'], opciones.puts['strike']]).unique()
    strikes.sort()
    ganancias = [cantidad * (put_buy['strike'] - max(put_sell['strike'], min(put_buy['strike'], strike)) - costo_spread) * 100 for strike in strikes]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=strikes, y=ganancias, mode='lines', name='Ganancia/Pérdida'))
    fig.add_hline(y=0, line_dash="dash", line_color="red")
    fig.add_vline(x=precio_actual, line_dash="dash", line_color="green", annotation_text="Precio Actual")
    fig.update_layout(title='Perfil de Ganancia/Pérdida del Bear Put Spread', xaxis_title='Precio del Subyacente', yaxis_title='Ganancia/Pérdida ($)')
    st.plotly_chart(fig)

def implementar_mariposa(opciones, precio_actual):
    st.write("### Mariposa (Butterfly Spread)")
    
    call_buy_low = opciones.calls[opciones.calls['strike'] <= precio_actual].iloc[-1]
    call_sell_mid = opciones.calls[opciones.calls['strike'] > call_buy_low['strike']].iloc[0]
    call_buy_high = opciones.calls[opciones.calls['strike'] > call_sell_mid['strike']].iloc[0]
    
    cantidad = st.number_input("Cantidad de mariposas", min_value=1, value=1, step=1)
    
    costo_mariposa = call_buy_low['lastPrice'] - 2 * call_sell_mid['lastPrice'] + call_buy_high['lastPrice']
    costo_total = costo_mariposa * 100 * cantidad
    ganancia_maxima = (call_sell_mid['strike'] - call_buy_low['strike'] - costo_mariposa) * 100 * cantidad
    perdida_maxima = costo_total
    
    st.write(f"Precio de ejercicio Call (compra bajo): ${call_buy_low['strike']:.2f}")
    st.write(f"Precio de ejercicio Call (venta medio): ${call_sell_mid['strike']:.2f}")
    st.write(f"Precio de ejercicio Call (compra alto): ${call_buy_high['strike']:.2f}")
    st.write(f"Prima Call (compra bajo): ${call_buy_low['lastPrice']:.2f}")
    st.write(f"Prima Call (venta medio): ${call_sell_mid['lastPrice']:.2f}")
    st.write(f"Prima Call (compra alto): ${call_buy_high['lastPrice']:.2f}")
    st.write(f"Costo total de la mariposa: ${costo_total:.2f}")
    st.write(f"Ganancia máxima: ${ganancia_maxima:.2f}")
    st.write(f"Pérdida máxima: ${perdida_maxima:.2f}")
    
    strikes = pd.concat([opciones.calls['strike'], opciones.puts['strike']]).unique()
    strikes.sort()
    ganancias = [cantidad * (max(0, strike - call_buy_low['strike']) - 2 * max(0, strike - call_sell_mid['strike']) + max(0, strike - call_buy_high['strike']) - costo_mariposa) * 100 for strike in strikes]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=strikes, y=ganancias, mode='lines', name='Ganancia/Pérdida'))
    fig.add_hline(y=0, line_dash="dash", line_color="red")
    fig.add_vline(x=precio_actual, line_dash="dash", line_color="green", annotation_text="Precio Actual")
    fig.update_layout(title='Perfil de Ganancia/Pérdida de la Mariposa', xaxis_title='Precio del Subyacente', yaxis_title='Ganancia/Pérdida ($)')
    st.plotly_chart(fig)

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

    # Obtener y manejar posibles errores en los datos del precio actual
    try:
        data = ticker.history(period="1d")
        if not data.empty:
            precio_actual = data['Close'].iloc[-1]
            st.write(f"Precio actual de {stock}: ${precio_actual:.2f}")
        else:
            st.error("No hay datos disponibles para este ticker o período.")
    except Exception as e:
        st.error(f"Error al obtener los datos: {e}")

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

    # Opciones mejoradas
    display_improved_options_strategy(ticker, precio_actual)

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
    st.subheader("📝 ¡Queremos saber tu opinión!")
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
    
    # Footer usando markdown de Streamlit
    st.markdown("---")
    st.markdown("© 2024 Optima Consulting & Management LLC | [LinkedIn](https://www.linkedin.com/company/optima-consulting-managament-llc) | [Capacitaciones](https://www.optimalearning.site/) | [Página Web](https://www.optimafinancials.com/)" )

if __name__ == "__main__":
    main()