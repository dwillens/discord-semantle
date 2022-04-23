import aiohttp
import discord
import json
import numpy as np
import random


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

    async def on_ready(self):
        print(f"We have logged in as {self.user}")

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content.startswith("!new"):
            old = self.word
            self.choose_new_word()
            await message.channel.send(f"old word was {old}. choosing a new word")

        elif message.content.startswith("!guess"):
            guess = message.content.split(" ")[1]

            if not guess in self.valid:
                await message.channel.send(f"{guess} is invalid")
            else:
                if not self.word in self.guesses:
                    self.guesses[self.word] = await self.result(self.word)
                    self.guesses[self.word]["similarity"] = 100.0

                if not guess in self.guesses:
                    self.guesses[guess] = await self.result(guess)
                    self.guesses[guess]["by"] = message.author

                    wa = self.guesses[self.word]["array"]
                    ga = self.guesses[guess]["array"]
                    sim = (
                        100 * np.dot(wa, ga) / (np.linalg.norm(wa) * np.linalg.norm(ga))
                    )
                    self.guesses[guess]["similarity"] = sim
                    self.top[sim] = guess

                await message.channel.send(self.format_guess(guess))

                if self.word == guess:
                    self.top[100.0] = guess
                    g = self.guesses[guess]
                    await message.channel.send(
                        f'{g["by"]} got the correct word {self.word}'
                    )

        elif message.content.startswith("!top"):
            n = 10
            try:
                n = int(message.content.split(" ")[1])
            except:
                pass

            for (_, guess) in reversed(sorted(self.top.items())[-n:]):
                g = self.guesses[guess]
                await message.channel.send(self.format_guess(guess))

    def format_guess(self, guess):
        g = self.guesses[guess]
        if "percentile" in g:
            percentile = f'{g["percentile"]}/1000'
        else:
            percentile = "cold"

        return f'{guess} {percentile} {round(g["similarity"], 3)} {g["by"]}'

    async def result(self, guess):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"http://semantle.novalis.org/model2/{self.word}/{guess}"
            ) as response:
                text = await response.text()
                result = json.loads(text)
                result["array"] = np.array(result["vec"])
                return result


client = PlaySemantle(intents=discord.Intents.default())

client.run(sys.argv[1])
