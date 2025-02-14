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
from subscription_manager import save_feedback
import numpy as np
import matplotlib.pyplot as plt

@st.cache_data
def get_cached_option_data(_ticker, expiration):
    return get_option_data(_ticker, expiration)


def get_option_data(_ticker, expiration):
    try:
        option_chain = _ticker.option_chain(expiration)
        if 'impliedVolatility' not in option_chain.calls.columns or 'impliedVolatility' not in option_chain.puts.columns:
            st.warning("Los datos de volatilidad implícita no están disponibles. Algunas gráficas pueden no mostrarse.")
        return option_chain
    except Exception as e:
        st.error(f"Error al obtener datos de opciones: {e}")
        return None

def calculate_macd(data, fast=12, slow=26, signal=9):
    exp1 = data['Close'].ewm(span=fast, adjust=False).mean()
    exp2 = data['Close'].ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line
    return macd, signal_line, histogram

def plot_candlestick_chart(prices):
    fig = go.Figure(data=[go.Candlestick(x=prices.index,
                open=prices['Open'],
                high=prices['High'],
                low=prices['Low'],
                close=prices['Close'])])
    fig.update_layout(xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

def get_eps_data(ticker, company):
    url = f"https://www.macrotrends.net/stocks/charts/{ticker}/{company}/eps-earnings-per-share-diluted"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', class_='historical_data_table')
        if not table:
            return None
        
        dates, eps_values = [], []
        for row in table.find_all('tr')[1:]:
            columns = row.find_all('td')
            dates.append(columns[0].get_text(strip=True))
            eps_values.append(columns[1].get_text(strip=True))
        
        df = pd.DataFrame({'Fecha': dates, 'BPA (Beneficio Por Acción)': eps_values})
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        return df
    except requests.RequestException as e:
        st.error(f"Error al obtener datos de BPA: {e}")
        return None

def implement_long_straddle(options, current_price):
    st.write("### Cono Largo (Long Straddle)")
    
    call_atm = options.calls[options.calls['inTheMoney'] == False].iloc[0]
    put_atm = options.puts[options.puts['inTheMoney'] == False].iloc[-1]
    
    quantity = st.number_input("Cantidad de conos", min_value=1, value=1, step=1)
    
    total_cost = (call_atm['lastPrice'] + put_atm['lastPrice']) * 100 * quantity
    max_profit = float('inf')
    max_loss = total_cost
    
    st.write(f"Precio de ejercicio Call (compra): ${call_atm['strike']:.2f}")
    st.write(f"Precio de ejercicio Put (compra): ${put_atm['strike']:.2f}")
    st.write(f"Prima Call: ${call_atm['lastPrice']:.2f}")
    st.write(f"Prima Put: ${put_atm['lastPrice']:.2f}")
    st.write(f"Costo total del cono: ${total_cost:.2f}")
    st.write(f"Ganancia máxima: Ilimitada")
    st.write(f"Pérdida máxima: ${max_loss:.2f}")
    
    plot_profit_loss_profile(options, current_price, lambda strike: quantity * (max(0, strike - call_atm['strike']) + max(0, put_atm['strike'] - strike) - (call_atm['lastPrice'] + put_atm['lastPrice'])) * 100, "Cono Largo")

def implement_short_straddle(options, current_price):
    st.write("### Cono Corto (Short Straddle)")
    
    call_atm = options.calls[options.calls['inTheMoney'] == False].iloc[0]
    put_atm = options.puts[options.puts['inTheMoney'] == False].iloc[-1]
    
    quantity = st.number_input("Cantidad de conos cortos", min_value=1, value=1, step=1)
    
    total_income = (call_atm['lastPrice'] + put_atm['lastPrice']) * 100 * quantity
    max_profit = total_income
    max_loss = float('inf')
    
    st.write(f"Precio de ejercicio Call (venta): ${call_atm['strike']:.2f}")
    st.write(f"Precio de ejercicio Put (venta): ${put_atm['strike']:.2f}")
    st.write(f"Prima Call: ${call_atm['lastPrice']:.2f}")
    st.write(f"Prima Put: ${put_atm['lastPrice']:.2f}")
    st.write(f"Ingreso total del cono: ${total_income:.2f}")
    st.write(f"Ganancia máxima: ${max_profit:.2f}")
    st.write(f"Pérdida máxima: Ilimitada")
    
    st.warning("⚠️ Advertencia: Esta estrategia implica un riesgo de pérdida ilimitada.")
    
    plot_profit_loss_profile(options, current_price, lambda strike: quantity * ((call_atm['lastPrice'] + put_atm['lastPrice']) - max(0, strike - call_atm['strike']) - max(0, put_atm['strike'] - strike)) * 100, "Cono Corto")

def implement_collar(options, current_price):
    st.write("### Collar")
    
    shares = st.number_input("Cantidad de acciones", min_value=100, value=100, step=100)
    
    call_otm = options.calls[options.calls['strike'] > current_price].iloc[0]
    put_otm = options.puts[options.puts['strike'] < current_price].iloc[-1]
    
    collar_cost = call_otm['lastPrice'] - put_otm['lastPrice']
    total_cost = collar_cost * shares
    max_profit = (call_otm['strike'] - current_price) * shares - total_cost
    max_loss = (current_price - put_otm['strike']) * shares + total_cost
    
    st.write(f"Precio actual: ${current_price:.2f}")
    st.write(f"Precio de ejercicio Call (venta): ${call_otm['strike']:.2f}")
    st.write(f"Precio de ejercicio Put (compra): ${put_otm['strike']:.2f}")
    st.write(f"Prima Call: ${call_otm['lastPrice']:.2f}")
    st.write(f"Prima Put: ${put_otm['lastPrice']:.2f}")
    st.write(f"Costo/Ingreso neto del collar: ${total_cost:.2f}")
    st.write(f"Ganancia máxima: ${max_profit:.2f}")
    st.write(f"Pérdida máxima: ${max_loss:.2f}")
    
    st.info("ℹ️ El Collar limita tanto las ganancias como las pérdidas potenciales.")
    
    plot_profit_loss_profile(options, current_price, lambda strike: (min(call_otm['strike'], max(put_otm['strike'], strike)) - current_price) * shares - total_cost, "Collar")

def implement_bull_call_spread(options, current_price):
    st.write("### Spread Alcista de Calls (Bull Call Spread)")
    
    call_buy = options.calls[options.calls['strike'] >= current_price].iloc[0]
    call_sell = options.calls[options.calls['strike'] > call_buy['strike']].iloc[0]
    
    quantity = st.number_input("Cantidad de spreads", min_value=1, value=1, step=1)
    
    spread_cost = call_buy['lastPrice'] - call_sell['lastPrice']
    total_cost = spread_cost * 100 * quantity
    max_profit = (call_sell['strike'] - call_buy['strike'] - spread_cost) * 100 * quantity
    max_loss = total_cost
    
    st.write(f"Precio de ejercicio Call (compra): ${call_buy['strike']:.2f}")
    st.write(f"Precio de ejercicio Call (venta): ${call_sell['strike']:.2f}")
    st.write(f"Prima Call (compra): ${call_buy['lastPrice']:.2f}")
    st.write(f"Prima Call (venta): ${call_sell['lastPrice']:.2f}")
    st.write(f"Costo total del spread: ${total_cost:.2f}")
    st.write(f"Ganancia máxima: ${max_profit:.2f}")
    st.write(f"Pérdida máxima: ${max_loss:.2f}")
    
    st.info("ℹ️ El Spread Alcista de Calls es una estrategia con riesgo limitado que se beneficia de un aumento moderado en el precio del activo subyacente.")
    
    plot_profit_loss_profile(options, current_price, lambda strike: quantity * (min(call_sell['strike'], max(call_buy['strike'], strike)) - call_buy['strike'] - spread_cost) * 100, "Spread Alcista de Calls")

def implement_bear_put_spread(options, current_price):
    st.write("### Spread Bajista de Puts (Bear Put Spread)")
    
    put_buy = options.puts[options.puts['strike'] <= current_price].iloc[-1]
    put_sell = options.puts[options.puts['strike'] < put_buy['strike']].iloc[-1]
    
    quantity = st.number_input("Cantidad de spreads", min_value=1, value=1, step=1)
    
    spread_cost = put_buy['lastPrice'] - put_sell['lastPrice']
    total_cost = spread_cost * 100 * quantity
    max_profit = (put_buy['strike'] - put_sell['strike'] - spread_cost) * 100 * quantity
    max_loss = total_cost
    
    st.write(f"Precio de ejercicio Put (compra): ${put_buy['strike']:.2f}")
    st.write(f"Precio de ejercicio Put (venta): ${put_sell['strike']:.2f}")
    st.write(f"Prima Put (compra): ${put_buy['lastPrice']:.2f}")
    st.write(f"Prima Put (venta): ${put_sell['lastPrice']:.2f}")
    st.write(f"Costo total del spread: ${total_cost:.2f}")
    st.write(f"Ganancia máxima: ${max_profit:.2f}")
    st.write(f"Pérdida máxima: ${max_loss:.2f}")
    
    st.info("ℹ️ El Spread Bajista de Puts es una estrategia con riesgo limitado que se beneficia de una disminución moderada en el precio del activo subyacente.")
    
    plot_profit_loss_profile(options, current_price, lambda strike: quantity * (put_buy['strike'] - max(put_sell['strike'], min(put_buy['strike'], strike)) - spread_cost) * 100, "Spread Bajista de Puts")

def implement_long_butterfly(options, current_price):
    st.write("### Mariposa Larga (Long Butterfly)")
    
    call_atm = options.calls[options.calls['inTheMoney'] == False].iloc[0]
    call_otm = options.calls[options.calls['strike'] > call_atm['strike']].iloc[0]
    call_itm = options.calls[options.calls['strike'] < call_atm['strike']].iloc[-1]
    
    quantity = st.number_input("Cantidad de mariposas", min_value=1, value=1, step=1)
    
    butterfly_cost = call_itm['lastPrice'] + call_otm['lastPrice'] - 2 * call_atm['lastPrice']
    total_cost = butterfly_cost * 100 * quantity
    max_profit = (call_atm['strike'] - call_itm['strike'] - butterfly_cost) * 100 * quantity
    max_loss = total_cost
    
    st.write(f"Precio de ejercicio Call (ITM): ${call_itm['strike']:.2f}")
    st.write(f"Precio de ejercicio Call (ATM): ${call_atm['strike']:.2f}")
    st.write(f"Precio de ejercicio Call (OTM): ${call_otm['strike']:.2f}")
    st.write(f"Prima Call (ITM): ${call_itm['lastPrice']:.2f}")
    st.write(f"Prima Call (ATM): ${call_atm['lastPrice']:.2f}")
    st.write(f"Prima Call (OTM): ${call_otm['lastPrice']:.2f}")
    st.write(f"Costo total de la mariposa: ${total_cost:.2f}")
    st.write(f"Ganancia máxima: ${max_profit:.2f}")
    st.write(f"Pérdida máxima: ${max_loss:.2f}")
    
    st.info("ℹ️ La Mariposa Larga es una estrategia de volatilidad neutral que se beneficia cuando el precio del activo subyacente permanece cerca del precio de ejercicio central al vencimiento.")
    
    plot_profit_loss_profile(options, current_price, lambda strike: quantity * (max(0, strike - call_itm['strike']) + max(0, call_otm['strike'] - strike) - 2 * max(0, strike - call_atm['strike']) - butterfly_cost) * 100, "Mariposa Larga")

def implement_short_butterfly(options, current_price):
    st.write("### Mariposa Corta (Short Butterfly)")
    
    call_atm = options.calls[options.calls['inTheMoney'] == False].iloc[0]
    call_otm = options.calls[options.calls['strike'] > call_atm['strike']].iloc[0]
    call_itm = options.calls[options.calls['strike'] < call_atm['strike']].iloc[-1]
    
    quantity = st.number_input("Cantidad de mariposas cortas", min_value=1, value=1, step=1)
    
    butterfly_credit = (2 * call_atm['lastPrice'] - call_itm['lastPrice'] - call_otm['lastPrice']) * 100 * quantity
    max_profit = butterfly_credit
    max_loss = ((call_atm['strike'] - call_itm['strike']) * 100 - butterfly_credit) * quantity
    
    st.write(f"Precio de ejercicio Call (ITM): ${call_itm['strike']:.2f}")
    st.write(f"Precio de ejercicio Call (ATM): ${call_atm['strike']:.2f}")
    st.write(f"Precio de ejercicio Call (OTM): ${call_otm['strike']:.2f}")
    st.write(f"Prima Call (ITM): ${call_itm['lastPrice']:.2f}")
    st.write(f"Prima Call (ATM): ${call_atm['lastPrice']:.2f}")
    st.write(f"Prima Call (OTM): ${call_otm['lastPrice']:.2f}")
    st.write(f"Crédito total de la mariposa: ${butterfly_credit:.2f}")
    st.write(f"Ganancia máxima: ${max_profit:.2f}")
    st.write(f"Pérdida máxima: ${max_loss:.2f}")
    
    st.info("ℹ️ La Mariposa Corta es una estrategia de volatilidad neutral que se beneficia cuando el precio del activo subyacente se mueve significativamente en cualquier dirección antes del vencimiento.")
    
    plot_profit_loss_profile(options, current_price, lambda strike: quantity * (2 * max(0, strike - call_atm['strike']) - max(0, strike - call_itm['strike']) - max(0, strike - call_otm['strike']) + butterfly_credit / 100), "Mariposa Corta")

def implement_neutral_butterfly(options, current_price):
    st.write("### Mariposa Neutral (Neutral Butterfly)")
    
    call_atm = options.calls[options.calls['inTheMoney'] == False].iloc[0]
    call_otm = options.calls[options.calls['strike'] > call_atm['strike']].iloc[0]
    put_atm = options.puts[options.puts['inTheMoney'] == False].iloc[-1]
    put_otm = options.puts[options.puts['strike'] < put_atm['strike']].iloc[-1]
    
    quantity = st.number_input("Cantidad de mariposas neutrales", min_value=1, value=1, step=1)
    
    butterfly_cost = (call_otm['lastPrice'] + put_otm['lastPrice'] - call_atm['lastPrice'] - put_atm['lastPrice']) * 100 * quantity
    max_profit = ((call_otm['strike'] - call_atm['strike']) * 100 - butterfly_cost) * quantity
    max_loss = butterfly_cost
    
    st.write(f"Precio de ejercicio Put (OTM): ${put_otm['strike']:.2f}")
    st.write(f"Precio de ejercicio Put/Call (ATM): ${call_atm['strike']:.2f}")
    st.write(f"Precio de ejercicio Call (OTM): ${call_otm['strike']:.2f}")
    st.write(f"Prima Put (OTM): ${put_otm['lastPrice']:.2f}")
    st.write(f"Prima Put (ATM): ${put_atm['lastPrice']:.2f}")
    st.write(f"Prima Call (ATM): ${call_atm['lastPrice']:.2f}")
    st.write(f"Prima Call (OTM): ${call_otm['lastPrice']:.2f}")
    st.write(f"Costo total de la mariposa neutral: ${butterfly_cost:.2f}")
    st.write(f"Ganancia máxima: ${max_profit:.2f}")
    st.write(f"Pérdida máxima: ${max_loss:.2f}")
    
    st.info("ℹ️ La Mariposa Neutral es una estrategia de volatilidad neutral que se beneficia cuando el precio del activo subyacente permanece cerca del precio de ejercicio central al vencimiento, pero ofrece una mayor flexibilidad que la mariposa tradicional.")

    # En implement_neutral_butterfly:
    plot_profit_loss_profile(options, current_price, lambda strike: quantity * (max(0, strike - put_otm['strike']) + max(0, call_otm['strike'] - strike) - max(0, strike - call_atm['strike']) - max(0, put_atm['strike'] - strike) - butterfly_cost / 100), "Mariposa Neutral")


def implement_iron_condor(options, current_price):
    st.write("### Cóndor de Hierro (Iron Condor)")
    
    call_otm = options.calls[options.calls['strike'] > current_price].iloc[0]
    call_far_otm = options.calls[options.calls['strike'] > call_otm['strike']].iloc[0]
    put_otm = options.puts[options.puts['strike'] < current_price].iloc[-1]
    put_far_otm = options.puts[options.puts['strike'] < put_otm['strike']].iloc[-1]
    
    quantity = st.number_input("Cantidad de cóndores de hierro", min_value=1, value=1, step=1)
    
    condor_credit = (call_otm['lastPrice'] - call_far_otm['lastPrice'] + put_otm['lastPrice'] - put_far_otm['lastPrice']) * 100 * quantity
    max_profit = condor_credit
    max_loss = ((call_far_otm['strike'] - call_otm['strike']) * 100 - condor_credit) * quantity
    
    st.write(f"Precio de ejercicio Put (lejano OTM): ${put_far_otm['strike']:.2f}")
    st.write(f"Precio de ejercicio Put (OTM): ${put_otm['strike']:.2f}")
    st.write(f"Precio de ejercicio Call (OTM): ${call_otm['strike']:.2f}")
    st.write(f"Precio de ejercicio Call (lejano OTM): ${call_far_otm['strike']:.2f}")
    st.write(f"Prima Put (lejano OTM): ${put_far_otm['lastPrice']:.2f}")
    st.write(f"Prima Put (OTM): ${put_otm['lastPrice']:.2f}")
    st.write(f"Prima Call (OTM): ${call_otm['lastPrice']:.2f}")
    st.write(f"Prima Call (lejano OTM): ${call_far_otm['lastPrice']:.2f}")
    st.write(f"Crédito total del cóndor: ${condor_credit:.2f}")
    st.write(f"Ganancia máxima: ${max_profit:.2f}")
    st.write(f"Pérdida máxima: ${max_loss:.2f}")
    
    st.info("ℹ️ El Cóndor de Hierro es una estrategia de volatilidad neutral que se beneficia cuando el precio del activo subyacente permanece dentro de un rango específico al vencimiento.")
    
    plot_profit_loss_profile(options, current_price, lambda strike: quantity * (min(call_otm['strike'], max(put_otm['strike'], strike)) - current_price + condor_credit / 100), "Cóndor de Hierro")

def plot_probability_cone(ticker, current_price, selected_expiration, iv):
    days_to_expiration = (datetime.strptime(selected_expiration, '%Y-%m-%d') - datetime.now()).days
    
    # Convertimos volatilidad anual a diaria
    iv_daily = iv / np.sqrt(252)
    
    # Generamos fechas futuras
    future_dates = pd.date_range(start=datetime.now(), periods=days_to_expiration, freq='D')
    
    # Cálculo de intervalos de confianza
    std_devs = np.sqrt(np.arange(1, days_to_expiration + 1)) * iv_daily
    upper_68 = current_price * np.exp(std_devs)
    lower_68 = current_price * np.exp(-std_devs)
    upper_95 = current_price * np.exp(2 * std_devs)
    lower_95 = current_price * np.exp(-2 * std_devs)
    
    fig = go.Figure()
    
    # Añadir líneas para diferentes niveles de confianza
    fig.add_trace(go.Scatter(x=future_dates, y=upper_95, fill=None, mode='lines', 
                            line=dict(color='rgba(0,100,80,0.2)'), name='95% Intervalo'))
    fig.add_trace(go.Scatter(x=future_dates, y=lower_95, fill='tonexty', mode='lines', 
                            line=dict(color='rgba(0,100,80,0.2)'), name='95% Intervalo'))
    fig.add_trace(go.Scatter(x=future_dates, y=upper_68, fill=None, mode='lines', 
                            line=dict(color='rgba(0,100,80,0.4)'), name='68% Intervalo'))
    fig.add_trace(go.Scatter(x=future_dates, y=lower_68, fill='tonexty', mode='lines', 
                            line=dict(color='rgba(0,100,80,0.4)'), name='68% Intervalo'))
    
    # Línea del precio actual
    fig.add_trace(go.Scatter(x=[datetime.now(), future_dates[-1]], y=[current_price, current_price],
                            mode='lines', line=dict(color='red', dash='dash'), name='Precio Actual'))
    
    fig.update_layout(
        title='Cono de Probabilidades basado en Volatilidad Implícita',
        xaxis_title='Fecha',
        yaxis_title='Precio proyectado',
        legend_title='Intervalos de Confianza',
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)

def plot_price_distribution(current_price, iv, days_to_expiration):
    # Convertir volatilidad anual a la duración hasta el vencimiento
    vol_to_expiry = iv * np.sqrt(days_to_expiration / 252)
    
    # Generar rango de precios
    price_range = np.linspace(current_price * 0.5, current_price * 1.5, 1000)
    
    # Calcular PDF (función de densidad de probabilidad) log-normal
    pdf = (1 / (price_range * vol_to_expiry * np.sqrt(2 * np.pi))) * \
          np.exp(-((np.log(price_range / current_price) + vol_to_expiry**2 / 2)**2) / (2 * vol_to_expiry**2))
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=price_range, y=pdf, mode='lines', fill='tozeroy',
                             line=dict(color='blue'), name='Distribución de Probabilidad'))
    
    fig.add_vline(x=current_price, line_dash="dash", line_color="red", 
                   annotation_text="Precio actual")
    
    fig.update_layout(
        title='Distribución de Probabilidad del Precio al Vencimiento',
        xaxis_title='Precio',
        yaxis_title='Densidad de Probabilidad',
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_greeks(options, current_price):
    st.subheader("🧮 Análisis de Griegas")
    
    # Filtrar opciones cerca del precio actual (ATM)
    calls_atm = options.calls[np.abs(options.calls['strike'] - current_price).idxmin()]
    puts_atm = options.puts[np.abs(options.puts['strike'] - current_price).idxmin()]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Griegas - Call ATM")
        if 'delta' in calls_atm:
            st.write(f"**Delta**: {calls_atm.get('delta', 'N/A'):.4f}")
            st.write(f"**Gamma**: {calls_atm.get('gamma', 'N/A'):.4f}")
            st.write(f"**Theta**: {calls_atm.get('theta', 'N/A'):.4f}")
            st.write(f"**Vega**: {calls_atm.get('vega', 'N/A'):.4f}")
            st.write(f"**Rho**: {calls_atm.get('rho', 'N/A'):.4f}")
        else:
            st.warning("Datos de griegas no disponibles para Calls")
    
    with col2:
        st.subheader("Griegas - Put ATM")
        if 'delta' in puts_atm:
            st.write(f"**Delta**: {puts_atm.get('delta', 'N/A'):.4f}")
            st.write(f"**Gamma**: {puts_atm.get('gamma', 'N/A'):.4f}")
            st.write(f"**Theta**: {puts_atm.get('theta', 'N/A'):.4f}")
            st.write(f"**Vega**: {puts_atm.get('vega', 'N/A'):.4f}")
            st.write(f"**Rho**: {puts_atm.get('rho', 'N/A'):.4f}")
        else:
            st.warning("Datos de griegas no disponibles para Puts")

def plot_volatility_term_structure(ticker):
    expirations = ticker.options
    if len(expirations) <2:
        st.warning("No hay suficientes vencimientos para mostrar la estructura temporal de volatilidad.")
        return
    
    atm_ivs = []
    expiration_dates = []
    
    for expiration in expirations:
        option_chain = get_option_data(ticker, expiration)
        if option_chain is None or 'impliedVolatility' not in option_chain.calls.columns:
            continue
        
        # Obtener el precio actual
        current_price = ticker.history(period="1d")['Close'].iloc[-1]
        
        # Obtener la opción ATM
        calls_atm = option_chain.calls[np.abs(option_chain.calls['strike'] - current_price).idxmin()]
        
        if 'impliedVolatility' in calls_atm:
            atm_ivs.append(calls_atm['impliedVolatility'])
            expiration_dates.append(datetime.strptime(expiration, '%Y-%m-%d'))
    
    if len(atm_ivs) < 2:
        st.warning("No hay suficientes datos de volatilidad para mostrar la estructura temporal.")
        return
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=expiration_dates, y=atm_ivs, mode='lines+markers',
                             name='Volatilidad Implícita ATM'))
    
    fig.update_layout(
        title='Estructura Temporal de Volatilidad Implícita',
        xaxis_title='Fecha de Vencimiento',
        yaxis_title='Volatilidad Implícita ATM',
    )
    
    st.plotly_chart(fig, use_container_width=True)

def plot_profit_loss_profile(options, current_price, profit_loss_function, strategy_name):
    strikes = np.linspace(options.calls['strike'].min(), options.calls['strike'].max(), 100)
    profits = [profit_loss_function(strike) for strike in strikes]
    
    fig = go.Figure()
    
    # Línea principal de Ganancias/Pérdidas
    fig.add_trace(go.Scatter(
        x=strikes,
        y=profits,
        mode='lines',
        name='Perfil de Ganancias/Pérdidas'
    ))
    
    # Línea de punto de equilibrio
    fig.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Punto de equilibrio")
    
    # Línea de precio actual
    fig.add_vline(x=current_price, line_dash="dash", line_color="green", annotation_text="Precio actual")
    
    fig.update_layout(
        title=f'Perfil de Ganancias/Pérdidas - {strategy_name}',
        xaxis_title='Precio del activo subyacente',
        yaxis_title='Ganancias/Pérdidas ($)',
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Agregar tabla de teóricos
    st.subheader("📊 Tabla de Valores Teóricos")
    
    # Generar precios de interés alrededor del precio actual
    price_range = 0.10  # 10% arriba y abajo del precio actual
    price_points = np.linspace(current_price * (1 - price_range), current_price * (1 + price_range), 9)
    price_points = np.round(price_points, 2)
    
    # Calcular ganancias/pérdidas para cada punto de precio
    theoretical_data = []
    for price in price_points:
        profit = profit_loss_function(price)
        theoretical_data.append({
            "Precio": f"${price:.2f}",
            "Ganancia/Pérdida": f"${profit:.2f}",
            "% Cambio desde precio actual": f"{((price / current_price) - 1) * 100:.2f}%"
        })
    
    # Crear y mostrar DataFrame
    df_theoretical = pd.DataFrame(theoretical_data)
    st.dataframe(df_theoretical, use_container_width=True)

def display_options_strategy(ticker, current_price, selected_expiration):
    st.subheader("💡 Estrategia de Opciones")
    
    strategy = st.selectbox("Elegir Estrategia", [
        "Cono Largo",
        "Cono Corto",
        "Collar",
        "Spread Alcista de Calls",
        "Spread Bajista de Puts",
        "Mariposa Larga",
        "Mariposa Corta",
        "Mariposa Neutral",
        "Cóndor de Hierro"
    ], key="strategy_selector")
    
    options = ticker.option_chain(selected_expiration)
    
    strategy_functions = {
        "Cono Largo": implement_long_straddle,
        "Cono Corto": implement_short_straddle,
        "Collar": implement_collar,
        "Spread Alcista de Calls": implement_bull_call_spread,
        "Spread Bajista de Puts": implement_bear_put_spread,
        "Mariposa Larga": implement_long_butterfly,
        "Mariposa Corta": implement_short_butterfly,
        "Mariposa Neutral": implement_neutral_butterfly,
        "Cóndor de Hierro": implement_iron_condor
    }
    
    strategy_functions[strategy](options, current_price)

def monte_carlo_simulation(current_price, vol, days, num_simulations=1000):
    dt = 1/252
    sqrt_dt = np.sqrt(dt)
    
    # Matriz para almacenar todas las simulaciones
    simulations = np.zeros((days, num_simulations))
    simulations[0] = current_price
    
    for i in range(1, days):
        z = np.random.standard_normal(num_simulations)
        simulations[i] = simulations[i-1] * np.exp((0 - 0.5 * vol**2) * dt + vol * sqrt_dt * z)
    
    return simulations

def plot_monte_carlo(ticker, current_price, days_to_simulate=252):
    hist_data = ticker.history(period="1y")
    returns = np.log(hist_data['Close'] / hist_data['Close'].shift(1)).dropna()
    vol = returns.std() * np.sqrt(252)  # anualizar volatilidad
    
    simulations = monte_carlo_simulation(current_price, vol, days_to_simulate)
    
    fig = go.Figure()
    
    # Plotear algunas trayectorias individuales
    for i in range(min(100, simulations.shape[1])):
        fig.add_trace(go.Scatter(
            y=simulations[:, i],
            mode='lines',
            line=dict(width=0.5, color='rgba(70, 130, 180, 0.1)'),
            showlegend=False
        ))
    
    # Calcular y plotear los percentiles
    percentiles = np.percentile(simulations, [5, 50, 95], axis=1)
    
    fig.add_trace(go.Scatter(
        y=percentiles[1, :],
        mode='lines',
        line=dict(color='blue', width=2),
        name='Mediana'
    ))
    
    fig.add_trace(go.Scatter(
        y=percentiles[2, :],
        mode='lines',
        line=dict(color='red', width=1.5, dash='dash'),
        name='Percentil 95'
    ))
    
    fig.add_trace(go.Scatter(
        y=percentiles[0, :],
        mode='lines',
        line=dict(color='green', width=1.5, dash='dash'),
        name='Percentil 5'
    ))
    
    fig.update_layout(
        title='Simulación de Monte Carlo - Proyección de Precios (1 año)',
        xaxis_title='Días de Operación',
        yaxis_title='Precio Proyectado',
    )
    
    st.plotly_chart(fig, use_container_width=True)

def plot_correlation_with_market(ticker_symbol):
    benchmark = '^MERV'  # Usa MERVAL para acciones argentinas, o cambia a SPY/^GSPC para USA
    
    # Obtener datos
    ticker_data = yf.download(ticker_symbol, period="1y")['Adj Close']
    market_data = yf.download(benchmark, period="1y")['Adj Close']
    
    # Alinear los datos
    df = pd.DataFrame({'Ticker': ticker_data, 'Mercado': market_data})
    df = df.dropna()
    
    # Calcular retornos diarios
    returns = df.pct_change().dropna()
    
    # Calcular correlación
    correlation = returns['Ticker'].corr(returns['Mercado'])
    
    # Crear scatter plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=returns['Mercado'],
        y=returns['Ticker'],
        mode='markers',
        marker=dict(
            size=8,
            color='blue',
            opacity=0.6
        ),
        name='Retornos Diarios'
    ))
    
    # Línea de regresión
    slope, intercept = np.polyfit(returns['Mercado'], returns['Ticker'], 1)
    x_range = np.linspace(returns['Mercado'].min(), returns['Mercado'].max(), 100)
    y_fit = slope * x_range + intercept
    
    fig.add_trace(go.Scatter(
        x=x_range,
        y=y_fit,
        mode='lines',
        line=dict(color='red'),
        name=f'Beta = {slope:.2f}'
    ))
    
    fig.update_layout(
        title=f'Correlación con el Mercado (Beta = {slope:.2f}, Correlación = {correlation:.2f})',
        xaxis_title='Retorno del Mercado',
        yaxis_title=f'Retorno de {ticker_symbol}',
    )
    
    st.plotly_chart(fig, use_container_width=True)

def hedging_calculator(ticker, current_price, shares_owned):
    st.subheader("🛡️ Calculadora de Cobertura (Hedging)")
    
    st.write(f"Posición actual: {shares_owned} acciones a ${current_price:.2f} = ${shares_owned * current_price:.2f}")
    
    # Opciones disponibles
    expirations = ticker.options
    if not expirations:
        st.warning("No hay opciones disponibles para coberturas")
        return
    
    expiration = st.selectbox("Seleccionar vencimiento para cobertura", expirations, key="hedge_expiry")
    options = get_option_data(ticker, expiration)
    
    if options is None or 'puts' not in options.__dict__:
        st.warning("No se pudieron obtener datos de puts para la cobertura")
        return
    
    # Mostrar puts disponibles para cobertura
    st.dataframe(options.puts)
    
    # Selector de puts para cobertura
    selected_put_strike = st.number_input("Seleccionar precio de ejercicio del put para cobertura", 
                                         min_value=float(options.puts['strike'].min()),
                                         max_value=float(options.puts['strike'].max()),
                                         value=float(current_price * 0.9))
    
    # Encontrar el put más cercano al strike seleccionado
    put_index = np.abs(options.puts['strike'] - selected_put_strike).idxmin()
    selected_put = options.puts.iloc[put_index]
    
    # Calcular número de contratos necesarios
    contracts_needed = shares_owned / 100
    if contracts_needed < 1:
        contracts_needed = 1
    
    st.write(f"Put seleccionado - Strike: ${selected_put['strike']:.2f}, Prima: ${selected_put['lastPrice']:.2f}")
    st.write(f"Contratos de put recomendados: {int(np.ceil(contracts_needed))}")
    
    # Costo de la cobertura
    hedge_cost = int(np.ceil(contracts_needed)) * selected_put['lastPrice'] * 100
    hedge_coverage = int(np.ceil(contracts_needed)) * 100
    
    st.write(f"Costo total de la cobertura: ${hedge_cost:.2f}")
    st.write(f"Protección: {hedge_coverage} acciones de {shares_owned} ({hedge_coverage/shares_owned*100:.0f}%)")
    
    # Análisis de escenarios
    st.subheader("Análisis de Escenarios con Cobertura")
    
    price_changes = [-0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3]
    scenarios = []
    
    for change in price_changes:
        new_price = current_price * (1 + change)
        stock_pl = shares_owned * (new_price - current_price)
        
        # Cálculo del P&L de los puts
        if new_price <selected_put['strike']:
            put_pl = (selected_put['strike'] - new_price) * hedge_coverage - hedge_cost
        else:
            put_pl = -hedge_cost
            
        total_pl = stock_pl + put_pl
        
        scenarios.append({
            "Cambio %": f"{change*100:.0f}%",
            "Nuevo Precio": f"${new_price:.2f}",
            "P&L Acciones": f"${stock_pl:.2f}",
            "P&L Cobertura": f"${put_pl:.2f}",
            "P&L Total": f"${total_pl:.2f}"
        })
    
    df_scenarios = pd.DataFrame(scenarios)
    st.dataframe(df_scenarios)

def main():
    stock = st.text_input("Ingrese el símbolo del ticker del activo subyacente", value="GGAL")
    ticker = yf.Ticker(stock)
    
    # Obtener precio actual
    try:
        data = ticker.history(period="1d")
        if not data.empty:
            current_price = data['Close'].iloc[-1]
            st.write(f"Precio actual de {stock}: ${current_price:.2f}")
        else:
            st.error("No hay datos disponibles para este ticker o período.")
            return
    except Exception as e:
        st.error(f"Error al obtener datos: {e}")
        return
    
    # Información General
    st.header(f'📊 Panel de Opciones para {stock}')
    
    # Ratios Financieros extendidos
    st.subheader("📊 Ratios Financieros")
    info = ticker.info
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Ratio P/E**: {info.get('trailingPE', 'N/A')}")
        st.write(f"**Ratio P/B**: {info.get('priceToBook', 'N/A')}")
        st.write(f"**Rendimiento del Dividendo**: {info.get('dividendYield', 'N/A') * 100 if info.get('dividendYield') else 'N/A'}%")
        st.write(f"**Beta**: {info.get('beta', 'N/A')}")
    
    with col2:
        st.write(f"**ROE**: {info.get('returnOnEquity', 'N/A') * 100 if info.get('returnOnEquity') else 'N/A'}%")
        st.write(f"**ROA**: {info.get('returnOnAssets', 'N/A') * 100 if info.get('returnOnAssets') else 'N/A'}%")
        st.write(f"**Margen Operativo**: {info.get('operatingMargins', 'N/A') * 100 if info.get('operatingMargins') else 'N/A'}%")
        st.write(f"**FCF Yield**: {info.get('freeCashflowYield', 'N/A') * 100 if info.get('freeCashflowYield') else 'N/A'}%")
    
    # Gráfico de precios históricos
    st.subheader("📈 Gráfico de Precios Históricos")
    period = st.selectbox('Seleccionar período', ['1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'])
    hist_data = ticker.history(period=period)
    plot_candlestick_chart(hist_data)
    
    # Análisis Técnico
    st.header("📊 Análisis Técnico")
    
    # MACD
    st.subheader("📉 MACD")
    hist_data = ticker.history(period="6mo")
    macd, signal_line, histogram = calculate_macd(hist_data)
    fig_macd = go.Figure()
    fig_macd.add_trace(go.Scatter(x=hist_data.index, y=macd, mode='lines', name='MACD'))
    fig_macd.add_trace(go.Scatter(x=hist_data.index, y=signal_line, mode='lines', name='Línea de Señal'))
    fig_macd.add_trace(go.Bar(x=hist_data.index, y=histogram, name='Histograma'))
    st.plotly_chart(fig_macd, use_container_width=True)
    
    # Correlación con el mercado
    st.subheader("🔄 Correlación con el Mercado")
    plot_correlation_with_market(stock)
    
    # Datos de Opciones
    st.header("🎯 Datos de Opciones")
    
    expirations = ticker.options
    if expirations:
        expiration = st.selectbox("📅 Seleccionar Fecha de Vencimiento", expirations)
        option_chain = get_cached_option_data(ticker, expiration)
        
        if option_chain is not None:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📈 Calls")
                st.dataframe(option_chain.calls)
            with col2:
                st.subheader("📉 Puts")
                st.dataframe(option_chain.puts)
            
            # Análisis de Volatilidad y Griegas
            display_greeks(option_chain, current_price)
            plot_volatility_term_structure(ticker)
            
            # Estrategias de Opciones
            st.header("💡 Estrategias de Opciones")
            display_options_strategy(ticker, current_price, expiration)
    else:
        st.error(f"No hay datos de opciones disponibles para {stock}")
    
    # Análisis Fundamental
    st.header("📊 Análisis Fundamental")
    
    # Ratios financieros detallados
    st.subheader("Métricas Fundamentales")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Valuación**")
        st.write(f"P/E: {info.get('trailingPE', 'N/A')}")
        st.write(f"P/B: {info.get('priceToBook', 'N/A')}")
        st.write(f"P/S: {info.get('priceToSalesTrailing12Months', 'N/A')}")
    
    with col2:
        st.write("**Rentabilidad**")
        st.write(f"ROE: {info.get('returnOnEquity', 'N/A') * 100 if info.get('returnOnEquity') else 'N/A'}%")
        st.write(f"ROA: {info.get('returnOnAssets', 'N/A') * 100 if info.get('returnOnAssets') else 'N/A'}%")
        st.write(f"Margen Operativo: {info.get('operatingMargins', 'N/A') * 100 if info.get('operatingMargins') else 'N/A'}%")
    
    with col3:
        st.write("**Crecimiento**")
        st.write(f"Crecimiento Ingresos: {info.get('revenueGrowth', 'N/A') * 100 if info.get('revenueGrowth') else 'N/A'}%")
        st.write(f"Crecimiento EPS: {info.get('earningsGrowth', 'N/A') * 100 if info.get('earningsGrowth') else 'N/A'}%")
    
    # Simulaciones y Proyecciones
    st.header("🔮 Simulaciones y Proyecciones")
    
    # Monte Carlo
    st.subheader("📈 Simulación de Monte Carlo")
    plot_monte_carlo(ticker, current_price)
    
    # Cono de probabilidad
    st.subheader("🎯 Cono de Probabilidad")
    if len(ticker.options) > 0:
        expiration = ticker.options[0]
        option_chain = get_cached_option_data(ticker, expiration)
        if option_chain is not None and 'impliedVolatility' in option_chain.calls.columns:
            iv = option_chain.calls['impliedVolatility'].mean()
            plot_probability_cone(ticker, current_price, expiration, iv)
    
    # Calculadora de Cobertura
    st.header("🛡️ Calculadora de Cobertura")
    shares_owned = st.number_input("Número de acciones a cubrir", min_value=0, value=100)
    hedging_calculator(ticker, current_price, shares_owned)
    
    # Descripción de Estrategias de Opciones
    st.subheader("📈 Descripción de Estrategias de Opciones")
    st.markdown("""
    ### Estrategias Comunes:
    1. **📊 Compra de Call**: Usar cuando se espera un aumento significativo en el precio del activo subyacente.
    2. **🔻 Compra de Put**: Estrategia defensiva para protegerse contra una caída en el precio del subyacente.
    3. **⚖️ Cono Largo**: Capitalizar la alta volatilidad comprando un call y un put con el mismo precio de ejercicio y vencimiento.
    4. **🔒 Cono Corto**: Beneficiarse de la baja volatilidad vendiendo un call y un put con el mismo precio de ejercicio y vencimiento.
    5. **🛡️ Collar**: Proteger una posición larga en acciones vendiendo un call y comprando un put.
    6. **📈 Spread Alcista de Calls**: Beneficiarse de un movimiento alcista limitado comprando un call y vendiendo otro con un precio de ejercicio más alto.
    7. **📉 Spread Bajista de Puts**: Beneficiarse de un movimiento bajista limitado comprando un put y vendiendo otro con un precio de ejercicio más bajo.
    8. **🦋 Mariposa Larga**: Beneficiarse de la baja volatilidad o cuando se espera que el precio se mantenga dentro de un rango estrecho.
    9. **🦅 Cóndor de Hierro**: Estrategia de volatilidad neutral que se beneficia cuando el precio del activo subyacente permanece dentro de un rango específico.
    """)
    
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
    
    # Footer
    st.markdown("---")
    st.markdown("© 2024 Optima Consulting & Management LLC | [LinkedIn](https://www.linkedin.com/company/optima-consulting-managament-llc) | [Capacitaciones](https://optima-learning--ashy.vercel.app/) | [Página Web](https://www.optimafinancials.com/)")

if __name__ == "__main__":
    main()