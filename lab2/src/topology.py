class Topology:
    def __init__(self):
        self.topology = []

    def print_nodes(self):
        res_str = ""
        for i in range(len(self.topology)):
            res_str += f"{i}: "
            for j in self.topology[i]:
                res_str += f"{j}, "
            res_str += "\n"
        res_str += "\n"
        print(res_str, end="")

    def get_shortest_ways(self, start):
        if len(self.topology) == 0:
            return None

        class Node:
            def __init__(self, value):
                self.value = value
                self.distance = None
                self.way = []

        unvisited = {node: None for node in range(len(self.topology))}  # using None as +inf

        for i in range(len(self.topology)):
            if len(self.topology[i]) == 0:
                unvisited.pop(i)

        ways = [[] for i in range(len(self.topology))]
        visited = {}
        curr_node = start
        curr_distance = 0

        unvisited[curr_node] = curr_distance
        ways[curr_node].append(start)

        while True:
            for neighbour in self.topology[curr_node]:
                distance = 1
                if neighbour not in unvisited:
                    continue
                new_distance = curr_distance + distance
                if unvisited[neighbour] is None or unvisited[neighbour] > new_distance:
                    unvisited[neighbour] = new_distance
                    ways[neighbour] = ways[curr_node].copy()
                    ways[neighbour].append(neighbour)
            visited[curr_node] = curr_distance
            del unvisited[curr_node]
            if not unvisited:
                break

            candidates = [node for node in unvisited.items() if node[1]]
            if len(candidates) == 0:
                break
            curr_node, curr_distance = sorted(candidates, key=lambda x: x[1])[0]

        return ways

    def add_new_node(self, new_index):
        count = new_index - len(self.topology) + 1
        for i in range(0, count):
            self.topology.append(set())

    def delete_node(self, index):
        self.topology[index].clear()
        for i in range(len(self.topology)):
            self.topology[i].discard(index)

    def add_new_link(self, i, j):
        self.add_new_node(i)
        self.add_new_node(j)
        self.topology[i].add(j)

    def delete_link(self, i, j):
        self.topology[i].discard(j)
        self.topology[j].discard(i)

    def copy(self):
        ret_val = Topology()
        ret_val.topology = self.topology.copy()
        return ret_val
