import discord
import time
import random
import aiohttp
import asyncio
import xml.etree.ElementTree as ET
from html import unescape
from discord import FFmpegPCMAudio
import os
import edge_tts

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

user_last_ping = {}
user_waiting_for_pain_rating = {}

COMMAND_PREFIX = "b!"

random_replies = [
    "I am always here if you need me.",
    "Your personal healthcare companion is listening.",
    "Hello! How can I assist you today?",
    "I hope you are having a healthy day.",
    "My purpose is to care for you."
    "Remember, I am always here to help you.",
    "Your health is my priority.",
    "Balalalala",
    "I am here to support you.",
    "Your well-being is important to me.",
]

health_advice = {
    "sadness": (
        "💔 Sadness advice:\n"
        "- Talk to someone you trust about how you feel.\n"
        "- Engage in activities you enjoy to lift your mood.\n"
        "- Consider practicing mindfulness or meditation.\n"
        "- If sadness persists or worsens, please seek professional help.\n"
        "\n Please remember, you are not alone and there are people who care about you.\n"
    ),
    "pain": (
        "🩹 Pain management advice:\n"
        "- Rest and avoid strenuous activities.\n"
        "- Apply a cold or warm compress to the affected area.\n"
        "- Over-the-counter pain relievers like acetaminophen or ibuprofen can help.\n"
        "- If pain persists or is severe, please seek medical care.\n"
        "\n🌐 [More info](https://uhs.princeton.edu/health-resources/common-illnesses)"
    ),
    "headache": (
        "🧠 Headache advice:\n"
        "- Get plenty of rest and stay hydrated.\n"
        "- Try over-the-counter pain relievers like acetaminophen or ibuprofen.\n"
        "- Avoid excessive caffeine and screen time.\n"
        "- If headaches are frequent or severe, consider seeking medical care.\n"
        "\n🌐 [More info](https://uhs.princeton.edu/health-resources/common-illnesses)"
    ),
    "cold": (
        "🤧 Common cold advice:\n"
        "- Drink lots of fluids and get extra rest.\n"
        "- Use saline nasal spray or humidifiers to ease congestion.\n"
        "- Over-the-counter medications can help relieve symptoms.\n"
        "- Seek medical care if symptoms last longer than 10 days or worsen.\n"
        "\n🌐 [More info](https://uhs.princeton.edu/health-resources/common-illnesses)"
    ),
    "sore throat": (
        "😮‍💨 Sore throat advice:\n"
        "- Drink warm liquids like tea or broth.\n"
        "- Gargle with warm salt water.\n"
        "- Use throat lozenges or sprays for relief.\n"
        "- Seek care if sore throat lasts over a week or is very painful.\n"
        "\n🌐 [More info](https://uhs.princeton.edu/health-resources/common-illnesses)"
    ),
    "flu": (
        "🦠 Flu advice:\n"
        "- Rest and drink plenty of fluids.\n"
        "- Use fever reducers like acetaminophen if needed.\n"
        "- Stay home to avoid spreading the virus.\n"
        "- Seek medical care if symptoms are severe or you are at high risk for complications.\n"
        "\n🌐 [More info](https://uhs.princeton.edu/health-resources/common-illnesses)"
    ),
    "nausea": (
        "🤢 Nausea advice:\n"
        "- Try eating small, bland meals.\n"
        "- Sip clear fluids to stay hydrated.\n"
        "- Rest in an upright position after eating.\n"
        "- Seek care if nausea persists or is accompanied by severe pain or dehydration signs.\n"
        "\n🌐 [More info](https://uhs.princeton.edu/health-resources/common-illnesses)"
    ),
    "diarrhea": (
        "🚽 Diarrhea advice:\n"
        "- Drink clear fluids to stay hydrated (e.g. water, broth).\n"
        "- Eat light, bland foods like rice, bananas, toast.\n"
        "- Avoid dairy, fatty, and spicy foods.\n"
        "- Seek care if diarrhea is severe, bloody, or lasts more than 2 days.\n"
        "\n🌐 [More info](https://uhs.princeton.edu/health-resources/common-illnesses)"
    ),
    "fever": (
        "🌡 Fever advice:\n"
        "- Rest and drink plenty of fluids.\n"
        "- Use a cool cloth on your forehead to help lower temperature.\n"
        "- Take acetaminophen or ibuprofen if uncomfortable.\n"
        "- Seek medical care if fever is very high (over 103°F / 39.4°C) or persists for several days.\n"
        "\n🌐 [More info](https://uhs.princeton.edu/health-resources/common-illnesses)"
    ),
    "stomach ache" or "stomachache": (
        "🤕 Stomach ache advice:\n"
        "- Rest and avoid heavy meals.\n"
        "- Drink clear fluids to stay hydrated.\n"
        "- Try ginger tea or peppermint for relief.\n"
        "- Seek care if stomach pain is severe, persistent, or accompanied by vomiting or diarrhea.\n"
    )
}

async def fetch_pokemon_info(name):
    url = f"https://pokeapi.co/api/v2/pokemon/{name.lower()}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return None
            data = await response.json()
            try:
                sprite = data["sprites"]["front_default"]
                types = [t["type"]["name"] for t in data["types"]]
                height = data["height"]
                weight = data["weight"]
                fact = f"Type(s): {', '.join(types).title()}\nHeight: {height / 10} m\nWeight: {weight / 10} kg"
                return {
                    "name": data["name"].title(),
                    "sprite": sprite,
                    "fact": fact
                }
            except (KeyError, IndexError):
                return None

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

def parse_news(xml_text, max_items=5):
    root = ET.fromstring(xml_text)
    items = root.findall(".//item")
    news_list = []
    for item in items[:max_items]:
        title = item.find("title").text
        link = item.find("link").text
        news_list.append((title, link))
    return news_list


@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')

    activity = discord.Activity(type=discord.ActivityType.listening, name="You")
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
    if content.lower().startswith("ronaldo") or content.lower().startswith("Ronaldo"):
        auto_baymax_last_ping = user_last_ping.get(f"auto_baymax_{user_id}", 0)
        if now - auto_baymax_last_ping >= 5:
            baymax_replies = [
            "(●—●) Siuuuuuuuuuuuuuuuu!  ",
        ]
            embed = discord.Embed(
                title="b4ymax (●—●):",
                description=random.choice(baymax_replies),
                color=0x89f0ff
            )
            await message.channel.send(embed=embed)
        user_last_ping[f"auto_baymax_{user_id}"] = now
        return
    
    if content.lower().startswith("b4ymax") or content.lower().startswith("baymax"):
        auto_baymax_last_ping = user_last_ping.get(f"auto_baymax_{user_id}", 0)
        if now - auto_baymax_last_ping >= 5:
            baymax_replies = [
            "(●—●)",
            "Balalalala!",
        ]
            embed = discord.Embed(
            title="b4ymax (●—●):",
            description=random.choice(baymax_replies),
            color=0x89f0ff
        )
        await message.channel.send(embed=embed)
        await message.add_reaction("💙")
        user_last_ping[f"auto_baymax_{user_id}"] = now
        return

    if content.startswith(COMMAND_PREFIX):
        command_body = content[len(COMMAND_PREFIX):].strip().lower()
        should_respond = True
    elif client.user in message.mentions:
        mention_text = f"<@{client.user.id}>"
        command_body = content.replace(mention_text, "").strip().lower()
        should_respond = True

    if not should_respond:
        return
    
    reply = None
# Commands

    if reply is None:
        if command_body == "ping":
            reply = "Pong! (●—●)."
        elif "marry me" in content:
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

        elif command_body == "ily" or command_body == "i love you" or command_body == "Ily" or command_body == "I love you" :
            reply = "I love you too! (●—●) I am here to care for you."

        elif command_body == "dsr":
            reply = ("DSR stands for 'Demon Slayer Retribution', it's a game from Roblox which united us all together many years ago.\n"
            "\n"
            "Although the game is no longer available, the memories and friendships we made will always remain in our hearts.\n"
            "And although some of us have moved on, we still cherish the time we spent together.\n"
            "Thank you for being a part of our community and for all the memories we shared.\n"
            "Thank you for being a part of c4fe even after all these years (●—●) Your support means a lot to us.\n")

        elif command_body == "bye":
            reply = "Goodbye! Remember, I am always here if you need me. Take care! (●—●)"

        elif command_body == "hello" or command_body == "hi":
            reply = "Hello I am b4ymax, your personal healthcare companion ԅ(ᵔᗜᵔ)!"

        elif command_body == "yo" or command_body == "Yo":
            reply = "Gurts! (●—●) How can I assist you today?"

        elif command_body == "yomama":
            yomama = [
                "Yomama is so old, she knew Burger King when he was still a prince! (●—●)",
                "Yomama is so poor, she can't even afford to pay attention! (●—●)",
                "Yomama is so lazy, she took a nap during a marathon! (●—●)",
                "Yomama is so clumsy, she tripped over a wireless internet connection! (●—●)",
                "Yomama is so short, she can hang glide on a Dorito! (●—●)",
                "Yomama is so tall, she tripped over a rock and hit her head on the moon! (●—●)",
                "Yomama is so hairy, Bigfoot took her picture! (●—●)",
                "Yomama is so fat, when she wears a yellow coat, people yell 'Taxi!' (●—●)",
                "Yomama is so skinny, she hula hoops with a Cheerio! (●—●)",
                "Yomama is so old, she walked out of a museum and the alarm went off! (●—●)",
                "Yomama is so poor, ducks throw bread at her! (●—●)",
                "Yomama is so lazy, she has a remote for her remote! (●—●)",
                "Yomama is beautiful, flowers bloom when she walks (●—●)",
                "Yomama is a haaaairrry babyy! ₍^. .^₎⟆",
                "Yomama is so cute, even the emojis blush when she enters the chat! (●—●)",
                "Yomama is so smart, she solved the Rubik's Cube in her sleep! (●—●)",
                "Yomama is so strong, she can lift the spirits of everyone around her! (●—●)",
                "Yomama is so kind, even her shadow gives hugs! (●—●)",
                "Yomama is so funny, even the jokes laugh at her! (●—●)",
                "Yomama is so wise, she gives advice to the stars! (●—●)",
                "Yomama is so magical, she makes unicorns jealous! (●—●)",
                "Yomama is so cool, even ice cubes want to be her friend! (●—●)",
                "Yomama is so awesome, even superheroes ask her for tips! (●—●)",
                "Yomama is so sweet, candy shops ask her for recipes! (●—●)",
                "Yomama is so charming, even the sun shines brighter when she smiles! (●—●)",
                "Yomama is so fashionable, even the runway wants her to walk on it! (●—●)",
                "Yomama is so fat when she got on the scale it said, I need your weight not your phone number. (●—●)"
            ]

            reply = random.choice(yomama)

        elif command_body == "help":                                                            
            reply = (

                "Here are some commands you can use:\n"

                "\n"

                "`b!ping` - Check if I am online.\n"

                "`b!status` - Get my current status.\n"

                "`b!selfie` - See a picture of me.\n"

                "`b!news` - Get the latest news.\n"

                "`b!define <word>` - Get the definition of a word.\n"

                "`b!pain` - Report your pain level.\n"

                "`b!bye` - Say goodbye.\n"

                "`b!8ball` - Ask a question and get a random answer.\n"

                "`b!staff` - See the list of staff members.\n"

                "`b!hi` or `b!hello` - Greet me!\n"

                "`b!ily` or `b!I love you` - Express your love for me.\n"

                "`b!coinflip` or `b!flipcoin` - Flip a coin for a random outcome.\n"

                "`b!yomama` - Get a random yomama joke.\n"

                "`b!yo` - Greet me in a casual way.\n"

                "`b!pokemon <pokemon>` - Get information about a Pokémon.\n"

                "`b!health <condition>` - Get health advice for a condition (e.g. headache, cold, sore throat, flu, nausea, diarrhea, fever).\n"

                "`b!balalalala` - baymax gives you a Balalalala in your voice channel.\n"

                "`b!voice hello` - baymax greets you in your voice channel.\n"

                "`b!say <text>` - baymax speaks the text you provide in your voice channel.\n"

                "\n"
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

        elif command_body == "coinflip" or command_body == "flipcoin":

            outcome = [ 

                "Heads",

                "Tails"

             ]

            reply = random.choice(outcome)
        
    # Handle pain rating continuation
    elif command_body == "pain":
        user_waiting_for_pain_rating[user_id] = True
        reply = "🩺 Please rate your pain from **1 to 10**."

    if user_id in user_waiting_for_pain_rating:
        try:
            pain_level = int(command_body)
            if 1 <= pain_level <= 10:
                reply = f"🩹 Acknowledged. Your pain level is {pain_level}. Please rest while I notify medical personnel."
            else:
                reply = f"⚠️ {pain_level}? That is beyond my scale. Please provide a number between 1 and 10."
        except ValueError:
            reply = random.choice(random_replies)
        user_waiting_for_pain_rating.pop(user_id, None)
    
    elif command_body.startswith("pokemon"):
        parts = command_body.split(maxsplit=1)
        if len(parts) > 1:
            pokemon_name = parts[1].strip()
            poke_info = await fetch_pokemon_info(pokemon_name)
            if poke_info:
                embed = discord.Embed(
                    title=f"🐾 {poke_info['name']} - Pokémon",
                    description=poke_info["fact"],
                    color=0x89f0ff
                )
                embed.set_thumbnail(url=poke_info["sprite"])
            else:
                embed = discord.Embed(
                    title="b4ymax (●—●) :",
                    description=f"⚠️ I could not find information for **{pokemon_name}**.",
                    color=0x89f0ff
                )
        else:
            embed = discord.Embed(
                title="b4ymax (●—●) :",
                description="❓ Please provide a Pokémon name. Example: `pokemon pikachu`",
                color=0x89f0ff
            )
        await message.channel.send(embed=embed)
        user_last_ping[user_id] = now
        return

    elif command_body == "news":
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
            reply = "❓ Please provide a word to define. Example: `!define empathy`"

    elif command_body.startswith("health "):
        condition = command_body[7:].strip()
        advice = health_advice.get(condition)
        if advice:
            embed = discord.Embed(
                title=f"(●—●) Health Advice: {condition.title()}",
                description=advice,
                color=0x89f0ff
        )
        else:
            embed = discord.Embed(
            title="b4ymax (●—●) :",
            description="❓ I don't have advice for that condition. Try: headache, cold, sore throat, flu, nausea, diarrhea, fever.",
            color=0x89f0ff
        )
        await message.channel.send(embed=embed)
        user_last_ping[user_id] = now
        return

    elif command_body == "balalalala":
        if not message.author.voice:
            await message.channel.send("❌ You need to be in a voice channel to use this command!")
            return
            
        channel = message.author.voice.channel
        try:
            vc = await channel.connect()
        except discord.ClientException:
            vc = message.guild.voice_client  # Already connected

        await message.channel.send("(●—●) Balalalala!")

        source = FFmpegPCMAudio("balalala.mp3", executable=os.path.join(os.getcwd(), "ffmpeg"))
        
        def after_playing(error):
            if error:
                print(f'Player error: {error}')
            # Schedule disconnection on the event loop
            asyncio.run_coroutine_threadsafe(vc.disconnect(), client.loop)

        vc.play(source, after=after_playing)
        user_last_ping[user_id] = now
        return

    elif command_body == "voice hello":
        if not message.author.voice:
            await message.channel.send("❌ You need to be in a voice channel to use this command!")
            return
            
        channel = message.author.voice.channel
        try:
            vc = await channel.connect()
        except discord.ClientException:
            vc = message.guild.voice_client  # Already connected

        source = FFmpegPCMAudio("baymaxhello.mp3", executable=os.path.join(os.getcwd(), "ffmpeg"))
        
        def after_playing(error):
            if error:
                print(f'Player error: {error}')
            # Schedule disconnection on the event loop
            asyncio.run_coroutine_threadsafe(vc.disconnect(), client.loop)

        vc.play(source, after=after_playing)
        user_last_ping[user_id] = now
        return

    elif command_body.startswith("say"):
        if not message.author.voice:
            await message.channel.send("❌ You need to be in a voice channel to use this command!")
            return

        text = command_body[len("say "):].strip()
        if not text:
            await message.channel.send("🗣️ Please provide something for Baymax to say.")
            return

        channel = message.author.voice.channel
        try:
            vc = await channel.connect()
        except discord.ClientException:
            vc = message.guild.voice_client  # Already connected

        await message.channel.send(f"(●—●) Speaking: \"{text}\"")

        # Generate TTS
        output_file = "baymax.mp3"
        communicate = edge_tts.Communicate(
                text, 
                voice="en-US-ChristopherNeural",    
                rate="-30%",
        )
        await communicate.save(output_file)

            # Play in voice channel
        audio = FFmpegPCMAudio(output_file, executable="ffmpeg")

        def after_playing(error):
            if error:
                print(f'Player error: {error}')
            # Schedule disconnection on the event loop
            asyncio.run_coroutine_threadsafe(vc.disconnect(), client.loop)

        vc.play(audio, after=after_playing)
        user_last_ping[user_id] = now
        return
    
    # Send final reply
    embed = discord.Embed(

        title="b4ymax (●—●):",

        description=reply,

        color=0x89f0ff
    )

    await message.channel.send(embed=embed)

    user_last_ping[user_id] = now

    if message.author.bot:

        return

    content = message.content.strip().lower()

    # Cooldown
    last_ping = user_last_ping.get(user_id, 0)
    if now - last_ping < 2:
        return

# Add error logging
@client.event
async def on_error(event, *args, **kwargs):
    import traceback
    print(f"Error in {event}:")
    traceback.print_exc()


intents = discord.Intents.default()
intents.message_content = True  # only if you need to read message content


token = os.getenv("DISCORD_TOKEN")
print("TOKEN DEBUG:", token)

if not token:
    raise RuntimeError("DISCORD_TOKEN environment variable is missing!")

client.run(token)



