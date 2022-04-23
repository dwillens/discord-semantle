import aiohttp
import argparse
import discord
import json
import logging
import numpy as np
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlaySemantle(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        with open("words.txt") as f:
            self.words = [l.strip() for l in f.readlines()]

        self.choose_new_word()

        with open("words_alpha.txt") as f:
            self.valid = [l.strip() for l in f.readlines()]

    def choose_new_word(self):
        self.word = self.words[random.randrange(len(self.words))]
        self.guesses = dict()
        self.top = dict()
        logger.debug(f"{self.word}")

    async def on_ready(self):
        logger.info(f"We have logged in as {self.user}")

    async def on_message(self, message):
        if message.author == self.user:
            pass

        elif not "semantle" in message.channel.name:
            pass

        elif message.content.startswith("!new"):
            await message.channel.send(self.format_top(20))
            await message.channel.send(f"old word was {self.word}. choosing a new word")
            self.choose_new_word()

        elif message.content.startswith("!guess"):
            if not self.word in self.guesses:
                self.guesses[self.word] = await self.result(self.word)
                self.guesses[self.word]["similarity"] = 100.0

            guess = message.content.split(" ")[1]
            try:
                await self.do_guess(message, guess)
            except ValueError:
                await message.channel.send(f"{guess} is invalid")
            except json.decoder.JSONDecodeError:
                await message.channel.send(f"{guess} is invalid")

        elif message.content.startswith("!top"):
            n = 10
            try:
                n = int(message.content.split(" ")[1])
            except:
                pass

            await message.channel.send(self.format_top(n))

    def format_top(self, n):
        lines = [
            self.format_guess(guess)
            for (_, guess) in reversed(sorted(self.top.items())[-n:])
        ]
        text = "\n".join(lines)
        return f"```{text}```"

    async def do_guess(self, message, guess):
        if not guess in self.valid:
            raise ValueError('not in list')

        if not guess in self.guesses:
            self.guesses[guess] = await self.result(guess)

            wa = self.guesses[self.word]["array"]
            ga = self.guesses[guess]["array"]
            sim = 100 * np.dot(wa, ga) / (np.linalg.norm(wa) * np.linalg.norm(ga))
            self.guesses[guess]["similarity"] = sim
            self.top[sim] = guess

        if not "by" in self.guesses[guess]:
            self.guesses[guess]["by"] = message.author

        await message.channel.send(f"```{self.format_guess(guess)}```")

        if self.word == guess:
            self.top[100.0] = guess
            g = self.guesses[guess]
            await message.channel.send(
                f':confetti_ball: {g["by"]} got the correct word `{self.word}`'
            )

    def format_guess(self, guess):
        g = self.guesses[guess]
        if "percentile" in g:
            percentile = f'{g["percentile"]}/1000'
        else:
            percentile = "cold"

        similarity = round(g["similarity"], 3)
        by = str(g["by"])
        return f"{guess:16} {percentile:10} {similarity:6} {by:>20}"

    async def result(self, guess):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"http://semantle.novalis.org/model2/{self.word}/{guess}"
            ) as response:
                text = await response.text()
                result = json.loads(text)
                result["array"] = np.array(result["vec"])
                return result


parser = argparse.ArgumentParser(description="Semantle bot")
parser.add_argument("-d", "--debug", action="store_true")
parser.add_argument("-t", "--token")

args = parser.parse_args()

if args.debug:
    logger.setLevel(logging.DEBUG)

client = PlaySemantle(intents=discord.Intents.default())

client.run(args.token)
