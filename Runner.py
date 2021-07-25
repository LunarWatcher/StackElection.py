import discord
import discord.ext.commands as Cmd
import discord.ext.tasks as tasks

import json
import os
import time
import requests

from conf import API_KEY

# config {{{
config = {}

if os.path.isfile("botconf.json"):
    with open("botconf.json", "r") as f:
        config = json.load(f)

def commitConfig():
    global config
    with open("botconf.json", "w") as f:
        json.dump(config, f)

# }}}
# Cogs {{{
class BotManagement(Cmd.Cog, name = "Bot management"):

    def __init__(self, bot):
        self.bot = bot

    @Cmd.command()
    @Cmd.has_guild_permissions(administrator = True)
    async def setOutputHere(self, ctx):
        global config
        if str(ctx.channel.guild.id) not in config:
            config[str(ctx.channel.guild.id)] = {}
        config[str(ctx.channel.guild.id)]["channel"] = ctx.channel.id

        commitConfig()
        await ctx.reply("Channel changed.")

class ElectionCommands(Cmd.Cog, name = "Election commands"):

    def __init__(self, bot):
        self.bot = bot

# }}}


bot = Cmd.Bot("el!")
bot.add_cog(BotManagement(bot))

# Standard shit {{{
@bot.listen("on_command_error")
async def onGlobalError(ctx, error):
    if isinstance(error, Cmd.MissingPermissions):
        await ctx.reply("You don't have the proper permissions to use that command")
    else:
        await ctx.reply("An error occured while handling your command: " + str(error))

    raise error
# }}}
# Election monitoring {{{

@tasks.loop(seconds = 60 * 60 * 6)
async def task():
    print("henlo, logged in")

@bot.event
async def on_ready():
    print("Bot connected")

    task.start()

# }}}
# Update sites {{{
def updateSites():
    page = 1
    sites = []

    while True:
        r = requests.get(f"https://api.stackexchange.com/2.3/sites?pagesize=100&page={page}")

        res = r.json()
        items = res["items"]
        for site in items:
            if site["site_url"] not in sites:
                sites.append(site["site_url"])

        if not res["has_more"]:
            break
        page += 1
    with open("sites.json", "w") as f:
        json.dump(sites, f)
    return sites

network = []

if not os.path.isfile("sites.json"):
    print("Refreshing network...")
    network = updateSites()
else:
    print("Loading network...")
    with open("sites.json", "r") as f:
        network = json.load(f)

# }}}

bot.run(API_KEY)
