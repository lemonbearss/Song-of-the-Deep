import os
import json

import requests
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

if not DISCORD_TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN was not found in your .env file.")

OLLAMA_MODEL = "qwen2.5:3b"
OLLAMA_URL = "http://localhost:11434/api/generate"

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


def load_json_file(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ✅ FIXED PATHS FOR RENDER
races = load_json_file("src/data/races.json")
classes = load_json_file("src/data/classes.json")
rules = load_json_file("src/data/rules.json")
weapons = load_json_file("src/data/weapons.json")
factions = load_json_file("src/data/factions.json")


def find_race_by_name(name):
    return next((r for r in races if r["name"].lower() == name.lower()), None)


def find_class_by_name(name):
    return next((c for c in classes if c["name"].lower() == name.lower()), None)


def find_rule_by_name(name):
    return rules.get(name.lower())


def find_weapon_by_name(name):
    return weapons.get(name.lower())


def find_faction_by_name(name):
    return next((f for f in factions if f["name"].lower() == name.lower()), None)


async def race_autocomplete(interaction, current):
    return [app_commands.Choice(name=r["name"], value=r["name"]) for r in races if current.lower() in r["name"].lower()][:25]


async def class_autocomplete(interaction, current):
    return [app_commands.Choice(name=c["name"], value=c["name"]) for c in classes if current.lower() in c["name"].lower()][:25]


async def rule_autocomplete(interaction, current):
    return [app_commands.Choice(name=v["title"], value=k) for k, v in rules.items() if current.lower() in k][:25]


async def weapon_autocomplete(interaction, current):
    return [app_commands.Choice(name=v["title"], value=k) for k, v in weapons.items() if current.lower() in k][:25]


async def faction_autocomplete(interaction, current):
    return [app_commands.Choice(name=f["name"], value=f["name"]) for f in factions if current.lower() in f["name"].lower()][:25]


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")


# ---------------- MENU ----------------
@bot.tree.command(name="menu", description="Show everything the bot offers")
async def menu(interaction):
    embed = discord.Embed(title="Song Keeper Menu", color=discord.Color.dark_teal())

    embed.add_field(
        name="Lookup",
        value=(
            "`/races`\n`/race`\n"
            "`/classes`\n`/class`\n"
            "`/rules`\n`/rule`\n"
            "`/weapons`\n`/weapon`\n"
            "`/factions`\n`/faction`"
        ),
        inline=False
    )

    embed.add_field(
        name="AI",
        value="`/ask`\n`/sanity`",
        inline=False
    )

    await interaction.response.send_message(embed=embed)


# ---------------- RACES ----------------
@bot.tree.command(name="races")
async def races_cmd(interaction):
    await interaction.response.send_message("\n".join(f"• {r['name']}" for r in races))


@bot.tree.command(name="race")
@app_commands.autocomplete(race_name=race_autocomplete)
async def race_cmd(interaction, race_name: str):
    race = find_race_by_name(race_name)
    if not race:
        return await interaction.response.send_message("Race not found", ephemeral=True)

    embed = discord.Embed(title=race["name"], description=race.get("title", ""))
    await interaction.response.send_message(embed=embed)


# ---------------- CLASSES ----------------
@bot.tree.command(name="classes")
async def classes_cmd(interaction):
    await interaction.response.send_message("\n".join(f"• {c['name']}" for c in classes))


@bot.tree.command(name="class")
@app_commands.autocomplete(class_name=class_autocomplete)
async def class_cmd(interaction, class_name: str):
    cls = find_class_by_name(class_name)
    if not cls:
        return await interaction.response.send_message("Class not found", ephemeral=True)

    embed = discord.Embed(title=cls["name"], description=cls.get("description", ""))
    await interaction.response.send_message(embed=embed)


# ---------------- RULES ----------------
@bot.tree.command(name="rules")
async def rules_cmd(interaction):
    await interaction.response.send_message("\n".join(f"• {v['title']}" for v in rules.values()))


@bot.tree.command(name="rule")
@app_commands.autocomplete(rule_name=rule_autocomplete)
async def rule_cmd(interaction, rule_name: str):
    rule = find_rule_by_name(rule_name)
    if not rule:
        return await interaction.response.send_message("Rule not found", ephemeral=True)

    await interaction.response.send_message(rule["text"])


# ---------------- WEAPONS ----------------
@bot.tree.command(name="weapons")
async def weapons_cmd(interaction):
    await interaction.response.send_message("\n".join(f"• {v['title']}" for v in weapons.values()))


@bot.tree.command(name="weapon")
@app_commands.autocomplete(weapon_name=weapon_autocomplete)
async def weapon_cmd(interaction, weapon_name: str):
    weapon = find_weapon_by_name(weapon_name)
    if not weapon:
        return await interaction.response.send_message("Weapon not found", ephemeral=True)

    await interaction.response.send_message(weapon["text"])


# ---------------- FACTIONS ----------------
@bot.tree.command(name="factions")
async def factions_cmd(interaction):
    await interaction.response.send_message("\n".join(f"• {f['name']}" for f in factions))


@bot.tree.command(name="faction")
@app_commands.autocomplete(faction_name=faction_autocomplete)
async def faction_cmd(interaction, faction_name: str):
    faction = find_faction_by_name(faction_name)
    if not faction:
        return await interaction.response.send_message("Faction not found", ephemeral=True)

    embed = discord.Embed(
        title=faction["name"],
        description=faction["description"],
        color=discord.Color.dark_green()
    )

    # ✅ IMAGE SUPPORT
    if faction.get("logo_url"):
        embed.set_thumbnail(url=faction["logo_url"])

    if faction.get("image_url"):
        embed.set_image(url=faction["image_url"])

    embed.add_field(name="Territory", value=", ".join(faction.get("territory", [])) or "None", inline=False)
    embed.add_field(name="Enemies", value=", ".join(faction.get("enemies", [])) or "None", inline=False)
    embed.add_field(name="Goals", value=", ".join(faction.get("goals", [])) or "None", inline=False)

    await interaction.response.send_message(embed=embed)


# ---------------- SANITY ----------------
@bot.tree.command(name="sanity")
async def sanity(interaction, current: int, maximum: int):
    await interaction.response.send_message(f"Sanity: {current}/{maximum}")


# ---------------- ASK ----------------
@bot.tree.command(name="ask")
async def ask(interaction, question: str):
    await interaction.response.defer()

    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": question, "stream": False},
            timeout=10
        )

        data = response.json()
        await interaction.followup.send(data.get("response", "No response"))

    except:
        await interaction.followup.send("AI is currently offline.")


bot.run(DISCORD_TOKEN)
