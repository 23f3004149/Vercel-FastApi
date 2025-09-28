# api/index.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import pandas as pd

# Initialize the FastAPI app
app = FastAPI()

# Enable CORS to allow requests from any origin, as required
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Load your JSON data into a pandas DataFrame when the app starts
# This is efficient because it only happens once
df = pd.read_json("api/q-vercel-latency.json")

# Define the structure of the incoming request body for validation
class LatencyRequest(BaseModel):
    regions: List[str]
    threshold_ms: int

# Define the main POST endpoint. Vercel will make this available at /api
@app.post("/api")
async def get_latency_metrics(request: LatencyRequest):
    results = {}
    for region in request.regions:
        # Filter the DataFrame for the current region
        region_df = df[df['region'] == region]

        # If the region has no data, skip it
        if region_df.empty:
            continue

        # Calculate the required metrics using pandas
        avg_latency = region_df['latency_ms'].mean()
        p95_latency = region_df['latency_ms'].quantile(0.95)
        avg_uptime = region_df['uptime_pct'].mean()
        breaches = (region_df['latency_ms'] > request.threshold_ms).sum()

        # Store the results for the current region
        # Convert numpy types to standard Python types for JSON response
        results[region] = {
            "avg_latency": float(avg_latency),
            "p95_latency": float(p95_latency),
            "avg_uptime": float(avg_uptime),
            "breaches": int(breaches)
        }
        
    return results