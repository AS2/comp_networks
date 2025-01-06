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


    def __printer(self):
        while True:
            time.sleep(1)
            self.printer_flag = True
            if self.stop_flag:
                break
            
    
    def simulate_short_parts_building(self, nodes : tp.List, neighbors : tp.List):
        dr_thread = Thread(target=self.__designed_router_run, args=())

        node_threads = [Thread(target=self.__router_run, args=(neighbors[i], [], i)) for i in range(len(nodes))]
        self.blink_conn_arr = [False for i in range(len(nodes))]

        dr_thread.start()
        for i in range(len(nodes)):
            node_threads[i].start()

        printer_thread = Thread(target=self.__printer, args=())
        printer_thread.start()

        time.sleep(10.0)
        self.stop_flag = True
        for i in range(len(nodes)):
            node_threads[i].join()

        dr_thread.join()
        
        
    def simulate_storing(self, nodes : tp.List, neighbors : tp.List, data : tp.Any, splits : int, logging : bool):
        # init basic storing variables
        parts = [FilePart(data[i:i+splits], i) for i in range(0, len(data), splits)]
        parts_for_each_node = [[] for i in range(len(nodes))]
        for i, part in enumerate(parts):
            parts_for_each_node[i % len(nodes)].append(part)
            
        return
    
    
    def simulate_build(self, nodes : tp.List, neighbors : tp.List, data : tp.Any, splits : int, protocol : ResendProtocol, logging : bool):
        parts = [data[i:i+splits] for i in range(0, len(data), splits)]
        node_threads = [Thread(target=self.__router_run, args=(neighbors[i],)) for i in range(len(nodes))]
        return