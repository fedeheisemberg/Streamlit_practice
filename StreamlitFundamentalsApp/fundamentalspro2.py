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
from bs4 import BeautifulSoup
import wikipedia
import os

# Configuración de la página con favicon
favicon_path = os.path.join(os.getcwd(), "StreamlitFundamentalsApp", "favicon.ico")
st.set_page_config(page_title="Dashboard Fundamentals", layout="wide", page_icon=favicon_path)

# Función para determinar el modo (oscuro o claro)
def get_theme():
    return st.get_option("theme.base")

# Cargar logo basado en el tema
logo_light = os.path.join(os.getcwd(), "StreamlitFundamentalsApp", "logo2.png")
logo_dark = os.path.join(os.getcwd(), "StreamlitFundamentalsApp", "logo1.png")

if get_theme() == "light":
    if os.path.exists(logo_light):
        st.image(logo_light)
    else:
        st.warning("No se encontró el logo claro.")
else:
    if os.path.exists(logo_dark):
        st.image(logo_dark)
    else:
        st.warning("No se encontró el logo oscuro.")

# Crear título
st.title("Dashboard Fundamentals - Optima Consulting & Management LLC")

st.markdown("""
Este dashboard proporciona un análisis fundamental completo de las empresas del S&P 500, incluyendo métricas clave y visualizaciones interactivas.
* **Fuentes de datos:** Wikipedia, Yahoo Finance, Alpha Vantage
* **Bibliotecas:** streamlit, pandas, numpy, matplotlib, seaborn, plotly, yfinance, beautifulsoup4, wikipedia
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

# Nueva función para obtener información de Wikipedia
@st.cache_data
def get_wikipedia_info(company_name):
    try:
        # Buscar la página de Wikipedia
        search_results = wikipedia.search(company_name)
        if not search_results:
            return None
        
        # Obtener el contenido de la página
        page = wikipedia.page(search_results[0])
        soup = BeautifulSoup(page.html(), 'html.parser')
        
        # Extraer el resumen (primer párrafo)
        summary = soup.find('p', class_=lambda x: x != 'mw-empty-elt').text
        
        # Extraer información de la infobox
        infobox = soup.find('table', class_='infobox')
        info_dict = {}
        
        if infobox:
            for row in infobox.find_all('tr'):
                header = row.find('th')
                data = row.find('td')
                if header and data:
                    key = header.text.strip()
                    value = data.text.strip()
                    info_dict[key] = value
        
        # Extraer datos específicos de interés
        founded = info_dict.get('Founded', 'N/A')
        industry = info_dict.get('Industry', 'N/A')
        key_people = info_dict.get('Key people', 'N/A')
        products = info_dict.get('Products', 'N/A')
        revenue = info_dict.get('Revenue', 'N/A')
        number_of_employees = info_dict.get('Number of employees', 'N/A')
        website = info_dict.get('Website', 'N/A')
        
        return {
            'summary': summary,
            'founded': founded,
            'industry': industry,
            'key_people': key_people,
            'products': products,
            'revenue': revenue,
            'number_of_employees': number_of_employees,
            'website': website
        }
    except Exception as e:
        st.error(f"Error al obtener información de Wikipedia: {str(e)}")
        return None

# Obtener datos fundamentales
fundamental_data = get_fundamental_data(selected_company)
alpha_vantage_data = get_alpha_vantage_data(selected_company)
wiki_info = get_wikipedia_info(fundamental_data.get('longName', selected_company))

# Mostrar información general de la empresa
st.header(f"Información General de {fundamental_data.get('longName', selected_company)}")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Precio Actual", f"${fundamental_data.get('currentPrice', 'N/A')}")
with col2:
    st.metric("Capitalización de Mercado", f"${fundamental_data.get('marketCap', 'N/A'):,}")
with col3:
    st.metric("Sector", fundamental_data.get('sector', 'N/A'))

# Mostrar información de Wikipedia
if wiki_info:
    st.subheader("Resumen de la Empresa")
    st.write(wiki_info['summary'])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Año de Fundación", wiki_info['founded'])
        st.metric("Industria", wiki_info['industry'])
    with col2:
        st.metric("Ingresos", wiki_info['revenue'])
        st.metric("Número de Empleados", wiki_info['number_of_employees'])
    with col3:
        st.metric("Productos Principales", wiki_info['products'])
        st.metric("Sitio Web", wiki_info['website'])
    
    st.subheader("Personas Clave")
    st.write(wiki_info['key_people'])
else:
    st.warning("No se pudo obtener información detallada de Wikipedia para esta empresa.")

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
    st.markdown("❗ Compara el precio de la acción con las ganancias por acción. Un P/E más bajo puede indicar que la acción está subvalorada.", unsafe_allow_html=True)
with col2:
    st.metric("PEG Ratio", fundamental_data.get('pegRatio', 'N/A'))
    st.markdown("❗ Relaciona el P/E con el crecimiento esperado. Un PEG cercano a 1 puede indicar una valoración justa.", unsafe_allow_html=True)
with col3:
    st.metric("Precio/Valor en Libros", fundamental_data.get('priceToBook', 'N/A'))
    st.markdown("❗ Compara el precio de mercado con el valor contable. Un ratio bajo puede indicar una acción subvalorada.", unsafe_allow_html=True)
with col4:
    st.metric("EV/EBITDA", fundamental_data.get('enterpriseToEbitda', 'N/A'))
    st.markdown("❗ Compara el valor de la empresa con sus ganancias antes de intereses, impuestos, depreciación y amortización. Un valor más bajo puede indicar una valoración atractiva.", unsafe_allow_html=True)

# Métricas de rentabilidad
st.header("Métricas de Rentabilidad")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Margen de Beneficio", f"{fundamental_data.get('profitMargins', 'N/A'):.2%}")
    st.markdown("❗ Indica qué porcentaje de los ingresos se convierte en beneficio. Un margen más alto sugiere una mayor eficiencia.", unsafe_allow_html=True)
with col2:
    st.metric("ROE", f"{fundamental_data.get('returnOnEquity', 'N/A'):.2%}")
    st.markdown("❗ Mide la rentabilidad en relación con el patrimonio de los accionistas. Un ROE más alto indica un uso más eficiente del capital.", unsafe_allow_html=True)
with col3:
    st.metric("ROA", f"{fundamental_data.get('returnOnAssets', 'N/A'):.2%}")
    st.markdown("❗ Indica cuán eficientemente la empresa utiliza sus activos para generar ganancias. Un ROA más alto es generalmente mejor.", unsafe_allow_html=True)

# Gráfico de crecimiento de ingresos y beneficios
st.header("Crecimiento de Ingresos y Beneficios")
revenue_growth = alpha_vantage_data.get('QuarterlyRevenueGrowthYOY', 'N/A')
earnings_growth = alpha_vantage_data.get('QuarterlyEarningsGrowthYOY', 'N/A')

fig = go.Figure(data=[
    go.Bar(name='Crecimiento de Ingresos', x=['Últimos 12 meses'], y=[float(revenue_growth) if revenue_growth != 'N/A' else 0], marker_color='#4CAF50'),
    go.Bar(name='Crecimiento de Beneficios', x=['Últimos 12 meses'], y=[float(earnings_growth) if earnings_growth != 'N/A' else 0], marker_color='#2196F3')
])
fig.update_layout(barmode='group', title='Crecimiento Anual de Ingresos y Beneficios')
st.plotly_chart(fig, use_container_width=True)
st.markdown("❗ Estos gráficos muestran el crecimiento anual de los ingresos y beneficios. Un crecimiento positivo y consistente es generalmente una buena señal.", unsafe_allow_html=True)

# Análisis de dividendos
st.header("Análisis de Dividendos")
col1, col2 = st.columns(2)
with col1:
    st.metric("Rendimiento del Dividendo", f"{fundamental_data.get('dividendYield', 'N/A'):.2%}")
    st.markdown("❗ Indica cuánto paga la empresa en dividendos en relación con el precio de la acción. Un rendimiento más alto puede ser atractivo para los inversores que buscan ingresos.", unsafe_allow_html=True)
with col2:
    st.metric("Ratio de Pago", f"{fundamental_data.get('payoutRatio', 'N/A'):.2%}")
    st.markdown("❗ Muestra qué porcentaje de las ganancias se paga como dividendos. Un ratio más bajo puede indicar más espacio para el crecimiento de los dividendos.", unsafe_allow_html=True)

# Gráfico de evolución de dividendos
st.subheader("Evolución de Dividendos")
dividends = yf.Ticker(selected_company).dividends
if not dividends.empty:
    fig = px.line(dividends, x=dividends.index, y=dividends.values, title=f"Evolución de Dividendos de {selected_company}")
    fig.update_layout(xaxis_title="Fecha", yaxis_title="Dividendo por Acción")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No hay datos de dividendos disponibles para esta empresa.")

# Salud financiera
st.header("Salud Financiera")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Ratio de Deuda/Capital", fundamental_data.get('debtToEquity', 'N/A'))
    st.markdown("❗ Compara la deuda total con el patrimonio de los accionistas. Un ratio más bajo generalmente indica una posición financiera más fuerte.", unsafe_allow_html=True)
with col2:
    st.metric("Ratio Corriente", fundamental_data.get('currentRatio', 'N/A'))
    st.markdown("❗ Mide la capacidad de la empresa para pagar sus obligaciones a corto plazo. Un ratio superior a 1 es generalmente considerado saludable.", unsafe_allow_html=True)
with col3:
    st.metric("Flujo de Caja Libre (TTM)", f"${fundamental_data.get('freeCashflow', 'N/A'):,}")
    st.markdown("❗ Indica el efectivo que queda después de los gastos de capital. Un flujo de caja libre positivo y creciente es una buena señal.", unsafe_allow_html=True)

# Análisis de volatilidad
st.header("Análisis de Volatilidad")
stock_data = yf.Ticker(selected_company).history(period="1y")
stock_data['Returns'] = stock_data['Close'].pct_change()
volatility = stock_data['Returns'].std() * (252 ** 0.5)  # Volatilidad anualizada
st.metric("Volatilidad Anualizada", f"{volatility:.2%}")
st.markdown("❗ La volatilidad anualizada mide la variación del precio de la acción en un año. Una volatilidad más alta indica mayor riesgo pero también potencial de mayores retornos.", unsafe_allow_html=True)

# Gráfico de distribución de retornos
fig = px.histogram(stock_data, x='Returns', nbins=50, title=f"Distribución de Retornos Diarios de {selected_company}")
fig.update_layout(xaxis_title="Retorno Diario", yaxis_title="Frecuencia")
st.plotly_chart(fig, use_container_width=True)

# Comparación con el índice (S&P 500)
st.header("Comparación con el Índice S&P 500")
sp500 = yf.Ticker("^GSPC").history(period="1y")
sp500['Returns'] = sp500['Close'].pct_change()
stock_data['Cumulative_Returns'] = (1 + stock_data['Returns']).cumprod()
sp500['Cumulative_Returns'] = (1 + sp500['Returns']).cumprod()

fig = go.Figure()
fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Cumulative_Returns'], name=selected_company))
fig.add_trace(go.Scatter(x=sp500.index, y=sp500['Cumulative_Returns'], name='S&P 500'))
fig.update_layout(title=f"Rendimiento Acumulado: {selected_company} vs S&P 500", xaxis_title="Fecha", yaxis_title="Rendimiento Acumulado")
st.plotly_chart(fig, use_container_width=True)

st.markdown("❗ Este gráfico compara el rendimiento de la acción con el índice S&P 500. Un rendimiento superior al índice indica un buen desempeño relativo de la acción.", unsafe_allow_html=True)

# Función para descargar datos
def filedownload(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="fundamental_data.csv">Descargar Datos CSV</a>'
    return href

# Crear DataFrame con los datos fundamentales
fundamental_df = pd.DataFrame({
    'Métrica': ['P/E Ratio', 'PEG Ratio', 'Precio/Valor en Libros', 'EV/EBITDA', 'Margen de Beneficio', 'ROE', 'ROA', 
                'Rendimiento del Dividendo', 'Ratio de Pago', 'Ratio de Deuda/Capital', 'Ratio Corriente', 'Flujo de Caja Libre (TTM)', 'Volatilidad Anualizada'],
    'Valor': [fundamental_data.get('trailingPE', 'N/A'), 
              fundamental_data.get('pegRatio', 'N/A'),
              fundamental_data.get('priceToBook', 'N/A'),
              fundamental_data.get('enterpriseToEbitda', 'N/A'),
              f"{fundamental_data.get('profitMargins', 'N/A'):.2%}" if fundamental_data.get('profitMargins') is not None else 'N/A',
              f"{fundamental_data.get('returnOnEquity', 'N/A'):.2%}" if fundamental_data.get('returnOnEquity') is not None else 'N/A',
              f"{fundamental_data.get('returnOnAssets', 'N/A'):.2%}" if fundamental_data.get('returnOnAssets') is not None else 'N/A',
              f"{fundamental_data.get('dividendYield', 'N/A'):.2%}" if fundamental_data.get('dividendYield') is not None else 'N/A',
              f"{fundamental_data.get('payoutRatio', 'N/A'):.2%}" if fundamental_data.get('payoutRatio') is not None else 'N/A',
              fundamental_data.get('debtToEquity', 'N/A'),
              fundamental_data.get('currentRatio', 'N/A'),
              f"${fundamental_data.get('freeCashflow', 'N/A'):,}" if fundamental_data.get('freeCashflow') is not None else 'N/A',
              f"{volatility:.2%}"]
})

st.dataframe(fundamental_df)
st.markdown(filedownload(fundamental_df), unsafe_allow_html=True)

# Feedback
st.header("📣 ¡Tu opinión es importante!")
st.markdown("""
Nos encantaría saber qué piensas sobre este dashboard de análisis fundamental. 
¿Qué otras funcionalidades o métricas te gustaría ver? 
¿Estás interesado en un proyecto más avanzado sobre análisis de opciones?

Tu feedback es invaluable para nosotros y nos ayuda a mejorar constantemente nuestras herramientas.

**¿Qué podemos mejorar de esto que acabas de ver?** 

Envíanos tus comentarios, sugerencias o ideas a:

### 📧 optimaconsultingmanagement@gmail.com

¡Esperamos con interés tus valiosos aportes!
""")

# Footer usando markdown de Streamlit
st.markdown("---")
st.markdown("© 2024 Optima Consulting & Management LLC | [LinkedIn](https://www.linkedin.com/company/optima-consulting-managament-llc) | [Capacitaciones](https://www.optimalearning.site/) | [Página Web](https://www.optimafinancials.com/)")