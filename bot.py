# /root/whatssap-bot/bot.py
import uuid
import shutil
import sys
import sqlite3
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# Configurações principais
DB_PATH = "/root/lais-backend/db.sqlite3"
CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver"
WHATSAPP_SESSION_PATH = "/root/perfil-lais"
MENSAGEM = "Olá, aqui é o sistema da Lais confirmando seu agendamento. ❤️"

# Cria cópia temporária do perfil para evitar conflito
perfil_temp = f"/tmp/perfil-lais-{uuid.uuid4()}"
def ignorar_arquivos(src, names):
    return [n for n in names if n.startswith("Singleton")]

shutil.copytree(WHATSAPP_SESSION_PATH, perfil_temp, ignore=ignorar_arquivos)

options = Options()
options.add_argument(f"--user-data-dir={perfil_temp}")
# options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)

# Conectar ao banco
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Filtra por data, se fornecida
print(f'Argumentos fornecidos: {sys.argv}')
if len(sys.argv) > 1:
    try:
        filtro_data = datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
        print(f"📆 Filtrando agendamentos por data: {filtro_data}")
        cursor.execute("""
            SELECT id, client_name, client_phone
            FROM appointments
            WHERE send_confirmation_email = 0 AND appointment_date = ?
        """, (filtro_data,))
    except ValueError:
        print("❌ Data inválida. Use o formato YYYY-MM-DD.")
        driver.quit()
        conn.close()
        sys.exit(1)
else:
    print("📆 Sem filtro de data. Buscando todos não enviados.")
    cursor.execute("""
        SELECT id, client_name, client_phone
        FROM appointments
        WHERE send_confirmation_email = 0
    """)

agendamentos = cursor.fetchall()

def enviar_mensagem(numero, mensagem):
    try:
        numero_limpo = ''.join(filter(str.isdigit, numero))
        url = f"https://web.whatsapp.com/send?phone=55{numero_limpo}&text={mensagem}"
        driver.get(url)
        time.sleep(10)
        driver.save_screenshot(f"/root/print_debug_{numero_limpo}.png")

        # Simula pressionar ENTER mesmo sem localizar caixa
        ActionChains(driver).send_keys(Keys.ENTER).perform()
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
shutil.rmtree(perfil_temp, ignore_errors=True)
