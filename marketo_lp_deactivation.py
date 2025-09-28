import requests
import json

client_id = "your_client_id_here"       # replace with your actual client ID
client_secret = "your_client_secret_here"  # Rrplace with your actual client secret
munchkin_id = "your_munchkin_id_here"   # replace with your actual Munchkin ID
folder_id = 1234                        # replace with the actual folder ID

def get_access_token(client_id, client_secret, munchkin_id):
    url = f"https://{munchkin_id}.mktorest.com/identity/oauth/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        token_info = response.json()
        return token_info['access_token']
    else:
        raise Exception(f"Failed to get access token: {response.status_code} {response.text}")

def get_lp_ids(access_token, munchkin_id, folder_id):
    url = f"https://{munchkin_id}.mktorest.com/rest/asset/v1/landingPages.json"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "folder": json.dumps({"id": folder_id, "type": "Folder"}),
        "maxReturn": 200
    }
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        lps = response.json().get('result', [])
        return [lp['id'] for lp in lps if lp.get('status') == "approved"]
    else:
        raise Exception(f"Failed to get landing pages: {response.status_code} {response.text}")

def unapprove_lp(access_token, munchkin_id, lp_id):
    url = f"https://{munchkin_id}.mktorest.com/rest/asset/v1/landingPage/{lp_id}/unapprove.json"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        print(f"Unapproved LP {lp_id}")
    else:
        print(f"Failed to unapprove LP {lp_id}: {response.status_code} {response.text}")

if __name__ == "__main__":
    token = get_access_token(client_id, client_secret, munchkin_id)
    lp_ids = get_lp_ids(token, munchkin_id, folder_id)
    
    for lp_id in lp_ids:
        unapprove_lp(token, munchkin_id, lp_id)
