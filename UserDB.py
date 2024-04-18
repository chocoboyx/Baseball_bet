import psycopg2
import psycopg2.extras
import pytz
from datetime import datetime

class UserDB:
    def __init__(self, table = 'users'):
        self.table=table
        self.host='localhost'
        self.user='foxbot'
        self.password='fox'
        self.dbname='foxbot'
        self.port=5432
    def add_coin(self,id,value):
        conn = psycopg2.connect(host=self.host, user=self.user,
                              password=self.password, 
                              dbname=self.dbname, port=self.port)
        cur = conn.cursor()
        cur.execute('UPDATE %s set coin = coin + %d WHERE id = %d;' %(self.table,value,id))
        conn.commit()   
        cur.close()
        conn.close()
        return
    
    def add_all_coin(self,value):
        conn = psycopg2.connect(host=self.host, user=self.user,
                              password=self.password, 
                              dbname=self.dbname, port=self.port)
        cur = conn.cursor()
        cur.execute('UPDATE %s set coin = coin + %d;' %(self.table,value,id))
        conn.commit()   
        cur.close()
        conn.close()
        return
    
    def sub_coin(self,id,value):
        conn = psycopg2.connect(host=self.host, user=self.user,
                              password=self.password, 
                              dbname=self.dbname, port=self.port)
        cur = conn.cursor()
        cur.execute('UPDATE %s set coin = coin - %d WHERE id = %d;' %(self.table,value,id))
        conn.commit()   
        cur.close()
        conn.close()
        return

    def get_coin(self,id):
        conn = psycopg2.connect(host=self.host, user=self.user,
                              password=self.password, 
                              dbname=self.dbname, port=self.port)
        cur = conn.cursor()
        cur.execute('SELECT coin FROM %s WHERE id=%d' %(self.table,id))
        result=cur.fetchall()
        conn.commit()   
        cur.close()
        conn.close()
        if len(result)==0:
            return '404'
        return result[0][0]

    def get_lastdate(self,id):
        conn = psycopg2.connect(host=self.host, user=self.user,
                              password=self.password, 
                              dbname=self.dbname, port=self.port)
        cur = conn.cursor()
        cur.execute('SELECT login FROM %s WHERE id=%d' %(self.table,id))
        result=cur.fetchall()
        conn.commit()   
        cur.close()
        conn.close()
        if len(result)==0:
            return '404'
        return result[0][0]

    def set_lastdate_today(self,id):
        conn = psycopg2.connect(host=self.host, user=self.user,
                              password=self.password, 
                              dbname=self.dbname, port=self.port)
        cur = conn.cursor()
        cur.execute('UPDATE %s set login = \'%s\' WHERE id = %d;' %(self.table, self.get_today(), id))
        conn.commit()   
        cur.close()
        conn.close()
        return

    def set_lastdate_thisweek(self,id):
        conn = psycopg2.connect(host=self.host, user=self.user,
                              password=self.password, 
                              dbname=self.dbname, port=self.port)
        cur = conn.cursor()
        cur.execute('UPDATE %s set login = \'%s\' WHERE id = %d;' %(self.table, self.get_thisweek(), id))
        conn.commit()   
        cur.close()
        conn.close()
        return
    
    def get_today(self):
        country_time_zone = pytz.timezone('Asia/Taipei')
        country_time = datetime.now(country_time_zone)
        return country_time.strftime("%d/%m/%y")
    
    def get_thisweek(self):
        country_time_zone = pytz.timezone('Asia/Taipei')
        country_time = datetime.now(country_time_zone)
        return country_time.strftime("%W/%y")

    def add_user(self,id,name):
        conn = psycopg2.connect(host=self.host, user=self.user,
                              password=self.password, 
                              dbname=self.dbname, port=self.port)
        cur = conn.cursor()
        cur.execute('SELECT * FROM %s WHERE id=%d' %(self.table,id))
        result=cur.fetchall()
        if len(result)==0:
            cur.execute('INSERT INTO %s(id, coin, name,login) VALUES(%d, 10000 , \'%s\',\'%s\')' %(self.table,id,name,self.get_today()))
        conn.commit()   
        cur.close()
        conn.close()
        
    def get_users(self):
        conn = psycopg2.connect(host=self.host, user=self.user,
                              password=self.password, 
                              dbname=self.dbname, port=self.port)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute('SELECT * FROM %s ORDER BY coin DESC' %(self.table))
        result=cur.fetchall()
        conn.commit()   
        cur.close()
        conn.close()
        return result
    

'''
DATABASE_URL = 'postgres://cypfbrscqjhrxk:3c432fe34f2dfb37b374e7cb348851993972bf7a31d88fd76de34e3266fe3dfe@ec2-3-234-131-8.compute-1.amazonaws.com:5432/d1lubcdiabgh26'

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()
cur.execute('UPDATE users set coin = 10000000 WHERE id = 4569')
conn.commit()   
cur.close()
conn.close()

'''
#DB = UserDB()
#DB.add_user(0,'OOO')
#print(DB.get_today())
#print((DB.get_users()[0]).id)