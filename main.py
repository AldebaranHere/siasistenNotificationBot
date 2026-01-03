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
import logging

load_dotenv()

# Use file logging instead of console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()  # Also log to the console
    ]
)
logger = logging.getLogger(__name__)

# Validate required environment variables
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
SIASISTEN_USERNAME = os.getenv('SIASISTEN_USERNAME')
SIASISTEN_PASSWORD = os.getenv('SIASISTEN_PASSWORD')
SIASISTEN_URL = os.getenv('SIASISTEN_URL')
INFO_MATKUL = os.getenv('INFO_MATKUL')
GUILD_ID = os.getenv('GUILD_ID')

# Validate critical environment variables
if not all([DISCORD_TOKEN, SIASISTEN_USERNAME, SIASISTEN_PASSWORD, SIASISTEN_URL, INFO_MATKUL, GUILD_ID]):
    logger.error("Missing required environment variables. Check your .env file.")
    raise ValueError("Missing required environment variables")

try:
    INFO_MATKUL = int(INFO_MATKUL)
    GUILD_ID = int(GUILD_ID)
except ValueError as e:
    logger.error(f"Invalid format for numeric environment variables: {e}")
    raise

chrome_options = Options()
chrome_options.add_argument("--headless=new")  
chrome_options.add_argument("--no-sandbox")    
chrome_options.add_argument("--disable-dev-shm-usage") 
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
# RAM-saving flags
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--window-size=1024,768") # smaller screen means less RAM
chrome_options.add_argument("--proxy-server='direct://'")
chrome_options.add_argument("--proxy-bypass-list=*")
chrome_options.add_argument("--blink-settings=imagesEnabled=false") # DO NOT load images

class Client(commands.Bot):
    async def on_ready(self):
        logger.info(f"Logged in as {self.user}")

        try:
            guild = discord.Object(id=GUILD_ID)
            synced = await self.tree.sync(guild=guild)
            logger.info(f"Synced {len(synced)} commands to the guild {guild.id}")

        except Exception as e:
            logger.error(f"Error syncing commands: {e}", exc_info=True)
        
        if not background_loop.is_running():
            background_loop.start()

intents = discord.Intents.default()
intents.message_content = True
client = Client(command_prefix="!", intents = intents)

CHANNEL_ID=INFO_MATKUL
@tasks.loop(minutes=10.0)
async def background_loop():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    if channel:

        await channel.send(f"=====================================================================================================================")
        await channel.send(f"Pengecekan dimulai! Simak informasi berikut:")

        try:
            if platform.system() == "Linux":
                service = Service("/usr/bin/chromedriver")
                driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                # Use Windows/MacOS
                driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            logger.error(f"Error initializing webdriver: {e}", exc_info=True)
            await channel.send("Terjadi kesalahan saat pengecekan. Mohon tunggu pengecekan selanjutnya.")
            return

        try:
            driver.get(SIASISTEN_URL)

            driver.refresh()

            wait = WebDriverWait(driver, 10)
            
            try:
                username_field = wait.until(EC.presence_of_element_located((By.ID, "id_username")))
                username_field.send_keys(SIASISTEN_USERNAME)
            except Exception as e:
                logger.error("Failed to locate username field. The website may have changed.", exc_info=True)
                await channel.send("Terjadi kesalahan saat pengecekan. Mohon tunggu pengecekan selanjutnya.")
                return
                
            try:
                password_field = wait.until(EC.presence_of_element_located((By.ID, "id_password")))
                password_field.send_keys(SIASISTEN_PASSWORD)
            except Exception as e:
                logger.error("Failed to locate password field. The website may have changed.", exc_info=True)
                await channel.send("Terjadi kesalahan saat pengecekan. Mohon tunggu pengecekan selanjutnya.")
                return
            
            try:
                driver.find_element(By.CSS_SELECTOR, "input[value='login']").click()
            except Exception as e:
                logger.error("Failed to click login button. The website may have changed.", exc_info=True)
                await channel.send("Terjadi kesalahan saat pengecekan. Mohon tunggu pengecekan selanjutnya.")
                return

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
                    mk_name = mk_code_to_name.get(mk_code, None)
                    status = cells[5].text.strip()

                    # Skip if course not in our tracking list
                    if mk_code not in course_codes or mk_name is None:
                        continue

                    try:
                        # Find specific sign up link
                        link_element = cells[10].find_element(By.TAG_NAME, "a")
                        daftar_link = link_element.get_attribute("href")
                    except Exception:
                        # Default link: the siasisten URL
                        daftar_link = SIASISTEN_URL

                    # Verify role exists before sending notification
                    if mk_name not in role_data:
                        logger.warning(f"Role '{mk_name}' not found in guild. Skipping notification.")
                        continue

                    if ("Internasional" in course_info) and ("Buka" in status):
                        await channel.send(f"<@&{role_data[mk_name]}> {mk_name} Internasional sudah dibuka! Segera daftar di {daftar_link}")
                    elif ("Buka" in status):
                        await channel.send(f"<@&{role_data[mk_name]}> {mk_name} Reguler sudah dibuka! Segera daftar di {daftar_link}")
                
            await channel.send(f"Pengecekan selesai! Tunggu 10 menit untuk pengecekan selanjutnya.")
            await channel.send(f"=====================================================================================================================")
        
        except Exception as e:
            logger.error(f"Error during course checking: {e}", exc_info=True)
            await channel.send("Terjadi kesalahan saat pengecekan. Mohon tunggu pengecekan selanjutnya.")

        finally:
            try:
                driver.quit()
            except Exception as e:
                logger.error(f"Error closing webdriver: {e}", exc_info=True)

    else:
        logger.warning(f"Channel with ID {CHANNEL_ID} not found.")
                 
try:
    client.run(DISCORD_TOKEN)
except Exception as e:
    logger.critical(f"Failed to start bot: {e}", exc_info=True)
    raise