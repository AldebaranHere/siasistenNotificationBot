import os
from dotenv import load_dotenv
import discord
from selenium import webdriver
from discord.ext import commands
from discord.ext import tasks
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import platform
from webdriver_manager.chrome import ChromeDriverManager

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
SIASISTEN_USERNAME = os.getenv('SIASISTEN_USERNAME')
SIASISTEN_PASSWORD = os.getenv('SIASISTEN_PASSWORD')
SIASISTEN_URL = os.getenv('SIASISTEN_URL')
INFO_MATKUL = int(os.getenv('INFO_MATKUL'))
GUILD_ID = int(os.getenv('GUILD_ID'))

chrome_options = Options()
chrome_options.add_argument("--headless=new")  
chrome_options.add_argument("--no-sandbox")    
chrome_options.add_argument("--disable-dev-shm-usage") 
chrome_options.add_argument("--disable-gpu")   
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

class Client(commands.Bot):
    async def on_ready(self):
        print(f"Logged in as {self.user}!")

        try:
            guild = discord.Object(id=GUILD_ID)
            synced = await self.tree.sync(guild=guild)
            print(f"Synced {len(synced)} commands to the guild {guild.id}.")

        except Exception as e:
            print(f"Error syncing commands: {e}")
        
        background_loop.start()

intents = discord.Intents.default()
intents.message_content = True
client = Client(command_prefix="!", intents = intents)

CHANNEL_ID=INFO_MATKUL
@tasks.loop(minutes=5.0)
async def background_loop():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    if channel:

        await channel.send(f"=====================================================================================================================")
        await channel.send(f"Pengecekan dimulai! Simak informasi berikut:")

        try:
            if platform.system() == "Linux":
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                # Use Windows/MacOS
                driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            print(f"Error occurred while assigning the webdriver: {e}")
            return

        try:
            driver.get(SIASISTEN_URL)

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
                    "ALIN": "CSGE602012",

                    "BASDAT": "CSGE602070",
                    "SISTER": "CSGE602024",
                    "PKPL": "CSGE602023",
                    "TBA": "CSCM602241",
                    "ADPRO": "CSCM602223",

                    "KASDAD": "CSGE603130",
                    "JARKOM": "CSCM603154",
                    "ANUM": "CSCM603117",
                    "DAA": "CSCM603142",
                }

            # Find the table
            waitTableExists = wait.until(EC.presence_of_element_located((By.XPATH, "//h4[@id='term-header']/following-sibling::table[1]")))
            table = driver.find_element(By.XPATH, "//h4[@id='term-header']/following-sibling::table[1]")
            rows = table.find_elements(By.TAG_NAME, "tr")

            guild = channel.guild
            role_data = {r.name: r.id for r in guild.roles[1:]}
            course_codes = set(mata_kuliah.values())
            mk_code_to_name = {v: k for k, v in mata_kuliah.items()}

            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                
                # Skip <th> header rows
                if len(cells) > 0:
                    
                    course_info = cells[1].text
                    mk_code = course_info.split()[0]
                    mk_name = mk_code_to_name.get(mk_code, "Unknown course")
                    status = cells[5].text.strip()

                    try:
                        # Find specific sign up link
                        link_element = cells[10].find_element(By.TAG_NAME, "a")
                        daftar_link = link_element.get_attribute("href")
                    except:
                        # Default link: the siasisten URL
                        daftar_link = SIASISTEN_URL

                    if (mk_code not in course_codes):
                        continue
                    else:
                        if ("Internasional" in course_info) and ("Buka" in status):
                            await channel.send(f"<@&{role_data[mk_name]}> {mk_name} Internasional sudah dibuka! Segera daftar di {daftar_link}")
                        elif ("Buka" in status):
                            await channel.send(f"<@&{role_data[mk_name]}> {mk_name} Reguler sudah dibuka! Segera daftar di {daftar_link}")
                
            await channel.send(f"Pengecekan selesai! Tunggu 5 menit untuk pengecekan selanjutnya.")
            await channel.send(f"=====================================================================================================================")
        
        except Exception as e:
            print(f"An error occurred: {e}")

        finally:
            driver.quit()

    else:
        print(f"Channel with ID {CHANNEL_ID} not found.")
                 
client.run(DISCORD_TOKEN)