from django.urls import path

from . import views


urlpatterns = [

    path(
        "",
        views.dashboard,
        name="dashboard"
    ),

    path(
        "api/traffic/refresh/",
        views.refresh_traffic,
        name="refresh_traffic"
    ),

    path(
        "api/traffic/latest/",
        views.latest_traffic,
        name="latest_traffic"
    ),

    path(
        "api/traffic/analytics/",
        views.traffic_analytics,
        name="traffic_analytics"
    ),

    path(
        "api/traffic/hotspots/",
        views.traffic_hotspots,
        name="traffic_hotspots"
    ),

    path(
    "api/traffic/incidents/",
    views.traffic_incidents,
    name="traffic_incidents"
    ),
]