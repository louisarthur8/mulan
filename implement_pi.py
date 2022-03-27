import random
import numpy as np
    

epsilon = None # proba to not pick the best
alpha = None # learning rate

def update(SFs,now_sf,acked):
    global alpha
    SFs[now_sf-7] = SFs[now_sf-7] +alpha*(acked - SFs[now_sf-7])
    return SFs

def random_pick_sf(estimateval,minsf):
    global epsilon
    x = random.uniform(0,1)
    if (x > epsilon):
        return np.argmax(estimateval) + 7
    else :
        return random.choice([n for n in range (minsf,13)])


def main():
    
    is_acked = -1
    sf = 12
    minsf = 12

    SFs = [0]*6
    transmit(is_acked,sf,minsf,SFs)

def transmit(is_acked,sf,minsf,SFs):

    if is_acked > 0:
        SFs = update(SFs,sf,1)
    else:
        SFs = update(SFs,sf,0)
    sf = random_pick_sf(SFs,minsf)