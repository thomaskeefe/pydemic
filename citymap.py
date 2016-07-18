import networkx as nx

citymap = nx.read_adjlist("city_map_adj_list_data.txt")

blue_cities = ["san_francisco",
    "chicago",
    "montreal",
    "new_york",
    "washington",
    "atlanta",
    "london",
    "madrid",
    "paris",
    "essen",
    "milan",
    "st_petersburg",]

yellow_cities = ["los_angeles",
    "mexico_city",
    "miami",
    "bogota",
    "lima",
    "santiago",
    "sao_paolo",
    "buenos_aires",
    "lagos",
    "kinshasa",
    "khartoum",
    "johannesburg",]

black_cities = ["algiers",
    "istanbul",
    "cairo",
    "moscow",
    "baghdad",
    "riyadh",
    "tehran",
    "karachi",
    "mumbai",
    "delhi",
    "chennai",
    "kolkata",]

red_cities = ["bangkok",
    "jakarta",
    "beijing",
    "shanghai",
    "hong_kong",
    "ho_chi_minh_city",
    "seoul",
    "taipei",
    "manila",
    "sydney",
    "tokyo",
    "osaka",]

for city in blue_cities:
    citymap.node[city]['color'] = 'blue'

for city in yellow_cities:
    citymap.node[city]['color'] = 'yellow'

for city in black_cities:
    citymap.node[city]['color'] = 'black'

for city in red_cities:
    citymap.node[city]['color'] = 'red'
