import aiohttp
import json
import numpy as np


ROOT_URL = "http://semantle.com"

async def story(word):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{ROOT_URL}/similarity/{word}"
        ) as response:
            text = await response.text()
            result = json.loads(text)
            return result

async def result(word, guess):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{ROOT_URL}/model2/{word}/{guess}"
        ) as response:
            text = await response.text()
            result = json.loads(text)
            result["vec"] = np.array(result["vec"])
            return result

async def nth_nearby(word, n):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{ROOT_URL}/nth_nearby/{word}/{n}"
        ) as response:
            text = await response.text()
            result = json.loads(text)
            return result
