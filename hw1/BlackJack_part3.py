import gym
from gym import spaces
from gym.utils import seeding

# 1 = Ace, 2-10 = Number cards, Jack/Queen/King = 10
deck = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10] * 4

matcher = {
    2: 0.5,
    3: 1,
    4: 1,
    5: 1.5,
    6: 1,
    7: 0.5,
    8: 0,
    9: -0.5,
    10: -1,
    1: -1
}


def cmp(a, b):
    return float(a > b) - float(a < b)


def usable_ace(hand):  # Does this hand have a usable ace?
    return 1 in hand and sum(hand) + 10 <= 21


def sum_hand(hand):  # Return current hand total
    if usable_ace(hand):
        return sum(hand) + 10
    return sum(hand)


def is_bust(hand):  # Is this hand a bust?
    return sum_hand(hand) > 21


def score(hand):  # What is the score of this hand (0 if bust)
    return 0 if is_bust(hand) else sum_hand(hand)


def is_natural(hand):  # Is this hand a natural blackjack?
    return sorted(hand) == [1, 10]


class BlackJack(type(gym.make('Blackjack-v0'))):
    def __init__(self, natural=False, sab=False):
        self.start = True
        self.deck = deck.copy()
        self.card_score = 0
        super().__init__(natural)
        self.observation_space = spaces.Tuple(
            (spaces.Discrete(32), spaces.Discrete(11), spaces.Discrete(2), spaces.Discrete(2), spaces.Discrete(93))
        )
        self.action_space = spaces.Discrete(3)
        self.sab = sab
        self._hard_reset()

    def step(self, action):
        assert self.action_space.contains(action)
        if action == 2:  # double
            self.player.append(self.draw_card(self.np_random))
            done = True
            self.card_score += matcher[self.dealer[1]]
            if is_bust(self.player):
                reward = -2.0
            else:
                while sum_hand(self.dealer) < 17:
                    self.dealer.append(self.draw_card(self.np_random))
                reward = 2 * cmp(score(self.player), score(self.dealer))
            if not self.start:
                reward = -100  # сделал дабл не на первый ход = избили в казино
        elif action:  # hit: add a card to players hand and return
            self.player.append(self.draw_card(self.np_random))
            if is_bust(self.player):
                done = True
                self.card_score += matcher[self.dealer[1]]
                reward = -1.0
            else:
                done = False
                reward = 0.0
        else:  # stick: play out the dealers hand, and score
            done = True
            self.card_score += matcher[self.dealer[1]]  # в конце игры знаем все карты
            while sum_hand(self.dealer) < 17:
                self.dealer.append(self.draw_card(self.np_random))
            reward = cmp(score(self.player), score(self.dealer))
            if self.sab and is_natural(self.player) and not is_natural(self.dealer):
                # Player automatically wins. Rules consistent with S&B
                reward = 1.0
            elif (
                    not self.sab
                    and self.natural
                    and is_natural(self.player)
                    and reward == 1.0
            ):
                # Natural gives extra points, but doesn't autowin. Legacy implementation
                reward = 1.5
        self.start = False
        return self._get_obs(), reward, done, {}

    def _get_obs(self):
        return sum_hand(self.player), self.dealer[0], usable_ace(self.player), self.start, int(2*self.card_score)

    def _hard_reset(self):
        self.card_score = 0
        self.deck = deck.copy()
        self.dealer = []
        self.player = []

    def reset(self):
        if len(self.deck) <= 15:
            self.card_score = 0
            self.deck = deck.copy()
        self.dealer = self.draw_hand(self.np_random)
        self.card_score -= matcher[self.dealer[-1]]  # мы не знаем одну карту дилера в течение игры
        self.player = self.draw_hand(self.np_random)
        self.start = True
        return self._get_obs()

    def draw_card(self, np_random):
        num = np_random.randint(0, len(self.deck))
        card = self.deck.pop(num)
        self.card_score += matcher[card]
        return int(card)

    def draw_hand(self, np_random):
        return [self.draw_card(np_random), self.draw_card(np_random)]

    def get_deck(self):
        return self.deck.copy()