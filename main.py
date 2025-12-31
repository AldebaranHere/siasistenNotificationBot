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

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
SIASISTEN_USERNAME = os.getenv('SIASISTEN_USERNAME')
SIASISTEN_PASSWORD = os.getenv('SIASISTEN_PASSWORD')
INFO_MATKUL = int(os.getenv('INFO_MATKUL'))

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

# PythonAnywhere specific: Tell it where the browser is
chrome_options.binary_location = "/usr/bin/chromium-browser"

# Use the pre-installed driver path
service = Service(executable_path="/usr/bin/chromedriver")

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

        driver = webdriver.Chrome(service=service, options=chrome_options)

        driver.get("https://siasisten.cs.ui.ac.id/lowongan/listLowongan/")

        with open("cookies.pkl", "rb") as file:
            cookies = pickle.load(file)

        for cookie in cookies:
            if 'expiry' in cookie:
                cookie['expiry'] = int(cookie['expiry'])
            driver.add_cookie(cookie)

        time.sleep(2)
        driver.refresh()

        time.sleep(2)
        driver.find_element(By.ID, "id_username").send_keys(SIASISTEN_USERNAME)
        driver.find_element(By.ID, "id_password").send_keys(SIASISTEN_PASSWORD)
        driver.find_element(By.CSS_SELECTOR, "input[value='login']").click()

        time.sleep(2)
        driver.refresh()

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
        guild = channel.guild
        role_data = {r.name: r.id for r in guild.roles[1:]}

        time.sleep(2)
        # Find the table
        # Syntax is verbose due to the HTML content of the webpage
        table = driver.find_element(By.XPATH, "//h4[@id='next-term-header']/following-sibling::table[1]")
        rows = table.find_elements(By.TAG_NAME, "tr")

        for mk_name, mk_code in mata_kuliah.items():
            is_not_available = True
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                
                # Skip <th> header rows
                if len(cells) > 0:
                    
                    course_info = cells[1].text
                    status = cells[3].text.strip()

                    if mk_code in course_info and "Buka" in status:
                        is_not_available = False
                        await channel.send(f"<@&{role_data[mk_name]}> {mk_name} sudah dibuka! Segera daftar di https://siasisten.cs.ui.ac.id/lowongan/listLowongan/")
            
            if is_not_available:
                await channel.send(f"<@&{role_data[mk_name]}> {mk_name} belum dibuka atau sudah penuh")

        await channel.send(f"Pengecekan selesai! Tunggu 3 menit untuk pengecekan selanjutnya.")
        await channel.send(f"=================================================================")
        driver.quit()

    else:
        print(f"Channel with ID {CHANNEL_ID} not found.")
                 
client.run(DISCORD_TOKEN)