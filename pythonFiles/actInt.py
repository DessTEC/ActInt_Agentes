from math import nan
from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from mesa.visualization.modules import CanvasGrid, TextElement
from mesa.visualization.ModularVisualization import ModularServer
import random

from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid as GridPath
from pathfinding.finder.a_star import AStarFinder

import math

class WallBlock(Agent):
    def __init__(self, model, pos):
        super().__init__(model.next_id(), model)
        self.pos = pos
    def step(self):
        pass

# Creación de la calse Celda, 1 sucio y 0 limpio
class Celda(Agent):
    def __init__(self, model, pos, cajas, esTorre):
        super().__init__(model.next_id(), model)
        self.pos = pos
        self.cajas = cajas
        self.esTorre = esTorre
    def step(self):
        pass
    
class Robot(Agent):
    def __init__(self, model, pos, matrix):
        super().__init__(model.next_id(), model)
        self.pos = pos
        self.tieneCaja = False
        self.matrix = matrix
        grid = GridPath(matrix= matrix)
        self.grid = grid

    def getCajasDisp(self):
        listaCajasDisp = []
        #Si aún no tiene caja, buscar cajas solas, si ya tiene, incluye las torres
        if self.tieneCaja == False:
            for agent in self.model.schedule.agents:
                if(type(agent) is Celda and agent.cajas == 1):
                    listaCajasDisp.append(agent)
        else:
            for agent in self.model.schedule.agents:
                if(type(agent) is Celda and agent.esTorre == True and agent.cajas < 5):
                    listaCajasDisp.append(agent)
        
        return listaCajasDisp

    def getClosestBoxPath(self, listaCajasDisp):
        minDistance = math.inf
        pathSelect = None
        cajaSelect = None

        #Encontrar la caja más cercana al robot
        for caja in listaCajasDisp:
            #Sacar vecinos válidos de caja actual considerando obstáculos y límites del tablero
            casillasCaja = self.model.grid.get_neighborhood(caja.pos, moore=False)
            casillasCajaValida = []

            for i in range(len(casillasCaja)):
                if(self.matrix[casillasCaja[i][1]][casillasCaja[i][0]] == 1):
                    casillasCajaValida.append(casillasCaja[i])
                
            # Datos de celda más cercana del robot a las adyacencias de la caja actual
            minDistAdy = math.inf
            pathSelectAdy = None
            cajaSelectAdy = None

            for coordenada in casillasCajaValida:
                self.grid.cleanup()
                grid = GridPath(matrix= self.matrix)
                self.grid = grid

                start = self.grid.node(self.pos[0], self.pos[1])
                end = self.grid.node(coordenada[0], coordenada[1])
                finder = AStarFinder(diagonal_movement = DiagonalMovement.never)
                path, runs = finder.find_path(start, end, self.grid)

                if len(path) < minDistAdy:
                    minDistAdy = runs
                    pathSelectAdy = path
                    cajaSelectAdy = caja
                        
            #Comparar distancia mínima de caja, contra distancia mínima de todas las cajas    
            if minDistAdy < minDistance:
                minDistance = minDistAdy
                pathSelect = pathSelectAdy
                cajaSelect = cajaSelectAdy
        
        return pathSelect, cajaSelect

    def step(self):
        
        listaCajasDisp = self.getCajasDisp()
        
        if len(listaCajasDisp) == 0:
            pass
        else:
            pathSelect, cajaSelect = self.getClosestBoxPath(listaCajasDisp)
            
            if(len(pathSelect) > 1): #Moverse hacia la caja elegida
                self.model.grid.move_agent(self, pathSelect[1])
                self.model.movimientos += 1
            else: #Si no tiene caja, recogerla, si ya tiene, sumarle a la torre
                if self.tieneCaja == False:
                    cajaSelect.cajas = 0
                    self.tieneCaja = True
                else:
                    cajaSelect.cajas += 1
                    self.tieneCaja = False
    
 
class Maze(Model):
 
    def __init__(self, M=10, N=10, numCajas=15, tiempoMaximo= 100):
        super().__init__()
    
        #Definir tamaño de tabla
    
        self.schedule = RandomActivation(self)
        self.tiempoMaximo = tiempoMaximo
        self.celdasTotales = M*N
        self.movimientos = 0

        #Crear mesa con los tamaños dados
        self.grid = MultiGrid(M, N, torus=False)

        matrix = [
            [0,0,0,0,0,0,0,0,0,0],
            [0,1,1,1,0,0,1,1,1,0],
            [0,1,1,1,1,1,1,1,1,0],
            [0,1,1,1,1,1,1,1,1,0],
            [0,0,1,1,1,1,1,1,0,0],
            [0,0,1,1,1,1,1,1,0,0],
            [0,1,1,1,1,1,1,1,1,0],
            [0,1,1,1,1,1,1,1,1,0],
            [0,1,1,1,0,0,1,1,1,0],
            [0,0,0,0,0,0,0,0,0,0],
        ]

        # Obtener lista de celdas transitables
        listaCeldasValidas = []
        for i in range(len(matrix)):
            for j in range(len(matrix[i])):
                if matrix[i][j] == 1:
                    listaCeldasValidas.append((j, i))

        listaIndexes = (random.sample(listaCeldasValidas, numCajas))

        currentIndex = 0
        listaCeldasCajas = []

        # Se posicionan las celdas en donde corresponden
        for _,x,y in self.grid.coord_iter():
            if (x,y) in listaIndexes:
                tile = Celda(self, (x, y), 1, False)
                listaCeldasCajas.append(tile)
                self.grid.place_agent(tile, tile.pos)
                self.schedule.add(tile)
                currentIndex += 1
            else:
                tile = Celda(self, (x, y), 0, False)
                self.grid.place_agent(tile, tile.pos)
                self.schedule.add(tile)

        # Decidir qué celdas serán torres
        listaCeldasTorres = (random.sample(listaCeldasCajas, int(math.ceil(numCajas/5))))
        for celda in listaCeldasTorres:
            celda.esTorre = True

        #Lista de posiciones para robots, tomando de las celdas válidas que no tienen cajas
        listaCeldasSinCajas = list(set(listaCeldasValidas) - set(listaIndexes))

        #Posicionar todos los agentes robots
        for i in range(5):
            posRobot = random.choice(listaCeldasSinCajas)
            listaCeldasSinCajas.remove(posRobot)
            robot = Robot(self, posRobot, matrix)
            self.grid.place_agent(robot, robot.pos)
            self.schedule.add(robot)

        for _,x,y in self.grid.coord_iter():
            if matrix[y][x] == 0:
                block = WallBlock(self, (x, y))
                self.grid.place_agent(block, block.pos)
                self.schedule.add(block)

    def step(self):
        # Si todas las cajas están en una torre y si los robots no llevan cajas, se ha terminado
        isComplete = True
        for agent in self.schedule.agents:
                if(type(agent) is Celda and agent.cajas == 1):
                    isComplete = False
                    break
                if(type(agent) is Robot and agent.tieneCaja == True):
                    isComplete = False
                    break

        if(self.schedule.steps == self.tiempoMaximo - 2 or isComplete):
            self.running = False
        else:
            self.schedule.step()

class ResultsElement(TextElement):
    def __init__(self):
        pass

    def render(self, model):
        return "Tiempo total de ejecución: " + str(model.schedule.steps + 2) + "\nPasos totales de robots: " + str(model.movimientos)

    

def agent_portrayal(agent):
  # Dependiendo del tipo de agente se genera el formato correspondiente
    if(type(agent) is Celda):
        if agent.cajas == 0:
            return {"Shape": "rect", "w": 1, "h": 1, "Filled": "true", "Color": "White", "Layer": 0}
        elif agent.cajas == 1:
            return {"Shape": "caja1.png", "Layer": 0}
        elif agent.cajas == 2:
            return {"Shape": "caja2.png", "Layer": 0}
        elif agent.cajas == 3:
            return {"Shape": "caja3.png", "Layer": 0}
        elif agent.cajas == 4:
            return {"Shape": "caja4.png", "Layer": 0}
        else:
            return {"Shape": "caja5.png", "Layer": 0}
    elif(type(agent) is Robot):
        if agent.tieneCaja == False:
            return {"Shape": "robot.png", "Layer": 0}
        else:
            return {"Shape": "robotConCaja.png", "Layer": 0}
    else:
        return {"Shape": "rect", "w": 1, "h": 1, "Filled": "true", "Color": "Gray", "Layer": 0}

    
grid = CanvasGrid(agent_portrayal, 10, 10, 450, 450)
results_element = ResultsElement()

# server = ModularServer(Maze, [grid, results_element], "Robots", {})
# server.port = 8520
# server.launch()