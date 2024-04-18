from itertools import count
import discord
import os
from discord.ext import commands
from pprint import pprint
import psycopg2
import asyncio
import random
from threading import Thread
import pytz
from datetime import datetime, timedelta
import GameDB
import UserDB
import time
import threading
import Config
BetChannelID = Config.BetChannelID
BetGMChannelID = Config.BetGMChannelID
BaseBallRoleID = Config.BaseBallRoleID
gameDB = GameDB.GameDB()
userDB = UserDB.UserDB()

def cancel_game(gameid):
    """取消比賽退回賭金"""
    game = gameDB.get_game(gameid)
    gameDB.del_game(gameid)
    team1bets = game['state']['team1bets']
    team2bets = game['state']['team2bets']
    for bet in team1bets:
        userDB.add_coin(bet['userid'],bet['coin'])
    for bet in team2bets:
        userDB.add_coin(bet['userid'],bet['coin'])

    return

def complete_game(gameid,winteam):
    """
    結算比賽
    gameid:比賽ID
    winteam:勝利隊伍 0(隊伍一獲勝) 1(隊伍二獲勝)
    """
    game = gameDB.get_game(gameid)
    gameDB.del_game(gameid)
    rate1 = game['rate1']
    rate2 = game['rate2']
    team1bets = game['state']['team1bets']
    team2bets = game['state']['team2bets']
    if winteam == 0:
        for bet in team1bets:
            userDB.add_coin(bet['userid'], int(bet['coin']*rate1))
    if winteam == 1:
        for bet in team2bets:
            userDB.add_coin(bet['userid'], int(bet['coin']*rate2))
    return

def get_gameid():
    """生成比賽ID"""
    country_time_zone = pytz.timezone('Asia/Taipei')
    country_time = datetime.now(country_time_zone)

    id = (int)(country_time.strftime("1%S%M%H%d%m%y"))
    return id
        

def ignore_exception(IgnoreException=Exception,DefaultVal=None):
    """ Decorator for ignoring exception from a function
    e.g.   @ignore_exception(DivideByZero)
    e.g.2. ignore_exception(DivideByZero)(Divide)(2/0)
    """
    def dec(function):
        def _dec(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except IgnoreException:
                return DefaultVal
        return _dec
    return dec
sint = ignore_exception(ValueError)(int)
sfloat = ignore_exception(ValueError)(float)

#下注表單
class StartGameBetSheet(discord.ui.Modal, title='下注金額'):
    def __init__(self,gameid,info,team,teamname, timeout = None):
        """下注金額輸入表單"""
        super().__init__(timeout=timeout)
        self.gameid = gameid
        self.team = team
        self.teamname = teamname
        self.info = info

    coin = discord.ui.TextInput(label='金額')
    async def on_submit(self, interaction: discord.Interaction):
        coin_num = (sint)(self.coin.value)
        if coin_num == None or coin_num <= 0:#金額格式判定
            await interaction.response.send_message(f'金額錯誤 {self.coin}!', ephemeral=True)
        else:
            usercoin = userDB.get_coin(interaction.user.id)
            #新帳戶
            if usercoin == '404':
                userDB.add_user(interaction.user.id,interaction.user.display_name)
                usercoin = 10000
            #餘額不足
            if usercoin < coin_num:
                await interaction.response.send_message('金額不足', ephemeral=True)
                return
            userid = interaction.user.id
            game = gameDB.get_game(self.gameid)
            #重複下注判定
            for bet in game['state']['team1bets']:
                if userid == bet['userid']:
                    await interaction.response.send_message('已下注此比賽', ephemeral=True)
                    return
            for bet in game['state']['team2bets']:
                if userid == bet['userid']:
                    await interaction.response.send_message('已下注此比賽', ephemeral=True)
                    return
            #下注
            bet = {'userid': userid, 'coin': coin_num}
            gameDB.add_bet(self.gameid,self.team,bet)
            userDB.sub_coin(userid,coin_num)
            await interaction.response.send_message(f'{self.info} : {interaction.user.display_name} 下注 {self.teamname} {self.coin}', ephemeral=False)

#開賭局表單
class StartGameBetSheetGM(discord.ui.Modal, title='建立賽局'):
    def __init__(self, timeout = None):
        """開賭局表單"""
        super().__init__(timeout=timeout)
        
    info = discord.ui.TextInput(label='說明', style=discord.TextStyle.paragraph)
    team1 = discord.ui.TextInput(label='隊伍1')
    rate1 = discord.ui.TextInput(label='隊伍1賠率')
    team2 = discord.ui.TextInput(label='隊伍2')
    rate2 = discord.ui.TextInput(label='隊伍2賠率')
    
    async def on_submit(self, interaction: discord.Interaction):
        rate1f = (sfloat)(self.rate1.value)
        rate2f = (sfloat)(self.rate2.value)
        #賠率格式判定
        if rate1f == None or rate2f == None:
            await interaction.response.send_message('賠率錯誤', ephemeral=True)
            return
        #建立賽局DB
        gameid = get_gameid()
        gameDB.add_game(gameid,self.team1.value,self.team2.value,rate1f,rate2f)
        #建立賽局互動UI
        view = GameBetViewGM(gameid,self.info.value)
        betgmchannel = interaction.guild.get_channel(BetGMChannelID)
        await betgmchannel.send(self.info.value,view=view)
        await interaction.response.send_message('已建立賽局', ephemeral=True)

#發錢表單
class BonusSheetGM(discord.ui.Modal, title='獎勵金額'):
    def __init__(self, timeout = None):
        """發錢表單"""
        super().__init__(timeout=timeout)
    info = discord.ui.TextInput(label='說明', style=discord.TextStyle.paragraph)
    coin = discord.ui.TextInput(label='金額')
    minute = discord.ui.TextInput(label='限時分鐘數')
    async def on_submit(self, interaction: discord.Interaction):
        coin_num = (sint)(self.coin.value)
        minute_num = (sint)(self.minute.value)
        if coin_num == None or coin_num <= 0:#金額格式判定
            await interaction.response.send_message(f'金額錯誤 {self.coin}!', ephemeral=True)
            return
        if minute_num == None or minute_num <= 0:#時間格式判定
            await interaction.response.send_message(f'時間錯誤 {self.coin}!', ephemeral=True)
            return
        self.sec = minute_num * 60
        view = BonusView(coin_num)
        betchannel = interaction.guild.get_channel(BetChannelID)
        await interaction.response.send_message(f'發放金額 {self.coin}!', ephemeral=True)
        endtime = int(datetime.now().timestamp() + self.sec)
        view.msg = await betchannel.send(self.info.value + f'\n<@&{BaseBallRoleID}> <t:{endtime}:R>',view=view)
        await asyncio.sleep(self.sec)
        await view.msg.delete()


class MainView(discord.ui.View):
    def __init__(self, timeout = None):
        """一般主選單"""
        super().__init__(timeout=timeout)
    @discord.ui.button(label="每周獎勵", style=discord.ButtonStyle.success)
    async def login(self,  interaction: discord.Interaction, button: discord.ui.Button):
        userid = interaction.user.id
        login = userDB.get_lastdate(userid)
        #新帳戶
        if login == '404':
            userDB.add_user(userid,interaction.user.display_name)
            await interaction.response.send_message('領取10000幣', ephemeral=True)
            return
        #已領取
        if login == userDB.get_thisweek():
            await interaction.response.send_message('這周已領', ephemeral=True)
            return
        userDB.set_lastdate_thisweek(userid)
        userDB.add_coin(userid,10000)
        await interaction.response.send_message('領取10000幣', ephemeral=True)
    

    @discord.ui.button(label="餘額確認", style=discord.ButtonStyle.success)
    async def check(self,  interaction: discord.Interaction, button: discord.ui.Button):
        coin = userDB.get_coin(interaction.user.id)
        #新帳戶
        if coin == '404':
            userDB.add_user(interaction.user.id,interaction.user.display_name)
            await interaction.response.send_message('餘額:10000', ephemeral=True)
            return
        await interaction.response.send_message('餘額:%d'%(coin), ephemeral=True)

    
    @discord.ui.button(label="排行榜", style=discord.ButtonStyle.success)
    async def rank(self,  interaction: discord.Interaction, button: discord.ui.Button):
        msg = ''
        users = userDB.get_users()
        for user in users:
            user = dict(user)
            msg += (user['name'] + '\t' + str(user['coin']) + '\n')
        await interaction.response.send_message(msg, ephemeral=True)

    @discord.ui.button(label="通知開關", style=discord.ButtonStyle.success)
    async def getrole(self,  interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(BaseBallRoleID)
        urole = interaction.user.get_role(BaseBallRoleID)
        if urole == None:
            await interaction.user.add_roles(role)
            await interaction.response.send_message('開啟通知', ephemeral=True)
        else:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message('關閉通知', ephemeral=True)
    

class GameBetView(discord.ui.View):
    def __init__(self,gameid,info,team1,team2, timeout = None):
        """下注互動訊息"""
        super().__init__(timeout=timeout)
        self.gameid = gameid
        self.info = info
        self.team1 = team1
        self.team2 = team2
        self.game = gameDB.get_game(gameid)
        self.children[0].label = team1 + '(%.2f)'%self.game['rate1']
        self.children[1].label = team2 + '(%.2f)'%self.game['rate2']
    @discord.ui.button(label="team1", style=discord.ButtonStyle.success)
    async def betTeam1(self,  interaction: discord.Interaction, button: discord.ui.Button):
        betsheet = StartGameBetSheet(self.gameid,self.info,0,self.team1)
        await interaction.response.send_modal(betsheet)
    @discord.ui.button(label="team2", style=discord.ButtonStyle.success)
    async def betTeam2(self,  interaction: discord.Interaction, button: discord.ui.Button):
        betsheet = StartGameBetSheet(self.gameid,self.info,1,self.team2)
        await interaction.response.send_modal(betsheet)

#領取獎勵
class BonusView(discord.ui.View):
    def __init__(self,coin, timeout = None):
        """領取獎勵互動消息"""
        super().__init__(timeout=timeout)
        self.coin = coin
        self.ids = []
    @discord.ui.button(label="領取獎勵", style=discord.ButtonStyle.success)
    async def bonus(self,  interaction: discord.Interaction, button: discord.ui.Button):
        #領取判定
        if interaction.user.id in self.ids:
            await interaction.response.send_message('已領取', ephemeral=True)
            return
        self.ids.append(interaction.user.id)
        userid = interaction.user.id
        login = userDB.get_lastdate(userid)
        #新帳戶
        if login == '404':
            userDB.add_user(userid,interaction.user.display_name)
        userDB.add_coin(userid,self.coin)
        await interaction.response.send_message(f'領取{self.coin}', ephemeral=True)
    #async def on_timeout(self):
    #    print('delete bonus')
    #    await self.msg.delete()
    

class MainViewGM(discord.ui.View):
    def __init__(self, timeout = None):
        """管理員主選單"""
        super().__init__(timeout=timeout)
    @discord.ui.button(label="新增賽局", style=discord.ButtonStyle.success)
    async def newgamebet(self,  interaction: discord.Interaction, button: discord.ui.Button):
        sheet = StartGameBetSheetGM()
        await interaction.response.send_modal(sheet)
    @discord.ui.button(label="新增獎勵", style=discord.ButtonStyle.success)
    async def newbonus(self,  interaction: discord.Interaction, button: discord.ui.Button):
        sheet = BonusSheetGM()
        await interaction.response.send_modal(sheet)



class GameBetViewGM(discord.ui.View):
    def __init__(self,gameid,info, timeout = None):
        """比賽後台管理互動消息"""
        super().__init__(timeout=timeout)
        self.startbet = False
        self.endbet = False
        self.gameid = gameid
        self.info = info
        self.game = gameDB.get_game(gameid)


    @discord.ui.button(label="開始下注", style=discord.ButtonStyle.success)
    async def start(self,  interaction: discord.Interaction, button: discord.ui.Button):
        if self.startbet:
            await interaction.response.send_message('賭局已開始', ephemeral=True)
            return
        self.startbet = True
        betchannel = interaction.guild.get_channel(BetChannelID)
        gamebetview = GameBetView(self.gameid,self.info,self.game['team1'],self.game['team2'])
        self.betmsg = await betchannel.send(self.info + f'\n<@&{BaseBallRoleID}>',view=gamebetview)
        await interaction.response.send_message('成功開始下注', ephemeral=True)

    @discord.ui.button(label="中止下注", style=discord.ButtonStyle.success)
    async def bettimeout(self,  interaction: discord.Interaction, button: discord.ui.Button):
        #狀態判定
        if not self.startbet:
            await interaction.response.send_message('賭局未開始', ephemeral=True)
            return
        if self.endbet:
            await interaction.response.send_message('已中止下注', ephemeral=True)
            return
        self.endbet = True
        #判定後處理

        #刪除下注訊息
        await self.betmsg.delete()
        #提示下注中止
        betchannel = interaction.guild.get_channel(BetChannelID)
        await betchannel.send(self.info + '\n中止下注')
        await interaction.response.send_message('成功中止下注', ephemeral=True)

    @discord.ui.button(label="隊伍一獲勝", style=discord.ButtonStyle.success)
    async def team1win(self,  interaction: discord.Interaction, button: discord.ui.Button):
        #狀態判定
        if not self.startbet:
            await interaction.response.send_message('賭局未開始', ephemeral=True)
            return
        if not self.endbet:
            await interaction.response.send_message('未中止下注', ephemeral=True)
            return
        #賭金處理
        complete_game(self.gameid,0)
        #提示
        betchannel = interaction.guild.get_channel(BetChannelID)
        team1 = self.game['team1']
        await betchannel.send(self.info + f'\n{team1}獲勝結算')
        await interaction.response.send_message(self.info + ' 隊伍一獲勝結算', ephemeral=True)
        await interaction.message.delete()

    @discord.ui.button(label="隊伍二獲勝", style=discord.ButtonStyle.success)
    async def team2win(self,  interaction: discord.Interaction, button: discord.ui.Button):
        #狀態判定
        if not self.startbet:
            await interaction.response.send_message('賭局未開始', ephemeral=True)
            return
        if not self.endbet:
            await interaction.response.send_message('未中止下注', ephemeral=True)
            return
        #賭金處理
        complete_game(self.gameid,1)
        #提示
        betchannel = interaction.guild.get_channel(BetChannelID)
        team2 = self.game['team2']
        await betchannel.send(self.info + f'\n{team2}獲勝結算')
        await interaction.response.send_message(self.info + ' 隊伍二獲勝結算', ephemeral=True)
        await interaction.message.delete()

    @discord.ui.button(label="取消賭局", style=discord.ButtonStyle.success)
    async def cancel(self,  interaction: discord.Interaction, button: discord.ui.Button):
        if self.startbet:
            #刪除下注訊息
            await self.betmsg.delete()
        #賭金處理
        cancel_game(self.gameid)
        await interaction.response.send_message(self.info + '\n已取消賭局', ephemeral=True)
        await interaction.message.delete()