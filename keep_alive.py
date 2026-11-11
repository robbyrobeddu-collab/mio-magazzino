import sys
import requests

# Sostituisci con l'URL ufficiale della tua app Streamlit
STREAMLIT_APP_URL = "https://ricambilvdm.streamlit.app/"

def ping_app():
    print(f"Tentativo di connessione a: {STREAMLIT_APP_URL}")
    
    try:
        # Esegue la richiesta GET impostando un timeout di 30 secondi
        # Usiamo anche un User-Agent standard per simulare un browser reale
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(STREAMLIT_APP_URL, headers=headers, timeout=30)
        
        # Controlla se la risposta è positiva (Codice HTTP 200)
        if response.status_code == 200:
            print(f"Successo! L'app ha risposto correttamente. Status Code: {response.status_code}")
            sys.exit(0)  # Uscita pulita con successo
        else:
            print(f"Attenzione: L'app ha risposto con un codice anomalo: {response.status_code}")
            sys.exit(1)  # Uscita con errore per segnalarlo nei log
            
    except requests.exceptions.Timeout:
        print("Errore: Timeout della richiesta. L'app potrebbe essere in fase di risveglio.")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"Errore di connessione durante il ping dell'app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ping_app()
