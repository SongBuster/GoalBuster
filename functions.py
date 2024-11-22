import streamlit as st
import variables as v
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd

def style_rows(df):
    def highlight_row(row):
        # Cambiar el color de la fila si el atributo es 'final'
        if row["Accion Final"] == True:
            if row["Resultado"] in v.valores_exito:
                return ["background-color: rgb(128,204,128)"] * len(row)
            elif row["Resultado"] in v.valores_fallo:            
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

def fetch_actions(db):
    game_actions_ref = (
                    db.collection("users")
                    .document(v.user_id)
                    .collection("games")
                    .document(v.game_id)
                    .collection("gameActions")                    
                    .order_by("gameTime", direction=firestore.Query.DESCENDING)  # Ordenar por gameTime                 
                    .stream()
                )

    return game_actions_ref

def print_actions_table(db):

    game_actions_no_subst = ["Ataque","Defensa","Cambio","Sanción","Portero","Equipo"]

    game_actions_ref = fetch_actions(db)
    
    filtered_actions = [
        doc.to_dict() for doc in game_actions_ref if doc.to_dict().get("actionType") != "Cambio"
    ][:v.max_rows_in_table]

    game_actions = []

    for action in filtered_actions:                
        player = action.get("player","")
        action["player"] = f"{player.get('jersey','')}-{player.get('name','')}"
                
        seconds = action.get("gameTime",0)
        action["gameTime"] = segundos_string(seconds) 
        
        game_actions.append(action)

        if action["isFinalPlay"]:
            if action["actionResult"] in v.valores_exito:
                action["backgroundColor"] = '#d4edda'
            else:
                action["backgroundColor"] = "#f8d7da"
        else:
            action["backgroundColor"] = "#ffffff"
    
    html_rows = "".join(f"""
<tr style="background-color: {action.get('backgroundColor','#ffffff')}">
    <td style="border: 1px solid black; padding: 5px;">{action.get('gameTime','')}</td>
    <td style="border: 1px solid black; padding: 5px;">{action.get('player','')}</td>
    <td style="border: 1px solid black; padding: 5px;">{action.get('actionLiteral','')}</td>
    <td style="border: 1px solid black; padding: 5px;">{action.get('actionResult','')}</td>
</tr>
""" for action in game_actions)
            

    html_table = f"""
<table style="width:100%; border: 1px solid black; border-collapse: collapse;">
    <thead style="background-color: #343a40; color: white;">
        <tr>
            <th style="border: 1px solid black; padding: 5px;">Tiempo</th>
            <th style="border: 1px solid black; padding: 5px;">Jugador</th>
            <th style="border: 1px solid black; padding: 5px;">Jugada</th>
            <th style="border: 1px solid black; padding: 5px;">Resultado</th>
        </tr>
    </thead>
    {html_rows}
</table>
"""
    st.markdown(html_table, unsafe_allow_html=True)


def print_court_players(db):
    game_actions_ref = (
                    db.collection("users")
                    .document(v.user_id)
                    .collection("games")
                    .document(v.game_id)
                    .collection("gameActions")                    
                    .order_by("gameTime", direction=firestore.Query.DESCENDING)  # Ordenar por gameTime         
                    .limit(1)        
                    .stream()
                )
    # me vale con la última jugada
    try:
        doc = next(game_actions_ref)
        action_data = doc.to_dict()
        players_on_field = action_data.get('playersOnField',[])
        
        for player in players_on_field:
            st.markdown(
    f"""
    <div style="display: flex; align-items: baseline;">
        <p style="margin: 5px; font-size: 18px; color: darkblue;">{player.get('jersey','')}-{player.get('name','')}</p>
        <p style="margin: 5px; font-size: 14px; color: gray;">({segundos_string(player.get('timePlaying',0))})</p>
    </div>
    """,
    unsafe_allow_html=True)

    except StopIteration:
        st.error("No hay jugadas")


    


# def print_actions(db):
#     game_actions_ref = (
#                     db.collection("users")
#                     .document(v.user_id)
#                     .collection("games")
#                     .document(v.game_id)
#                     .collection("gameActions")
#                     .order_by("gameTime", direction=firestore.Query.DESCENDING)  # Ordenar por gameTime
#                     .limit(20)
#                     .stream()
#                 )
#     game_actions = []
    

#     for action in game_actions_ref:
#         data = action.to_dict()
#         if "player" in data and isinstance(data["player"],dict):
#             player = data["player"]
#             data["player"] = f"{player.get('jersey','')}-{player.get('name','')}"

#         if "gameTime" in data:            
#             seconds = data["gameTime"]
#             data["gameTime"] = segundos_string(seconds)        

#         game_actions.append(data)

#     if game_actions:
#         # Convertir las acciones en una tabla        
#         column_mapping = {"gameTime" : "Tiempo", "player" : "Jugador", "actionLiteral" : "Acción", "actionResult" : "Resultado", "isFinalPlay" : "Accion Final"}
#         df = pd.DataFrame(game_actions)
#         df.rename(columns=column_mapping, inplace=True)
#         desired_columns = list(column_mapping.values())
#         df = df[desired_columns]
#         df.reset_index(drop=True, inplace=True)
#         st.write("Últimas acciones:")
#         styled_df = style_rows(df)
#         st.dataframe(styled_df, use_container_width=True)  # Muestra los datos como tabla interactiva
#     else:
#         st.warning("No se encontraron acciones para este juego.")

# Inicializa Firestore con Firebase Admin
@st.cache_resource
def init_firestore():
    cred = credentials.Certificate(v.firebase_creedentials)  # Ruta a tu archivo JSON de credenciales
    firebase_admin.initialize_app(cred)
    return firestore.client()
