"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb


class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email =ndb.StringProperty()


class Game(ndb.Model):
    """Game object"""
    ###target = ndb.IntegerProperty(required=True)
    ## Make target a string property, not required each time
    target_word = ndb.StringProperty(required=True)
    guess_word = ndb.StringProperty()
    # add in a guess attempt, must be one-letter in length
    ## TODO: create a check that the string entered length 1
    guess_letter = ndb.StringProperty()
    guessed_letters = ndb.StringProperty()
    attempts_allowed = ndb.IntegerProperty(required=True)
    attempts_remaining = ndb.IntegerProperty(required=True, default=12)
    ## add in game history tracker
    history = ndb.StringProperty()
    game_over = ndb.BooleanProperty(required=True, default=False)
    user = ndb.KeyProperty(required=True, kind='User')

    @classmethod
    def new_game(cls, user, min, max, attempts):
        """Creates and returns a new game"""
        if max < min:
            raise ValueError('Maximum must be greater than minimum')
        game = Game(user=user,
                    # target_word chooses random word from txt file
                    target_word = random.choice([line.strip() for line in open('wordlist.txt')]),
                    attempts_allowed=attempts,
                    attempts_remaining=attempts,
                    game_over=False)
        game.put()
        return game

    def to_form(self, message):
        """Returns a GameForm representation of the Game"""
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.user.get().name
        form.attempts_remaining = self.attempts_remaining
        form.game_over = self.game_over
        form.message = message
        return form

    def to_gamelistform(self):
        """Returns a GameListForm representation of the Game"""
        form = GameListForm()
        form.urlsafe_key = self.key.urlsafe()
        return form

    def end_game(self, won=False):
        """Ends the game - if won is True, the player won. - if won is False,
        the player lost."""
        self.game_over = True
        self.put()
        # measure the # of remaining attempts as score
        # Add the game to the score 'board'
        score = Score(user=self.user, date=date.today(), won=won, 
                    guesses=self.attempts_allowed - self.attempts_remaining,
                    )
        
        score.put()


class Score(ndb.Model):
    """Score object"""
    user = ndb.KeyProperty(required=True, kind='User')
    date = ndb.DateProperty(required=True)
    won = ndb.BooleanProperty(required=True)
    guesses = ndb.IntegerProperty(required=True)
    def to_form(self):
        return ScoreForm(user_name=self.user.get().name, won=self.won,
                         date=str(self.date), guesses=self.guesses)

class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    attempts_remaining = messages.IntegerField(2, required=True)
    game_over = messages.BooleanField(3, required=True)
    message = messages.StringField(4, required=True)
    user_name = messages.StringField(5, required=True)

## add in a form to show all games
class GameListForm(messages.Message):
    """Pull active game for the user"""
    urlsafe_key = messages.StringField(1, required=True)

class GameListForms(messages.Message):
    """Return multiple game entries."""
    items = messages.MessageField(GameListForm, 1, repeated=True)

class NewGameForm(messages.Message):
    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)
    min = messages.IntegerField(2, default=1)
    max = messages.IntegerField(3, default=10)
    attempts = messages.IntegerField(4, default=12)

class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    guess_letter = messages.StringField(1)
    guess_word = messages.StringField(2)

class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    user_name = messages.StringField(1, required=True)
    date = messages.StringField(2, required=True)
    won = messages.BooleanField(3, required=True)
    guesses = messages.IntegerField(4, required=True)

class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)

class UserRankForm(messages.Message):
    """User Ranking Information"""
    user = messages.StringField(1, required=True)
    ratio = messages.FloatField(2, required=True)
    
class UserRankForms(messages.Message):
    """Return User Ranking List"""
    items = messages.MessageField(UserRankForm, 1, repeated=True)

class GameHistoryForm(messages.Message):
    """Return History of a Game"""
    history = messages.StringField(1, required=True)

class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)
