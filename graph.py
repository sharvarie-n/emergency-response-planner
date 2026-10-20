graph = {
    "Location A": {
        "Location B": 5,
        "Location C": 10
    },

    "Location B": {
        "Location A": 5,
        "Location C": 3,
        "Location D": 8
    },

    "Location C": {
        "Location A": 10,
        "Location B": 3,
        "Location D": 2
    },

    "Location D": {
        "Location B": 8,
        "Location C": 2
    }
}


blocked_roads = set()


def dijkstra(graph, start, blocked_roads=None):

    if blocked_roads is None:
        blocked_roads = set()

    distances = {}
    previous = {}
    unvisited = set(graph.keys())

    for node in graph:
        distances[node] = float("inf")
        previous[node] = None

    if start not in graph:
        return distances, previous

    distances[start] = 0

    while unvisited:

        current = min(
            unvisited,
            key=lambda node: distances[node]
        )

        if distances[current] == float("inf"):
            break

        unvisited.remove(current)

        for neighbour, weight in graph[current].items():

            road1 = (current, neighbour)
            road2 = (neighbour, current)

            if road1 in blocked_roads or road2 in blocked_roads:
                continue

            new_distance = (
                distances[current] + weight
            )

            if new_distance < distances[neighbour]:

                distances[neighbour] = new_distance
                previous[neighbour] = current

    return distances, previous


def find_shortest_path(
    graph,
    start,
    destination,
    blocked_roads=None
):

    if start not in graph or destination not in graph:
        return [], float("inf")

    distances, previous = dijkstra(
        graph,
        start,
        blocked_roads
    )

    if distances[destination] == float("inf"):
        return [], float("inf")

    path = []
    current = destination

    while current is not None:
        path.append(current)
        current = previous[current]

    path.reverse()

    return path, distances[destination]


def find_nearest_unit(
    units,
    destination,
    blocked_roads=None
):

    nearest_unit = None
    shortest_distance = float("inf")
    nearest_route = []

    for unit in units:

        unit_location = unit[3]

        route, distance = find_shortest_path(
            graph,
            unit_location,
            destination,
            blocked_roads
        )

        if route and distance < shortest_distance:

            shortest_distance = distance
            nearest_unit = unit
            nearest_route = route

    return (
        nearest_unit,
        nearest_route,
        shortest_distance
    )