from utils import *
from store_simulation import *

from connection import *

def test_connection(data, protocol_type, window, timeout, loss_prob):
    some_conn = Connection("Test connection", protocol_type, window, timeout, loss_prob)
    some_conn.push(data, True)
    res = some_conn.get()
    assert res == data
    print(res)
    return

def dif_connections_testing():
    protocol_types = [ResendProtocol.SRP, ResendProtocol.GBN]
    windows = [2, 3, 4, 5, 6, 7, 8, 9]
    loss_probs = [0., 0.1, 0.2, 0.3]
    
    data = list(range(100, 0, -1))
    
    for prot_type in protocol_types:
        for win in windows:
            for loss_prob in loss_probs:
                print(f'win={win}, loss={loss_prob}')
                start = time.time()
                test_connection(data, prot_type, win, 1.00, loss_prob)
                print(time.time() - start)

    return

def test_network_conf(data, topology, splits):
    return

def dif_network_testing():
    linear = {
        "name": "linear",
        "nodes": [0, 1, 2, 3, 4, 5, 6],
        "neighbors": [[1], [0, 2], [1, 3], [2, 4], [3, 5], [4, 6], [5]]
    }
    
    star = {
        "name": "star",
        "nodes": [0, 1, 2, 3, 4],
        "neighbors": [[1, 2, 3, 4], [0], [0], [0], [0]]
    }
    
    circle = {
        "name": "circle",
        "nodes": [0, 1, 2, 3],
        "neighbors": [[3, 1], [0, 2], [1, 3], [2, 0]]
    }
    
    topologies = [linear, star, circle]
    splits = list(range(8, 17, 1))
    data = load_text("./lab3/src/data/input.txt")
    
    for tplg in topologies:
        for split in splits:
            cur_topology = tplg
            print(f"\ntopology: {cur_topology['name']}, splits: {split}\n")

            sim = StoreSimulation()
            start = time.time()
            sim.simulate_short_parts_building(tplg["nodes"], tplg['neighbors'], )
            print(f'Time: {time.time() - start}')
            
    return

if __name__ == "__main__":
    #dif_connections_testing()
    dif_network_testing()