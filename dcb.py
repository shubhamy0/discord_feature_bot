import discord
from discord.ext import commands, tasks
from server import start
from dotenv import load_dotenv
import json
import os
import random
import logging

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger(__name__)

PREFIX = "-"
DATA_FILE = "./data.json"
OWNER_IDS = {int(os.getenv("OWNER_ID")), int(os.getenv("OWNER_ID2"))}
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))
TARGET_USER_ID = int(os.getenv("TARGET_USER_ID"))

AUTO_REPLY_MAP: dict[int, list[str]] = {}

EMOJI_REACT_MAP: dict[int, list[str]] = {
    int(os.getenv("REACT_TARGET_ID")): ["💀", "🗿", "😂", "🤣", "🤡"],
}

DM_MESSAGES = [
    "hey",
    "hello",
]
used_messages = []

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

def load_json(path: str) -> dict:
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        log.warning(f"File not found: {path}")
        return {}
    except json.JSONDecodeError:
        log.error(f"Invalid JSON in: {path}")
        return {}

# Auto DM Task
@tasks.loop(hours=1)
async def auto_dm():
    global used_messages
    remaining = [m for m in DM_MESSAGES if m not in used_messages]
    if not remaining:
        used_messages = []
        remaining = DM_MESSAGES.copy()
    message = random.choice(remaining)
    used_messages.append(message)
    user = await bot.fetch_user(TARGET_USER_ID)
    if user:
        if message.startswith("http"):
            embed = discord.Embed()
            embed.set_image(url=message)
            await user.send(embed=embed)
        else:
            await user.send(message)

# Global check: only owners can use commands
@bot.check
async def owner_only(ctx: commands.Context) -> bool:
    if ctx.author.id not in OWNER_IDS:
        return False
    return True

@bot.event
async def on_ready():
    auto_dm.start()
    await bot.change_presence(activity=discord.Game(name="online"))
    log.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    log.info(f"Loaded {len(bot.commands)} commands")

@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.CheckFailure):
        return
    if isinstance(error, commands.CommandNotFound):
        if ctx.author.id in OWNER_IDS:
            await ctx.send(f"❓ Unknown command. Try `{PREFIX}help`.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"⚠️ Missing argument: `{error.param.name}`")
    else:
        log.error(f"Unhandled error in '{ctx.command}': {error}")
        await ctx.send("⚠️ Something went wrong. Please try again.")

@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return

    # Log DMs sent to the bot
    if isinstance(message.channel, discord.DMChannel):
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                title="📩 New DM Reply",
                description=message.content or "*No text (maybe an image/GIF)*",
                color=discord.Color.green()
            )
            embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
            embed.set_footer(text=f"User ID: {message.author.id}")
            await log_channel.send(embed=embed)

    # Auto-reply to specific users
    if message.author.id in AUTO_REPLY_MAP:
        replies = AUTO_REPLY_MAP[message.author.id]
        reply = random.choice(replies)
        if reply.startswith("http"):
            embed = discord.Embed()
            embed.set_image(url=reply)
            await message.reply(embed=embed)
        else:
            await message.reply(reply)

    # Auto react to specific users
    if message.author.id in EMOJI_REACT_MAP:
        emoji = random.choice(EMOJI_REACT_MAP[message.author.id])
        await message.add_reaction(emoji)

    await bot.process_commands(message)

@bot.command(help="Say hi to the bot!")
async def hi(ctx: commands.Context):
    await ctx.send(f"Hello, {ctx.author.display_name}! 👋")

@bot.command(help="Look up a saved tag. Usage: -tag <key>")
async def tag(ctx: commands.Context, key: str):
    data = load_json(DATA_FILE)
    if not data:
        await ctx.send("⚠️ Tag database is unavailable right now.")
        return
    value = data.get(key)
    if value:
        await ctx.send(value)
    else:
        await ctx.send(f"❌ No tag found for `{key}`. Try `-tags` to see all available tags.")

@bot.command(help="List all available tags.")
async def tags(ctx: commands.Context):
    data = load_json(DATA_FILE)
    if not data:
        await ctx.send("⚠️ No tags found.")
        return
    keys = ", ".join(f"`{k}`" for k in data.keys())
    await ctx.send(f"📋 Available tags: {keys}")

@bot.command(help="Show bot info and stats.")
async def info(ctx: commands.Context):
    embed = discord.Embed(title="🤖 Bot Info", color=discord.Color.blurple())
    embed.add_field(name="Prefix", value=PREFIX, inline=True)
    embed.add_field(name="Commands", value=len(bot.commands), inline=True)
    embed.add_field(name="Servers", value=len(bot.guilds), inline=True)
    embed.set_footer(text=f"Requested by {ctx.author.display_name}")
    await ctx.send(embed=embed)

@bot.command(help="Send a DM to a user. Usage: -dm @user <message>")
async def dm(ctx: commands.Context, member: discord.Member, *, message: str):
    try:
        await member.send(message)
        await ctx.send(f"✅ DM sent to {member.display_name}!")
    except discord.Forbidden:
        await ctx.send(f"❌ Couldn't DM {member.display_name} — they may have DMs disabled.")
    except discord.HTTPException:
        await ctx.send("⚠️ Something went wrong while sending the DM.")

@bot.command(help="Send a GIF/image DM to a user. Usage: -dmgif @user <url>")
async def dmgif(ctx: commands.Context, member: discord.Member, *, url: str):
    try:
        if "tenor.com/view/" in url:
            gif_id = url.split("-")[-1]
            url = f"https://media.tenor.com/{gif_id}/tenor.gif"
        embed = discord.Embed(color=discord.Color.random())
        embed.set_image(url=url)
        await member.send(embed=embed)
        await ctx.send(f"✅ GIF sent to {member.display_name}!")
    except discord.Forbidden:
        await ctx.send(f"❌ Couldn't DM {member.display_name} — they may have DMs disabled.")

@bot.command(help="Send a DM to any user by ID. Usage: -dmid <user_id> <message>")
async def dmid(ctx: commands.Context, user_id: int, *, message: str):
    try:
        user = await bot.fetch_user(user_id)
        await user.send(message)
        await ctx.send(f"✅ DM sent to {user.name}!")
    except discord.NotFound:
        await ctx.send("❌ User not found.")
    except discord.Forbidden:
        await ctx.send("❌ Couldn't DM that user — they may have DMs disabled.")
    except discord.HTTPException:
        await ctx.send("⚠️ Something went wrong while sending the DM.")

@bot.command(help="Screenshot recent chat. Usage: -screenshot <number of messages>")
async def screenshot(ctx: commands.Context, limit: int = 10):
    messages = []
    async for msg in ctx.channel.history(limit=limit):
        messages.append(f"**{msg.author.display_name}**: {msg.content}")
    messages.reverse()
    chat_log = "\n".join(messages)
    embed = discord.Embed(
        title=f"📸 Last {limit} messages in #{ctx.channel.name}",
        description=chat_log[:4000],
        color=discord.Color.blurple()
    )
    await ctx.send(embed=embed)

start()
bot.run(os.getenv("BOT_TOKEN"), log_handler=None)
