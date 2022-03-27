# import STEPS_individual
# import STEPS_pureQL
# import STEPS_pureQL_prior
# import STEPS_QL_policy
# import STEPS_QL_policy_prior
# import LoRaSim_randomSF
import ucb1

import csv
import numpy as np
import matplotlib.pyplot as plt
from plotter import *

graphic_on = False

multi_run = False

sim_times = 1000
# simulator_name = 'STEPS_QL_policy_prior'
simulator_name = 'ucb1'

nrNodes_list = [50,100,250,500,600,750] #if multi run
nrNodes = 500 # if single run
avgSendTime = 5*60*1000
simtime = 2*60*60*1000
plsize = 20
full_collision = 1
is_update_db = False
db_size = 0
max_Dist = 5000
regular_placement=0

variable_list = ["total sent","new packets","resend tentatives",\
                 "packets abandonned","collisions","lost packets",\
                 "receive ratio(based on total sent)","ack ratio(based on new packets)",\
                 "Acked number","Energy(J)","energy_per_100_ack(J)","effective packets ratio",'energy_per_100_new_packet']
    
if multi_run:
    data_to_write = []
    sim_file = '.\\data\\csv_data\\'+simulator_name+'_'+str(avgSendTime)+'_'+str(simtime)+'_'+str(sim_times)+'times.csv'
    for nrNode in nrNodes_list:
        temp = None
        for i in range(sim_times):
            # sf_file,results_file,results_file_on_time,result = STEPS_pureQL.run(nrNodes,avgSendTime,simtime,plsize,db_size,max_dist=max_Dist,regular_placement=regular_placement,sim_times=sim_times)
            # sf_file,results_file,results_file_on_time,result = STEPS_pureQL_prior.run(nrNodes,avgSendTime,simtime,plsize,db_size,max_dist=max_Dist,regular_placement=regular_placement,sim_times=sim_times)
            # sf_file,results_file,results_file_on_time,result = STEPS_QL_policy.run(nrNodes,avgSendTime,simtime,plsize,db_size,max_dist=max_Dist,regular_placement=regular_placement,sim_times=sim_times)
            # sf_file,results_file,results_file_on_time,result = STEPS_QL_policy_prior.run(nrNode,avgSendTime,simtime,plsize,db_size,max_dist=max_Dist,regular_placement=regular_placement,sim_times=sim_times)
            sf_file,results_file,results_file_on_time,result = ucb1.run(nrNode,avgSendTime,simtime,plsize,db_size,max_dist=max_Dist,regular_placement=regular_placement,sim_times=sim_times)
            if temp is None:
                temp = result
            else: 
                temp = np.vstack((temp,result))
        avg = list(np.mean(temp, axis=0))        
        avg.insert(0,nrNode)
        print(["nrNodes","total sent","new packets","resend tentatives",\
                 "packets abandonned","collisions","lost packets",\
                 "receive ratio(based on total sent)","ack ratio(based on new packets)",\
                 "Acked number","Energy(J)","energy_per_100_ack(J)","effective packets ratio","energy_per_100_new_packet"])
        print(avg)
        data_to_write.append(avg)
    with open(sim_file,'w',newline='') as f:
        w = csv.writer(f,delimiter=',')
        w.writerow(["nrNodes","total sent","new packets","resend tentatives",\
                 "packets abandonned","collisions","lost packets",\
                 "receive ratio(based on total sent)","ack ratio(based on new packets)",\
                 "Acked number","Energy(J)","energy_per_100_ack(J)","effective packets ratio","energy_per_100_new_packet"])
        w.writerows(data_to_write)
    f.close()
    if graphic_on:
        fig_name = '.\\figs\\multi\\'+simulator_name+'_'+str(avgSendTime)+'_'+str(simtime)+'_'+str(db_size)+'_'+str(sim_times)
        plot_multi_run(results_file,fig_name,variable_list)

else:
    results_file = '.\\data\\csv_data\\'+simulator_name+'_'+str(avgSendTime)+'_'+str(simtime)+'_'+str(db_size)+'_'+str(sim_times)+'times.csv'
    temp = None
    for i in range(sim_times):
        # sf_file,results_file,results_file_on_time,result = STEPS_pureQL.run(nrNodes,avgSendTime,simtime,plsize,db_size,max_dist=max_Dist,regular_placement=regular_placement,sim_times=sim_times)
        # sf_file,results_file,results_file_on_time,result = STEPS_pureQL_prior.run(nrNodes,avgSendTime,simtime,plsize,db_size,max_dist=max_Dist,regular_placement=regular_placement,sim_times=sim_times)
        # sf_file,results_file,results_file_on_time,result = STEPS_QL_policy.run(nrNodes,avgSendTime,simtime,plsize,db_size,max_dist=max_Dist,regular_placement=regular_placement,sim_times=sim_times)
        # sf_file,results_file,results_file_on_time,result = STEPS_QL_policy_prior.run(nrNodes,avgSendTime,simtime,plsize,db_size,max_dist=max_Dist,regular_placement=regular_placement,sim_times=sim_times)
        # sf_file,results_file,results_file_on_time,result = LoRaSim_randomSF.run(nrNodes,avgSendTime,simtime,plsize,max_dist = max_Dist,regular_placement=regular_placement,sim_times=sim_times)
        sf_file,results_file,results_file_on_time,result = ucb1.run(nrNodes,avgSendTime,simtime,plsize,db_size,max_dist = max_Dist,regular_placement=regular_placement,sim_times=sim_times)     
        if temp is None:
            temp = result
        else: 
            temp = np.vstack((temp,result))
    avg = list(np.mean(temp, axis=0))        
    avg.insert(0,nrNodes)
    print(["nrNodes","total sent","new packets","resend tentatives",\
                "packets abandonned","collisions","lost packets",\
                "receive ratio(based on total sent)","ack ratio(based on new packets)",\
                "Acked number","Energy(J)","energy_per_100_ack(J)","effective packets ratio","energy_per_100_new_packet"])
    print(list(avg))
    if graphic_on:
        fig_name = '.\\figs\\single\\'+simulator_name+'_'+str(avgSendTime)+'_'+str(simtime)+'_'+str(db_size)+'_'+str(sim_times)
        plot_sf(sf_file,fig_name)
        plot_single_run(results_file,fig_name,variable_list,regular_placement)
        plot_single_run_ontime(results_file_on_time,fig_name,variable_list,simtime)

