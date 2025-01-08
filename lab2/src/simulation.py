import numpy as np
import time
from threading import Thread

from network import DesignatedRouter, Router


class Simulation():
    def __init__(self, _msgs_types_filter):
        self.designed_router = None
        self.stop_flag = False
        self.printer_flag = False
        self.blink_conn_arr = []
        self.msgs_types_filter = _msgs_types_filter


    def __router_run(self, neighbors):
        conn, index = self.designed_router.add_connection()
        router = Router(conn, index)
        router.neighbors = neighbors.copy()
        router.router_start()
        time.sleep(0.1)

        while True:
            router.proc_message(self.msgs_types_filter)
            if self.blink_conn_arr[router.index]:
                router.router_off()
                time.sleep(2)
                router.router_start()
                self.blink_conn_arr[router.index] = False

            if self.stop_flag:
                break


    def __designed_router_run(self):
        self.designed_router = DesignatedRouter()

        while True:
            self.designed_router.proc_message(self.msgs_types_filter)
            
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


    def __connections_breaker(self):
        time.sleep(2)
        
        threshold = 0.5
        while True:
            time.sleep(0.01)
            val = np.random.rand()
            if val >= threshold:
                index = np.random.randint(0, len(self.blink_conn_arr))
                self.blink_conn_arr[index] = True
                time.sleep(2)

            if self.stop_flag:
                break


    def simulate(self, nodes, neighbors, simulation_time:int=10, conn_break_prob:float=0.25):
        dr_thread = Thread(target=self.__designed_router_run, args=())

        node_threads = [Thread(target=self.__router_run, args=(neighbors[i],)) for i in range(len(nodes))]
        self.blink_conn_arr = [False for i in range(len(nodes))]

        dr_thread.start()
        for i in range(len(nodes)):
            node_threads[i].start()

        printer_thread = Thread(target=self.__printer, args=())
        conn_breaker_thread = Thread(target=self.__connections_breaker, args=())
        conn_breaker_thread.start()
        printer_thread.start()

        time.sleep(simulation_time)
        self.stop_flag = True
        for i in range(len(nodes)):
            node_threads[i].join()

        dr_thread.join()
