from mcts import MCTS,Node
import numpy as np

class DynamicMCTS(MCTS):
    """ An implementation of Monte Carlo Tree Search that aggregates statistics
        as it explores the tree
    """
    def __init__(self, params, **kwargs):
        params = params.get('mcts')
        return super().__init__(**params, **kwargs)
    
    # Overriding from MCTS
    def FindLeaf(self, node):
        while True:
            # If we are at the edge of our currently explored branch, 
            # build out the children and stop.
            if node.Children is None:
                self.AddChildren(node)
                break
            if np.sum(node.LegalActions) == 0:
                break

            # Otherwise, keep going!
            lastAction = self._selectAction(node)
            node = node.Children[lastAction]

        return node


