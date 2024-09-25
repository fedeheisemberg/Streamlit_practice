import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st

# Autenticación con Google Sheets
def authenticate_google_sheets(json_keyfile):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile, scope)
    client = gspread.authorize(creds)
    return client

# Función para guardar el email en Google Sheets
def save_email_to_sheet(email, sheet_name, client):
    sheet = client.open(sheet_name).sheet1
    existing_emails = sheet.col_values(1)  # Suponiendo que la primera columna es donde se almacenan los emails

    if email not in existing_emails:
        sheet.append_row([email])
        return True
    return False

# Función de suscripción principal
def subscribe_user(email, sheet_name, json_keyfile):
    client = authenticate_google_sheets(json_keyfile)
    return save_email_to_sheet(email, sheet_name, client)
