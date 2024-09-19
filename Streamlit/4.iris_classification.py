import streamlit as st
import pandas as pd
from sklearn import datasets
from sklearn.ensemble import RandomForestClassifier

st.write("""
# Aplicación de Predicción de Flores Iris

¡Esta aplicación predice el tipo de **flor Iris**!
""")

st.sidebar.header('Parámetros de Entrada del Usuario')

def user_input_features():
    sepal_length = st.sidebar.slider('Longitud del sépalo', 4.3, 7.9, 5.4)
    sepal_width = st.sidebar.slider('Ancho del sépalo', 2.0, 4.4, 3.4)
    petal_length = st.sidebar.slider('Longitud del pétalo', 1.0, 6.9, 1.3)
    petal_width = st.sidebar.slider('Ancho del pétalo', 0.1, 2.5, 0.2)
    data = {'Longitud del sépalo': sepal_length,
            'Ancho del sépalo': sepal_width,
            'Longitud del pétalo': petal_length,
            'Ancho del pétalo': petal_width}
    features = pd.DataFrame(data, index=[0])
    return features

df = user_input_features()

st.subheader('Parámetros de Entrada del Usuario')
st.write(df)

iris = datasets.load_iris()
X = iris.data
Y = iris.target

clf = RandomForestClassifier()
clf.fit(X, Y)

prediction = clf.predict(df)
prediction_proba = clf.predict_proba(df)

st.subheader('Etiquetas de Clase y sus números de índice correspondientes')
st.write(iris.target_names)

st.subheader('Predicción')
st.write(iris.target_names[prediction])

st.subheader('Probabilidad de Predicción')
st.write(prediction_proba)
