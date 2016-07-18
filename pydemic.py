from citymap import citymap
from random import shuffle

class Game(object):
    """
    Instantiate this class to play the game.
    game = Game(num_players=4)
    game.game_setup()
    game.turn.treat_disease("blue")
    game.next_turn()
    """

    def __init__(self, num_players, num_epidemic_cards):
        self.players = [Player(game=self) for i in range(num_players)]
        self.num_epidemic_cards = num_epidemic_cards

        self.turn_count = 0
        self.turn = None
        self.infection_turn = None

        self.cities = {city_name: City(game=self, name=city_name, color=citymap.node[city_name]['color'])
                       for city_name in citymap}

        self.infection_deck = InfectionDeck(game=self)

        self.player_deck = [city_name for city_name in citymap]
        self.player_discard_pile = []

        self.infection_track = 1
        self.outbreaks = 0
        self.outbreak_chain = []  # used to keep track of chain reaction outbraks

        self.cube_supply = {"blue": 24,
            "yellow": 24,
            "black": 24,
            "red": 24}

        self.cured_diseases = []
        self.eradicated_diseases = []

        self.cities['atlanta'].has_research_station = True
        self.research_stations = 1

        self.lost = False

    def game_setup(self):
        "Run the non-deterministic aspects of game setup."

        shuffle(self.player_deck)
        cards_per_player = 6 - len(self.players)
        for player in self.players:
            player.hand.extend(self.player_deck[-cards_per_player:])
            del self.player_deck[-cards_per_player:]

        self.prepare_player_deck()

        shuffle(self.infection_deck.deck)
        for i in range(3):
            city = self.infection_deck.draw()
            city.infect()
            city.infect()
            city.infect()

        for i in range(3):
            city = self.infection_deck.draw()
            city.infect()
            city.infect()

        for i in range(3):
            city = self.infection_deck.draw()
            city.infect()

        self.next_turn()

    def prepare_player_deck(self):
        "Shuffle the Epidemic cards into the Player Deck."
        shuffle(self.player_deck)
        output = []
        sub_piles = [[] for i in range(self.num_epidemic_cards)]

        for i, city_name in enumerate(self.player_deck):
            sub_piles[i % self.num_epidemic_cards].append(city_name)

        for sub_pile in sub_piles:
            sub_pile.append("epidemic")
            shuffle(sub_pile)
            output.extend(sub_pile)

        output.reverse()  # so the smallest sub_pile is on the bottom of the stack
        self.player_deck = output

    def get_infection_rate(self):
        "Return the Infection Rate for the current index in the Infection Track."
        if self.infection_track < 4:
            return 2
        if self.infection_track < 6:
            return 3
        return 4

    def next_turn(self):
        "Start the next player's turn."
        if self.turn_count > 0 and not self.turn.ended:
            raise ValueError("Must end your turn before starting next turn.")
        if self.turn_count > 0 and not self.infection_turn.ended:
            raise ValueError("Must end the infection turn before starting next turn")
        self.turn_count += 1
        next_player_index = self.turn_count % len(self.players)
        next_player = self.players[next_player_index]
        self.turn = PlayerTurn(game=self, player=next_player)
        self.infection_turn = None
        print "Turn {}. Ready player {}".format(self.turn_count, next_player_index)

    def epidemic(self):
        "Execute the logic of an Epidemic card."
        # INCREASE
        self.infection_track += 1

        # INFECT
        target_city = self.infection_deck.draw(0)
        print "Epidemic in {}".format(target_city.name)
        cubes_present = target_city.cubes[target_city.color]
        if cubes_present == 0:
            for i in range(3):
                target_city.infect()
        else:
            for i in range(4 - cubes_present):
                target_city.infect()  # this will cause an outbreak.

        # INTENSIFY
        shuffle(self.infection_deck.discards)
        self.infection_deck.deck.extend(self.infection_deck.discards)
        del self.infection_deck.discards[:]

    def check_eradication(self, color):
        "Determine if a disease has been eradicated"
        if color not in self.cured_diseases:
            return False
        if self.cube_supply[color] < 24:
            return False
        self.eradicated_diseases.append(color)
        print "{} has been eradicated.".format(color)

    def remove_research_station(self, city_name):
        "Remove a research station from the board. This is not an action."
        city = self.cities[city_name]
        if not city.has_research_station:
            raise ValueError("Can't remove a research station from a city without one.")
        city.has_research_station = False
        self.research_stations -= 1

    def lose(self, reason):
        "Declare game loss for the specified reason."
        self.lost = True
        self.turn = None
        print "You have lost: {}".format(reason)

class Player(object):
    "Represents a player."
    def __init__(self, game):
        self.game = game
        self.hand = PlayerHand(player=self)
        self.city = "atlanta"  # all players start here.

    # TODO: def play_event_card(self, card)


class PlayerHand(list):
    "Represents a player's hand and discards to the game-wide Player Discard Pile."
    def __init__(self, player):
        self.player = player

    def discard(self, card):
        "Discard from your hand and add to Player Discard Pile."
        self.remove(card)
        self.player.game.player_discard_pile.append(card)

class PlayerTurn(object):
    """
    Manages single player's turn of actions. Player actions are methods
    of this class. The card-drawing and city-infecting steps are handled
    by InfectionTurn.
    """
    def __init__(self, game, player):
        self.game = game
        self.player = player
        self.actions = 4
        self.ended = False

    def raise_for_too_many_cards(self):
        "Raise an error if a player has more than seven cards."
        for i, player in enumerate(self.game.players):
            if len(player.hand) > 7:
                raise ValueError("Player {} must discard to 7 cards before continuing".format(i))

    def end(self):
        "Declare the end of the action phase of a turn and start the InfectionTurn."
        self.raise_for_too_many_cards()
        self.ended = True
        self.game.infection_turn = InfectionTurn(self.game, self.player)

    def action(method):
        "Apply common logic to actions with this decorator."
        def method_wrapper(*args, **kwargs):
            self = args[0]
            if self.ended:
                raise ValueError("Turn has ended. Run game.next_turn()")
            if self.actions == 0:
                raise ValueError("No more actions. End your turn.")
            self.raise_for_too_many_cards()

            try:
                method(*args, **kwargs)
            except Exception:
                raise
            else:
                self.actions -= 1

        return method_wrapper

    @action
    def skip(self):
        "Skip one action."
        pass

    @action
    def drive(self, target_city):
        "Drive or ferry to a neighboring city."
        if target_city not in citymap.neighbors(self.player.city):
            raise ValueError("Target city not adjacent to current city")
        self.player.city = target_city

    @action
    def direct_flight(self, target_city):
        "Play a card to fly directly to that city."
        if target_city not in self.player.hand:
            raise ValueError("Target city card not in player's hand")
        self.player.city = target_city
        self.player.hand.discard(target_city)

    @action
    def charter_flight(self, target_city):
        "Play the card matching your current city to fly anywhere."
        current_city = self.player.city
        if current_city not in self.player.hand:
            raise ValueError("Current city card not in player's hand")
        self.player.city = target_city
        self.player.hand.discard(current_city)

    @action
    def shuttle_flight(self, target_city):
        "Fly between two cities with reserach stations"
        current_city = self.player.city
        research_station_here = self.game.cities[current_city].has_research_station
        research_station_there = self.game.cities[target_city].has_research_station
        if not (research_station_here and research_station_there):
            raise ValueError("Both cities need a research station")
        self.player.city = target_city

    @action
    def build_research_station(self):
        "Build a research station in your current city."
        current_city = self.game.cities[self.player.city]
        if current_city.has_research_station:
            raise ValueError("There is already a research station here.")

        if current_city.name not in self.player.hand:
            raise ValueError("Current city card not in player's hand")

        if self.game.research_stations == 6:
            raise ValueError("Already 6 research stations on board, remove one with game.remove_research_station")

        current_city.has_research_station = True
        self.game.research_stations += 1

    @action
    def treat_disease(self, color):
        "Treat a specific disease in your current city."
        city = self.game.cities[self.player.city]
        if color in self.game.cured_diseases:
            while city.cubes[color] > 0:
                city.cubes[color] -= 1
                self.game.cube_supply[color] += 1
        else:
            city.cubes[color] -= 1
            self.game.cube_supply[color] += 1

        self.game.check_eradication(color)

    @action
    def share_knowledge(self, target_player):
        """
        Give or take the card that matches your current city from/to a player
        in that same city.
        """
        if self.player.city != target_player.city:
            raise ValueError("Both players must be in same city")

        if self.player.city in self.player.hand:
            self._transfer_card(self.player, target_player, self.player.city)
        elif self.player.city in target_player.hand:
            self._transfer_card(target_player, self.player, self.player.city)
        else:
            raise ValueError("Neither player has the card for the city they're in.")

    def _transfer_card(self, giver, recipient, card):
        giver.hand.remove(card)
        recipient.hand.append(card)

    @action
    def discover_cure(self, color, cities):
        "Discover a cure while at a research station by expending 5 cards of one color."
        if not self.game.cities[self.player.city].has_research_station:
            raise ValueError("Your city must have a research station to discover a cure")

        if len(cities) != 5:
            raise ValueError("Did not supply 5 cards.")

        for city in cities:
            if city not in self.player.hand:
                raise ValueError("Chosen cards must be in your hand.")
            if self.game.cities[city].color != color:
                raise ValueError("City cards must all match color to cure.")

        for city in cities:
            self.player.hand.discard(city)

        self.game.cured_diseases.append(color)
        if len(self.game.cured_diseases) == 4:
            print "All diseases cured: you win!"
        self.game.check_eradication(color)


class InfectionTurn(object):
    "Manages the card-drawing and city-infecting steps of a game turn."
    def __init__(self, game, player):
        self.game = game
        self.player = player
        self.ended = False
        self.player_cards_drawn = 0
        self.infection_cards_drawn = 0

        if len(self.game.player_deck) < 2:
            self.game.lose("Ran out of player deck cards.")
            return None

    def draw_player_card(self):
        "Draw a top card from the Player Deck and add it to your hand, unless it's an Epidemic."
        if self.player_cards_drawn == 2:
            raise ValueError("You can only draw 2 cards per turn.")
        if len(self.player.hand) > 7:
            raise ValueError("Player {} must discard to 7 cards before continuing".format(i))

        card = self.game.player_deck.pop()
        self.player_cards_drawn += 1
        if card == "epidemic":
            self.game.epidemic()
        else:
            self.player.hand.append(card)

    def draw_infection_card(self):
        "Draw the top card from the Infection Deck and infect that city."
        if self.player_cards_drawn < 2:
            raise ValueError("You must finish drawing player cards first.")
        if self.infection_cards_drawn == self.game.get_infection_rate():
            raise ValueError("Drawn enough infection cards for this turn.")

        target_city = self.game.infection_deck.draw()
        print target_city
        self.infection_cards_drawn += 1
        target_city.infect()

    def end(self):
        """
        Declare the end of the card-drawing and city-infecting stages of a turn.
        Use game.next_turn() to start the next player's action phase.
        """
        if self.player_cards_drawn < 2:
            raise ValueError("You must finish drawing player cards first.")
        if self.infection_cards_drawn < self.game.get_infection_rate():
            raise ValueError("You must finish drawing infection cards first.")

        self.ended = True

class InfectionDeck(object):
    """
    Manages the Infection Deck and Infection Discard Pile.
    """
    def __init__(self, game):
        self.game = game
        self.deck = [city_name for city_name in citymap]
        self.discards = []

    def draw(self, index=None):
        """
        Draw and discard the top card from the infection deck
        and return as a City. Use the index arg to specify a
        specific card in the deck. This method also resets the
        outbreak_chain everytime a card is drawn.
        """
        del self.game.outbreak_chain[:]
        if index is not None:
            target_city_name = self.deck.pop(index)
        else:
            target_city_name = self.deck.pop()
        self.discards.append(target_city_name)
        target_city = self.game.cities[target_city_name]
        return target_city

class City(object):
    """
    The City class
    * contains the name and color of the City
    * manages the cube state
    * manages infections and outbreaks.
    No city graph data or player data is in this class.
    """
    def __init__(self, game, name, color):
        self.game = game
        self.name = name
        self.color = color
        self.cubes = {"blue": 0,
            "yellow": 0,
            "black": 0,
            "red": 0}
        self.has_research_station = False

    def __repr__(self):
        return self.name

    def infect(self, color=None):
        "Infect the city with one cube."
        if not color:
            color = self.color

        if color in self.game.eradicated_diseases:
            return None

        if self.cubes[color] < 3:
            if self.game.cube_supply[color] == 0:
                self.game.lose("Ran out of {} cubes".format(color))
                return None
            self.cubes[color] += 1
            self.game.cube_supply[color] -= 1

        else:
            self.outbreak(color)

    def outbreak(self, color):
        """
        Spread an infection to neighboring cities.
        Only called by .infect().
        """
        self.game.outbreaks += 1

        if self.game.outbreaks > 7:
            self.game.lose("Reached eigth outbreak.")
            return None

        self.game.outbreak_chain.append((self.name, color))
        for city_name in citymap.neighbors(self.name):
            if (city_name, color) not in self.game.outbreak_chain:
                self.game.cities[city_name].infect(color)
