import streamlit as st
from PIL import Image
import pandas as pd
import base64
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import requests
import json

#---------------------------------#
# Página de configuración
st.set_page_config(layout="wide")

# Título
st.title('Aplicación de Precios de Criptoactivos')
st.markdown("""
Esta aplicación recupera los precios de criptomonedas para las 100 principales criptomonedas de **CoinMarketCap**!
""")

#---------------------------------#
# Acerca de
expander_bar = st.expander("Acerca de")
expander_bar.markdown("""
* **Bibliotecas de Python:** base64, pandas, streamlit, numpy, matplotlib, seaborn, BeautifulSoup, requests, json
* **Fuente de datos:** [CoinMarketCap](http://coinmarketcap.com).
* **Crédito:** Web scraper adaptado del artículo de Medium *[Web Scraping Crypto Prices With Python](https://towardsdatascience.com/web-scraping-crypto-prices-with-python-41072ea5b5bf)* escrito por [Bryan Feng](https://medium.com/@bryanf).
""")

#---------------------------------#
# Diseño de la página (continuación)
col1 = st.sidebar
col2, col3 = st.columns((2,1))

col1.header('Opciones de Entrada')

# Unidad de precio de la moneda
currency_price_unit = col1.selectbox('Selecciona la moneda para el precio', ('USD', 'BTC', 'ETH'))

# Web scraping de datos de CoinMarketCap
@st.cache
def load_data():
    cmc = requests.get('https://coinmarketcap.com')
    soup = BeautifulSoup(cmc.content, 'html.parser')

    # Imprimir el contenido para depuración
    script_tag = soup.find('script', id='__NEXT_DATA__', type='application/json')
    if script_tag is None:
        st.error("No se pudo encontrar el script con datos de CoinMarketCap.")
        return pd.DataFrame()

    try:
        data = json.loads(script_tag.contents[0])
        listings = data['props']['initialState']['cryptocurrency']['listingLatest']['data']
    except (KeyError, json.JSONDecodeError) as e:
        st.error(f"Error al procesar los datos: {e}")
        return pd.DataFrame()

    # Procesar datos
    coin_name = []
    coin_symbol = []
    market_cap = []
    percent_change_1h = []
    percent_change_24h = []
    percent_change_7d = []
    price = []
    volume_24h = []

    for i in listings:
        coin_name.append(i['slug'])
        coin_symbol.append(i['symbol'])
        price.append(i['quote'][currency_price_unit]['price'])
        percent_change_1h.append(i['quote'][currency_price_unit]['percent_change_1h'])
        percent_change_24h.append(i['quote'][currency_price_unit]['percent_change_24h'])
        percent_change_7d.append(i['quote'][currency_price_unit]['percent_change_7d'])
        market_cap.append(i['quote'][currency_price_unit]['market_cap'])
        volume_24h.append(i['quote'][currency_price_unit]['volume_24h'])

    df = pd.DataFrame({
        'coin_name': coin_name,
        'coin_symbol': coin_symbol,
        'price': price,
        'percent_change_1h': percent_change_1h,
        'percent_change_24h': percent_change_24h,
        'percent_change_7d': percent_change_7d,
        'market_cap': market_cap,
        'volume_24h': volume_24h
    })
    return df

df = load_data()

# Barra lateral - Selección de criptomonedas
sorted_coin = sorted(df['coin_symbol'])
selected_coin = col1.multiselect('Criptomoneda', sorted_coin, sorted_coin)

df_selected_coin = df[df['coin_symbol'].isin(selected_coin)] # Filtrar datos

# Barra lateral - Número de monedas a mostrar
num_coin = col1.slider('Mostrar las primeras N monedas', 1, 100, 100)
df_coins = df_selected_coin[:num_coin]

# Barra lateral - Marco temporal del cambio porcentual
percent_timeframe = col1.selectbox('Marco temporal del cambio porcentual',
                                    ['7d', '24h', '1h'])
percent_dict = {"7d": 'percent_change_7d', "24h": 'percent_change_24h', "1h": 'percent_change_1h'}
selected_percent_timeframe = percent_dict[percent_timeframe]

# Barra lateral - Ordenar valores
sort_values = col1.selectbox('¿Ordenar valores?', ['Sí', 'No'])

col2.subheader('Datos de Precios de Criptomonedas Seleccionadas')
col2.write('Dimensión de los datos: ' + str(df_selected_coin.shape[0]) + ' filas y ' + str(df_selected_coin.shape[1]) + ' columnas.')

col2.dataframe(df_coins)

# Descargar CSV de datos
def filedownload(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # conversiones de cadenas <-> bytes
    href = f'<a href="data:file/csv;base64,{b64}" download="crypto.csv">Descargar archivo CSV</a>'
    return href

col2.markdown(filedownload(df_selected_coin), unsafe_allow_html=True)

# Preparando datos para el gráfico de barras del cambio porcentual
col2.subheader('Tabla de Cambio Porcentual del Precio')
df_change = pd.concat([df_coins.coin_symbol, df_coins.percent_change_1h, df_coins.percent_change_24h, df_coins.percent_change_7d], axis=1)
df_change = df_change.set_index('coin_symbol')
df_change['positive_percent_change_1h'] = df_change['percent_change_1h'] > 0
df_change['positive_percent_change_24h'] = df_change['percent_change_24h'] > 0
df_change['positive_percent_change_7d'] = df_change['percent_change_7d'] > 0
col2.dataframe(df_change)

# Creación condicional del gráfico de barras (marco temporal)
col3.subheader('Gráfico de Barras del Cambio Porcentual del Precio')

if percent_timeframe == '7d':
    if sort_values == 'Sí':
        df_change = df_change.sort_values(by=['percent_change_7d'])
    col3.write('*Periodo de 7 días*')
    plt.figure(figsize=(5, 25))
    plt.subplots_adjust(top=1, bottom=0)
    df_change['percent_change_7d'].plot(kind='barh', color=df_change.positive_percent_change_7d.map({True: 'g', False: 'r'}))
    col3.pyplot(plt)
elif percent_timeframe == '24h':
    if sort_values == 'Sí':
        df_change = df_change.sort_values(by=['percent_change_24h'])
    col3.write('*Periodo de 24 horas*')
    plt.figure(figsize=(5, 25))
    plt.subplots_adjust(top=1, bottom=0)
    df_change['percent_change_24h'].plot(kind='barh', color=df_change.positive_percent_change_24h.map({True: 'g', False: 'r'}))
    col3.pyplot(plt)
else:
    if sort_values == 'Sí':
        df_change = df_change.sort_values(by=['percent_change_1h'])
    col3.write('*Periodo de 1 hora*')
    plt.figure(figsize=(5, 25))
    plt.subplots_adjust(top=1, bottom=0)
    df_change['percent_change_1h'].plot(kind='barh', color=df_change.positive_percent_change_1h.map({True: 'g', False: 'r'}))
    col3.pyplot(plt)


