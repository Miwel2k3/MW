import discord
import asyncio
from discord.ext import commands
from discord import FFmpegPCMAudio
import youtube_dl
from collections import deque
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


intents = discord.Intents.default()
intents.members = True
intents.message_content = True


bot = commands.Bot(command_prefix='!', intents=intents)

queues = {}


def get_queue(guild_id):
    if guild_id not in queues:
        queues[guild_id] = deque()
    return queues[guild_id]


@bot.event
async def on_ready():
    print(f'Conectado como {bot.user.name}')


@bot.command()
async def join(ctx):
    channel = ctx.author.voice.channel
    await channel.connect()
    await ctx.send(f'Conectada al canal de voz: {channel}')


@bot.command()
async def pause(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.pause()
    else:
        await ctx.send("No hay ninguna canción sonando")

@bot.command()
async def resume(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_paused():
        voice.resume()
    else:
        await ctx.send("La canción no está pausada")


@bot.command()
async def exit(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client:
        await voice_client.disconnect()
        await ctx.send('Desconectada del canal de voz')
    else:
        await ctx.send('No estoy conectada a un canal de voz')


async def play_next(ctx):
    queue = get_queue(ctx.guild.id)
    if not queue:
        return

    url = queue.popleft()
    voice_client = ctx.guild.voice_client

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
    }

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            audio_url = info_dict['formats'][0]['url']

        audio_source = discord.FFmpegPCMAudio(
            audio_url,
            before_options="-reconnect 1 -reconnect_at_eof 1 -reconnect_streamed 1 -reconnect_delay_max 2"
        )

        voice_client.play(audio_source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
        await ctx.send('Reproduciendo uwu')

    except Exception as e:
        await ctx.send(f'Error al reproducir música: {str(e)}')


def youtube_search(query):
    youtube = build('youtube', 'v3', developerKey=DEVELOPER_KEY)

    search_response = youtube.search().list(
        q=query,
        part='id,snippet',
        maxResults=1,
        type='video'
    ).execute()

    video_id = search_response['items'][0]['id']['videoId']
    return f'https://www.youtube.com/watch?v={video_id}'


@bot.command()
async def play(ctx, *, query):
    url = youtube_search(query)
    queue = get_queue(ctx.guild.id)
    queue.append(url)

    voice_client = ctx.guild.voice_client
    if not voice_client:
        await ctx.send('No estoy conectada a un canal de voz')
        return

    if not voice_client.is_playing():
        await play_next(ctx)


@bot.command()
async def skip(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.stop()
        await ctx.send("Canción saltada")
    else:
        await ctx.send("No hay ninguna canción sonando")


DEVELOPER_KEY = 'AIzaSyDlK6Y3XIM0ORPx5-vABY0hIkagMgeiyF8'
TOKEN = 'MTEyMzQ1MzI4NzE4MjY1MTQzMg.GiOOdP.DU6aBsly_W-OGr_8blbHWPVL8PovNOBMjYUXUk'

bot.run(TOKEN)
