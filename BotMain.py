from itertools import count
import discord
import os
import BotUI
import Config
from discord.ext import commands
from pprint import pprint
import psycopg2
import asyncio
import random
from threading import Thread
import pytz
from datetime import datetime

TOKEN = Config.TOKEN
MemberGuildID = Config.MemberGuildID
MemberRobotChannelID = Config.MemberRobotChannelID
BetMenuChannelID = Config.BetMenuChannelID
BetGMChannelID = Config.BetGMChannelID

intent=discord.Intents.all()
client = commands.Bot(command_prefix = "!",intents=intent)
# 起動時呼叫
@client.event
async def on_ready():
    """登入執行"""
    print('成功登入')
    guild = client.get_guild(MemberGuildID)
    betchannel = guild.get_channel(BetMenuChannelID)
    betgmchannel = guild.get_channel(BetGMChannelID)
    await betchannel.send(view=BotUI.MainView())
    await betgmchannel.send(view=BotUI.MainViewGM())


@client.command()
async def test(ctx):
    #view = BotUI.GameBetView('','','111','222')
    await ctx.send("test")

# Bot起動
client.run(TOKEN)