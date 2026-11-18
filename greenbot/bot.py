import os
from dataclasses import dataclass

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

AZURACAST_BASE_URL = os.getenv("AZURACAST_BASE_URL", "https://radio.913aycltfm.com").rstrip("/")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")


@dataclass(frozen=True)
class Station:
    key: str
    name: str
    slug: str
    stream_url: str


STATIONS = {
    "main": Station(
        "main", "91.3 Ayclt FM", "91.3_ayclt_fm",
        os.getenv("STREAM_MAIN", "https://radio.913aycltfm.com/listen/91.3_ayclt_fm/913aycltfm")
    ),
    "hd2": Station(
        "hd2", "91.3 Ayclt FM HD2", "91.3_ayclt_fm_hd2",
        os.getenv("STREAM_HD2", "")
    ),
    "hd3": Station(
        "hd3", "91.3 Ayclt FM HD3", "91.3_ayclt_fm_hd3",
        os.getenv("STREAM_HD3", "")
    ),
    "hd4": Station(
        "hd4", "91.3 Ayclt FM HD4", "91.3_ayclt_fm_hd4",
        os.getenv("STREAM_HD4", "")
    ),
}

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


async def get_nowplaying(station: Station):
    url = f"{AZURACAST_BASE_URL}/api/nowplaying/{station.slug}"
    timeout = aiohttp.ClientTimeout(total=12)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.json()


def current_song(data):
    np = data.get("now_playing") or {}
    song = np.get("song") or {}
    artist = song.get("artist") or "Unknown artist"
    title = song.get("title") or "Unknown title"
    return f"{artist} — {title}"


async def require_voice(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.followup.send("This command can only be used in a server.", ephemeral=True)
        return None
    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.followup.send("Join a voice channel first.", ephemeral=True)
        return None
    channel = interaction.user.voice.channel
    voice = interaction.guild.voice_client
    if voice and voice.channel != channel:
        await voice.move_to(channel)
    elif not voice:
        voice = await channel.connect()
    else:
        voice = interaction.guild.voice_client
    return voice


async def play_station(interaction: discord.Interaction, station_key: str):
    station = STATIONS[station_key]
    if not station.stream_url:
        await interaction.followup.send(
            f"The stream URL for **{station.name}** is not configured yet. "
            f"Set `{'STREAM_' + station_key.upper()}` in the environment.",
            ephemeral=True
        )
        return

    voice = await require_voice(interaction)
    if voice is None:
        return

    if voice.is_playing() or voice.is_paused():
        voice.stop()

    source = discord.FFmpegPCMAudio(
        station.stream_url,
        before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        options="-vn"
    )
    voice.play(source)
    await interaction.followup.send(f"▶️ Now playing **{station.name}**.")


@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Logged in as {bot.user}; synced {len(synced)} slash commands.")
    except Exception as exc:
        print(f"Slash-command sync failed: {exc}")


@bot.tree.command(name="join", description="Join your current voice channel.")
async def join(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    voice = await require_voice(interaction)
    if voice:
        await interaction.followup.send(f"Connected to **{voice.channel.name}**.", ephemeral=True)


@bot.tree.command(name="play", description="Play one of the 91.3 Ayclt FM stations.")
@app_commands.describe(station="Choose the station to play")
@app_commands.choices(station=[
    app_commands.Choice(name="91.3 Ayclt FM", value="main"),
    app_commands.Choice(name="91.3 Ayclt FM HD2", value="hd2"),
    app_commands.Choice(name="91.3 Ayclt FM HD3", value="hd3"),
    app_commands.Choice(name="91.3 Ayclt FM HD4", value="hd4"),
])
async def play(interaction: discord.Interaction, station: app_commands.Choice[str]):
    await interaction.response.defer()
    await play_station(interaction, station.value)


@bot.tree.command(name="stations", description="Show all available radio stations.")
async def stations(interaction: discord.Interaction):
    lines = []
    for station in STATIONS.values():
        status = "Stream configured" if station.stream_url else "Stream URL not configured"
        lines.append(f"**{station.name}** — `{station.slug}` · {status}")
    embed = discord.Embed(
        title="91.3 Ayclt FM Radio Stations",
        description="\n".join(lines),
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="listeners", description="Show current listener counts for all stations.")
async def listeners(interaction: discord.Interaction):
    await interaction.response.defer()
    lines = []
    for station in STATIONS.values():
        try:
            data = await get_nowplaying(station)
            count = (data.get("listeners") or {}).get("current", 0)
            lines.append(f"**{station.name}:** {count}")
        except Exception:
            lines.append(f"**{station.name}:** unavailable")
    await interaction.followup.send(embed=discord.Embed(
        title="Current Listeners",
        description="\n".join(lines),
        color=discord.Color.green()
    ))


@bot.tree.command(name="nowplaying", description="Show what's playing on a station.")
@app_commands.describe(station="Choose the station")
@app_commands.choices(station=[
    app_commands.Choice(name="91.3 Ayclt FM", value="main"),
    app_commands.Choice(name="91.3 Ayclt FM HD2", value="hd2"),
    app_commands.Choice(name="91.3 Ayclt FM HD3", value="hd3"),
    app_commands.Choice(name="91.3 Ayclt FM HD4", value="hd4"),
])
async def nowplaying(interaction: discord.Interaction, station: app_commands.Choice[str]):
    await interaction.response.defer()
    selected = STATIONS[station.value]
    try:
        data = await get_nowplaying(selected)
        song = current_song(data)
        listeners = (data.get("listeners") or {}).get("current", 0)
        await interaction.followup.send(
            f"🎵 **{selected.name}**\nNow playing: **{song}**\nListeners: **{listeners}**"
        )
    except Exception as exc:
        await interaction.followup.send(f"Couldn't retrieve now-playing data for **{selected.name}**: `{exc}`")


@bot.tree.command(name="stop", description="Stop the current radio stream.")
async def stop(interaction: discord.Interaction):
    voice = interaction.guild.voice_client if interaction.guild else None
    if voice and (voice.is_playing() or voice.is_paused()):
        voice.stop()
        await interaction.response.send_message("⏹️ Radio playback stopped.")
    else:
        await interaction.response.send_message("Nothing is currently playing.", ephemeral=True)


@bot.tree.command(name="leave", description="Disconnect Greenbot from the voice channel.")
async def leave(interaction: discord.Interaction):
    voice = interaction.guild.voice_client if interaction.guild else None
    if voice:
        await voice.disconnect()
        await interaction.response.send_message("Disconnected from the voice channel.")
    else:
        await interaction.response.send_message("I'm not connected to a voice channel.", ephemeral=True)


if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing. Copy .env.example to .env and set your bot token.")

bot.run(DISCORD_TOKEN)
