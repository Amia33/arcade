"""Resolver for maimai otogame"""

import json
import os
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient


def create_client():
    """Create a mongodb client"""
    load_dotenv(".env")
    return MongoClient(os.getenv("MONGODB_URI"))


def update_song(db):
    """Update music data"""
    music_colle = db["songs"]
    with open("dx2025/music.json", "r", encoding="utf-8") as f:
        music_data = json.load(f)
    for music in music_data:
        print("Processing: "+music["basic_info"]["title"])
        if music["type"] == "DX":
            music_type = 1
        else:
            music_type = 0
        query_result = music_colle.find_one(
            {
                "name": music["basic_info"]["title"],
                "artist": music["basic_info"]["artist"],
                "deluxe": music_type
            }
        )
        if not query_result:
            new_song = {
                "name": music["basic_info"]["title"],
                "artist": music["basic_info"]["artist"],
                "deluxe": music_type,
                "genre": music["basic_info"]["genre"],
                "bpm": music["basic_info"]["bpm"],
                "game_version": music["basic_info"]["from"],
                "game_id": music["id"],
                "difficulties": music["ds"],
                "notes_info": music["charts"]
            }
            music_colle.insert_one(new_song)


def update_score(db):
    """Update score data"""
    new_records = []
    record_colle = db["scores"]
    with open("dx2025/record.json", "r", encoding="utf-8") as f:
        record_data = json.load(f)
    for record in record_data:
        print("Processing: "+str(record["song_id"]))
        if record["fc"] == "fc":
            combo_status = 1
        elif record["fc"] == "fcp":
            combo_status = 2
        elif record["fc"] == "ap":
            combo_status = 3
        elif record["fc"] == "app":
            combo_status = 4
        else:
            combo_status = 0
        query_result = record_colle.find_one(
            {
                "song_id": record["song_id"],
                "difficulty": record["level_index"]
            }
        )
        if query_result:
            score_id = query_result["_id"]
            record_colle.update_one(
                {
                    "_id": score_id
                },
                {
                    "$set":
                        {
                            "achievement": record["achievements"],
                            "dxscore": record["dxScore"],
                            "combo_status": combo_status,
                            "rating": record["ra"]
                        }
                }
            )
        else:
            new_record = {
                "song_id": record["song_id"],
                "difficulty": record["level_index"],
                "achievement": record["achievements"],
                "dxscore": record["dxScore"],
                "combo_status": combo_status,
                "rating": record["ra"]
            }
            new_records.append(new_record)
    if new_records:
        record_colle.insert_many(new_records)


mongo_cli = create_client()
mongo_db = mongo_cli["dx2025"]
update_song(mongo_db)
update_score(mongo_db)
mongo_cli.close()
