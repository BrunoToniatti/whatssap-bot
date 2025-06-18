from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import os

CAMINHO_SESSAO = os.path.join(os.getcwd(), "perfil-lais")

options = Options()
options.add_argument(f"--user-data-dir={CAMINHO_SESSAO}")
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

service = Service("/usr/local/bin/chromedriver")
driver = webdriver.Chrome(service=service, options=options)

driver.get("https://web.whatsapp.com")
time.sleep(15)

print("Página:", driver.title)
driver.quit()
