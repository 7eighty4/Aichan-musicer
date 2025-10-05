import nextcord
from nextcord.ext import commands
import yt_dlp
import asyncio
import os
from dotenv import load_dotenv
import traceback # Import the traceback module

load_dotenv() # Loads the .env file with your token

# --- BOT SETUP ---
intents = nextcord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- GLOBAL STATE ---
bot.queues = {}

# --- FFMPEG OPTIONS ---
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# --- HELPER FUNCTION TO START PLAYBACK ---
async def play_next(ctx):
    guild_id = ctx.guild.id
    if guild_id in bot.queues and bot.queues[guild_id]:
        song = bot.queues[guild_id].pop(0)
        
        try:
            source = nextcord.FFmpegPCMAudio(song['stream_url'], **FFMPEG_OPTIONS)
            
            embed = nextcord.Embed(
                title="🎵 Now Playing",
                description=f"**[{song['title']}]({song['webpage_url']})**",
                color=nextcord.Color.green()
            )
            embed.set_thumbnail(url=song['thumbnail'])
            embed.add_field(name="Requested by", value=song['requester'].mention)
            
            ctx.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
            
            await ctx.send(embed=embed, view=PlayerControls(ctx))

        except Exception as e:
            # Send a generic error to Discord
            error_embed = nextcord.Embed(title="❌ Playback Error", description="An unknown error occurred. Please check the logs for details.", color=nextcord.Color.red())
            await ctx.send(embed=error_embed)
            
            # Print the FULL detailed error to your Railway logs
            print("--- An error occurred in play_next ---")
            traceback.print_exc()
            print("------------------------------------")
            
            # Try to play the next song in the queue if there is one
            await play_next(ctx)

    else:
        await ctx.send(embed=nextcord.Embed(description="✅ Queue finished! I'm leaving the channel.", color=nextcord.Color.blue()))
        await ctx.voice_client.disconnect()


# --- INTERACTIVE BUTTONS VIEW ---
class PlayerControls(nextcord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=None)
        self.ctx = ctx

    @nextcord.ui.button(label="⏸️ Pause", style=nextcord.ButtonStyle.secondary)
    async def pause_button(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        if self.ctx.voice_client and self.ctx.voice_client.is_playing():
            self.ctx.voice_client.pause()
            await interaction.response.send_message("Playback paused.", ephemeral=True)
        else:
            await interaction.response.send_message("Nothing is playing.", ephemeral=True)

    @nextcord.ui.button(label="▶️ Resume", style=nextcord.ButtonStyle.secondary)
    async def resume_button(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        if self.ctx.voice_client and self.ctx.voice_client.is_paused():
            self.ctx.voice_client.resume()
            await interaction.response.send_message("Playback resumed.", ephemeral=True)
        else:
            await interaction.response.send_message("Playback is not paused.", ephemeral=True)

    @nextcord.ui.button(label="⏭️ Skip", style=nextcord.ButtonStyle.primary)
    async def skip_button(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        if self.ctx.voice_client and self.ctx.voice_client.is_playing():
            self.ctx.voice_client.stop()
            await interaction.response.send_message("Song skipped.", ephemeral=True)
        else:
            await interaction.response.send_message("Nothing to skip.", ephemeral=True)

    @nextcord.ui.button(label="⏹️ Stop", style=nextcord.ButtonStyle.danger)
    async def stop_button(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        if self.ctx.voice_client:
            bot.queues[self.ctx.guild.id] = []
            self.ctx.voice_client.stop()
            await self.ctx.voice_client.disconnect()
            await interaction.response.send_message("Playback stopped and queue cleared. Disconnecting.", ephemeral=True)

# --- BOT COMMANDS ---
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

@bot.command()
async def join(ctx):
    """Makes the bot join the voice channel of the command author."""
    if not ctx.author.voice:
        await ctx.send(f"{ctx.author.name} is not connected to a voice channel.")
        return
        
    channel = ctx.author.voice.channel
    if ctx.voice_client:
        await ctx.voice_client.move_to(channel)
    else:
        await channel.connect()
    await ctx.send(f"✅ Connected to: **{channel.name}**")

@bot.command()
async def play(ctx, *, search: str):
    """Adds a song to the queue and starts playing if the queue was empty."""
    if not ctx.author.voice:
        await ctx.send("You need to be in a voice channel to use this command.")
        return

    if not ctx.voice_client:
        await ctx.author.voice.channel.connect()

    guild_id = ctx.guild.id
    await ctx.send(f"🔎 Searching for: **{search}**...")

    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'noplaylist': 'True',
        'quiet': True,
    }

    cookie_file_path = "cookies.txt"
    if 'YOUTUBE_COOKIES' in os.environ:
        with open(cookie_file_path, 'w') as f:
            f.write(os.environ['YOUTUBE_COOKIES'])
        ydl_opts['cookiefile'] = cookie_file_path

    loop = asyncio.get_event_loop()
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(f"ytsearch:{search}", download=False))
            if 'entries' not in info or not info['entries']:
                await ctx.send("Couldn't find any song matching that query.")
                return
            video = info['entries'][0]
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")
            return
            
    song = {
        'title': video.get('title', 'Unknown Title'),
        'stream_url': video['url'],
        'thumbnail': video.get('thumbnail'),
        'webpage_url': video.get('webpage_url'),
        'requester': ctx.author
    }

    if guild_id not in bot.queues:
        bot.queues[guild_id] = []
    bot.queues[guild_id].append(song)
    
    embed = nextcord.Embed(
        title="✅ Added to Queue",
        description=f"**[{song['title']}]({song['webpage_url']})**",
        color=nextcord.Color.blue()
    )
    embed.set_thumbnail(url=song['thumbnail'])
    embed.add_field(name="Position in queue", value=len(bot.queues[guild_id]))
    await ctx.send(embed=embed)
    
    if not ctx.voice_client.is_playing():
        await play_next(ctx)

@bot.command()
async def pause(ctx):
    """Pauses the current song."""
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Playback paused.")
    else:
        await ctx.send("Nothing is currently playing.")

@bot.command()
async def resume(ctx):
    """Resumes the current song."""
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Playback resumed.")
    else:
        await ctx.send("The playback is not paused.")

@bot.command()
async def queue(ctx):
    """Displays the current song queue."""
    guild_id = ctx.guild.id
    if guild_id not in bot.queues or not bot.queues[guild_id]:
        await ctx.send(embed=nextcord.Embed(description="The queue is currently empty.", color=nextcord.Color.orange()))
        return

    embed = nextcord.Embed(title="🎶 Current Queue", color=nextcord.Color.purple())
    queue_list = ""
    for i, song in enumerate(bot.queues[guild_id][:10]):
        queue_list += f"`{i+1}.` [{song['title']}]({song['webpage_url']}) | Requested by {song['requester'].mention}\n"
    
    embed.description = queue_list
    embed.set_footer(text=f"Showing {len(bot.queues[guild_id][:10])} of {len(bot.queues[guild_id])} songs.")
    await ctx.send(embed=embed)

@bot.command()
async def skip(ctx):
    """Skips the current song."""
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ Song skipped!")
    else:
        await ctx.send("Nothing is playing to skip.")

@bot.command()
async def stop(ctx):
    """Stops playback, clears the queue, and disconnects."""
    if ctx.voice_client:
        bot.queues[ctx.guild.id] = []
        ctx.voice_client.stop()
        await ctx.voice_client.disconnect()
        await ctx.send("⏹️ Playback stopped, queue cleared, and disconnected.")
        
@bot.command()
async def resetvoice(ctx):
    """Disconnects and reconnects the bot to fix voice issues."""
    if ctx.voice_client:
        channel = ctx.voice_client.channel
        await ctx.voice_client.disconnect()
        await asyncio.sleep(1) # Give it a second to disconnect cleanly
        await channel.connect()
        await ctx.send(f"🎤 Voice connection has been reset in **{channel.name}**.")
    else:
        await ctx.send("I'm not in a voice channel to reset.")

# --- RUN THE BOT ---
bot.run(os.environ['DISCORD_TOKEN'])
