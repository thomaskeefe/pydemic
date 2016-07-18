import pydemic
from citymap import citymap
from collections import Counter
from unittest import TestCase

class TestGame(TestCase):
    "Test game methods that do not require running .game_setup."
    def setUp(self):
        self.game = pydemic.Game(num_players=4, num_epidemic_cards=5)

    def test_check_eradication(self):
        self.game.cured_diseases.append("blue")
        self.game.check_eradication("blue")
        self.assertIn("blue", self.game.eradicated_diseases)

    def test_remove_research_station(self):
        self.game.remove_research_station("atlanta")
        self.assertEqual(self.game.research_stations, 0)
        atlanta = self.game.cities["atlanta"]
        self.assertFalse(atlanta.has_research_station)

    def test_cannot_remove_research_station_where_none_exists(self):
        with self.assertRaises(ValueError):
            self.game.remove_research_station("moscow")
        self.assertEqual(self.game.research_stations, 1)

    def test_epidemic_not_resulting_in_outbreak(self):
        # beijing is on the bottom of the default deck
        beijing = self.game.cities['beijing']
        self.assertEqual(beijing.cubes[beijing.color], 0)
        self.game.epidemic()
        self.assertEqual(self.game.infection_track, 2)
        self.assertEqual(beijing.cubes[beijing.color], 3)
        self.assertEqual(self.game.outbreaks, 0)
        self.assertEqual(self.game.infection_deck.deck[-1], 'beijing')
        self.assertEqual(self.game.infection_deck.discards, [])

    def test_epidemic_resulting_in_outbreak(self):
        # beijing is on the bottom of the default deck
        beijing = self.game.cities['beijing']
        beijing.infect()
        self.game.epidemic()
        self.assertEqual(self.game.infection_track, 2)
        self.assertEqual(beijing.cubes[beijing.color], 3)
        self.assertEqual(self.game.outbreaks, 1)
        for city_name in citymap.neighbors('beijing'):
            neighboring_city = self.game.cities[city_name]
            self.assertEqual(neighboring_city.cubes[beijing.color], 1)

        self.assertEqual(self.game.infection_deck.deck[-1], 'beijing')
        self.assertEqual(self.game.infection_deck.discards, [])


class TestGameSetup(TestCase):
    """
    Test the methods that set up a game. These are non-deterministic procedures,
    but have some definite, testable outcomes.
    """
    def setUp(self):
        self.game = pydemic.Game(num_players=4, num_epidemic_cards=5)
        self.game.game_setup()

    def test_first_turn(self):
        self.assertIsNotNone(self.game.turn)

    def test_correct_cube_setup(self):
        total_cube_supply = sum(self.game.cube_supply.values())
        self.assertEqual(78, total_cube_supply)

    def test_city_cards_discarded_after_setup(self):
        self.assertEqual(9, len(self.game.infection_deck.discards))

    def test_correct_number_of_epidemic_cards(self):
        real_num_epidemic_cards = self.game.player_deck.count("epidemic")
        self.assertEqual(self.game.num_epidemic_cards, real_num_epidemic_cards)

    def test_correct_size_player_hands(self):
        for player in self.game.players:
            self.assertEqual(len(player.hand), 2)


class TestTurn(TestCase):
    def setUp(self):
        self.game = pydemic.Game(num_players=4, num_epidemic_cards=5)
        self.game.game_setup()

    def test_must_end_turn_before_next_turn(self):
        with self.assertRaises(ValueError):
            self.game.next_turn()

    def test_new_turn_increment(self):
        current_turn_num = self.game.turn_count
        self.game.turn.end()
        self.game.infection_turn.ended = True
        self.game.next_turn()
        self.assertEqual(current_turn_num + 1, self.game.turn_count)

    def test_only_4_actions_allowed(self):
        with self.assertRaises(ValueError):
            for i in range(5):
                self.game.turn.skip()

    def test_raise_for_too_many_cards(self):
        while len(self.game.turn.player.hand) < 8:
            self.game.turn.player.hand.append("dummy")

        with self.assertRaises(ValueError):
            self.game.turn.skip()

    def test_decrement_actions(self):
        self.game.turn.skip()
        self.assertEqual(self.game.turn.actions, 3)

    def test_invalid_action_doesnt_decrement_actions(self):
        with self.assertRaises(ValueError):
            self.game.turn.drive("moscow")
        self.assertEqual(self.game.turn.actions, 4)

    def test_new_player_turn_nullifies_infection_turn(self):
        self.game.turn.end()
        self.game.infection_turn.ended = True
        self.game.next_turn()
        self.assertIsNone(self.game.infection_turn)


class TestActions(TestCase):
    def setUp(self):
        self.game = pydemic.Game(num_players=4, num_epidemic_cards=5)
        self.player = self.game.players[0]
        self.game.turn = pydemic.PlayerTurn(self.game, self.player)
        self.turn = self.game.turn

    def test_drive(self):
        self.turn.drive("chicago")
        self.assertEqual(self.player.city, "chicago")

    def test_cannot_drive_to_non_neighboring_city(self):
        with self.assertRaises(ValueError):
            self.turn.drive("moscow")

    def test_direct_flight(self):
        self.player.hand.append("moscow")
        self.turn.direct_flight("moscow")
        self.assertEqual(self.player.city, "moscow")

    def test_need_card_for_direct_flight(self):
        self.assertNotIn("moscow", self.player.hand)
        with self.assertRaises(ValueError):
            self.turn.direct_flight("moscow")

    def test_charter_flight(self):
        self.player.hand.append("atlanta")
        self.turn.charter_flight("moscow")
        self.assertEqual(self.player.city, "moscow")

    def test_need_card_for_charter_flight(self):
        self.assertNotIn("atlanta", self.player.hand)
        with self.assertRaises(ValueError):
            self.turn.charter_flight("moscow")

    def test_shuttle_flight(self):
        self.game.cities["moscow"].has_research_station = True
        self.turn.shuttle_flight("moscow")
        self.assertEqual(self.player.city, "moscow")

    def test_need_research_station_for_shuttle_flight(self):
        self.assertFalse(self.game.cities["moscow"].has_research_station)
        with self.assertRaises(ValueError):
            self.turn.shuttle_flight("moscow")

    def test_build_research_station(self):
        current_num_research_stations = self.game.research_stations
        self.player.city = "moscow"
        self.player.hand.append("moscow")
        self.turn.build_research_station()
        self.assertTrue(self.game.cities["moscow"].has_research_station)
        self.assertEqual(self.game.research_stations, current_num_research_stations + 1)

    def test_need_card_to_build_research_station(self):
        self.player.city = "moscow"
        with self.assertRaises(ValueError):
            self.turn.build_research_station()

    def test_cannot_build_research_station_if_already_exists(self):
        self.assertEqual(self.player.city, "atlanta")
        with self.assertRaises(ValueError):
            self.turn.build_research_station()

    def test_cannot_build_research_station_when_max_exist(self):
        for city_name in ["san_francisco", "chicago", "los_angeles", "manila", "tokyo"]:
            city = self.game.cities[city_name]
            city.has_research_station = True
            self.game.research_stations += 1

        self.assertEqual(self.game.research_stations, 6)
        self.player.city = "moscow"
        self.player.hand.append("moscow")
        with self.assertRaises(ValueError):
            self.turn.build_research_station()

    def test_give_card(self):
        self.player.hand.append("atlanta")
        recipient = self.game.players[1]

        self.turn.share_knowledge(recipient)
        self.assertIn("atlanta", recipient.hand)
        self.assertNotIn("atlanta", self.player.hand)

    def test_take_card(self):
        giver = self.game.players[1]
        giver.hand.append("atlanta")

        self.turn.share_knowledge(giver)
        self.assertIn("atlanta", self.player.hand)
        self.assertNotIn("atlanta", giver.hand)

    def test_cannot_share_knowledge_without_card(self):
        giver = self.game.players[1]
        self.assertNotIn("atlanta", giver.hand)
        self.assertNotIn("atlanta", self.player.hand)
        with self.assertRaises(ValueError):
            self.turn.share_knowledge(giver)

    def test_cannot_share_knowledge_if_players_not_in_same_city(self):
        giver = self.game.players[1]
        giver.city = "moscow"
        giver.hand.append("atlanta")
        with self.assertRaises(ValueError):
            self.turn.share_knowledge(giver)

    def test_discover_cure(self):
        blue_cities = ["san_francisco", "chicago", "montreal", "new_york", "washington"]
        self.player.hand.extend(blue_cities)
        self.turn.discover_cure("blue", blue_cities)
        for city in blue_cities:
            self.assertNotIn(city, self.player.hand)
        self.assertIn("blue", self.game.cured_diseases)

    def test_too_few_cards_to_discover_cure(self):
        four_blue_cities = ["san_francisco", "chicago", "montreal", "new_york"]
        self.player.hand.extend(four_blue_cities)
        with self.assertRaises(ValueError):
            self.turn.discover_cure("blue", four_blue_cities)
        for city in four_blue_cities:
            self.assertIn(city, self.player.hand)
        self.assertNotIn("blue", self.game.cured_diseases)

    def test_cannot_discover_cure_without_research_station(self):
        self.game.remove_research_station("atlanta")
        blue_cities = ["san_francisco", "chicago", "montreal", "new_york", "washington"]
        self.player.hand.extend(blue_cities)

        with self.assertRaises(ValueError):
            self.turn.discover_cure("blue", blue_cities)

        for city in blue_cities:
            self.assertIn(city, self.player.hand)

        self.assertNotIn("blue", self.game.cured_diseases)

    def test_cards_must_be_in_hand_to_discover_cure(self):
        blue_cities = ["san_francisco", "chicago", "montreal", "new_york", "washington"]
        for city in blue_cities:
            self.assertNotIn(city, self.player.hand)

        with self.assertRaises(ValueError):
            self.turn.discover_cure("blue", blue_cities)

        self.assertNotIn("blue", self.game.cured_diseases)

    def test_city_colors_much_match_to_discover_cure(self):
        cities = ["moscow", "chicago", "montreal", "new_york", "washington"]
        self.player.hand.extend(cities)

        with self.assertRaises(ValueError):
            self.turn.discover_cure("blue", cities)

        for city in cities:
            self.assertIn(city, self.player.hand)

        self.assertNotIn("blue", self.game.cured_diseases)


class TestTreatingDisease(TestCase):
    def setUp(self):
        self.game = pydemic.Game(num_players=4, num_epidemic_cards=5)
        self.player = self.game.players[0]
        self.game.turn = pydemic.PlayerTurn(self.game, self.player)
        self.turn = self.game.turn
        self.atlanta = self.game.cities["atlanta"]
        self.atlanta.cubes["blue"] = 3
        self.atlanta.cubes["yellow"] = 3

    def test_treat_disease(self):
        self.turn.treat_disease("blue")
        self.assertEqual(self.atlanta.cubes["blue"], 2)
        self.assertEqual(self.atlanta.cubes["yellow"], 3)

    def test_treat_cured_disease(self):
        self.game.cured_diseases.append("blue")
        self.turn.treat_disease("blue")
        self.assertEqual(self.atlanta.cubes["blue"], 0)
        self.assertEqual(self.atlanta.cubes["yellow"], 3)


class TestInfectionTurn(TestCase):
    def setUp(self):
        self.game = pydemic.Game(num_players=4, num_epidemic_cards=5)
        self.game.turn = pydemic.PlayerTurn(self.game, self.game.players[0])  # so that there is a Turn object

    def test_ending_player_turn_creates_infection_turn(self):
        self.game.turn.end()
        self.assertIsNotNone(self.game.infection_turn)

    def test_must_end_infection_turn_before_next_turn(self):
        self.game.game_setup()
        self.game.turn.end()
        with self.assertRaises(ValueError):
            self.game.next_turn()

    def test_draw_player_card(self):
        self.game.infection_turn = pydemic.InfectionTurn(self.game, self.game.turn.player)

        # Epidemic cards haven't been shuffled into the Player Deck.
        self.game.infection_turn.draw_player_card()

        self.assertEqual(len(self.game.infection_turn.player.hand), 1)
        self.assertEqual(self.game.infection_turn.player_cards_drawn, 1)

    def test_cannot_draw_three_player_cards(self):
        self.game.infection_turn = pydemic.InfectionTurn(self.game, self.game.turn.player)

        # Epidemic cards haven't been shuffled into the Player Deck.
        self.game.infection_turn.draw_player_card()
        self.game.infection_turn.draw_player_card()
        with self.assertRaises(ValueError):
            self.game.infection_turn.draw_player_card()

        self.assertEqual(len(self.game.infection_turn.player.hand), 2)

    def test_draw_epidemic_card(self):
        self.game.infection_turn = pydemic.InfectionTurn(self.game, self.game.turn.player)
        self.game.player_deck.append("epidemic")
        self.game.infection_turn.draw_player_card()
        self.assertEqual(self.game.infection_track, 2)
        self.assertEqual(len(self.game.infection_turn.player.hand), 0)
        self.assertEqual(self.game.infection_turn.player_cards_drawn, 1)

    def test_draw_infection_card(self):
        self.game.infection_turn = pydemic.InfectionTurn(self.game, self.game.turn.player)
        # must draw 2 player cards before infection cards.
        self.game.infection_turn.player_cards_drawn = 2

        self.game.infection_turn.draw_infection_card()  # it will be montreal
        self.assertEqual(self.game.infection_turn.infection_cards_drawn, 1)
        montreal = self.game.cities['montreal']
        self.assertEqual(montreal.cubes[montreal.color], 1)

    def test_cannot_draw_infection_cards_before_drawing_two_player_cards(self):
        self.game.infection_turn = pydemic.InfectionTurn(self.game, self.game.turn.player)
        with self.assertRaises(ValueError):
            self.game.infection_turn.draw_infection_card()

    def test_cannot_draw_more_infection_cards_than_infection_rate(self):
        self.game.infection_turn = pydemic.InfectionTurn(self.game, self.game.turn.player)
        self.game.infection_turn.player_cards_drawn = 2
        while self.game.infection_turn.infection_cards_drawn < self.game.get_infection_rate():
            self.game.infection_turn.draw_infection_card()

        with self.assertRaises(ValueError):
            self.game.infection_turn.draw_infection_card()

class TestPlayerHand(TestCase):
    def test_discard(self):
        game = pydemic.Game(num_players=4, num_epidemic_cards=5)
        player = game.players[0]
        card = game.player_deck.pop()
        player.hand.append(card)
        player.hand.discard(card)
        self.assertNotIn(card, player.hand)
        self.assertEqual(card, game.player_discard_pile[-1])


class TestCity(TestCase):
    def setUp(self):
        self.game = pydemic.Game(num_players=4, num_epidemic_cards=5)
        self.moscow = self.game.cities['moscow']

    def test_infect(self):
        "Test infecting a city with no cubes"
        self.assertEqual(self.moscow.cubes['black'], 0)
        self.assertEqual(self.game.cube_supply['black'], 24)

        self.moscow.infect('black')

        self.assertEqual(self.moscow.cubes['black'], 1)
        self.assertEqual(self.game.cube_supply['black'], 23)

    def test_infect_resulting_in_outbreak(self):
        self.game.turn = pydemic.PlayerTurn(self.game, self.game.players[0])  # so that there is a Turn object
        for i in range(4):
            self.moscow.infect()
        self.assertEqual(self.game.outbreaks, 1)

    def test_no_new_infection_for_eradicated_disease(self):
        self.game.eradicated_diseases.append("black")
        self.assertEqual(self.moscow.cubes['black'], 0)
        self.moscow.infect()
        self.assertEqual(self.moscow.cubes['black'], 0)

    def test_outbreak(self):
        self.game.turn = pydemic.PlayerTurn(self.game, self.game.players[0])  # so that there is a Turn object
        self.assertEqual(self.game.outbreaks, 0)
        for city_name in citymap.neighbors('moscow'):
            city = self.game.cities[city_name]
            self.assertEqual(city.cubes['black'], 0)

        self.moscow.outbreak('black')

        self.assertEqual(self.game.outbreaks, 1)

        for city_name in citymap.neighbors('moscow'):
            city = self.game.cities[city_name]
            self.assertEqual(city.cubes['black'], 1)

    def test_chain_reaction_outbreak(self):
        self.game.game_setup()


class TestLoseConditions(TestCase):
    def setUp(self):
        self.game = pydemic.Game(num_players=4, num_epidemic_cards=5)

    def test_run_out_of_cubes(self):
        # place 24 blue cubes on the map, but cause no outbreaks
        blue_cities = ["san_francisco", "chicago", "montreal", "new_york", "washington", "atlanta", "london", "madrid"]
        for city_name in blue_cities:
            city = self.game.cities[city_name]
            for i in range(3):
                city.infect()

        self.game.cities["paris"].infect()  # try to place a 25th cube
        self.assertTrue(self.game.lost)
        self.assertEqual(self.game.cube_supply["blue"], 0)

    def test_eight_outbreaks(self):
        cities = ["chicago", "mexico_city", "algiers", "istanbul", "bangkok", "jakarta"]
        for city_name in cities:
            city = self.game.cities[city_name]
            for i in range(3):
                city.infect()
        for city_name in cities:
            city = self.game.cities[city_name]
            city.infect()
        self.assertEqual(self.game.outbreaks, 8)
        self.assertTrue(self.game.lost)

    def test_run_out_of_player_cards(self):
        del self.game.player_deck[:]
        self.game.infection_turn = pydemic.InfectionTurn(self.game, self.game.players[0])
        self.assertTrue(self.game.lost)


class TestCityMap(TestCase):
    def test_correct_number_of_cities_for_each_color(self):
        counter = Counter([citymap.node[city_name]['color'] for city_name in citymap])
        correct_counts = {'blue': 12, 'red': 12, 'black': 12, 'yellow': 12}
        self.assertEqual(counter, correct_counts)


class TestInfectionDeck(TestCase):
    def setUp(self):
        self.game = pydemic.Game(num_players=4, num_epidemic_cards=5)

    def test_draw(self):
        city = self.game.infection_deck.draw()
        self.assertEqual(city.name, "montreal")
        self.assertNotIn("montreal", self.game.infection_deck.deck)
        self.assertIn("montreal", self.game.infection_deck.discards)

    def test_draw_bottom_card(self):
        city = self.game.infection_deck.draw(0)
        self.assertEqual(city.name, "beijing")
