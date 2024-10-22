import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from scipy.stats import norm

# Configuración de la página
st.set_page_config(page_title="Portfolio Optimizer", layout="wide")

# Funciones de utilidad
def calculate_metrics(returns, weights, rf_rate):
    port_ret = np.sum(returns.mean() * weights) * 252
    port_vol = np.sqrt(np.dot(weights.T, np.dot(returns.cov() * 252, weights)))
    sharpe = (port_ret - rf_rate) / port_vol
    
    # Calcular VaR y CVaR
    port_returns = returns.dot(weights)
    var_95 = np.percentile(port_returns, 5)
    cvar_95 = port_returns[port_returns <= var_95].mean()
    
    # Maximum Drawdown
    cum_returns = (1 + port_returns).cumprod()
    rolling_max = cum_returns.expanding().max()
    drawdowns = cum_returns/rolling_max - 1
    max_drawdown = drawdowns.min()
    
    return port_ret, port_vol, sharpe, var_95, cvar_95, max_drawdown

def get_stock_data(tickers, start_date, end_date):
    data = pd.DataFrame()
    for ticker in tickers:
        try:
            stock_data = yf.download(ticker, start=start_date, end=end_date)['Adj Close']
            data[ticker] = stock_data
        except:
            st.error(f"Error downloading data for {ticker}")
    return data

# Título y descripción
st.title("📊 Advanced Portfolio Optimizer")
st.markdown("""
This app allows you to simulate and optimize investment portfolios using modern portfolio theory.
Include transaction costs, slippage, and advanced risk metrics.
""")

# Sidebar - Parámetros de entrada
with st.sidebar:
    st.header("Portfolio Parameters")
    
    # Input para tickers
    default_tickers = "AAPL,MSFT,GOOGL,AMZN,JPM"
    tickers_input = st.text_input("Enter stock tickers (comma-separated, max 15):", 
                                 value=default_tickers)
    stocks = [x.strip() for x in tickers_input.split(',')]
    
    if len(stocks) > 15:
        st.error("Maximum 15 stocks allowed")
        stocks = stocks[:15]
    
    # Fechas
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", 
                                  datetime.now() - timedelta(days=365*2))
    with col2:
        end_date = st.date_input("End Date", 
                                datetime.now())
    
    # Parámetros financieros
    initial_capital = st.number_input("Initial Capital ($)", 
                                    min_value=1000, 
                                    value=100000)
    
    rf_rate = st.slider("Risk-free Rate (%)", 
                       min_value=0.0, 
                       max_value=10.0, 
                       value=4.0) / 100
    
    transaction_cost = st.slider("Transaction Cost (%)", 
                               min_value=0.0, 
                               max_value=2.0, 
                               value=0.1) / 100
    
    slippage = st.slider("Slippage (%)", 
                        min_value=0.0, 
                        max_value=1.0, 
                        value=0.1) / 100
    
    num_simulations = st.slider("Number of Simulations", 
                              min_value=100, 
                              max_value=5000, 
                              value=1000)

# Main content
if st.button("Run Optimization"):
    with st.spinner("Downloading stock data and running simulations..."):
        # Obtener datos
        stock_data = get_stock_data(stocks, start_date, end_date)
        returns = stock_data.pct_change().dropna()
        
        if returns.empty:
            st.error("No data available for the selected stocks and date range")
        else:
            # Arrays para almacenar resultados
            all_weights = np.zeros((num_simulations, len(stocks)))
            metrics = np.zeros((num_simulations, 6))  # Ret, Vol, Sharpe, VaR, CVaR, MaxDD
            
            # Simulación Monte Carlo
            for port in range(num_simulations):
                weights = np.random.random(len(stocks))
                weights = weights/np.sum(weights)
                all_weights[port,:] = weights
                
                metrics[port,:] = calculate_metrics(returns, weights, rf_rate)
            
            # Crear DataFrame con resultados
            results = pd.DataFrame(metrics, 
                                 columns=['Return', 'Volatility', 'Sharpe', 
                                        'VaR_95', 'CVaR_95', 'Max_Drawdown'])
            
            # Encontrar portafolio óptimo
            optimal_idx = results['Sharpe'].argmax()
            optimal_weights = all_weights[optimal_idx,:]
            
            # Display results in multiple columns
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.subheader("Optimal Portfolio Metrics")
                metrics_df = pd.DataFrame({
                    'Metric': ['Expected Return', 'Volatility', 'Sharpe Ratio',
                             'VaR (95%)', 'CVaR (95%)', 'Max Drawdown'],
                    'Value': [f"{results.iloc[optimal_idx]['Return']*100:.2f}%",
                             f"{results.iloc[optimal_idx]['Volatility']*100:.2f}%",
                             f"{results.iloc[optimal_idx]['Sharpe']:.2f}",
                             f"{results.iloc[optimal_idx]['VaR_95']*100:.2f}%",
                             f"{results.iloc[optimal_idx]['CVaR_95']*100:.2f}%",
                             f"{results.iloc[optimal_idx]['Max_Drawdown']*100:.2f}%"]
                })
                st.dataframe(metrics_df)
            
            with col2:
                st.subheader("Optimal Weights")
                weights_df = pd.DataFrame({
                    'Stock': stocks,
                    'Weight': [f"{w*100:.2f}%" for w in optimal_weights]
                })
                st.dataframe(weights_df)
            
            with col3:
                st.subheader("Transaction Costs")
                total_cost = initial_capital * (transaction_cost + slippage)
                st.write(f"Transaction Cost: ${total_cost:,.2f}")
                st.write(f"Effective Investment: ${initial_capital-total_cost:,.2f}")
            
            # Visualizaciones
            st.subheader("Portfolio Visualization")
            
            # Efficient Frontier Plot
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=results['Volatility'],
                y=results['Return'],
                mode='markers',
                marker=dict(
                    size=8,
                    color=results['Sharpe'],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="Sharpe Ratio")
                ),
                text=[f"Return: {r:.2%}<br>Vol: {v:.2%}<br>Sharpe: {s:.2f}" 
                      for r,v,s in zip(results['Return'], 
                                     results['Volatility'], 
                                     results['Sharpe'])],
                name="Portfolios"
            ))
            
            # Añadir punto óptimo
            fig.add_trace(go.Scatter(
                x=[results.iloc[optimal_idx]['Volatility']],
                y=[results.iloc[optimal_idx]['Return']],
                mode='markers',
                marker=dict(size=15, color='red', symbol='star'),
                name="Optimal Portfolio"
            ))
            
            fig.update_layout(
                title="Efficient Frontier",
                xaxis_title="Volatility",
                yaxis_title="Expected Return",
                showlegend=True,
                height=600
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Historical Performance
            st.subheader("Historical Performance Analysis")
            portfolio_returns = returns.dot(optimal_weights)
            cumulative_returns = (1 + portfolio_returns).cumprod()
            
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=cumulative_returns.index,
                y=cumulative_returns.values,
                mode='lines',
                name='Portfolio Value'
            ))
            
            fig2.update_layout(
                title="Historical Portfolio Performance",
                xaxis_title="Date",
                yaxis_title="Cumulative Return",
                height=400
            )
            
            st.plotly_chart(fig2, use_container_width=True)
            
            # Drawdown analysis
            rolling_max = cumulative_returns.expanding().max()
            drawdowns = cumulative_returns/rolling_max - 1
            
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(
                x=drawdowns.index,
                y=drawdowns.values,
                fill='tozeroy',
                name='Drawdown'
            ))
            
            fig3.update_layout(
                title="Portfolio Drawdown Analysis",
                xaxis_title="Date",
                yaxis_title="Drawdown",
                height=400
            )
            
            st.plotly_chart(fig3, use_container_width=True)
            
            # Risk Metrics Distribution
            st.subheader("Risk Metrics Distribution")
            col1, col2 = st.columns(2)
            
            with col1:
                fig4 = px.histogram(portfolio_returns, 
                                  title="Daily Returns Distribution",
                                  labels={'value': 'Return', 'count': 'Frequency'})
                st.plotly_chart(fig4, use_container_width=True)
            
            with col2:
                rolling_vol = portfolio_returns.rolling(window=21).std() * np.sqrt(252)
                fig5 = go.Figure()
                fig5.add_trace(go.Scatter(
                    x=rolling_vol.index,
                    y=rolling_vol.values,
                    mode='lines',
                    name='Rolling Volatility'
                ))
                fig5.update_layout(title="21-Day Rolling Volatility")
                st.plotly_chart(fig5, use_container_width=True)