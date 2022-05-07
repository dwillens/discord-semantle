import aiohttp
import argparse
import database
import discord
import game
import json
import logging
import numpy as np
import random
import re
import shelve

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiscordBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.filter = re.compile("[^a-zA-Z]")

        with open("secretwords.json") as f:
            self.words = json.loads(f.read())

        self.games = shelve.open("play_semantle")

    async def close(self):
        self.games.close()
        await super().close()

    async def on_ready(self):
        logger.info(f"We have logged in as {self.user}")

    async def on_message(self, message):
        if message.author == self.user:
            pass

        elif not "semantle" in message.channel.name:
            pass

        else:
            if not str(message.channel.id) in self.games:
                word = random.choice(self.words)

                result = await database.result(word, word)
                story = await database.story(word)

                self.games[str(message.channel.id)] = game.GameState(word, result, story)
                self.games.sync()

                logger.debug(
                    f"{message.channel}({str(message.channel.id)})'s' word is {word}"
                )

            if message.content.startswith("!new"):
                await self.process_new(message)

            elif message.content.startswith("!hint"):
                await self.process_hint(message)

            elif message.content.startswith("!guess"):
                guess = self.filter.sub("", message.content[7:])
                await self.process_guess(message, str(message.author), guess)

            elif message.content.startswith("$"):
                guess = self.filter.sub("", message.content[1:])
                await self.process_guess(message, str(message.author), guess)

            elif message.content.startswith("!top"):
                try:
                    n = int(message.content.split(" ")[1])
                except:
                    n = 10

                await self.process_top(message, n)

    async def process_new(self, message):
        game = self.games[str(message.channel.id)]

        await message.channel.send(game.format_top(20))
        await message.channel.send(f"old word was {game.word}. choosing a new word")

        del self.games[str(message.channel.id)]
        self.games.sync()

    async def process_hint(self, message):
        game = self.games[str(message.channel.id)]

        n = game.hint()
        hint = await database.nth_nearby(game.word, n)

        await self.process_guess(message, "hint", hint)

    async def process_top(self, message, n):
        game = self.games[str(message.channel.id)]
        await message.channel.send(game.format_top(n))

    async def process_guess(self, message, author, guess):
        game = self.games[str(message.channel.id)]
        try:
            if not game.is_guessed(guess):
                result = await database.result(game.word, guess)

            game = self.games[str(message.channel.id)]

            if not game.is_guessed(guess):
                game.add_guess(guess, result)

            game.maybe_add_author(guess, author)

            self.games[str(message.channel.id)] = game
            self.games.sync()

            await message.channel.send(f"```{game.format_guess(guess)} ```")

            if game.is_win(guess):
                await message.channel.send(game.format_win())

        except json.decoder.JSONDecodeError:
            await message.channel.send(f"{guess} is invalid")


parser = argparse.ArgumentParser(description="Semantle bot")
parser.add_argument("-d", "--debug", action="store_true")
parser.add_argument("-t", "--token")

args = parser.parse_args()

if args.debug:
    logger.setLevel(logging.DEBUG)

client = DiscordBot(intents=discord.Intents.default())

client.run(args.token)
