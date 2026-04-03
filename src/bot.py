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


races = load_json_file("data/races.json")
classes = load_json_file("data/classes.json")
rules = load_json_file("data/rules.json")
weapons = load_json_file("data/weapons.json")
factions = load_json_file("data/factions.json")


SMART_KEYWORDS = {
    "stealth": [
        "stealth", "shadow", "shadows", "hidden", "hide", "sneak",
        "surprise", "unseen", "night", "dark", "speed", "agility"
    ],
    "tank": [
        "tank", "defense", "defensive", "durable", "durability",
        "fortitude", "armor", "heavy", "shield", "survive", "survivability"
    ],
    "damage": [
        "damage", "dps", "burst", "crit", "critical", "attack",
        "weapon", "kill", "offense", "offensive"
    ],
    "healing": [
        "heal", "healing", "support", "restore", "regen",
        "life", "blood", "recovery"
    ],
    "fire": [
        "fire", "burn", "burning", "flame", "flames", "lava"
    ],
    "ice": [
        "ice", "frost", "freeze", "frozen", "cold"
    ],
    "lightning": [
        "lightning", "thunder", "storm", "electric", "shock", "static"
    ],
    "wind": [
        "wind", "gale", "air", "mobility", "movement", "speed"
    ],
    "shadow": [
        "shadow", "darkness", "fear", "dark", "stealth", "hidden"
    ],
    "blood": [
        "blood", "bleed", "life force", "siphon", "heal"
    ],
    "weapons": [
        "weapon", "weapons", "light weapon", "medium weapon", "heavy weapon", "crit"
    ],
    "sanity": [
        "sanity", "insanity", "madness", "tier", "scyphozia"
    ],
    "traits": [
        "trait", "traits", "vitality", "erudition", "proficiency", "songchant"
    ],
    "factions": [
        "faction", "factions", "authority", "ministry", "union", "divers",
        "hive", "legions", "etrea", "summer company", "navae"
    ]
}


def find_race_by_name(race_name: str):
    for race in races:
        if race["name"].lower() == race_name.lower():
            return race
    return None


def find_class_by_name(class_name: str):
    for cls in classes:
        if cls["name"].lower() == class_name.lower():
            return cls
    return None


def find_rule_by_name(rule_name: str):
    return rules.get(rule_name.lower())


def find_weapon_by_name(weapon_name: str):
    return weapons.get(weapon_name.lower())


def find_faction_by_name(faction_name: str):
    for faction in factions:
        if faction["name"].lower() == faction_name.lower():
            return faction
    return None


def format_race(race: dict) -> str:
    return (
        f"Race: {race.get('name', 'Unknown')}\n"
        f"Title: {race.get('title', 'N/A')}\n"
        f"Aspect: {race.get('aspect', 'N/A')}\n"
        f"Size: {race.get('size', 'N/A')}\n"
        f"Speed: {race.get('speed', 'N/A')}\n"
        f"Languages: {', '.join(race.get('languages', []))}\n"
        f"Ability Score Increase: {race.get('ability_score_increase', {})}\n"
        f"Traits: {race.get('traits', [])}\n"
        f"Variants: {race.get('variants', [])}\n"
    )


def format_class(cls: dict) -> str:
    return (
        f"Class: {cls.get('name', 'Unknown')}\n"
        f"Title: {cls.get('title', 'N/A')}\n"
        f"Description: {cls.get('description', 'N/A')}\n"
        f"Role: {cls.get('role', 'N/A')}\n"
        f"Hit Die: {cls.get('hit_die', 'N/A')}\n"
        f"Primary Stats: {cls.get('primary_stats', [])}\n"
        f"Traits: {cls.get('traits', [])}\n"
    )


def format_rule(rule_key: str, rule_value: dict) -> str:
    return (
        f"Rule Key: {rule_key}\n"
        f"Title: {rule_value.get('title', 'N/A')}\n"
        f"Text: {rule_value.get('text', 'N/A')}\n"
    )


def format_weapon(weapon_key: str, weapon_value: dict) -> str:
    return (
        f"Weapon Category: {weapon_key}\n"
        f"Title: {weapon_value.get('title', 'N/A')}\n"
        f"Property: {weapon_value.get('property', 'N/A')}\n"
        f"Text: {weapon_value.get('text', 'N/A')}\n"
    )


def format_faction(faction: dict) -> str:
    return (
        f"Faction: {faction.get('name', 'Unknown')}\n"
        f"Description: {faction.get('description', 'N/A')}\n"
        f"Territory: {faction.get('territory', [])}\n"
        f"Enemies: {faction.get('enemies', [])}\n"
        f"Goals: {faction.get('goals', [])}\n"
        f"Party Rep: {faction.get('party_rep', 'N/A')}\n"
    )


def build_small_fallback_context() -> str:
    race_names = ", ".join(race["name"] for race in races)
    class_names = ", ".join(cls["name"] for cls in classes)
    rule_names = ", ".join(rule["title"] for rule in rules.values())
    weapon_names = ", ".join(weapon["title"] for weapon in weapons.values())
    faction_names = ", ".join(faction["name"] for faction in factions)

    return (
        "AVAILABLE DATA SUMMARY\n\n"
        f"Races: {race_names}\n"
        f"Classes: {class_names}\n"
        f"Rules: {rule_names}\n"
        f"Weapons: {weapon_names}\n"
        f"Factions: {faction_names}\n"
    )


def text_contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def get_keyword_groups(question: str) -> set[str]:
    q = question.lower()
    groups = set()

    for group_name, keywords in SMART_KEYWORDS.items():
        if text_contains_any(q, keywords):
            groups.add(group_name)

    return groups


def get_context_from_keyword_groups(groups: set[str]) -> list[str]:
    sections = []

    if "sanity" in groups and "sanity" in rules:
        sections.append("=== RELEVANT RULES ===\n" + format_rule("sanity", rules["sanity"]))

    if "traits" in groups and "traits" in rules:
        sections.append("=== RELEVANT RULES ===\n" + format_rule("traits", rules["traits"]))

    if "weapons" in groups and "weapons" in rules:
        sections.append("=== RELEVANT RULES ===\n" + format_rule("weapons", rules["weapons"]))

    if "fire" in groups:
        for cls in classes:
            if cls["name"].lower() == "flamecharmer":
                sections.append("=== RELEVANT CLASSES ===\n" + format_class(cls))
                break

    if "ice" in groups:
        for cls in classes:
            if cls["name"].lower() == "frostdrawer":
                sections.append("=== RELEVANT CLASSES ===\n" + format_class(cls))
                break

    if "lightning" in groups:
        for cls in classes:
            if cls["name"].lower() == "thundercaller":
                sections.append("=== RELEVANT CLASSES ===\n" + format_class(cls))
                break

    if "wind" in groups:
        for cls in classes:
            if cls["name"].lower() == "galebreather":
                sections.append("=== RELEVANT CLASSES ===\n" + format_class(cls))
                break

    if "shadow" in groups or "stealth" in groups:
        matched_shadow_blocks = []
        for cls in classes:
            if cls["name"].lower() == "shadowcast":
                matched_shadow_blocks.append(format_class(cls))
        for race in races:
            race_name = race["name"].lower()
            if race_name in {"felinor", "kiron", "etrean", "celtor"}:
                matched_shadow_blocks.append(format_race(race))
        if matched_shadow_blocks:
            sections.append("=== RELEVANT STEALTH / SHADOW OPTIONS ===\n" + "\n".join(matched_shadow_blocks))

    if "blood" in groups or "healing" in groups:
        matched_blood_blocks = []
        for cls in classes:
            if cls["name"].lower() in {"bloodrend", "life weaver"}:
                matched_blood_blocks.append(format_class(cls))
        if matched_blood_blocks:
            sections.append("=== RELEVANT HEALING / BLOOD OPTIONS ===\n" + "\n".join(matched_blood_blocks))

    if "tank" in groups:
        matched_tank_blocks = []
        for cls in classes:
            if cls["name"].lower() in {"ironsinger", "attunementless", "earth shift"}:
                matched_tank_blocks.append(format_class(cls))
        if "heavy" in weapons:
            matched_tank_blocks.append(format_weapon("heavy", weapons["heavy"]))
        if matched_tank_blocks:
            sections.append("=== RELEVANT TANK OPTIONS ===\n" + "\n".join(matched_tank_blocks))

    if "damage" in groups:
        matched_damage_blocks = []
        for cls in classes:
            if cls["name"].lower() in {"flamecharmer", "thundercaller", "bloodrend", "shadowcast"}:
                matched_damage_blocks.append(format_class(cls))
        if matched_damage_blocks:
            sections.append("=== RELEVANT DAMAGE OPTIONS ===\n" + "\n".join(matched_damage_blocks))

    return sections


def dedupe_sections(sections: list[str]) -> list[str]:
    seen = set()
    result = []
    for section in sections:
        if section not in seen:
            seen.add(section)
            result.append(section)
    return result


def get_relevant_context(question: str) -> str:
    q = question.lower()
    sections = []

    matched_races = []
    for race in races:
        if race["name"].lower() in q:
            matched_races.append(format_race(race))

    matched_classes = []
    for cls in classes:
        if cls["name"].lower() in q:
            matched_classes.append(format_class(cls))

    matched_rules = []
    for rule_key, rule_value in rules.items():
        if rule_key.lower() in q or rule_value["title"].lower() in q:
            matched_rules.append(format_rule(rule_key, rule_value))

    matched_weapons = []
    for weapon_key, weapon_value in weapons.items():
        if weapon_key.lower() in q or weapon_value["title"].lower() in q:
            matched_weapons.append(format_weapon(weapon_key, weapon_value))

    matched_factions = []
    for faction in factions:
        if faction["name"].lower() in q:
            matched_factions.append(format_faction(faction))

    if matched_races:
        sections.append("=== RELEVANT RACES ===\n" + "\n".join(matched_races))

    if matched_classes:
        sections.append("=== RELEVANT CLASSES ===\n" + "\n".join(matched_classes))

    if matched_rules:
        sections.append("=== RELEVANT RULES ===\n" + "\n".join(matched_rules))

    if matched_weapons:
        sections.append("=== RELEVANT WEAPONS ===\n" + "\n".join(matched_weapons))

    if matched_factions:
        sections.append("=== RELEVANT FACTIONS ===\n" + "\n".join(matched_factions))

    keyword_groups = get_keyword_groups(question)
    keyword_sections = get_context_from_keyword_groups(keyword_groups)
    sections.extend(keyword_sections)

    sections = dedupe_sections(sections)

    if sections:
        return "\n\n".join(sections)

    return build_small_fallback_context()


async def race_autocomplete(interaction: discord.Interaction, current: str):
    matches = []
    for race in races:
        if current.lower() in race["name"].lower():
            matches.append(app_commands.Choice(name=race["name"], value=race["name"]))
    return matches[:25]


async def class_autocomplete(interaction: discord.Interaction, current: str):
    matches = []
    for cls in classes:
        if current.lower() in cls["name"].lower():
            matches.append(app_commands.Choice(name=cls["name"], value=cls["name"]))
    return matches[:25]


async def rule_autocomplete(interaction: discord.Interaction, current: str):
    matches = []
    for rule_name, rule_data in rules.items():
        if current.lower() in rule_name.lower():
            matches.append(app_commands.Choice(name=rule_data["title"], value=rule_name))
    return matches[:25]


async def weapon_autocomplete(interaction: discord.Interaction, current: str):
    matches = []
    for weapon_name, weapon_info in weapons.items():
        if current.lower() in weapon_name.lower():
            matches.append(app_commands.Choice(name=weapon_info["title"], value=weapon_name))
    return matches[:25]


async def faction_autocomplete(interaction: discord.Interaction, current: str):
    matches = []
    for faction in factions:
        if current.lower() in faction["name"].lower():
            matches.append(app_commands.Choice(name=faction["name"], value=faction["name"]))
    return matches[:25]


def split_text(text: str, limit: int = 1900):
    chunks = []
    while len(text) > limit:
        split_at = text.rfind("\n", 0, limit)
        if split_at == -1:
            split_at = limit
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip()
    if text:
        chunks.append(text)
    return chunks


@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s).")
        for command in synced:
            print(f"- {command.name}")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

    print(f"Logged in as {bot.user}")


@bot.tree.command(name="menu", description="Show everything the bot offers")
async def menu_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Song Keeper Menu",
        description="Main commands and what they do.",
        color=discord.Color.dark_teal()
    )

    embed.add_field(
        name="Lookup",
        value=(
            "`/races` — List all races\n"
            "`/race` — View one race\n"
            "`/classes` — List all classes\n"
            "`/class` — View one class\n"
            "`/rules` — List all rules\n"
            "`/rule` — View one rule\n"
            "`/weapons` — List all weapon categories\n"
            "`/weapon` — View one weapon category\n"
            "`/factions` — List all factions\n"
            "`/faction` — View one faction"
        ),
        inline=False
    )

    embed.add_field(
        name="AI",
        value=(
            "`/ask` — Ask the local AI about your campaign\n"
            "`/sanity` — Check sanity tiers and effects"
        ),
        inline=False
    )

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="races", description="List all races in the campaign")
async def races_command(interaction: discord.Interaction):
    race_names = [race["name"] for race in races]

    embed = discord.Embed(
        title="Races",
        description="\n".join(f"• {name}" for name in race_names),
        color=discord.Color.purple()
    )

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="race", description="Get information about a specific race")
@app_commands.autocomplete(race_name=race_autocomplete)
async def race_command(interaction: discord.Interaction, race_name: str):
    race = find_race_by_name(race_name)

    if race is None:
        await interaction.response.send_message(
            f"I couldn't find a race called '{race_name}'.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title=race.get("name", "Unknown Race"),
        description=f"*{race.get('title', 'No title')}*",
        color=discord.Color.purple()
    )

    embed.add_field(
        name="Basic Info",
        value=(
            f"**Aspect:** {race.get('aspect', 'N/A')}\n"
            f"**Size:** {race.get('size', 'N/A')}\n"
            f"**Speed:** {race.get('speed', 'N/A')} ft\n"
            f"**Languages:** {', '.join(race.get('languages', ['N/A']))}"
        ),
        inline=False
    )

    ability_scores = race.get("ability_score_increase", {})
    ability_text = ", ".join(f"{stat.upper()} +{value}" for stat, value in ability_scores.items()) or "N/A"
    embed.add_field(name="Ability Scores", value=ability_text, inline=False)

    traits = race.get("traits", [])
    traits_text = "\n".join(
        f"**{trait.get('name', 'Unknown Trait')}**: {trait.get('description', 'N/A')}"
        for trait in traits
    ) or "No traits listed."
    embed.add_field(name="Traits", value=traits_text[:1024], inline=False)

    variants = race.get("variants", [])
    variants_text = "\n".join(
        f"**{variant.get('name', 'Unknown Variant')}**: {variant.get('bonus', 'N/A')}"
        for variant in variants
    ) or "No variants listed."
    embed.add_field(name="Variants", value=variants_text[:1024], inline=False)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="classes", description="List all classes in the campaign")
async def classes_command(interaction: discord.Interaction):
    class_names = [cls["name"] for cls in classes]

    embed = discord.Embed(
        title="Classes",
        description="\n".join(f"• {name}" for name in class_names),
        color=discord.Color.blue()
    )

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="class", description="Get information about a specific class")
@app_commands.autocomplete(class_name=class_autocomplete)
async def class_command(interaction: discord.Interaction, class_name: str):
    cls = find_class_by_name(class_name)

    if cls is None:
        await interaction.response.send_message(
            f"I couldn't find a class called '{class_name}'.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title=cls.get("name", "Unknown Class"),
        description=f"*{cls.get('title', 'No title')}*",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="Overview",
        value=(
            f"**Description:** {cls.get('description', 'N/A')}\n"
            f"**Role:** {cls.get('role', 'N/A')}\n"
            f"**Hit Die:** {cls.get('hit_die', 'N/A')}"
        ),
        inline=False
    )

    primary_stats = cls.get("primary_stats", [])
    primary_stats_text = ", ".join(primary_stats) if primary_stats else "N/A"
    embed.add_field(name="Primary Stats", value=primary_stats_text, inline=False)

    traits = cls.get("traits", [])
    traits_text = "\n".join(
        f"**{trait.get('name', 'Unknown Trait')}**: {trait.get('description', 'N/A')}"
        for trait in traits
    ) or "No class traits listed."
    embed.add_field(name="Class Features", value=traits_text[:1024], inline=False)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="rules", description="List all rule topics")
async def rules_command(interaction: discord.Interaction):
    rule_titles = [rule_data["title"] for rule_data in rules.values()]

    embed = discord.Embed(
        title="Rules",
        description="\n".join(f"• {title}" for title in rule_titles),
        color=discord.Color.gold()
    )

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="rule", description="Get information about a specific rule")
@app_commands.autocomplete(rule_name=rule_autocomplete)
async def rule_command(interaction: discord.Interaction, rule_name: str):
    rule = find_rule_by_name(rule_name)

    if rule is None:
        await interaction.response.send_message(
            f"I couldn't find a rule called '{rule_name}'.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title=rule.get("title", "Rule"),
        description=rule.get("text", "No rule text found.")[:4096],
        color=discord.Color.gold()
    )

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="weapons", description="List all weapon categories")
async def weapons_command(interaction: discord.Interaction):
    weapon_titles = [weapon_info["title"] for weapon_info in weapons.values()]

    embed = discord.Embed(
        title="Weapons",
        description="\n".join(f"• {title}" for title in weapon_titles),
        color=discord.Color.teal()
    )

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="weapon", description="Get information about a specific weapon category")
@app_commands.autocomplete(weapon_name=weapon_autocomplete)
async def weapon_command(interaction: discord.Interaction, weapon_name: str):
    weapon = find_weapon_by_name(weapon_name)

    if weapon is None:
        await interaction.response.send_message(
            f"I couldn't find a weapon category called '{weapon_name}'.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title=weapon["title"],
        description=f"**Property:** {weapon['property']}\n\n{weapon['text']}",
        color=discord.Color.teal()
    )

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="factions", description="List all factions in the campaign")
async def factions_command(interaction: discord.Interaction):
    faction_names = [faction["name"] for faction in factions]

    embed = discord.Embed(
        title="Factions",
        description="\n".join(f"• {name}" for name in faction_names),
        color=discord.Color.dark_green()
    )

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="faction", description="Get information about a specific faction")
@app_commands.autocomplete(faction_name=faction_autocomplete)
async def faction_command(interaction: discord.Interaction, faction_name: str):
    faction = find_faction_by_name(faction_name)

    if faction is None:
        await interaction.response.send_message(
            f"I couldn't find a faction called '{faction_name}'.",
            ephemeral=True
        )
        return

    territory_text = "\n".join(f"• {place}" for place in faction.get("territory", [])) or "None"
    enemies_text = "\n".join(f"• {enemy}" for enemy in faction.get("enemies", [])) or "None"
    goals_text = "\n".join(f"• {goal}" for goal in faction.get("goals", [])) or "None"

    embed = discord.Embed(
        title=faction.get("name", "Unknown Faction"),
        description=faction.get("description", "No description available."),
        color=discord.Color.dark_green()
    )

    if faction.get("logo_url"):
        embed.set_thumbnail(url=faction["logo_url"])

    if faction.get("image_url"):
        embed.set_image(url=faction["image_url"])

    embed.add_field(name="Territory", value=territory_text[:1024], inline=False)
    embed.add_field(name="Enemies", value=enemies_text[:1024], inline=False)
    embed.add_field(name="Goals", value=goals_text[:1024], inline=False)
    embed.add_field(name="Party Rep", value=faction.get("party_rep", "N/A"), inline=False)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="sanity", description="Check sanity tier and effects")
@app_commands.describe(current="Current sanity", maximum="Maximum sanity")
async def sanity_command(interaction: discord.Interaction, current: int, maximum: int):
    if maximum <= 0:
        await interaction.response.send_message(
            "Maximum sanity must be greater than 0.",
            ephemeral=True
        )
        return

    if current < 0:
        current = 0

    if current > maximum:
        current = maximum

    lost = maximum - current
    threshold = maximum / 3
    tier = int(lost // threshold)

    if tier <= 0:
        tier_name = "Stable"
        effect = "No insanity tier effects currently apply."
        color = discord.Color.green()
    elif tier == 1:
        tier_name = "Tier 1 – False Reality"
        effect = "All skill rolls are made with disadvantage."
        color = discord.Color.orange()
    elif tier == 2:
        tier_name = "Tier 2 – Tremors"
        effect = (
            "At the start of your turn, roll 1d20:\n"
            "• 10 or lower → lose your bonus action\n"
            "• 11 or higher → lose your main action"
        )
        color = discord.Color.red()
    else:
        tier_name = "Tier 3 – Complete Collapse"
        effect = (
            "Lose 25% of your maximum HP every 15 real-life minutes.\n"
            "This HP cannot be regained while insane.\n"
            "If you remain at Tier 3 for 1 full hour, you die."
        )
        color = discord.Color.dark_red()

    embed = discord.Embed(title="Sanity", color=color)
    embed.add_field(name="Current Sanity", value=f"{current}/{maximum}", inline=False)
    embed.add_field(name="Sanity Lost", value=str(lost), inline=False)
    embed.add_field(name="Current Tier", value=tier_name, inline=False)
    embed.add_field(name="Effects", value=effect, inline=False)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="ask", description="Ask the AI about your homebrew campaign")
@app_commands.describe(question="Ask a question about races, classes, rules, weapons, or factions")
async def ask_command(interaction: discord.Interaction, question: str):
    await interaction.response.defer()

    try:
        relevant_context = get_relevant_context(question)

        prompt = f"""
You are a Discord assistant for a homebrew tabletop campaign.

RULES:
- ONLY answer using the provided campaign data
- DO NOT make up rules, lore, mechanics, or details
- If the answer is not clearly in the data, say you cannot confirm it
- Be concise but helpful
- If the user asks for a comparison or recommendation, base it only on the provided data
- Do not mention hidden system logic, keywords, or internal matching

CAMPAIGN DATA:
{relevant_context}

QUESTION:
{question}
"""

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )

        response.raise_for_status()
        data = response.json()
        answer = data.get("response", "No response.").strip()

        if not answer:
            answer = "I couldn't generate an answer."

        chunks = split_text(answer)

        first_embed = discord.Embed(
            title="Ask",
            description=chunks[0],
            color=discord.Color.fuchsia()
        )

        await interaction.followup.send(embed=first_embed)

        for chunk in chunks[1:]:
            await interaction.followup.send(chunk)

    except requests.exceptions.ConnectionError:
        await interaction.followup.send(
            "AI is currently offline.",
            ephemeral=True
        )
    except requests.exceptions.Timeout:
        await interaction.followup.send(
            "AI is currently offline.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(
            f"There was an error while asking the local AI:\n`{e}`",
            ephemeral=True
        )


bot.run(DISCORD_TOKEN)