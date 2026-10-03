import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TOMTOM_API_KEY")

# Visakhapatnam test location
POINT = "17.6868,83.2185"

url = (
    "https://api.tomtom.com/traffic/services/4/"
    "flowSegmentData/absolute/10/json"
)

params = {
    "key": API_KEY,
    "point": POINT
}

response = requests.get(url, params=params, timeout=10)

print("=" * 40)
print("       TRAFFIC DENSITY MONITOR")
print("=" * 40)

if response.status_code != 200:
    print("API request failed!")
    print("Status Code:", response.status_code)
    print(response.text)
    exit()

data = response.json()

flow = data["flowSegmentData"]

current_speed = flow["currentSpeed"]
free_flow_speed = flow["freeFlowSpeed"]
current_travel_time = flow["currentTravelTime"]
free_flow_travel_time = flow["freeFlowTravelTime"]
confidence = flow["confidence"]
road_closure = flow["roadClosure"]

# Calculate speed reduction
if free_flow_speed > 0:
    speed_reduction = (
        (free_flow_speed - current_speed)
        / free_flow_speed
    ) * 100
else:
    speed_reduction = 0

# Convert seconds to minutes
current_minutes = current_travel_time / 60
free_flow_minutes = free_flow_travel_time / 60

# Basic traffic classification
if speed_reduction < 20:
    traffic_level = "LOW"
elif speed_reduction < 50:
    traffic_level = "MEDIUM"
else:
    traffic_level = "HIGH"

print(f"Current Speed       : {current_speed} km/h")
print(f"Free Flow Speed     : {free_flow_speed} km/h")
print(f"Speed Reduction     : {speed_reduction:.2f}%")

print(f"Current Travel Time : {current_minutes:.2f} min")
print(f"Free Flow Time      : {free_flow_minutes:.2f} min")

print(f"Confidence           : {confidence * 100:.2f}%")

if road_closure:
    print("Road Closure         : YES")
else:
    print("Road Closure         : NO")

print(f"Traffic Level        : {traffic_level}")

print("=" * 40)