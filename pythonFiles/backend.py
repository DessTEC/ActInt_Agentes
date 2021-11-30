import flask
from flask.json import jsonify
import uuid
from actInt import Celda, Maze, Robot

games = {}

app = flask.Flask(__name__)

@app.route("/games", methods=["POST"])
def create():
    global games
    id = str(uuid.uuid4())
    games[id] = Maze()
    return "ok", 201, {'Location': f"/games/{id}"}

@app.route("/games/<id>", methods=["GET"])
def queryStateCars(id):
    global model
    model = games[id]
    model.step()
    agents = model.schedule.agents
    
    listCeldas = []
    listRobots = []

    for agent in agents:
        if(isinstance(agent, Celda)):
            listCeldas.append({"id": agent.unique_id, "x": agent.pos[0], "y": agent.pos[1], "cajas": agent.cajas})
        elif(isinstance(agent, Robot)):
            listRobots.append({"id": agent.unique_id, "x": agent.pos[0], "y": agent.pos[1], "tieneCaja": agent.tieneCaja})

    return jsonify({"celdas": listCeldas, "robots": listRobots})

# @app.route("/games/<id>/celdas", methods=["GET"])
# def queryStateLights(id):
#     global model
#     model = games[id]
#     model.step()
#     celdas = model.schedule.agents
    
#     listAgents = []

#     for i in range(model.celdasTotales):
#         listAgents.append({"x": celdas[i].pos[0], "y": celdas[i].pos[1], "cajas": celdas[i].cajas})

#     return jsonify({"Items": listAgents})

# @app.route("/games/<id>/robots", methods=["GET"])
# def queryStateCars(id):
#     global model
#     model = games[id]
#     model.step()
#     robots = model.schedule.agents
    
#     listAgents = []

#     for m in range(model.celdasTotales, model.celdasTotales+5):
#         listAgents.append({"x": robots[m].pos[0], "y": robots[m].pos[1], "tieneCaja": robots[m].tieneCaja})

#     return jsonify({"Items": listAgents})

app.run()