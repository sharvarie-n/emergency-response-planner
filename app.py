from flask import Flask, render_template, jsonify, request

from graph import graph, find_shortest_path, find_nearest_unit

from database import (
    get_response_units,
    get_available_response_units,
    get_hospitals,
    add_emergency_request,
    get_emergency_requests,
    update_unit_status,
    update_emergency_status
)

app = Flask(__name__)

blocked_roads = set()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/route", methods=["GET"])
def route():
    start = request.args.get("start")
    destination = request.args.get("destination")

    if not start or not destination:
        return jsonify({
            "error": "Start and destination are required."
        }), 400

    path, distance = find_shortest_path(
        graph,
        start,
        destination,
        blocked_roads
    )

    if not path:
        return jsonify({
            "error": "No route available."
        }), 404

    speed = 40
    estimated_time = round((distance / speed) * 60)

    return jsonify({
        "route": path,
        "distance": distance,
        "estimated_time": estimated_time
    })


@app.route("/api/route-comparison")
def route_comparison():
    start = request.args.get("start")
    destination = request.args.get("destination")

    if not start or not destination:
        return jsonify({
            "error": "Start and destination are required."
        }), 400

    original_path, original_distance = find_shortest_path(
        graph,
        start,
        destination,
        set()
    )

    alternative_path, alternative_distance = find_shortest_path(
        graph,
        start,
        destination,
        blocked_roads
    )

    if not original_path:
        return jsonify({
            "error": "No original route available."
        }), 404

    if not alternative_path:
        return jsonify({
            "error": "No alternative route available."
        }), 404

    speed = 40

    original_time = round(
        (original_distance / speed) * 60
    )

    alternative_time = round(
        (alternative_distance / speed) * 60
    )

    return jsonify({
        "original_route": original_path,
        "original_distance": original_distance,
        "original_time": original_time,
        "alternative_route": alternative_path,
        "alternative_distance": alternative_distance,
        "alternative_time": alternative_time,
        "distance_difference": alternative_distance - original_distance,
        "time_difference": alternative_time - original_time
    })


@app.route("/api/units")
def get_units():
    return jsonify(get_response_units())


@app.route("/api/units/<int:unit_id>/status", methods=["PUT"])
def change_unit_status(unit_id):
    data = request.get_json(silent=True)

    if not data or not data.get("status"):
        return jsonify({
            "error": "Status is required."
        }), 400

    allowed_statuses = [
        "Available",
        "Busy",
        "Offline"
    ]

    if data["status"] not in allowed_statuses:
        return jsonify({
            "error": "Invalid unit status."
        }), 400

    update_unit_status(
        unit_id,
        data["status"]
    )

    return jsonify({
        "message": "Unit status updated successfully."
    })


@app.route("/api/hospitals")
def get_hospital_data():
    return jsonify(get_hospitals())


@app.route("/api/emergencies", methods=["GET"])
def get_emergencies():
    return jsonify(get_emergency_requests())


@app.route("/api/emergencies", methods=["POST"])
def create_emergency():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Invalid request data."
        }), 400

    location = data.get("location")
    emergency_type = data.get("emergency_type")
    severity = data.get("severity")

    if not location or not emergency_type or not severity:
        return jsonify({
            "error": "Please fill all emergency details."
        }), 400

    emergency_id = add_emergency_request(
        location,
        emergency_type,
        severity
    )

    return jsonify({
        "message": "Emergency request saved successfully.",
        "emergency_id": emergency_id
    })


@app.route("/api/emergencies/<int:emergency_id>/status", methods=["PUT"])
def change_emergency_status(emergency_id):
    data = request.get_json(silent=True)

    if not data or not data.get("status"):
        return jsonify({
            "error": "Status is required."
        }), 400

    allowed_statuses = [
        "Pending",
        "Dispatched",
        "In Progress",
        "Resolved"
    ]

    if data["status"] not in allowed_statuses:
        return jsonify({
            "error": "Invalid emergency status."
        }), 400

    update_emergency_status(
        emergency_id,
        data["status"]
    )

    return jsonify({
        "message": "Emergency status updated successfully."
    })


@app.route("/api/dispatch")
def dispatch_unit():
    destination = request.args.get("destination")
    emergency_type = request.args.get("emergency_type")
    emergency_id = request.args.get("emergency_id")

    if not destination:
        return jsonify({
            "error": "Emergency destination is required."
        }), 400

    units = get_available_response_units()

    if emergency_type in ["Medical", "Accident"]:
        matching_units = [
            unit for unit in units
            if unit[2] == "Medical"
        ]

    elif emergency_type == "Fire":
        matching_units = [
            unit for unit in units
            if unit[2] == "Fire"
        ]

    else:
        matching_units = units

    if not matching_units:
        return jsonify({
            "error": "No suitable response unit available."
        }), 404

    unit, route_path, distance = find_nearest_unit(
        matching_units,
        destination,
        blocked_roads
    )

    if not unit or not route_path:
        return jsonify({
            "error": "No route available for response unit."
        }), 404

    update_unit_status(
        unit[0],
        "Busy"
    )

    if emergency_id:
        update_emergency_status(
            int(emergency_id),
            "Dispatched"
        )

    return jsonify({
        "unit": unit,
        "route": route_path,
        "distance": distance,
        "emergency_status": "Dispatched"
    })


@app.route("/api/recommended-hospital")
def recommended_hospital():
    location = request.args.get("location")

    if not location:
        return jsonify({
            "error": "Emergency location is required."
        }), 400

    hospitals = get_hospitals()

    available_hospitals = [
        hospital for hospital in hospitals
        if hospital[3] == "Available"
    ]

    nearest_hospital = None
    shortest_distance = float("inf")
    best_route = []

    for hospital in available_hospitals:

        route_path, distance = find_shortest_path(
            graph,
            location,
            hospital[2],
            blocked_roads
        )

        if route_path and distance < shortest_distance:
            shortest_distance = distance
            nearest_hospital = hospital
            best_route = route_path

    if nearest_hospital is None:
        return jsonify({
            "error": "No reachable hospital found."
        }), 404

    return jsonify({
        "hospital": nearest_hospital,
        "route": best_route,
        "distance": shortest_distance
    })


@app.route("/api/blocked-roads", methods=["GET"])
def get_blocked_roads():
    return jsonify([
        {
            "start": road[0],
            "end": road[1]
        }
        for road in blocked_roads
    ])


@app.route("/api/blocked-roads", methods=["POST"])
def block_road():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Invalid request data."
        }), 400

    start = data.get("start")
    end = data.get("end")

    if not start or not end:
        return jsonify({
            "error": "Both road locations are required."
        }), 400

    if start == end:
        return jsonify({
            "error": "A location cannot be connected to itself."
        }), 400

    if start not in graph or end not in graph[start]:
        return jsonify({
            "error": "Invalid road."
        }), 400

    blocked_roads.add((start, end))

    return jsonify({
        "message": "Road blocked successfully."
    })


@app.route("/api/blocked-roads", methods=["DELETE"])
def unblock_road():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Invalid request data."
        }), 400

    start = data.get("start")
    end = data.get("end")

    blocked_roads.discard((start, end))
    blocked_roads.discard((end, start))

    return jsonify({
        "message": "Road unblocked successfully."
    })


if __name__ == "__main__":
    app.run(debug=True)