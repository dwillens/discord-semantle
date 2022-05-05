# discord-semantle
discord semantle gamemaster

## how to set up

### invite link
https://discord.com/api/oauth2/authorize?client_id=966183123400400946&permissions=2048&scope=applications.commands%20bot

### channel setup
- the bot will only respond to messages in channels that include `semantle` in their name, like `#semantle` or `#play-semantle`

- each channel has a separate game state

## differences from http://semantle.novalis.org
- guess similarity is scaled s.t. the 1000th closest word has similarity 20.0 and the closest word has similarity 90.0

## commands

### `!guess <WORD>`
make a guess in the game; the bot will respond with the score for the word or phrase

### `$<WORD>`
shorthand for `!guess`

### `!top <N>`
the bot will respond with a list of the top N guesses and their scores; defaults to `10` if no argument is specified

### `!hint`
the bot will respond with a hint halfway between the best word so far and the answer

### `!new`
the bot will report the top guesses and answer for the previous game, then select a new word
