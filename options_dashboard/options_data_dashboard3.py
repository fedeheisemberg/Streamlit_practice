#options_data_dashboard3.py
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from subscription_manager import save_feedback

# Configuración de la página de Streamlit
st.set_page_config(page_title="Dashboard OptionsPro", layout="wide", page_icon="options_dashboard/favicon.ico")
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

def display_options_strategy(ticker, current_price, selected_expiration):
    st.subheader("💡 Estrategia de Opciones")
    
    strategy = st.selectbox("Elegir Estrategia", [
        "Cono Largo",
        "Cono Corto",
        "Collar",
        "Spread Alcista de Calls",
        "Spread Bajista de Puts",
        "Spread Mariposa"
    ], key="strategy_selector")
    
    options = ticker.option_chain(selected_expiration)
    
    strategy_functions = {
        "Cono Largo": implement_long_straddle,
        "Cono Corto": implement_short_straddle,
        "Collar": implement_collar,
        "Spread Alcista de Calls": implement_bull_call_spread,
        "Spread Bajista de Puts": implement_bear_put_spread,
        "Spread Mariposa": implement_butterfly_spread
    }
    
    strategy_functions[strategy](options, current_price)

# ... [El resto de las funciones de implementación de estrategias se mantienen igual, solo traduciendo los mensajes al español] ...
def implement_long_straddle(options, current_price):
    st.write("### Long Straddle")
    
    call_atm = options.calls[options.calls['inTheMoney'] == False].iloc[0]
    put_atm = options.puts[options.puts['inTheMoney'] == False].iloc[-1]
    
    quantity = st.number_input("Number of straddles", min_value=1, value=1, step=1)
    
    total_cost = (call_atm['lastPrice'] + put_atm['lastPrice']) * 100 * quantity
    max_profit = float('inf')
    max_loss = total_cost
    
    display_strategy_details(call_atm['strike'], call_atm['lastPrice'], put_atm['lastPrice'], total_cost, max_profit, max_loss)
    plot_profit_loss_profile(options, current_price, lambda strike: quantity * (max(0, strike - call_atm['strike']) + max(0, put_atm['strike'] - strike) - (call_atm['lastPrice'] + put_atm['lastPrice'])) * 100, "Long Straddle")

def implement_short_straddle(options, current_price):
    st.write("### Short Straddle")
    
    call_atm = options.calls[options.calls['inTheMoney'] == False].iloc[0]
    put_atm = options.puts[options.puts['inTheMoney'] == False].iloc[-1]
    
    quantity = st.number_input("Number of short straddles", min_value=1, value=1, step=1)
    
    total_income = (call_atm['lastPrice'] + put_atm['lastPrice']) * 100 * quantity
    max_profit = total_income
    max_loss = float('inf')
    
    display_strategy_details(call_atm['strike'], call_atm['lastPrice'], put_atm['lastPrice'], -total_income, max_profit, max_loss)
    plot_profit_loss_profile(options, current_price, lambda strike: quantity * ((call_atm['lastPrice'] + put_atm['lastPrice']) - max(0, strike - call_atm['strike']) - max(0, put_atm['strike'] - strike)) * 100, "Short Straddle")

def implement_collar(options, current_price):
    st.write("### Collar")
    
    shares = st.number_input("Number of shares", min_value=100, value=100, step=100)
    
    call_otm = options.calls[options.calls['strike'] > current_price].iloc[0]
    put_otm = options.puts[options.puts['strike'] < current_price].iloc[-1]
    
    collar_cost = call_otm['lastPrice'] - put_otm['lastPrice']
    total_cost = collar_cost * shares
    max_profit = (call_otm['strike'] - current_price) * shares - total_cost
    max_loss = (current_price - put_otm['strike']) * shares + total_cost
    
    display_strategy_details(current_price, call_otm['lastPrice'], put_otm['lastPrice'], total_cost, max_profit, max_loss)
    plot_profit_loss_profile(options, current_price, lambda strike: (min(call_otm['strike'], max(put_otm['strike'], strike)) - current_price) * shares - total_cost, "Collar")

def implement_bull_call_spread(options, current_price):
    st.write("### Bull Call Spread")
    
    call_buy = options.calls[options.calls['strike'] >= current_price].iloc[0]
    call_sell = options.calls[options.calls['strike'] > call_buy['strike']].iloc[0]
    
    quantity = st.number_input("Number of spreads", min_value=1, value=1, step=1)
    
    spread_cost = call_buy['lastPrice'] - call_sell['lastPrice']
    total_cost = spread_cost * 100 * quantity
    max_profit = (call_sell['strike'] - call_buy['strike'] - spread_cost) * 100 * quantity
    max_loss = total_cost
    
    display_strategy_details(call_buy['strike'], call_buy['lastPrice'], call_sell['lastPrice'], total_cost, max_profit, max_loss)
    plot_profit_loss_profile(options, current_price, lambda strike: quantity * (min(call_sell['strike'], max(call_buy['strike'], strike)) - call_buy['strike'] - spread_cost) * 100, "Bull Call Spread")

def implement_bear_put_spread(options, current_price):
    st.write("### Bear Put Spread")
    
    put_buy = options.puts[options.puts['strike'] <= current_price].iloc[-1]
    put_sell = options.puts[options.puts['strike'] < put_buy['strike']].iloc[-1]
    
    quantity = st.number_input("Number of spreads", min_value=1, value=1, step=1)
    
    spread_cost = put_buy['lastPrice'] - put_sell['lastPrice']
    total_cost = spread_cost * 100 * quantity
    max_profit = (put_buy['strike'] - put_sell['strike'] - spread_cost) * 100 * quantity
    max_loss = total_cost
    
    display_strategy_details(put_buy['strike'], put_buy['lastPrice'], put_sell['lastPrice'], total_cost, max_profit, max_loss)
    plot_profit_loss_profile(options, current_price, lambda strike: quantity * (put_buy['strike'] - max(put_sell['strike'], min(put_buy['strike'], strike)) - spread_cost) * 100, "Bear Put Spread")

def implement_butterfly_spread(options, current_price):
    st.write("### Butterfly Spread")
    
    call_buy_low = options.calls[options.calls['strike'] <= current_price].iloc[-1]
    call_sell_mid = options.calls[options.calls['strike'] > call_buy_low['strike']].iloc[0]
    call_buy_high = options.calls[options.calls['strike'] > call_sell_mid['strike']].iloc[0]
    
    quantity = st.number_input("Number of butterflies", min_value=1, value=1, step=1)
    
    butterfly_cost = call_buy_low['lastPrice'] - 2 * call_sell_mid['lastPrice'] + call_buy_high['lastPrice']
    total_cost = butterfly_cost * 100 * quantity
    max_profit = (call_sell_mid['strike'] - call_buy_low['strike'] - butterfly_cost) * 100 * quantity
    max_loss = total_cost
    
    display_strategy_details(call_buy_low['strike'], call_buy_low['lastPrice'], call_buy_high['lastPrice'], total_cost, max_profit, max_loss)
    plot_profit_loss_profile(options, current_price, lambda strike: quantity * (max(0, strike - call_buy_low['strike']) - 2 * max(0, strike - call_sell_mid['strike']) + max(0, strike - call_buy_high['strike']) - butterfly_cost) * 100, "Butterfly Spread")

def display_strategy_details(strike, premium1, premium2, total_cost, max_profit, max_loss):
    st.write(f"Precio Strike: ${strike:.2f}")
    st.write(f"Prima 1: ${premium1:.2f}")
    st.write(f"Prima 2: ${premium2:.2f}")
    st.write(f"Costo total: ${abs(total_cost):.2f}")
    st.write(f"Máxima ganancia: {'Ilimitada' if max_profit == float('inf') else f'${max_profit:.2f}'}")
    st.write(f"Máxima pérdida: {'Ilimitada' if max_loss == float('inf') else f'${max_loss:.2f}'}")

def plot_profit_loss_profile(options, current_price, profit_function, strategy_name):
    strikes = pd.concat([options.calls['strike'], options.puts['strike']]).unique()
    strikes.sort()
    profits = [profit_function(strike) for strike in strikes]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=strikes, y=profits, mode='lines', name='Profit/Loss'))
    fig.add_hline(y=0, line_dash="dash", line_color="red")
    fig.add_vline(x=current_price, line_dash="dash", line_color="green", annotation_text="Current Price")
    fig.update_layout(title=f'Profit/Loss Profile for {strategy_name}', xaxis_title='Underlying Price', yaxis_title='Profit/Loss ($)')
    st.plotly_chart(fig)

def main():
    stock = st.text_input("Ingrese el símbolo del ticker del activo subyacente", value="GGAL")
    st.header(f'📊 Panel de Opciones para {stock}')

    ticker = yf.Ticker(stock)

    # Ratios Financieros
    st.subheader("📊 Ratios Financieros")
    info = ticker.info
    st.write(f"**Ratio P/E**: {info.get('trailingPE', 'N/A')}")
    st.write(f"**Ratio P/B**: {info.get('priceToBook', 'N/A')}")
    st.write(f"**Rendimiento del Dividendo**: {info.get('dividendYield', 'N/A') * 100 if info.get('dividendYield') else 'N/A'}%")
    st.write(f"**Beta**: {info.get('beta', 'N/A')}")

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
    8. **🦋 Spread Mariposa**: Beneficiarse de la baja volatilidad o cuando se espera que el precio se mantenga dentro de un rango estrecho.

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

    # Retroalimentación
    st.subheader("📝 ¡Queremos tu Opinión!")
    st.markdown("¿Qué más te gustaría ver en este proyecto? ¿Estarías interesado en un proyecto de opciones más complejo? ¡Tu opinión es muy importante para nosotros!")

    feedback = st.text_area("✍️ Deja tu comentario aquí:")
    email = st.text_input("📧 Deja tu email para que podamos contactarte (opcional)")

    if st.button("📨 Enviar Retroalimentación"):
        if feedback:
            sheet_name = "StreamlitSuscriber"
            
            if email:
                if save_feedback(email, feedback, sheet_name):
                    st.success(f"🎉 ¡Gracias por tu retroalimentación, {email}! Tu opinión es muy valiosa para nosotros.")
                else:
                    st.error("Hubo un problema al guardar tu retroalimentación. Por favor, inténtalo de nuevo.")
            else:
                if save_feedback("", feedback, sheet_name):
                    st.success("🎉 ¡Gracias por tu retroalimentación! Valoramos tu opinión.")
                else:
                    st.error("Hubo un problema al guardar tu retroalimentación. Por favor, inténtalo de nuevo.")
        else:
            st.error("⚠️ Por favor, ingresa tu retroalimentación.")
    
    # Pie de página
    st.markdown("---")
    st.markdown("© 2024 Optima Consulting & Management LLC | [LinkedIn](https://www.linkedin.com/company/optima-consulting-managament-llc) | [Formación](https://www.optimalearning.site/) | [Sitio Web](https://www.optimafinancials.com/)")

if __name__ == "__main__":
    main()