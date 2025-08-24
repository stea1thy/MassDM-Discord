import discord
from discord import Option
import asyncio

intents = discord.Intents.default()
intents.members = True
intents.presences = True  # Required to see who is online

bot = discord.Bot(intents=intents)

@bot.event
async def on_ready():
    activity = discord.Game(name="Check my bio!")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    print(f"✅ Bot is online as {bot.user}")

    
@bot.slash_command(description="Send a message with optional line breaks")
async def send(ctx, message: Option(str, "Use \\n for line breaks")):
    formatted = message.replace("\\n", "\n")
    await ctx.respond(formatted)

@bot.slash_command(description="DM all members and log progress, prioritizing online users")
async def start(
    ctx: discord.ApplicationContext,
    message: Option(str, "Message to send to all members"),
    log_channel: Option(discord.TextChannel, "Channel to post DM updates")
):
    await ctx.respond(f"📬 Starting DMs with online users first. Logging in {log_channel.mention}", ephemeral=True)

    guild = ctx.guild

    # Filter real users
    members = [m for m in guild.members if not m.bot]

    # Prioritize members by presence: online > idle/dnd > offline
    def presence_priority(member):
        status = member.status
        if status == discord.Status.online:
            return 0
        elif status in [discord.Status.idle, discord.Status.dnd]:
            return 1
        else:
            return 2

    members.sort(key=presence_priority)

    count = 0
    for member in members:
        try:
            await member.send(message)
            await log_channel.send(f"✅ Sent to {member.mention} ({member.status})")
            count += 1
        except discord.Forbidden:
            await log_channel.send(f"❌ Could not DM {member.mention} (DMs off or blocked)")
        except Exception as e:
            await log_channel.send(f"⚠️ Error with {member.mention}: {e}")
        
        await asyncio.sleep(20)  # Respect Discord rate limits

    await log_channel.send(f"🎉 Finished. Total successful DMs: {count}")

bot.run("YOURDISCORDBOTTOKEN")
