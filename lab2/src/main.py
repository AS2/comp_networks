from simulation import Simulation
from network import MsgType


def main():
    linear = {
        "name": "linear",
        "nodes": [0, 1, 2],
        "neighbors": [[1], [0, 2], [1]]
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
    for tplg in topologies:
        #simulator = Simulation(_msgs_types_filter=[])
        simulator = Simulation(_msgs_types_filter=[MsgType.NEIGHBORS, MsgType.GET_TOPOLOGY, MsgType.SET_TOPOLOGY, MsgType.OFF, MsgType.PRINT_WAYS])
        cur_topology = tplg
        print(f"\ntopology: {cur_topology['name']}\n")
        simulator.simulate(cur_topology["nodes"], cur_topology["neighbors"])


if __name__ == '__main__':
    main()

