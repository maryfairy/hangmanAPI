# hangmanAPI
# some directions copied from Guess A Number API

Instructions for playing the game 
## Set-Up Instructions:
1.  Update the value of application in app.yaml to the app ID you have registered
 in the App Engine admin console and would like to use to host your instance of this sample.
1.  Run the app with the devserver using dev_appserver.py hangmanAPI/DIR, and ensure it's
 running by visiting the API Explorer - by default localhost:8080/_ah/api/explorer.
1.  (Optional) Generate your client library(ies) with the endpoints tool.
 Deploy your application.
 
 
 
##Game Description:
Hangman is a game requiring the user to guess a letter (or word) for a randomly generated word. The user has 12 attempts to guess the letters. User must guess the word at the end, not the final letter.

To Play:
- create_user and enter a username
- new_game endpoint using the username entered
- Response will reveal a urlsafe_key. Copy this key in order to make moves.
- enter the urlsafe key into the urlsafe_game_key field.
- Type a letter into the guess_letter or type word into guess_word field.

##Files Included:
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - main.py: Handler for taskqueue handler.
 - models.py: Entity and message definitions including helper methods.
 - utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.
 - wordlist.txt: list of 100 random words for hangman game

##New Endpoints Included
 - **get_user_games**
    - Path: 'games/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: GameListForm with list of users game keys.
    - Description: lists users' game keys for given user name

 - **cancel_game**
    - Path: 'game/cancel/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: String response based on urlsafe_game_key.
    - Description: Will delete a game only if in progress.

 - **get_high_scores**
    - Path: 'high_scores'
    - Method: GET
    - Parameters: limit (optional)
    - Returns: ScoreForm with list of highest scores.
    - Description: Will return list of highest scores based on games with the lowest amount of guesses needed before game was won.

 - **get_user_games**
    - Path: 'user_rankings'
    - Method: GET
    - Parameters: user_name
    - Returns: GameListForm with list of users game keys.
    - Description: lists users' game keys for given user name

 - **get_user_rankings**
    - Path: 'games/user/{user_name}'
    - Method: GET
    - Parameters: 
    - Returns: UserRankForms with list of users and win/totalgames ratio.
    - Description: Lists users win percentage by highest percentage to lowers. Tie breakers / rank order decided by average number of guesses per game.

 - **get_game_history**
    - Path: 'game_history'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameHistoryForm with string of all actions completed in make_move
    - Description: Returns list of actions under make_move

##Endpoints Included (from Guess-A-Number):
 - **create_user**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name, email (optional)
    - Returns: Message confirming creation of the User.
    - Description: Creates a new User. user_name provided must be unique. Will 
    raise a ConflictException if a User with that user_name already exists.
    
 - **new_game**
    - Path: 'game'
    - Method: POST
    - Parameters: user_name, min, max, attempts
    - Returns: GameForm with initial game state.
    - Description: Creates a new Game. user_name provided must correspond to an
    existing user - will raise a NotFoundException if not. Min must be less than
    max. Also adds a task to a task queue to update the average moves remaining
    for active games.
     
 - **get_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with current game state.
    - Description: Returns the current state of a game.
    
 - **make_move**
    - Path: 'game/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key, guess
    - Returns: GameForm with new game state.
    - Description: Accepts a 'guess' and returns the updated state of the game.
    If this causes a game to end, a corresponding Score entity will be created.
    
 - **get_scores**
    - Path: 'scores'
    - Method: GET
    - Parameters: None
    - Returns: ScoreForms.
    - Description: Returns all Scores in the database (unordered).
    
 - **get_user_scores**
    - Path: 'scores/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: ScoreForms. 
    - Description: Returns all Scores recorded by the provided player (unordered).
    Will raise a NotFoundException if the User does not exist.
    
 - **get_active_game_count**
    - Path: 'games/active'
    - Method: GET
    - Parameters: None
    - Returns: StringMessage
    - Description: Gets the average number of attempts remaining for all games
    from a previously cached memcache key.

##Models Included:
 - **User**
    - Stores unique user_name and (optional) email address.
    
 - **Game**
    - Stores unique game states. Associated with User model via KeyProperty.
    
 - **Score**
    - Records completed games. Associated with Users model via KeyProperty.
    
##Forms Included:
 - **GameForm**
    - Representation of a Game's state (urlsafe_key, attempts_remaining,
    game_over flag, message, user_name).
 - **NewGameForm**
    - Used to create a new game (user_name, min, max, attempts)
 - **MakeMoveForm**
    - Inbound make move form (guess).
 - **ScoreForm**
    - Representation of a completed game's Score (user_name, date, won flag,
    guesses).
 - **ScoreForms**
    - Multiple ScoreForm container.
 - **StringMessage**
    - General purpose String container.

 - **GameListForm**
    - Representation of User's game (urlsafe_key).
 - **GameListsForm*
    - Representation of User's game (urlsafe_key).
 - **MakeMoveForm**
    - Inbound make move form (guess).
 - **UserRankForm**
    - Representation of list of users rank ordered by win percentage.
 - **GameHistoryForm**
    - Representation of string history of actions in a unique game.

