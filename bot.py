import sqlite3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.common.keys import Keys

# Configurações principais
DB_PATH = "/root/lais-backend/db.sqlite3"
CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver"
WHATSAPP_SESSION_PATH = "/root/perfil-lais"
MENSAGEM = "Olá, aqui é o sistema da Lais confirmando seu agendamento. ❤️"

# Configuração do navegador headless com sessão da Lais
options = Options()
options.add_argument(f"--user-data-dir={WHATSAPP_SESSION_PATH}")
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)

# Conectar ao banco
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Buscar agendamentos que ainda não foram enviados
cursor.execute("SELECT id, client_name, client_phone FROM appointments WHERE send_confirmation_email = 0")
agendamentos = cursor.fetchall()

def enviar_mensagem(numero, mensagem):
    try:
        numero_limpo = ''.join(filter(str.isdigit, numero))
        url = f"https://web.whatsapp.com/send?phone=55{numero_limpo}&text={mensagem}"
        driver.get(url)
        time.sleep(10)

        # Aguardar a caixa de mensagem e simular ENTER
        caixa = driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')
        caixa.send_keys(Keys.ENTER)
        time.sleep(5)
        return True
    except Exception as e:
        print(f"❌ Erro ao enviar para {numero}: {e}")
        return False

# Loop de envio
for agendamento in agendamentos:
    ag_id, nome, telefone = agendamento
    print(f"📲 Enviando para {nome} ({telefone})...")

    sucesso = enviar_mensagem(telefone, MENSAGEM)

    if sucesso:
        cursor.execute("UPDATE appointments SET send_confirmation_email = 1 WHERE id = ?", (ag_id,))
        conn.commit()
        print("✅ Mensagem enviada com sucesso!")
    else:
        print("⚠️ Falha no envio.")

# Finaliza
driver.quit()
conn.close()
