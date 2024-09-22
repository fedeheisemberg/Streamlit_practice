import streamlit as st
from datetime import date
import yfinance as yf
from prophet import Prophet
from prophet.plot import plot_plotly
from plotly import graph_objs as go

# Fecha de inicio y fecha de hoy
INICIO = "2015-01-01"
HOY = date.today().strftime("%Y-%m-%d")

# Título de la aplicación
st.title('Aplicación de Predicción de Acciones')

# Lista de acciones con 10 más añadidas
acciones = ('GOOG', 'AAPL', 'MSFT', 'GME', 'TSLA', 'AMZN', 'NFLX', 'NVDA', 'META', 'BABA', 'BA', 'XOM', 'JPM', 'V', 'KO')
accion_seleccionada = st.selectbox('Selecciona un conjunto de datos para la predicción', acciones)

# Control deslizante para elegir años de predicción
n_años = st.slider('Años de predicción:', 1, 4)
periodo = n_años * 365

# Carga de datos de Yahoo Finance
@st.cache_data
def cargar_datos(ticker):
    datos = yf.download(ticker, INICIO, HOY)
    datos.reset_index(inplace=True)
    return datos

# Mensaje de estado de carga de datos
estado_carga_datos = st.text('Cargando datos...')
datos = cargar_datos(accion_seleccionada)
estado_carga_datos.text('Cargando datos... ¡hecho!')

# Subtítulo para los datos en bruto
st.subheader('Datos en bruto')
st.write(datos.tail())

# Función para graficar los datos en bruto
def graficar_datos_brutos():
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=datos['Date'], y=datos['Open'], name="stock_open"))
    fig.add_trace(go.Scatter(x=datos['Date'], y=datos['Close'], name="stock_close"))
    fig.layout.update(title_text='Datos de Series Temporales con Rango deslizante', xaxis_rangeslider_visible=True)
    st.plotly_chart(fig)

graficar_datos_brutos()

# Predicción del pronóstico con Prophet
df_train = datos[['Date', 'Close']]
df_train = df_train.rename(columns={"Date": "ds", "Close": "y"})

m = Prophet()
m.fit(df_train)
futuro = m.make_future_dataframe(periods=periodo)
pronostico = m.predict(futuro)

# Mostrar y graficar el pronóstico
st.subheader('Datos del pronóstico')
st.write(pronostico.tail())

st.write(f'Gráfico del pronóstico para {n_años} años')
fig1 = plot_plotly(m, pronostico)
st.plotly_chart(fig1)

st.write("Componentes del pronóstico")
fig2 = m.plot_components(pronostico)
st.write(fig2)
