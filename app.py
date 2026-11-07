import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

# --- 1. CONFIGURAZIONE ---
def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", 
             "https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets, scope)
    client = gspread.authorize(creds)
    return client.open("Magazzino").sheet1

sheet = get_sheet()

# Funzione di supporto per convertire in sicurezza qualsiasi colonna in stringa standard (evita errori PyArrow/Pandas)
def to_str_safe(series):
    return series.astype(object).fillna("").apply(lambda x: "" if str(x).lower() in ["nan", "none", "<na>"] else str(x))

text_cols = ['codice', 'categoria', 'descrizione', 'posizione']

# --- 2. LETTURA E PULIZIA DATI ---
try:
    all_data = sheet.get_all_values()
    if len(all_data) > 1:
        headers = [str(c).lower().strip() for c in all_data[0]]
        df = pd.DataFrame(all_data[1:], columns=headers)
        
        # Pulizia preventiva delle colonne testuali
        for col in text_cols:
            if col in df.columns:
                df[col] = to_str_safe(df[col])
        
        # Forza la colonna prezzo a numerico, trattando la virgola come punto
        df['prezzo'] = to_str_safe(df['prezzo']).str.replace(',', '.')
        df['prezzo'] = pd.to_numeric(df['prezzo'], errors='coerce').fillna(0.0)
    else:
        df = pd.DataFrame(columns=['codice', 'categoria', 'descrizione', 'quantita', 'prezzo', 'posizione'])
except Exception as e:
    st.error(f"Errore lettura: {e}")

# --- 3. FILTRI DI RICERCA ---
st.subheader("📋 Inventario")

ricerca = st.text_input("🔍 Cerca per descrizione o codice...", placeholder="Scrivi qui per filtrare...")

col1, col2 = st.columns(2)

# Assicuriamoci che le colonne di testo siano sicure
for col in text_cols:
    if col in df.columns:
        df[col] = to_str_safe(df[col])

categorie = ["Tutte"] + sorted(df['categoria'].unique().tolist())
cat_scelta = col1.selectbox("Filtra per Categoria:", categorie)

posizioni = ["Tutte"] + sorted(df['posizione'].unique().tolist())
pos_scelta = col2.selectbox("Filtra per Posizione:", posizioni)

df_display = df.copy()

# Logica di filtraggio
if ricerca:
    df_display = df_display[
        df_display['descrizione'].str.contains(ricerca, case=False, na=False) | 
        df_display['codice'].str.contains(ricerca, case=False, na=False)
    ]

if cat_scelta != "Tutte":
    df_display = df_display[df_display['categoria'] == cat_scelta]
if pos_scelta != "Tutte":
    df_display = df_display[df_display['posizione'] == pos_scelta]

# --- 4. VISUALIZZAZIONE ---
editor_key = f"editor_{len(df_display)}"

df_display['quantita'] = pd.to_numeric(df_display['quantita'], errors='coerce').fillna(0).astype(int)
df_display['prezzo'] = pd.to_numeric(df_display['prezzo'], errors='coerce').fillna(0.0)

edited_df = st.data_editor(
    df_display,
    use_container_width=True,
    column_config={
        "prezzo": st.column_config.NumberColumn("Prezzo", format="€%.2f"),
    },
    key=editor_key
)

# --- 5. SALVATAGGIO MANUALE ---
if st.button("💾 Salva Modifiche"):
    try:
        # Mettiamo in sicurezza tutte le colonne testuali ricevute dall'editor
        for col in text_cols:
            if col in edited_df.columns:
                edited_df[col] = to_str_safe(edited_df[col])

        # Aggiorniamo il DataFrame principale
        df.update(edited_df)
        df_to_save = df.copy()
        
        # Pulizia finale prima della scrittura su Google Sheets
        for col in text_cols:
            if col in df_to_save.columns:
                df_to_save[col] = to_str_safe(df_to_save[col])
                
        df_to_save['quantita'] = pd.to_numeric(df_to_save['quantita'], errors='coerce').fillna(0).astype(int)
        
        # Gestione prezzo con virgola per Google Sheets Italia
        df_to_save['prezzo'] = pd.to_numeric(df_to_save['prezzo'], errors='coerce').fillna(0.0)
        df_to_save['prezzo'] = df_to_save['prezzo'].apply(lambda x: f"{float(x):.2f}".replace('.', ','))
        
        sheet.clear()
        sheet.append_row(df.columns.tolist())
        sheet.append_rows(df_to_save.values.tolist())
        
        st.success("✅ Salvataggio riuscito!")
        st.rerun()
    except Exception as e:
        st.error(f"Errore durante il salvataggio: {e}")

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
            sheet.append_row([str(new_cod), str(new_cat), str(new_desc), int(new_qta), float(new_prz), str(new_pos)])
            st.rerun()
