import requests

# Sostituisci con il link ufficiale della tua app Streamlit
url = "https://ricambilvdm.streamlit.app/"

try:
    # Esegue una richiesta GET con un timeout di 30 secondi
    response = requests.get(url, timeout=30)
    
    # Verifica che la risposta sia positiva (Codice 200)
    if response.status_code == 200:
        print(f"Successo! App visitata correttamente. Status: {response.status_code}")
    else:
        print(f"Attenzione: L'app ha risposto con codice {response.status_code}")
        
except Exception as e:
    print(f"Errore durante la connessione all'app: {e}")
