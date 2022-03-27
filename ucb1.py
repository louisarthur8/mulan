# -*- coding: utf-8 -*-


#03/05 MODIFIER DES FREQ&BW AUX SPECIFICTIONS EUR
#03/05 ALLOCARTION DE SF INITIALE AVEC LA METHODE DE LORAFREE
#03/05 UTILISER LA METHODE DE CALCUL DE POWERCOLLISION DANS LORAFREE

from datetime import datetime
import simpy
import random
import numpy as np
import math
import sys
import re
import matplotlib.pyplot as plt
import os
import operator
import scipy
import scipy.stats
import sqlite3
from static import static
import csv
from LoRaChannel import LoRaChannel
import json

def sql_pow(x,y):
    return x**y


def sql_sqrt(x):
    return np.sqrt(x)
try:
    # sqliteConnection = sqlite3.connect('STEPS_greedy.db')
    # create_table_sql = """ CREATE TABLE IF NOT EXISTS NodesPos (
    #                                     x float,
    #                                     y float,
    #                                     weight text
    #                                 ); """
    # sqliteConnection = sqlite3.connect('STEPS_greedy.db')
    # c = sqliteConnection.cursor()
    # c.execute(create_table_sql)
    # create_r_tree = """ CREATE VIRTUAL TABLE IF NOT EXISTS nodes_tree USING rtree (
    #                                  id PRIMARY KEY,
    #                                  minX ,maxX,
    #                                  minY, maxY,
    #                                  );
    #                                  """
    # c.execute(create_r_tree)
    sqliteConnection = sqlite3.connect('STEPS_greedy.db')
    create_table_sql = """ CREATE TABLE IF NOT EXISTS NodesPos (
                                        x float,
                                        y float,
                                        weight text
                                    ); """
    sqliteConnection = sqlite3.connect('STEPS_greedy.db')
    c = sqliteConnection.cursor()
    c.execute(create_table_sql)
except sqlite3.Error as error:
    print(("Error when connecting to sqlite3",error))
sqliteConnection.create_function("pow",2,sql_pow)
sqliteConnection.create_function("sqrt",1,sql_sqrt)


with open('LoRaEnv.json', 'r') as f:
    dict_loaded = json.load(fp=f)

sf7 = np.array(dict_loaded['sensi']['sensi_sf7']) if dict_loaded['sensi']['sensi_sf7'] is not None and len(dict_loaded['sensi']['sensi_sf7'])==4 else np.array([7,-123,-120,-117.0])
sf8 = np.array(dict_loaded['sensi']['sensi_sf8']) if dict_loaded['sensi']['sensi_sf8'] is not None and len(dict_loaded['sensi']['sensi_sf8'])==4 else np.array([8,-126,-123,-120.0])
sf9 = np.array(dict_loaded['sensi']['sensi_sf9']) if dict_loaded['sensi']['sensi_sf9'] is not None and len(dict_loaded['sensi']['sensi_sf9'])==4 else np.array([9,-129,-126,-123.0])
sf10 = np.array(dict_loaded['sensi']['sensi_sf10']) if dict_loaded['sensi']['sensi_sf10'] is not None and len(dict_loaded['sensi']['sensi_sf10'])==4 else np.array([10,-132,-129,-126.0])
sf11 = np.array(dict_loaded['sensi']['sensi_sf11']) if dict_loaded['sensi']['sensi_sf11'] is not None and len(dict_loaded['sensi']['sensi_sf11'])==4 else np.array([11,-134.53,-131.52,-128.51])
sf12 = np.array(dict_loaded['sensi']['sensi_sf12']) if dict_loaded['sensi']['sensi_sf12'] is not None and len(dict_loaded['sensi']['sensi_sf12'])==4 else np.array([12,-137,-134,-131.0])

sensi = np.array([sf7,sf8,sf9,sf10,sf11,sf12])

IS7 = np.array(dict_loaded['IsoThres']['IS7']) if dict_loaded['IsoThres']['IS7'] is not None and len(dict_loaded['IsoThres']['IS7'])==6 else np.array([1,-8,-9,-9,-9,-9])
IS8 = np.array(dict_loaded['IsoThres']['IS8']) if dict_loaded['IsoThres']['IS8'] is not None and len(dict_loaded['IsoThres']['IS8'])==6 else np.array([-11,1,-11,-12,-13,-13])
IS9 = np.array(dict_loaded['IsoThres']['IS9']) if dict_loaded['IsoThres']['IS9'] is not None and len(dict_loaded['IsoThres']['IS9'])==6 else np.array([-15,-13,1,-13,-14,-15])
IS10 = np.array(dict_loaded['IsoThres']['IS10']) if dict_loaded['IsoThres']['IS10'] is not None and len(dict_loaded['IsoThres']['IS10'])==6 else np.array([-19,-18,-17,1,-17,-18])
IS11 = np.array(dict_loaded['IsoThres']['IS11']) if dict_loaded['IsoThres']['IS11'] is not None and len(dict_loaded['IsoThres']['IS11'])==6 else np.array([-22,-22,-21,-20,1,-20])
IS12 = np.array(dict_loaded['IsoThres']['IS12']) if dict_loaded['IsoThres']['IS12'] is not None and len(dict_loaded['IsoThres']['IS12'])==6 else np.array([-25,-25,-25,-24,-23,1])
IsoThresholds = np.array([IS7,IS8,IS9,IS10,IS11,IS12])

# compute energy
# Transmit consumption in mA from -2 to +17 dBm
TX = dict_loaded['energy']['TX'] if dict_loaded['energy']['TX'] is not None and len(dict_loaded['energy']['TX'])==23 else [22, 22, 22, 23,24, 24, 24, 25, 25, 25, 25, 26, 31, 32, 34, 35, 44,82, 85, 90,105, 115, 125]
RX = dict_loaded['energy']['RX'] if dict_loaded['energy']['RX'] > 0 else 16
V = dict_loaded['energy']['V'] if dict_loaded['energy']['V'] > 0 else 3.0     # voltage XXX

freq_list = []
channel_list = []
try:
    for channel in dict_loaded['channels']['first_window']:
        freq_list.append(channel['freq'])
        channel_list.append(LoRaChannel(channel['freq'],channel['duty_cycle']))
except: 
    freq_list = [868100000, 868300000, 868500000]
    channel_list = []
    for freq in freq_list:
        channel_list.append(LoRaChannel(freq,0.01))

try:
    second_channel = LoRaChannel(dict_loaded['channels']['second_window']['freq'],dict_loaded['channels']['second_window']['duty_cycle'])
except:
    second_channel = LoRaChannel(868700000,0.1)
    
Ptx = dict_loaded['pathlossModel']['Ptx'] if dict_loaded['pathlossModel']['Ptx']>0 else 14
gamma = dict_loaded['pathlossModel']['gamma'] if dict_loaded['pathlossModel']['gamma']>0 else 2.32
d0 = dict_loaded['pathlossModel']['d0'] if dict_loaded['pathlossModel']['d0']>0 else 1000.0
var = dict_loaded['pathlossModel']['var'] if dict_loaded['pathlossModel']['var']>0 else 7.8
Lpld0 = dict_loaded['pathlossModel']['Lpld0'] if dict_loaded['pathlossModel']['Lpld0']>0 else 128.95
GL = dict_loaded['pathlossModel']['GL'] if dict_loaded['pathlossModel']['GL']>0 else 0

#parameters physiques
Bandwidth = 125
CodingRate = 1
LorawanHeader = 1

AckMessLen = 0
minsensi = np.amin(sensi[:,[125,250,500].index(Bandwidth) + 1])
Lpl = Ptx - minsensi

record = 0  # enregistreement ou non de l'expérience
nbrrec = 10  # nombre d'expérience récupèrées
intervalle = 100 # donne l'intervalle (+/-) pour la récupération de données

epsilon = None # proba to not pick the best
alpha = None # learning rate

#parameters a modifier
is_update_db = False
is_using_db = False
maxDist = d0*(10**((Lpl-Lpld0)/(10.0*gamma)))
# maxDist = 3000

from scipy.stats import norm
def ber_reynders(eb_no, sf):
    """Given the energy per bit to noise ratio (in db), compute the bit error for the SF"""
    return norm.sf(math.log(sf, 12)/math.sqrt(2)*eb_no)

def ber_reynders_snr(snr, sf, bw, cr):
    """Compute the bit error given the SNR (db) and SF"""
    Temp = [4.0/5,4.0/6,4.0/7,4.0/8]
    CR = Temp[cr-1]
    BW = bw*1000.0
    eb_no =  snr - 10*math.log10(BW/2**sf) - 10*math.log10(sf) - 10*math.log10(CR) + 10*math.log10(BW)
    return ber_reynders(eb_no, sf)

def per(sf,bw,cr,rssi,pl):
    snr = rssi  +174 - 10*math.log10(bw) - 6
    return 1 - (1 - ber_reynders_snr(snr, sf, bw, cr))**(pl*8)


#sent,nrCollisions nrReceived, nrProcessed, nrLost, nrNoACK
def checkACK(packet):
    global  channel_list
    global  second_channel
    # check ack in the first window
    chanlindex=freq_list.index(packet.freq)
    timeofacking = env.now + 1000  # one sec after receiving the packet
    packet.acklost = 0
    if (timeofacking >= channel_list[chanlindex].transmission_time):
        # this packet can be acked
        packet.acked = 1
        tempairtime = airtime(packet.downlink_sf, CodingRate, AckMessLen+LorawanHeader, Bandwidth)
        channel_list[chanlindex].transmission_time = timeofacking+(tempairtime/channel_list[chanlindex].duty_cycle)
        nodes[packet.nodeid].rxtime += tempairtime
        if (14 - Lpld0 - 10*gamma*math.log10(nodes[packet.nodeid].dist/d0) + np.random.normal(0, var)) < sensi[packet.downlink_sf-7, [125,250,500].index(packet.bw) + 1]:
            packet.acklost = 1
            packet.acked = 0
        return packet.acked,packet.acklost    
    else:
        # this packet can not be acked
        packet.acked = 0
        Tsym = (2**packet.downlink_sf)/(Bandwidth) # sec
        Tpream = (8 + 4.25)*Tsym
        nodes[packet.nodeid].rxtime += Tpream

    # chcek ack in the second window
    timeofacking = env.now + 2000  # two secs after receiving the packet
    if (timeofacking >= second_channel.transmission_time):
        # this packet can be acked
        packet.acked = 2
        tempairtime = airtime(12, CodingRate, AckMessLen+LorawanHeader, Bandwidth)
        second_channel.transmission_time = timeofacking+(tempairtime/second_channel.duty_cycle)
        nodes[packet.nodeid].rxtime += tempairtime
        if (14 - Lpld0 - 10*gamma*math.log10(nodes[packet.nodeid].dist/d0) + np.random.normal(0, var)) < sensi[12-7, [125,250,500].index(packet.bw) + 1]:
            packet.acklost = 1
            packet.acked = 0
        return packet.acked,packet.acklost
    else:
        # this packet can not be acked
        packet.acked = 0
        Tsym = (2.0**12)/(Bandwidth) # sec
        Tpream = (8 + 4.25)*Tsym
        nodes[packet.nodeid].rxtime += Tpream
        return packet.acked,packet.acklost
# freq_col = 1, sf_col = 2, time_col = 4
# check for collisions at base station
# Note: called before a packet (or rather node) is inserted into the list
def checkcollision(packet):
    col = 0 # flag needed since there might be several collisions for packet
    processing = 0
    for i in range(0,len(packetsAtBS)):
        if packetsAtBS[i].packet.processed == 1:
            processing = processing + 1
    if (processing > maxBSReceives):
        packet.processed = 0
    else:
        packet.processed = 1

    if packetsAtBS:
        for other in packetsAtBS:
            if other.nodeid != packet.nodeid:
               # simple collision
               freq_collision = frequencyCollision(packet, other.packet)
               sf_collision = sfCollision(packet, other.packet,)
               if(freq_collision and sf_collision):
                   if full_collision:
                       if timingCollision(packet, other.packet,):
                           # check who collides in the power domain
                            c = powerCollision(packet, other.packet)
                            # c = powerCollision_2(packet, other.packet)
                            for p in c:
                               p.collided = 1
                               if p == packet:
                                   col = 1
                       else:
                           # no timing collision, all fine
                           pass
                   else:
                       packet.collided = 1
                       other.packet.collided = 1  # other also got lost, if it wasn't lost already
                       col = 1
        return col
    return 0

#
# frequencyCollision, conditions
#
#        |f1-f2| <= 120 kHz if f1 or f2 has bw 500
#        |f1-f2| <= 60 kHz if f1 or f2 has bw 250
#        |f1-f2| <= 30 kHz if f1 or f2 has bw 125
def frequencyCollision(p1,p2):
    if (abs(p1.freq-p2.freq)<=120 and (p1.bw==500 or p2.bw==500)):
        # print "frequency coll 500"
        return True
    elif (abs(p1.freq-p2.freq)<=60 and (p1.bw==250 or p2.bw==250)):
        # print "frequency coll 250"
        return True
    else:
        if (abs(p1.freq-p2.freq)<=30):
            # print "frequency coll 125"
            return True
        #else:
    # print "no frequency coll"
    return False

def sfCollision(p1, p2):
    if p1.sf == p2.sf:
        # print "collision sf node {} and node {}".format(p1.nodeid, p2.nodeid)
        # p2 may have been lost too, will be marked by other checks
        return True
    return False

# check only the capture between the same spreading factor
def powerCollision(p1, p2):
    powerThreshold = 6 # dB
    ##print "pwr: node {0.nodeid} {0.rssi:3.2f} dBm node {1.nodeid} {1.rssi:3.2f} dBm; diff {2:3.2f} dBm".format(p1, p2, round(p1.rssi - p2.rssi,2))
    if abs(p1.rssi - p2.rssi) < powerThreshold:
        ##print "collision pwr both node {} and node {}".format(p1.nodeid, p2.nodeid)
        # packets are too close to each other, both collide
        # return both packets as casualties
        return (p1, p2)
    elif p1.rssi - p2.rssi < powerThreshold:
        # p2 overpowered p1, return p1 as casualty
        ##print "collision pwr node {} overpowered node {}".format(p2.nodeid, p1.nodeid)
        return (p1,)
    ##print "p1 wins, p2 lost"
    # p2 was the weaker packet, return it as a casualty
    return (p2,)

def powerCollision_2(p1, p2):
    #powerThreshold = 6
    if p1.sf == p2.sf:
       if abs(p1.rssi - p2.rssi) < IsoThresholds[p1.sf-7][p2.sf-7]:
           return (p1, p2)
       elif p1.rssi - p2.rssi < IsoThresholds[p1.sf-7][p2.sf-7]:
           return (p1,)
       return (p2,)
    else:
       if p1.rssi-p2.rssi > IsoThresholds[p1.sf-7][p2.sf-7]:
          if p2.rssi-p1.rssi > IsoThresholds[p2.sf-7][p1.sf-7]:
              return ()
          else:
              return (p2,)
       else:
           if p2.rssi-p1.rssi > IsoThresholds[p2.sf-7][p1.sf-7]:
               return (p1,)
           else:
               return (p1,p2)


def timingCollision(p1, p2):
    # assuming p1 is the freshly arrived packet and this is the last check
    # we've already determined that p1 is a weak packet, so the only
    # way we can win is by being late enough (only the first n - 5 preamble symbols overlap)
    # assuming 8 preamble symbols
    Npream = 8

    # we can lose at most (Npream - 5) * Tsym of our preamble
    Tpreamb = 2**p1.sf/(1.0*p1.bw) * (Npream - 5)

    # check whether p2 ends in p1's critical section
    p2_end = p2.addTime + p2.rectime
    p1_cs = env.now + Tpreamb
    if p1_cs < p2_end:
        # p1 collided with p2 and lost
        # print "not late enough"
        return True
    # print "saved by the preamble"
    return False

# this function computes the airtime of a packet
# according to LoraDesignGuide_STD.pdf
#
def airtime(sf,cr,pl,bw):
    H = 0        # implicit header disabled (H=0) or not (H=1)
    DE = 0       # low data rate optimization enabled (=1) or not (=0)
    Npream = 8   # number of preamble symbol (12.25  from Utz paper)

    if bw == 125 and sf in [11, 12]:
        # low data rate optimization mandated for BW125 with SF11 and SF12
        DE = 1
    if sf == 6:
        # can only have implicit header with SF6
        H = 1

    Tsym = (2.0**sf)/bw
    Tpream = (Npream + 4.25)*Tsym
    # print "sf", sf, " cr", cr, "pl", pl, "bw", bw
    payloadSymbNB = 8 + max(math.ceil((8.0*pl-4.0*sf+28+16-20*H)/(4.0*(sf-2*DE)))*(cr+4),0)
    Tpayload = payloadSymbNB * Tsym
    return (Tpream + Tpayload)

def soft_max(list_sfs):
    z_exp = [math.exp(i) for i in list_sfs]
    sum_exp = sum(z_exp)
    result = [i / sum_exp for i in z_exp]
    return result

def simple_norm(list_sfs):
    sum_exp = sum(list_sfs)
    if(sum_exp==0):
        print('error')
    result = [i / sum_exp for i in list_sfs]
    return result

def minsf_cut(SFs,minsf,alpha):
    if checkScore(SFs):
        for i in range(minsf-7):
            SFs[i] = 0
    else:
        for i in range(minsf,13):
            SFs[i-7] = math.exp(-alpha*abs(minsf-i))
    SFs = simple_norm(SFs)  
    return SFs

def minsf_generate(Prx,bw,thres = 0.75):
    possibility_of_sf = [0]*6
    for i in range(0,6):  # SFs
        sensi_sf = sensi[i, [125,250,500].index(bw) + 1]
        z = sensi_sf - Prx    
        possibility_of_sf[i] = 1 - 0.5*(1+math.erf(z/(var*math.sqrt(2))))
    result_sf = 12
    for i in range(5,-1,-1):
        if possibility_of_sf[i] > thres:
             result_sf = i+7
    possibility_of_sf = minsf_cut([0]*6,result_sf,2)
    return result_sf,possibility_of_sf

def get_non_zero_min(SFs):
    min_val = 999
    min_index = -1
    for i in range(len(SFs)):
        if(SFs[i] < min_val and SFs[i] > 0):
            min_val = SFs[i]
            min_index = i
    return min_index
    
def random_pick_sf(estimateval,minsf):
    global epsilon
    x = random.uniform(0,1)
    if (x > epsilon):
        return np.argmax(estimateval) + 7
    else :
        return random.choice([n for n in range (minsf,13)])
#
# this function creates a node
#
class myNode():
    def __init__(self, nodeid, bs, period,packetlen,max_dist,random_place = True):
        self.nodeid = nodeid
        self.period = period
        self.bs = bs
        self.buffer = 0
        self.first = 1
        self.period = period
        self.lstretans = 0
        self.losterror = 0
        self.rxtime = 0
        self.x = 0
        self.y = 0
        self.SFs = [0]*6
        self.avg_rew  = [0]*6
        self.turn = 1
        self.algoCounts = [1]*6
        self.all_rewards = [0]*6
        # print('node %d' %nodeid, "x", self.x, "y", self.y, "dist: ", self.dist)
        self.set_position(max_dist,random_place=random_place)
        # c.execute("Select sqrt(pow(x-?,2)+pow(y-?,2)) AS closest, weight FROM NodesPos,nodes_tree WHERE NodesPos.rowid = id AND minX >= ? AND maxX <= ? AND minY >= ? AND maxY <= ? ORDER BY closest LIMIT ?",\
        #                 (self.x,self.y,self.x-intervalle,self.x+intervalle,self.y-intervalle,self.y+intervalle,nbrrec))
        c.execute("Select sqrt(pow(x-?,2)+pow(y-?,2)) AS closest, weight FROM NodesPos ORDER BY closest LIMIT 20",(self.x,self.y))
        result = c.fetchall()
        nbrdata = len(result)
        if (nbrdata != 0):
            self.SFs = [0]*6
            for j in range(nbrdata):
                for i in range(6):
                    self.SFs[i] += float(result[j][1].split(',')[i])
            self.SFs = [i/nbrdata for i in self.SFs ]
        self.packet = myPacket(self.nodeid, packetlen)
        possibility_of_sf = self.packet.calcul_minsf(self.dist)
        self.minsf = self.packet.sf
        # if not checkScore(self.SFs):
        #     self.SFs = possibility_of_sf
        # else:
        #     for i in range(self.packet.sf-7):
        #         SFs[i] = 0
        if not checkScore(self.SFs):
            for n in range (0,6):
                if (n < (self.minsf-7)):
                    self.SFs[n] = 0
                elif (n == (self.minsf-7) or n == (self.minsf-6)):
                    self.SFs[n] = 0.5
                else :
                    self.SFs[n] = 0.01
        else:
            for i in range(self.minsf-7):
                self.SFs[i] = 0
        self.static = static(self.x-bsx,self.y-bsy,is_dynamic=True) 
    def set_position(self,maxDist,random_place):
        # this is very complex prodecure for placing nodes
        # and ensure minimum distance between each pair of nodes
        found = 0
        rounds = 0
        global nodes
        while (found == 0 and rounds < 100):
            a = random.random()
            b = random.random()
            # if b<a:
            #     a,b = b,a
            if random_place:
                posx = (1-a)*maxDist*math.cos(2*math.pi*b)+bsx
                posy = (1-a)*maxDist*math.sin(2*math.pi*b)+bsy
            else:
                posx = maxDist*math.cos(2*math.pi*b)+bsx
                posy = maxDist*math.sin(2*math.pi*b)+bsy
            if len(nodes) > 0:
                for index, n in enumerate(nodes):
                    dist = np.sqrt(((abs(n.x-posx))**2)+((abs(n.y-posy))**2))
                    if dist >= 10:
                        found = 1
                        self.x = posx
                        self.y = posy
                    else:
                        rounds = rounds + 1
                        if rounds == 100:
                            # print "could not place new node, giving up"
                            exit(-1)
            else:
                # print "first node"
                self.x = posx
                self.y = posy
                found = 1
        self.dist = np.sqrt((self.x-bsx)*(self.x-bsx)+(self.y-bsy)*(self.y-bsy))
        
        
#
# this function creates a packet (associated with a node)
# it also sets all parameters, currently random
#

def checkScore(SFs):
    for n in SFs:
        if n != 0:
            return True
    return False

class myPacket():
    def __init__(self, nodeid, plen):
        self.sf = 12
        self.downlink_sf = self.sf
        self.nodeid = nodeid
        self.txpow = Ptx
        self.cr = CodingRate
        self.bw = Bandwidth       
        self.pl = plen
        self.symTime = (2.0**self.sf)/self.bw
        self.arriveTime = 0
        self.rssi = 0
        # frequencies: lower bound + number of 61 Hz steps
        channel = random.choice(channel_list)
        self.freq = channel.freq
        self.duty_cycle = channel.duty_cycle
        
        self.rectime = 0
        # denote if packet is collided
        self.collided = 0
        self.processed = 0
        self.lost = False
        self.perror = False
        self.acked = 0
        self.acklost = 0
    def calcul_minsf(self,distance):
        global Ptx
        global gamma
        global d0
        global var
        global Lpld0
        global GL
        Prx = self.txpow  #  zero path loss by default
        # log-shadow
        Lpl = Lpld0 + 10*gamma*math.log10(distance/d0)
        Prx = self.txpow - GL - Lpl
        if var == 0:
            for i in range(0,6):  # SFs
                if ((sensi[i, [125,250,500].index(self.bw) + 1]) < Prx):
                    at = airtime(i+7, self.cr, self.pl, self.bw)
                    if at < minairtime:
                        minairtime = at
                        minsf = i+7
                        minsensi = sensi[i, [125,250,500].index(self.bw) + 1]
            if (minsf != 0):
                self.rectime = minairtime
                self.sf = minsf
        else:
            result_sf,possibility_of_sf = minsf_generate(Prx,self.bw)
            self.sf = result_sf
        # self.sf = 10
        self.downlink_sf = self.sf
        self.rectime = airtime(self.sf,self.cr,self.pl,self.bw)
        return possibility_of_sf
    
def update(SFs,avg_rew,now_sf,turn,algoCounts):
    SFs[now_sf-7] = avg_rew[now_sf-7] + math.sqrt( (2.0 * math.log(turn) / algoCounts[now_sf-7]) )
    return SFs
#
# main discrete event loop, runs for each node
# a global list of packet being processed at the gateway
# is maintained
#
def transmit(env,node):
    lastsf = 0
    last_airtime = 0
    is_acked = -1
    while True: 
        node.packet.rssi = node.packet.txpow - Lpld0 - 10*gamma*math.log10(node.dist/d0) + np.random.normal(0, var)      
        if (node.lstretans and node.lstretans <= 8):
            Tsym = (2.0**12)/(Bandwidth) # sec
            Tpream = (8 + 4.25)*Tsym
            # node.buffer += PcktLength_SF[node.packet.sf-7]
            # the randomization part (2 secs) to resove the collisions among retrasmissions
            yield env.timeout(max(2000+Tpream, float(last_airtime*((1-node.packet.duty_cycle)/node.packet.duty_cycle)))+(random.expovariate(1.0/float(2000))))
            node.static.retransmissions += 1
        else:
            node.lstretans = 0
            if is_acked == 1:
                dl_time = 1000+airtime(node.packet.downlink_sf, CodingRate, AckMessLen+LorawanHeader, Bandwidth)
            elif is_acked == 2:
                dl_time = 2000+airtime(12, CodingRate, AckMessLen+LorawanHeader, Bandwidth)
            elif is_acked == 0:
                Tsym = (2.0**12)/(Bandwidth) # sec
                Tpream = (8 + 4.25)*Tsym
                dl_time = 2000+Tpream
            else:
                dl_time = 0
            yield env.timeout(max(dl_time+random.expovariate(1.0/float(node.period)),float(last_airtime*((1-node.packet.duty_cycle)/node.packet.duty_cycle))))
            node.buffer += node.packet.pl
            node.static.new_packet += 1              
        node.buffer -= node.packet.pl
        node.static.total_send += 1
        if (node in packetsAtBS):
            print("ERROR: packet already in")
            global nrAtBS
            nrAtBS = nrAtBS + 1
        else:
            sensitivity = sensi[node.packet.sf - 7, [125,250,500].index(node.packet.bw) + 1]
            if node.packet.rssi < sensitivity:
                # print "node {}: packet will be lost".format(node.nodeid)
                node.packet.lost = True
            else:
                node.packet.lost = False
                if (per(node.packet.sf,node.packet.bw,node.packet.cr,node.packet.rssi,node.packet.pl) < random.uniform(0,1)):
                    # OK CRC
                    node.packet.perror = False
                else:
                    # Bad CRC
                    node.packet.perror = True
                    global nrProcessesError
                    nrProcessesError = nrProcessesError + 1
            # adding packet if no collision
                if (checkcollision(node.packet)==1):
                    node.packet.collided = 1
                else:
                    node.packet.collided = 0
                    packetsAtBS.append(node)
                    node.packet.addTime = env.now
        node.packet.rectime = airtime(node.packet.sf,node.packet.cr,node.packet.pl,node.packet.bw)
        node.static.energy += node.packet.rectime * TX[int(node.packet.txpow)+2] * V
        yield env.timeout(node.packet.rectime)
        if (node.packet.lost == False\
                and node.packet.perror == False\
                and node.packet.collided == False):
            node.packet.acked, node.packet.acklost  = checkACK(node.packet)

        if node.packet.processed == 1:
            global nrProcessed
            nrProcessed = nrProcessed + 1
        is_acked = 0
        if node.packet.lost:
            node.buffer += node.packet.pl
            node.static.lost += 1
            node.lstretans += 1
            global nrLost
            nrLost += 1 
        elif node.packet.perror:
            global nrLostError
            nrLostError += 1
        elif node.packet.collided == 1:
            node.buffer += node.packet.pl
            node.static.collisions += 1
            node.lstretans += 1
            global nrCollisions
            nrCollisions = nrCollisions +1
        elif node.packet.acked == 0:
            node.buffer += node.packet.pl
            node.lstretans += 1
            global nrNoACK
            nrNoACK += 1
        elif node.packet.acklost == 1:
            node.buffer += node.packet.pl
            node.lstretans += 1
            global nrACKLost
            nrACKLost += 1
        else:
            node.lstretans = 0
            global nrACKed
            nrACKed = nrACKed + 1
            node.static.acked += 1
            is_acked = node.packet.acked
        if node.packet.lost == False and node.packet.collided == 0:
            global nrReceived
            nrReceived = nrReceived + 1
            node.static.received += 1
        punish_on = False
        
        node.all_rewards[node.packet.sf-7] = node.all_rewards[node.packet.sf-7] + is_acked
        node.algoCounts[node.packet.sf-7] = node.algoCounts[node.packet.sf-7] + 1
        node.avg_rew[node.packet.sf-7] = node.all_rewards[node.packet.sf-7] / node.algoCounts[node.packet.sf-7]
        node.SFs = update(node.SFs,node.avg_rew,node.packet.sf,node.turn,node.algoCounts)
        node.packet.sf = random_pick_sf(node.SFs,node.minsf)

        if (node in packetsAtBS):
            packetsAtBS.remove(node)
            # reset the packet
        node.packet.collided = 0
        node.packet.processed = 0
        node.packet.lost = False
        node.packet.acked = 0
        node.packet.acklost = 0
        last_airtime = node.packet.rectime
        node.packet.rectime = airtime(node.packet.sf,node.packet.cr,node.packet.pl,node.packet.bw)

#
# "main" program
#
# Nouveaux tableaux
SFdistribution = [0 for x in range(0,6)]
BWdistribution = [0 for x in range(0,3)]
CRdistribution = [0 for x in range(0,4)]
TXdistribution = [0 for x in range(0,13)]
# global stuff
#Rnd = random.seed(12345)
nodes = []
packetsAtBS = []
env = None
# maximum number of packets the BS can receive at the same time
maxBSReceives = 8

# max distance: 300m in city, 3000 m outside (5 km Utz experiment)
# also more unit-disc like according to Utz
bsId = 1
nrCollisions = 0
nrReceived = 0
nrProcessed = 0
nrLost = 0
nrAtBS = 0
nrLostError = 0 #nrLostError, nrACKLost
nrNoACK = 0
nrACKLost = 0
nrACKed = 0
nrProcessesError = 0

# base station placement
bsx = maxDist+10
bsy = maxDist+10
full_collision = 99
simdate = str(datetime.now()).split('.')[0].replace('-','').replace(':','').replace(' ','')
filepath  = './data/ucb1_'+simdate

def initalize_env():
    global env
    global c
    global nodes
    global full_collision
    global channel_list
    global second_channel
    global SFdistribution
    global BWdistribution
    global CRdistribution
    global TXdistribution
    global packetsAtBS
    global maxBSReceives
    global bsId
    global nrCollisions
    global nrReceived
    global nrProcessed
    global nrLost
    global nrAtBS
    global nrLostError
    global nrNoACK
    global nrACKLost
    global nrACKed
    global nrProcessesError
    global bsx
    global bsy
    global alpha
    global epsilon
    global maxDist

    SFdistribution = [0 for x in range(0,6)]
    BWdistribution = [0 for x in range(0,3)]
    CRdistribution = [0 for x in range(0,4)]
    TXdistribution = [0 for x in range(0,13)]
    # global stuff
    #Rnd = random.seed(12345)
    nodes = []
    packetsAtBS = []
    env = None
    # maximum number of packets the BS can receive at the same time
    maxBSReceives = 8

    # max distance: 300m in city, 3000 m outside (5 km Utz experiment)
    # also more unit-disc like according to Utz
    bsId = 1
    nrCollisions = 0
    nrReceived = 0
    nrProcessed = 0
    nrLost = 0
    nrAtBS = 0
    nrLostError = 0 #nrLostError, nrACKLost
    nrNoACK = 0
    nrACKLost = 0
    nrACKed = 0
    nrProcessesError = 0
    # base station placement
    bsx = maxDist+10
    bsy = maxDist+10
    full_collision = 99
    second_channel.transmission_time = 0
    alpha = None
    epsilon = None
    for channel in channel_list:
        channel.transmission_time = 0
        
def monitor(env,results_array,simtime):
    while True:       
        sent = sum(n.static.total_send for n in nodes)
        diff_packet = sum(n.static.new_packet for n in nodes)
        resend_packet = sum(n.static.retransmissions for n in nodes)
        rest_packet = sum(n.buffer/n.packet.pl for n in nodes)
        eff_send = float(diff_packet)/float(sent) if sent != 0 else 0
        recv_energy = 0
        for node in nodes:
            recv_energy += node.rxtime * RX * V/1e6
        energy = sum(node.static.energy for node in nodes)/1e6+recv_energy
        der2 = (nrReceived)/float(sent) if sent!=0 else 0
        der3 = (nrACKed)/float(diff_packet) if diff_packet!=0 else 0
        energy_per_100ack = energy/nrACKed*100 if nrACKed!=0 else 0
        energy_per_100newpacket = energy/diff_packet*100 if diff_packet!=0 else 0
        new_line = [env.now,sent,diff_packet,resend_packet,rest_packet,nrCollisions,nrLost,der2,der3,nrACKed,energy,energy_per_100ack,eff_send,energy_per_100newpacket]
        results_array.append(new_line)
        yield env.timeout((simtime/100)) 
                
def run(nrNodes,avgSendTime,simtime,plsize,db_size,fullcollision = 1,is_update_db = False,max_dist = maxDist,regular_placement=0,sim_times=1,epsi = 0.1,alp = 0.1):
    global env
    global full_collision
    global SFdistribution
    global BWdistribution
    global CRdistribution
    global TXdistribution
    global alpha
    global epsilon
    global maxDist
    maxDist = max_dist
    initalize_env()
    epsilon = epsi
    alpha = alp
    print("maxDist:", maxDist)
    env = simpy.Environment()
    results_array = []
    full_collision = fullcollision
    if regular_placement ==0:
        for i in range(0,nrNodes):
            # myNode takes period (in ms), base station id packetlen (in Bytes)
            node = myNode(i,bsId, avgSendTime,plsize+LorawanHeader,maxDist)
            nodes.append(node)
            env.process(transmit(env,node))
    else:
        dist = 0
        for i in range(regular_placement):
            dist += maxDist/regular_placement
            for j in range(int(nrNodes/regular_placement)):
                node = myNode(len(nodes),bsId, avgSendTime,plsize+LorawanHeader,dist,random_place=False)
                nodes.append(node)
                env.process(transmit(env,node))        
        for i in range(regular_placement):
            if len(nodes)<nrNodes:
                node = myNode(len(nodes),bsId, avgSendTime,plsize+LorawanHeader,dist,random_place=False)
                nodes.append(node)
                env.process(transmit(env,node))
                dist -= maxDist/regular_placement
            else:
                break
            
    for n in nodes:
        n.static.init_sf = n.packet.sf
        SFdistribution[n.packet.sf-7]+=1
        CRdistribution[n.packet.cr-1]+=1
        TXdistribution[int(n.packet.txpow)-2]+=1
        if n.packet.bw==125:
            BWdistribution[0]+=1
        elif n.packet.bw==250:
            BWdistribution[1]+=1
        else:
            BWdistribution[2]+=1
    print("starting distribution")
    print("SFdistribution: ", SFdistribution)
    print("BWdistribution: ", BWdistribution)
    print("CRdistribution: ", CRdistribution)
    print("TXdistribution: ", TXdistribution)
    SFdistribution = [0 for x in range(0,6)]
    BWdistribution = [0 for x in range(0,3)]
    CRdistribution = [0 for x in range(0,4)]
    TXdistribution = [0 for x in range(0,13)]
    # start simulation
    env.process(monitor(env,results_array,simtime))    
    env.run(until=simtime)

    # print stats and save into file
    #print "nrCollisions ", nrCollisions


    sent = sum(n.static.total_send for n in nodes)
    diff_packet = sum(n.static.new_packet for n in nodes)
    resend_packet = sum(n.static.retransmissions for n in nodes)
    rest_packet = sum(n.buffer/n.packet.pl for n in nodes)
    for node in nodes:
        node.static.energy += node.rxtime * RX * V
        node.static.energy /= 1e6
    energy = sum(node.static.energy for node in nodes)

    print("energy (in J): ", energy)
    print("\n")
    print("****************************************")
    print("actual packets: ", diff_packet)
    print("resend packets: ", resend_packet)
    print("sent packets: ", sent)
    print("non sent packets: ", rest_packet)
    print("collisions: ", nrCollisions)
    print("received packets: ", nrReceived)
    print("received and acked packets: ", nrACKed)
    print("processed packets: ", nrProcessed)
    print("lost packets: ", nrLost)
    print("Bad CRC: ", nrLostError)
    print("NoACK packets: ", nrNoACK)
    print("ACKLost packets:", nrACKLost)
    # data extraction rate
    der1 = (sent-nrCollisions)/float(sent) if sent!=0 else 0
    print("DER:", der1)
    der2 = (nrReceived)/float(sent) if sent!=0 else 0
    print("DER method 2:", der2)
    der3 = (nrACKed)/float(diff_packet) if diff_packet!=0 else 0
    print("DER method 3:", der3)
    print("****************************************")
    print("\n")


    print("============end distribution================")
    for n in nodes:
        n.static.final_sf = n.packet.sf
        n.static.sim_end()
        SFdistribution[n.packet.sf-7]+=1
        CRdistribution[n.packet.cr-1]+=1
        TXdistribution[int(n.packet.txpow)-2]+=1
        if n.packet.bw==125:
            BWdistribution[0]+=1
        elif n.packet.bw==250:
            BWdistribution[1]+=1
        else:
            BWdistribution[2]+=1
    print("SFdistribution: ", SFdistribution)
    print("BWdistribution: ", BWdistribution)
    print("CRdistribution: ", CRdistribution)
    print("TXdistribution: ", TXdistribution)
    print("CollectionTime: ", env.now)
    sf_file = filepath+'_'+str(nrNodes)+'_'+str(avgSendTime)+'_'+str(simtime)+'_'+str(db_size)+'_'+str(sim_times)+'times''_sf.csv'
    results_file = filepath+'_'+str(nrNodes)+'_'+str(avgSendTime)+'_'+str(simtime)+'_'+str(db_size)+'_'+str(sim_times)+'times''_results.csv'
    results_file_on_time = filepath+'_'+str(nrNodes)+'_'+str(avgSendTime)+'_'+str(simtime)+'_'+'_'+str(sim_times)+'times''_on_time.csv'    
    with open(sf_file, 'w',newline='') as file:
        writer = csv.writer(file,delimiter=',')
        for n in nodes:
            if n.static.is_dynamic:
                sf_line = [n.static.x,n.static.y,n.static.init_sf,n.static.final_sf]
            else:
                sf_line = [n.static.x,n.static.y,n.static.init_sf,n.static.init_sf]
            writer.writerow(sf_line)
    file.close()
    with open(results_file, 'a',newline='') as file:
        writer = csv.writer(file,delimiter=',')
        for n in nodes:
            energy_per_100newpacket = n.static.energy/n.static.new_packet*100 if n.static.new_packet!=0 else 0
            result_line = [n.static.x,n.static.y,n.static.total_send,n.static.new_packet,n.static.retransmissions,n.buffer/n.packet.pl,\
                            n.static.collisions,n.static.lost,n.static.receive_ratio,n.static.ack_ratio,\
                            n.static.acked,n.static.energy,n.static.energy_per100_ack,n.static.effective_send,energy_per_100newpacket]
            writer.writerow(result_line)
    file.close()
        

    if is_update_db:
        for n in nodes:
            string_arr_of_sfs = [str(i) for i in n.SFs]
            str_of_sfs = ",".join(string_arr_of_sfs)
            c.execute("Delete from NodesPos where x = ? and y = ?", (n.x,n.y))
            c.execute("Insert INTO NodesPos Values (?,?,?)",(n.x,n.y,str_of_sfs))
            sqliteConnection.commit()



    energy_per_100ack = energy/nrACKed*100 if nrACKed!=0 else 0
    energy_per_100newpacket = energy/diff_packet*100 if diff_packet!=0 else 0
    new_line = [sent,diff_packet,resend_packet,rest_packet,nrCollisions,nrLost,der2,der3,nrACKed,energy,energy_per_100ack,float(diff_packet)/float(sent),energy_per_100newpacket]
    last_line = [simtime,sent,diff_packet,resend_packet,rest_packet,nrCollisions,nrLost,der2,der3,nrACKed,energy,energy_per_100ack,float(diff_packet)/float(sent),energy_per_100newpacket]
    results_array.append(last_line)
    results_array = np.array(results_array)
    with open(results_file_on_time,'a',newline='') as f:
        w = csv.writer(f,delimiter=',')
        w.writerows(results_array)
    f.close()    
    return sf_file,results_file,results_file_on_time,np.array(new_line).reshape(1,-1)


def sqlclose():
    if (sqliteConnection):
        sqliteConnection.close()
        print("closed")
    else:
        print("already closed")


def prepare_db():
    c.execute("Delete from NodesPos")
    sqliteConnection.commit()