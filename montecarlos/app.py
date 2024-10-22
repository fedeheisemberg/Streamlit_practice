import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime

def get_stock_data(symbol, start_date, end_date):
    stock = yf.download(symbol, start=start_date, end=end_date)
    return stock

def calculate_transaction_costs(price, shares, commission=0.001, slippage=0.0001):
    """
    Calcula los costos de transacción
    commission: 0.1% por operación
    slippage: 0.01% por operación
    """
    commission_cost = price * shares * commission
    slippage_cost = price * shares * slippage
    return commission_cost + slippage_cost

def run_monte_carlo(data, n_simulations, n_days, initial_investment=10000):
    # Calcular retornos diarios considerando costos
    returns = np.log(1 + data['Adj Close'].pct_change())
    mu = returns.mean()
    sigma = returns.std()
    
    # Parámetros de costos
    commission_rate = 0.001  # 0.1%
    slippage_rate = 0.0001  # 0.01%
    transaction_frequency = 5  # Días promedio entre operaciones
    
    simulations = np.zeros((n_days, n_simulations))
    equity_curves = np.zeros((n_days, n_simulations))
    drawdowns = np.zeros((n_days, n_simulations))
    
    initial_price = data['Adj Close'].iloc[-1]
    
    for i in range(n_simulations):
        # Generar retornos aleatorios
        daily_returns = np.random.normal(mu, sigma, n_days)
        
        # Calcular precios
        price_path = initial_price * np.exp(np.cumsum(daily_returns))
        
        # Calcular equity curve con costos
        equity = np.zeros(n_days)
        equity[0] = initial_investment
        
        for day in range(1, n_days):
            # Aplicar retorno del día
            equity[day] = equity[day-1] * (1 + daily_returns[day])
            
            # Aplicar costos de transacción si corresponde
            if day % transaction_frequency == 0:
                transaction_cost = equity[day] * (commission_rate + slippage_rate)
                equity[day] -= transaction_cost
        
        simulations[:, i] = price_path
        equity_curves[:, i] = equity
        
        # Calcular drawdown
        peak = np.maximum.accumulate(equity)
        drawdown = (equity - peak) / peak
        drawdowns[:, i] = drawdown
        
    return simulations, equity_curves, drawdowns

def main():
    st.title("Dashboard de Análisis de Mercado con Simulación Monte Carlo")
    
    # Inputs en la barra lateral
    st.sidebar.header("Parámetros")
    symbol = st.sidebar.text_input("Símbolo de la Acción", value="AAPL")
    n_simulations = st.sidebar.number_input("Número de Simulaciones", min_value=100, max_value=10000, value=5000)
    n_days = st.sidebar.number_input("Días de Pronóstico", min_value=30, max_value=365, value=252)
    initial_investment = st.sidebar.number_input("Inversión Inicial ($)", min_value=1000, value=10000)
    
    # Fechas
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=365)
    start_date = st.sidebar.date_input("Fecha de Inicio", value=start_date)
    end_date = st.sidebar.date_input("Fecha Final", value=end_date)
    
    if st.sidebar.button("Ejecutar Análisis"):
        # Obtener datos
        with st.spinner("Obteniendo datos del mercado..."):
            data = get_stock_data(symbol, start_date, end_date)
            
        # Ejecutar simulación
        with st.spinner("Ejecutando simulaciones Monte Carlo..."):
            simulations, equity_curves, drawdowns = run_monte_carlo(
                data, n_simulations, n_days, initial_investment)
            
        # 1. Gráfico de Simulaciones Monte Carlo
        fig1 = go.Figure()
        
        # Datos históricos
        fig1.add_trace(go.Scatter(
            x=data.index,
            y=data['Adj Close'],
            name="Histórico",
            line=dict(color='blue', width=2)
        ))
        
        # Simulaciones
        for i in range(min(100, n_simulations)):
            fig1.add_trace(go.Scatter(
                x=pd.date_range(start=data.index[-1], periods=n_days, freq='B'),
                y=simulations[:, i],
                name=f"Sim {i}",
                line=dict(color='gray', width=0.5),
                opacity=0.1,
                showlegend=False
            ))
            
        fig1.update_layout(title="Simulaciones Monte Carlo")
        st.plotly_chart(fig1)
        st.markdown("""
        **Explicación:** Este gráfico muestra las posibles trayectorias futuras del precio del activo. 
        La línea azul representa el precio histórico, mientras que las líneas grises son las diferentes 
        simulaciones basadas en la volatilidad histórica y el retorno esperado.
        """)
        
        # 2. Curva de Equity y Drawdown
        fig2 = make_subplots(rows=2, cols=1)
        
        # Equity Curve
        for i in range(min(100, n_simulations)):
            fig2.add_trace(
                go.Scatter(
                    y=equity_curves[:, i],
                    name=f"Equity {i}",
                    line=dict(color='gray', width=0.5),
                    opacity=0.1,
                    showlegend=False
                ),
                row=1, col=1
            )
            
        # Drawdown
        for i in range(min(100, n_simulations)):
            fig2.add_trace(
                go.Scatter(
                    y=drawdowns[:, i] * 100,
                    name=f"Drawdown {i}",
                    line=dict(color='red', width=0.5),
                    opacity=0.1,
                    showlegend=False
                ),
                row=2, col=1
            )
            
        fig2.update_layout(
            height=800,
            title="Curva de Equity y Drawdown"
        )
        fig2.update_yaxes(title="Equity ($)", row=1, col=1)
        fig2.update_yaxes(title="Drawdown (%)", row=2, col=1)
        
        st.plotly_chart(fig2)
        st.markdown("""
        **Explicación:** 
        - La gráfica superior muestra la evolución del capital (equity) para cada simulación.
        - La gráfica inferior muestra el drawdown (caída desde máximos) en porcentaje para cada simulación.
        """)
        
        # 3. Distribución de Retornos Finales
        final_values = equity_curves[-1, :]
        final_returns = (final_values - initial_investment) / initial_investment * 100
        
        fig3 = go.Figure()
        fig3.add_trace(go.Histogram(
            x=final_returns,
            nbinsx=50,
            name="Distribución de Retornos"
        ))
        
        fig3.add_vline(
            x=np.median(final_returns),
            line_dash="dash",
            line_color="green",
            annotation_text="Mediana"
        )
        
        fig3.update_layout(title="Distribución de Retornos Finales")
        fig3.update_xaxes(title="Retorno (%)")
        fig3.update_yaxes(title="Frecuencia")
        
        st.plotly_chart(fig3)
        st.markdown("""
        **Explicación:** Este histograma muestra la distribución de los retornos finales posibles 
        después del período simulado. La línea vertical verde representa la mediana de los retornos.
        """)
        
        # Estadísticas
        max_drawdowns = np.min(drawdowns, axis=0) * 100
        stats = pd.DataFrame({
            'Métrica': [
                'Inversión Inicial',
                'Retorno Medio (%)',
                'Retorno Mediano (%)',
                'Drawdown Máximo Medio (%)',
                'Drawdown Máximo Mediano (%)',
                'VaR 95% (%)',
                'Pérdida Máxima Potencial (%)'
            ],
            'Valor': [
                f"${initial_investment:,.2f}",
                f"{np.mean(final_returns):.2f}%",
                f"{np.median(final_returns):.2f}%",
                f"{np.mean(max_drawdowns):.2f}%",
                f"{np.median(max_drawdowns):.2f}%",
                f"{np.percentile(final_returns, 5):.2f}%",
                f"{np.min(final_returns):.2f}%"
            ]
        })
        
        st.table(stats)
        st.markdown("""
        **Explicación de las métricas:**
        - **Inversión Inicial:** Capital inicial invertido
        - **Retorno Medio/Mediano:** Rendimiento promedio/mediano al final del período
        - **Drawdown Máximo Medio/Mediano:** Caída promedio/mediana máxima desde picos
        - **VaR 95%:** Pérdida máxima esperada con 95% de confianza
        - **Pérdida Máxima Potencial:** Peor escenario simulado
        """)
        
        # Intervalos de Confianza
        confidence_levels = [50, 60, 70, 80, 90, 95, 97, 98, 99]
        conf_intervals = pd.DataFrame({
            'Nivel de Confianza (%)': confidence_levels,
            'Retorno Mínimo (%)': [np.percentile(final_returns, (100-x)/2) for x in confidence_levels],
            'Retorno Máximo (%)': [np.percentile(final_returns, 100-(100-x)/2) for x in confidence_levels]
        })
        
        st.write("Intervalos de Confianza para Retornos")
        st.table(conf_intervals)
        st.markdown("""
        **Explicación:** Esta tabla muestra los rangos de retorno esperados para diferentes niveles 
        de confianza. Por ejemplo, con un 95% de confianza, el retorno estará entre el valor mínimo 
        y máximo mostrado en esa fila.
        """)

if __name__ == "__main__":
    main()