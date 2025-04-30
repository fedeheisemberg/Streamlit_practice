# 📊 Simulador Monte Carlo para Análisis de Inversiones 📈

## Descripción
Este dashboard avanzado utiliza simulaciones Monte Carlo para proporcionar análisis detallados sobre posibles trayectorias futuras de activos financieros. La aplicación permite a inversores y analistas visualizar distintos escenarios de inversión, cuantificar riesgos y tomar decisiones más informadas basadas en datos estadísticos.


## 🌟 Características principales

- **🚀 Análisis dinámico de activos** - Acciones, ETFs, criptomonedas y más
- **📊 Simulaciones Monte Carlo personalizables** - Miles de posibles trayectorias futuras
- **💰 Proyección de retornos de inversiones** - Modelado de rendimientos ajustados por costos
- **📉 Análisis de drawdown** - Visualización y cuantificación de posibles caídas
- **⚠️ Evaluación de riesgos** - VaR, probabilidades e intervalos de confianza
- **🧮 Métricas de rendimiento** - Ratios de Sharpe, probabilidades de ganancia y más
- **🎯 Intervalos de confianza interactivos** - Para diferentes niveles de tolerancia al riesgo
- **📚 Recursos educativos integrados** - Explicaciones detalladas de cada visualización

## 🔧 Tecnologías utilizadas

- **Streamlit** - Framework para aplicaciones de datos interactivas
- **YFinance** - API para obtención de datos financieros históricos
- **Pandas/NumPy** - Procesamiento y análisis de datos
- **Plotly** - Visualizaciones interactivas avanzadas
- **Monte Carlo** - Técnicas estadísticas para modelado de incertidumbre

## 📋 Requisitos previos

- Python 3.8 o superior
- Pip (gestor de paquetes de Python)

## 🚀 Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/fedemartiinez/monte-carlo-finance.git
cd monte-carlo-finance
```

2. Crear y activar un entorno virtual (opcional pero recomendado):
```bash
python -m venv venv
# En Windows:
venv\Scripts\activate
# En macOS/Linux:
source venv/bin/activate
```

3. Instalar las dependencias:
```bash
pip install -r requirements.txt
```

4. Ejecutar la aplicación:
```bash
streamlit run app.py
```

## 🖥️ Uso

1. Ingresar el símbolo del activo que desea analizar (ej. AAPL, MSFT, BTC-USD)
2. Ajustar parámetros según sus necesidades:
   - Número de simulaciones
   - Período de pronóstico
   - Inversión inicial
   - Fechas para análisis histórico
3. Explorar visualizaciones interactivas y análisis estadísticos
4. Utilizar las explicaciones detalladas para interpretar los resultados

## 🔍 Principales secciones de la aplicación

### 📈 Proyección de Precios
Visualización de posibles trayectorias de precios futuros con bandas de confianza.

### 💰 Rendimiento de la Inversión
Proyección de capital y análisis de drawdown con percentiles estadísticos.

### 📊 Distribución de Resultados Finales
Histograma de posibles retornos finales con métricas clave (media, mediana, VaR).

### 📈 Estadísticas de Rendimiento y Riesgo
Métricas detalladas sobre rendimiento esperado y posibles riesgos.

### 🎯 Intervalos de Confianza
Visualización de rangos de retornos esperados para diferentes niveles de confianza estadística.

### 🧠 Conclusiones y Recomendaciones
Análisis automatizado y recomendaciones basadas en los resultados de las simulaciones.

## 📊 Detalles técnicos

### Metodología Monte Carlo

La aplicación utiliza el método Monte Carlo para generar miles de posibles trayectorias futuras basadas en la volatilidad histórica y el rendimiento medio del activo seleccionado. Específicamente:

1. Calcula los retornos logarítmicos diarios del activo histórico
2. Estima la media (drift) y desviación estándar (volatilidad)
3. Simula múltiples trayectorias aleatorias usando estos parámetros
4. Incorpora costos de transacción y slippage para un modelo más realista
5. Calcula métricas de riesgo y rendimiento a partir de las simulaciones

### Consideraciones matemáticas

- Utiliza movimiento browniano geométrico (GBM) para modelar precios de activos
- Incluye costos de transacción y slippage para mayor realismo
- Calcula múltiples percentiles para cuantificar la incertidumbre
- Implementa Value at Risk (VaR) y otras métricas estadísticas

## 🤝 Contribución

Las contribuciones son bienvenidas. Para cambios importantes, por favor abra primero un issue para discutir lo que le gustaría cambiar.

## 📝 Licencia

[MIT](https://choosealicense.com/licenses/mit/)

## 👤 Autor

**Federico Martinez**


---

⭐️ Si encuentras útil este proyecto, ¡no dudes en darle una estrella en GitHub!