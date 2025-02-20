#options_data_dashboard.py
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from subscription_manager import save_feedback
import numpy as np

# Configuración de la página con favicon
st.set_page_config(page_title="Dashboard OptionsPro", layout="wide", page_icon="options_dashboard/favicon.ico")

# Función para determinar el modo (oscuro o claro)
def get_theme():
    return st.get_option("theme.base")

# Cargar logo basado en el tema
if get_theme() == "light":
    st.image("options_dashboard/logo2.png")
else:
    st.image("options_dashboard/logo1.png")

# Crear título
st.title("Dashboard OptionsPro - Optima Consulting & Management LLC")


def get_option_data(ticker, expiration):
    try:
        option_chain = ticker.option_chain(expiration)
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

def plot_probability_cone(hist_data, current_price, days=30):
    """Calcula y grafica el cono de probabilidad usando volatilidad histórica"""
    try:
        # Obtener tema actual de Streamlit
        theme = get_theme()
        
        # Colores mejorados para dark y light mode
        if theme == "light":
            color_3sigma = 'rgba(255, 87, 34, 0.25)'  # Naranja fuerte
            border_3sigma = 'rgba(255, 87, 34, 0.8)'
            color_2sigma = 'rgba(33, 150, 243, 0.3)'  # Azul vibrante
            border_2sigma = 'rgba(33, 150, 243, 0.9)'
            current_price_color = '#1E1E1E'  # Gris oscuro
            line_1sigma_up = '#D32F2F'  # Rojo oscuro
            line_1sigma_down = '#388E3C'  # Verde oscuro
            grid_color = 'rgba(160, 160, 160, 0.5)'
            bg_color = 'rgba(255, 255, 255, 0.9)'  # Fondo blanco
        else:
            color_3sigma = 'rgba(255, 87, 34, 0.35)'
            border_3sigma = 'rgba(255, 87, 34, 1)'
            color_2sigma = 'rgba(33, 150, 243, 0.4)'
            border_2sigma = 'rgba(33, 150, 243, 1)'
            current_price_color = '#E0E0E0'  # Gris claro
            line_1sigma_up = '#FF5252'  # Rojo claro
            line_1sigma_down = '#66BB6A'  # Verde claro
            grid_color = 'rgba(70, 70, 70, 0.5)'
            bg_color = 'rgba(30, 30, 30, 0.9)'  # Fondo oscuro
        
        # Calcular volatilidad histórica
        returns = np.log(hist_data['Close'] / hist_data['Close'].shift(1))
        volatility = returns.std() * np.sqrt(252)  # Volatilidad anualizada
        
        # Crear rango de fechas futuras
        future_dates = [datetime.today() + timedelta(days=i) for i in range(days)]
        
        # Calcular desviaciones estándar para cada día
        time_periods = np.arange(1, days+1) / 252
        std_devs_1 = volatility * np.sqrt(time_periods)
        std_devs_2 = 2 * volatility * np.sqrt(time_periods)
        std_devs_3 = 3 * volatility * np.sqrt(time_periods)
        
        # Calcular niveles de precios
        upper_2sigma = current_price * (1 + std_devs_2)
        lower_2sigma = current_price * (1 - std_devs_2)
        upper_3sigma = current_price * (1 + std_devs_3)
        lower_3sigma = current_price * (1 - std_devs_3)
        
        # Crear gráfico con colores mejorados
        fig = go.Figure()
        
        # Área de 3σ (99.7% de probabilidad)
        fig.add_trace(go.Scatter(
            x=future_dates + future_dates[::-1],
            y=np.concatenate([upper_3sigma, lower_3sigma[::-1]]),
            fill='toself',
            fillcolor=color_3sigma,
            line=dict(color=border_3sigma),
            name='Zona de 3σ (99.7%)'
        ))
        
        # Área de 2σ (95.4% de probabilidad)
        fig.add_trace(go.Scatter(
            x=future_dates + future_dates[::-1],
            y=np.concatenate([upper_2sigma, lower_2sigma[::-1]]),
            fill='toself',
            fillcolor=color_2sigma,
            line=dict(color=border_2sigma),
            name='Zona de 2σ (95.4%)'
        ))
        
        # Línea central (precio actual)
        fig.add_trace(go.Scatter(
            x=future_dates,
            y=[current_price]*days,
            line=dict(color=current_price_color, width=2, dash='dot'),
            name='Precio Actual'
        ))
        
        # Líneas de tendencia media
        fig.add_trace(go.Scatter(
            x=future_dates,
            y=current_price * (1 + std_devs_1),
            line=dict(color=line_1sigma_up, width=1.5, dash='dash'),
            name='+1σ (68.3%)'
        ))
        
        fig.add_trace(go.Scatter(
            x=future_dates,
            y=current_price * (1 - std_devs_1),
            line=dict(color=line_1sigma_down, width=1.5, dash='dash'),
            name='-1σ (68.3%)'
        ))
        
        fig.update_layout(
            title='📊 Cono de Probabilidad (Niveles Sigma)',
            xaxis_title='Fecha',
            yaxis_title='Precio Proyectado',
            plot_bgcolor=bg_color,
            paper_bgcolor='rgba(0, 0, 0, 0)',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            hovermode="x unified",
            showlegend=True,
            xaxis=dict(gridcolor=grid_color),
            yaxis=dict(gridcolor=grid_color)
        )
        
        # Anotaciones explicativas
        fig.add_annotation(
            x=future_dates[-10],
            y=upper_3sigma[-10],
            text="Máximo esperado (3σ)",
            showarrow=True,
            arrowhead=1,
            ax=-50,
            ay=-40
        )
        
        fig.add_annotation(
            x=future_dates[-10],
            y=lower_3sigma[-10],
            text="Mínimo esperado (3σ)",
            showarrow=True,
            arrowhead=1,
            ax=-50,
            ay=40
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error calculando el cono de probabilidad: {e}")


def plot_iv_term_structure(ticker, current_price):
    """Grafica la estructura temporal de la volatilidad implícita"""
    try:
        expirations = ticker.options
        iv_data = []
        
        for exp in expirations:
            try:
                # Obtener datos de opciones
                chain = ticker.option_chain(exp)
                days_to_exp = (datetime.strptime(exp, "%Y-%m-%d") - datetime.today()).days
                
                # Encontrar strikes ATM
                call_atm = chain.calls.iloc[(chain.calls['strike'] - current_price).abs().argsort()[:1]]
                put_atm = chain.puts.iloc[(chain.puts['strike'] - current_price).abs().argsort()[:1]]
                
                # Calcular IV promedio
                avg_iv = (call_atm['impliedVolatility'].values[0] + put_atm['impliedVolatility'].values[0]) / 2
                
                iv_data.append({
                    'Expiración': exp,
                    'Días': days_to_exp,
                    'IV Promedio': avg_iv
                })
            except:
                continue
        
        if not iv_data:
            st.warning("No se encontraron datos de IV para la estructura temporal")
            return
        
        df_iv = pd.DataFrame(iv_data).sort_values('Días')
        
        # Crear gráfico
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df_iv['Días'],
            y=df_iv['IV Promedio'],
            mode='lines+markers',
            name='IV Promedio ATM'
        ))
        
        fig.update_layout(
            title='📈 Estructura Temporal de Volatilidad Implícita',
            xaxis_title='Días hasta el Vencimiento',
            yaxis_title='Volatilidad Implícita',
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error generando estructura temporal de IV: {e}")

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

def main():
    stock = st.text_input("Ingrese el símbolo del ticker del activo subyacente", value="GGAL")
    st.header(f'📊 Panel de Opciones para {stock}')

    ticker = yf.Ticker(stock)

    # Ratios Financieros Ampliados
    st.subheader("📊 Ratios Financieros Ampliados")
    info = ticker.info

    # Capitalización de mercado y valor empresarial
    st.write(f"**Capitalización de Mercado**: ${info.get('marketCap', 'N/A'):,}")
    st.write(f"**Valor Empresarial (EV)**: ${info.get('enterpriseValue', 'N/A'):,}")

    # Ratios de Rentabilidad
    st.write(f"**Ratio P/E**: {info.get('trailingPE', 'N/A')}")
    st.write(f"**Ratio P/B**: {info.get('priceToBook', 'N/A')}")
    st.write(f"**Rendimiento del Dividendo**: {info.get('dividendYield', 'N/A') * 100 if info.get('dividendYield') else 'N/A'}%")
    st.write(f"**Margen de Beneficio Neto**: {info.get('profitMargins', 'N/A') * 100 if info.get('profitMargins') else 'N/A'}%")
    # EBITDA con manejo de errores
    ebitda = info.get('ebitda', None)
    if ebitda is not None:
        st.write(f"**EBITDA**: ${ebitda:,}")
    else:
        st.write("**EBITDA**: N/A")
    st.write(f"**Beta**: {info.get('beta', 'N/A')}")

    # Ratios de Eficiencia y Rentabilidad
    st.write(f"**ROE (Return on Equity)**: {info.get('returnOnEquity', 'N/A') * 100 if info.get('returnOnEquity') else 'N/A'}%")
    st.write(f"**ROA (Return on Assets)**: {info.get('returnOnAssets', 'N/A') * 100 if info.get('returnOnAssets') else 'N/A'}%")

    # Ratios de Endeudamiento
    st.write(f"**Debt to Equity Ratio**: {info.get('debtToEquity', 'N/A')}")

    # Crecimientos
    st.write(f"**Crecimiento de Ingresos**: {info.get('revenueGrowth', 'N/A') * 100 if info.get('revenueGrowth') else 'N/A'}%")
    st.write(f"**Crecimiento de BPA (Beneficio Por Acción)**: {info.get('earningsGrowth', 'N/A') * 100 if info.get('earningsGrowth') else 'N/A'}%")

    # Precio Actual
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

    # Gráfico de Precios Históricos
    st.subheader("📈 Gráfico de Precios Históricos")
    period = st.selectbox('Seleccionar período', ['1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'])
    
    hist_data = ticker.history(period=period)
    plot_candlestick_chart(hist_data)

    # MACD
    st.subheader("📉 MACD")
    macd, signal_line, histogram = calculate_macd(hist_data)
    fig_macd = go.Figure()
    fig_macd.add_trace(go.Scatter(x=hist_data.index, y=macd, mode='lines', name='MACD'))
    fig_macd.add_trace(go.Scatter(x=hist_data.index, y=signal_line, mode='lines', name='Línea de Señal'))
    fig_macd.add_trace(go.Bar(x=hist_data.index, y=histogram, name='Histograma'))
    fig_macd.update_layout(title=f'MACD para {stock}', xaxis_title='Fecha', yaxis_title='MACD')
    st.plotly_chart(fig_macd, use_container_width=True)

    # Nuevas secciones añadidas aquí
    st.subheader("🔮 Cono de Probabilidad")
    st.markdown("""
    El cono de probabilidad muestra el rango esperado de precios basado en la volatilidad histórica (2 desviaciones estándar).
    Indica la zona donde el precio tiene un 95% de probabilidad de permanecer según el movimiento histórico.
    """)
    plot_probability_cone(hist_data, current_price)
    
    st.subheader("⏳ Estructura Temporal de Volatilidad")
    st.markdown("""
    La estructura temporal de volatilidad muestra cómo varía la volatilidad implícita entre diferentes fechas de vencimiento.
    Una curva invertida (contango) indica mayor volatilidad en corto plazo, mientras que una curva normal señala mayor incertidumbre a largo plazo.
    """)
    plot_iv_term_structure(ticker, current_price)

    # Opciones
    expirations = ticker.options
    if not expirations:
        st.error(f"No hay datos de opciones disponibles para {stock}")
    else:
        expiration = st.selectbox("📅 Seleccionar Fecha de Vencimiento", expirations, key="main_expiration_selector")
        
        option_chain = get_option_data(ticker, expiration)
        
        if option_chain is not None:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 Calls")
                st.dataframe(option_chain.calls)
                st.download_button(
                    label="Descargar Datos de Calls",
                    data=option_chain.calls.to_csv(index=False),
                    file_name=f"{stock}_calls_{expiration}.csv",
                    mime="text/csv",
                )
            
            with col2:
                st.subheader("📉 Puts")
                st.dataframe(option_chain.puts)
                st.download_button(
                    label="Descargar Datos de Puts",
                    data=option_chain.puts.to_csv(index=False),
                    file_name=f"{stock}_puts_{expiration}.csv",
                    mime="text/csv",
                )
            
            # Análisis de Volatilidad Implícita
            st.subheader("Análisis de Volatilidad Implícita")
            st.markdown("""
            La sonrisa de volatilidad implícita refleja cómo cambia la volatilidad con el precio de ejercicio.
            Una sonrisa pronunciada indica mayor incertidumbre en los extremos del rango de precios del activo subyacente.
            Las opciones at-the-money tienden a tener menor volatilidad implícita, mientras que las opciones out-of-the-money (OTM) muestran mayor volatilidad debido al riesgo.
            """)
            
            # Sonrisa de Volatilidad Implícita
            if 'impliedVolatility' in option_chain.calls.columns and 'impliedVolatility' in option_chain.puts.columns:
                fig_vol = go.Figure()
                fig_vol.add_trace(go.Scatter(x=option_chain.calls['strike'], y=option_chain.calls['impliedVolatility'], mode='lines', name='Calls'))
                fig_vol.add_trace(go.Scatter(x=option_chain.puts['strike'], y=option_chain.puts['impliedVolatility'], mode='lines', name='Puts'))
                fig_vol.update_layout(title='📊 Sonrisa de Volatilidad Implícita', xaxis_title='Precio de Ejercicio', yaxis_title='Volatilidad Implícita')
                st.plotly_chart(fig_vol, use_container_width=True)
            else:
                st.warning("No se puede mostrar la sonrisa de volatilidad implícita debido a datos faltantes.")

    # Estrategias de Opciones
            display_options_strategy(ticker, current_price, expiration)

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

    Cada estrategia tiene su propio perfil de riesgo y recompensa. La clave es seleccionar la apropiada basándose en la volatilidad implícita y las tendencias del mercado.
    """)

    # Crecimiento del Beneficio Por Acción
    st.subheader(f"💰 Beneficio Por Acción Anual para {stock}")
    eps_data = get_eps_data(stock, stock.lower())
    if eps_data is not None:
        st.dataframe(eps_data)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=eps_data['Fecha'],
            y=eps_data['BPA (Beneficio Por Acción)'],
            mode='lines+markers',
            name='BPA'
        ))
        
        fig.update_layout(
            title=f'📅 Beneficio Por Acción (BPA) Anual para {stock}',
            xaxis_title='Fecha',
            yaxis_title='BPA (Beneficio Por Acción)',
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
    st.markdown("© 2024 Optima Consulting & Management LLC | [LinkedIn](https://www.linkedin.com/company/optima-consulting-managament-llc) | [Capacitaciones](https://optima-learning--ashy.vercel.app/) | [Página Web](https://www.optimafinancials.com/)" )


if __name__ == "__main__":
    main()