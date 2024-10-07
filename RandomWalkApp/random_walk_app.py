import streamlit as st
import numpy as np
import plotly.graph_objects as go
import plotly.figure_factory as ff

def simular_caminatas_aleatorias(num_simulaciones, num_pasos, valor_inicial, prob_subida, prob_bajada, prob_gran_subida):
    todas_caminatas = []
    for _ in range(num_simulaciones):
        caminata = [valor_inicial]
        for _ in range(num_pasos):
            paso = caminata[-1]
            rand = np.random.random()
            if rand < prob_bajada:
                paso = max(0, paso - 1)
            elif rand < prob_bajada + prob_subida:
                paso += 1
            elif rand < prob_bajada + prob_subida + prob_gran_subida:
                paso += np.random.randint(1, 7)
            else:
                paso = paso  # Sin cambio
            caminata.append(paso)
        todas_caminatas.append(caminata)
    return np.array(todas_caminatas)

def graficar_caminatas_aleatorias(caminatas, titulo):
    fig = go.Figure()
    for caminata in caminatas:
        fig.add_trace(go.Scatter(y=caminata, mode='lines', opacity=0.3))
    fig.update_layout(
        title=titulo,
        xaxis_title='Número de Pasos',
        yaxis_title='Valor',
        showlegend=False
    )
    return fig

def graficar_distribucion_final(caminatas):
    valores_finales = caminatas[:, -1]
    fig = ff.create_distplot([valores_finales], ['Distribución'], bin_size=1, show_hist=False, show_rug=False)
    fig.update_layout(
        title='Distribución de Valores Finales',
        xaxis_title='Valor Final',
        yaxis_title='Densidad'
    )
    return fig

def main():
    st.set_page_config(page_title="Simulador de Caminata Aleatoria", layout="wide")
    st.title('Simulador de Caminata Aleatoria')
    st.write('Esta aplicación simula caminatas aleatorias y visualiza los resultados.')

    # Barra lateral para entradas del usuario
    st.sidebar.header('Parámetros de Simulación')
    num_simulaciones = st.sidebar.slider('Número de Simulaciones', 10, 1000, 100)
    num_pasos = st.sidebar.slider('Número de Pasos', 10, 1000, 100)
    valor_inicial = st.sidebar.number_input('Valor Inicial', 0, 1000, 0)
    
    st.sidebar.header('Parámetros de Probabilidad')
    prob_bajada = st.sidebar.slider('Probabilidad de Bajar', 0.0, 1.0, 0.3)
    prob_subida = st.sidebar.slider('Probabilidad de Subir', 0.0, 1.0, 0.5)
    prob_gran_subida = st.sidebar.slider('Probabilidad de Gran Subida', 0.0, 1.0, 0.1)

    # Asegurar que las probabilidades sumen 1
    prob_total = prob_bajada + prob_subida + prob_gran_subida
    if prob_total > 1:
        st.sidebar.error('La probabilidad total excede 1. Ajustando probabilidades...')
        prob_bajada /= prob_total
        prob_subida /= prob_total
        prob_gran_subida /= prob_total

    # Ejecutar simulación
    if st.button('Ejecutar Simulación'):
        caminatas = simular_caminatas_aleatorias(num_simulaciones, num_pasos, valor_inicial, prob_subida, prob_bajada, prob_gran_subida)

        # Gráfico de caminatas aleatorias
        fig_caminatas = graficar_caminatas_aleatorias(caminatas, 'Simulaciones de Caminata Aleatoria')
        st.plotly_chart(fig_caminatas, use_container_width=True)

        # Gráfico de distribución final
        fig_dist = graficar_distribucion_final(caminatas)
        st.plotly_chart(fig_dist, use_container_width=True)

        # Estadísticas
        st.subheader('Estadísticas de la Simulación')
        valores_finales = caminatas[:, -1]
        col1, col2 = st.columns(2)
        with col1:
            st.write(f'Valor final medio: {valores_finales.mean():.2f}')
            st.write(f'Valor final mediano: {np.median(valores_finales):.2f}')
            st.write(f'Desviación estándar de valores finales: {valores_finales.std():.2f}')
        with col2:
            st.write(f'Valor final mínimo: {valores_finales.min():.2f}')
            st.write(f'Valor final máximo: {valores_finales.max():.2f}')

if __name__ == '__main__':
    main()