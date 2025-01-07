from copy import copy
import enum
import time 

import topology as topology_class
from primitives import *
from connection import Connection
from resend_protocol_base import *

class NetworkCode(enum.Enum):
    # codes for build paths from every router to each other
    NEIGHBORS = enum.auto()
    GET_TOPOLOGY = enum.auto()
    SET_TOPOLOGY = enum.auto()
    
    # print paths code
    PRINT_WAYS = enum.auto()
    
    # build file code
    BUILD_FILE_START = enum.auto()
    BUILD_FILE_END = enum.auto()
    BUILD_CONNS = enum.auto()


# Class for describing router communications and actions
class NetworkMsg:
    def __init__(self):
        self.data = None
        self.type = None
        
    def __repr__(self):
        return f"({self.type}: {self.data})"

    def __str__(self):
        return f"({self.type}: {self.data})"
    
class FilePartPackage():
    def __init__(self):
        self.filepart = None
        self.destination = -1
        

class DesignatedRouter:
    def __init__(self):
        self.connections = []                       # outputed and inputed connections with all routers
        self.topology = topology_class.Topology()   # builded and spreaded topology
        self.is_yet_building = False

        # connections indexing consts
        self.__FROM_DR = 0
        self.__FROM_R = 1
    
    def add_connection(self, name:str):
        fDR2R = Connection(name+"_f-DR-2-R", ResendProtocol.SRP, 3, 0.5, 0.0)
        fR2DR = Connection(name+"_f-R-2-DR", ResendProtocol.SRP, 3, 0.5, 0.0)
        
        new_index = len(self.connections)
        self.connections.append((fDR2R, fR2DR))
        return fDR2R, fR2DR, new_index

    def add_node(self, index : int, neighbors : tp.List[int]):
        self.topology.add_new_node(index)
        for j in neighbors:
            self.topology.add_new_link(index, j)

    def send_all_exclude_one(self, exclude_index : int, msg : tp.Any):
        for conn_ind in range(len(self.connections)):
            conn = self.connections[conn_ind]
            if conn is None:
                continue
            if conn_ind == exclude_index:
                continue
            conn[self.__FROM_DR].push([msg], False)

    def proc_msg_neighbors(self, conn_ind : int, input_msg : NetworkMsg):
        self.add_node(conn_ind, input_msg.data)

        msg = NetworkMsg()
        msg.type = NetworkCode.NEIGHBORS
        msg.data = {"index": conn_ind,
                    "neighbors": input_msg.data
                    }

        self.send_all_exclude_one(conn_ind, msg)

    
    def print_shortest_ways(self):
        print("DR going to ask print ways...")
        msg = NetworkMsg()
        msg.type = NetworkCode.PRINT_WAYS
        for conn in self.connections:
            conn[self.__FROM_DR].push([msg], False)
            
    def proc_one_msg(self, conn, conn_ind, msg):
        input_msg = msg
        print(f"dr({conn_ind}): {input_msg}\n", end="")

        if input_msg.type == NetworkCode.NEIGHBORS:
            self.proc_msg_neighbors(conn_ind, input_msg)

        elif input_msg.type == NetworkCode.GET_TOPOLOGY:
            msg = NetworkMsg()
            msg.type = NetworkCode.SET_TOPOLOGY
            msg.data = self.topology.copy()
            conn[self.__FROM_DR].push([msg], False)
            
        elif input_msg.type == NetworkCode.BUILD_CONNS:
            input_cons = [{} for _ in range(len(self.topology.topology))]
            output_cons = [{} for _ in range(len(self.topology.topology))]
                
            for i, nodes_neighbors in enumerate(self.topology.topology):
                for neighbor in nodes_neighbors:
                    if neighbor <= i:
                        continue
                        
                    conn_1 = Connection(f"{i}->{neighbor}", ResendProtocol.SRP, 5, 0.1, 0.2)
                    conn_2 = Connection(f"{neighbor}->{i}", ResendProtocol.SRP, 5, 0.1, 0.2)
                        
                    input_cons[i][neighbor] = conn_2
                    input_cons[neighbor][i] = conn_1
                    output_cons[i][neighbor] = conn_1
                    output_cons[neighbor][i] = conn_2
                        
            for i in range(len(self.topology.topology)):
                msg = NetworkMsg()
                msg.type = NetworkCode.BUILD_CONNS
                msg.data = (input_cons[i], output_cons[i])
                self.connections[i][self.__FROM_DR].push([msg], False)
                    
        elif input_msg.type == NetworkCode.BUILD_FILE_START:
            self.is_yet_building = True
            new_msg = NetworkMsg()
            new_msg.type = NetworkCode.BUILD_FILE_START
            new_msg.data = input_msg.data
                
            for i in range(len(self.connections)):
                some_conn = self.connections[conn_ind][self.__FROM_DR]
                    
                if some_conn is None:
                    continue
                    
                some_conn.push([new_msg], False)
                    
        elif input_msg.type == NetworkCode.BUILD_FILE_END:
            self.is_yet_building = False
            new_msg = NetworkMsg()
            new_msg.type = NetworkCode.BUILD_FILE_END
            new_msg.data = input_msg.data
                
            for i in range(len(self.connections)):
                some_conn = self.connections[conn_ind][self.__FROM_DR]
                    
                if some_conn is None:
                    continue
                    
                some_conn[self.__FROM_DR].push([new_msg], False)
                    
        else:
            print("DR: unexpected msf type:", input_msg.type)
        
        return

    def proc_message(self):
        for conn_ind in range(len(self.connections)):
            conn = self.connections[conn_ind]
            if conn is None:
                continue

            input_msg = conn[self.__FROM_R].get()

            if input_msg is None:
                continue
            else:
                print(input_msg)
                for msg in input_msg:
                    self.proc_one_msg(conn, conn_ind, msg[0])
            

class Router:
    def __init__(self, conn_from_DR : Connection, conn_2_DR : Connection, index : int, router_file_parts : tp.List[FilePart]):
        # connections to communicate with DR
        self.conn_2_DR = conn_2_DR
        self.conn_from_DR = conn_from_DR
        
        # built nformation about total network
        self.topology = topology_class.Topology()
        self.shortest_roads = None
        
        # information about this router and connected to him routers
        self.index = index
        self.neighbors = []
        
        # connections to communicate with connected to DR neighbors
        self.inputed_conns = {}
        self.outputed_conns = {}
        
        # stored data
        self.file_parts = router_file_parts
        
        # variables to manage file building
        self.is_yet_building = False
        self.transmited_parts = []

    def print_shortest_ways(self):
        shortest_ways = self.topology.get_shortest_ways(self.index)
        result = 'shortest ways from {}:\n'.format(self.index)
        for i, way in enumerate(shortest_ways):
            if way:
                way_str = ' -> '.join(map(str, way))
            else:
                way_str = None
            result += '({}, {}): {}\n'.format(self.index, i, way_str)
        print(result)
    
    def ask_build_conns(self):
        msg = NetworkMsg()
        msg.type = NetworkCode.BUILD_CONNS
        msg.data = None
        self.conn_2_DR.push([msg], False)
        return
    
    def ask_build_file(self):
        msg = NetworkMsg()
        msg.type = NetworkCode.BUILD_FILE_START
        msg.data = self.index
        self.conn_2_DR.push([msg], False)
        return
    
    def build_file(self, file_metadata : FileMetadata):
        print(f"Building for {self.index} asked...")
        # ask for build connections to transfer files
        self.ask_build_conns()
        time.sleep(0.2)
        
        # ask for share parts from another routers to 
        self.ask_build_file()
        time.sleep(0.2)
        
        # save file metadata for future building
        self.filemetadata = file_metadata
        return

    def send_neighbors(self):
        msg = NetworkMsg()
        msg.type = NetworkCode.NEIGHBORS
        msg.data = self.neighbors.copy()
        self.conn_2_DR.push([msg], False)

    def get_topology(self):
        msg = NetworkMsg()
        msg.type = NetworkCode.GET_TOPOLOGY
        self.conn_2_DR.push([msg], False)

    def router_start(self):
        self.send_neighbors()
        self.get_topology()

    def add_node(self, index, neighbors):
        self.topology.add_new_node(index)
        for j in neighbors:
            self.topology.add_new_link(index, j)

        if index in self.neighbors:
            if index not in self.topology.topology[self.index]:
                msg = NetworkMsg()
                msg.type = NetworkCode.NEIGHBORS
                msg.data = [index]
                self.conn_2_DR.push([msg], False)
    
    def ask_stop_building(self):
        msg = NetworkMsg()
        msg.type = NetworkCode.BUILD_FILE_END
        msg.data = self.index
        self.conn_2_DR.push([msg], False)
        return
    
    def validate_packages(self):
        # Check if all packages are in the correct place
        for package in self.transmited_parts:
            if package.destination != self.index:
                return
        
        # Check that all parts are collected
        if self.filemetadata.parts_cnt != len(self.transmited_parts):
            return
        
        # Sort parts and check id they are correct
        sorted(self.transmited_parts, key=lambda x: x.filepart.part_idx)
        expected = 0
        for part in self.transmited_parts:
            if part.filepart.part_idx == expected:
                expected += 1
            else:
                return
        
        self.ask_stop_building()
        self.data = []
        for part in self.transmited_parts:
            self.data += part.filepart.data
        return

    def proc_transfering(self):
        if self.is_yet_building == False:
            return
        
        # collect data from all inputs connections
        for input_conn_key in self.input_conn.keys():
            input_conn = self.input_conn[input_conn_key]
            
            get_packages = input_conn.get()
            
            if get_packages == None:
                continue
            else:
                self.transmited_parts += get_packages
        
        # if transmitted parts are in correct place - just check if there are all packages and 
        if len(self.transmited_parts) == 0:
            return
        
        if self.transmited_parts[0].destination == self.index:
            self.validate_packages()
            return
        
        # generate packages array of file parts
        data_to_transfer = copy(self.transmited_parts)
        self.transmited_parts = []
        
        # choose the way to put all packages
        destination = data_to_transfer[0].destination
        packages_path = self.shortest_roads[destination]
        reciever = packages_path[1] # <- 'cause '0' element is for start position
        self.outputed_conns[reciever].push(data_to_transfer, False) 

        return
    
    def package_file_parts(self, delivery_idx : int):
        for file_part in self.file_parts:
            new_package = FilePartPackage()
            new_package.destination = delivery_idx
            new_package.filepart = file_part
            self.transmited_parts.append(new_package)
        return
    
    def proc_one_message(self, input_msg):
        print(f"r({self.index}): {input_msg}")

        text = 'router' + str(self.index) + ' got: "{}"'
        if input_msg.type == NetworkCode.NEIGHBORS:
            index = input_msg.data["index"]
            neighbors = input_msg.data["neighbors"]
            self.add_node(index, neighbors)

        elif input_msg.type == NetworkCode.SET_TOPOLOGY:
            new_topology = input_msg.data
            self.topology = new_topology

        elif input_msg.type == NetworkCode.PRINT_WAYS:
            print('Gonna print ways!')
            self.print_shortest_ways()
            
        elif input_msg.type == NetworkCode.BUILD_CONNS:
            self.inputed_conns, self.outputed_conns = input_msg.data
            
        elif input_msg.type == NetworkCode.BUILD_FILE_START:
            if (input_msg.data == self.index):
                print('---ASKED NODE STARTS TO BUILDING FILE---')
                self.start_time = time.time()
            
            print(f"Node-{self.index}: starting to build file.")
            self.is_yet_building = True
            self.package_file_parts(input_msg.data)
            
        elif input_msg.type == NetworkCode.BUILD_FILE_END:
            self.is_yet_building = False
            print(f"Node-{self.index}: ending to build file.")
            if input_msg.data == self.index:
                print(f"---ASKED NODE FINISHED BUILDING FILE with time {time.time() - self.start_time}---")
                print(f"RESULT:\n{self.data}")

        else:
            print("DR: unexpected msf type:", input_msg.type)
            
        return

    def proc_message(self):
        input_msg = self.conn_from_DR.get()
        
        if input_msg is not None:
            print(input_msg)
            for msg in input_msg:
                self.proc_one_message(msg[0])

        self.proc_transfering()

    pass
