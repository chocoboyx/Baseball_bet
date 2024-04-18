import configparser


config = configparser.ConfigParser()
config.read('foxbot.ini')



TOKEN = config['bot']['token']
MemberGuildID = int(config['guild']['id'])
MemberRobotChannelID = int(config['guild']['RobotChannelID'])
BetChannelID = int(config['guild']['BetChannelID'])
BetMenuChannelID = int(config['guild']['BetMenuChannelID'])
BetGMChannelID = int(config['guild']['BetGMChannelID'])
BaseBallRoleID = int(config['guild']['BaseBallRoleID'])