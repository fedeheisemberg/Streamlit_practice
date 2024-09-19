import streamlit as st
import pandas as pd
import numpy as np
import pickle
from sklearn.ensemble import RandomForestClassifier

st.write("""
# Aplicación de Predicción de Pingüinos

¡Esta aplicación predice la especie de **Pingüino de Palmer**!

Datos obtenidos de la [biblioteca palmerpenguins](https://github.com/allisonhorst/palmerpenguins) en R por Allison Horst.
""")

st.sidebar.header('Características de Entrada del Usuario')

st.sidebar.markdown("""
[Archivo CSV de ejemplo](https://raw.githubusercontent.com/dataprofessor/data/master/penguins_example.csv)
""")

# Recoge las características de entrada del usuario en un dataframe
uploaded_file = st.sidebar.file_uploader("Sube tu archivo CSV de entrada", type=["csv"])
if uploaded_file is not None:
    input_df = pd.read_csv(uploaded_file)
else:
    def user_input_features():
        island = st.sidebar.selectbox('Isla',('Biscoe','Dream','Torgersen'))
        sex = st.sidebar.selectbox('Sexo',('masculino','femenino'))
        bill_length_mm = st.sidebar.slider('Longitud del pico (mm)', 32.1,59.6,43.9)
        bill_depth_mm = st.sidebar.slider('Profundidad del pico (mm)', 13.1,21.5,17.2)
        flipper_length_mm = st.sidebar.slider('Longitud de la aleta (mm)', 172.0,231.0,201.0)
        body_mass_g = st.sidebar.slider('Masa corporal (g)', 2700.0,6300.0,4207.0)
        data = {'isla': island,
                'longitud_pico_mm': bill_length_mm,
                'profundidad_pico_mm': bill_depth_mm,
                'longitud_aleta_mm': flipper_length_mm,
                'masa_corporal_g': body_mass_g,
                'sexo': sex}
        features = pd.DataFrame(data, index=[0])
        return features
    input_df = user_input_features()

# Combina las características de entrada del usuario con el conjunto de datos completo de pingüinos
# Esto será útil para la fase de codificación
penguins_raw = pd.read_csv('penguins_cleaned.csv')
penguins = penguins_raw.drop(columns=['species'])
df = pd.concat([input_df,penguins],axis=0)

# Codificación de características ordinales
# https://www.kaggle.com/pratik1120/penguin-dataset-eda-classification-and-clustering
encode = ['sexo','isla']
for col in encode:
    dummy = pd.get_dummies(df[col], prefix=col)
    df = pd.concat([df,dummy], axis=1)
    del df[col]
df = df[:1] # Selecciona solo la primera fila (los datos de entrada del usuario)

# Muestra las características de entrada del usuario
st.subheader('Características de Entrada del Usuario')

if uploaded_file is not None:
    st.write(df)
else:
    st.write('Esperando a que se suba el archivo CSV. Actualmente utilizando parámetros de entrada de ejemplo (mostrados a continuación).')
    st.write(df)

# Lee el modelo de clasificación guardado
load_clf = pickle.load(open('penguins_clf.pkl', 'rb'))

# Aplica el modelo para hacer predicciones
prediction = load_clf.predict(df)
prediction_proba = load_clf.predict_proba(df)

st.subheader('Predicción')
penguins_species = np.array(['Adelie','Chinstrap','Gentoo'])
st.write(penguins_species[prediction])

st.subheader('Probabilidad de Predicción')
st.write(prediction_proba)
