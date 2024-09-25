import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st

# Función de autenticación con Google Sheets
def authenticate_google_sheets():
    # Obtener las credenciales desde st.secrets
    json_keyfile = {
        "type": st.secrets["google_service_account"]["type"],
        "project_id": st.secrets["google_service_account"]["project_id"],
        "private_key_id": st.secrets["google_service_account"]["private_key_id"],
        "private_key": st.secrets["google_service_account"]["private_key"],
        "client_email": st.secrets["google_service_account"]["client_email"],
        "client_id": st.secrets["google_service_account"]["client_id"],
        "auth_uri": st.secrets["google_service_account"]["auth_uri"],
        "token_uri": st.secrets["google_service_account"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["google_service_account"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["google_service_account"]["client_x509_cert_url"]
    }
    
    # Definir los alcances (scopes)
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(json_keyfile, scope)
    client = gspread.authorize(creds)
    return client

# Función de suscripción principal
def subscribe_user(email, sheet_name):
    try:
        client = authenticate_google_sheets()
        sheet = client.open(sheet_name).sheet1  # Abre la primera hoja del archivo de Google Sheets

        # Verifica si el email ya está registrado
        existing_emails = sheet.col_values(1)  # Obtiene todos los correos electrónicos de la primera columna
        if email in existing_emails:
            return False

        # Si el email no está registrado, lo agrega
        sheet.append_row([email])
        return True
    except Exception as e:
        st.error(f"Error en la suscripción: {e}")
        return False

