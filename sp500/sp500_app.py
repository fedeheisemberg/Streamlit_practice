import streamlit as st
import pandas as pd
import base64
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import yfinance as yf

st.title('S&P 500')

st.markdown("""
Esta aplicación recupera la lista de las empresas del **S&P 500** (de Wikipedia) y su correspondiente **precio de cierre de las acciones** (del año hasta la fecha)!
* **Bibliotecas de Python:** base64, pandas, streamlit, numpy, matplotlib, seaborn
* **Fuente de datos:** [Wikipedia](https://en.wikipedia.org/wiki/List_of_S%26P_500_companies).
""")

st.sidebar.header('Características de Entrada del Usuario')

# Web scraping de datos del S&P 500
@st.cache_data
def load_data():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    html = pd.read_html(url, header = 0)
    df = html[0]
    return df

df = load_data()
sector = df.groupby('GICS Sector')

# Barra lateral - Selección de sector
sorted_sector_unique = sorted( df['GICS Sector'].unique() )
selected_sector = st.sidebar.multiselect('Sector', sorted_sector_unique, sorted_sector_unique)

# Filtrado de datos
df_selected_sector = df[ (df['GICS Sector'].isin(selected_sector)) ]

st.header('Mostrar Empresas en el Sector Seleccionado')
st.write('Dimensión de los Datos: ' + str(df_selected_sector.shape[0]) + ' filas y ' + str(df_selected_sector.shape[1]) + ' columnas.')
st.dataframe(df_selected_sector)

# Descargar datos del S&P500
def filedownload(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # conversiones strings <-> bytes
    href = f'<a href="data:file/csv;base64,{b64}" download="SP500.csv">Descargar Archivo CSV</a>'
    return href

st.markdown(filedownload(df_selected_sector), unsafe_allow_html=True)

# Descargar datos de Yahoo Finance
data = yf.download(
        tickers = list(df_selected_sector[:10].Symbol),
        period = "5y",
        interval = "1d",
        group_by = 'ticker',
        auto_adjust = True,
        prepost = True,
        threads = True,
        proxy = None
    )

# Graficar el Precio de Cierre del Símbolo Consultado
def price_plot(symbol):
    fig, ax = plt.subplots(figsize=(10, 5))
    df = pd.DataFrame(data[symbol].Close)
    df['Date'] = df.index
    ax.fill_between(df.Date, df.Close, color='skyblue', alpha=0.3)
    ax.plot(df.Date, df.Close, color='skyblue', alpha=0.8)
    plt.xticks(rotation=90)
    plt.title(symbol, fontweight='bold')
    plt.xlabel('Fecha', fontweight='bold')
    plt.ylabel('Precio de Cierre', fontweight='bold')
    return fig

num_company = st.sidebar.slider('Número de Empresas', 1, 10)

# Modificar la sección donde se muestran los gráficos
if st.button('Mostrar Gráficos'):
    st.header('Precio de Cierre de las Acciones')
    for i in list(df_selected_sector.Symbol)[:num_company]:
        fig = price_plot(i)
        st.pyplot(fig)
        plt.close(fig)  # Cerrar la figura para liberar memoria