import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st

def authenticate_google_sheets():
    json_keyfile = {
        "type": st.secrets["gcp_service_account"]["type"],
        "project_id": st.secrets["gcp_service_account"]["project_id"],
        "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
        "private_key": st.secrets["gcp_service_account"]["private_key"],
        "client_email": st.secrets["gcp_service_account"]["client_email"],
        "client_id": st.secrets["gcp_service_account"]["client_id"],
        "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
        "token_uri": st.secrets["gcp_service_account"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"]
    }
    
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(json_keyfile, scope)
    client = gspread.authorize(creds)
    return client

def save_feedback(email, feedback, sheet_name):
    try:
        client = authenticate_google_sheets()
        sheet = client.open(sheet_name).sheet1
        
        # Get all existing emails
        existing_emails = sheet.col_values(1)[1:]  # Exclude header
        
        if email in existing_emails:
            # If email exists, update the feedback in the corresponding row
            row_index = existing_emails.index(email) + 2  # +2 for header and 0-indexing
            sheet.update_cell(row_index, 2, feedback)
        else:
            # If email doesn't exist, append a new row
            sheet.append_row([email, feedback])
        
        return True
    except Exception as e:
        st.error(f"Error al guardar el feedback: {e}")
        return False



