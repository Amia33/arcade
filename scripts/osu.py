"""Resolver for osu"""

from datetime import datetime
import os
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv, set_key
from pymongo.mongo_client import MongoClient
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import requests


def requests_session():
    """Create a requests session"""
    session = requests.Session()
    retry = Retry(
        total=10,
        read=10,
        connect=10,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def requests_retry(url, timeout, headers):
    """Adapter for retry to work properly"""
    session = requests_session()
    return session.get(url, timeout=timeout, headers=headers)


def get_token():
    """Get access_token"""
    load_dotenv(".env")
    url = "https://osu.ppy.sh/oauth/token"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload = "client_id="+os.getenv("CLIENT_ID")+"&client_secret="+os.getenv("CLIENT_SECRET") +\
        "&code="+os.getenv("CODE")+"&grant_type=authorization_code&redirect_uri=" +\
        os.getenv("REDIRECT_URI")
    resp = requests.post(url=url, headers=headers, data=payload, timeout=15)
    set_key(".env", "ACCESS_TOKEN", resp.json()["access_token"])
    set_key(".env", "REFRESH_TOKEN", resp.json()["refresh_token"])
    return resp.json()["access_token"]


def refresh_token():
    """Refresh access_token"""
    load_dotenv(".env")
    url = "https://osu.ppy.sh/oauth/token"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload = "client_id="+os.getenv("CLIENT_ID")+"&client_secret="+os.getenv("CLIENT_SECRET") +\
        "&code="+os.getenv("CODE")+"&grant_type=refresh_token&refresh_token=" +\
        os.getenv("REFRESH_TOKEN")+"&scope=identify+public"
    resp = requests.post(url=url, headers=headers, data=payload, timeout=15)
    print(resp.json())
    set_key(".env", "ACCESS_TOKEN", resp.json()["access_token"])
    set_key(".env", "REFRESH_TOKEN", resp.json()["refresh_token"])
    return resp.json()["access_token"]


def load_token():
    """Load access_token"""
    load_dotenv(".env")
    return os.getenv("ACCESS_TOKEN")


def extract_links():
    """Extract links from file"""
    with open("osu/player_data.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    soup = BeautifulSoup(html_content, "html.parser")
    ms = []
    m = []
    for link in soup.find_all("a", class_="beatmap-playcount__title"):
        mapdata = re.findall(r"[0-9]+", link.get("href"))
        if mapdata[0] not in ms:
            ms.append(mapdata[0])
        m.append(mapdata[1])
    return ms, m


def create_mapset(msid, acctoken):
    """Create mapset data"""
    url = "https://osu.ppy.sh/api/v2/beatmapsets/"+msid
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Bearer "+acctoken
    }
    resp = requests_retry(url, 15, headers)
    collected = resp.json()
    return construct_mapset(collected), construct_map(collected["beatmaps"])


def construct_mapset(codata):
    """Construct mapset data"""
    new_mapset = {
        "mapset_id": codata["id"],
        "title": codata["title_unicode"],
        "artist": codata["artist_unicode"],
        "source": codata["source"],
        "ranked": codata["ranked"],
        "creator_id": codata["user_id"],
        "datetime": {
            "submitted": parse_datetime(codata["submitted_date"]),
            "updated": parse_datetime(codata["last_updated"]),
            "ranked": parse_datetime(codata["ranked_date"]),
        },
        "video": codata["video"],
        "storyboard": codata["storyboard"],
        "genre": codata["genre"]["id"],
        "language": codata["language"]["id"],
        "nsfw": codata["nsfw"],
        "tags": codata["tags"].split(" "),
        "statistics": {
            "play_count": codata["play_count"],
            "favourite": codata["favourite_count"],
            "rating": float(codata["rating"])
        }
    }
    return new_mapset


def parse_datetime(jsondate):
    """Correctly parse datetime object"""
    try:
        dt = datetime.fromisoformat(jsondate.replace('Z', '+00:00'))
        return dt
    except AttributeError:
        return None


def construct_map(codata):
    """Construct map data"""
    new_map = []
    for item in codata:
        new_map_data = {
            "map_id": item["id"],
            "diff_name": item["version"],
            "diff_creator_id": item["user_id"],
            "mapset_id": item["beatmapset_id"],
            "mode": item["mode_int"],
            "ranked": item["ranked"],
            "creator_id": item["user_id"],
            "updated": parse_datetime(item["last_updated"]),
            "statistics": {
                "self_playcount": 0,
                "star_rating": float(item["difficulty_rating"]),
                "full_length": item["total_length"],
                "hit_length": item["hit_length"],
                "bpm": float(item["bpm"]),
                "max_combo": item["max_combo"],
                "circles": item["count_circles"],
                "sliders": item["count_sliders"],
                "spinners": item["count_spinners"],
                "circle_size": float(item["cs"]),
                "hp_drain": float(item["drain"]),
                "accuracy": float(item["accuracy"]),
                "approach_rate": float(item["ar"]),
                "play_count": item["playcount"],
                "pass_count": item["passcount"]
            }
        }
        new_map.append(new_map_data)
    return new_map


def create_scores(mapid, acctoken, uid):
    """Create score data"""
    url = "https://osu.ppy.sh/api/v2/beatmaps/" + \
        mapid+"/scores/users/"+uid+"/all"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Bearer "+acctoken
    }
    resp = requests_retry(url, 15, headers)
    new_scores = []
    try:
        collected = resp.json()["scores"]
    except KeyError:
        return new_scores
    for item in collected:
        try:
            pp = float(item["pp"])
        except TypeError:
            pp = float(0)
        new_score = {
            "replay": item["replay"],
            "map_id": int(mapid),
            "mode": item["mode_int"],
            "active_mods": item["mods"],
            "datetime": parse_datetime(item["created_at"]),
            "score": item["score"],
            "accuracy": float(item["accuracy"]),
            "pp": pp,
            "statistics": {
                "webui_id": item["current_user_attributes"]["pin"]["score_id"],
                "fullcombo": item["perfect"],
                "max_combo": item["max_combo"],
                "rank": item["rank"],
                "300": item["statistics"]["count_300"],
                "100": item["statistics"]["count_100"],
                "50": item["statistics"]["count_50"],
                "miss": item["statistics"]["count_miss"],
                "geki": item["statistics"]["count_geki"],
                "katu": item["statistics"]["count_katu"]
            }
        }
        new_scores.append(new_score)
    return new_scores


def update_self_playcount(db, mapid, acctoken):
    """Update self playcount"""
    url = "https://osu.ppy.sh/api/v2/beatmaps/"+mapid
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Bearer "+acctoken
    }
    resp = requests_retry(url, 15, headers)
    collected = resp.json()["current_user_playcount"]
    query = {
        "map_id": int(mapid)
    }
    update = {
        "$set": {
            "statistics.self_playcount": collected
        }
    }
    db["maps"].update_one(query, update)


# Run get_token() only FIRST TIME, run refresh_token() DAILY
# access_token = get_token()
# access_token = refresh_token()
access_token = load_token()
mapsets, maps = extract_links()
user_id = os.getenv("SELECT_USER_ID")
mongo_cli = MongoClient(os.getenv("MONGODB_URI"))
mongo_db = mongo_cli["osu"]
mapsets_data = []
maps_data = []
scores_data = []
for mapset_id in mapsets:
    print("Processing beatmapset: "+mapset_id)
    mapset_data, map_data = create_mapset(mapset_id, access_token)
    mapsets_data.append(mapset_data)
    maps_data.extend(map_data)
mongo_db["mapsets"].insert_many(mapsets_data)
mongo_db["maps"].insert_many(maps_data)
for map_id in maps:
    print("Processing beatmap: "+map_id)
    map_scores = create_scores(map_id, access_token, user_id)
    update_self_playcount(mongo_db, map_id, access_token)
    scores_data.extend(map_scores)
mongo_db["scores"].insert_many(scores_data)
mongo_cli.close()
