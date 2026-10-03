let speedChart = null;
let distributionChart = null;

let map = null;
let markers = [];

let countdownSeconds = 60;

let dashboardLoading = false;
let refreshInProgress = false;

let autoRefreshTimer = null;

const API_LATEST = "/api/traffic/latest/";
const API_ANALYTICS = "/api/traffic/analytics/";
const API_REFRESH = "/api/traffic/refresh/";
const API_HOTSPOTS = "/api/traffic/hotspots/";
const API_INCIDENTS = "/api/traffic/incidents/";

function escapeHTML(value) {
    if (value === null || value === undefined) {
        return "";
    }

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function formatNumber(value, decimals = 1) {
    const number = Number(value);

    if (!Number.isFinite(number)) {
        return "0";
    }

    return number.toFixed(decimals);
}

function getCity() {
    return (
        document.getElementById("cityFilter")?.value ||
        "all"
    );
}

function getArea() {
    return (
        document.getElementById("areaFilter")?.value ||
        "all"
    );
}

function getPoint() {
    return (
        document.getElementById("pointFilter")?.value ||
        "all"
    );
}

function buildQuery(city, area, point) {
    const params = new URLSearchParams();

    if (city && city !== "all") {
        params.append("city", city);
    }

    if (area && area !== "all") {
        params.append("area", area);
    }

    if (point && point !== "all") {
        params.append("point_id", point);
    }

    const query = params.toString();

    return query ? `?${query}` : "";
}

function setLiveStatus(status, message = null) {
    const statusElement =
        document.getElementById("liveStatus") ||
        document.querySelector(".live-status");

    if (!statusElement) {
        return;
    }

    const messages = {
        live: "LIVE MONITORING",
        updating: "UPDATING",
        success: "LIVE • UPDATED",
        error: "CONNECTION ERROR"
    };

    const text =
        message ||
        messages[status] ||
        "LIVE MONITORING";

    let dotColor = "#10b981";
    let background = "#052e2b";
    let textColor = "#6ee7b7";

    if (status === "updating") {
        dotColor = "#d97706";
        background = "#451a03";
        textColor = "#fcd34d";
    }

    if (status === "error") {
        dotColor = "#dc2626";
        background = "#450a0a";
        textColor = "#fca5a5";
    }

    statusElement.style.background = background;
    statusElement.style.color = textColor;

    statusElement.innerHTML = `
        <span
            class="live-dot"
            style="background:${dotColor};">
        </span>
        ${escapeHTML(text)}
    `;
}

function trafficBadge(level) {
    const value =
        String(level || "UNKNOWN").toUpperCase();

    if (value === "LOW") {
        return `
            <span class="traffic-badge traffic-low">
                LOW
            </span>
        `;
    }

    if (value === "MEDIUM") {
        return `
            <span class="traffic-badge traffic-medium">
                MEDIUM
            </span>
        `;
    }

    if (value === "HIGH") {
        return `
            <span class="traffic-badge traffic-high">
                HIGH
            </span>
        `;
    }

    return `
        <span class="traffic-badge">
            ${escapeHTML(value)}
        </span>
    `;
}

function hotspotStatusBadge(status) {
    const value =
        String(status || "NORMAL").toUpperCase();

    let className = "traffic-badge";

    if (value === "CRITICAL") {
        className = "traffic-badge traffic-high";
    }
    else if (value === "HEAVY") {
        className = "traffic-badge traffic-high";
    }
    else if (value === "MODERATE") {
        className = "traffic-badge traffic-medium";
    }
    else if (value === "NORMAL") {
        className = "traffic-badge traffic-low";
    }

    return `
        <span class="${className}">
            ${escapeHTML(value)}
        </span>
    `;
}

function incidentSeverityBadge(severity) {
    const value =
        String(severity || "MEDIUM").toUpperCase();

    let className = "incident-severity";

    if (value === "CRITICAL") {
        className += " incident-severity-critical";
    }
    else if (value === "HIGH") {
        className += " incident-severity-high";
    }
    else if (value === "MEDIUM") {
        className += " incident-severity-medium";
    }
    else {
        className += " incident-severity-low";
    }

    return `
        <span class="${className}">
            ${escapeHTML(value)}
        </span>
    `;
}

function closureBadge(value) {
    const closed =
        value === true ||
        value === 1 ||
        value === "1" ||
        value === "true";

    if (closed) {
        return `
            <span class="closure-badge closure-yes">
                YES
            </span>
        `;
    }

    return `
        <span class="closure-badge closure-no">
            NO
        </span>
    `;
}

function updateCountdown() {
    const countdown =
        document.getElementById("countdown");

    if (!countdown) {
        return;
    }

    countdown.textContent =
        `Next update: ${countdownSeconds}s`;
}

function resetCountdown() {
    countdownSeconds = 60;
    updateCountdown();
}

async function fetchJSON(url, timeout = 10000) {
    const controller =
        new AbortController();

    const timeoutId =
        setTimeout(
            () => controller.abort(),
            timeout
        );

    try {
        const response =
            await fetch(
                url,
                {
                    method: "GET",
                    headers: {
                        "Accept": "application/json"
                    },
                    cache: "no-store",
                    signal: controller.signal
                }
            );

        if (!response.ok) {
            throw new Error(
                `HTTP ${response.status}`
            );
        }

        return await response.json();
    }
    catch (error) {
        if (error.name === "AbortError") {
            throw new Error(
                "Request timed out."
            );
        }

        throw error;
    }
    finally {
        clearTimeout(timeoutId);
    }
}

async function loadCities() {
    try {
        const data =
            await fetchJSON(
                API_LATEST,
                10000
            );

        const select =
            document.getElementById(
                "cityFilter"
            );

        if (!select) {
            return;
        }

        const currentValue =
            select.value;

        select.innerHTML = `
            <option value="all">
                All Cities
            </option>
        `;

        const cities =
            Array.isArray(data.cities)
                ? data.cities
                : [];

        cities.forEach(city => {
            const option =
                document.createElement("option");

            if (typeof city === "object") {
                option.value =
                    city.city || "";

                option.textContent =
                    city.city || "";
            }
            else {
                option.value = city;
                option.textContent = city;
            }

            select.appendChild(option);
        });

        const exists =
            [...select.options].some(
                option =>
                    option.value === currentValue
            );

        if (exists) {
            select.value = currentValue;
        }
    }
    catch (error) {
        console.error(
            "City loading error:",
            error
        );
    }
}

async function loadAreas(city = getCity()) {
    const areaSelect =
        document.getElementById(
            "areaFilter"
        );

    if (!areaSelect) {
        return;
    }

    const currentArea =
        areaSelect.value;

    areaSelect.innerHTML = `
        <option value="all">
            All Areas
        </option>
    `;

    try {
        const url =
            API_LATEST +
            buildQuery(
                city,
                "all",
                "all"
            );

        const data =
            await fetchJSON(
                url,
                10000
            );

        const areas =
            Array.isArray(data.areas)
                ? data.areas
                : [];

        areas.forEach(area => {
            const option =
                document.createElement("option");

            if (typeof area === "object") {
                option.value =
                    area.area || "";

                option.textContent =
                    area.area || "";
            }
            else {
                option.value = area;
                option.textContent = area;
            }

            areaSelect.appendChild(option);
        });

        const exists =
            [...areaSelect.options].some(
                option =>
                    option.value === currentArea
            );

        if (exists) {
            areaSelect.value =
                currentArea;
        }
    }
    catch (error) {
        console.error(
            "Area loading error:",
            error
        );
    }
}

async function loadPoints(
    city = getCity(),
    area = getArea()
) {
    const pointSelect =
        document.getElementById(
            "pointFilter"
        );

    if (!pointSelect) {
        return;
    }

    const currentPoint =
        pointSelect.value;

    pointSelect.innerHTML = `
        <option value="all">
            All Points
        </option>
    `;

    try {
        const url =
            API_LATEST +
            buildQuery(
                city,
                area,
                "all"
            );

        const data =
            await fetchJSON(
                url,
                10000
            );

        const points =
            Array.isArray(data.points)
                ? data.points
                : [];

        points.forEach(point => {
            const option =
                document.createElement("option");

            if (typeof point === "object") {
                option.value =
                    point.point_id || "";

                option.textContent =
                    point.area
                        ? `${point.point_id} — ${point.area}`
                        : point.point_id || "";
            }
            else {
                option.value = point;
                option.textContent = point;
            }

            pointSelect.appendChild(option);
        });

        const exists =
            [...pointSelect.options].some(
                option =>
                    option.value === currentPoint
            );

        if (exists) {
            pointSelect.value =
                currentPoint;
        }
    }
    catch (error) {
        console.error(
            "Point loading error:",
            error
        );
    }
}

async function handleCityChange() {
    const city = getCity();

    const areaSelect =
        document.getElementById(
            "areaFilter"
        );

    const pointSelect =
        document.getElementById(
            "pointFilter"
        );

    if (areaSelect) {
        areaSelect.innerHTML = `
            <option value="all">
                All Areas
            </option>
        `;
    }

    if (pointSelect) {
        pointSelect.innerHTML = `
            <option value="all">
                All Points
            </option>
        `;
    }

    await loadAreas(city);

    await loadPoints(
        city,
        "all"
    );

    await loadDashboard();

    await loadIncidents();
}

async function handleAreaChange() {
    const city = getCity();
    const area = getArea();

    await loadPoints(
        city,
        area
    );

    await loadDashboard();

    await loadIncidents();
}

async function handlePointChange() {
    await loadDashboard();

    await loadIncidents();
}

async function loadDashboard() {
    if (dashboardLoading) {
        return;
    }

    dashboardLoading = true;

    setLiveStatus(
        "updating",
        "LOADING TRAFFIC"
    );

    try {
        const city = getCity();
        const area = getArea();
        const point = getPoint();

        const url =
            API_LATEST +
            buildQuery(
                city,
                area,
                point
            );

        const data =
            await fetchJSON(
                url,
                10000
            );

        if (!data.success) {
            throw new Error(
                data.message ||
                "Dashboard API returned an error."
            );
        }

        const latest =
            Array.isArray(data.latest)
                ? data.latest
                : [];

        const history =
            Array.isArray(data.history)
                ? data.history
                : [];

        updateSummary(
            data.summary || {}
        );

        updateAreaTable(
            latest
        );

        updateHistory(
            history
        );

        updateMap(
            latest
        );

        updateLastUpdated(
            data.timestamp
        );

        await loadAnalytics(
            city,
            area,
            point
        );

        await loadHotspots();

        setLiveStatus(
            "success"
        );

        resetCountdown();
    }
    catch (error) {
        console.error(
            "Dashboard loading error:",
            error
        );

        setLiveStatus(
            "error",
            "CONNECTION ERROR"
        );

        showDashboardError(
            error.message
        );
    }
    finally {
        dashboardLoading = false;
    }
}

function updateSummary(summary) {
    const locations =
        document.getElementById(
            "locationsCount"
        );

    const low =
        document.getElementById(
            "lowCount"
        );

    const medium =
        document.getElementById(
            "mediumCount"
        );

    const high =
        document.getElementById(
            "highCount"
        );

    if (locations) {
        locations.textContent =
            summary.monitored_locations ?? 0;
    }

    if (low) {
        low.textContent =
            summary.low ?? 0;
    }

    if (medium) {
        medium.textContent =
            summary.medium ?? 0;
    }

    if (high) {
        high.textContent =
            summary.high ?? 0;
    }
}

async function loadAnalytics(
    city,
    area,
    point
) {
    try {
        const url =
            API_ANALYTICS +
            buildQuery(
                city,
                area,
                point
            );

        const data =
            await fetchJSON(
                url,
                10000
            );

        if (!data.success) {
            throw new Error(
                data.message ||
                "Analytics API error."
            );
        }

        updateAnalytics(
            data.overview || {}
        );

        updateDistributionChart(
            data.traffic_distribution || {}
        );

        updateCityTable(
            data.city_analytics || []
        );

        updateCharts(
            data.area_analytics || []
        );

        updateInsight(
            data.overview || {},
            data.traffic_distribution || {}
        );
    }
    catch (error) {
        console.error(
            "Analytics error:",
            error
        );
    }
}

function updateAnalytics(overview) {
    const averageSpeed =
        document.getElementById(
            "averageSpeed"
        );

    const averageReduction =
        document.getElementById(
            "averageReduction"
        );

    const averageConfidence =
        document.getElementById(
            "averageConfidence"
        );

    const highestReduction =
        document.getElementById(
            "highestReduction"
        );

    const highestLocation =
        document.getElementById(
            "highestLocation"
        );

    if (averageSpeed) {
        averageSpeed.textContent =
            `${formatNumber(
                overview.average_speed
            )} km/h`;
    }

    if (averageReduction) {
        averageReduction.textContent =
            `${formatNumber(
                overview.average_reduction
            )} %`;
    }

    if (averageConfidence) {
        averageConfidence.textContent =
            `${formatNumber(
                overview.average_confidence
            )} %`;
    }

    if (highestReduction) {
        highestReduction.textContent =
            `${formatNumber(
                overview.highest_reduction
            )} %`;
    }

    if (highestLocation) {
        highestLocation.textContent =
            overview.highest_reduction_location ||
            "No data";
    }

    const averageScore =
        document.getElementById(
            "averageScore"
        );

    const averageDelay =
        document.getElementById(
            "averageDelay"
        );

    if (averageScore) {
        averageScore.textContent =
            `${formatNumber(
                overview.average_score,
                2
            )} / 100`;
    }

    if (averageDelay) {
        averageDelay.textContent =
            `${formatNumber(
                overview.average_delay,
                2
            )} min`;
    }
}

function updateCityTable(cities) {
    const tbody =
        document.getElementById(
            "cityTable"
        );

    if (!tbody) {
        return;
    }

    tbody.innerHTML = "";

    if (
        !cities ||
        cities.length === 0
    ) {
        tbody.innerHTML = `
            <tr>
                <td
                    colspan="5"
                    class="text-center text-secondary py-4">
                    No city analytics available
                </td>
            </tr>
        `;

        return;
    }

    cities.forEach(city => {
        const row =
            document.createElement("tr");

        const trafficLevel =
            city.high > 0
                ? "HIGH"
                : city.medium > 0
                    ? "MEDIUM"
                    : "LOW";

        row.innerHTML = `
            <td>
                <strong>
                    ${escapeHTML(
                        city.city
                    )}
                </strong>
            </td>

            <td>
                ${city.locations ?? 0}
            </td>

            <td>
                ${formatNumber(
                    city.average_speed
                )}
                km/h
            </td>

            <td>
                ${formatNumber(
                    city.average_reduction
                )}%
            </td>

            <td>
                ${trafficBadge(
                    trafficLevel
                )}
            </td>
        `;

        tbody.appendChild(row);
    });
}

function updateAreaTable(records) {
    const tbody =
        document.getElementById(
            "areaTable"
        );

    if (!tbody) {
        return;
    }

    tbody.innerHTML = "";

    if (
        !records ||
        records.length === 0
    ) {
        tbody.innerHTML = `
            <tr>
                <td
                    colspan="9"
                    class="text-center text-secondary">
                    No traffic data available
                </td>
            </tr>
        `;

        return;
    }

    records.forEach(record => {
        const row =
            document.createElement("tr");

        const trafficStatus =
            record.traffic_status ||
            record.traffic_level ||
            "UNKNOWN";

        row.innerHTML = `
            <td>
                ${escapeHTML(
                    record.point_id
                )}
            </td>

            <td>
                <strong>
                    ${escapeHTML(
                        record.area
                    )}
                </strong>
            </td>

            <td>
                ${escapeHTML(
                    record.city
                )}
            </td>

            <td>
                ${formatNumber(
                    record.current_speed
                )}
                km/h
            </td>

            <td>
                ${formatNumber(
                    record.free_flow_speed
                )}
                km/h
            </td>

            <td>
                ${formatNumber(
                    record.speed_reduction
                )}%
            </td>

            <td>
                ${formatNumber(
                    record.confidence
                )}%
            </td>

            <td>
                ${trafficBadge(
                    trafficStatus
                )}
            </td>

            <td>
                ${closureBadge(
                    record.road_closure
                )}
            </td>
        `;

        tbody.appendChild(row);
    });
}

function updateHistory(records) {
    const tbody =
        document.getElementById(
            "historyTable"
        );

    if (!tbody) {
        return;
    }

    tbody.innerHTML = "";

    if (
        !records ||
        records.length === 0
    ) {
        tbody.innerHTML = `
            <tr>
                <td
                    colspan="7"
                    class="text-center text-secondary py-4">
                    No history available
                </td>
            </tr>
        `;

        return;
    }

    records
        .slice(0, 30)
        .forEach(record => {
            const row =
                document.createElement("tr");

            const trafficStatus =
                record.traffic_status ||
                record.traffic_level ||
                "UNKNOWN";

            row.innerHTML = `
                <td>
                    ${escapeHTML(
                        record.timestamp
                    )}
                </td>

                <td>
                    ${escapeHTML(
                        record.point_id
                    )}
                </td>

                <td>
                    ${escapeHTML(
                        record.area
                    )}
                </td>

                <td>
                    ${escapeHTML(
                        record.city
                    )}
                </td>

                <td>
                    ${formatNumber(
                        record.current_speed
                    )}
                    km/h
                </td>

                <td>
                    ${formatNumber(
                        record.speed_reduction
                    )}%
                </td>

                <td>
                    ${trafficBadge(
                        trafficStatus
                    )}
                </td>
            `;

            tbody.appendChild(row);
        });
}

function updateCharts(records) {
    const canvas =
        document.getElementById(
            "speedChart"
        );

    if (!canvas) {
        return;
    }

    if (speedChart) {
        speedChart.destroy();
        speedChart = null;
    }

    if (
        !records ||
        records.length === 0
    ) {
        return;
    }

    const labels =
        records.map(item => {
            const point =
                item.point_id || "";

            const area =
                item.area || "";

            return area
                ? `${point} • ${area}`
                : point;
        });

    const currentSpeed =
        records.map(item =>
            Number(
                item.current_speed || 0
            )
        );

    const freeFlowSpeed =
        records.map(item =>
            Number(
                item.free_flow_speed || 0
            )
        );

    speedChart =
        new Chart(
            canvas.getContext("2d"),
            {
                type: "bar",

                data: {
                    labels,

                    datasets: [
                        {
                            label:
                                "Current Speed",

                            data:
                                currentSpeed,

                            backgroundColor:
                                "rgba(5,150,105,0.82)",

                            borderRadius: 6
                        },

                        {
                            label:
                                "Free Flow Speed",

                            data:
                                freeFlowSpeed,

                            backgroundColor:
                                "rgba(217,119,6,0.78)",

                            borderRadius: 6
                        }
                    ]
                },

                options: {
                    responsive: true,

                    maintainAspectRatio: false,

                    interaction: {
                        mode: "index",
                        intersect: false
                    },

                    plugins: {
                        legend: {
                            labels: {
                                color:
                                    "#d1d5db"
                            }
                        },

                        tooltip: {
                            callbacks: {
                                label:
                                    function(context) {
                                        return (
                                            `${context.dataset.label}: ` +
                                            `${context.parsed.y} km/h`
                                        );
                                    }
                            }
                        }
                    },

                    scales: {
                        x: {
                            ticks: {
                                color:
                                    "#9ca3af",

                                maxRotation: 55,

                                minRotation: 25
                            },

                            grid: {
                                color:
                                    "#1f2937"
                            }
                        },

                        y: {
                            beginAtZero: true,

                            ticks: {
                                color:
                                    "#9ca3af"
                            },

                            grid: {
                                color:
                                    "#1f2937"
                            }
                        }
                    }
                }
            }
        );
}

function updateDistributionChart(distribution) {
    const canvas =
        document.getElementById(
            "distributionChart"
        );

    if (!canvas) {
        return;
    }

    if (distributionChart) {
        distributionChart.destroy();
        distributionChart = null;
    }

    const low =
        Number(
            distribution.LOW || 0
        );

    const medium =
        Number(
            distribution.MEDIUM || 0
        );

    const high =
        Number(
            distribution.HIGH || 0
        );

    distributionChart =
        new Chart(
            canvas.getContext("2d"),
            {
                type: "doughnut",

                data: {
                    labels: [
                        "LOW",
                        "MEDIUM",
                        "HIGH"
                    ],

                    datasets: [
                        {
                            data: [
                                low,
                                medium,
                                high
                            ],

                            backgroundColor: [
                                "#059669",
                                "#d97706",
                                "#dc2626"
                            ],

                            borderWidth: 0
                        }
                    ]
                },

                options: {
                    responsive: true,

                    maintainAspectRatio: false,

                    cutout: "68%",

                    plugins: {
                        legend: {
                            position: "bottom",

                            labels: {
                                color:
                                    "#d1d5db",

                                padding: 18
                            }
                        }
                    }
                }
            }
        );
}

async function loadHotspots() {
    try {
        const data =
            await fetchJSON(
                API_HOTSPOTS +
                "?limit=5",
                8000
            );

        if (!data.success) {
            throw new Error(
                data.message ||
                "Hotspots API error."
            );
        }

        updateHotspots(
            data.hotspots || []
        );
    }
    catch (error) {
        console.error(
            "Hotspots loading error:",
            error
        );

        updateHotspots([]);
    }
}

function updateHotspots(hotspots) {
    const container =
        document.getElementById(
            "hotspotsContainer"
        );

    if (!container) {
        return;
    }

    container.innerHTML = "";

    if (
        !Array.isArray(hotspots) ||
        hotspots.length === 0
    ) {
        container.innerHTML = `
            <div
                class="text-center text-secondary py-4">

                <i
                    class="bi bi-check-circle fs-3">
                </i>

                <div class="mt-2">
                    No traffic hotspots detected.
                </div>
            </div>
        `;

        return;
    }

    hotspots.forEach(
        (hotspot, index) => {
            const score =
                Number(
                    hotspot.traffic_score || 0
                );

            const delay =
                Number(
                    hotspot.delay_minutes || 0
                );

            const closure =
                hotspot.road_closure === true ||
                hotspot.road_closure === 1 ||
                hotspot.road_closure === "1" ||
                hotspot.road_closure === "true";

            const rank =
                index + 1;

            const rankClass =
                rank === 1
                    ? "hotspot-rank hotspot-rank-first"
                    : "hotspot-rank";

            const location =
                hotspot.area ||
                hotspot.point_id ||
                "Unknown Location";

            const city =
                hotspot.city ||
                "Unknown City";

            container.innerHTML += `
                <div class="hotspot-item">

                    <div class="${rankClass}">
                        ${rank}
                    </div>

                    <div class="hotspot-main">

                        <div class="hotspot-location">
                            ${escapeHTML(
                                location
                            )}
                        </div>

                        <div class="hotspot-city">
                            <i
                                class="bi bi-geo-alt">
                            </i>

                            ${escapeHTML(
                                city
                            )}
                        </div>

                        <div class="hotspot-meta">

                            <span>
                                Score:

                                <strong>
                                    ${formatNumber(
                                        score,
                                        2
                                    )}
                                </strong>
                            </span>

                            <span>
                                Delay:

                                <strong>
                                    ${formatNumber(
                                        delay,
                                        2
                                    )}
                                    min
                                </strong>
                            </span>
                        </div>
                    </div>

                    <div class="hotspot-status">

                        ${hotspotStatusBadge(
                            hotspot.traffic_status
                        )}

                        ${
                            closure
                                ? `
                                    <span
                                        class="
                                            closure-badge
                                            closure-yes
                                            mt-1
                                        "
                                    >
                                        ROAD CLOSED
                                    </span>
                                  `
                                : ""
                        }

                    </div>

                </div>
            `;
        }
    );
}

function getIncidentSection() {
    return document.getElementById(
        "incidents-section"
    );
}

function hideIncidentSection() {
    const section =
        getIncidentSection();

    if (section) {
        section.style.display = "none";
    }

    updateIncidentCount(0);
}

function showIncidentSection() {
    const section =
        getIncidentSection();

    if (section) {
        section.style.display = "";
    }
}

async function loadIncidents() {
    const container =
        document.getElementById(
            "incidentsContainer"
        );

    if (!container) {
        return;
    }

    try {
        const data =
            await fetchJSON(
                API_INCIDENTS,
                5000
            );

        if (!data.success) {
            throw new Error(
                data.message ||
                "Incidents API error."
            );
        }

        const incidents =
            Array.isArray(data.incidents)
                ? data.incidents
                : [];

        updateIncidents(
            incidents
        );
    }
    catch (error) {
        console.error(
            "Incidents loading error:",
            error
        );

        updateIncidents(
            [],
            true
        );
    }
}

function updateIncidents(
    incidents,
    hasError = false
) {
    const container =
        document.getElementById(
            "incidentsContainer"
        );

    if (!container) {
        hideIncidentSection();
        return;
    }

    if (
        hasError ||
        !Array.isArray(incidents) ||
        incidents.length === 0
    ) {
        container.innerHTML = "";
        hideIncidentSection();
        return;
    }

    showIncidentSection();

    container.innerHTML = "";

    updateIncidentCount(
        incidents.length
    );

    incidents.forEach(
        (incident, index) => {
            const score =
                Number(
                    incident.traffic_score || 0
                );

            const delay =
                Number(
                    incident.delay_minutes || 0
                );

            const currentSpeed =
                Number(
                    incident.current_speed || 0
                );

            const freeFlowSpeed =
                Number(
                    incident.free_flow_speed || 0
                );

            const reduction =
                Number(
                    incident.speed_reduction || 0
                );

            const closure =
                incident.road_closure === true ||
                incident.road_closure === 1 ||
                incident.road_closure === "1" ||
                incident.road_closure === "true";

            const severity =
                String(
                    incident.severity ||
                    "MEDIUM"
                ).toUpperCase();

            const incidentType =
                incident.incident_type ||
                "TRAFFIC INCIDENT";

            const location =
                incident.area ||
                incident.point_id ||
                "Unknown Location";

            const city =
                incident.city ||
                "Unknown City";

            const message =
                incident.message ||
                "Traffic incident detected.";

            const timestamp =
                incident.timestamp ||
                "Time unavailable";

            const icon =
                closure
                    ? "bi-sign-stop-fill"
                    : severity === "CRITICAL"
                        ? "bi-exclamation-octagon-fill"
                        : severity === "HIGH"
                            ? "bi-exclamation-triangle-fill"
                            : "bi-info-circle-fill";

            const item =
                document.createElement("div");

            item.className =
                `incident-item incident-${severity.toLowerCase()}`;

            item.innerHTML = `
                <div class="incident-icon">
                    <i class="bi ${icon}"></i>
                </div>

                <div class="incident-main">

                    <div class="incident-title-row">

                        <div class="incident-title">
                            ${escapeHTML(
                                incidentType
                            )}
                        </div>

                        ${incidentSeverityBadge(
                            severity
                        )}

                    </div>

                    <div class="incident-location">

                        <i class="bi bi-geo-alt-fill"></i>

                        <strong>
                            ${escapeHTML(
                                location
                            )}
                        </strong>

                        <span>
                            ${escapeHTML(
                                city
                            )}
                        </span>

                    </div>

                    <div class="incident-message">
                        ${escapeHTML(
                            message
                        )}
                    </div>

                    <div class="incident-meta">

                        <span>
                            <i class="bi bi-speedometer2"></i>
                            Speed:
                            <strong>
                                ${formatNumber(
                                    currentSpeed
                                )} km/h
                            </strong>
                        </span>

                        <span>
                            <i class="bi bi-signpost-2"></i>
                            Free Flow:
                            <strong>
                                ${formatNumber(
                                    freeFlowSpeed
                                )} km/h
                            </strong>
                        </span>

                        <span>
                            <i class="bi bi-graph-down-arrow"></i>
                            Reduction:
                            <strong>
                                ${formatNumber(
                                    reduction
                                )}%
                            </strong>
                        </span>

                        <span>
                            <i class="bi bi-clock-history"></i>
                            Delay:
                            <strong>
                                ${formatNumber(
                                    delay,
                                    2
                                )} min
                            </strong>
                        </span>

                        <span>
                            <i class="bi bi-speedometer"></i>
                            Score:
                            <strong>
                                ${formatNumber(
                                    score,
                                    2
                                )}/100
                            </strong>
                        </span>

                    </div>

                    <div class="incident-time">

                        <i class="bi bi-clock"></i>

                        ${escapeHTML(
                            timestamp
                        )}

                    </div>

                </div>

                <div class="incident-status">

                    ${incidentSeverityBadge(
                        severity
                    )}

                    ${
                        closure
                            ? `
                                <span
                                    class="
                                        closure-badge
                                        closure-yes
                                        incident-closure
                                    "
                                >
                                    <i class="bi bi-sign-stop-fill"></i>
                                    ROAD CLOSED
                                </span>
                              `
                            : ""
                    }

                </div>
            `;

            item.style.animationDelay =
                `${index * 60}ms`;

            container.appendChild(item);
        }
    );
}

function updateIncidentCount(count) {
    const badge =
        document.getElementById(
            "incidentCountBadge"
        );

    if (badge) {
        badge.textContent =
            `${count} Active`;

        if (count > 0) {
            badge.className =
                "badge rounded-pill bg-danger";
        }
        else {
            badge.className =
                "badge rounded-pill bg-secondary";
        }
    }

    const elements = [
        document.getElementById(
            "incidentCount"
        ),
        document.getElementById(
            "activeIncidentCount"
        )
    ];

    elements.forEach(element => {
        if (!element) {
            return;
        }

        element.textContent =
            count;
    });
}

function initializeMap() {
    if (map) {
        return;
    }

    const mapElement =
        document.getElementById(
            "trafficMap"
        );

    if (!mapElement) {
        console.error(
            "Traffic map element not found."
        );

        return;
    }

    if (typeof L === "undefined") {
        console.error(
            "Leaflet is not loaded."
        );

        return;
    }

    map =
        L.map(
            "trafficMap",
            {
                zoomControl: true,
                preferCanvas: true
            }
        ).setView(
            [15.9129, 79.7400],
            7
        );

    L.tileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
        {
            maxZoom: 19,

            attribution:
                "Tiles &copy; Esri — " +
                "Source: Esri, Garmin, FAO, NOAA, USGS, " +
                "OpenStreetMap contributors, " +
                "and the GIS User Community"
        }
    ).addTo(map);

    setTimeout(() => {
        if (map) {
            map.invalidateSize();
        }
    }, 300);
}

function getMarkerColor(
    status,
    level,
    closure
) {
    const isClosed =
        closure === true ||
        closure === 1 ||
        closure === "1" ||
        closure === "true";

    if (isClosed) {
        return "#dc2626";
    }

    const value =
        String(
            status ||
            level ||
            ""
        ).toUpperCase();

    if (
        value === "CRITICAL" ||
        value === "HEAVY" ||
        value === "HIGH"
    ) {
        return "#dc2626";
    }

    if (
        value === "MODERATE" ||
        value === "MEDIUM"
    ) {
        return "#d97706";
    }

    return "#059669";
}

function createTrafficIcon(color) {
    return L.divIcon({
        className:
            "custom-traffic-marker",

        html: `
            <div
                style="
                    width:22px;
                    height:22px;
                    border-radius:50%;
                    background:${color};
                    border:3px solid white;
                    box-shadow:
                        0 0 0 2px rgba(0,0,0,.35),
                        0 3px 12px rgba(0,0,0,.65);
                "
            >
            </div>
        `,

        iconSize: [
            22,
            22
        ],

        iconAnchor: [
            11,
            11
        ],

        popupAnchor: [
            0,
            -10
        ]
    });
}

function updateMap(records) {
    if (!map) {
        return;
    }

    markers.forEach(marker => {
        if (map.hasLayer(marker)) {
            map.removeLayer(marker);
        }
    });

    markers = [];

    if (
        !Array.isArray(records) ||
        records.length === 0
    ) {
        return;
    }

    const bounds = [];

    records.forEach(record => {
        const latitude =
            Number(
                record.latitude
            );

        const longitude =
            Number(
                record.longitude
            );

        if (
            !Number.isFinite(latitude) ||
            !Number.isFinite(longitude)
        ) {
            console.warn(
                "Invalid coordinates:",
                record
            );

            return;
        }

        const markerColor =
            getMarkerColor(
                record.traffic_status,
                record.traffic_level,
                record.road_closure
            );

        const icon =
            createTrafficIcon(
                markerColor
            );

        const marker =
            L.marker(
                [
                    latitude,
                    longitude
                ],
                {
                    icon: icon
                }
            ).addTo(map);

        const closure =
            record.road_closure === true ||
            record.road_closure === 1 ||
            record.road_closure === "1" ||
            record.road_closure === "true";

        const closureText =
            closure
                ? "YES"
                : "NO";

        const trafficStatus =
            record.traffic_status ||
            record.traffic_level ||
            "UNKNOWN";

        const trafficScore =
            Number(
                record.traffic_score || 0
            );

        const delayMinutes =
            Number(
                record.delay_minutes || 0
            );

        marker.bindPopup(`
            <div
                style="
                    min-width:270px;
                    line-height:1.65;
                    font-family:Arial,sans-serif;
                "
            >

                <div
                    style="
                        font-size:16px;
                        font-weight:700;
                        margin-bottom:4px;
                    "
                >
                    ${escapeHTML(
                        record.point_id ||
                        "Monitoring Point"
                    )}
                </div>

                <div
                    style="
                        font-size:13px;
                        color:#555;
                        margin-bottom:8px;
                    "
                >
                    ${escapeHTML(
                        record.area || ""
                    )}
                </div>

                <div>
                    <strong>
                        City:
                    </strong>

                    ${escapeHTML(
                        record.city || ""
                    )}
                </div>

                <div>
                    <strong>
                        Current Speed:
                    </strong>

                    ${formatNumber(
                        record.current_speed
                    )}

                    km/h
                </div>

                <div>
                    <strong>
                        Free Flow:
                    </strong>

                    ${formatNumber(
                        record.free_flow_speed
                    )}

                    km/h
                </div>

                <div>
                    <strong>
                        Reduction:
                    </strong>

                    ${formatNumber(
                        record.speed_reduction
                    )}%
                </div>

                <div>
                    <strong>
                        Confidence:
                    </strong>

                    ${formatNumber(
                        record.confidence
                    )}%
                </div>

                <div>
                    <strong>
                        Traffic Score:
                    </strong>

                    ${formatNumber(
                        trafficScore,
                        2
                    )}

                    / 100
                </div>

                <div>
                    <strong>
                        Status:
                    </strong>

                    ${escapeHTML(
                        trafficStatus
                    )}
                </div>

                <div>
                    <strong>
                        Delay:
                    </strong>

                    ${formatNumber(
                        delayMinutes,
                        2
                    )}

                    min
                </div>

                <div>
                    <strong>
                        Road Closure:
                    </strong>

                    ${closureText}
                </div>

                <hr style="margin:8px 0">

                <small>
                    ${escapeHTML(
                        record.timestamp || ""
                    )}
                </small>

            </div>
        `);

        markers.push(
            marker
        );

        bounds.push([
            latitude,
            longitude
        ]);
    });

    if (
        bounds.length === 1
    ) {
        map.setView(
            bounds[0],
            14
        );
    }
    else if (
        bounds.length > 1
    ) {
        map.fitBounds(
            bounds,
            {
                padding: [
                    40,
                    40
                ],

                maxZoom: 12
            }
        );
    }

    setTimeout(() => {
        if (map) {
            map.invalidateSize();
        }
    }, 200);
}

function updateLastUpdated(timestamp) {
    const element =
        document.getElementById(
            "lastUpdated"
        );

    if (!element) {
        return;
    }

    if (!timestamp) {
        element.textContent =
            "Last updated: —";

        return;
    }

    const date =
        new Date(timestamp);

    if (
        Number.isNaN(
            date.getTime()
        )
    ) {
        element.textContent =
            `Last updated: ${timestamp}`;

        return;
    }

    element.textContent =
        `Last updated: ${date.toLocaleString()}`;
}

function updateInsight(
    overview,
    distribution
) {
    const element =
        document.getElementById(
            "trafficInsight"
        );

    if (!element) {
        return;
    }

    const high =
        Number(
            distribution.HIGH || 0
        );

    const medium =
        Number(
            distribution.MEDIUM || 0
        );

    const low =
        Number(
            distribution.LOW || 0
        );

    const total =
        high +
        medium +
        low;

    if (total === 0) {
        element.textContent =
            "No traffic observations are currently available.";

        return;
    }

    const highestLocation =
        overview.highest_reduction_location ||
        "the monitored network";

    const highestReduction =
        formatNumber(
            overview.highest_reduction || 0
        );

    if (
        high > medium &&
        high > low
    ) {
        element.textContent =
            `Higher congestion is currently observed across the monitored network. ` +
            `The highest speed reduction is ${highestReduction}% at ` +
            `${highestLocation}.`;
    }
    else if (
        medium >= high &&
        medium >= low
    ) {
        element.textContent =
            `Moderate traffic conditions are currently dominant across the ` +
            `monitored network. The highest speed reduction is ` +
            `${highestReduction}% at ${highestLocation}.`;
    }
    else {
        element.textContent =
            `Traffic conditions are currently mostly normal across the ` +
            `monitored network. The highest observed speed reduction is ` +
            `${highestReduction}% at ${highestLocation}.`;
    }
}

function showDashboardError(message) {
    console.error(
        "Dashboard error:",
        message
    );

    const areaTable =
        document.getElementById(
            "areaTable"
        );

    if (areaTable) {
        areaTable.innerHTML = `
            <tr>
                <td
                    colspan="9"
                    class="text-center text-danger py-4"
                >
                    ${escapeHTML(
                        message ||
                        "Unable to load traffic data."
                    )}
                </td>
            </tr>
        `;
    }

    const historyTable =
        document.getElementById(
            "historyTable"
        );

    if (historyTable) {
        historyTable.innerHTML = `
            <tr>
                <td
                    colspan="7"
                    class="text-center text-danger py-4"
                >
                    Traffic history unavailable.
                </td>
            </tr>
        `;
    }

    const hotspotsContainer =
        document.getElementById(
            "hotspotsContainer"
        );

    if (hotspotsContainer) {
        hotspotsContainer.innerHTML = `
            <div
                class="text-center text-danger py-4">

                <i
                    class="bi bi-exclamation-triangle">
                </i>

                <div class="mt-2">
                    Traffic hotspot data unavailable.
                </div>
            </div>
        `;
    }

    hideIncidentSection();
}

async function manualRefresh() {
    if (refreshInProgress) {
        return;
    }

    refreshInProgress = true;

    setLiveStatus(
        "updating",
        "REFRESHING DATA"
    );

    const button =
        document.getElementById(
            "refreshButton"
        );

    if (button) {
        button.disabled = true;

        button.classList.add(
            "refreshing"
        );
    }

    try {
        try {
            const refreshResponse =
                await fetch(
                    API_REFRESH,
                    {
                        method: "GET",

                        headers: {
                            "Accept":
                                "application/json"
                        },

                        cache: "no-store"
                    }
                );

            if (
                refreshResponse.ok
            ) {
                const refreshData =
                    await refreshResponse.json();

                console.log(
                    "Traffic refresh response:",
                    refreshData
                );
            }
        }
        catch (refreshError) {
            console.warn(
                "Optional refresh endpoint unavailable:",
                refreshError
            );
        }

        await loadDashboard();

        await loadIncidents();

        resetCountdown();
    }
    catch (error) {
        console.error(
            "Manual refresh error:",
            error
        );
    }
    finally {
        refreshInProgress = false;

        if (button) {
            button.disabled = false;

            button.classList.remove(
                "refreshing"
            );
        }
    }
}

function startAutoRefresh() {
    if (autoRefreshTimer) {
        clearInterval(
            autoRefreshTimer
        );
    }

    countdownSeconds = 60;

    updateCountdown();

    autoRefreshTimer =
        setInterval(
            async () => {
                countdownSeconds--;

                if (
                    countdownSeconds <= 0
                ) {
                    countdownSeconds = 60;

                    if (
                        !refreshInProgress &&
                        !dashboardLoading
                    ) {
                        await manualRefresh();
                    }
                    else {
                        await loadIncidents();
                    }
                }

                updateCountdown();
            },
            1000
        );
}

function setupEventListeners() {
    const cityFilter =
        document.getElementById(
            "cityFilter"
        );

    const areaFilter =
        document.getElementById(
            "areaFilter"
        );

    const pointFilter =
        document.getElementById(
            "pointFilter"
        );

    const refreshButton =
        document.getElementById(
            "refreshButton"
        );

    if (cityFilter) {
        cityFilter.addEventListener(
            "change",
            handleCityChange
        );
    }

    if (areaFilter) {
        areaFilter.addEventListener(
            "change",
            handleAreaChange
        );
    }

    if (pointFilter) {
        pointFilter.addEventListener(
            "change",
            handlePointChange
        );
    }

    if (refreshButton) {
        refreshButton.addEventListener(
            "click",
            manualRefresh
        );
    }
}

async function initializeDashboard() {
    console.log(
        "AP Traffic Intelligence Dashboard initializing..."
    );

    hideIncidentSection();

    if (
        typeof L === "undefined"
    ) {
        console.error(
            "Leaflet is not loaded."
        );

        setLiveStatus(
            "error",
            "LEAFLET NOT LOADED"
        );

        return;
    }

    if (
        typeof Chart === "undefined"
    ) {
        console.error(
            "Chart.js is not loaded."
        );

        setLiveStatus(
            "error",
            "CHART.JS NOT LOADED"
        );

        return;
    }

    initializeMap();

    setupEventListeners();

    await loadCities();

    await loadAreas(
        getCity()
    );

    await loadPoints(
        getCity(),
        getArea()
    );

    await loadDashboard();

    await loadIncidents();

    startAutoRefresh();

    console.log(
        "AP Traffic Intelligence Dashboard ready."
    );
}

document.addEventListener(
    "DOMContentLoaded",
    initializeDashboard
);