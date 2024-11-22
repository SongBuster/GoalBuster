import streamlit as st
import pyrebase
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import time
import os

import variables as v
import functions as fn

firebase = pyrebase.initialize_app(v.firebase_config)
auth = firebase.auth()

# Inicializa Firestore con Firebase Admin
@st.cache_resource
def init_firestore():
    cred = credentials.Certificate(v.firebase_creedentials)  # Ruta a tu archivo JSON de credenciales
    firebase_admin.initialize_app(cred)
    return firestore.client()


db = init_firestore()

try:
    # Autenticar usuario
    user = auth.sign_in_with_email_and_password(v.email, v.password)
    #st.success(f"Autenticado como: {user['email']}")

    # Obtener el UID del usuario autenticado
    v.user_id = user['localId']  # Este es el UID único del usuario en Firebase Authentication

    placeholder = st.empty()

    refresh_interval = st.slider("Intervalo de actualización (segundos)", min_value=30, max_value=180, value=60)

    while True:
        games_ref = db.collection("users").document(v.user_id).collection("games").document(v.game_id)            
        doc = games_ref.get()
        if doc.exists:
            with placeholder.container():                
                fn.print_game(doc.to_dict())
                options = ["Jugadas","Jugadores en Pista"]
                selected_option = st.selectbox("Selecciona una vista", options)
                if selected_option == "Jugadas":
                    fn.print_actions_table(db)
                elif selected_option == "Jugadores en Pista":
                    fn.print_court_players(db)

            time.sleep(refresh_interval)
        else:
            with placeholder.container():
                    st.warning("No se encontraron acciones para este juego.")
except Exception as e:
    st.error(f"Error al autenticar o recuperar datos: {e}")

