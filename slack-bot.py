import aiohttp
import argparse
import discord
from game import GameState
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

                result = await self.result(word, word)
                story = await self.story(word)

                self.games[str(message.channel.id)] = GameState(word, result, story)
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
        hint = await self.nth_nearby(game.word, n)

        await self.process_guess(message, "hint", hint)

    async def process_top(self, message, n):
        game = self.games[str(message.channel.id)]
        await message.channel.send(game.format_top(n))

    async def process_guess(self, message, author, guess):
        game = self.games[str(message.channel.id)]
        try:
            if not game.is_guessed(guess):
                result = await self.result(game.word, guess)

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

    async def story(self, word):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"http://semantle.com/similarity/{word}"
            ) as response:
                text = await response.text()
                result = json.loads(text)
                return result

    async def result(self, word, guess):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"http://semantle.com/model2/{word}/{guess}"
            ) as response:
                text = await response.text()
                result = json.loads(text)
                result["vec"] = np.array(result["vec"])
                return result

    async def nth_nearby(self, word, n):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"http://semantle.com/nth_nearby/{word}/{n}"
            ) as response:
                text = await response.text()
                result = json.loads(text)
                return result


parser = argparse.ArgumentParser(description="Semantle bot")
parser.add_argument("-d", "--debug", action="store_true")
parser.add_argument("-t", "--token")

args = parser.parse_args()

if args.debug:
    logger.setLevel(logging.DEBUG)

client = DiscordBot(intents=discord.Intents.default())

client.run(args.token)
