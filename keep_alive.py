import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# Inizializza il driver di Chrome
driver = webdriver.Chrome(options=options)

try:
    # Sostituisci con l'URL ufficiale della tua app Streamlit
    url = "https://tuo-nome-app.streamlit.app"
    driver.get(url)
    
    # Attendi qualche secondo per assicurarti che la pagina venga renderizzata completamente
    time.sleep(15)
    print(f"App visitata con successo: {url}")
finally:
    driver.quit()
