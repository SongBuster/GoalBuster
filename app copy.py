import streamlit as st
import pyrebase
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import time
import os


def style_rows(df):
    def highlight_row(row):
        # Cambiar el color de la fila si el atributo es 'final'
        if row["Accion Final"] == True:
            if row["Resultado"] in valores_exito:
                return ["background-color: rgb(128,204,128)"] * len(row)
            elif row["Resultado"] in valores_fallo:            
                return ["background-color: rgb(204,128,128)"] * len(row)
        return [""] * len(row)

    # Agregar estilos condicionales
    return df.style.apply(highlight_row, axis=1)

def print_game(data):
    #st.write(f"Datos actuales:{data} ")
    fecha = data["date"].strftime("%d-%m-%Y %H:%M:%S")
    st.write(f"Actualización: {fecha}")
    rival = data["awayTeam"]
    goles_nuestros = data["ourGoals"]
    goles_rival = data["rivalGoals"]
    st.subheader(f"Agustinos: {goles_nuestros} {rival}: {goles_rival}")
    tiempo_actual = data["currentTime"]
    st.write(f"Tiempo actual: {segundos_string(tiempo_actual)}")

def segundos_string(seconds):    
    minutes = seconds // 60
    remaining = seconds % 60
    return f"{minutes:02}:{remaining:02}"

def print_actions():
    game_actions_ref = (
                    db.collection("users")
                    .document(user_id)
                    .collection("games")
                    .document(game_id)
                    .collection("gameActions")
                    .order_by("gameTime", direction=firestore.Query.DESCENDING)  # Ordenar por gameTime
                    .limit(20)
                    .stream()
                )
    game_actions = []

    for action in game_actions_ref:
        data = action.to_dict()
        if "player" in data and isinstance(data["player"],dict):
            player = data["player"]
            data["player"] = f"{player.get('jersey','')}-{player.get('name','')}"

        if "gameTime" in data:            
            seconds = data["gameTime"]
            data["gameTime"] = segundos_string(seconds)        

        game_actions.append(data)

    if game_actions:
        # Convertir las acciones en una tabla        
        column_mapping = {"gameTime" : "Tiempo", "player" : "Jugador", "actionLiteral" : "Acción", "actionResult" : "Resultado", "isFinalPlay" : "Accion Final"}
        df = pd.DataFrame(game_actions)
        df.rename(columns=column_mapping, inplace=True)
        desired_columns = list(column_mapping.values())
        df = df[desired_columns]
        df.reset_index(drop=True, inplace=True)
        st.write("Últimas acciones:")
        styled_df = style_rows(df)
        st.dataframe(styled_df, use_container_width=True)  # Muestra los datos como tabla interactiva
    else:
        st.warning("No se encontraron acciones para este juego.")



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

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

# Inicializa Firestore con Firebase Admin
@st.cache_resource
def init_firestore():
    cred = credentials.Certificate(firebase_creedentials)  # Ruta a tu archivo JSON de credenciales
    firebase_admin.initialize_app(cred)
    return firestore.client()

db = init_firestore()

email = "handballlivestats@gmail.com"
password = "d43HANn3rys"
game_id = "DIRECTO"

valores_exito = {"GOL","PARADA","FALLO RIVAL","GOL+ASISTENCIA","EXITO"}
valores_fallo = {"FRACASO","GOL RIVAL","PARADA RIVAL","FALLO"}

try:
    # Autenticar usuario
    user = auth.sign_in_with_email_and_password(email, password)
    #st.success(f"Autenticado como: {user['email']}")

    # Obtener el UID del usuario autenticado
    user_id = user['localId']  # Este es el UID único del usuario en Firebase Authentication

    # Obtener la subcolección `games` del usuario
   
    
    placeholder = st.empty()

    refresh_interval = st.slider("Intervalo de actualización (segundos)", min_value=30, max_value=180, value=60)

    while True:
        games_ref = db.collection("users").document(user_id).collection("games").document(game_id)            
        doc = games_ref.get()
        if doc.exists:
            with placeholder.container():                
                print_game(doc.to_dict())
                print_actions()

            time.sleep(refresh_interval)
        else:
            with placeholder.container():
                    st.warning("No se encontraron acciones para este juego.")
except Exception as e:
    st.error(f"Error al autenticar o recuperar datos: {e}")

