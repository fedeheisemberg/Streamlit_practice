import streamlit as st
import yfinance as yf
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scikitplot as skplt
from lime import lime_tabular

# Función para obtener datos de Yahoo Finance
def get_stock_data(ticker, start_date, end_date):
    stock_data = yf.download(ticker, start=start_date, end=end_date)
    return stock_data

# Función para preparar los datos
def prepare_data(df):
    # Calcular características técnicas
    df['Returns'] = df['Close'].pct_change()
    df['SMA_5'] = df['Close'].rolling(window=5).mean()
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['Volatility'] = df['Returns'].rolling(window=20).std()
    
    # Crear variable objetivo (1 si sube, 0 si baja)
    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    
    # Eliminar filas con valores NaN
    df.dropna(inplace=True)
    
    return df

# Cargar y preparar los datos
ticker = 'AAPL'  # Puedes cambiar esto a cualquier símbolo de acción
start_date = '2010-01-01'
end_date = '2023-09-20'

stock_data = get_stock_data(ticker, start_date, end_date)
prepared_data = prepare_data(stock_data)

# Definir características y objetivo
features = ['Returns', 'SMA_5', 'SMA_20', 'Volatility']
X = prepared_data[features]
y = prepared_data['Target']

# Dividir los datos
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Escalar las características
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Entrenar el modelo
rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X_train_scaled, y_train)

# Hacer predicciones
y_pred = rf_model.predict(X_test_scaled)

# Panel de control de Streamlit
st.title(f"Predicción del Precio de la Acción de {ticker} :chart_with_upwards_trend:")

tab1, tab2, tab3 = st.tabs(["Datos :clipboard:", "Rendimiento Global :weight_lifter:", "Predicción :crystal_ball:"])

with tab1:
    st.header("Conjunto de Datos de la Acción")
    st.write(prepared_data)

with tab2:
    st.header("Matriz de Confusión | Importancia Global de Características")
    col1, col2 = st.columns(2)
    with col1:
        # Matriz de Confusión
        conf_mat_fig = plt.figure(figsize=(6,6))
        ax1 = conf_mat_fig.add_subplot(111)
        skplt.metrics.plot_confusion_matrix(y_test, y_pred, ax=ax1)
        st.pyplot(conf_mat_fig, use_container_width=True)

    with col2:
        # Importancia de las Características
        feat_imp_fig = plt.figure(figsize=(6,6))
        ax1 = feat_imp_fig.add_subplot(111)
        skplt.estimators.plot_feature_importances(rf_model, feature_names=features, ax=ax1,
                                                  title="Importancia de las Características", x_tick_rotation=45)
        st.pyplot(feat_imp_fig, use_container_width=True)

    st.divider()
    st.header("Reporte de Clasificación")
    st.code(classification_report(y_test, y_pred))

with tab3:
    st.header("Predicción para el Siguiente Día")
    
    col1, col2 = st.columns(2, gap="medium")
    input_features = {}
    
    with col1:
        for feature in features:
            input_features[feature] = st.number_input(f"{feature}", value=float(X[feature].mean()), 
                                                      step=float(X[feature].std()/10))

    with col2:
        input_array = np.array([input_features[f] for f in features]).reshape(1, -1)
        input_scaled = scaler.transform(input_array)
        prediction = rf_model.predict(input_scaled)
        probability = rf_model.predict_proba(input_scaled)[0]

        st.markdown(f"#### Predicción: <strong style='color:{'green' if prediction[0] == 1 else 'red'};'>"
                    f"{'Subir' if prediction[0] == 1 else 'Bajar'}</strong>", unsafe_allow_html=True)
        
        st.metric(label="Confianza del Modelo", 
                  value=f"{probability[prediction[0]]:.2f}",
                  delta=f"{probability[prediction[0]] - 0.5:.2f}")

    # LIME para interpretación local
    explainer = lime_tabular.LimeTabularExplainer(X_train_scaled, mode="classification", 
                                                  feature_names=features, class_names=['Bajar', 'Subir'])
    explanation = explainer.explain_instance(input_scaled[0], rf_model.predict_proba, num_features=len(features), top_labels=2)
    
    st.pyplot(explanation.as_pyplot_figure(), use_container_width=True)