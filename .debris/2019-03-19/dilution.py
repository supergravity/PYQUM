'''Reading Dilution Status'''

from pathlib import Path
from datetime import datetime
from time import mktime
from os import listdir
from numpy import diff
from telnetlib import Telnet
from pyqum.instrument.analyzer import derivative, curve

class bluefors:

    def __init__(self):
        self.LogPath = Path(r'\\BLUEFORSAS\BlueLogs')
        self.Days = listdir(self.LogPath)

    def whichday(self):
        total = len(self.Days)
        for i,day in enumerate(self.Days):
            print("%s. %s" %(i+1,day))
        while True:
            try:
                k = int(input("Which day would you like to check out (1-%s): " %total))
                if k-1 in range(total):
                    break
            except(ValueError):
                print("Bad index. Please use numeric!")

        return k-1

        
    def selectday(self, index):
        try:
            self.Date = self.Days[index]
            print("Date selected: %s"%self.Date)
        except(ValueError): 
            print("index might be out of range")
            pass
    
    def pressurelog(self, Channel):
        LogFile = self.LogPath / self.Date / ("maxigauge " + self.Date + ".log")
        with open(LogFile, 'r') as L:
            L = L.read()
        Plog = L.split('\n')[:-1]
        Plog = [x for x in Plog if ',,' not in x] #filter-out bad logs
        t = [datetime.strptime(x.split("CH")[0][:-1].split(',')[1], '%H:%M:%S') for x in Plog]
        startime = t[0].strftime('%H:%M:%S')
        t = [(x-t[0]).total_seconds()/3600 for x in t]
        P = [float(x.split("CH")[Channel][14:21]) for x in Plog]
        P_stat = [int(x.split("CH")[Channel][11]) for x in Plog]

        return startime, t, P, P_stat

    def temperaturelog(self, Channel, Unit='K'):
        LogFile = self.LogPath / self.Date / ("CH%s T "%Channel + self.Date + ".log")
        with open(LogFile, 'r') as L:
            L = L.read()
        Tlog = list([x.split(',') for x in L.split('\n')[:-1]])
        t, T = [datetime.strptime(x[1], '%H:%M:%S') for x in Tlog], [float(x[2]) for x in Tlog]
        startime = t[0].strftime('%H:%M:%S')
        t = [(x-t[0]).total_seconds()/3600 for x in t]
        if Unit.upper() == 'C':
            T = [x - 273 for x in T]

        return startime, t, T

    def initiate(self, ip="192.168.1.23", port=8325):
        self.tell = Telnet(ip, port)
        # self.tell.write("remote\n".encode('ascii'))
        # print(self.tell.read_until(b"\r\n").decode('ascii').replace('\r\n',''))
        self.tell.write("control 1\n".encode('ascii'))
        control = self.tell.read_until(b"\r\n").decode('ascii').replace('\r\n','')
        self.tell.write("remote 1\n".encode('ascii'))
        remote = self.tell.read_until(b"\r\n").decode('ascii').replace('\r\n','')
        if remote.split(': ')[1] == '1': print("Dilution connected: %s"%control.split(' ')[3])
        else: print("NO remote: make sure the server is configured correctly!")
        
    def gauge(self, Channel):
            self.tell.write(("mgstatus %s\n"%Channel).encode('ascii'))
            output = self.tell.read_until(b"\r\n").decode('ascii').replace('\r\n','').split(": ")
            return output[1]

    def close(self):
        self.tell.write("exit\n".encode('ascii'))
        print("Dilution's server disconnected!")
        
class valve(bluefors):

        def __init__(self, tell):
            super().__init__()
            self.tell = tell
        
        def status(self, Channel):
            self.tell.write(("status v%s\n"%Channel).encode('ascii'))
            output = self.tell.read_until(b"\r\n").decode('ascii').replace('\r\n','').split(": ")
            return output[1]

class scroll(bluefors):

        def __init__(self, tell):
            super().__init__()
            self.tell = tell
        
        def status(self, Channel):
            self.tell.write(("status scroll%s\n"%Channel).encode('ascii'))
            output = self.tell.read_until(b"\r\n").decode('ascii').replace('\r\n','').split(": ")
            return output[1]

        def off(self, Channel):
            self.tell.write(("off scroll%s\n"%Channel).encode('ascii'))
            output = self.tell.read_until(b"\r\n").decode('ascii').replace('\r\n','').split(": ")
            return output[1]

        def on(self, Channel):
            self.tell.write(("on scroll%s\n"%Channel).encode('ascii'))
            output = self.tell.read_until(b"\r\n").decode('ascii').replace('\r\n','').split(": ")
            return output[1]

def test():
    b = bluefors()
    # b.selectday(b.whichday())
    # Ch = 3
    # P = b.pressure(Ch)
    # curve(P[1], P[2], "P%s Starting %s"%(Ch, P[0]), "t(hr)", "P(mbar)")
    # t, dPdt = derivative(P[1], P[2], 3)
    # curve(t, dPdt, "dP%s/dt Starting %s"%(Ch, P[0]), "t(hr)", "dP/dt(mbar/hr)")
    # Ch = 2
    # T_unit = 'C'
    # T = b.temperature(2, T_unit)
    # curve(T[1], T[2], "T%s Starting %s"%(Ch, T[0]), "t(hr)", "T(%s)"%T_unit)
    # t, dTdt = derivative(T[1], T[2], 3)
    # curve(t, dTdt, "dT%s/dt Starting %s"%(Ch, T[0]), "t(hr)", "dT/dt(%s/hr)"%T_unit)    
    b.initiate()
    v, s = valve(b.tell), scroll(b.tell)
    print(v.status(17))
    print("P2: %s"%b.gauge(2))
    print(s.status(2))
    # print("ON Scroll2: %s"%s.on(2).upper())
    if int(input("TURN OFF SCROLL2(0/1)? ")):
        print("OFF Scroll2: %s"%s.off(2).upper())
    b.close()

test()

