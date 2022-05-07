import logging
import numpy as np

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

    def format_win(self):
        g = self.guesses[self.word]
        return f':confetti_ball: {g["by"]} got the correct word `{self.word}`'

    def format_top(self, n):
        lines = [self.format_guess(guess) for guess in self.top()[:n]]
        text = "\n".join(lines)
        return f"```{text} ```"

    def format_guess(self, guess):
        def circle(percentile):
            if percentile > 990:
                return "\N{large red circle}"
            elif percentile > 900:
                return "\N{large orange circle}"
            elif percentile > 750:
                return "\N{large yellow circle}"
            elif percentile > 500:
                return "\N{large green circle}"
            else:
                return "\N{large blue circle}"

        g = self.guesses[guess]
        if "percentile" in g:
            p = g["percentile"]
            percentile = f'{p}{circle(int(p))}'
        elif g["similarity"] >= self.story["rest"]:
            percentile = "????\N{black question mark ornament}"
        else:
            percentile = "cold\N{snowflake}"

        s = g["similarity"] - self.story["rest"]
        s = s * 0.7 / (self.story["top"] - self.story["rest"])
        s = s + 0.2

        similarity = round(100 * s, 2)
        by = str(g["by"])[:6]
        return f"{guess:15} {percentile:>5} {similarity:6} {by:>6}"
