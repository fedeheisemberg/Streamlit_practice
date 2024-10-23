import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import os
import sys
from pathlib import Path

# Asegurar que streamlit pueda encontrar el módulo
file_path = Path(__file__).parent.absolute()
sys.path.append(str(file_path))

def get_stock_data(ticker):
    """Obtiene datos del activo desde Yahoo Finance"""
    stock = yf.Ticker(ticker)
    current_price = stock.info['regularMarketPrice']
    return current_price, stock

def calculate_factors(volatility, delta_t):
    """Calcula los factores u y d del modelo binomial"""
    u = np.exp(volatility * np.sqrt(delta_t))
    d = 1/u
    return u, d

def calculate_risk_neutral_probability(r, u, d, delta_t):
    """Calcula la probabilidad neutral al riesgo"""
    p = (np.exp(r * delta_t) - d) / (u - d)
    return p

def create_price_tree(S0, u, d, steps):
    """Crea el árbol de precios"""
    tree = np.zeros((steps + 1, steps + 1))
    for i in range(steps + 1):
        for j in range(i + 1):
            tree[j, i] = S0 * (u ** (i - j)) * (d ** j)
    return tree

def create_option_tree(price_tree, K, r, p, delta_t, steps, option_type='call', american=False):
    """Crea el árbol de valores de la opción"""
    option_tree = np.zeros((steps + 1, steps + 1))
    
    # Valores finales
    if option_type.lower() == 'call':
        option_tree[:, steps] = np.maximum(price_tree[:, steps] - K, 0)
    else:  # put
        option_tree[:, steps] = np.maximum(K - price_tree[:, steps], 0)
    
    # Retroceder en el árbol
    for i in range(steps-1, -1, -1):
        for j in range(i + 1):
            hold_value = np.exp(-r * delta_t) * (
                p * option_tree[j, i + 1] + 
                (1 - p) * option_tree[j + 1, i + 1]
            )
            
            if american:
                if option_type.lower() == 'call':
                    exercise_value = price_tree[j, i] - K
                else:  # put
                    exercise_value = K - price_tree[j, i]
                option_tree[j, i] = max(hold_value, exercise_value)
            else:
                option_tree[j, i] = hold_value
                
    return option_tree

def plot_trees(price_tree, option_tree, steps):
    """Crea visualizaciones de los árboles usando plotly"""
    def create_node_trace(x, y, values, name):
        return go.Scatter(
            x=x, y=y,
            mode='markers+text',
            name=name,
            text=[f'{v:.2f}' for v in values],
            textposition='top center',
            marker=dict(size=10)
        )

    fig = go.Figure()
    
    for i in range(steps + 1):
        x = [i] * (i + 1)
        y = list(range(i + 1))
        
        # Añadir nodos de precio
        fig.add_trace(create_node_trace(
            x, y,
            price_tree[:i+1, i],
            f'Precio paso {i}'
        ))
        
        # Añadir nodos de opción
        fig.add_trace(create_node_trace(
            x, [-y_ - 2 for y_ in y],
            option_tree[:i+1, i],
            f'Opción paso {i}'
        ))

    fig.update_layout(
        title='Árboles de Precio y Valor de la Opción',
        showlegend=True,
        height=800
    )
    
    return fig

# Interfaz de Streamlit
st.title('Calculadora de Opciones - Modelo Binomial')

# Input del usuario
col1, col2 = st.columns(2)

with col1:
    ticker = st.text_input('Símbolo del activo (ej: GGAL)', 'GGAL')
    try:
        current_price, stock = get_stock_data(ticker)
        st.success(f'Precio actual de {ticker}: ${current_price:.2f}')
    except:
        st.error('Error al obtener datos. Verifica el símbolo.')
        current_price = 100  # valor por defecto
    
    strike = st.number_input('Precio de ejercicio (Strike)', 
                            min_value=0.0, 
                            value=float(current_price))
    
    volatility = st.number_input('Volatilidad anual (%)', 
                                min_value=0.0, 
                                value=30.0) / 100
    
    risk_free_rate = st.number_input('Tasa libre de riesgo (%)', 
                                    min_value=0.0, 
                                    value=5.0) / 100

with col2:
    time_to_expiry = st.number_input('Tiempo hasta vencimiento (días)', 
                                    min_value=1, 
                                    value=30)
    
    steps = st.number_input('Número de pasos', 
                           min_value=1, 
                           max_value=50,
                           value=5)
    
    option_type = st.selectbox('Tipo de opción', 
                              ['Call', 'Put'])
    
    american = st.checkbox('Opción Americana', 
                          value=False)

if st.button('Calcular'):
    # Cálculos
    delta_t = time_to_expiry / 365 / steps
    u, d = calculate_factors(volatility, delta_t)
    p = calculate_risk_neutral_probability(risk_free_rate, u, d, delta_t)
    
    # Crear árboles
    price_tree = create_price_tree(current_price, u, d, steps)
    option_tree = create_option_tree(
        price_tree, strike, risk_free_rate, p, delta_t, 
        steps, option_type, american
    )
    
    # Mostrar resultado
    option_price = option_tree[0, 0]
    st.success(f'Precio de la opción: ${option_price:.2f}')
    
    # Mostrar parámetros calculados
    st.write('### Parámetros del modelo')
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f'Factor u: {u:.4f}')
    with col2:
        st.write(f'Factor d: {d:.4f}')
    with col3:
        st.write(f'Probabilidad p: {p:.4f}')
    
    # Visualización
    fig = plot_trees(price_tree, option_tree, steps)
    st.plotly_chart(fig)
    
    # Mostrar árboles en formato tabular
    st.write('### Árbol de precios del activo')
    st.dataframe(pd.DataFrame(price_tree))
    
    st.write('### Árbol de valores de la opción')
    st.dataframe(pd.DataFrame(option_tree))

st.markdown("""
### Notas:
- Los precios se obtienen en tiempo real de Yahoo Finance
- La volatilidad debe ingresarse como porcentaje anual
- La tasa libre de riesgo debe ingresarse como porcentaje anual
- El tiempo hasta el vencimiento se ingresa en días
- Los árboles muestran tanto los precios del activo como los valores de la opción en cada nodo
""")