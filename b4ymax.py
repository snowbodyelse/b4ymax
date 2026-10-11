import asyncio
import os
import random
import time
import traceback
import xml.etree.ElementTree as ET

import aiohttp
import discord
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

user_last_ping = {}

COMMAND_PREFIX = "b!"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_FILE = os.path.join(BASE_DIR, "balalala.mp3")
FFMPEG_PATH = os.path.join(BASE_DIR, "ffmpeg.exe")

random_replies = [
    "I am always here if you need me.",
    "Your personal healthcare companion is listening.",
    "Hello! How can I assist you today?",
    "I hope you are having a healthy day.",
    "My purpose is to care for you.",
    "Remember, I am always here to help you.",
    "Your health is my priority.",
    "Balalalala",
]

async def fetch_definition(word):
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return None
            data = await response.json()
            try:
                meaning = data[0]['meanings'][0]
                part_of_speech = meaning['partOfSpeech']
                definition = meaning['definitions'][0]['definition']
                return f"({part_of_speech}) {definition}"
            except (KeyError, IndexError):
                return None

async def fetch_google_news():
    url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return None
            text = await response.text()
            return text

def parse_news(xml_text, max_items=3):
    root = ET.fromstring(xml_text)
    items = root.findall(".//item")
    news_list = []
    for item in items[:max_items]:
        title = item.find("title").text
        link = item.find("link").text
        news_list.append((title, link))
    return news_list

async def play_balalala(message):
    """Join the author's voice channel, play the mp3, then leave. Returns the reply text."""
    if not message.guild:
        return "⚠️ I can only sing in a server."
    voice_state = message.author.voice
    if not voice_state or not voice_state.channel:
        return "⚠️ Join a voice channel first, then ask me again."
    if message.guild.voice_client:
        return "⚠️ I am already singing somewhere!"
    if not os.path.isfile(AUDIO_FILE):
        return "⚠️ I lost my song file."

    try:
        vc = await voice_state.channel.connect()
    except discord.DiscordException as e:
        return f"⚠️ I could not join the call: {e}"

    done = asyncio.Event()
    loop = asyncio.get_running_loop()
    source = discord.FFmpegPCMAudio(AUDIO_FILE, executable=FFMPEG_PATH)
    vc.play(source, after=lambda err: loop.call_soon_threadsafe(done.set))
    try:
        await done.wait()
    finally:
        await vc.disconnect()
    return "Balalalala 🎶"


@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')

    activity = discord.Activity(type=discord.ActivityType.listening, name="your woes 💙")
    await client.change_presence(status=discord.Status.idle, activity=activity)

@client.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.strip()
    user_id = message.author.id
    now = time.time()

    # Determine if the bot should respond (prefix or mention)
    should_respond = False
    command_body = ""

    if content.startswith(COMMAND_PREFIX):
        command_body = content[len(COMMAND_PREFIX):].strip().lower()
        should_respond = True
    elif client.user in message.mentions:
        mention_text = f"<@{client.user.id}>"
        command_body = content.replace(mention_text, "").strip().lower()
        should_respond = True

    if not should_respond:
        return

    # Cooldown
    last_ping = user_last_ping.get(user_id, 0)
    if now - last_ping < 2:
        return

    reply = None

    if command_body == "news":
        embed = discord.Embed(
            title="📰 Fetching the latest news...",
            color=0x00bfff
        )
        await message.channel.send(embed=embed)
        xml_text = await fetch_google_news()
        if not xml_text:
            await message.channel.send("⚠️ I could not fetch the news.")
        else:
            news_list = parse_news(xml_text)
            news_embed = discord.Embed(
                title="🗞️ Latest News from Google",
                color=0x00bfff
            )
            for title, link in news_list:
                news_embed.add_field(name=title, value=f"[Read more]({link})", inline=False)
            news_embed.set_footer(text="Provided by Google News RSS")
            await message.channel.send(embed=news_embed)
        user_last_ping[user_id] = now
        return
    elif command_body.startswith("define "):
        word = command_body[7:].strip()
        if word:
            looking_embed = discord.Embed(
                title=f"📖 Looking up definition for: **{word}**...",
                color=0x89f0ff
            )
            await message.channel.send(embed=looking_embed)
            definition = await fetch_definition(word)
            if definition:
            
                reply = f"The word **{word}** stands for:\n\n{definition}"
            else:
                reply = f"⚠️ I could not find a definition for **{word}**."
        else:
            reply = "❓ Please provide a word to define. Example: `b!define empathy`"
    # Commands
    if reply is None:
        if command_body == "ping":
            reply = "Pong! (●—●)."
        elif command_body == "balalala":
            reply = await play_balalala(message)
        elif "marry me" in content.lower():
            reply = "Sorry, I am just a bot and cannot marry anyone. But I appreciate the sentiment! 💙"
        elif "cat" in content or "dog" in content:
            reply = "Hairy Babyy Haaaairrrry Babyy! ₍^. .^₎⟆"
        elif command_body == "staff":
            reply = (
                        "‧͙⁺˚･༓୨ the most darling staff ୧༓･˚⁺‧͙\n\n"
                        "snow - owner\n"
                        "Dalkin - co owner\n"
                        "kaymee - co owner\n\n"
                        "ren - chairman\n"
                        "ha1den - community manager\n\n"
                        "scy - staff head\n"
                        "Status Report - advisor\n\n"
                        "latom - moderator\n"
                        "clvrk - moderator\n"
                        "Swiyls - moderator"
                    )
        elif command_body == "status":
            reply = "I am functioning within normal parameters (ᵔᗜᵔ)"
        elif command_body == "selfie":
            reply = (
                "⠀⠀hi⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣀⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
                "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡠⠚⠉⠀⣀⠈⠱⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
                "⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⠏⠀⠀⠀⡠⠟⠀⠀⣿⣀⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
                "⠀⠀⠀⡀⣀⠀⠀⠀⠀⢸⠀⠘⡿⠁⠀⠀⣠⠞⠁⠀⠉⠉⠓⠲⠦⢤⣄⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
                "⢀⡤⡎⢹⠉⡷⢤⠀⠀⠈⠳⣄⣀⡠⠴⠊⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⠉⠛⠶⣄⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
                "⠸⡇⠸⠀⠃⡇⠸⣇⠀⠀⣠⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⡀⠀⠀⠈⠙⢶⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
                "⢀⡇⠀⠀⠀⠀⠀⠘⣦⠾⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢳⠀⠀⠀⠀⠀⠉⢷⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
                "⢸⡇⠀⠀⠀⠀⠀⠀⠘⣷⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣆⠀⠀⠀⠀⠀⠀⡟⢦⡀⠀⠀⠀⠀⠀⠀⠀\n"
                "⢸⡇⠀⠀⠀⠀⠀⠀⠀⠘⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⣦⠀⠀⠀⠀⠀⠘⡌⢷⡀⠀⠀⠀⠀⠀⠀\n"
                "⠘⡇⠀⠀⠀⠀⠀⠀⠀⠀⢸⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢧⡀⠀⠀⠀⠀⠈⠺⣧⠀⠀⠀⠀⠀⠀\n"
                "⠀⢻⡀⠀⠀⠀⠀⠀⠀⠀⢸⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢷⡀⠀⠀⠀⠀⠀⠹⡆⠀⠀⠀⠀⠀\n"
                "⠀⠘⣇⠀⠀⠀⠀⠀⠀⠀⣼⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⡀⠀⠀⠀⠀⠀⣿⠀⠀⠀⠀⠀\n"
                "⠀⠀⠹⣦⡀⠀⠀⠀⠀⣰⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢷⠀⠀⠀⠀⠀⢿⠀⠀⠀⠀⠀\n"
                "⠀⠀⠀⠈⠙⠒⠦⠔⠚⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⡇⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀\n"
                "⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣇⠀⠀⠀⠀⣿⠀⠀⠀⠀⠀\n"
                "⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠏⣷⠀⢀⢠⡏⠀⠀⠀⠀⠀\n"
                "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⡿⣤⠟⠀⢠⡟⠀⠀⠀⠀⠀⠀\n"
                "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠻⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⡞⠁⠈⠓⠚⠉⠀⠀⠀⠀⠀⠀⠀\n"
                "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡟⠷⣄⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⡾⢻⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
                "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀⠏⠙⠶⢤⣄⣀⡀⠀⠀⢀⣀⣠⡤⠞⠋⠁⡇⢸⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
                "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⡾⠀⠀⠀⠀⠀⠈⠉⠉⡏⠉⠁⠀⠀⠀⠀⠀⢡⣾⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
                "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢿⡀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠀⠀⠀⠀⣸⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
                "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢷⡀⠀⠀⠀⠀⣀⣀⣇⠀⠀⠀⠀⠀⠀⢠⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
                "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢻⣤⠔⠒⠉⠀⢈⣏⠀⠉⠑⠒⢄⣠⠏⠀⠀⠀\n"
                "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠛⠲⠶⠒⠋⠉⠙⠓⠒⠒⠛⠁⠀⠀⠀⠀"
            )
        elif command_body in ("ily", "i love you"):
            reply = "I love you too! (●—●) I am here to care for you."
        elif command_body == "bye":
            reply = "Goodbye! Remember, I am always here if you need me. Take care! (●—●)"
        elif command_body in ("hello", "hi"):
            reply = "Hello I am b4ymax, your personal healthcare companion ԅ(ᵔᗜᵔ)!"
        elif command_body == "help":
            reply = (
                "Here are some commands you can use:\n"
                "`b!ping` - Check if I am online.\n"
                "`b!status` - Get my current status.\n"
                "`b!selfie` - See a picture of me.\n"
                "`b!news` - Get the latest news.\n"
                "`b!define <word>` - Get the definition of a word.\n"
                "`b!balalala` - I join your voice channel and sing.\n"
                "`b!bye` - Say goodbye.\n"
                "`b!8ball` - Ask a question and get a random answer.\n"
                "`b!staff` - See the list of staff members.\n"
                "`b!hi` or `b!hello` - Greet me!\n"
                "`b!ily` or `b!I love you` - Express your love for me.\n"
                "`b!coinflip` or `b!flipcoin` - Flip a coin for a random outcome.\n"
            )
        elif command_body.startswith("8ball"):
            responses = [
                "Yes, definitely.",
                "No, absolutely not.",
                "Maybe, who knows?",
                "Ask again later.",
                "It is certain.",
                "Don't count on it.",
                "My sources say no.",
                "Outlook not so good.",
                "It is decidedly so.",
                "Without a doubt.",
                "You may rely on it.",
                "As I see it, yes.",
                "Runt says no.",
                "snow would kill you if you asked me that.",
                "kaymee is shaking her head. She says, yomama",
                "Dalkin is screaming",
                "Swiyls is nodding",
                "scy is concerned with that question.",
                "latom is neutral about it.",
                "Zulf thinks you're a monkey.",
                "Ariza is disappointed.",
                "Status is giggling.",
                "Silly thinks it's silly.",
                "ha1den has no words.", 
                "Sansei gave his thumbs up.",
                "toast says una, whatever that means...",
                "Renlie is nervously smiling at that.",
                "Ham advises you to find a lawyer.",
                "banana."
            ]
            reply = random.choice(responses)

        elif command_body in ("coinflip", "flipcoin"):
            reply = random.choice(["Heads", "Tails"])
        else:
            reply = random.choice(random_replies)


    # Send final reply
    embed = discord.Embed(
        title="b4ymax (●—●):",
        description=reply,
        color=0x89f0ff
    )
    await message.channel.send(embed=embed)
    user_last_ping[user_id] = now

# Add error logging
@client.event
async def on_error(event, *args, **kwargs):
    print(f"Error in {event}:")
    traceback.print_exc()

token = os.environ.get("DISCORD_TOKEN")
if not token:
    raise SystemExit("DISCORD_TOKEN not found. Add DISCORD_TOKEN=your-token to the .env file.")
client.run(token)
