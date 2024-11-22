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
    st.caption(f"Actualización: {fecha}")
    rival = data["awayTeam"]
    goles_nuestros = data["ourGoals"]
    goles_rival = data["rivalGoals"]
    tiempo_actual = data["currentTime"]
    v.current_time = tiempo_actual

    st.markdown(
    f"""  
        <p style="margin: 5px; font-size: 24px; color: darkblue;">Agustinos: {goles_nuestros}</p>
        <p style="margin: 5px; font-size: 24px; color: darkred;">{rival}: {goles_rival}</p>
        <p style="margin: 5px; font-size: 18px; color: black;">Tiempo: {segundos_string(tiempo_actual)}</p>
    """,
    unsafe_allow_html=True)
    #st.subheader(f"Agustinos: {goles_nuestros} {rival}: {goles_rival}")
    
    #st.write(f"Tiempo actual: {segundos_string(tiempo_actual)}")

def segundos_string(seconds):    
    minutes = seconds // 60
    remaining = seconds % 60
    return f"{minutes:02}:{remaining:02}"

def fetch_actions(db, reverse):

    direction = firestore.Query.DESCENDING if reverse else firestore.Query.ASCENDING

    game_actions_ref = (
                    db.collection("users")
                    .document(v.user_id)
                    .collection("games")
                    .document(v.game_id)
                    .collection("gameActions")                    
                    .order_by("gameTime", direction=direction)  # Ordenar por gameTime                 
                    .stream()
                )

    return game_actions_ref

def print_actions_table(db):

    game_actions_no_subst = ["Ataque","Defensa","Cambio","Sanción","Portero","Equipo"]

    game_actions_ref = fetch_actions(db,True)
    
    filtered_actions = [
        doc.to_dict() for doc in game_actions_ref if doc.to_dict().get("actionType") != "Cambio"
    ][:v.max_rows_in_table]

    game_actions = []

    for action in filtered_actions:                
        player = action.get("player","")
        action["player"] = f"{player.get('jersey','')}-{player.get('name','')}"
                
        actionType = action.get("actionType","")
        if actionType in (["Ataque"]):
            action["A_D"] = "A"
        else:
            action["A_D"] = "D"

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
    <td style="border: 1px solid black; padding: 5px;">{action.get('A_D','')}</td>
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
            <th style="border: 1px solid black; padding: 5px;">A/D</th>
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


def print_stats(db):
    
    game_actions_ref = fetch_actions(db,False)    
    succ_att = 0
    total_att = 0
    throws = 0
    rival_saves = 0
    first_act = True
    last_act_time = 0
    secs_att = 0

    total_def = 0
    succ_def =  0
    rival_throws = 0
    suc_riv_th = 0
    saves = 0
    
    
    
    for action in game_actions_ref:
        data = action.to_dict()                        
        if data.get("isFinalPlay"):      
            if first_act:
                last_act_time = 0
                first_act = False      
            if data.get("actionType") == "Ataque":            
                secs_att += data.get("gameTime") - last_act_time
                total_att += 1
                if data.get("actionResult") in v.valores_exito:
                    succ_att += 1
                if data.get("actionLiteral")[:5].upper() == "LANZA":
                    throws += 1
                    if data.get("actionResult") == "PARADA RIVAL":
                        rival_saves += 1            
            else:
                total_def += 1
                if data.get("actionResult") in v.valores_exito:
                    succ_def += 1
                if data.get("actionType") == "Portero" and data.get("actionLiteral")[:5].upper() == "LANZA":
                    rival_throws += 1
                    if data.get("actionResult") in v.valores_fallo:
                        suc_riv_th += 1
                    if data.get("actionResult") == "PARADA":
                        saves += 1                        
            last_act_time = data.get("gameTime")

    pct_suc_att = 0.0 if total_att == 0 else succ_att / total_att * 100
    pct_suc_th = 0.0 if throws == 0 else succ_att / throws * 100
    pct_rival_saves = 0.0 if throws + rival_saves == 0 else rival_saves / throws * 100
    pct_att_time = 0.0 if v.current_time == 0 else secs_att / v.current_time * 100
    pct_suc_def = 0.0 if total_def == 0 else succ_def / total_def * 100
    pct_rival_throws = 0.0 if rival_throws == 0 else suc_riv_th / rival_throws * 100
    pct_saves = 0.0 if suc_riv_th + saves == 0 else saves / (suc_riv_th + saves) * 100
    pct_def_time = 0.0 if v.current_time == 0 else (v.current_time -  secs_att) / v.current_time * 100

    st.markdown(f"Total ataques: <b>{total_att}</b>&nbsp;&nbsp;&nbsp;acabados en éxito: <b>{succ_att}</b>&nbsp;&nbsp;&nbsp;(<i>{pct_suc_att:.2f}%</i>)", unsafe_allow_html=True)
    st.markdown(f"Lanzamientos: <b>{throws}</b>&nbsp;&nbsp;&nbsp;% éxito: <i>{pct_suc_th:.2f}%</i>&nbsp;&nbsp;&nbsp;paradas rival:&nbsp;{rival_saves}/{rival_saves + succ_att}&nbsp;<i>({pct_rival_saves:.2f}%</i>)", unsafe_allow_html=True)
    st.markdown(f"<h6>Tiempo atacando: {segundos_string(secs_att)}&nbsp;&nbsp;(<i>{pct_att_time:.2f}</i>)</h6>", unsafe_allow_html=True)
    st.divider()
    st.markdown(f"Total defensas: <b>{total_def}</b>&nbsp;&nbsp;&nbsp;acabadas en éxito: <b>{succ_def}</b>&nbsp;&nbsp;&nbsp;(<i>{pct_suc_def:.2f}%</i>)", unsafe_allow_html=True)
    st.markdown(f"Lanzamientos rival: <b>{rival_throws}</b>&nbsp;&nbsp;&nbsp;% éxito: <i>{pct_rival_throws:.2f}%</i>&nbsp;&nbsp;&nbsp;paradas:&nbsp;{saves}/{saves + suc_riv_th}&nbsp;<i>({pct_saves:.2f}%</i>)", unsafe_allow_html=True)
    st.markdown(f"<h6>Tiempo defendiendo: {segundos_string(v.current_time - secs_att)}&nbsp;&nbsp;(<i>{pct_def_time:.2f}</i>)</h6>", unsafe_allow_html=True)



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


