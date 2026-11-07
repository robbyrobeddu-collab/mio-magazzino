import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. CONFIGURAZIONE ---
def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", 
             "https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets, scope)
    client = gspread.authorize(creds)
    return client.open("Magazzino").sheet1

sheet = get_sheet()

text_cols = ['codice', 'categoria', 'descrizione', 'posizione']

# --- 2. LETTURA E PULIZIA DATI ---
try:
    all_data = sheet.get_all_values()
    if len(all_data) > 1:
        headers = [str(c).lower().strip() for c in all_data[0]]
        # Forza tutto a object per evitare blocchi di tipo in Pandas
        df = pd.DataFrame(all_data[1:], columns=headers, dtype=object)
        
        for col in df.columns:
            df[col] = df[col].fillna("").astype(object)
            
        if 'prezzo' in df.columns:
            df['prezzo'] = df['prezzo'].astype(str).str.replace(',', '.')
            df['prezzo'] = pd.to_numeric(df['prezzo'], errors='coerce').fillna(0.0)
            
        if 'quantita' in df.columns:
            df['quantita'] = pd.to_numeric(df['quantita'], errors='coerce').fillna(0).astype(int)
    else:
        df = pd.DataFrame(columns=['codice', 'categoria', 'descrizione', 'quantita', 'prezzo', 'posizione'], dtype=object)
except Exception as e:
    st.error(f"Errore lettura: {e}")
    df = pd.DataFrame(columns=['codice', 'categoria', 'descrizione', 'quantita', 'prezzo', 'posizione'], dtype=object)

# --- 3. FILTRI DI RICERCA ---
st.subheader("📋 Inventario")

ricerca = st.text_input("🔍 Cerca per descrizione o codice...", placeholder="Scrivi qui per filtrare...")

col1, col2 = st.columns(2)

for col in text_cols:
    if col in df.columns:
        df[col] = df[col].astype(object).fillna("")

cat_list = sorted(df['categoria'].astype(str).unique().tolist()) if 'categoria' in df.columns else []
categorie = ["Tutte"] + [c for c in cat_list if c != ""]

pos_list = sorted(df['posizione'].astype(str).unique().tolist()) if 'posizione' in df.columns else []
posizioni = ["Tutte"] + [p for p in pos_list if p != ""]

cat_scelta = col1.selectbox("Filtra per Categoria:", categorie)
pos_scelta = col2.selectbox("Filtra per Posizione:", posizioni)

df_display = df.copy()

# Logica di filtraggio
if ricerca:
    mask = (
        df_display['descrizione'].astype(str).str.contains(ricerca, case=False, na=False) | 
        df_display['codice'].astype(str).str.contains(ricerca, case=False, na=False)
    )
    df_display = df_display[mask]

if cat_scelta != "Tutte":
    df_display = df_display[df_display['categoria'].astype(str) == cat_scelta]
if pos_scelta != "Tutte":
    df_display = df_display[df_display['posizione'].astype(str) == pos_scelta]

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
        # Aggiornamento sicuro cella per cella (evita i controlli di dtype di df.update)
        for idx in edited_df.index:
            for col in edited_df.columns:
                df.loc[idx, col] = edited_df.loc[idx, col]
        
        df_to_save = df.copy()
        
        # Pulizia finale prima della scrittura su Google Sheets
        for col in text_cols:
            if col in df_to_save.columns:
                df_to_save[col] = df_to_save[col].astype(object).fillna("").apply(lambda x: "" if str(x).lower() in ["nan", "none", "<na>"] else str(x))
                
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
