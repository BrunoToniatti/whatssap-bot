import uuid
import shutil
import sys
import sqlite3
import time
import os
import fcntl
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

# Configurações principais
DB_PATH = "/root/lais-backend/db.sqlite3"
CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver"
WHATSAPP_SESSION_PATH = "/root/perfil-lais"
MENSAGEM = "Olá, aqui é o sistema da Lais confirmando seu agendamento. ❤️"

# Trava de execução (para evitar execuções simultâneas)
LOCK_PATH = "/tmp/lais_bot.lock"
lock_file = open(LOCK_PATH, "w")
try:
    fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError:
    print("⚠️ Outro processo do bot já está em execução.")
    sys.exit(1)

# Cria cópia temporária do perfil para evitar conflito
perfil_temp = f"/tmp/perfil-lais-{uuid.uuid4()}"
def ignorar_arquivos(src, names):
    return [n for n in names if n.startswith("Singleton")]

shutil.copytree(WHATSAPP_SESSION_PATH, perfil_temp, ignore=ignorar_arquivos)

# Configura opções do navegador
options = Options()
options.add_argument(f"--user-data-dir={perfil_temp}")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
# options.add_argument("--headless=new")  # opcional, se quiser headless de fato

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
        time.sleep(15)
        driver.save_screenshot(f"/root/print_antes_{numero_limpo}.png")

        print("🖱️ Tentando clicar no botão de enviar...")

        botao = driver.find_element("xpath", '//*[@id="main"]/footer/div[1]/div/span/div/div[2]/div/div[4]/button')
        driver.execute_script("arguments[0].click();", botao)

        time.sleep(5)
        driver.save_screenshot(f"/root/print_depois_{numero_limpo}.png")

        print("✅ Mensagem enviada via clique.")
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
        print("✅ Mensagem marcada como enviada.")
    else:
        print("⚠️ Falha no envio. Não foi marcada como enviada.")

# Finaliza
driver.quit()
conn.close()
shutil.rmtree(perfil_temp, ignore_errors=True)
lock_file.close()
