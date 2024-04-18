import psycopg2
import psycopg2.extras
import pytz
from datetime import datetime
import json

class GameDB:
    def __init__(self, table = 'games'):
        """比賽資料庫操作"""
        self.table=table
        self.host='localhost'
        self.user='foxbot'
        self.password='fox'
        self.dbname='foxbot'
        self.port=5432

    def add_bet(self, id:int, team:int, bet:dict):
        """
        新增賭注
        id: 比賽ID
        team: 0(隊伍一) 1(隊伍二)
        bet: dict {'userid': userid, 'coin': coin_num}
        """ 
        conn = psycopg2.connect(host=self.host, user=self.user,
                              password=self.password, 
                              dbname=self.dbname, port=self.port)
        cur = conn.cursor()
        cur.execute('SELECT state FROM %s WHERE id=%d' %(self.table,id))
        if team == 0:
            bets=cur.fetchall()[0][0]['team1bets']
            print(bets)
            bets.append(bet)
            print(bets)
            cur.execute('UPDATE %s SET state[\'team1bets\'] = \'%s\' WHERE id = %d' %(self.table,json.dumps(bets),id))
        if team == 1:
            bets=cur.fetchall()[0][0]['team2bets']
            print(bets)
            bets.append(bet)
            print(bets)
            cur.execute('UPDATE %s SET state[\'team2bets\'] = \'%s\' WHERE id = %d' %(self.table,json.dumps(bets),id))
        #cur.execute('UPDATE %s set coin = coin + %d WHERE id = %d;' %(self.table,value,id))
        conn.commit()   
        cur.close()
        conn.close()
        return


    def get_game(self, id:int):
        conn = psycopg2.connect(host=self.host, user=self.user,
                              password=self.password, 
                              dbname=self.dbname, port=self.port)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute('SELECT * FROM %s WHERE id=%d' %(self.table,id))
        result=cur.fetchall()
        conn.commit()   
        cur.close()
        conn.close()
        if len(result)==0:
            return -1
        return dict(result[0])

    def del_game(self, id:int):
        conn = psycopg2.connect(host=self.host, user=self.user,
                              password=self.password, 
                              dbname=self.dbname, port=self.port)
        cur = conn.cursor()
        cur.execute('DELETE FROM %s WHERE id=%d' %(self.table,id))
        conn.commit()   
        cur.close()
        conn.close()

    def get_today(self):
        country_time_zone = pytz.timezone('Asia/Taipei')
        country_time = datetime.now(country_time_zone)
        return country_time.strftime("%d/%m/%y")

    def add_game(self, id:int, team1:str, team2:str, rate1:float, rate2:float):
        conn = psycopg2.connect(host=self.host, user=self.user,
                              password=self.password, 
                              dbname=self.dbname, port=self.port)
        cur = conn.cursor()
        cur.execute('SELECT * FROM %s WHERE id=%d' %(self.table,id))
        result=cur.fetchall()
        if len(result)==0:
            cur.execute('INSERT INTO %s(id, team1, team2, datetime, state, rate1, rate2) VALUES(%d, \'%s\' , \'%s\' , \'%s\' , \'{"team1bets":[],"team2bets":[]}\', %f, %f)' %(self.table,id,team1,team2,self.get_today(),rate1,rate2))
        conn.commit()   
        cur.close()
        conn.close()
        
    def get_games(self):
        conn = psycopg2.connect(host=self.host, user=self.user,
                              password=self.password, 
                              dbname=self.dbname, port=self.port)
        cur = conn.cursor()
        cur.execute('SELECT * FROM %s ORDER BY id DESC' %(self.table))
        result=cur.fetchall()
        conn.commit()   
        cur.close()
        conn.close()
        return result
    
#DB = GameDB()
#DB.add_user(0,'OOO')
#DB.add_game(0,'111','222',2.1,2)
#bet = {'userid': 0, 'coin': 1000}
#DB.add_bet(0,0,bet)
#print(DB.get_game(0))
#DB.del_game(0)