import streamlit as st
import pandas as pd
import base64
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import requests
import time
import json
from datetime import datetime, timedelta

# Configuración de la página
st.set_page_config(page_title="Dashboard Stock Analysis", layout="wide")

# Crear título
st.title("Dashboard de Análisis Fundamental - Stock Analysis")

st.markdown("""
Este dashboard proporciona un análisis fundamental completo de las empresas del S&P 500, incluyendo métricas clave y visualizaciones interactivas.
* **Fuentes de datos:** Wikipedia, Yahoo Finance, Alpha Vantage
* **Bibliotecas:** streamlit, pandas, numpy, plotly, yfinance
""")

# Función para cargar datos del S&P 500 con manejo de errores
@st.cache_data(ttl=3600)  # Caché por 1 hora
def load_data():
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        html = pd.read_html(url, header=0)
        df = html[0]
        return df
    except Exception as e:
        st.error(f"Error al cargar datos del S&P 500: {e}")
        # Proporcionar un dataset mínimo de respaldo
        return pd.DataFrame({
            'Symbol': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META'],
            'Security': ['Apple Inc.', 'Microsoft Corp.', 'Alphabet Inc.', 'Amazon.com Inc.', 'Meta Platforms Inc.'],
            'GICS Sector': ['Information Technology', 'Information Technology', 'Communication Services', 'Consumer Discretionary', 'Communication Services']
        })

# Función para obtener datos fundamentales de Yahoo Finance con reintentos y manejo de errores
@st.cache_data(ttl=3600)  # Caché por 1 hora
def get_fundamental_data(ticker):
    # Valores predeterminados en caso de error
    default_data = {
        'longName': ticker,
        'currentPrice': 0,
        'marketCap': 0,
        'sector': 'N/A',
        'trailingPE': 0,
        'pegRatio': 0,
        'priceToBook': 0,
        'enterpriseToEbitda': 0,
        'profitMargins': 0,
        'returnOnEquity': 0,
        'returnOnAssets': 0,
        'dividendYield': 0,
        'payoutRatio': 0,
        'debtToEquity': 0,
        'currentRatio': 0,
        'freeCashflow': 0
    }
    
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            # Comprobamos que hayamos obtenido datos válidos
            if 'longName' in info:
                return info
            time.sleep(retry_delay)
        except Exception as e:
            if attempt < max_retries - 1:
                st.warning(f"Reintento {attempt+1}/{max_retries} para {ticker}...")
                time.sleep(retry_delay)
            else:
                st.error(f"Error al obtener datos de Yahoo Finance para {ticker}: {e}")
    
    return default_data

# Función para obtener datos de Alpha Vantage con manejo de errores
@st.cache_data(ttl=3600)  # Caché por 1 hora
def get_alpha_vantage_data(symbol):
    default_data = {
        'QuarterlyRevenueGrowthYOY': '0',
        'QuarterlyEarningsGrowthYOY': '0'
    }
    
    try:
        api_key = '9RQZ699U0PT6NTHN'  # Nota: en producción, usar st.secrets
        url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={api_key}'
        r = requests.get(url, timeout=10)
        data = r.json()
        
        # Verificar si recibimos datos válidos
        if data and not 'Error Message' in data:
            return data
        else:
            st.warning(f"No se pudieron obtener datos de Alpha Vantage para {symbol}")
            return default_data
    except Exception as e:
        st.error(f"Error en la solicitud a Alpha Vantage: {e}")
        return default_data

# Función para obtener datos históricos con manejo de errores
@st.cache_data(ttl=3600)
def get_stock_data(ticker, period="1y"):
    try:
        data = yf.download(ticker, period=period, progress=False, auto_adjust=False)
        if data.empty:
            raise ValueError("No se obtuvieron datos históricos")
        return data
    except Exception as e:
        st.error(f"Error al obtener datos históricos para {ticker}: {e}")
        # Crear datos históricos ficticios para mantener la aplicación funcionando
        end = datetime.now()
        start = end - timedelta(days=365)
        dates = pd.date_range(start=start, end=end, freq='B')
        
        # Crear un DataFrame con precios simulados
        data = pd.DataFrame(index=dates)
        data['Open'] = np.random.normal(100, 5, len(dates))
        data['High'] = data['Open'] + abs(np.random.normal(0, 2, len(dates)))
        data['Low'] = data['Open'] - abs(np.random.normal(0, 2, len(dates)))
        data['Close'] = data['Open'] + np.random.normal(0, 1, len(dates))
        data['Volume'] = np.random.randint(1000000, 10000000, len(dates))
        
        st.warning("⚠️ Mostrando datos simulados. Los datos reales no están disponibles actualmente.")
        return data

# Cargar datos del S&P 500
df = load_data()
sector = df.groupby('GICS Sector')

# Barra lateral - Selección de sector y empresa
st.sidebar.header('Filtros')
sorted_sector_unique = sorted(df['GICS Sector'].unique())
selected_sector = st.sidebar.multiselect('Sector', sorted_sector_unique, default=sorted_sector_unique[0])

# Filtrado de datos por sector
if not selected_sector:
    st.warning("Por favor, selecciona al menos un sector.")
    df_selected_sector = df
else:
    df_selected_sector = df[df['GICS Sector'].isin(selected_sector)]

# Selección de empresa
selected_company = st.sidebar.selectbox('Empresa', df_selected_sector['Symbol'].tolist())

# Añadir un menú para mostrar diferentes tipos de análisis
analysis_type = st.sidebar.radio(
    "Tipo de Análisis",
    ["Visión General", "Métricas de Valoración", "Análisis de Rentabilidad", "Salud Financiera"]
)

# Añadir botón para refrescar datos
if st.sidebar.button('Refrescar Datos'):
    st.cache_data.clear()
    st.experimental_rerun()

# Mostrar información sobre limitaciones de API
st.sidebar.markdown("---")
st.sidebar.info("ℹ️ **Nota:** Las APIs gratuitas tienen límites de solicitudes. Si no ves datos, prueba a refrescar o cambiar de empresa.")

# Obtener datos fundamentales con manejo de errores
with st.spinner('Cargando datos fundamentales...'):
    fundamental_data = get_fundamental_data(selected_company)
    alpha_vantage_data = get_alpha_vantage_data(selected_company)

# Información general de la empresa (siempre visible)
st.header(f"Información General de {fundamental_data.get('longName', selected_company)}")

col1, col2, col3 = st.columns(3)
with col1:
    price = fundamental_data.get('currentPrice', 'N/A')
    if price != 'N/A':
        st.metric("Precio Actual", f"${price:.2f}")
    else:
        st.metric("Precio Actual", "N/A")
        
with col2:
    market_cap = fundamental_data.get('marketCap', 'N/A')
    if market_cap not in ['N/A', 0]:
        # Formatear para mostrar en miles de millones si es grande
        if market_cap > 1_000_000_000:
            market_cap_str = f"${market_cap/1_000_000_000:.2f}B"
        else:
            market_cap_str = f"${market_cap:,}"
        st.metric("Capitalización de Mercado", market_cap_str)
    else:
        st.metric("Capitalización de Mercado", "N/A")
        
with col3:
    st.metric("Sector", fundamental_data.get('sector', 'N/A'))

# Función para crear gráfico de velas
def create_candlestick_chart(ticker):
    data = get_stock_data(ticker)
    fig = go.Figure(data=[go.Candlestick(x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                increasing_line_color='green',
                decreasing_line_color='red')])
    fig.update_layout(title=f'Gráfico de Velas de {ticker} - Último Año',
                      xaxis_title='Fecha',
                      yaxis_title='Precio',
                      height=500)
    return fig

# Mostrar gráfico de velas
st.plotly_chart(create_candlestick_chart(selected_company), use_container_width=True)

# Mostrar diferentes secciones según el tipo de análisis seleccionado
if analysis_type == "Visión General":
    # Crear gráfico de volumen
    data = get_stock_data(selected_company)
    
    # Calcular medias móviles
    data['MA20'] = data['Close'].rolling(window=20).mean()
    data['MA50'] = data['Close'].rolling(window=50).mean()
    data['MA200'] = data['Close'].rolling(window=200).mean()
    
    # Crear figura con dos subplots
    fig = go.Figure()
    
    # Añadir precio de cierre
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Precio de Cierre', line=dict(color='blue')))
    
    # Añadir medias móviles
    fig.add_trace(go.Scatter(x=data.index, y=data['MA20'], name='Media Móvil 20 días', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=data.index, y=data['MA50'], name='Media Móvil 50 días', line=dict(color='green')))
    fig.add_trace(go.Scatter(x=data.index, y=data['MA200'], name='Media Móvil 200 días', line=dict(color='red')))
    
    fig.update_layout(title=f'Análisis Técnico de {selected_company} - Último Año',
                      xaxis_title='Fecha',
                      yaxis_title='Precio',
                      height=500)
    
    st.subheader("Análisis Técnico")
    st.plotly_chart(fig, use_container_width=True)
    
    # Explicación del análisis técnico
    st.markdown("""
    **Interpretación del Análisis Técnico:**
    * **Media Móvil de 20 días (naranja)**: Tendencia a corto plazo
    * **Media Móvil de 50 días (verde)**: Tendencia a medio plazo
    * **Media Móvil de 200 días (roja)**: Tendencia a largo plazo
    
    Cuando la media móvil a corto plazo cruza por encima de la media móvil a largo plazo, se considera una señal alcista (Golden Cross).
    Cuando la media móvil a corto plazo cruza por debajo de la media móvil a largo plazo, se considera una señal bajista (Death Cross).
    """)

elif analysis_type == "Métricas de Valoración":
    st.header("Métricas de Valoración")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("P/E Ratio", fundamental_data.get('trailingPE', 'N/A'))
        st.markdown("**Interpretación:** Compara el precio de la acción con las ganancias por acción. Un P/E más bajo puede indicar que la acción está subvalorada.")
    with col2:
        st.metric("PEG Ratio", fundamental_data.get('pegRatio', 'N/A'))
        st.markdown("**Interpretación:** Relaciona el P/E con el crecimiento esperado. Un PEG cercano a 1 puede indicar una valoración justa.")
    with col3:
        st.metric("Precio/Valor en Libros", fundamental_data.get('priceToBook', 'N/A'))
        st.markdown("**Interpretación:** Compara el precio de mercado con el valor contable. Un ratio bajo puede indicar una acción subvalorada.")
    with col4:
        st.metric("EV/EBITDA", fundamental_data.get('enterpriseToEbitda', 'N/A'))
        st.markdown("**Interpretación:** Compara el valor de la empresa con sus ganancias antes de intereses, impuestos, depreciación y amortización. Un valor más bajo puede indicar una valoración atractiva.")
    
    # Análisis comparativo de valoración con el sector
    st.subheader("Análisis Comparativo de Valoración")
    st.markdown("""
    Para evaluar si una acción está cara o barata, es fundamental comparar sus métricas de valoración con:
    
    1. **El promedio histórico de la empresa**: Para ver si la valoración actual es alta o baja respecto a su propio historial.
    2. **El promedio del sector**: Para entender cómo se compara con empresas similares.
    3. **El promedio del mercado**: Para contextualizar la valoración respecto al mercado en general.
    
    Un P/E ratio por debajo del promedio del sector puede indicar una potencial infravaloración, pero también puede reflejar problemas fundamentales o expectativas de crecimiento más bajas.
    """)

elif analysis_type == "Análisis de Rentabilidad":
    st.header("Métricas de Rentabilidad")
    col1, col2, col3 = st.columns(3)
    with col1:
        profit_margin = fundamental_data.get('profitMargins', 'N/A')
        if profit_margin not in ['N/A', 0]:
            st.metric("Margen de Beneficio", f"{profit_margin:.2%}")
        else:
            st.metric("Margen de Beneficio", "N/A")
        st.markdown("**Interpretación:** Indica qué porcentaje de los ingresos se convierte en beneficio. Un margen más alto sugiere una mayor eficiencia.")
    with col2:
        roe = fundamental_data.get('returnOnEquity', 'N/A')
        if roe not in ['N/A', 0]:
            st.metric("ROE", f"{roe:.2%}")
        else:
            st.metric("ROE", "N/A")
        st.markdown("**Interpretación:** Mide la rentabilidad en relación con el patrimonio de los accionistas. Un ROE más alto indica un uso más eficiente del capital.")
    with col3:
        roa = fundamental_data.get('returnOnAssets', 'N/A')
        if roa not in ['N/A', 0]:
            st.metric("ROA", f"{roa:.2%}")
        else:
            st.metric("ROA", "N/A")
        st.markdown("**Interpretación:** Indica cuán eficientemente la empresa utiliza sus activos para generar ganancias. Un ROA más alto es generalmente mejor.")

    # Gráfico de crecimiento de ingresos y beneficios
    st.subheader("Crecimiento de Ingresos y Beneficios")
    revenue_growth = alpha_vantage_data.get('QuarterlyRevenueGrowthYOY', '0')
    earnings_growth = alpha_vantage_data.get('QuarterlyEarningsGrowthYOY', '0')
    
    try:
        # Convertir a float y luego a porcentaje
        revenue_growth_float = float(revenue_growth) * 100
        earnings_growth_float = float(earnings_growth) * 100
        
        fig = go.Figure(data=[
            go.Bar(name='Crecimiento de Ingresos', x=['Últimos 12 meses'], y=[revenue_growth_float], 
                   marker_color='royalblue'),
            go.Bar(name='Crecimiento de Beneficios', x=['Últimos 12 meses'], y=[earnings_growth_float],
                  marker_color='lightgreen' if earnings_growth_float > 0 else 'salmon')
        ])
        fig.update_layout(barmode='group', title='Crecimiento Anual de Ingresos y Beneficios (%)')
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"No se pudo crear el gráfico de crecimiento: {e}")
    
    st.markdown("""
    **Interpretación del Crecimiento:** 
    
    Un crecimiento sostenible de ingresos y beneficios es crucial para la valoración a largo plazo de una acción. 
    
    * **Crecimiento de ingresos > Crecimiento de beneficios**: Puede indicar presión en los márgenes o inversiones para escalamiento.
    * **Crecimiento de beneficios > Crecimiento de ingresos**: Sugiere mejoras en la eficiencia operativa o economías de escala.
    * **Ambos negativos**: Podría señalar problemas fundamentales en el modelo de negocio o condiciones de mercado adversas.
    
    Los inversores value suelen buscar empresas con crecimiento estable y predecible, mientras que los growth investors priorizan tasas de crecimiento altas aunque sean menos estables.
    """)

elif analysis_type == "Salud Financiera":
    st.header("Salud Financiera")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Ratio de Deuda/Capital", fundamental_data.get('debtToEquity', 'N/A'))
        st.markdown("**Interpretación:** Compara la deuda total con el patrimonio de los accionistas. Un ratio más bajo generalmente indica una posición financiera más fuerte.")
    with col2:
        st.metric("Ratio Corriente", fundamental_data.get('currentRatio', 'N/A'))
        st.markdown("**Interpretación:** Mide la capacidad de la empresa para pagar sus obligaciones a corto plazo. Un ratio superior a 1 es generalmente considerado saludable.")
    with col3:
        fcf = fundamental_data.get('freeCashflow', 'N/A')
        if fcf not in ['N/A', 0]:
            if abs(fcf) > 1_000_000_000:
                fcf_str = f"${fcf/1_000_000_000:.2f}B"
            else:
                fcf_str = f"${fcf:,}"
            st.metric("Flujo de Caja Libre (TTM)", fcf_str)
        else:
            st.metric("Flujo de Caja Libre (TTM)", "N/A")
        st.markdown("**Interpretación:** Indica el efectivo que queda después de los gastos de capital. Un flujo de caja libre positivo y creciente es una buena señal.")
    
    st.subheader("Importancia de la Salud Financiera")
    st.markdown("""
    La salud financiera de una empresa es fundamental para su supervivencia a largo plazo y su capacidad para generar valor para los accionistas:
    
    * **Alto nivel de deuda**: Puede limitar la flexibilidad financiera y aumentar el riesgo en períodos de recesión económica.
    * **Liquidez insuficiente**: Puede provocar problemas operativos incluso en empresas rentables.
    * **Flujo de caja libre negativo persistente**: Puede indicar un modelo de negocio insostenible a largo plazo.
    
    Las empresas con balances sólidos (baja deuda, alta liquidez) suelen resistir mejor las crisis económicas y pueden aprovechar oportunidades de mercado cuando los competidores más débiles están luchando por sobrevivir.
    """)

# Función para descargar datos
def filedownload(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="fundamental_data.csv">Descargar Datos CSV</a>'
    return href

# Crear DataFrame con los datos fundamentales para descarga
st.header("Resumen de Métricas")
try:
    fundamental_df = pd.DataFrame({
        'Métrica': ['P/E Ratio', 'PEG Ratio', 'Precio/Valor en Libros', 'EV/EBITDA', 'Margen de Beneficio', 'ROE', 'ROA', 
                    'Rendimiento del Dividendo', 'Ratio de Pago', 'Ratio de Deuda/Capital', 'Ratio Corriente', 'Flujo de Caja Libre (TTM)'],
        'Valor': [fundamental_data.get('trailingPE', 'N/A'), 
                fundamental_data.get('pegRatio', 'N/A'),
                fundamental_data.get('priceToBook', 'N/A'),
                fundamental_data.get('enterpriseToEbitda', 'N/A'),
                f"{fundamental_data.get('profitMargins', 'N/A'):.2%}" if fundamental_data.get('profitMargins', 'N/A') != 'N/A' else 'N/A',
                f"{fundamental_data.get('returnOnEquity', 'N/A'):.2%}" if fundamental_data.get('returnOnEquity', 'N/A') != 'N/A' else 'N/A',
                f"{fundamental_data.get('returnOnAssets', 'N/A'):.2%}" if fundamental_data.get('returnOnAssets', 'N/A') != 'N/A' else 'N/A',
                f"{fundamental_data.get('dividendYield', 'N/A'):.2%}" if fundamental_data.get('dividendYield', 'N/A') != 'N/A' else 'N/A',
                f"{fundamental_data.get('payoutRatio', 'N/A'):.2%}" if fundamental_data.get('payoutRatio', 'N/A') != 'N/A' else 'N/A',
                fundamental_data.get('debtToEquity', 'N/A'),
                fundamental_data.get('currentRatio', 'N/A'),
                f"${fundamental_data.get('freeCashflow', 'N/A'):,}" if fundamental_data.get('freeCashflow', 'N/A') != 'N/A' else 'N/A']
    })

    st.dataframe(fundamental_df)
    st.markdown(filedownload(fundamental_df), unsafe_allow_html=True)
except Exception as e:
    st.error(f"Error al crear el resumen de métricas: {e}")

# Añadir información educativa
with st.expander("📚 Aprende más sobre análisis fundamental"):
    st.markdown("""
    ### ¿Qué es el análisis fundamental?
    
    El análisis fundamental evalúa el valor intrínseco de una acción mediante el estudio de factores económicos y financieros relacionados. Se examina todo lo que puede afectar el valor de la acción, desde condiciones macroeconómicas y la industria hasta la situación financiera específica de la empresa.
    
    ### Principales métricas para inversores:
    
    1. **P/E Ratio (Price to Earnings)**: Compara el precio de la acción con las ganancias por acción.
    2. **PEG Ratio (Price/Earnings to Growth)**: Ajusta el P/E según la tasa de crecimiento esperada.
    3. **Price to Book Ratio**: Compara el precio de mercado con el valor contable.
    4. **Debt to Equity**: Evalúa el apalancamiento financiero de la empresa.
    5. **Dividend Yield**: Rendimiento de dividendos en relación al precio de la acción.
    
    ### Estrategias de inversión:
    
    - **Value Investing**: Busca empresas infravaloradas según sus fundamentales.
    - **Growth Investing**: Prioriza empresas con alto potencial de crecimiento.
    - **GARP (Growth At Reasonable Price)**: Combina elementos de value y growth.
    - **Dividend Investing**: Se centra en empresas con dividendos estables y crecientes.
    
    El análisis fundamental es complementario al análisis técnico, y muchos inversores utilizan ambos enfoques para tomar decisiones de inversión más informadas.
    """)

# Función para crear el footer personalizado
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

# Agregar el footer personalizado
add_footer()