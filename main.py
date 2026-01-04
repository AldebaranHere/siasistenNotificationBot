import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord.ext import tasks
import platform
import requests
from bs4 import BeautifulSoup
import time
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
SIASISTEN_LOGIN_URL=os.getenv('SIASISTEN_LOGIN_URL')
SIASISTEN_ROOT_URL=os.getenv('SIASISTEN_ROOT_URL')
INFO_MATKUL = os.getenv('INFO_MATKUL')
GUILD_ID = os.getenv('GUILD_ID')

# Validate critical environment variables
if not all([DISCORD_TOKEN, SIASISTEN_USERNAME, SIASISTEN_PASSWORD, SIASISTEN_URL, INFO_MATKUL, GUILD_ID, SIASISTEN_LOGIN_URL]):
    logger.error("Missing required environment variables. Check your .env file.")
    raise ValueError("Missing required environment variables")

try:
    INFO_MATKUL = int(INFO_MATKUL)
    GUILD_ID = int(GUILD_ID)
except ValueError as e:
    logger.error(f"Invalid format for numeric environment variables: {e}")
    raise

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
@tasks.loop(minutes=15.0)
async def background_loop():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    if channel:

        await channel.send(f"=====================================================================================================================")
        await channel.send(f"Pengecekan dimulai! Simak informasi berikut:")

        try:
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
        except Exception as e:
            logger.error(f"Error initializing session: {e}", exc_info=True)
            await channel.send("Terjadi kesalahan saat pengecekan. Mohon tunggu pengecekan selanjutnya.")
            return

        try:
            
            login_url = SIASISTEN_LOGIN_URL
            destination_url = SIASISTEN_URL

            response = session.get(login_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']

            payload = {
                'username': SIASISTEN_USERNAME,
                'password': SIASISTEN_PASSWORD,
                'csrfmiddlewaretoken': csrf_token,
                'next': destination_url
            }

            login_post = session.post(login_url, data=payload, headers={'Referer': login_url})

            data_page = session.get(destination_url)
            final_soup = BeautifulSoup(data_page.text, 'html.parser')

            table_rows = final_soup.find_all('tr')
            rows_courses_only = table_rows[1:] # Skip header row
        
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
                    "MANBIS": "CSIM601190",
                    "KOMBISTEK": "CSIM601191",

                    "BASDAT": "CSGE602070",
                    "SISTER": "CSGE602024",
                    "PKPL": "CSGE602023",
                    "TBA": "CSCM602241",
                    "ADPRO": "CSCM602223",

                    "KASDAD": "CSGE603130",
                    "JARKOM": "CSCM603154",
                    "ANUM": "CSCM603217",
                    "DAA": "CSCM603142",
                }

            guild = channel.guild
            role_data = {r.name: r.id for r in guild.roles[1:]}
            course_codes = set(mata_kuliah.values())
            mk_code_to_name = {v: k for k, v in mata_kuliah.items()}

            for row in rows_courses_only:
                cells = row.find_all('td')
                
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
                        link_element = cells[10].find_all('a')[0]['href']
                        daftar_link = SIASISTEN_ROOT_URL+link_element[1:]
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
                
            await channel.send(f"Pengecekan selesai! Tunggu 15 menit untuk pengecekan selanjutnya.")
            await channel.send(f"=====================================================================================================================")
        
        except Exception as e:
            logger.error(f"Error during course checking: {e}", exc_info=True)
            await channel.send("Terjadi kesalahan saat pengecekan. Mohon tunggu pengecekan selanjutnya.")

        finally:
            try:
                session.close()
            except Exception as e:
                logger.error(f"Error closing session: {e}", exc_info=True)

    else:
        logger.warning(f"Channel with ID {CHANNEL_ID} not found.")
                 
try:
    client.run(DISCORD_TOKEN)
except Exception as e:
    logger.critical(f"Failed to start bot: {e}", exc_info=True)
    raise