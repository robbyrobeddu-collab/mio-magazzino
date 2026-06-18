import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials


def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", 
             "https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive"]
    
    # st.secrets carica automaticamente il file TOML che hai salvato in Settings
    # Assicurati di non passare il nome di un file qui!
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets, scope)
    client = gspread.authorize(creds)
    return client.open("Magazzino").sheet1

# Chiama la funzione
sheet = get_sheet()

# --- 2. LETTURA DATI ---
try:
    data = sheet.get_all_records(head=1)
    if data and isinstance(data, list) and len(data) > 0:
        df = pd.DataFrame(data)
        # Normalizzazione nomi colonne
        df.columns = [str(c).lower().strip() for c in df.columns]
    else:
        # Crea un DataFrame vuoto con le colonne previste se il foglio è vuoto
        df = pd.DataFrame(columns=['codice', 'categoria', 'descrizione', 'quantita', 'prezzo', 'posizione'])
except Exception as e:
    st.error(f"Errore nella lettura del foglio: {e}")
    df = pd.DataFrame(columns=['codice', 'categoria', 'descrizione', 'quantita', 'prezzo', 'posizione'])

# --- 3. FILTRI DI RICERCA ---
st.subheader("📋 Inventario")
col1, col2 = st.columns(2)

categorie = ["Tutte"] + sorted(df['categoria'].unique().tolist())
cat_scelta = col1.selectbox("Categoria:", categorie)

posizioni = ["Tutte"] + sorted(df['posizione'].unique().tolist())
pos_scelta = col2.selectbox("Posizione:", posizioni)

df_display = df.copy()
if cat_scelta != "Tutte":
    df_display = df_display[df_display['categoria'] == cat_scelta]
if pos_scelta != "Tutte":
    df_display = df_display[df_display['posizione'] == pos_scelta]

# --- 4. VISUALIZZAZIONE STABILE (Sostituisci il vecchio blocco 4) ---
# Usiamo st.data_editor di Streamlit nativo, è molto più stabile di AgGrid
# e gestisce meglio il layout mobile.
edited_df = st.data_editor(
    df_display,
    use_container_width=True,
    hide_index=True,
    column_config={
        "codice": st.column_config.TextColumn("Codice", disabled=True), # Bloccato
        "categoria": st.column_config.TextColumn("Categoria"),
        "descrizione": st.column_config.TextColumn("Descrizione"),
        "quantita": st.column_config.NumberColumn("Quantità"),
        "prezzo": st.column_config.NumberColumn("Prezzo", format="€%.2f"),
    },
    key="editor"
)

# --- 5. SALVATAGGIO MANUALE ---
# Invece di salvare ad ogni minima modifica, mostriamo il pulsante 
# solo se ci sono cambiamenti rilevati rispetto al dato iniziale.

if not edited_df.astype(str).equals(df_display.astype(str)):
    st.warning("⚠️ Hai modifiche in sospeso!")
    if st.button("💾 Salva Modifiche nel Cloud"):
        try:
            # Pulisce e riscrive il foglio
            sheet.clear()
            sheet.append_row(df.columns.tolist())
            sheet.append_rows(edited_df.values.tolist())
            
            st.success("✅ Salvataggio effettuato con successo!")
            # Un piccolo ritardo per far vedere il messaggio, poi ricarica
            import time
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"Errore di sincronizzazione: {e}")
            
# --- 6. AGGIUNGI PRODOTTO ---
with st.expander("➕ Aggiungi Nuovo Prodotto"):
    with st.form("add_form"):
        new_cod = st.text_input("Codice")
        new_cat = st.text_input("Categoria")
        new_desc = st.text_input("Descrizione")
        new_qta = st.number_input("Quantità", value=0)
        new_prz = st.number_input("Prezzo", value=0.0)
        new_pos = st.text_input("Posizione")
        if st.form_submit_button("Salva"):
            sheet.append_row([new_cod, new_cat, new_desc, new_qta, new_prz, new_pos])
            st.rerun()
