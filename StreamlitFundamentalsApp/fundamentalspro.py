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

# Configuración de la página con favicon
st.set_page_config(page_title="Dashboard OptionsPro", layout="wide", page_icon="StreamlitFundamentalsApp/favicon.ico")

# Función para determinar el modo (oscuro o claro)
def get_theme():
    return st.get_option("theme.base")

# Cargar logo basado en el tema
if get_theme() == "light":
    st.image("StreamlitFundamentalsApp/logo2.png")
else:
    st.image("StreamlitFundamentalsApp/logo1.png")

# Crear título
st.title("Dashboard Fundamentals - Optima Consulting & Management LLC")

st.markdown("""
Este dashboard proporciona un análisis fundamental completo de las empresas del S&P 500, incluyendo métricas clave y visualizaciones interactivas.
* **Fuentes de datos:** Wikipedia, Yahoo Finance, Alpha Vantage
* **Bibliotecas:** streamlit, pandas, numpy, matplotlib, seaborn, plotly, yfinance
""")

# Función para cargar datos del S&P 500
@st.cache_data
def load_data():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    html = pd.read_html(url, header = 0)
    df = html[0]
    return df

df = load_data()
sector = df.groupby('GICS Sector')

# Barra lateral - Selección de sector y empresa
st.sidebar.header('Filtros')
sorted_sector_unique = sorted(df['GICS Sector'].unique())
selected_sector = st.sidebar.multiselect('Sector', sorted_sector_unique, sorted_sector_unique[0])

# Filtrado de datos por sector
df_selected_sector = df[df['GICS Sector'].isin(selected_sector)]

# Selección de empresa
selected_company = st.sidebar.selectbox('Empresa', df_selected_sector['Symbol'].tolist())

# Función para obtener datos fundamentales de Yahoo Finance
@st.cache_data
def get_fundamental_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    return info

# Función para obtener datos de Alpha Vantage
@st.cache_data
def get_alpha_vantage_data(symbol):
    api_key = '9RQZ699U0PT6NTHN'
    url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={api_key}'
    r = requests.get(url)
    return r.json()

# Obtener datos fundamentales
fundamental_data = get_fundamental_data(selected_company)
alpha_vantage_data = get_alpha_vantage_data(selected_company)

# Mostrar información general de la empresa
st.header(f"Información General de {fundamental_data.get('longName', selected_company)}")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Precio Actual", f"${fundamental_data.get('currentPrice', 'N/A')}")
with col2:
    st.metric("Capitalización de Mercado", f"${fundamental_data.get('marketCap', 'N/A'):,}")
with col3:
    st.metric("Sector", fundamental_data.get('sector', 'N/A'))

# Función para crear gráfico de velas
def create_candlestick_chart(ticker):
    data = yf.download(ticker, period="1y")
    fig = go.Figure(data=[go.Candlestick(x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'])])
    fig.update_layout(title=f'Gráfico de Velas de {ticker} - Último Año',
                      xaxis_title='Fecha',
                      yaxis_title='Precio')
    return fig

# Mostrar gráfico de velas
st.plotly_chart(create_candlestick_chart(selected_company), use_container_width=True)

# Métricas de valoración
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

# Métricas de rentabilidad
st.header("Métricas de Rentabilidad")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Margen de Beneficio", f"{fundamental_data.get('profitMargins', 'N/A'):.2%}")
    st.markdown("**Interpretación:** Indica qué porcentaje de los ingresos se convierte en beneficio. Un margen más alto sugiere una mayor eficiencia.")
with col2:
    st.metric("ROE", f"{fundamental_data.get('returnOnEquity', 'N/A'):.2%}")
    st.markdown("**Interpretación:** Mide la rentabilidad en relación con el patrimonio de los accionistas. Un ROE más alto indica un uso más eficiente del capital.")
with col3:
    st.metric("ROA", f"{fundamental_data.get('returnOnAssets', 'N/A'):.2%}")
    st.markdown("**Interpretación:** Indica cuán eficientemente la empresa utiliza sus activos para generar ganancias. Un ROA más alto es generalmente mejor.")

# Gráfico de crecimiento de ingresos y beneficios
st.header("Crecimiento de Ingresos y Beneficios")
revenue_growth = alpha_vantage_data.get('QuarterlyRevenueGrowthYOY', 'N/A')
earnings_growth = alpha_vantage_data.get('QuarterlyEarningsGrowthYOY', 'N/A')

fig = go.Figure(data=[
    go.Bar(name='Crecimiento de Ingresos', x=['Últimos 12 meses'], y=[float(revenue_growth) if revenue_growth != 'N/A' else 0]),
    go.Bar(name='Crecimiento de Beneficios', x=['Últimos 12 meses'], y=[float(earnings_growth) if earnings_growth != 'N/A' else 0])
])
fig.update_layout(barmode='group', title='Crecimiento Anual de Ingresos y Beneficios')
st.plotly_chart(fig, use_container_width=True)
st.markdown("**Interpretación:** Estos gráficos muestran el crecimiento anual de los ingresos y beneficios. Un crecimiento positivo y consistente es generalmente una buena señal.")

# Análisis de dividendos
st.header("Análisis de Dividendos")
col1, col2 = st.columns(2)
with col1:
    st.metric("Rendimiento del Dividendo", f"{fundamental_data.get('dividendYield', 'N/A'):.2%}")
    st.markdown("**Interpretación:** Indica cuánto paga la empresa en dividendos en relación con el precio de la acción. Un rendimiento más alto puede ser atractivo para los inversores que buscan ingresos.")
with col2:
    st.metric("Ratio de Pago", f"{fundamental_data.get('payoutRatio', 'N/A'):.2%}")
    st.markdown("**Interpretación:** Muestra qué porcentaje de las ganancias se paga como dividendos. Un ratio más bajo puede indicar más espacio para el crecimiento de los dividendos.")

# Salud financiera
st.header("Salud Financiera")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Ratio de Deuda/Capital", fundamental_data.get('debtToEquity', 'N/A'))
    st.markdown("**Interpretación:** Compara la deuda total con el patrimonio de los accionistas. Un ratio más bajo generalmente indica una posición financiera más fuerte.")
with col2:
    st.metric("Ratio Corriente", fundamental_data.get('currentRatio', 'N/A'))
    st.markdown("**Interpretación:** Mide la capacidad de la empresa para pagar sus obligaciones a corto plazo. Un ratio superior a 1 es generalmente considerado saludable.")
with col3:
    st.metric("Flujo de Caja Libre (TTM)", f"${fundamental_data.get('freeCashflow', 'N/A'):,}")
    st.markdown("**Interpretación:** Indica el efectivo que queda después de los gastos de capital. Un flujo de caja libre positivo y creciente es una buena señal.")

# Función para descargar datos
def filedownload(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="fundamental_data.csv">Descargar Datos CSV</a>'
    return href

# Crear DataFrame con los datos fundamentales
fundamental_df = pd.DataFrame({
    'Métrica': ['P/E Ratio', 'PEG Ratio', 'Precio/Valor en Libros', 'EV/EBITDA', 'Margen de Beneficio', 'ROE', 'ROA', 
                'Rendimiento del Dividendo', 'Ratio de Pago', 'Ratio de Deuda/Capital', 'Ratio Corriente', 'Flujo de Caja Libre (TTM)'],
    'Valor': [fundamental_data.get('trailingPE', 'N/A'), 
              fundamental_data.get('pegRatio', 'N/A'),
              fundamental_data.get('priceToBook', 'N/A'),
              fundamental_data.get('enterpriseToEbitda', 'N/A'),
              f"{fundamental_data.get('profitMargins', 'N/A'):.2%}",
              f"{fundamental_data.get('returnOnEquity', 'N/A'):.2%}",
              f"{fundamental_data.get('returnOnAssets', 'N/A'):.2%}",
              f"{fundamental_data.get('dividendYield', 'N/A'):.2%}",
              f"{fundamental_data.get('payoutRatio', 'N/A'):.2%}",
              fundamental_data.get('debtToEquity', 'N/A'),
              fundamental_data.get('currentRatio', 'N/A'),
              f"${fundamental_data.get('freeCashflow', 'N/A'):,}"]
})

st.dataframe(fundamental_df)
st.markdown(filedownload(fundamental_df), unsafe_allow_html=True)

# Footer usando markdown de Streamlit
st.markdown("---")
st.markdown("© 2024 Optima Consulting & Management LLC | [LinkedIn](https://www.linkedin.com/company/optima-consulting-managament-llc) | [Capacitaciones](https://www.optimalearning.site/) | [Página Web](https://www.optimafinancials.com/)")