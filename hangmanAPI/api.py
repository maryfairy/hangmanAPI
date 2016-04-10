# -*- coding: utf-8 -*-`
"""api.py - Create and configure the Game API exposing the resources.
This can also contain game logic. For more complex games it would be wise to
move game logic to another file. Ideally the API will be simple, concerned
primarily with communication to/from the API's users."""


import logging
import endpoints
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue

from models import User, Game, Score
from models import StringMessage, NewGameForm, GameForm, MakeMoveForm,\
    ScoreForms, GameListForm, GameListForms, UserRankForm, UserRankForms, \
    GameHistoryForm

from utils import get_by_urlsafe

NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(
        urlsafe_game_key=messages.StringField(1),)
GET_HIGH_SCORE_REQUEST = endpoints.ResourceContainer(
     limit=messages.IntegerField(1))
MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeMoveForm,
    urlsafe_game_key=messages.StringField(1),)
USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                           email=messages.StringField(2))

MEMCACHE_MOVES_REMAINING = 'MOVES_REMAINING'

### Add on one player hangman API
@endpoints.api(name='hangman', version='v1')
class HangmanApi(remote.Service):
    """Game API"""
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                    'A User with that name already exists!')
        user = User(name=request.user_name, email=request.email)
        user.put()
        return StringMessage(message='User {} created!'.format(
                request.user_name))

    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    
    def new_game(self, request):
        """Creates new game"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        try:
            game = Game.new_game(user.key, request.min,
                                 request.max, request.attempts)
        except ValueError:
            raise endpoints.BadRequestException('Maximum must be greater '
                                                'than minimum!')

        # Use a task queue to update the average attempts remaining.
        # This operation is not needed to complete the creation of a new game
        # so it is performed out of sequence.
        taskqueue.add(url='/tasks/cache_average_attempts')
        return game.to_form('Good luck playing Hangman!')

## Add in cancel game request
    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=StringMessage,
                      path='game/cancel/{urlsafe_game_key}',
                      name='cancel_game',
                      http_method='GET')
    
    def cancel_game(self, request):
        """Cancel playing game."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            if(game.game_over == False):
                game.key.delete()
                return StringMessage(message="Game cancelled.")
            else:
                return StringMessage(message="Cannot delete already completed game.")
        else:
            raise endpoints.NotFoundException('Incorrect Game Key')

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.to_form('Time to make a move!')
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PUT')
    
    def make_move(self, request):
        """Makes a move. Returns a game state with message"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game.game_over:
            return game.to_form('Game already over!')

        ## set-up history of message string
        if game.history is None:
          history = []

        if request.guess_word == game.target_word:
            game.end_game(True)
            game.history = str(game.history) + ' ' + str([request.guess_word, 'You Win!'])
            game.put()
            return game.to_form('You win!')

        if request.guess_word is not None:
            game.history = str(game.history) + ' ' + str([request.guess_word, 'Incorrect Guess!'])
            game.attempts_remaining -= 1
            game.put()
            return game.to_form('Incorrect Guess!')

        # need to breakdown target_word into individual strings
        # did this by splitting a string into an array
        # http://stackoverflow.com/questions/113655/is-there-a-function-in-python-to-split-a-word-into-a-list

        # create string of previously guessed letters
        string_guessed_letter = request.guess_letter.encode('UTF8')

        # check illegal move if letter was guessed already
        if game.guessed_letters is not None:
          if string_guessed_letter in game.guessed_letters:
            return game.to_form('Letter already guessed!')


        # attempts will only be decreased if no letter found in target_word
        if request.guess_letter[0] not in game.target_word:
          game.attempts_remaining -= 1

        # add new guest letter to string
        if game.guessed_letters is None:
          game.guessed_letters = string_guessed_letter
        else:
          game.guessed_letters= str(game.guessed_letters) + string_guessed_letter
        game.put()
               
        # need to print out the hangman board
        strip_unicode_letter_history = [str(x) for x in game.guessed_letters]

        print_hint = [str(x) for x in game.target_word]
        show_hint = []

        for i in range(len(print_hint)):
          for x in range(len(strip_unicode_letter_history)):
            if x == max(range(len(strip_unicode_letter_history))):
              if strip_unicode_letter_history[x] == print_hint[i]:
                show_hint.append(strip_unicode_letter_history[x])
              else:
                show_hint.append('_')
            elif strip_unicode_letter_history[x] == print_hint[i]:
              show_hint.append(strip_unicode_letter_history[x])
              break

        msg = ' '.join(show_hint)

        game.history = str(game.history) + ' ' + str([string_guessed_letter,msg])
        game.put()

        #print(msg)
        # TODO add more to the message during the game (# moves left
        # letters guessed, etc)
        if game.attempts_remaining < 1:
            game.end_game(False)
            game.history = str(game.history) + ' ' + str([msg + '  Game over!'])
            game.put()
            return game.to_form(msg + '  Game over!')
        else:
            game.put()
            return game.to_form(msg)

    ## Add in get_user_games
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=GameListForms,
                      path='games/user/{user_name}',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Returns all of an individual User's games."""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        games = Game.query(Game.user == user.key)
        games = games.filter(Game.game_over == False)
        return GameListForms(items=[game.to_gamelistform() for game in games])


    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Return all scores"""
        return ScoreForms(items=[score.to_form() for score in Score.query()])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=ScoreForms,
                      path='scores/user/{user_name}',
                      name='get_user_scores',
                      http_method='GET')

    def get_user_scores(self, request):
        """Returns all of an individual User's scores"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        scores = Score.query(Score.user == user.key)
        return ScoreForms(items=[score.to_form() for score in scores])

    ## Add in get_high_scores
    @endpoints.method(request_message=GET_HIGH_SCORE_REQUEST,
                      response_message=ScoreForms,
                      path='high_scores',
                      name='get_high_scores',
                      http_method='GET')
    def get_high_scores(self, request):
        """Return high scores"""
        scores = Score.query(Score.won == True).order(Score.guesses)
        scores = scores.fetch(limit=request.limit);
        return ScoreForms(items=[score.to_form() for score in scores])

    ## Add in get_user_rankings
    @endpoints.method(response_message=UserRankForms,
                      path='user_rankings',
                      name='get_user_rankings',
                      http_method='GET')
    def get_user_rankings(self, request):
        """Return User Rankings"""
        ## For each user, calculate their win/loss ratio
        ## use the average number of guesses per game as tiebreaker
        users = User.query()
        user_stats = []
        #old_user_stats = []
        for u in users:
          ## sum # wins and # games completed
          ## Need table like : user, rank, wins, totalgames, # guesses
          scores = Score.query(Score.user == u.key).fetch()
          ## how do we say cycle through scores table
          if scores:
            tot_games = len(scores) # i think this is right, test
            tot_wins = sum([1 if score.won == True else 0 for score in scores])
            tot_guesses = sum([score.guesses for score in scores])
          #user_stats.append([u.name, tot_games, tot_wins, tot_guesses])
          #old_user_stats.append([u.name, tot_games, tot_wins, tot_guesses])
          user_stats.append([u.name, 100*(tot_wins/float(tot_games)), round((tot_guesses/float(tot_games)),3)]) 
          # re-order by desc win/loss ratio
          user_stats = sorted(user_stats, key=lambda x: x[1], reverse=True)
        return UserRankForms(items=[UserRankForm(user=a[0],
            ratio=a[1]) for a in user_stats])

    ## Add in get_game_history
    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameHistoryForm,
                      path='game_history',
                      name='get_game_history',
                      http_method='GET')
    def get_game_history(self, request):
        """Return Game History"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        #if game:
        #    return game.to_form('Time to make a move!')
        #else:
        #    raise endpoints.NotFoundException('Game not found!')
        #TODO clean up how history is returned (do item thing)
        return GameHistoryForm(history=game.history)
        #return StringMessage(message='XX')

    @endpoints.method(response_message=StringMessage,
                      path='games/average_attempts',
                      name='get_average_attempts_remaining',
                      http_method='GET')
    def get_average_attempts(self, request):
        """Get the cached average moves remaining"""
        return StringMessage(message=memcache.get(MEMCACHE_MOVES_REMAINING) or '')

    @staticmethod
    def _cache_average_attempts():
        """Populates memcache with the average moves remaining of Games"""
        games = Game.query(Game.game_over == False).fetch()
        if games:
            count = len(games)
            total_attempts_remaining = sum([game.attempts_remaining
                                        for game in games])
            average = float(total_attempts_remaining)/count
            memcache.set(MEMCACHE_MOVES_REMAINING,
                         'The average moves remaining is {:.2f}'.format(average))


api = endpoints.api_server([HangmanApi])