# discord-semantle
Discord Semantle DM

## how to set up

### invite link
https://discord.com/api/oauth2/authorize?client_id=966183123400400946&permissions=2048&scope=applications.commands%20bot

### channel setup
- The bot will only respond to messages in channels named `#semantle` (or channels that include `semantle` in their name.

- Each channel has a separate game state.

## differences from http://semantle.novalis.org
- Guess similarity is scaled s.t. the 1000th closest word has similarity 20.0 and the closest word has similarity 90.0.

## commands

### `!guess <WORD>`
Make a guess in the game. The bot will respond with the score for the word or phrase.

### `$<WORD>`
Shorthand for `!guess`.

### `!top <N>`
The bot will respond with a list of the top N guesses and their scores. Defaults to `10` if no argument is specified.

### `!hint`
The bot will respond with a hint halfway between the best word so far and the answer.

### `!new`
The bot will report the top guesses and answer for the previous game, then select a new word.
