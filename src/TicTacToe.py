from FixedMCTS import FixedMCTS
from DynamicMCTS import DynamicMCTS
from GameState import GameState
import numpy as np

class BoardState(GameState):
    Players = {0: ' ', 1 : 'X', 2 : 'O'}
    Size = 3
    InARow = 3
    Dirs = [(0,1),(1,1),(1,0),(1,-1)]

    def __init__(self):
        self.Board = np.zeros((self.Size,self.Size,2))
        self.Player = 1
        self.PreviousPlayer = None
        return 

    def Copy(self):
        copy = BoardState()
        copy.Player = self.Player
        copy.Board = np.copy(self.Board)
        return copy

    def LegalActions(self):
        actions = np.zeros(self.Size * self.Size)
        for i in range(self.Size):
            for j in range(self.Size):
                if np.sum(self.Board[i, j, :]) == 0:
                    actions[self._coordsToIndex((i,j))] = 1

        return actions

    def ApplyAction(self, action):
        coords = self._indexToCoords(action)
        assert np.sum(self.Board[coords[0], coords[1], :]) == 0, 'Ahh. Can\'t go there! {}'.format(action)
        self.Board[coords[0], coords[1], self.Player - 1] = 1
        self.PreviousPlayer = self.Player
        self.Player = 1 if self.Player == 2 else 2
        return

    def AsInputArray(self):
        player = np.full((self.Size, self.Size), 1 if self.Player == 1 else -1)
        array = np.zeros((1, self.Size, self.Size, 3))
        array[0, :, :, 0:2] = self.Board
        array[0, :, :, 2] = player
        return array

    def Winner(self, prevAction = None):
        board = self._collapsed()

        if prevAction is not None:
            coords = self._indexToCoords(prevAction)
            win = self._checkVictory(board, coords[0], coords[1])
            if win is not None: 
                return win
        else:
            for i in range(self.Size):
                for j in range(self.Size):
                    if board[i,j] == 0:
                        continue
                    win = self._checkVictory(board, i, j)
                    if win is not None: 
                        return win

        if self._isOver(board):
            return 0
        return None

    def _isOver(self, board):
        return np.sum(board > 0) == self.Size * self.Size

    def _checkVictory(self, board, i, j):
        p = board[i,j]
        for dir in self.Dirs:
            inARow = 0
            r = 0
            while r*dir[0] + i < self.Size and r*dir[1] + j < self.Size and r*dir[1] + j >= 0 and board[r*dir[0] + i, r*dir[1] + j] == p:
                inARow += 1
                r += 1
            r = -1
            while r*dir[0] + i >= 0 and r*dir[1] + j < self.Size and r*dir[1] + j >= 0 and board[r*dir[0] + i, r*dir[1] + j] == p:
                inARow += 1
                r -= 1
            if inARow >= self.InARow:
                return p
        return None
    
    def _coordsToIndex(self, coords):
        return coords[0]*self.Size + coords[1]

    def _indexToCoords(self, index):
        return (index//self.Size, index % self.Size)
    
    def _collapsed(self):
        array = np.zeros(self.Board.shape[:2])
        for p in BoardState.Players:
            array[self.Board[:, :, p - 1] == 1] = p
        return array

    def __str__(self):
        array = self._collapsed()
        s = ''
        for i in range(array.shape[0]):
            s += '[ '
            for j in range(array.shape[1]):
                s += ' {} '.format(BoardState.Players[array[i, j]])
                if j < array.shape[1] - 1:
                    s += '|'
            s += ']\n'

        return s

    def __eq__(self, other):
        if other.Player != self.Player:
            return False
        return (other.Board == self.Board).all()

    def __hash__(self):
        return "{0}{1}".format(self.Player,str(self)).__hash__()

if __name__ == '__main__':
    params = {'mcts' : {'maxDepth' : 10, 'explorationRate' : 1.414, 'playLimit' : 5000}}
    player = FixedMCTS(**params)
    BoardState.Size = 3
    BoardState.InARow = 3

    state = BoardState()
    while state.Winner() is None:
        print(state)
        print('To move: {}'.format(state.Player))
        state, v, p = player.FindMove(state)
        print('Value: {}'.format(v))
        print('Selection Probabilities: {}'.format(p))
        print('Child Values: {}'.format(player.Root.ChildWinRates()))
        print('Child Exploration Rates: {}'.format(player.Root.ChildPlays()))
        print()
        player.MoveRoot([state])
    print(state)
    print(state.Winner())





