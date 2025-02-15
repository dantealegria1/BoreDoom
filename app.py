from flask import Flask, jsonify, request
from flask_cors import CORS  # Add this import
from typing import Dict, List, Tuple, Optional
import random
import json
from datetime import datetime
import requests

app = Flask(__name__)
CORS(app)  # Enable CORS

# GitHub repository configuration
GITHUB_REPO = "dantealegria1/BoreDoom"
GITHUB_BRANCH = "main"
ACTIVITIES_FILE = "activities.json"

# Enhanced categories with more options
categories = {
    "location": ["Indoor", "Outdoor", "Virtual", "Urban", "Nature"],
    "people": ["Solo", "Pair", "Small Group", "Large Group", "Family"],
    "type": ["Physical", "Creative", "Relaxing", "Educational", "Social", "Technical", "Musical", "Culinary"],
    "duration": ["Quick (15min)", "Short (30min)", "Medium (1hr)", "Long (2hr+)"]
}

# Initialize empty activities database
activities_db = {}

def fetch_activities_from_github() -> None:
    """Fetch activities from GitHub repository."""
    try:
        # Construct the raw GitHub content URL
        github_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{ACTIVITIES_FILE}"
        print(f"Fetching from URL: {github_url}")  # Debug print
        
        # Fetch the content
        response = requests.get(github_url)
        print(f"Response status: {response.status_code}")  # Debug print
        response.raise_for_status()
        
        # Parse the JSON content
        global activities_db
        activities_db = json.loads(response.text)
        print(f"Loaded {len(activities_db)} activities")  # Debug print
        
        # Convert dictionary keys from strings back to tuples
        activities_db = {tuple(eval(k)): v for k, v in activities_db.items()}
        
    except requests.RequestException as e:
        print(f"Error fetching activities from GitHub: {e}")
        load_default_activities()
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON from GitHub: {e}")
        load_default_activities()
    except Exception as e:
        print(f"Unexpected error: {e}")
        load_default_activities()

def load_default_activities() -> None:
    """Load default activities if GitHub fetch fails."""
    global activities_db
    activities_db = {
        ("Indoor", "Solo", "Creative", "Medium (1hr)"): [
            {"name": "Draw a self-portrait", "description": "Express yourself through art"},
            {"name": "Write a short story", "description": "Create a fictional narrative"},
            {"name": "Learn origami", "description": "Master the art of paper folding"}
        ],
        ("Outdoor", "Small Group", "Physical", "Long (2hr+)"): [
            {"name": "Organize a scavenger hunt", "description": "Create and solve outdoor riddles"},
            {"name": "Start a hiking club", "description": "Explore nature trails together"},
            {"name": "Beach volleyball", "description": "Play a fun beach sport"}
        ]
    }
    print("Loaded default activities")  # Debug print

@app.route('/')
def home():
    """Home route to verify API is working."""
    return jsonify({
        "message": "Welcome to the Activities API",
        "endpoints": {
            "/activity": "Get a random activity",
            "/categories": "List all categories",
            "/stats": "Get activity statistics",
            "/refresh": "Refresh activities from GitHub"
        }
    })

@app.route('/activity', methods=['GET'])
def get_activity():
    """Get a random activity with optional filtering."""
    try:
        if not activities_db:
            fetch_activities_from_github()
            
        preferences = {}
        for category in categories.keys():
            if request.args.get(category):
                preferences[category] = request.args.get(category)
        
        return jsonify(generate_activity(preferences))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Rest of your code remains the same...

def generate_activity(preferences: Optional[Dict] = None) -> Dict:
    """Generate an activity based on user preferences."""
    if not activities_db:
        load_default_activities()
        
    if preferences:
        possible_combos = [
            combo for combo in activities_db.keys()
            if all(pref in combo for pref in preferences.values())
        ]
        if possible_combos:
            combo = random.choice(possible_combos)
        else:
            combo = random.choice(list(activities_db.keys()))
    else:
        combo = random.choice(list(activities_db.keys()))

    activity = random.choice(activities_db[combo])
    
    return {
        "activity": activity["name"],
        "description": activity["description"],
        "category": {
            "location": combo[0],
            "people": combo[1],
            "type": combo[2],
            "duration": combo[3]
        },
        "timestamp": datetime.now().isoformat()
    }

@app.route('/categories', methods=['GET'])
def get_categories():
    """Get all available categories and their options."""
    return jsonify(categories)

@app.route('/refresh', methods=['POST'])
def refresh_activities():
    """Refresh activities from GitHub."""
    fetch_activities_from_github()
    return jsonify({"message": "Activities refreshed successfully"}), 200

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get statistics about the activities database."""
    if not activities_db:
        fetch_activities_from_github()
        
    total_activities = sum(len(activities) for activities in activities_db.values())
    stats = {
        "total_activities": total_activities,
        "categories_count": {k: len(v) for k, v in categories.items()},
        "activities_per_type": {},
    }
    
    for combo in activities_db:
        activity_type = combo[2]
        if activity_type not in stats["activities_per_type"]:
            stats["activities_per_type"][activity_type] = 0
        stats["activities_per_type"][activity_type] += len(activities_db[combo])
    
    return jsonify(stats)

if __name__ == '__main__':
    fetch_activities_from_github()
    app.run(debug=True, host='0.0.0.0', port=8000)
