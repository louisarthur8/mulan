import simpy


global nodes

class MyNode():
    def __init__(self, node_id, bs, period,packetlen,max_dist,random_place = True):
        self.node_id = node_id
        self.SFs = [0]*6
        self.avg_rew  = [0]*6
        self.turn = 0
        self.algoCounts = [0]*6
        self.all_rewards = [0]*6

        #TODO def SFs  with min_sf()
    #TODO : functions set_position()


class MyPacket():
    def __init__(self, node_id, plen):
        self.sf = 12
        self.node_id = node_id
    #TODO : calcul_minsf()


def update(SFs,avg_rew,now_sf,turn,algoCounts):
    SFs[now_sf-7] = avg_rew[now_sf-7] + math.sqrt( (2.0 * math.log(turn) / algoCounts[now_sf-7]) )
    return SFs

def transmit(env,node):
    is_acked = -1
    node.all_rewards = node.all_rewards + is_acked
    node.algoCounts = node.algoCounts + 1
    node.avg_rew = node.all_rewards / node.algoCounts
    node.SFs = update(node.SFs,node.avg_rew,node.packet.sf,node.turn,node.algoCounts)
    node.packet.sf = random_pick_sf(node.SFs,node.minsf)

def monitor(env,results_array,simtime): # TODO : understand and maybe simplify 
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
    
    env = simpy.Environment()
    
    if regular_placement == 0:
        for i in range(0,nrNodes):
            # myNode takes period (in ms), base station id packetlen (in Bytes)
            node = MyNode(i,bsId, avgSendTime,plsize+LorawanHeader,maxDist)
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

    
    #TODO: encapsulation 
    with open(results_file, 'a',newline='') as file:
        writer = csv.writer(file,delimiter=',')
        for n in nodes:
            energy_per_100newpacket = n.static.energy/n.static.new_packet*100 if n.static.new_packet!=0 else 0
            result_line = [n.static.x,n.static.y,n.static.total_send,n.static.new_packet,n.static.retransmissions,n.buffer/n.packet.pl,\
                            n.static.collisions,n.static.lost,n.static.receive_ratio,n.static.ack_ratio,\
                            n.static.acked,n.static.energy,n.static.energy_per100_ack,n.static.effective_send,energy_per_100newpacket]
            writer.writerow(result_line)
    file.close()