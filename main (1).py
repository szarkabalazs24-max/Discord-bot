import discord
from discord import app_commands
from discord.ext import commands
import os
import json
import datetime
import asyncio
import re
from keep_alive import keep_alive

TOKEN = os.getenv("DISCORD_TOKEN")

WARN_FILE = "warns.json"

FOOTER_TEXT = "✨ Numiz’s MM Basement szervere ✨"
BAN_FOOTER = "🚫 A közösség védelme érdekében eltávolítva!\n✨ Numiz’s MM Basement szervere ✨"

FORBIDDEN_WORDS = [
"f@szom","szarka","baszam","geci","kutya","anyad","anyád",
"fasz","fasszopo","hülye","hulye","köcsög","kocsog",
"fsz","coco","meleg","buzi","bazmeg","bazdmeg"
]

LINK_REGEX = r"http[s]?://"

# ---------------- WARN ----------------

def get_warns():
    if not os.path.exists(WARN_FILE):
        return {}

    with open(WARN_FILE,"r") as f:
        try:
            return json.load(f)
        except:
            return {}

def save_warns(data):
    with open(WARN_FILE,"w") as f:
        json.dump(data,f,indent=4)

def add_point(user_id):

    data=get_warns()
    uid=str(user_id)

    if uid not in data:
        data[uid]=0

    data[uid]+=1

    save_warns(data)

    return data[uid]

# ---------------- BOT ----------------

class MyBot(commands.Bot):

    def __init__(self):

        intents=discord.Intents.all()

        super().__init__(
            command_prefix="!",
            intents=intents
        )

    async def setup_hook(self):
        await self.tree.sync()

bot=MyBot()

# ---------------- EMBED ----------------

def decorative_embed(title,text,ban=False):

    desc=f"┏━━━━━━━━━━━━━━━━━━━━━━┓\n┣ {text}\n┗━━━━━━━━━━━━━━━━━━━━━━┛"

    embed=discord.Embed(
        title=title,
        description=desc,
        color=discord.Color.blue()
    )

    if ban:
        embed.set_footer(text=BAN_FOOTER)
    else:
        embed.set_footer(text=FOOTER_TEXT)

    return embed

# ---------------- READY ----------------

@bot.event
async def on_ready():

    print(f"✅ Bot online: {bot.user}")

# ---------------- AUTOMOD ----------------

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    if re.search(LINK_REGEX,message.content):

        try:
            await message.delete()
        except:
            pass

        await message.author.timeout(datetime.timedelta(minutes=10))

        await message.channel.send(
            embed=decorative_embed(
                "Link tiltva",
                f"{message.author.mention} link tiltott\n10 perc némítás"
            )
        )

    if any(word in message.content.lower() for word in FORBIDDEN_WORDS):

        try:
            await message.delete()
        except:
            pass

        points=add_point(message.author.id)

        mute=points*2

        await message.author.timeout(datetime.timedelta(minutes=mute))

        await message.channel.send(
            embed=decorative_embed(
                "Automod",
                f"{message.author.mention} tiltott szó!\n{mute} perc némítás"
            )
        )

    await bot.process_commands(message)

# ---------------- /MOND ----------------

@bot.tree.command(name="mond",description="A bot küld üzenetet")
async def mond(interaction:discord.Interaction,szoveg:str):

    if not interaction.user.guild_permissions.manage_messages:

        await interaction.response.send_message(
            "❌ Nincs jogod ehhez",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        "✅ Üzenet elküldve",
        ephemeral=True
    )

    await interaction.channel.send(szoveg)

# ---------------- NÉMÍTÁS ----------------

@bot.tree.command(name="nemitas",description="Felhasználó némítása")
async def nemitas(interaction:discord.Interaction,felhasznalo:discord.Member,percek:int,indok:str):

    await felhasznalo.timeout(datetime.timedelta(minutes=percek))

    await interaction.response.send_message(
        embed=decorative_embed(
            "🔨 Némítás",
            f"{felhasznalo.mention} némítva {percek} percre\nIndok: {indok}"
        )
    )

# ---------------- NÉMÍTÁS FELOLDÁS ----------------

@bot.tree.command(name="nemitas_feloldasa",description="Némítás feloldása")
async def unmute(interaction:discord.Interaction,felhasznalo:discord.Member):

    await felhasznalo.timeout(None)

    await interaction.response.send_message(
        embed=decorative_embed(
            "🔓 Némítás feloldva",
            f"{felhasznalo.mention} újra beszélhet"
        )
    )

# ---------------- FIGYELMEZTETÉS ----------------

@bot.tree.command(name="figyelmeztetes",description="Figyelmeztetés")
async def warn(interaction:discord.Interaction,felhasznalo:discord.Member,indok:str):

    points=add_point(felhasznalo.id)

    mute=points*2

    await felhasznalo.timeout(datetime.timedelta(minutes=mute))

    await interaction.response.send_message(
        embed=decorative_embed(
            "⚠️ Figyelmeztetés",
            f"{felhasznalo.mention} figyelmeztetve\nPontok: {points}\nNémítás: {mute} perc"
        )
    )

# ---------------- WARN LEKÉRÉS ----------------

@bot.tree.command(name="figyelmeztetesek",description="Warn pontok")
async def warns(interaction:discord.Interaction,felhasznalo:discord.Member):

    data=get_warns()

    pont=data.get(str(felhasznalo.id),0)

    await interaction.response.send_message(
        embed=decorative_embed(
            "Figyelmeztetések",
            f"{felhasznalo.mention} pontjai: {pont}"
        )
    )

# ---------------- WARN TÖRLÉS ----------------

@bot.tree.command(name="figyelmeztetes_torles",description="Warn törlés")
async def warn_delete(interaction:discord.Interaction,felhasznalo:discord.Member):

    data=get_warns()

    data[str(felhasznalo.id)]=0

    save_warns(data)

    await interaction.response.send_message(
        embed=decorative_embed(
            "Warn törölve",
            f"{felhasznalo.mention} pontjai törölve"
        )
    )

# ---------------- ÜZENET TÖRLÉS ----------------

@bot.tree.command(name="torles",description="Üzenetek törlése")
async def clear(interaction:discord.Interaction,mennyiseg:int):

    await interaction.channel.purge(limit=mennyiseg)

    await interaction.response.send_message(
        f"{mennyiseg} üzenet törölve",
        ephemeral=True
    )

# ---------------- TICKET ----------------

class TicketClose(discord.ui.View):

    @discord.ui.button(label="🔒 Bezárás",style=discord.ButtonStyle.red)

    async def close(self,interaction:discord.Interaction,button):

        await interaction.response.send_message("Ticket törlés 5 mp múlva")

        await asyncio.sleep(5)

        await interaction.channel.delete()

class TicketPanel(discord.ui.View):

    @discord.ui.button(label="🎫 Support",style=discord.ButtonStyle.blurple)

    async def support(self,interaction:discord.Interaction,button):

        overwrites={
            interaction.guild.default_role:discord.PermissionOverwrite(view_channel=False),
            interaction.user:discord.PermissionOverwrite(view_channel=True,send_messages=True)
        }

        ch=await interaction.guild.create_text_channel(
            f"ticket-{interaction.user.name}",
            overwrites=overwrites
        )

        await interaction.response.send_message(
            f"Ticket létrehozva: {ch.mention}",
            ephemeral=True
        )

        await ch.send(
            embed=decorative_embed(
                "Ticket",
                "Írd le a problémád"
            ),
            view=TicketClose()
        )

@bot.tree.command(name="ticket_panel",description="Ticket panel")
async def ticket_panel(interaction:discord.Interaction):

    await interaction.response.send_message(
        embed=decorative_embed(
            "Ticket rendszer",
            "Nyiss ticketet"
        ),
        view=TicketPanel()
    )

keep_alive()
bot.run(TOKEN)