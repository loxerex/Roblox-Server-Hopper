import json
import os
import sys
import time
import typing
from threading import Thread

import keyboard
import requests
from rblib import r_client


def resource_path(relative):
    if getattr(sys, "frozen", False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative)


id = None
Order = None
retry_time = None
refresh_cache = None
hop_key = None

load_json = False
client = r_client.RobloxClient()

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
WHITE = "\033[97m"
RESET = "\033[0m"

print(f"""{CYAN}

▄▄▄▄▄▄▄    ▄▄▄▄▄▄▄ ▄▄▄   ▄▄▄
███▀▀███▄ █████▀▀▀ ███   ███
███▄▄███▀  ▀████▄  █████████
███▀▀██▄     ▀████ ███▀▀▀███
███  ▀███ ███████▀ ███   ███
{MAGENTA}    Roblox Server Hopper by LoxerEx
{RESET}""")
if os.path.exists(resource_path("user_data.json")):
    print(f"{YELLOW}Would you like to use a saved json? [y/n]{RESET}")

    if (ind := input(f"{BLUE}>{RESET}").lower()) in ("yes", "y"):
        load_json = True
        json_d = None
        with open(resource_path("user_data.json"), "r") as f:
            json_d = json.load(f)
        print(f"{GREEN}Saved Aliases: {list(json_d.keys())}{RESET}")
        print(f"{CYAN}Enter alias name:{RESET}")
        selected_data = None
        while not selected_data:
            if data := json_d.get(input(f"{BLUE}>{RESET}")):
                print(f"{MAGENTA}{data}{RESET}")
                id = data["id"]
                Order = data["order"]
                retry_time = data["rt_time"]
                refresh_cache = data["rf_cache"]
                hop_key = data["hop_key"]
                selected_data = True

if not load_json:
    print(f"{CYAN}Press the key you want to serverhop with:{RESET}")
    while hop_key is None:
        try:
            kb = keyboard.read_key()
            if kb == "enter":
                continue
            print(f"{GREEN}Pressed:{RESET} {YELLOW}{kb}{RESET}")
            print(f"{MAGENTA}Would you like {kb} to be your hop key? [y/n]{RESET}")
            if (ind := input(f"{BLUE}>{RESET}").lower()) in ("yes", "y"):
                hop_key = kb
        except Exception:
            pass

    print(f"{CYAN}Insert game id:{RESET}")
    while id is None:
        try:
            id = int(input(f"{BLUE}>{RESET}"))
        except Exception:
            pass

    print(
        f"{CYAN}Server Sort Order: {RESET}{YELLOW}[1: Ascending, 2: Descending]{RESET}"
    )
    while Order is None:
        try:
            _ui = int(input(f"{BLUE}>{RESET}"))
            if _ui in (1, 2):
                Order = _ui
        except Exception:
            pass

    print(f"{CYAN}Enter retry delay before pulling server list again:{RESET}")
    while retry_time is None:
        try:
            retry_time = int(input(f"{BLUE}>{RESET}"))
        except Exception:
            pass

    print(f"{CYAN}Enter how many retries until cache refresh:{RESET}")
    while refresh_cache is None:
        try:
            refresh_cache = int(input(f"{BLUE}>{RESET}"))
        except Exception:
            pass

    print(f"{YELLOW}Save this configuration to JSON? [y/n]{RESET}")
    if (ind := input(f"{BLUE}>{RESET}").lower()) in ("yes", "y"):
        print(f"{CYAN}Enter alias name:{RESET}")
        alias = input(f"{BLUE}>{RESET}")
        json_data = {
            alias: {
                "id": id,
                "order": Order,
                "rt_time": retry_time,
                "rf_cache": refresh_cache,
                "hop_key": hop_key,
            }
        }
        if not os.path.exists(resource_path("user_data.json")):
            with open(resource_path("user_data.json"), "w") as f:
                json.dump(json_data, f, indent=2)
        else:
            p_data = None
            with open(resource_path("user_data.json"), "r") as f:
                p_data = json.load(f)
            p_data[alias] = json_data[alias]
            with open(resource_path("user_data.json"), "w") as f:
                json.dump(p_data, f, indent=2)

endpoint = f"https://games.roblox.com/v1/games/{id}/servers/0?sortOrder={Order}&excludeFullGames=true&limit=100"
cached_cusor = None
job_id_cache = []
job_id_blacklist = []


def get_servers(cursor: str | None = None):
    global cached_cusor

    if cached_cusor is not None and cursor is None:
        cursor = cached_cusor

    if cursor is not None:
        cached_cusor = cursor

    send = endpoint + cursor if cursor is not None else endpoint
    r = requests.get(send)
    print(r.json())
    if r.status_code != 200:
        return

    if r.json().get("nextPageCursor"):
        npc = "&cursor=" + r.json()["nextPageCursor"]
    else:
        print(f"{RED}No next page{RESET}")
        return

    for server in r.json().get("data"):
        if (
            server.get("id") not in job_id_cache
            and server.get("id") not in job_id_blacklist
        ):
            ping = server.get("ping")
            jid = server.get("id")
            if ping is not None:
                job_id_cache.append((ping, jid))

    job_id_cache.sort(key=lambda x: x[0])
    print(f"{GREEN}Updated cache: {len(job_id_cache)} servers{RESET}")
    get_servers(npc)


def join_random(x: typing.Any) -> None:
    if len(job_id_cache) > 0:
        job_id = job_id_cache[0][1]
        ping = job_id_cache[0][0]
        job_id_blacklist.append(job_id)
        job_id_cache.pop(0)
    else:
        print(f"{RED}No cached servers, joining {id}{RESET}")
        job_id = ""
        ping = "???"

    print(f"{GREEN}Joining {job_id}, ping {ping}{RESET}")
    client.join(placeId=id, jobId=job_id)


def server_loop():
    global job_id_cache, job_id_blacklist
    c = refresh_cache
    while True:
        if c <= 0:
            c = refresh_cache
            print(f"{YELLOW}Refreshing Cache{RESET}")
            job_id_cache = []
            job_id_blacklist = []
        get_servers()
        c -= 1
        print(f"{RED}ratelimited, trying again in {retry_time}{RESET}")
        time.sleep(retry_time)


Thread(target=server_loop, daemon=True).start()
keyboard.on_press_key(hop_key, join_random)

while True:
    time.sleep(1)
