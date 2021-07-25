#!/usr/bin/python3

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
        if str(ctx.channel.guild.id) not in config["servers"]:
            config["servers"][str(ctx.channel.guild.id)] = {}
        config["servers"][str(ctx.channel.guild.id)]["channel"] = ctx.channel.id

        commitConfig()
        await ctx.reply("Channel changed.")

    @Cmd.command()
    @Cmd.has_guild_permissions(administrator = True)
    async def subscribe(self, ctx, site: str, lastElection: int):
        global config
        global network

        if site not in network:
            await ctx.reply("URL not found in the known network.")
            return

        if "network" not in config:
            config["network"] = {}

        config["network"][site] = lastElection
        commitConfig()
        await ctx.reply(f"Successfully set up <{site}> with last election being number {lastElection}")

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
    global config

    print("henlo, logged in")

    if "network" in config:
        #                         vvvv create a copy, because we can't have nice things
        for site, lastElection in list(config["network"].items()):
            r = requests.get(f"{site}/election/{lastElection}")
            if r.status_code != 404:
                for server, sConfig in config["servers"].items():
                    if "channel" not in sConfig:
                        continue
                    try:
                        await bot.get_channel(sConfig["channel"]).send(f"Election started: {site}/election/{lastElection}")
                    except:
                        pass
                    config["network"][site] = lastElection + 1
    commitConfig()


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

if "servers" not in config:
    config["servers"] = {}

bot.run(API_KEY)
