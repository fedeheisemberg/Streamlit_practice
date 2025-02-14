import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from subscription_manager import save_feedback

@st.cache_data
def get_option_data(ticker, expiration):
    """Get option chain data for a given ticker and expiration date."""
    try:
        option_chain = ticker.option_chain(expiration)
        if 'impliedVolatility' not in option_chain.calls.columns or 'impliedVolatility' not in option_chain.puts.columns:
            st.warning("Los datos de volatilidad implícita no están disponibles. Algunas gráficas pueden no mostrarse.")
        return option_chain
    except Exception as e:
        st.error(f"Error al obtener datos de opciones: {e}")
        return None

def calculate_technical_indicators(data):
    """Calculate various technical indicators for the given price data."""
    # MACD calculation
    exp1 = data['Close'].ewm(span=12, adjust=False).mean()
    exp2 = data['Close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - signal_line
    return macd, signal_line, histogram

def plot_chart(fig, title, x_title="", y_title="", show_legend=True):
    """Common function to update chart layouts."""
    fig.update_layout(
        title=title,
        xaxis_title=x_title,
        yaxis_title=y_title,
        showlegend=show_legend
    )
    st.plotly_chart(fig, use_container_width=True)

def create_profit_loss_chart(strikes, profits, current_price, strategy_name):
    """Create a profit/loss chart for option strategies."""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(x=strikes, y=profits, mode='lines', name='Perfil de Ganancias/Pérdidas'))
    fig.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Punto de equilibrio")
    fig.add_vline(x=current_price, line_dash="dash", line_color="green", annotation_text="Precio actual")
    
    plot_chart(
        fig,
        f'Perfil de Ganancias/Pérdidas - {strategy_name}',
        'Precio del activo subyacente',
        'Ganancias/Pérdidas ($)'
    )

def implement_strategy(options, current_price, strategy_config):
    """Generic function to implement various option strategies."""
    st.write(f"### {strategy_config['name']}")
    
    # Get required options based on strategy type
    selected_options = {}
    for option_type, selection_criteria in strategy_config['options'].items():
        if selection_criteria['type'] == 'ATM':
            selected_options[option_type] = options.calls[options.calls['inTheMoney'] == False].iloc[0] if 'call' in option_type.lower() else options.puts[options.puts['inTheMoney'] == False].iloc[-1]
        elif selection_criteria['type'] == 'OTM':
            selected_options[option_type] = options.calls[options.calls['strike'] > current_price].iloc[0] if 'call' in option_type.lower() else options.puts[options.puts['strike'] < current_price].iloc[-1]
    
    # Get quantity input
    quantity = st.number_input(f"Cantidad de {strategy_config['name'].lower()}", min_value=1, value=1, step=1)
    
    # Calculate costs and profits
    costs = strategy_config['calculate_costs'](selected_options, quantity)
    
    # Display strategy details
    for detail in strategy_config['display_details']:
        st.write(detail['label'], detail['calculate'](selected_options, costs))
    
    # Create and display profit/loss chart
    strikes = np.linspace(options.calls['strike'].min(), options.calls['strike'].max(), 100)
    profits = [strategy_config['profit_function'](strike, selected_options, quantity, costs) for strike in strikes]
    create_profit_loss_chart(strikes, profits, current_price, strategy_config['name'])

def get_strategy_configs():
    """Return configuration for all supported option strategies."""
    return {
        'long_straddle': {
            'name': 'Cono Largo',
            'options': {
                'call_atm': {'type': 'ATM'},
                'put_atm': {'type': 'ATM'}
            },
            'calculate_costs': lambda options, quantity: (options['call_atm']['lastPrice'] + options['put_atm']['lastPrice']) * 100 * quantity,
            'profit_function': lambda strike, options, quantity, costs: quantity * (max(0, strike - options['call_atm']['strike']) + max(0, options['put_atm']['strike'] - strike) - costs/100),
            'display_details': [
                {'label': 'Ganancia máxima:', 'calculate': lambda options, costs: 'Ilimitada'},
                {'label': 'Pérdida máxima:', 'calculate': lambda options, costs: f"${costs:.2f}"}
            ]
        },
        # Add other strategies here...
    }

def main():
    st.title("Panel de Opciones")
    
    # Get stock data
    stock = st.text_input("Ingrese el símbolo del ticker del activo subyacente", value="GGAL")
    ticker = yf.Ticker(stock)
    
    try:
        current_price = ticker.history(period="1d")['Close'].iloc[-1]
        st.write(f"Precio actual de {stock}: ${current_price:.2f}")
    except Exception as e:
        st.error(f"Error al obtener datos: {e}")
        return
    
    # Display main sections
    sections = {
        "Información General": display_general_info,
        "Análisis Técnico": display_technical_analysis,
        "Datos de Opciones": display_options_data,
        "Estrategias": display_strategies,
        "Simulaciones": display_simulations
    }
    
    selected_section = st.sidebar.selectbox("Seleccionar Sección", list(sections.keys()))
    sections[selected_section](ticker, current_price)
    
    # Display feedback section
    display_feedback_section()

def display_general_info(ticker, current_price):
    """Display general information about the stock."""
    st.header("📊 Información General")
    info = ticker.info
    
    col1, col2 = st.columns(2)
    metrics = {
        "Ratio P/E": "trailingPE",
        "Ratio P/B": "priceToBook",
        "ROE": ("returnOnEquity", True),  # True indicates percentage
        "ROA": ("returnOnAssets", True)
    }
    
    for i, (label, key) in enumerate(metrics.items()):
        col = col1 if i < len(metrics)//2 else col2
        with col:
            if isinstance(key, tuple):
                value = info.get(key[0], 'N/A')
                if value != 'N/A' and key[1]:
                    value = f"{value * 100:.2f}%"
            else:
                value = info.get(key, 'N/A')
            st.write(f"**{label}**: {value}")

def display_technical_analysis(ticker, current_price):
    """Display technical analysis charts and indicators."""
    st.header("📈 Análisis Técnico")
    
    # Price chart
    hist_data = ticker.history(period="6mo")
    fig = go.Figure(data=[go.Candlestick(
        x=hist_data.index,
        open=hist_data['Open'],
        high=hist_data['High'],
        low=hist_data['Low'],
        close=hist_data['Close']
    )])
    plot_chart(fig, "Gráfico de Precios", "Fecha", "Precio")
    
    # MACD
    macd, signal, hist = calculate_technical_indicators(hist_data)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist_data.index, y=macd, mode='lines', name='MACD'))
    fig.add_trace(go.Scatter(x=hist_data.index, y=signal, mode='lines', name='Señal'))
    fig.add_trace(go.Bar(x=hist_data.index, y=hist, name='Histograma'))
    plot_chart(fig, "MACD", "Fecha", "Valor")

def display_options_data(ticker, current_price):
    """Display options chain data and analysis."""
    st.header("🎯 Datos de Opciones")
    
    expirations = ticker.options
    if not expirations:
        st.error(f"No hay datos de opciones disponibles para {ticker.ticker}")
        return
        
    expiration = st.selectbox("Fecha de Vencimiento", expirations)
    options = get_option_data(ticker, expiration)
    
    if options:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Calls")
            st.dataframe(options.calls)
        with col2:
            st.subheader("Puts")
            st.dataframe(options.puts)

def display_strategies(ticker, current_price):
    """Display available option strategies."""
    st.header("💡 Estrategias de Opciones")
    
    strategy_configs = get_strategy_configs()
    selected_strategy = st.selectbox("Seleccionar Estrategia", list(strategy_configs.keys()))
    
    if selected_strategy:
        options = get_option_data(ticker, ticker.options[0])
        if options:
            implement_strategy(options, current_price, strategy_configs[selected_strategy])

def display_simulations(ticker, current_price):
    """Display Monte Carlo simulations and probability analysis."""
    st.header("🔮 Simulaciones")
    
    # Monte Carlo simulation parameters
    days = 252  # One trading year
    simulations = 1000
    
    # Calculate historical volatility
    returns = ticker.history(period="1y")['Close'].pct_change().dropna()
    vol = returns.std() * np.sqrt(252)
    
    # Run simulation
    dt = 1/252
    paths = np.exp(
        (0 - 0.5 * vol ** 2) * dt +
        vol * np.sqrt(dt) * 
        np.random.normal(0, 1, size=(simulations, days))
    ).cumprod(axis=1) * current_price
    
    # Plot results
    fig = go.Figure()
    for path in paths[np.random.choice(simulations, 100)]:
        fig.add_trace(go.Scatter(y=path, mode='lines', opacity=0.1, showlegend=False))
    
    percentiles = np.percentile(paths, [5, 50, 95], axis=0)
    for i, p in enumerate(['5%', '50%', '95%']):
        fig.add_trace(go.Scatter(y=percentiles[i], name=p, line=dict(width=2)))
    
    plot_chart(fig, "Simulación de Monte Carlo", "Días", "Precio Proyectado")

def display_feedback_section():
    """Display feedback form."""
    st.header("📝 Feedback")
    
    feedback = st.text_area("Compartenos tu opinión:")
    email = st.text_input("Email (opcional):")
    
    if st.button("Enviar"):
        if feedback:
            if save_feedback(email or "", feedback, "StreamlitSuscriber"):
                st.success("¡Gracias por tu feedback!")
            else:
                st.error("Error al guardar el feedback.")
        else:
            st.error("Por favor ingresa tu feedback.")

if __name__ == "__main__":
    main()
    