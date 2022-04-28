import aiohttp
import argparse
import discord
import json
import logging
import numpy as np
import random
import re
import shelve

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GameState:
    def __init__(self, word, result, story, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.word = word

        result["similarity"] = 1.0
        self.guesses = {word: result}

        self.story = story

    def add_guess(self, guess, result):
        self.guesses[guess] = result

        wa = self.guesses[self.word]["vec"]
        ga = self.guesses[guess]["vec"]
        self.guesses[guess]["similarity"] = np.dot(wa, ga) / (
            np.linalg.norm(wa) * np.linalg.norm(ga)
        )

    def maybe_add_author(self, guess, author):
        if not "by" in self.guesses[guess]:
            self.guesses[guess]["by"] = author

    def top(self):
        by_sim = [(v["similarity"], k) for (k, v) in self.guesses.items() if "by" in v]
        return [k for (_, k) in reversed(sorted(by_sim))]

    def hint(self):
        top = [self.guesses[guess] for guess in self.top()]

        if not top:
            return 1
        elif not "percentile" in top[0]:
            return 1
        elif 999 <= top[0]["percentile"]:
            n = top[0]["percentile"] - 1
            for g in top[1:]:
                if not "percentile" in g:
                    break
                elif n > g["percentile"]:
                    break
                else:
                    n = g["percentile"] - 1
            return n
        else:
            return int((1000 + top[0]["percentile"]) / 2)

    def is_guessed(self, guess):
        return guess in self.guesses

    def is_win(self, guess):
        return self.word == guess

    def format_win(self, guess):
        g = self.guesses[guess]
        return f':confetti_ball: {g["by"]} got the correct word `{self.word}`'

    def format_top(self, n):
        lines = [self.format_guess(guess) for guess in self.top()[:n]]
        text = "\n".join(lines)
        return f"```{text} ```"

    def format_guess(self, guess):
        g = self.guesses[guess]
        if "percentile" in g:
            percentile = f'{g["percentile"]}'
        elif g["similarity"] >= self.story["rest"]:
            percentile = "????"
        else:
            percentile = "cold"

        s = g["similarity"] - self.story["rest"]
        s = s * 0.7 / (self.story["top"] - self.story["rest"])
        s = s + 0.2

        similarity = round(100 * s, 2)
        by = str(g["by"])[:8]
        return f"{guess:15} {percentile:>4} {similarity:6} {by:>8}"


class PlaySemantle(discord.Client):
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
                word = self.words[random.randrange(len(self.words))]

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
                await message.channel.send(game.format_win(guess))

        except json.decoder.JSONDecodeError:
            await message.channel.send(f"{guess} is invalid")

    async def story(self, word):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"http://semantle.novalis.org/similarity/{word}"
            ) as response:
                text = await response.text()
                result = json.loads(text)
                return result

    async def result(self, word, guess):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"http://semantle.novalis.org/model2/{word}/{guess}"
            ) as response:
                text = await response.text()
                result = json.loads(text)
                result["vec"] = np.array(result["vec"])
                return result

    async def nth_nearby(self, word, n):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"http://semantle.novalis.org/nth_nearby/{word}/{n}"
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

client = PlaySemantle(intents=discord.Intents.default())

client.run(args.token)
