import os
from dotenv import load_dotenv
import discord
import bs4
from bs4 import BeautifulSoup
from selenium import webdriver
import time

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
SIASISTEN_USERNAME = os.getenv('SIASISTEN_USERNAME')
SIASISTEN_PASSWORD = os.getenv('SIASISTEN_PASSWORD')
SIASISTEN_COOKIES = os.getenv('SIASISTEN_COOKIES')

class Client(discord.Client):
    async def on_ready(self):
        print(f"Logged in as {self.user}!")

intents = discord.Intents.default()
intents.message_content = True

client = Client(intents=intents)
client.run(DISCORD_TOKEN)