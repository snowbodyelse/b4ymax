import discord
import time
import random
import aiohttp
import asyncio
import xml.etree.ElementTree as ET
from discord import FFmpegPCMAudio
import os
import edge_tts

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

COMMAND_PREFIX = "b!"

user_last_ping = {}
user_waiting_for_pain_rating = {}

random_replies = [
    "I am always here if you need me.",
    "Your personal healthcare companion is listening.",
    "Hello! How can I assist you today?",
    "I hope you are having a healthy day.",
    "My purpose is to care for you.",
    "Remember, I am always here to help you.",
    "Your health is my priority.",
    "Balalalala",
    "I am here to support you.",
    "Your well-being is important to me.",
]

# -----------------------------
# FIXED: stomach bug
# -----------------------------
health_advice = {
    "headache": "🧠 Rest, hydrate, reduce screen time.",
    "cold": "🤧 Drink fluids and rest.",
    "fever": "🌡 Rest and monitor temperature.",
    "stomach ache": "🤕 Rest and drink fluids.",
    "stomachache": "🤕 Rest and drink fluids.",
}

async def fetch_pokemon_info(name):
    url = f"https://pokeapi.co/api/v2/pokemon/{name.lower()}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return None
            data = await response.json()
            return {
                "name": data["name"].title(),
                "sprite": data["sprites"]["front_default"],
                "fact": f"Type: {', '.join([t['type']['name'] for t in data['types']])}"
            }

async def fetch_google_news():
    url = "https://news.google.com/rss"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()

def parse_news(xml_text):
    root = ET.fromstring(xml_text)
    items = root.findall(".//item")
    return [(i.find("title").text, i.find("link").text) for i in items[:5]]


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.strip()
    user_id = message.author.id
    now = time.time()

    if not content.startswith(COMMAND_PREFIX):
        return

    command_body = content[len(COMMAND_PREFIX):].strip().lower()
    print("COMMAND:", command_body)

    reply = None

    if command_body == "ping":
        reply = "Pong! (●—●)"

    elif command_body == "hello":
        reply = "Hello I am b4ymax!"

    elif command_body.startswith("pokemon"):
        parts = command_body.split(maxsplit=1)

        if len(parts) > 1:
            name = parts[1]
            data = await fetch_pokemon_info(name)

            if data:
                embed = discord.Embed(
                    title=f"🐾 {data['name']}",
                    description=data["fact"],
                    color=0x89f0ff
                )
                embed.set_thumbnail(url=data["sprite"])
            else:
                embed = discord.Embed(
                    description="⚠️ Pokémon not found",
                    color=0xff0000
                )
        else:
            embed = discord.Embed(
                description="❓ Example: b!pokemon pikachu",
                color=0x89f0ff
            )

        await message.channel.send(embed=embed)
        return


    elif command_body == "news":
        xml = await fetch_google_news()
        news = parse_news(xml)

        embed = discord.Embed(title="📰 News")
        for title, link in news:
            embed.add_field(name=title, value=link, inline=False)

        await message.channel.send(embed=embed)
        return

    elif command_body == "balalalala":
        if not message.author.voice:
            await message.channel.send("Join VC first")
            return

        vc = await message.author.voice.channel.connect()

        source = FFmpegPCMAudio("balalala.mp3")  # ❌ NO PATH

        vc.play(source)

        while vc.is_playing():
            await asyncio.sleep(1)

        await vc.disconnect()
        return

    elif command_body.startswith("say"):
        if not message.author.voice:
            await message.channel.send("Join VC first")
            return

        text = command_body[4:]

        vc = await message.author.voice.channel.connect()

        file = "tts.mp3"
        tts = edge_tts.Communicate(text, voice="en-US-ChristopherNeural")
        await tts.save(file)

        vc.play(FFmpegPCMAudio(file))

        while vc.is_playing():
            await asyncio.sleep(1)

        await vc.disconnect()
        return
        
    if reply:
        embed = discord.Embed(
            title="b4ymax (●—●)",
            description=reply,
            color=0x89f0ff
        )
        await message.channel.send(embed=embed)


token = os.getenv("DISCORD_TOKEN")

if not token:
    raise RuntimeError("DISCORD_TOKEN missing")

client.run(token)
