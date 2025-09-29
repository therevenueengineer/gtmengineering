import requests
import re
from datetime import datetime
import json
import time

new_program_name = "unique event name"
description = "unique description here"
start = "startDate"
base_url = "Marketo Base URL = url with unique munchkin id"
source_campaign_id = "insert program id here"
target_folder_id = "folder where it's stored"

# 1. format event name
eventFormatted = new_program_name.replace(" ", "_") #replaces any spaces with '_' as per marketo naming conventions and fromatting rules

# 2. format date to marketo best practices ie. gets only year + month
datetime_object = datetime.strptime(start, "%Y-%m-%dT%H:%M:%S.%fZ")
year = datetime_object.year
month = datetime_object.month

# 3. create event name in marketo best practice naming convention
new_campaign_name = str(year) + "_" + str(month) + "_" + eventFormatted

# 4. get access token
def getAccessToken():
    client_id = 'clientId'
    client_secret = 'clientSecret'
    token_url = f"{base_url}/identity/oauth/token?grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}"
    token_response = requests.get(token_url)
    token_response.raise_for_status()
    return token_response.json()["access_token"]

# clone campaign template
def clone_campaign(source_campaign_id, new_campaign_name, target_folder_id, description):
    """Clones a Marketo program (campaign)."""
    access_token = getAccessToken()
    clone_url = f"{base_url}/rest/asset/v1/program/{source_campaign_id}/clone.json"

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {
        "name": new_campaign_name,
        "folder": json.dumps({"id": target_folder_id, "type": "Folder"}),
        "description": description
    }
    params = {"access_token": access_token}

    response = requests.post(url=clone_url, headers=headers, params=params, data=payload)
    response.raise_for_status()
    return response.json()

# fetch Static Lists (Asset API) under a Program
def get_static_lists_in_program(program_id, max_return=200):
    """
    Uses Asset API:
    GET /rest/asset/v1/staticLists.json?folder={"id":<program_id>,"type":"Program"}
    Returns [{"id": <int>, "name": <str>}]
    """
    access_token = getAccessToken()
    url = f"{base_url}/rest/asset/v1/staticLists.json"

    lists = []
    offset = 0
    while True:
        params = {
            "access_token": access_token,
            "maxReturn": max_return,
            "offset": offset,
            "folder": json.dumps({"id": int(program_id), "type": "Program"})
        }
        r = requests.get(url, params=params)
        r.raise_for_status()
        data = r.json()

        if not data.get("success"):
            break

        results = data.get("result") or []
        for item in results:
            lists.append({"id": item.get("id"), "name": item.get("name")})

        if len(results) < max_return:
            break

        offset += len(results)

    return lists

# main
try:
    # 1) Clone the program
    clone_result = clone_campaign(source_campaign_id, new_campaign_name, target_folder_id, description)

    # Extract cloned program ID
    if not (clone_result.get("result") and clone_result["result"][0].get("id")):
        raise RuntimeError(f"Clone did not return a program id. Raw: {clone_result}")

    program_id = clone_result["result"][0]["id"]

    # 2) Wait 5 seconds to ensure assets are created and committed to marketo database
    time.sleep(5)

    # 3) Retrieve Static Lists (asset IDs & names) under the cloned Program for referencing a particular list to add, in this case event registrants
    lists = get_static_lists_in_program(program_id)

    output = {
        "ok": True,
        "message": "Program cloned; static lists fetched successfully",
        "new_campaign_name": new_campaign_name,
        "program_id": program_id,
        "clone_result": clone_result,
        "lists": lists  # <-- numeric asset IDs + names
    }

except requests.exceptions.RequestException as e:
    output = {"ok": False, "error": f"HTTP error: {e}"}
except Exception as e:
    output = {"ok": False, "error": str(e)}
