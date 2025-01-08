import typing as tp
import numpy as np
import time
from threading import Thread

from primitives import *
from network import DesignatedRouter, Router
from resend_protocol_base import ResendProtocol

class StoreSimulation():
    def __init__(self):
        self.designed_router = None
        self.stop_flag = False
        self.printer_flag = False
        
        self.building_flag = False
        self.metadata = None
        self.build_router = -1


    def __router_run(self, neighbors, router_file_parts, orig_idx):
        fDR2R, fR2DR, new_index = self.designed_router.add_connection(f'Router "{orig_idx}"')
        print(fDR2R, fR2DR, new_index, 'is starting...')
        router = Router(fDR2R, fR2DR, new_index, router_file_parts)
        router.neighbors = neighbors.copy()
        router.router_start()
        time.sleep(0.1)                 # for preventing data race !!!

        while True:
            router.proc_message()
            
            if self.building_flag == True and new_index == self.build_router:
                router.build_file(self.metadata)
                self.building_flag = False
            
            if self.stop_flag:
                print(f'R({orig_idx}) is stopping with next files: {router.file_parts}')
                break


    def __designed_router_run(self):
        self.designed_router = DesignatedRouter()

        while True:
            self.designed_router.proc_message()
            
            if self.printer_flag:
                self.designed_router.print_shortest_ways()
                self.printer_flag = False
            
            if self.stop_flag:
                break


    def __printer(self, max_calls : int = 5):
        calls_count = 0
        while calls_count < max_calls:
            time.sleep(1)
            calls_count += 1
            self.printer_flag = True
            
            
    
    def simulate_short_parts_building(self, nodes : tp.List, neighbors : tp.List):
        print(len(nodes), nodes, neighbors)
        
        dr_thread = Thread(target=self.__designed_router_run, args=())

        node_threads = [Thread(target=self.__router_run, args=(neighbors[i], [], i)) for i in range(len(nodes))]

        dr_thread.start()
        for i in range(len(nodes)):
            node_threads[i].start()

        time.sleep(1.0)
        self.__printer(5)
        
        self.stop_flag = True
        for i in range(len(nodes)):
            node_threads[i].join()

        dr_thread.join()
        
        print(self.designed_router.topology.topology)
        
        
    def simulate_storing(self, nodes : tp.List, neighbors : tp.List, data : tp.Any, splits : int):
        # init basic storing variables
        print(splits)
        k, m = divmod(len(data), splits)
        parts = [FilePart(data[i*k+min(i, m):(i+1)*k+min(i+1, m)], i) for i in range(splits)]
        parts_for_each_node = [[] for i in range(len(nodes))]
        for i, part in enumerate(parts):
            parts_for_each_node[i % len(nodes)].append(part)
        self.metadata = FileMetadata()
        self.metadata.data = data
        self.metadata.parts_cnt = splits
        self.metadata.size = len(data)
        
        # start building
        print(len(nodes), nodes, neighbors)
        
        dr_thread = Thread(target=self.__designed_router_run, args=())

        node_threads = [Thread(target=self.__router_run, args=(neighbors[i], parts_for_each_node[i], i)) for i in range(len(nodes))]

        dr_thread.start()
        for i in range(len(nodes)):
            node_threads[i].start()

        time.sleep(1.0)
        self.__printer(5)

        self.stop_flag = True
        for i in range(len(nodes)):
            node_threads[i].join()

        dr_thread.join()
        print(self.designed_router.topology.topology)
        return
    
    
    def simulate_build(self, nodes : tp.List, neighbors : tp.List, data : tp.Any, splits : int, idx_to_build_file : int):
        # init basic storing variables
        print(splits)
        k, m = divmod(len(data), splits)
        parts = [FilePart(data[i*k+min(i, m):(i+1)*k+min(i+1, m)], i) for i in range(splits)]
        parts_for_each_node = [[] for i in range(len(nodes))]
        for i, part in enumerate(parts):
            parts_for_each_node[i % len(nodes)].append(part)
        self.metadata = FileMetadata(data, splits)
        self.metadata.data = data
        self.metadata.parts_cnt = splits
        self.metadata.size = len(data)
        
        # start building
        print(len(nodes), nodes, neighbors)
        
        dr_thread = Thread(target=self.__designed_router_run, args=())

        node_threads = [Thread(target=self.__router_run, args=(neighbors[i], parts_for_each_node[i], i)) for i in range(len(nodes))]

        dr_thread.start()
        for i in range(len(nodes)):
            node_threads[i].start()

        # build parts and print paths from each 
        time.sleep(1.0)
        self.__printer(3)
        print('\n Stop printing calls...\n')
        time.sleep(5.0)
        
        # build file for index
        print('\n Start building call ...\n')
        self.building_flag = True
        self.build_router = idx_to_build_file
        time.sleep(25) # wait for file transporting

        self.stop_flag = True
        for i in range(len(nodes)):
            node_threads[i].join()

        dr_thread.join()
        print(self.designed_router.topology.topology)
        return