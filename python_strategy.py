import json
import random
import numpy as np
import math


COMMANDS = ['left','up','right','down']
WIDTH=30
LEFT='left'
RIGHT='right'
UP='up'
DOWN='down'
import networkx as nx

def in_polygon(x, y, xp, yp):
    c = 0
    for i in range(len(xp)):
        if (((yp[i] <= y and y < yp[i - 1]) or (yp[i - 1] <= y and y < yp[i])) and \
                (x > (xp[i - 1] - xp[i]) * (y - yp[i]) / (yp[i - 1] - yp[i]) + xp[i])): c = 1 - c
    return c


def get_diagonals(point, width=WIDTH):
    x, y = point

    return [
        (x + width, y + width),
        (x - width, y + width),
        (x + width, y - width),
        (x - width, y - width)
    ]


def get_vert_and_horiz(point, width=WIDTH):
    x, y = point

    return [
        (x, y + width),
        (x - width, y),
        (x, y - width),
        (x + width, y),
    ]


def get_neighboring(point, width=WIDTH):
    return [
        *get_vert_and_horiz(point, width),
        *get_diagonals(point, width)
    ]


class Territory:
    def __init__(self, points):
        self.points = points
        self.changed = True


    def get_boundary(self):     #функция для получения границы территории
        boundary = []
        for point in self.points:
            if any([neighboring not in self.points for neighboring in get_neighboring(point)]):
                boundary.append(point)
        return boundary

    def get_nearest_boundary(self, point, boundary):
        for neighbor in [point, *get_neighboring(point)]:
            if neighbor in boundary:
                return neighbor

    def _capture(self, boundary):
        poligon_x_arr = [x for x, _ in boundary]
        poligon_y_arr = [y for _, y in boundary]

        max_x = max(poligon_x_arr)
        max_y = max(poligon_y_arr)
        min_x = min(poligon_x_arr)
        min_y = min(poligon_y_arr)

        captured = []
        x = max_x
        while x > min_x:
            y = max_y
            while y > min_y:
                if (x, y) not in self.points and in_polygon(x, y, poligon_x_arr, poligon_y_arr):
                    captured.append((x, y))
                y -= WIDTH
            x -= WIDTH
        return captured

    def is_siblings(self, p1, p2):
        return p2 in get_vert_and_horiz(p1)

    def get_voids_between_lines_and_territory(self, lines):
        boundary = self.get_boundary()
        voids = []
        for i_lp1, lp1 in enumerate(lines):
            for point in get_neighboring(lp1):
                if point in boundary:
                    prev = None
                    for lp2 in lines[:i_lp1 + 1]:
                        start_point = self.get_nearest_boundary(lp2, boundary)
                        if start_point:
                            if prev and (self.is_siblings(prev, start_point) or prev == start_point):
                                prev = start_point
                                continue
                            end_index = boundary.index(point)
                            start_index = boundary.index(start_point)

                            try:
                                path = self.get_path(start_index, end_index, boundary)
                            except (nx.NetworkXNoPath, nx.NodeNotFound):
                                continue

                            if len(path) > 1 and path[0] == path[-1]:
                                path = path[1:]

                            path = [boundary[index] for index in path]
                            lines_path = lines[lines.index(lp2):i_lp1 + 1]

                            voids.append(lines_path + path)
                        prev = start_point
        return voids

    def capture_voids_between_lines(self, lines):
        captured = []
        for index, cur in enumerate(lines):
            for point in get_neighboring(cur):
                if point in lines:
                    end_index = lines.index(point)
                    path = lines[index:end_index + 1]
                    if len(path) >= 8:
                        captured.extend(self._capture(path))
        return captured

    def capture(self, lines):
        captured = set()
        if len(lines) > 1:
            if lines[-1] in self.points:
                voids = self.get_voids_between_lines_and_territory(lines)

                captured.update(self.capture_voids_between_lines(lines))

                for line in lines:
                    if line not in self.points:
                        captured.add(line)

                for void in voids:
                    captured.update(self._capture(void))
        if len(captured) > 0:
            self.changed = True
        return captured

    def remove_points(self, points):
        removed = []
        for point in points:
            if point in self.points:
                self.points.discard(point)
                removed.append(point)

        if len(removed) > 0:
            self.changed = True
        return removed

    def get_siblings(self, point, boundary):
        return [sibling for sibling in get_neighboring(point) if sibling in boundary]

    def get_path(self, start_index, end_index, boundary):
        graph = nx.Graph()
        for index, point in enumerate(boundary):
            siblings = self.get_siblings(point, boundary)
            for sibling in siblings:
                graph.add_edge(index, boundary.index(sibling), weight=1)

        return nx.shortest_path(graph, end_index, start_index, weight='weight')

    def split(self, line, direction, player):
        removed = []
        l_point = line[0]

        if any([point in self.points for point in line]):
            for point in list(self.points):
                if direction in [UP, DOWN]:
                    if player.x < l_point[0]:
                        if point[0] >= l_point[0]:
                            removed.append(point)
                            self.points.discard(point)
                    else:
                        if point[0] <= l_point[0]:
                            removed.append(point)
                            self.points.discard(point)

                if direction in [LEFT, RIGHT]:
                    if player.y < l_point[1]:
                        if point[1] >= l_point[1]:
                            removed.append(point)
                            self.points.discard(point)
                    else:
                        if point[1] <= l_point[1]:
                            removed.append(point)
                            self.points.discard(point)

        if len(removed) > 0:
            self.changed = True
        return removed







class Player():
    def __init__(self):
        self.tick = 0
        self.direction = None
        self.lines = []
        self.territory = []
        self.position = None

        self.speed = None
        self.width = None
        self.x_cells_count = None
        self.y_cells_count = None
        self.id = None
        self.message = None

    def Update(self,message):
        self.message = message
        self.direction = message['params']['players'][self.id]['direction']
        self.lines = message['params']['players'][self.id]['lines']
        self.position = message['params']['players'][self.id]['position']
        self.territory = message['params']['players'][self.id]['territory']
        self.tick = message['params']['tick_num']

    def Length_to_line(self, pos):
        if len(self.lines)>0:
            matr = (np.array(self.lines) - np.array(pos)) / self.width
            argmin = np.argmin(matr[:, 0] ** 2 + matr[:, 1] ** 2)
            x = pos[0] - self.lines[argmin][0]
            y = pos[1] - self.lines[argmin][1]
            distance = (abs(x) + abs(y)) / 30
            return distance
        else:
            return self.x_cells_count + self.y_cells_count

    def Length_to_my_territory(self, pos):
        matr = (np.array(self.territory) - np.array(pos)) / self.width
        argmin = np.argmin(matr[:,0]**2+matr[:,1]**2)
        x = pos[0] - self.territory[argmin][0]
        y = pos[1] - self.territory[argmin][1]
        distance = (abs(x)+abs(y))/30
        return distance





class My_Player(Player):
    def __init__(self,speed,width,x_cells_count,y_cells_count):
        self.command = None
        self.tick = 0
        self.direction = None
        self.lines = []
        self.position = None

        self.speed = speed
        self.width = width
        self.x_cells_count = x_cells_count
        self.y_cells_count = y_cells_count
        self.true_dir = None #сюда записываем последнюю команду
        self.next_pos = None
        self.id = 'i'

    def Update(self,message):
        self.message = message
        self.direction = message['params']['players'][self.id]['direction']
        self.lines = message['params']['players'][self.id]['lines']
        self.position = message['params']['players'][self.id]['position']
        self.territory = message['params']['players'][self.id]['territory']
        self.tick = message['params']['tick_num']

        x, y = self.position
        if self.true_dir == 'up':
            self.next_pos = np.array([x, y + self.width])
        if self.true_dir == 'down':
            self.next_pos = np.array([x, y - self.width])
        if self.true_dir == 'left':
            self.next_pos = np.array([x - self.width, y])
        if self.true_dir == 'right':
            self.next_pos = np.array([x + self.width, y])

    def get_next_point(self):       #следующая после следующей, если не менять направления
        x, y = self.position
        if self.true_dir == 'up':
            return x, y + self.width*2
        if self.true_dir == 'down':
            return x, y - self.width*2
        if self.true_dir == 'left':
            return x - self.width*2, y
        if self.true_dir == 'right':
            return x + self.width*2, y
        if self.true_dir == None:
            return x, y

    def border_check(self, pos):
        x, y = pos
        result = x < round(self.width / 2) or \
               x > self.x_cells_count * self.width - round(self.width / 2) or \
               y < round(self.width / 2) or \
               y > self.y_cells_count * self.width - round(self.width / 2)
        #with open("tettetetetetet.txt", "a") as data_file:
        #    to_write = self.tick, self.position, result, self.direction
        #    json.dump(to_write, data_file, indent=4)
        return result

    def line_check(self, pos):
        x,y=pos
        x = int(x)
        y = int(y)
        #list
        result = bool(self.lines.count([x,y])) #смотрю наличие точки в моем шлейфе
        return result


    def get_next_command(self):
        if self.border_check() or self.line_check():
            if self.true_dir == 'up':
                return 'right'
            if self.true_dir == 'down':
                return 'left'
            if self.true_dir == 'left':
                return 'up'
            if self.true_dir == 'right':
                return 'down'
        else:
            return self.true_dir


    def Get_dist_from_attacker(self):       #get distance from nearest attacker to my line
        enemies = list(message['params']['players'].keys())
        enemies.remove(self.id) #удаляю из списка игроков себя
        if len(enemies)>0:
            lengths = []
            for enemy in enemies:
                enemy_pos = message['params']['players'][enemy]['position']
                len_from_enemy = self.Length_to_line(enemy_pos)
                lengths.append(len_from_enemy)
            lengths.sort()

            return lengths[0]
        else:
            return self.x_cells_count*self.y_cells_count

    def Go_home_routine(self):
        pass
        #check your and attacker points

    def Nearest_way_home(self):
        pass



    def Explore_routine(self):
        pass


    def Possible_turns(self):

        POS = np.tile(self.next_pos, 4).reshape(4, 2)
        matr = np.array([[-self.width,0],[0,self.width],[self.width,0],[0,-self.width]])    #координаты, куда возможны повороты, их нужно проверить
        possible_nnext_positions = POS + matr
        allowed_turns_num = [0,1,2,3]  #номер поворота (лево, вверх, право, вниз) !!COMMANDS!!
        for i, nnext_pos in enumerate(possible_nnext_positions):
            if self.border_check(nnext_pos) or self.line_check(nnext_pos):
                allowed_turns_num.remove(i)    #т.е. остаются только те номера, куда поворачивать можно

        return possible_nnext_positions, allowed_turns_num


    def Go_Home_command(self):

        possible_pos, allowed_turns_num = self.Possible_turns()    #possible_pos - возможные 4 точки поворота
        allowed_pos = possible_pos[allowed_turns_num]              #allowed_turns_num - разрешенные повороты
        lengths = []
        for pos in allowed_pos:
            lengths.append(self.Length_to_my_territory(pos))

        with open("tettetetetetet.txt", "a") as data_file:
            to_write = str(lengths) + '\n'
            data_file.write(to_write)

        _argmin = np.argmin(np.array(lengths))   #ищем индекс минимального расстояния до своей территории
        ind = allowed_turns_num[_argmin]
        command = COMMANDS[ind] #
        next_pos = possible_pos[ind]
        return command, next_pos

    def Explore_command(self):
        possible_pos, allowed_turns_num = self.Possible_turns()
        allowed_commands = (np.array(COMMANDS)[allowed_turns_num]).tolist() #не дает так делать на обычных списках
        allowed_pos = possible_pos[allowed_turns_num]
        lengths = []
        for pos in allowed_pos:
            len_capt = self.Len_Captured(pos)
            lengths.append(len_capt)
        ind = np.argmax(lengths)

        return allowed_commands[ind]

    def Get_command(self):
        len_to_my_ter = self.Length_to_my_territory(self.position)
        len_form_attacker = self.Get_dist_from_attacker()
        if len_to_my_ter<len_form_attacker-2:
            return self.Explore_command()
        else:
            command, _ = self.Go_Home_command()
            return command

    def test_func(self,prin):
        if prin==0:
            lines = [[225,405],[195,405],[165,405],[165,435],[165,465],[195,465],[225,465],[255,465]]

            a = {tuple(point) for point in self.territory}
            ter = Territory(a)

            lines = [tuple(line) for line in lines]
            capt = ter.capture(lines)

            with open("tettetetetetet.txt", "a") as data_file:
                to_write = str(capt) + '\n'
                data_file.write(to_write)
            #json.dump(to_write, data_file, indent=4)

    def Len_Captured(self,nextnext):
        LINES_BACKUP = self.lines.copy()
        SELF_POS_BACKUP = self.next_pos.copy()

        self.lines.append(list(self.next_pos))
        self.next_pos = nextnext.copy()
        while self.Length_to_my_territory(self.next_pos)>0:
            _, next_pos = self.Go_Home_command()
            self.lines.append(list(next_pos))
            self.next_pos = next_pos.copy()

        a = {tuple(point) for point in self.territory}
        ter = Territory(a)
        lines = [tuple(line) for line in self.lines]
        capt = ter.capture(lines)

        self.lines = LINES_BACKUP.copy()
        self.next_pos = SELF_POS_BACKUP.copy()
        return len(capt)




i=0
cmd='left'
while True:
    z = input()
    message = json.loads(z)
    if message['type'] == 'start_game':
        x_cells_count = message['params']['x_cells_count']
        y_cells_count = message['params']['y_cells_count']
        speed = message['params']['speed']
        width = message['params']['width']
        Mine_player = My_Player(speed,width,x_cells_count,y_cells_count)
        Mine_player.true_dir = cmd
        print(json.dumps({"command": cmd, 'debug': str(z)}))

    if message['type'] == 'tick':
        Mine_player.Update(message)
        cmd = Mine_player.Get_command()
        Mine_player.true_dir = cmd



        print(json.dumps({"command": cmd, 'debug': str(z)}))




    if message['type'] == 'end_game':
        break