import streamlit as st
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
data = sheet.get_all_records(head=1)
if data:
    df = pd.DataFrame(data)
    df.columns = [str(c).lower().strip() for c in df.columns]
else:
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

# --- 4. CONFIGURAZIONE GRIGLIA ---
gb = GridOptionsBuilder.from_dataframe(df_display)
gb.configure_default_column(editable=True)
gb.configure_column("codice", editable=False)
grid_options = gb.build()

response = AgGrid(df_display, gridOptions=grid_options, update_mode=GridUpdateMode.GRID_CHANGED, key="aggrid")

# --- 5. SALVATAGGIO AUTOMATICO ---
# Controlliamo se 'data' esiste nella risposta
if 'data' in response and response['data'] is not None:
    nuovo_df = pd.DataFrame(response['data'])

    # Pulizia colonne
    nuovo_df.columns = [str(c).lower().strip() for c in nuovo_df.columns]

    # Confronto tra DataFrame per verificare se c'è stato un cambiamento reale
    # Usiamo .astype(str) per evitare errori di tipo
    if not nuovo_df.astype(str).equals(df.astype(str)):
        try:
            # Pulisce solo i dati, mantiene l'header (Riga 1)
            if sheet.row_count > 1:
                sheet.delete_rows(2, sheet.row_count)

            # Scrive i nuovi dati
            if not nuovo_df.empty:
                sheet.append_rows(nuovo_df.values.tolist())

            st.toast("✅ Dati sincronizzati con il Cloud!")
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
