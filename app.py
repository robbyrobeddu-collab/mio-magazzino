import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Gestione Magazzino",
    page_icon="📦",
    layout="wide"
)

# --- SISTEMA DI AUTENTICAZIONE ---
def check_password():
    """Restituisce True se l'utente ha inserito la password corretta."""
    def password_entered():
        correct_password = st.secrets.get("app_password", "1234")
        if st.session_state["password"] == correct_password:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.subheader("🔐 Accesso Riservato")
        st.text_input("Inserisci la password per accedere al magazzino:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.subheader("🔐 Accesso Riservato")
        st.text_input("Inserisci la password per accedere al magazzino:", type="password", on_change=password_entered, key="password")
        st.error("😕 Password errata. Riprova.")
        return False
    else:
        return True

if not check_password():
    st.stop()

# --- 2. CONFIGURAZIONE GOOGLE SHEETS & CACHING ---
def get_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds", 
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets, scope)
    client = gspread.authorize(creds)
    return client.open("Magazzino").sheet1

sheet = get_sheet()

@st.cache_data(ttl=60)
def load_data_from_sheet():
    """Legge i dati da Google Sheets con cache di 60 secondi per velocizzare l'app."""
    text_cols = ['codice', 'categoria', 'descrizione', 'posizione']
    try:
        all_data = sheet.get_all_values()
        if len(all_data) > 1:
            headers = [str(c).lower().strip() for c in all_data[0]]
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
    return df

df = load_data_from_sheet()
text_cols = ['codice', 'categoria', 'descrizione', 'posizione']

# --- 3. FILTRI DI RICERCA ---
st.subheader("📋 Inventario")

# Ampliato il placeholder per indicare che cerca anche nella posizione
ricerca = st.text_input("🔍 Cerca per descrizione, codice o posizione...", placeholder="Scrivi qui per filtrare...")

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

# Logica di filtraggio estesa anche alla colonna 'posizione'
if ricerca:
    mask = (
        df_display['descrizione'].astype(str).str.contains(ricerca, case=False, na=False) | 
        df_display['codice'].astype(str).str.contains(ricerca, case=False, na=False) |
        df_display['posizione'].astype(str).str.contains(ricerca, case=False, na=False)
    )
    df_display = df_display[mask]

if cat_scelta != "Tutte":
    df_display = df_display[df_display['categoria'].astype(str) == cat_scelta]
if pos_scelta != "Tutte":
    df_display = df_display[df_display['posizione'].astype(str) == pos_scelta]

# --- 4. VISUALIZZAZIONE & EDITOR ---
editor_key = "editor_magazzino_main"

df_display['quantita'] = pd.to_numeric(df_display['quantita'], errors='coerce').fillna(0).astype(int)
df_display['prezzo'] = pd.to_numeric(df_display['prezzo'], errors='coerce').fillna(0.0)

edited_df = st.data_editor(
    df_display,
    use_container_width=True,
    column_config={
        "prezzo": st.column_config.NumberColumn("Prezzo", format="€%.2f"),
        "descrizione": st.column_config.TextColumn("Descrizione", width="large"),
    },
    key=editor_key
)

# --- 5. SALVATAGGIO MANUALE (SICURO SULLI INDICI) ---
if st.button("💾 Salva Modifiche"):
    try:
        # Aggiorniamo le righe modificate direttamente sul DataFrame originale mantenendo la corrispondenza degli indici
        df.update(edited_df)
        
        df_to_save = df.copy()
        
        for col in text_cols:
            if col in df_to_save.columns:
                df_to_save[col] = df_to_save[col].astype(object).fillna("").apply(lambda x: "" if str(x).lower() in ["nan", "none", "<na>"] else str(x))
                
        df_to_save['quantita'] = pd.to_numeric(df_to_save['quantita'], errors='coerce').fillna(0).astype(int)
        df_to_save['prezzo'] = pd.to_numeric(df_to_save['prezzo'], errors='coerce').fillna(0.0)
        df_to_save['prezzo'] = df_to_save['prezzo'].apply(lambda x: f"{float(x):.2f}".replace('.', ','))
        
        sheet.clear()
        sheet.append_row(df.columns.tolist())
        sheet.append_rows(df_to_save.values.tolist())
        
        # Invalida la cache per forzare la ricarica dei dati aggiornati
        st.cache_data.clear()
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
        new_qta = st.number_input("Quantità", value=0, step=1)
        new_prz = st.number_input("Prezzo (€)", value=0.0, format="%.2f")
        new_pos = st.text_input("Posizione")
        
        if st.form_submit_button("Salva Prodotto"):
            prz_str = f"{float(new_prz):.2f}".replace('.', ',')
            sheet.append_row([str(new_cod), str(new_cat), str(new_desc), int(new_qta), prz_str, str(new_pos)])
            st.cache_data.clear()
            st.success("Prodotto aggiunto con successo!")
            st.rerun()
