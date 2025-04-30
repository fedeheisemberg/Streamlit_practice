import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import time

# Configuración de la página
st.set_page_config(
    page_title="📊 Monte Carlo Market Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Función para mostrar el footer
# Función para crear el footer
def add_footer():
    footer_html = """
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #0E1117;
        color: #FAFAFA;
        text-align: center;
        padding: 10px;
        font-size: 14px;
        border-top: 1px solid #333;
    }
    </style>
    <div class="footer">
        💼 Made with ❤️ by Fede Martinez - Finanzas & Data
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)

# Funciones para el análisis
def get_stock_data(symbol, start_date, end_date, retries=3, wait=5):
    for attempt in range(retries):
        try:
            stock = yf.download(symbol, start=start_date, end=end_date, progress=False, auto_adjust=False)
            if stock.empty or 'Adj Close' not in stock.columns:
                raise ValueError("No data or missing 'Adj Close'")
            return stock
        except Exception as e:
            st.warning(f"⚠️ Intento {attempt+1} fallido para {symbol}: {e}")
            time.sleep(wait)
    st.error(f"❌ No se pudieron obtener datos para {symbol} tras {retries} intentos.")
    return None


def calculate_transaction_costs(price, shares, commission=0.001, slippage=0.0001):
    """
    Calcula los costos de transacción
    - commission: 0.1% por operación
    - slippage: 0.01% por operación
    """
    commission_cost = price * shares * commission
    slippage_cost = price * shares * slippage
    return commission_cost + slippage_cost

def run_monte_carlo(data, n_simulations, n_days, initial_investment=10000, commission_rate=0.001, slippage_rate=0.0001, transaction_frequency=5):
    """
    Ejecuta simulaciones Monte Carlo para proyectar posibles trayectorias de precios
    y rendimientos de la inversión
    
    Parámetros:
    - data: DataFrame con datos históricos
    - n_simulations: Número de simulaciones a ejecutar
    - n_days: Número de días a proyectar
    - initial_investment: Inversión inicial en USD
    - commission_rate: Tasa de comisión por operación
    - slippage_rate: Tasa de deslizamiento por operación
    - transaction_frequency: Frecuencia promedio de operaciones (en días)
    """
    # Calcular retornos diarios logarítmicos
    returns = np.log(1 + data['Adj Close'].pct_change()).dropna()
    mu = returns.mean()
    sigma = returns.std()
    
    # Inicializar arrays para almacenar resultados
    simulations = np.zeros((n_days, n_simulations))
    equity_curves = np.zeros((n_days, n_simulations))
    drawdowns = np.zeros((n_days, n_simulations))
    
    initial_price = data['Adj Close'].iloc[-1]
    
    for i in range(n_simulations):
        # Generar retornos aleatorios usando distribución normal
        daily_returns = np.random.normal(mu, sigma, n_days)
        
        # Calcular trayectoria de precios (movimiento browniano geométrico)
        price_path = initial_price * np.exp(np.cumsum(daily_returns))
        
        # Calcular equity curve con costos de transacción
        equity = np.zeros(n_days)
        equity[0] = initial_investment
        
        for day in range(1, n_days):
            # Aplicar retorno diario
            equity[day] = equity[day-1] * (1 + np.exp(daily_returns[day]) - 1)
            
            # Aplicar costos de transacción si corresponde
            if day % transaction_frequency == 0:
                transaction_cost = equity[day] * (commission_rate + slippage_rate)
                equity[day] -= transaction_cost
        
        simulations[:, i] = price_path
        equity_curves[:, i] = equity
        
        # Calcular drawdown (caída desde máximos)
        peak = np.maximum.accumulate(equity)
        drawdown = (equity - peak) / peak
        drawdowns[:, i] = drawdown
        
    return simulations, equity_curves, drawdowns

def format_number(num):
    """Formatea números para mejor visualización"""
    if abs(num) >= 1e6:
        return f"{num/1e6:.2f}M"
    elif abs(num) >= 1e3:
        return f"{num/1e3:.2f}K"
    else:
        return f"{num:.2f}"

def display_key_metrics(data, symbol, initial_investment):
    """Muestra métricas clave del activo actual"""
    col1, col2, col3, col4 = st.columns(4)
    
    # Cálculo de métricas
    current_price = data['Adj Close'].iloc[-1]
    change_1d = data['Adj Close'].pct_change().iloc[-1] * 100
    change_30d = (data['Adj Close'].iloc[-1] / data['Adj Close'].iloc[-min(30, len(data))] - 1) * 100
    volume_avg = data['Volume'].mean()
    
    # Mostrar métricas con iconos y colores
    with col1:
        st.metric(
            label=f"💰 Precio Actual ({symbol})",
            value=f"${current_price:.2f}"
        )
    
    with col2:
        st.metric(
            label="📈 Cambio (1 día)",
            value=f"{change_1d:.2f}%",
            delta=f"{change_1d:.2f}%"
        )
    
    with col3:
        st.metric(
            label="📅 Cambio (30 días)",
            value=f"{change_30d:.2f}%",
            delta=f"{change_30d:.2f}%"
        )
    
    with col4:
        st.metric(
            label="💼 Inversión Inicial",
            value=f"${format_number(initial_investment)}"
        )

def main():
    # Título principal con estilo y emojis
    st.markdown("""
    # 📊 Simulador Monte Carlo para Análisis de Inversiones 📈
    """)
    
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #2c3e50;
        text-align: center;
    }
    .subheader {
        font-size: 1.5rem;
        color: #34495e;
        margin-bottom: 20px;
    }
    .highlight {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Introducción
    with st.expander("ℹ️ ¿Qué es la simulación Monte Carlo?", expanded=False):
        st.markdown("""
        ### La Simulación Monte Carlo: Una Herramienta Poderosa para Inversores 🧮
        
        La simulación Monte Carlo es una técnica matemática que permite modelar la incertidumbre en los mercados financieros.
        
        **¿Cómo funciona?** 📝
        1. Analiza los datos históricos para calcular rendimientos y volatilidad
        2. Genera miles de posibles escenarios futuros aleatorios
        3. Permite visualizar un rango de resultados posibles
        4. Ayuda a cuantificar el riesgo y potencial rendimiento
        
        **Beneficios** ✅
        - **Visualiza la incertidumbre**: No sólo un único pronóstico, sino un rango de posibles resultados
        - **Cuantifica el riesgo**: Mide la probabilidad de diversos escenarios
        - **Informa decisiones**: Ayuda a establecer expectativas realistas sobre inversiones
        
        > *"El objetivo de la simulación Monte Carlo no es predecir el futuro con exactitud, sino entender la gama de futuros posibles y sus probabilidades."*
        """)
    
    # Inputs en la barra lateral mejorada
    st.sidebar.markdown("## ⚙️ Parámetros de Simulación")
    
    # Sección de búsqueda de activos con ejemplos
    st.sidebar.markdown("### 🔍 Buscar Activo")
    default_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "SPY", "QQQ", "BTC-USD"]
    selected_default = st.sidebar.selectbox("Ejemplos populares", default_symbols)
    symbol = st.sidebar.text_input("Símbolo de la Acción/ETF/Crypto", value=selected_default)
    
    st.sidebar.markdown("### 📊 Parámetros de Simulación")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        n_simulations = st.number_input("Número de Simulaciones", min_value=100, max_value=10000, value=2000, step=100, 
                                       help="Mayor número = más precisión pero más lento")
    with col2:
        n_days = st.number_input("Días de Pronóstico", min_value=30, max_value=365, value=252, step=30,
                                help="252 días = Aproximadamente 1 año de trading")
    
    st.sidebar.markdown("### 💰 Parámetros de Inversión")
    initial_investment = st.sidebar.number_input("Inversión Inicial ($)", min_value=1000, value=10000, step=1000,
                                               help="Capital inicial para la simulación")
    
    st.sidebar.markdown("### 📅 Período Histórico")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        end_date = datetime.datetime.now()
        end_date = st.date_input("Fecha Final", value=end_date)
    with col2:
        default_start = end_date - datetime.timedelta(days=365)
        start_date = st.date_input("Fecha de Inicio", value=default_start)
    
    # Parámetros avanzados
    with st.sidebar.expander("🔧 Parámetros Avanzados", expanded=False):
        commission_rate = st.slider("Comisión por Operación (%)", min_value=0.0, max_value=0.5, value=0.1, step=0.05) / 100
        slippage_rate = st.slider("Slippage por Operación (%)", min_value=0.0, max_value=0.2, value=0.01, step=0.01) / 100
        transaction_frequency = st.slider("Frecuencia de Operaciones (días)", min_value=1, max_value=30, value=5)
    
    run_button = st.sidebar.button("🚀 Ejecutar Análisis", use_container_width=True)
    
    if run_button:
        # Obtener datos
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("⏳ Obteniendo datos del mercado...")
        progress_bar.progress(10)
        
        data = get_stock_data(symbol, start_date, end_date)
        
        if data is None or data.empty:
            st.error(f"❌ No se encontraron datos para el símbolo {symbol}. Verifica que sea un símbolo válido y que existan datos para el período seleccionado.")
        else:
            # Mostrar métricas clave
            display_key_metrics(data, symbol, initial_investment)
            
            # Actualizar barra de progreso
            progress_bar.progress(30)
            status_text.text("🧮 Ejecutando simulaciones Monte Carlo...")
            
            # Ejecutar simulación
            simulations, equity_curves, drawdowns = run_monte_carlo(
                data, n_simulations, n_days, initial_investment, 
                commission_rate, slippage_rate, transaction_frequency
            )
            
            # Actualizar progreso
            progress_bar.progress(70)
            status_text.text("📊 Generando visualizaciones...")
            
            # 1. Gráfico de Simulaciones Monte Carlo mejorado
            st.markdown("## 📈 Proyección de Precios con Monte Carlo")
            
            # Crear bandas de confianza
            percentiles = [5, 25, 50, 75, 95]
            percentile_values = np.percentile(simulations, percentiles, axis=1).T
            
            fig1 = go.Figure()
            
            # Datos históricos
            fig1.add_trace(go.Scatter(
                x=data.index,
                y=data['Adj Close'],
                name="Histórico",
                line=dict(color='blue', width=3)
            ))
            
            # Simulaciones de fondo (solo algunas para no saturar)
            for i in range(min(50, n_simulations)):
                if i % 5 == 0:  # Mostrar solo una fracción para no saturar
                    fig1.add_trace(go.Scatter(
                        x=pd.date_range(start=data.index[-1], periods=n_days, freq='B'),
                        y=simulations[:, i],
                        name=f"Sim {i}",
                        line=dict(color='rgba(169, 169, 169, 0.2)', width=1),
                        showlegend=False
                    ))
            
            # Bandas de confianza
            band_colors = ['rgba(255,0,0,0.2)', 'rgba(255,165,0,0.3)', 'rgba(46,139,87,0.4)']
            band_names = ['90% (5%-95%)', '50% (25%-75%)', 'Mediana']
            
            # Añadir cada banda
            fig1.add_trace(go.Scatter(
                x=pd.date_range(start=data.index[-1], periods=n_days, freq='B'),
                y=percentile_values[:, 4],  # 95th percentile
                name=band_names[0],
                line=dict(color='red', width=0),
                showlegend=True
            ))
            
            fig1.add_trace(go.Scatter(
                x=pd.date_range(start=data.index[-1], periods=n_days, freq='B'),
                y=percentile_values[:, 0],  # 5th percentile
                name=band_names[0],
                line=dict(color='red', width=0),
                fill='tonexty',
                fillcolor=band_colors[0],
                showlegend=False
            ))
            
            fig1.add_trace(go.Scatter(
                x=pd.date_range(start=data.index[-1], periods=n_days, freq='B'),
                y=percentile_values[:, 3],  # 75th percentile
                name=band_names[1],
                line=dict(color='orange', width=0),
                showlegend=True
            ))
            
            fig1.add_trace(go.Scatter(
                x=pd.date_range(start=data.index[-1], periods=n_days, freq='B'),
                y=percentile_values[:, 1],  # 25th percentile
                name=band_names[1],
                line=dict(color='orange', width=0),
                fill='tonexty',
                fillcolor=band_colors[1],
                showlegend=False
            ))
            
            fig1.add_trace(go.Scatter(
                x=pd.date_range(start=data.index[-1], periods=n_days, freq='B'),
                y=percentile_values[:, 2],  # 50th percentile (median)
                name=band_names[2],
                line=dict(color='green', width=2),
                showlegend=True
            ))
            
            # Mejorar el diseño
            fig1.update_layout(
                title=f"Proyección de Precios para {symbol} - {n_simulations} Simulaciones",
                yaxis_title="Precio ($)",
                xaxis_title="Fecha",
                legend_title="Elementos:",
                template="plotly_white",
                height=500,
                hovermode="x unified"
            )
            
            # Añadir una anotación que explique las bandas
            fig1.add_annotation(
                x=0.5, y=-0.15,
                xref="paper", yref="paper",
                text="Las bandas de confianza muestran los rangos de precios probables en diferentes percentiles",
                showarrow=False,
                font=dict(size=12)
            )
            
            st.plotly_chart(fig1, use_container_width=True)
            
            with st.expander("📝 Explicación: Proyección de Precios", expanded=True):
                st.markdown("""
                ### 🎯 Interpretación del Gráfico de Proyección
                
                Este gráfico muestra las posibles trayectorias futuras del precio de **{symbol}** basadas en sus características históricas de volatilidad y rendimiento.
                
                **Elementos principales:**
                
                - **Línea azul**: Precios históricos reales
                - **Línea verde**: Mediana de todas las simulaciones (resultado central esperado)
                - **Banda naranja**: Muestra el rango donde esperamos que el precio se mantenga con un 50% de probabilidad
                - **Banda roja**: Muestra el rango donde esperamos que el precio se mantenga con un 90% de probabilidad
                - **Líneas grises**: Muestras de trayectorias individuales simuladas
                
                **¿Cómo interpretarlo?** 📊
                
                - Cuanto más amplio sea el cono de proyección, mayor incertidumbre existe sobre el precio futuro
                - La mediana (línea verde) representa el "camino más probable" basado en las simulaciones
                - Las bandas exteriores representan escenarios más extremos pero posibles
                
                > **Nota:** Esta proyección no es una predicción exacta sino una representación estadística de posibles escenarios basados en el comportamiento histórico.
                """.format(symbol=symbol))
            
            # 2. Curva de Equity y Drawdown mejorada
            st.markdown("## 💰 Rendimiento de la Inversión")
            
            # Calcular bandas de confianza para equity
            equity_percentiles = np.percentile(equity_curves, percentiles, axis=1).T
            
            fig2 = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                vertical_spacing=0.1,
                                subplot_titles=("Proyección de Capital ($)", "Drawdown Potencial (%)"))
            
            # Equity Curves percentiles
            # 95th percentile
            fig2.add_trace(
                go.Scatter(
                    x=pd.date_range(start=data.index[-1], periods=n_days, freq='B'),
                    y=equity_percentiles[:, 4],
                    name="Percentil 95%",
                    line=dict(color='rgba(0,128,0,0.7)', width=0)
                ),
                row=1, col=1
            )
            
            # 5th percentile
            fig2.add_trace(
                go.Scatter(
                    x=pd.date_range(start=data.index[-1], periods=n_days, freq='B'),
                    y=equity_percentiles[:, 0],
                    name="Percentil 5%",
                    line=dict(color='rgba(0,128,0,0.7)', width=0),
                    fill='tonexty',
                    fillcolor='rgba(0,128,0,0.2)'
                ),
                row=1, col=1
            )
            
            # Median
            fig2.add_trace(
                go.Scatter(
                    x=pd.date_range(start=data.index[-1], periods=n_days, freq='B'),
                    y=equity_percentiles[:, 2],
                    name="Mediana",
                    line=dict(color='green', width=2)
                ),
                row=1, col=1
            )
            
            # Initial investment line
            fig2.add_trace(
                go.Scatter(
                    x=pd.date_range(start=data.index[-1], periods=n_days, freq='B'),
                    y=[initial_investment] * n_days,
                    name="Inversión Inicial",
                    line=dict(color='black', width=1, dash='dash')
                ),
                row=1, col=1
            )
            
            # Drawdown
            drawdown_percentiles = np.percentile(drawdowns, [5, 50, 95], axis=1).T
            
            fig2.add_trace(
                go.Scatter(
                    x=pd.date_range(start=data.index[-1], periods=n_days, freq='B'),
                    y=drawdown_percentiles[:, 0] * 100,  # 5th percentile (worst drawdowns)
                    name="Peor Drawdown (5%)",
                    line=dict(color='red', width=2)
                ),
                row=2, col=1
            )
            
            fig2.add_trace(
                go.Scatter(
                    x=pd.date_range(start=data.index[-1], periods=n_days, freq='B'),
                    y=drawdown_percentiles[:, 1] * 100,  # Median
                    name="Drawdown Mediano",
                    line=dict(color='orange', width=2)
                ),
                row=2, col=1
            )
            
            # Líneas de referencia para drawdown
            for level in [-5, -10, -20]:
                fig2.add_shape(
                    type="line",
                    x0=pd.date_range(start=data.index[-1], periods=n_days, freq='B')[0],
                    y0=level,
                    x1=pd.date_range(start=data.index[-1], periods=n_days, freq='B')[-1],
                    y1=level,
                    line=dict(color="gray", width=1, dash="dot"),
                    row=2, col=1
                )
                
                # Añadir etiqueta
                fig2.add_annotation(
                    x=pd.date_range(start=data.index[-1], periods=n_days, freq='B')[-1],
                    y=level,
                    text=f"{level}%",
                    showarrow=False,
                    xshift=10,
                    font=dict(size=10, color="gray"),
                    row=2, col=1
                )
            
            fig2.update_layout(
                height=700,
                template="plotly_white",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                hovermode="x unified"
            )
            
            fig2.update_yaxes(title="Capital ($)", row=1, col=1)
            fig2.update_yaxes(title="Drawdown (%)", row=2, col=1)
            fig2.update_xaxes(title="Fecha", row=2, col=1)
            
            st.plotly_chart(fig2, use_container_width=True)
            
            with st.expander("📝 Explicación: Rendimiento y Drawdown", expanded=True):
                st.markdown("""
                ### 📊 Interpretación de los Gráficos de Rendimiento
                
                #### Gráfico Superior: Proyección de Capital 💰
                
                Este gráfico muestra cómo podría evolucionar tu inversión inicial de **${:,.2f}** en el tiempo:
                
                - **Línea verde sólida**: Representa la mediana (resultado central esperado)
                - **Área verde clara**: Muestra el rango de resultados entre el percentil 5% y 95%
                - **Línea negra punteada**: Marca tu inversión inicial
                
                #### Gráfico Inferior: Drawdown Potencial 📉
                
                El drawdown mide la caída desde un pico previo hasta un valle, representando pérdidas temporales:
                
                - **Línea roja**: Muestra el peor drawdown esperado (percentil 5%)
                - **Línea naranja**: Muestra el drawdown mediano esperado
                - **Líneas horizontales**: Referencias de niveles de drawdown comunes (-5%, -10%, -20%)
                
                **¿Por qué es importante?** 🤔
                
                - Te ayuda a entender no solo el rendimiento final sino también la volatilidad durante el camino
                - Te permite prepararte psicológicamente para las fluctuaciones naturales del mercado
                - Te ofrece expectativas realistas sobre posibles caídas temporales
                
                > **Consejo:** Los inversores exitosos tienen expectativas realistas sobre los drawdowns y no entran en pánico durante caídas temporales que están dentro de los rangos esperados.
                """.format(initial_investment))
            
            # 3. Distribución de Retornos Finales mejorada
            st.markdown("## 📊 Distribución de Resultados Finales")
            
            # Calcular valores finales y retornos
            final_values = equity_curves[-1, :]
            final_returns = (final_values - initial_investment) / initial_investment * 100
            
            # Preparar datos para el histograma - agregar KDE
            profit_mask = final_returns >= 0
            loss_mask = final_returns < 0
            
            fig3 = go.Figure()
            
            # Histograma de ganancias (verde)
            fig3.add_trace(go.Histogram(
                x=final_returns[profit_mask],
                nbinsx=40,
                name="Ganancias",
                marker=dict(color='rgba(0,128,0,0.7)'),
                opacity=0.7
            ))
            
            # Histograma de pérdidas (rojo)
            fig3.add_trace(go.Histogram(
                x=final_returns[loss_mask],
                nbinsx=40,
                name="Pérdidas",
                marker=dict(color='rgba(255,0,0,0.7)'),
                opacity=0.7
            ))
            
            # Líneas de referencia
            fig3.add_vline(
                x=np.median(final_returns),
                line_dash="solid",
                line_color="green",
                line_width=2,
                annotation_text=f"Mediana: {np.median(final_returns):.2f}%",
                annotation_position="top right"
            )
            
            fig3.add_vline(
                x=np.mean(final_returns),
                line_dash="dash",
                line_color="blue",
                line_width=2,
                annotation_text=f"Media: {np.mean(final_returns):.2f}%",
                annotation_position="top left"
            )
            
            fig3.add_vline(
                x=np.percentile(final_returns, 5),
                line_dash="dot",
                line_color="red",
                line_width=2,
                annotation_text=f"VAR(95%): {np.percentile(final_returns, 5):.2f}%",
                annotation_position="bottom left"
            )
            
            fig3.update_layout(
                title=f"Distribución de Retornos Finales Después de {n_days} Días",
                xaxis_title="Retorno (%)",
                yaxis_title="Frecuencia",
                barmode='overlay',
                template="plotly_white",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            st.plotly_chart(fig3, use_container_width=True)
            
            with st.expander("📝 Explicación: Distribución de Resultados", expanded=True):
                st.markdown("""
                ### 📊 Interpretación de la Distribución de Resultados
                
                Este histograma muestra la distribución de todos los posibles retornos finales después del período simulado:
                
                - **Barras verdes**: Representan escenarios con ganancias
                - **Barras rojas**: Representan escenarios con pérdidas
                - **Línea verde sólida**: Marca la mediana de todos los retornos simulados
                - **Línea azul punteada**: Marca la media de todos los retornos simulados
                - **Línea roja punteada**: Marca el Valor en Riesgo (VaR) al 95% - el peor resultado esperado con 95% de confianza
                
                **¿Cómo interpretarlo?** 🧐
                
                - La forma del histograma muestra la dispersión y probabilidad de diferentes resultados
                - Un histograma más concentrado indica menor incertidumbre
                - Un histograma más extendido indica mayor variabilidad en los resultados posibles
                
                **Preguntas clave:**
                - ¿Cuál es la probabilidad de obtener un retorno positivo?
                - ¿Cuál es la pérdida máxima que podría esperar con 95% de confianza?
                - ¿Están mis expectativas de retorno alineadas con esta distribución?
                
                > **Nota:** Esta simulación considera costos de transacción de {:.2f}% por operación y slippage de {:.2f}%, con operaciones cada {} días en promedio.
                """.format(commission_rate*100, slippage_rate*100, transaction_frequency))
            
            # Estadísticas y métricas
            st.markdown("## 📈 Estadísticas de Rendimiento y Riesgo")
            
            # Crear columnas para las métricas
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 💵 Métricas de Rendimiento")
                
                max_drawdowns = np.min(drawdowns, axis=0) * 100
                prob_profit = np.mean(final_returns > 0) * 100
                sharpe = np.mean(final_returns) / np.std(final_returns) if np.std(final_returns) > 0 else 0
                
                stats1 = pd.DataFrame({
                    'Métrica': [
                        '💰 Inversión Inicial',
                        '📊 Retorno Medio',
                        '📊 Retorno Mediano',
                        '📈 Valor Final Medio',
                        '🎯 Valor Final Mediano',
                        '🍀 Probabilidad de Ganancia',
                        '📑 Ratio Sharpe Estimado'
                    ],
                    'Valor': [
                        f"${initial_investment:,.2f}",
                        f"{np.mean(final_returns):.2f}%",
                        f"{np.median(final_returns):.2f}%",
                        f"${np.mean(final_values):,.2f}",
                        f"${np.median(final_values):,.2f}",
                        f"{prob_profit:.1f}%",
                        f"{sharpe:.2f}"
                    ]
                })
                
                st.table(stats1)
                
                st.markdown("""
                **Explicación:**
                - **Retorno Medio/Mediano**: Rendimiento promedio/mediano al final del período
                - **Valor Final Medio/Mediano**: Capital estimado al final del período
                - **Probabilidad de Ganancia**: % de simulaciones con resultado positivo
                - **Ratio Sharpe**: Proporción entre rendimiento y riesgo (mayor = mejor)
                """)
            
            with col2:
                st.markdown("### 📉 Métricas de Riesgo")
                
                stats2 = pd.DataFrame({
                    'Métrica': [
                        '📉 Drawdown Máximo Medio',
                        '📉 Drawdown Máximo Mediano',
                        '⚠️ VaR 95%',
                        '⚠️ VaR 99%',
                        '💥 Pérdida Máxima Potencial',
                        '🔄 Volatilidad Estimada',
                        '📊 Coeficiente de Variación'
                    ],
                    'Valor': [
                        f"{np.mean(max_drawdowns):.2f}%",
                        f"{np.median(max_drawdowns):.2f}%",
                        f"{np.percentile(final_returns, 5):.2f}%",
                        f"{np.percentile(final_returns, 1):.2f}%",
                        f"{np.min(final_returns):.2f}%",
                        f"{np.std(final_returns):.2f}%",
                        f"{np.std(final_returns)/np.mean(final_returns) if np.mean(final_returns) != 0 else 0:.2f}"
                    ]
                })
                
                st.table(stats2)
                
                st.markdown("""
                **Explicación:**
                - **Drawdown Máximo**: Caída promedio/mediana máxima desde picos
                - **VaR 95%/99%**: Pérdida máxima esperada con 95%/99% de confianza
                - **Pérdida Máxima Potencial**: Peor escenario simulado
                - **Volatilidad**: Desviación estándar de los retornos
                - **Coeficiente de Variación**: Relación entre volatilidad y retorno medio
                """)
            
            # Intervalos de Confianza mejorados
            st.markdown("### 📊 Intervalos de Confianza")
            
            # Crear visualización mejorada para intervalos de confianza
            confidence_levels = [50, 75, 90, 95, 99]
            conf_intervals = pd.DataFrame({
                'Nivel de Confianza (%)': confidence_levels,
                'Retorno Mínimo (%)': [np.percentile(final_returns, (100-x)/2) for x in confidence_levels],
                'Retorno Máximo (%)': [np.percentile(final_returns, 100-(100-x)/2) for x in confidence_levels],
                'Valor Final Mínimo ($)': [initial_investment * (1 + np.percentile(final_returns, (100-x)/2)/100) for x in confidence_levels],
                'Valor Final Máximo ($)': [initial_investment * (1 + np.percentile(final_returns, 100-(100-x)/2)/100) for x in confidence_levels]
            })
            
            # Visualización de intervalos de confianza
            fig4 = go.Figure()
            
            for i, conf in enumerate(confidence_levels):
                min_ret = conf_intervals.loc[i, 'Retorno Mínimo (%)']
                max_ret = conf_intervals.loc[i, 'Retorno Máximo (%)']
                
                # Añadir barras horizontales para cada nivel de confianza
                fig4.add_trace(go.Scatter(
                    x=[min_ret, max_ret],
                    y=[conf, conf],
                    mode='lines',
                    line=dict(color='rgba(0,0,255,0.7)', width=10-(i*1.5)),
                    name=f"{conf}% de confianza"
                ))
                
                # Añadir etiquetas en los extremos
                fig4.add_annotation(
                    x=min_ret,
                    y=conf,
                    text=f"{min_ret:.1f}%",
                    showarrow=False,
                    xshift=-40,
                    font=dict(size=10)
                )
                
                fig4.add_annotation(
                    x=max_ret,
                    y=conf,
                    text=f"{max_ret:.1f}%",
                    showarrow=False,
                    xshift=40,
                    font=dict(size=10)
                )
            
            # Línea vertical en 0%
            fig4.add_vline(
                x=0,
                line_dash="dash",
                line_color="black",
                line_width=1,
                annotation_text="0%",
                annotation_position="top"
            )
            
            fig4.update_layout(
                title="Intervalos de Confianza para Retornos",
                xaxis_title="Retorno (%)",
                yaxis_title="Nivel de Confianza (%)",
                template="plotly_white",
                height=400,
                xaxis=dict(
                    zeroline=True,
                    zerolinewidth=1,
                    zerolinecolor='black'
                )
            )
            
            st.plotly_chart(fig4, use_container_width=True)
            
            with st.expander("📝 Explicación: Intervalos de Confianza", expanded=True):
                st.markdown("""
                ### 🎯 Interpretación de los Intervalos de Confianza
                
                Este gráfico muestra los rangos de retornos esperados para diferentes niveles de confianza estadística:
                
                **¿Cómo interpretarlo?** 📊
                
                - Las barras horizontales representan el rango de retornos esperados para cada nivel de confianza
                - Barras más anchas indican mayor certeza estadística
                - Por ejemplo, con un 95% de confianza, el retorno se encontrará entre los valores mostrados en esa barra
                
                **Aplicación práctica:** 💼
                
                - Utiliza el nivel de confianza que mejor se adapte a tu tolerancia al riesgo
                - Para decisiones conservadoras, considera el límite inferior del intervalo de 95% o 99%
                - Para planificación equilibrada, considera el rango del intervalo de 50% o 75%
                
                > **Consejo:** Un inversor prudente debería planificar para el escenario del límite inferior del intervalo de confianza que corresponda a su tolerancia al riesgo.
                """)
            
            # Sección de conclusiones y recomendaciones
            st.markdown("## 🧠 Conclusiones y Recomendaciones")
            
            # Determinar recomendaciones basadas en los resultados
            mean_return = np.mean(final_returns)
            risk_level = np.std(final_returns)
            sharpe_ratio = mean_return / risk_level if risk_level > 0 else 0
            var_95 = np.percentile(final_returns, 5)
            max_dd = np.mean(max_drawdowns)
            
            # Clasificar según métricas
            risk_category = "bajo" if risk_level < 10 else "moderado" if risk_level < 20 else "alto"
            sharpe_category = "excelente" if sharpe_ratio > 1 else "bueno" if sharpe_ratio > 0.5 else "aceptable" if sharpe_ratio > 0 else "deficiente"
            return_category = "positivo" if mean_return > 0 else "negativo"
            
            recommendations = []
            
            if mean_return > 0 and sharpe_ratio > 0.5:
                recommendations.append("✅ Los resultados sugieren un perfil favorable de riesgo-rendimiento para esta inversión.")
            elif mean_return > 0:
                recommendations.append("⚠️ Rendimiento positivo esperado pero con volatilidad significativa.")
            else:
                recommendations.append("❌ Los resultados sugieren un rendimiento esperado negativo.")
                
            if var_95 < -20:
                recommendations.append("⚠️ Alta probabilidad de pérdidas significativas (>20%). Considere diversificar.")
            
            if max_dd > 30:
                recommendations.append("⚠️ Drawdowns potencialmente severos. Evalúe su tolerancia a pérdidas temporales significativas.")
            
            if prob_profit < 60:
                recommendations.append("⚠️ La probabilidad de obtener beneficios es menor al 60%. Considere alternativas de inversión.")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"""
                ### Resumen de {symbol} - Proyección a {n_days} días
                
                Basado en {n_simulations} simulaciones Monte Carlo, podemos concluir:
                
                - **Rendimiento esperado: {return_category.upper()}** con un retorno medio proyectado de {mean_return:.2f}%
                - **Nivel de riesgo: {risk_category.upper()}** con una volatilidad de {risk_level:.2f}%
                - **Ratio riesgo-rendimiento: {sharpe_category.upper()}** con un Sharpe Ratio de {sharpe_ratio:.2f}
                - **Probabilidad de ganancia: {prob_profit:.1f}%**
                
                **Recomendaciones:**
                
                {chr(10).join(recommendations)}
                
                > **Recuerde:** Las simulaciones Monte Carlo son herramientas de análisis, no predicciones exactas. Los resultados reales pueden variar.
                """)
            
            with col2:
                # Mostrar un medidor visual de riesgo/rendimiento
                fig5 = go.Figure(go.Indicator(
                    mode = "gauge+number+delta",
                    value = sharpe_ratio,
                    title = {'text': "Ratio Sharpe"},
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    gauge = {
                        'axis': {'range': [-0.5, 2], 'tickwidth': 1},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [-0.5, 0], 'color': "red"},
                            {'range': [0, 0.5], 'color': "orange"},
                            {'range': [0.5, 1], 'color': "yellow"},
                            {'range': [1, 2], 'color': "green"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 0.5
                        }
                    }
                ))
                
                fig5.update_layout(height=300)
                st.plotly_chart(fig5, use_container_width=True)
                
                # Probabilidad de ganancia vs pérdida
                labels = ['Ganancia', 'Pérdida']
                values = [prob_profit, 100-prob_profit]
                colors = ['green', 'red']
                
                fig6 = go.Figure(data=[go.Pie(
                    labels=labels, 
                    values=values,
                    hole=.3,
                    marker=dict(colors=colors)
                )])
                
                fig6.update_layout(
                    title="Probabilidad de Resultado",
                    height=300
                )
                
                st.plotly_chart(fig6, use_container_width=True)
            
            # Limpiar indicadores de progreso
            progress_bar.empty()
            status_text.empty()
    
    # Sección de información educativa
    st.markdown("---")
    with st.expander("📚 Recursos Educativos", expanded=False):
        st.markdown("""
        ### 📖 Recursos para Aprender Más Sobre Simulaciones Monte Carlo
        
        #### 📊 ¿Por qué utilizar simulaciones Monte Carlo en inversiones?
        
        Las simulaciones Monte Carlo son herramientas poderosas para la planificación financiera porque:
        
        1. **Capturan la incertidumbre** - No se limitan a un único escenario "promedio"
        2. **Modelan la aleatoriedad** - Reflejan la naturaleza impredecible de los mercados
        3. **Cuantifican el riesgo** - Permiten entender la probabilidad de diferentes resultados
        4. **Mejoran la toma de decisiones** - Proporcionan una visión más completa de posibles escenarios
        
        #### 📚 Recursos Recomendados
        
        **Libros:**
        - "Monte Carlo Simulation and Finance" por Don L. McLeish
        - "Financial Risk Forecasting" por Jon Danielsson
        
        **Cursos Online:**
        - "Financial Engineering and Risk Management" (Coursera)
        - "Introduction to Portfolio Construction and Analysis with Python" (Coursera)
        
        **Blogs y Sitios Web:**
        - Quantopian Blog
        - QuantStart
        - Towards Data Science (artículos sobre finanzas cuantitativas)
        """)
    
    # Footer
    add_footer()

if __name__ == "__main__":
    main()