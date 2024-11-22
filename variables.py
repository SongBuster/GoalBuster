import streamlit as st

firebase_config =  {
    "apiKey": st.secrets["firebase_config"]["API_KEY"],
    "authDomain": st.secrets["firebase_config"]["AUTH_DOMAIN"],
    "databaseURL": st.secrets["firebase_config"]["DATABASE_URL"],
    "storageBucket": st.secrets["firebase_config"]["STORAGE_BUCKET"],
    "messagingSenderId": st.secrets["firebase_config"]["MESSAGING_SENDER_ID"],
    "appId": st.secrets["firebase_config"]["APP_ID"],
}

firebase_creedentials = {
    "type": st.secrets["firebase_credentials"]["FIREBASE_TYPE"], 
    "project_id": st.secrets["firebase_credentials"]["FIREBASE_PROJECT_ID"] , 
    "private_key_id": st.secrets["firebase_credentials"]["FIREBASE_PRIVATE_KEY_ID"] ,
    "private_key": st.secrets["firebase_credentials"]["FIREBASE_PRIVATE_KEY"].replace("\\n", "\n"),
    "client_email": st.secrets["firebase_credentials"]["FIREBASE_CLIENT_EMAIL"],
    "client_id": st.secrets["firebase_credentials"]["FIREBASE_CLIENT_ID"],
    "token_uri" : st.secrets["firebase_credentials"]["TOKEN_URI"],
    "auth_provider_x509_cert_url" : st.secrets["firebase_credentials"]["AUTH_X509_CERT"],
    "client_x509_cert_url" : st.secrets["firebase_credentials"]["CLIENT_X509_CERT"],
    "universe_domain" : st.secrets["firebase_credentials"]["UNIVERSE_DOMAIN"],
}


email = "handballlivestats@gmail.com"
password = "d43HANn3rys"
game_id = "DIRECTO"

valores_exito = {"GOL","PARADA","FALLO RIVAL","GOL+ASISTENCIA","EXITO"}
valores_fallo = {"FRACASO","GOL RIVAL","PARADA RIVAL","FALLO"}

user_id = ""

max_rows_in_table = 20