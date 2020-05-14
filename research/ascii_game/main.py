import copy
import random
from typing import Dict, List

import joblib
import numpy as np
from blessed import Terminal

from pluribus.games.short_deck.state import new_game, ShortDeckPokerState
from card_collection import CardCollection
from player import Player


def _compute_header_str(state: ShortDeckPokerState) -> str:
    if state.is_terminal:
        winner_i = None
        best_delta = -np.inf
        for player_i, chips_delta in state.payout.items():
            if chips_delta > best_delta:
                best_delta = chips_delta
                winner_i = player_i
        winner = state.players[winner_i]
        header_str = f"{state.betting_stage} - {winner.name} wins {best_delta} chips"
    else:
        header_str = state.betting_stage
    return header_str


def print_header(state: ShortDeckPokerState):
    header_str = _compute_header_str(state)
    print(term.center(term.yellow(header_str)))
    print()
    print(f"{term.width * '-'}")
    print()


def print_footer(selected_action_i: int, legal_actions: List[str]):
    print()
    print(f"{term.width * '-'}")
    print()
    actions = []
    for action_i in range(len(legal_actions)):
        action = copy.deepcopy(legal_actions[action_i])
        if action_i == selected_action_i:
            action = term.blink_bold_orangered(action)
        actions.append(action)
    print(term.center("    ".join(actions)))


def print_table(players: List[Player], public_cards: CardCollection):
    for line in players[2].lines:
        print(term.center(line))
    for line_a, line_b in zip(players[1].lines, public_cards.lines):
        print(line_a + " " + line_b)
    for line in players[0].lines:
        print(term.center(line))


term = Terminal()

table_position_to_orientation: Dict[int, str] = {0: "top", 1: "right", 2: "bottom"}
n_players: int = 3
pickle_dir: str = "/home/tollie/dev/pluribus/research/blueprint_algo"
state: ShortDeckPokerState = new_game(n_players, pickle_dir=pickle_dir)
is_bot: List[bool] = [False, True, True]
selected_action_i: int = 0
agent: str = "offline"
strategy_path: str = (
    "/home/tollie/dev/pluribus/research/blueprint_algo/offline_strategy_285800.gz"
)
if agent in {"offline", "online"}:
    offline_strategy = joblib.load(strategy_path)
with term.cbreak(), term.hidden_cursor():
    while True:
        players: List[Player] = []
        for player_i, state_player in enumerate(state.players):
            ascii_player = Player(
                *state_player.cards,
                name=state_player.name,
                term=term,
                info_position=table_position_to_orientation[player_i],
                hide_cards=is_bot[player_i] and not state.is_terminal,
                folded=not state_player.is_active,
                is_turn=player_i == state.player_i,
                chips_in_pot=state_player.n_bet_chips,
                chips_in_bank=state_player.n_chips,
                is_small_blind=state_player.is_small_blind,
                is_big_blind=state_player.is_big_blind,
                is_dealer=state_player.is_dealer,
            )
            players.append(ascii_player)
        public_cards = CardCollection(*state.community_cards)
        if state.is_terminal:
            legal_actions = ["quit", "new game"]
        else:
            legal_actions = [] if is_bot[state.player_i] else state.legal_actions
        print(term.home + term.white + term.clear)
        print_header(state)
        print_table(players, public_cards)
        print_footer(selected_action_i, legal_actions)
        if not is_bot[state.player_i] or state.is_terminal:
            key = term.inkey(timeout=None)
            if key.name == "KEY_LEFT":
                selected_action_i -= 1
                if selected_action_i < 0:
                    selected_action_i = len(legal_actions) - 1
            elif key.name == "KEY_RIGHT":
                selected_action_i = (selected_action_i + 1) % len(legal_actions)
            elif key.name == "KEY_ENTER":
                action = legal_actions[selected_action_i]
                selected_action_i = 0
                if action == "quit":
                    break
                elif action == "new game":
                    state: ShortDeckPokerState = new_game(
                        n_players, state.info_set_lut,
                    )
                else:
                    state: ShortDeckPokerState = state.apply_action(action)
        else:
            if agent == "random":
                action = random.choice(state.legal_actions)
            elif agent == "offline":
                default_strategy = {
                    action: 1 / len(state.legal_actions)
                    for action in state.legal_actions
                }
                this_state_strategy = offline_strategy.get(
                    state.info_set, default_strategy
                )
                actions = list(this_state_strategy.keys())
                probabilties = list(this_state_strategy.values())
                action = np.random.choice(actions, p=probabilties)
            state: ShortDeckPokerState = state.apply_action(action)
