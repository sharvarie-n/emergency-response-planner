const locationCoordinates = {
    "Location A": [19.1860, 72.9756],
    "Location B": [19.2437, 73.1355],
    "Location C": [19.1726, 72.9425],
    "Location D": [19.0330, 73.0297]
};

const severityPriority = {
    Critical: 1,
    High: 2,
    Medium: 3,
    Low: 4
};

let map = null;
let routeLine = null;

async function getJSON(url, options = {}) {
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.error || "Request failed.");
    }
    return data;
}

function createMap() {
    map = L.map("map").setView([19.1450, 73.0200], 11);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors"
    }).addTo(map);

    Object.entries(locationCoordinates).forEach(([name, coords]) => {
        L.marker(coords).addTo(map).bindPopup(`
            <strong>🚨 Emergency Location</strong><br>${name}
        `);
    });
}

async function loadDashboardData() {
    try {
        const [units, hospitals, emergencies] = await Promise.all([
            getJSON("/api/units"),
            getJSON("/api/hospitals"),
            getJSON("/api/emergencies")
        ]);

        const available = units.filter(unit => unit[4] === "Available").length;
        const busy = units.filter(unit => unit[4] === "Busy").length;

        document.getElementById("available-count").textContent = available;
        document.getElementById("busy-count").textContent = busy;
        document.getElementById("hospital-count").textContent = hospitals.length;
        document.getElementById("emergency-count").textContent = emergencies.length;

        renderResponseUnits(units);
        renderHospitals(hospitals);
        renderEmergencyQueue(emergencies);
    } catch (error) {
        console.error(error);
    }
}

function renderResponseUnits(units) {
    const container = document.getElementById("response-units");

    if (!units.length) {
        container.innerHTML = `<p class="empty">No response units available.</p>`;
        return;
    }

    container.innerHTML = units.map(unit => {
        const id = unit[0];
        const name = unit[1];
        const type = unit[2];
        const location = unit[3];
        const status = unit[4];

        return `
            <div class="resource-card unit-card">
                <div class="resource-header">
                    <div>
                        <strong>${name}</strong>
                        <span>${type} Unit</span>
                    </div>
                    <span class="status-badge ${status.toLowerCase()}">${status}</span>
                </div>
                <div class="resource-details">
                    <span>📍 ${location}</span>
                    <label>
                        Status
                        <select onchange="updateUnitStatus(${id}, this.value)">
                            <option value="Available" ${status === "Available" ? "selected" : ""}>Available</option>
                            <option value="Busy" ${status === "Busy" ? "selected" : ""}>Busy</option>
                            <option value="Offline" ${status === "Offline" ? "selected" : ""}>Offline</option>
                        </select>
                    </label>
                </div>
            </div>
        `;
    }).join("");
}

function renderHospitals(hospitals) {
    const container = document.getElementById("hospitals-list");

    if (!hospitals.length) {
        container.innerHTML = `<p class="empty">No hospitals available.</p>`;
        return;
    }

    container.innerHTML = hospitals.map(hospital => {
        const name = hospital[1];
        const location = hospital[2];
        const status = hospital[3];

        return `
            <div class="resource-card hospital-card">
                <div class="resource-header">
                    <div>
                        <strong>🏥 ${name}</strong>
                        <span>Emergency Medical Facility</span>
                    </div>
                    <span class="status-badge ${status.toLowerCase()}">${status}</span>
                </div>
                <div class="resource-details">
                    <span>📍 ${location}</span>
                    <span>🚑 Emergency Services</span>
                </div>
            </div>
        `;
    }).join("");
}

async function updateUnitStatus(unitId, status) {
    try {
        await getJSON(`/api/units/${unitId}/status`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ status: status })
        });

        await loadDashboardData();
    } catch (error) {
        alert(error.message);
        await loadDashboardData();
    }
}

function renderEmergencyQueue(emergencies) {
    const container = document.getElementById("emergency-queue");

    if (!emergencies.length) {
        container.innerHTML = `<p class="empty">No emergency requests yet.</p>`;
        return;
    }

    emergencies.sort((a, b) => {
        const priorityDifference =
            (severityPriority[a[3]] || 5) -
            (severityPriority[b[3]] || 5);

        if (priorityDifference !== 0) {
            return priorityDifference;
        }

        return b[0] - a[0];
    });

    container.innerHTML = emergencies.slice(0, 3).map(emergency => {
        const id = emergency[0];
        const location = emergency[1];
        const type = emergency[2];
        const severity = emergency[3];
        const status = emergency[4];

        return `
            <div class="emergency-item">
                <div class="emergency-top">
                    <strong>🚨 Emergency #${id}</strong>
                    <span class="priority-badge">${severity}</span>
                </div>
                <div class="emergency-details">
                    <b>Location:</b><br>${location}<br>
                    <b>Type:</b><br>${type}<br>
                    <b>Priority:</b><br>🔴 ${severity === "Critical" ? "Highest Priority" : severity}
                </div>
                <div class="emergency-status">
                    <strong>Status:</strong>
                    <select onchange="updateEmergencyStatus(${id}, this.value)">
                        <option ${status === "Pending" ? "selected" : ""}>Pending</option>
                        <option ${status === "Dispatched" ? "selected" : ""}>Dispatched</option>
                        <option ${status === "In Progress" ? "selected" : ""}>In Progress</option>
                        <option ${status === "Resolved" ? "selected" : ""}>Resolved</option>
                    </select>
                </div>
            </div>
        `;
    }).join("");
}

async function updateEmergencyStatus(id, status) {
    try {
        await getJSON(`/api/emergencies/${id}/status`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ status: status })
        });

        await loadDashboardData();
    } catch (error) {
        alert(error.message);
    }
}

async function submitEmergency(event) {
    event.preventDefault();

    const location = document.getElementById("location").value;
    const emergencyType = document.getElementById("emergency-type").value;
    const severity = document.getElementById("severity").value;
    const message = document.getElementById("emergency-message");

    if (!location || !emergencyType || !severity) {
        message.className = "message error";
        message.textContent = "Please fill all emergency details.";
        return;
    }

    try {
        message.className = "message success";
        message.textContent = "Processing emergency...";

        const saved = await getJSON("/api/emergencies", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                location: location,
                emergency_type: emergencyType,
                severity: severity
            })
        });

        const dispatch = await getJSON(
            `/api/dispatch?destination=${encodeURIComponent(location)}` +
            `&emergency_type=${encodeURIComponent(emergencyType)}` +
            `&emergency_id=${saved.emergency_id}`
        );

        document.getElementById("assigned-unit").textContent =
            `${dispatch.unit[1]} (${dispatch.unit[2]})`;

        document.getElementById("route-path").textContent =
            dispatch.route.join(" → ");

        document.getElementById("route-distance").textContent =
            dispatch.distance;

        document.getElementById("route-time").textContent =
            Math.round((dispatch.distance / 40) * 60);

        try {
            const hospital = await getJSON(
                `/api/recommended-hospital?location=${encodeURIComponent(location)}`
            );

            document.getElementById("recommended-hospital").textContent =
                hospital.hospital[1];
        } catch {
            document.getElementById("recommended-hospital").textContent =
                "No hospital available";
        }

        message.textContent = "Emergency dispatched successfully.";
        await loadDashboardData();
    } catch (error) {
        message.className = "message error";
        message.textContent = error.message;
        await loadDashboardData();
    }
}

async function calculateRoute() {
    const start = document.getElementById("route-start").value;
    const destination = document.getElementById("route-destination").value;
    const message = document.getElementById("route-message");

    try {
        const data = await getJSON(
            `/route?start=${encodeURIComponent(start)}` +
            `&destination=${encodeURIComponent(destination)}`
        );

        document.getElementById("planner-route").textContent =
            data.route.join(" → ");

        document.getElementById("planner-distance").textContent =
            data.distance;

        document.getElementById("planner-time").textContent =
            data.estimated_time;

        const comparison = await getJSON(
            `/api/route-comparison?start=${encodeURIComponent(start)}` +
            `&destination=${encodeURIComponent(destination)}`
        );

        document.getElementById("original-route").textContent =
            comparison.original_route.join(" → ");

        document.getElementById("alternative-route").textContent =
            comparison.alternative_route.join(" → ");

        document.getElementById("distance-difference").textContent =
            comparison.distance_difference;

        document.getElementById("time-difference").textContent =
            comparison.time_difference;

        message.className = "message success";
        message.textContent = "Shortest route calculated successfully.";

        await drawOSRMRoute(data.route);
    } catch (error) {
        message.className = "message error";
        message.textContent = error.message;
    }
}

async function drawOSRMRoute(route) {
    if (routeLine) {
        map.removeLayer(routeLine);
        routeLine = null;
    }

    if (!route || route.length < 2) {
        return;
    }

    const coords = route.map(location => locationCoordinates[location]).filter(Boolean);

    if (coords.length < 2) {
        return;
    }

    const coordinateString = coords
        .map(coordinate => `${coordinate[1]},${coordinate[0]}`)
        .join(";");

    try {
        const response = await fetch(
            `https://router.project-osrm.org/route/v1/driving/${coordinateString}?overview=full&geometries=geojson`
        );

        const data = await response.json();

        if (!data.routes || !data.routes.length) {
            throw new Error("OSRM route unavailable");
        }

        routeLine = L.geoJSON(data.routes[0].geometry, {
            style: {
                color: "#287df5",
                weight: 7,
                opacity: 0.9
            }
        }).addTo(map);

        map.fitBounds(routeLine.getBounds(), {
            padding: [30, 30]
        });
    } catch {
        routeLine = L.polyline(coords, {
            color: "#287df5",
            weight: 7,
            opacity: 0.9
        }).addTo(map);

        map.fitBounds(routeLine.getBounds(), {
            padding: [30, 30]
        });
    }
}

async function loadBlockedRoads() {
    const roads = await getJSON("/api/blocked-roads");
    const container = document.getElementById("blocked-roads-list");

    if (!roads.length) {
        container.innerHTML = `<p class="empty">No roads are currently blocked.</p>`;
        return;
    }

    container.innerHTML = roads.map(road => `
        <div class="blocked-road">
            🚧 <strong>${road.start} → ${road.end}</strong> is currently blocked.
        </div>
    `).join("");
}

async function blockRoad() {
    const start = document.getElementById("blocked-road-start").value;
    const end = document.getElementById("blocked-road-end").value;

    try {
        await getJSON("/api/blocked-roads", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                start: start,
                end: end
            })
        });

        await loadBlockedRoads();
        await calculateRoute();
    } catch (error) {
        alert(error.message);
    }
}

async function unblockRoad() {
    const start = document.getElementById("blocked-road-start").value;
    const end = document.getElementById("blocked-road-end").value;

    try {
        await getJSON("/api/blocked-roads", {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                start: start,
                end: end
            })
        });

        await loadBlockedRoads();
        await calculateRoute();
    } catch (error) {
        alert(error.message);
    }
}

document.addEventListener("DOMContentLoaded", async function() {
    createMap();

    document.getElementById("emergency-form").addEventListener(
        "submit",
        submitEmergency
    );

    document.getElementById("calculate-route").addEventListener(
        "click",
        calculateRoute
    );

    document.getElementById("block-road-button").addEventListener(
        "click",
        blockRoad
    );

    document.getElementById("unblock-road-button").addEventListener(
        "click",
        unblockRoad
    );

    await loadDashboardData();
    await loadBlockedRoads();
    await calculateRoute();
});
