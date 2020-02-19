import random
import math
import sys
import copy
import time
import numpy as np
sys.path.append("..")  #so other modules can be found in parent dir
from Player import *
from Constants import *
from Construction import CONSTR_STATS
from Ant import UNIT_STATS
from Move import Move
from GameState import *
from AIPlayerUtils import *

MAX_TURNS = 999
_FOOD = 0
_STORAGE = 1

##
#AIPlayer
#Description: The responsbility of this class is to interact with the game by
#deciding a valid move based on a given game state. This class has methods that
#will be implemented by students in Dr. Nuxoll's AI course.
#
#Variables:
#   playerId - The id of the player.
##
class AIPlayer(Player):

    #__init__
    #Description: Creates a new Player
    #
    #Parameters:
    #   inputPlayerId - The id to give the new player (int)
    #   cpy           - whether the player is a copy (when playing itself)
    ##
    def __init__(self, inputPlayerId):
        super(AIPlayer, self).__init__(inputPlayerId, "AlexandJulian")
        self.storageToFood = None

    def resetState(self):
        self.storageToFood = None
    
    ##
    #getPlacement
    #
    #Description: called during setup phase for each Construction that
    #   must be placed by the player.  These items are: 1 Anthill on
    #   the player's side; 1 tunnel on player's side; 9 grass on the
    #   player's side; and 2 food on the enemy's side.
    #
    #Parameters:
    #   construction - the Construction to be placed.
    #   currentState - the state of the game at this point in time.
    #
    #Return: The coordinates of where the construction is to be placed
    ##
    def getPlacement(self, currentState):
        numToPlace = 0
        #implemented by students to return their next move
        if currentState.phase == SETUP_PHASE_1:    #stuff on my side
            self.resetState()
            numToPlace = 11
            moves = []
            for i in range(0, numToPlace):
                move = None
                while move == None:
                    #Choose any x location
                    x = random.randint(0, 9)
                    #Choose any y location on your side of the board
                    y = random.randint(0, 3)
                    #Set the move if this space is empty
                    if currentState.board[x][y].constr == None and (x, y) not in moves:
                        move = (x, y)
                        #Just need to make the space non-empty. So I threw whatever I felt like in there.
                        currentState.board[x][y].constr == True
                moves.append(move)
            return moves
        elif currentState.phase == SETUP_PHASE_2:   #stuff on foe's side
            numToPlace = 2
            moves = []
            for i in range(0, numToPlace):
                move = None
                while move == None:
                    #Choose any x location
                    x = random.randint(0, 9)
                    #Choose any y location on enemy side of the board
                    y = random.randint(6, 9)
                    #Set the move if this space is empty
                    if currentState.board[x][y].constr == None and (x, y) not in moves:
                        move = (x, y)
                        #Just need to make the space non-empty. So I threw whatever I felt like in there.
                        currentState.board[x][y].constr == True
                moves.append(move)
            return moves
        else:
            return [(0, 0)]

    #Caluclates the quickest path from storage to food
    def getOptimalStorageToFood(self, currentState):
        storage = getConstrList(currentState, currentState.whoseTurn, (ANTHILL, TUNNEL))
        storageToFood = {}
        for store in storage:
            food = self.getClosestTarget(currentState, store, _FOOD)
            dist = stepsToReach(currentState, store.coords, food.coords)
            turns = dist if (dist % 2 == 0) else dist + 1
            storageToFood[store.coords] = turns
        return storageToFood

    #Returns heuristic measurements concerning turns to win for various strategies
    def heuristicStepsToGoal(self, currentState, myInv):
        workerTotalTurns = self.workerHeuristic(currentState, myInv)
        queenTurns = self.queenHeuristic(currentState, myInv)
        starveTotalTurns = self.starveHeuristic(currentState, myInv)
        return (starveTotalTurns * 3) + (workerTotalTurns * 4) + (queenTurns * 3)

    def queenHeuristic(self, currentState, myInv):
        queen = next((a for a in myInv.ants if a.type == QUEEN))
        allGrass = getConstrList(currentState, None, (GRASS,))
        grass = next((g for g in allGrass if g.coords[1] <= 3))
        return approxDist(grass.coords, queen.coords)
       
    #Returns the minimum turns to win by killing all enemy workers
    def starveHeuristic(self, currentState, myInv):
        aggressors = getAntList(currentState, currentState.whoseTurn,
                                (SOLDIER, R_SOLDIER, DRONE))

        totalTurns = MAX_TURNS
        if len(aggressors) == 1:
            enemyTunnel = getConstrList(currentState, 1 - myInv.player, (TUNNEL,))[0]
            totalTurns = approxDist(aggressors[0].coords, enemyTunnel.coords)
        return totalTurns

    #Returns the minimum turns to win by reaching 11 food
    def workerHeuristic(self, currentState, myInv):
        needFood = 11 - myInv.foodCount
        workers = getAntList(currentState, currentState.whoseTurn, (WORKER,))

        if len(workers) > 0:
            antTurns, store = self.antTurnsToGoal(currentState, workers[0])
            return antTurns + ((needFood - 1) * self.storageToFood[store.coords])
        return MAX_TURNS

    #Caluclates the number of turns it will take each ant to deposit one food
    def antTurnsToGoal(self, currentState, ant):
        turns = MAX_TURNS
        if not hasattr(ant, "carrying") or not ant.carrying:
            food = self.getClosestTarget(currentState, ant, _FOOD)
            foodDist = stepsToReach(currentState, ant.coords, food.coords)

            store = self.getClosestTarget(currentState, food, _STORAGE)
            storeDist = stepsToReach(currentState, food.coords, store.coords)

            turns = (foodDist + storeDist) / 2
            
        elif ant.carrying:
            store = self.getClosestTarget(currentState, ant, _STORAGE)
            dist = stepsToReach(currentState, ant.coords, store.coords)
            turns = dist / 2

        return turns, store

    #Calculates the closest target (of specified type) to the specified source
    def getClosestTarget(self, currentState, source, targetType):
        if targetType == _STORAGE:
            targets = getConstrList(currentState, currentState.whoseTurn, (ANTHILL, TUNNEL))    
        elif targetType == _FOOD:
            targets = getCurrPlayerFood(None, currentState)

        dist1 = stepsToReach(currentState, source.coords, targets[0].coords)
        dist2 = stepsToReach(currentState, source.coords, targets[1].coords)
            
        return targets[0] if (dist1 < dist2) else targets[1]
    
    #Determines the best move for a given state
    def bestMove(self, currentState, moves):
         #End turn if only option
        if len(moves) == 1:
            return moves[0]

        expandedNodes = set()
        frontierNodes = [self.createNode(None, currentState, 0, float('inf'), None)]
        
        bestNode = frontierNodes[0]
        # Setting to 3 to look 3 moves ahead
        while (bestNode["depth"] < 3 and len(frontierNodes) > 0):
            bestNode = frontierNodes.pop(0)
            
            asciiList = asciiState(bestNode["state"])
            asciiList.append(str(bestNode["depth"]))
            asciiRep = ''.join(asciiList)
            if asciiRep not in expandedNodes:
                expandList = self.expandNode(bestNode)
                frontierNodes.extend(expandList)
                frontierNodes.sort(key = lambda x : x["turnsToWin"])
                frontierNodes = frontierNodes[:3]

                #print(asciiPrintState(bestNode["state"]))
                #print("Min turns to win: ", min([n["turnsToWin"] for n in frontierNodes]))
                #print("Best node -- current depth: ", bestNode["depth"], "turns to win: ", bestNode["turnsToWin"], "move: ", bestNode["move"])
            expandedNodes.add(asciiRep)

        for i in range(bestNode["depth"]):
            bestMove = bestNode["move"]
            bestNode = bestNode["parent"]

        return bestMove

    def expandNode(self, node):
        nodeState = node["state"]
        depth = node["depth"]
        moves = listAllLegalMoves(nodeState)

        vecEval = np.vectorize(self.evalNode)
        return vecEval(nodeState, moves, depth, node)

    def evalNode(self, nodeState, move, depth, node):
        nextState = getNextState(nodeState, move)
        myInv = getCurrPlayerInventory(nextState)
        turnsToWin = self.heuristicStepsToGoal(nextState, myInv)
        return self.createNode(move, nextState, depth + 1, turnsToWin, node)

    def createNode(self, move, nextState, depth, turnsToWin, parent):
        return {"move": move, "state": nextState, "depth": depth,
                "turnsToWin": turnsToWin + depth, "parent": parent}

    ##############################################
    ##             START OF HW 3               ##
    ##############################################

    # External Citation: https://stackabuse.com/minimax-and-alpha-beta-pruning-in-python/

    def minimax ():
        # Check if move is legal
        # Check if game has ended (win or lose condition has been met)
        return None

    def max ():
        # For all legal moves
            # Make a move or set of moves (then end turn)
            # Call min fxn
    #         (m, min_i, min_j) = self.min()
    #             # Fixing the maxv value if needed
    #             if m > maxv:
    #                 maxv = m
    #                 px = i
    #                 py = j
    #          # Setting back the field to empty
    #          self.current_state[i][j] = '.'
    # return (maxv, px, py)
            

        return None
    
    def min ():
        # For all legal moves
            # Make a move or set of moves (then end turn)
            # Call max fxn
    #         (m, max_i, max_j) = self.max()
    #             # Fixing the minv value if needed
    #             if m > minv:
    #                 minv = m
    #                 px = i
    #                 py = j
    #          # Setting back the field to empty
    #          self.current_state[i][j] = '.'
    # return (minv, px, py)
        return None


    
    ##
    #getMove
    #Description: Gets the next move from the Player.
    #
    #Parameters:
    #   currentState - The state of the current game waiting for the player's move (GameState)
    #
    #Return: The Move to be made
    ##
    def getMove(self, currentState):
        if (self.storageToFood == None):
            self.storageToFood = self.getOptimalStorageToFood(currentState)

        moves = listAllLegalMoves(currentState)
        return self.bestMove(currentState, moves)
    
    ##
    #getAttack
    #Description: Gets the attack to be made from the Player
    #
    #Parameters:
    #   currentState - A clone of the current state (GameState)
    #   attackingAnt - The ant currently making the attack (Ant)
    #   enemyLocation - The Locations of the Enemies that can be attacked (Location[])
    ##
    def getAttack(self, currentState, attackingAnt, enemyLocations):
        #Attack a random enemy.
        return enemyLocations[random.randint(0, len(enemyLocations) - 1)]

    ##
    #registerWin
    #
    # This agent doens't learn
    #
    def registerWin(self, hasWon):
        #method templaste, not implemented
        pass

def asciiState(state):
    stateStr = []
    for x in range(0,10):
        for y in range(0,10):
            ant = getAntAt(state, (y, x))
            if (ant != None):
                stateStr.append(charRepAnt(ant))
            else:
                constr = getConstrAt(state, (y, x))
                if (constr != None):
                    stateStr.append(charRepConstr(constr))
                else:
                    stateStr.append(".")

    stateStr.append(str(state.inventories[0].foodCount))
    stateStr.append(str(state.inventories[1].foodCount))
    return stateStr

#TESTS
ants1 = [Ant((0,0), WORKER, PLAYER_ONE), Ant((3,1), DRONE, PLAYER_ONE), 
         Ant((9,0), QUEEN, PLAYER_ONE)]
ants2 = [Ant((6,1), WORKER, PLAYER_TWO)]
constrs1 = [Building((0,2), ANTHILL, PLAYER_ONE), Building((5,0), TUNNEL, PLAYER_ONE)]
constrs2 = [Building((7,8), TUNNEL, PLAYER_TWO)]
constrs3 = [Building((8,0), FOOD, NEUTRAL), Building((9,0), FOOD, NEUTRAL),
            Building((2,0), FOOD, NEUTRAL), Building((3,0), FOOD, NEUTRAL), 
            Building((5,3), GRASS, NEUTRAL)]
foodCount = 0
dummyInventories = [Inventory(PLAYER_ONE, ants1, constrs1, foodCount),
                    Inventory(PLAYER_TWO, ants2, constrs2, []),
                    Inventory(NEUTRAL, [], constrs3, 0)]
dummyGameState = GameState(None, dummyInventories, PLAY_PHASE, PLAYER_ONE)
ai = AIPlayer(PLAYER_ONE)


#TEST - getOptimalStorageToFood
ai_1 = copy.deepcopy(ai)
storageToFood = ai_1.getOptimalStorageToFood(dummyGameState)
if storageToFood != {(0, 2): 4, (5, 0): 2}:
    print("ERROR - storageToFood() has identified a suboptimal path: " + str(storageToFood))


#TEST - heuristicStepsToGoal
ai_2 = copy.deepcopy(ai)
ai_2.workerHeuristic = lambda x, y: 3
ai_2.starveHeuristic = lambda x, y: 5
heuristics = ai_2.heuristicStepsToGoal(dummyGameState, dummyInventories[0])
if heuristics != (48):
    print("ERROR - heuristicStepsToGoal() has produced a suboptimal ordering: " + str(heuristics))



#TEST - queenHeuristic
ai_qH = copy.deepcopy(ai)
queenHeuristic = ai_qH.queenHeuristic(dummyGameState, dummyInventories[0])
if (queenHeuristic != 7):
    print("ERROR - queenHeuristic() has produced a suboptimal ordering: " + str(queenHeuristic))



#TEST - starveHeuristic
ai_3 = copy.deepcopy(ai)
ai_3.aggressorTurnsToEnemy = lambda w, x, y, z: [{"agg": ants1[1], "turns": 5, "workerIdx": 0}]
starveHeur = ai_3.starveHeuristic(dummyGameState, dummyInventories[0])
if starveHeur != (11):
    print("ERROR - starveHeuristic() has miscalculated turns to win: " + str(starveHeur))


#TEST - workerHeuristic
ai_5 = copy.deepcopy(ai)
ai_5.storageToFood = ai_5.getOptimalStorageToFood(dummyGameState)
turnsToWin = ai_5.workerHeuristic(dummyGameState, dummyInventories[0])
if (turnsToWin != (22.5)):
    print("ERROR - workerHeuristic() has miscalculated turns to win: " + str(turnsToWin))


#TEST - antTurnsToGoal
ai_6 = copy.deepcopy(ai)
turnsToGoal = ai_6.antTurnsToGoal(dummyGameState, ants1[0])
if (turnsToGoal[0] != 2.5):
    print("ERROR - antTurnsToGoal() has miscalculated turns to goal: " + str(turnsToGoal))

#TEST - getClosestTarget
ai_8 = copy.deepcopy(ai)
closestFoodToWorker = ai_8.getClosestTarget(dummyGameState, ants1[0], _FOOD)
if (closestFoodToWorker.coords != (2,0)):
    print("ERROR - getClosestTarget() has miscalculated the worker's closest food: " + str(closestFoodToWorker.coords))



#TEST - bestMove
ai_9 = copy.deepcopy(ai)
ai_9.storageToFood = ai_9.getOptimalStorageToFood(dummyGameState)
moves = listAllLegalMoves(dummyGameState)
best_move = ai_9.bestMove(dummyGameState, moves)
if (best_move.moveType != MOVE_ANT or best_move.coordList != [(3, 1), (4, 1), (5, 1), (5, 2)]):
    print("ERROR - bestMove() miscalculated the drone's best move: " + str(best_move))


#TEST - expandNode
ai_10 = copy.deepcopy(ai)
ai_10.storageToFood = ai_10.getOptimalStorageToFood(dummyGameState)
dummyNode = ai_10.createNode(moves[0], dummyGameState, 0, 3, None)
bestNodes = ai_10.expandNode(dummyNode)
if (bestNodes[2]["turnsToWin"] != 141.0):
    print("ERROR - expandNode() did not expand nodes properly: " + str(bestNodes[2]))

#TEST - evalNode
ai_11 = copy.deepcopy(ai)
ai_11.storageToFood = ai_10.getOptimalStorageToFood(dummyGameState)
nodeEvaluation = ai_11.evalNode(dummyGameState, moves[0], 0, None)
if (nodeEvaluation["turnsToWin"] != 143.0):
    print("ERROR - evalNode() did not evaluate the node properly: " + str(nodeEvaluation))

#TEST - createNode
ai_12 = copy.deepcopy(ai)
dummyNode = ai_12.createNode(moves[0], dummyGameState, 0, 13, None)
if (dummyNode["turnsToWin"] != 13):
    print("ERROR - createNode() failed to create a node: " + str(dummyNode))
