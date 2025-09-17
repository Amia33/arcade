"""Resolver for maimai otogame"""

from datetime import datetime, timezone
import json
import os
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient


def create_client():
    """Create a mongodb client"""
    load_dotenv(".env")
    return MongoClient(os.getenv("MONGODB_URI"))


def load_json(file_id):
    """Load json file"""
    with open("otogame/"+str(file_id)+".json", "r", encoding="utf-8") as f:
        json_data = json.load(f)
    json_data.reverse()
    return json_data


def parse_music(db, music_item):
    """Parse music data from item"""
    music_colle = db["songs"]
    query_result = music_colle.find_one(
        {
            "name": music_item["name"],
            "artist": music_item["artist"],
            "deluxe": music_item["is_deluxe"]
        }
    )
    if query_result:
        return query_result["_id"]
    new_song = {
        "name": music_item["name"],
        "artist": music_item["artist"],
        "deluxe": music_item["is_deluxe"]
    }
    insert_result = music_colle.insert_one(new_song)
    return insert_result.inserted_id


def parse_score(music, score_item, scores):
    """Parse score data from item"""
    if score_item["is_perfect_challenge"]:
        challenge_type = 1
    elif score_item["is_course"]:
        challenge_type = 2
    elif score_item["is_kaleidx"]:
        challenge_type = 3
    else:
        challenge_type = 0
    new_score = {
        "song_id": music,
        "difficulty": score_item["difficulty"],
        "track": score_item["track_no"],
        "play_datetime": datetime.fromtimestamp(score_item["play_date"], tz=timezone.utc),
        "achievement": score_item["achievement"],
        "dxscore": score_item["deluxe_score"],
        "combo": {
            "status": score_item["combo_status"],
            "actual": score_item["max_combo"],
            "max": score_item["total_combo"]
        },
        "challenge": {
            "type": challenge_type,
            "result_life": score_item["life"],
            "start_life": score_item["total_life"]
        },
        "fast": score_item["fast_count"],
        "late": score_item["late_count"],
        "tap": [
            score_item["tap_critical_perfect"],
            score_item["tap_perfect"],
            score_item["tap_great"],
            score_item["tap_good"],
            score_item["tap_miss"]
        ],
        "hold": [
            score_item["hold_critical_perfect"],
            score_item["hold_perfect"],
            score_item["hold_great"],
            score_item["hold_good"],
            score_item["hold_miss"]
        ],
        "slide": [
            score_item["slide_critical_perfect"],
            score_item["slide_perfect"],
            score_item["slide_great"],
            score_item["slide_good"],
            score_item["slide_miss"]
        ],
        "touch": [
            score_item["touch_critical_perfect"],
            score_item["touch_perfect"],
            score_item["touch_great"],
            score_item["touch_good"],
            score_item["touch_miss"]
        ],
        "break": [
            score_item["break_critical_perfect"],
            score_item["break_perfect"],
            score_item["break_great"],
            score_item["break_good"],
            score_item["break_miss"]
        ]
    }
    scores.append(new_score)


mongo_cli = create_client()
mongo_db = mongo_cli["otogame"]
scores_new = []
for i in range(1, 0, -1):
    data = load_json(i)
    for item in data:
        print("Processing: "+item["music"]["name"])
        music_id = parse_music(mongo_db, item["music"])
        parse_score(music_id, item, scores_new)
mongo_db["scores"].insert_many(scores_new)
mongo_cli.close()
