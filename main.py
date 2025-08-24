import discord
from discord import Option
import asyncio

intents = discord.Intents.default()
intents.members = True
intents.presences = True  # Required to see who is online
intents.message_content = True  # Needed for message content access

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
    # Check if user has administrator permissions
    if not ctx.author.guild_permissions.administrator:
        await ctx.respond("❌ You need administrator permissions to use this command.", ephemeral=True)
        return
        
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
    failed = 0
    
    # Send initial status message
    status_msg = await log_channel.send(f"📤 Starting mass DM to {len(members)} members...")
    
    for i, member in enumerate(members):
        try:
            # Update status message every 10 members
            if i % 10 == 0:
                await status_msg.edit(content=f"📤 Progress: {i}/{len(members)} members processed. Successful: {count}, Failed: {failed}")
            
            await member.send(message)
            await log_channel.send(f"✅ Sent to {member.mention} ({member.status})")
            count += 1
        except discord.Forbidden:
            await log_channel.send(f"❌ Could not DM {member.mention} (DMs off or blocked)")
            failed += 1
        except Exception as e:
            await log_channel.send(f"⚠️ Error with {member.mention}: {e}")
            failed += 1
        
        await asyncio.sleep(20)  # Respect Discord rate limits

    # Send final summary
    await log_channel.send(f"🎉 Finished. Total successful DMs: {count}, Failed: {failed}, Total members: {len(members)}")

# Paste your bot token between the quotes below
bot.run("BOT TOKEN HERE")
