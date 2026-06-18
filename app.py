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

# --- 2. LETTURA E PULIZIA DATI ---
try:
    all_data = sheet.get_all_values()
    if len(all_data) > 1:
        headers = [str(c).lower().strip() for c in all_data[0]]
        df = pd.DataFrame(all_data[1:], columns=headers)
        
        # Forza la colonna prezzo a numerico, trattando la virgola come punto
        df['prezzo'] = df['prezzo'].astype(str).str.replace(',', '.')
        df['prezzo'] = pd.to_numeric(df['prezzo'], errors='coerce').fillna(0.0)
    else:
        df = pd.DataFrame(columns=['codice', 'categoria', 'descrizione', 'quantita', 'prezzo', 'posizione'])
except Exception as e:
    st.error(f"Errore lettura: {e}")

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

# --- 4. VISUALIZZAZIONE ---
edited_df = st.data_editor(
    df_display,
    use_container_width=True,
    column_config={
        "prezzo": st.column_config.NumberColumn("Prezzo", format="€%.2f"),
    },
    key="editor"
)

# --- 5. SALVATAGGIO MANUALE (Versione Blindata) ---
if not edited_df.astype(str).equals(df_display.astype(str)):
    st.warning("⚠️ Hai modifiche in sospeso!")
    if st.button("💾 Salva Modifiche nel Cloud"):
        try:
            # 1. Aggiorna il dataframe principale
            df.update(edited_df)
            
            # 2. Convertiamo i prezzi in stringhe con il punto (formato internazionale standard)
            # Questo assicura che il dato salvato sia fisso e non venga reinterpretato
            df_to_save = df.copy()
            df_to_save['prezzo'] = df_to_save['prezzo'].apply(lambda x: f"{float(x):.2f}")
            
            # 3. Riscrittura sicura
            sheet.clear()
            sheet.append_row(df.columns.tolist())
            sheet.append_rows(df_to_save.values.tolist())
            
            st.success("✅ Salvataggio effettuato!")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"Errore: {e}")

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
