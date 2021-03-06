import os
import sys
import yaml
sys.path.insert(0, './src/')

from blackbird import BlackBird
from TicTacToe import BoardState

def main():
    assert os.path.isfile('parameters.yaml'), 'Copy the parameters_template.yaml file into parameters.yaml to test runs.'
    with open('parameters.yaml') as param_file:
        parameters = yaml.load(param_file.read().strip())

    LogDir = parameters.get('logging').get('log_dir')
    if LogDir is not None and os.path.isdir(LogDir):
        for file in os.listdir(os.path.join(os.curdir, LogDir)):
            os.remove(os.path.join(os.curdir, LogDir, file))
            
    TrainingParameters = parameters.get('selfplay')
    BlackbirdInstance = BlackBird(saver=True, tfLog=True,
                                  loadOld=True, **parameters)

    for epoch in range(1, TrainingParameters.get('epochs') + 1):
        print('Starting epoch {0}...'.format(epoch))
        nGames = parameters.get('selfplay').get('training_games')
        examples = BlackbirdInstance.GenerateTrainingSamples(
            nGames,
            parameters.get('mcts').get('temperature').get('exploration'))
        BlackbirdInstance.LearnFromExamples(examples)
        print('Finished training for this epoch!')

        (wins, draws, losses) = BlackbirdInstance.TestRandom(
            parameters.get('mcts').get('temperature').get('exploitation'),
            parameters.get('selfplay').get('random_tests'))
        print('Against a random player:')
        print('Wins = {0}'.format(wins))
        print('Draws = {0}'.format(draws))
        print('Losses = {0}'.format(losses))

        (wins, draws, losses) = BlackbirdInstance.TestPrevious(
            parameters.get('mcts').get('temperature').get('exploitation'),
            parameters.get('selfplay').get('selfplay_tests'))
        print('Against the last best player:')
        print('Wins = {0}'.format(wins))
        print('Draws = {0}'.format(draws))
        print('Losses = {0}'.format(losses))

        print('\n')

        if wins > losses:
            BlackbirdInstance.saveModel()

if __name__ == '__main__':
    main()
