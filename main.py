import os
from dotenv import load_dotenv
import discord
from selenium import webdriver
import time
from discord.ext import commands
from discord.ext import tasks
import pickle
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import platform

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
SIASISTEN_USERNAME = os.getenv('SIASISTEN_USERNAME')
SIASISTEN_PASSWORD = os.getenv('SIASISTEN_PASSWORD')
INFO_MATKUL = int(os.getenv('INFO_MATKUL'))

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

class Client(commands.Bot):
    async def on_ready(self):
        print(f"Logged in as {self.user}!")

        try:
            guild = discord.Object(id=1455503949611401463)
            synced = await self.tree.sync(guild=guild)
            print(f"Synced {len(synced)} commands to the guild {guild.id}.")

        except Exception as e:
            print(f"Error syncing commands: {e}")
        
        background_loop.start()

intents = discord.Intents.default()
intents.message_content = True
client = Client(command_prefix="!", intents = intents)

CHANNEL_ID=INFO_MATKUL
@tasks.loop(minutes=3.0)
async def background_loop():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    if channel:

        await channel.send(f"=================================================================")
        await channel.send(f"Pengecekan dimulai! Simak informasi berikut:")

        if platform.system() == "Linux":
            # Use case: PythonAnywhere or a Linux server
            chrome_options.binary_location = "/usr/bin/chromium-browser"
            service = Service(executable_path="/usr/bin/chromedriver")
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            # Automatic Windows/Mac detection
            driver = webdriver.Chrome(options=chrome_options)

        try:
            driver.get("https://siasisten.cs.ui.ac.id/lowongan/listLowongan/")

            with open("cookies.pkl", "rb") as file:
                cookies = pickle.load(file)

            for cookie in cookies:
                if 'expiry' in cookie:
                    cookie['expiry'] = int(cookie['expiry'])
                driver.add_cookie(cookie)

            driver.refresh()

            wait = WebDriverWait(driver, 10)
            waitUsernameExists = wait.until(EC.presence_of_element_located((By.ID, "id_username")))
            waitUsernameExists.send_keys(SIASISTEN_USERNAME)
            waitPasswordExists = wait.until(EC.presence_of_element_located((By.ID, "id_password")))
            waitPasswordExists.send_keys(SIASISTEN_PASSWORD)
            driver.find_element(By.CSS_SELECTOR, "input[value='login']").click()

            mata_kuliah = {
                    "SDA": "CSGE602040",
                    "MD2": "CSGE601011",
                    "Kalkulus2": "CSCM601213",
                    "POK": "CSCM601252",
                    "DDP2": "CSGE601021",

                    "Kalkulus1": "CSGE601012",
                    "DDP1": "CSGE601020",
                    "PSD": "CSCM601150",
                    "MD1": "CSGE601010",
                    "ALIN": "CSGE602012"
                }

            # Find the table
            waitTableExists = wait.until(EC.presence_of_element_located((By.XPATH, "//h4[@id='term-header']/following-sibling::table[1]")))
            table = driver.find_element(By.XPATH, "//h4[@id='term-header']/following-sibling::table[1]")
            rows = table.find_elements(By.TAG_NAME, "tr")

            guild = channel.guild
            role_data = {r.name: r.id for r in guild.roles[1:]}

            for mk_name, mk_code in mata_kuliah.items():
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    
                    # Skip <th> header rows
                    if len(cells) > 0:
                        
                        course_info = cells[1].text
                        status = cells[5].text.strip()

                        try:
                            # Find the 'a' tag specifically in the last cell of THIS row
                            link_element = cells[10].find_element(By.TAG_NAME, "a")
                            daftar_link = link_element.get_attribute("href")
                        except:
                            # Fallback if the link isn't found for some reason
                            daftar_link = "https://siasisten.cs.ui.ac.id/lowongan/listLowongan/"

                        if (mk_code in course_info) and ("Internasional" in course_info) and ("Buka" in status):
                            await channel.send(f"<@&{role_data[mk_name]}> {mk_name} Internasional sudah dibuka! Segera daftar di {daftar_link}")
                        elif (mk_code in course_info) and ("Buka" in status):
                            await channel.send(f"<@&{role_data[mk_name]}> {mk_name} Reguler sudah dibuka! Segera daftar di {daftar_link}")
                
            await channel.send(f"Pengecekan selesai! Tunggu 3 menit untuk pengecekan selanjutnya.")
            await channel.send(f"=================================================================")
        
        finally:
            driver.quit()

    else:
        print(f"Channel with ID {CHANNEL_ID} not found.")
                 
client.run(DISCORD_TOKEN)