import requests
import datetime
import time

# Calculate the schedule time
current_time = datetime.datetime.now()
schedule_time = (current_time + datetime.timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")  # ISO 8601 format

# Schedule a Single Send
url = "https://api.sendgrid.com/v3/marketing/singlesends"

# Headers with Auth
headers = {
    "Authorization": f"Bearer xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "Content-Type": "application/json",
}

# HTML content
html_content = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html data-editor-version="2" class="sg-campaigns" xmlns="http://www.w3.org/1999/xhtml">
    <head>
      <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1, minimum-scale=1, maximum-scale=1">
    </head>
    <body>
     [Insert body content here]
    </body>
</html>
"""

# Plain text content
plain_content = """
Dear Subscriber,

[Insert message here]

"""

# Payload to create the Single Send with content
payload = {
    "name": "Campaign Name",
    "send_to": {
        "list_ids": ["xxxxx"],  # Use the list ID stored in SendGrid
    },
    "email_config": {
        "subject": "Inser subject here", 
        "html_content": html_content,  
        "plain_content": plain_content,  
        "from": {
            "email": "from@email.com",
        },
        "template_id": "xxxxxxxxx",  # The Dynamic Template ID
        "asm_group_id" : "insert number here",
        "sender_id": "insert number here",  # Add the required sender ID
        "suppression_group_id": "insert number here",  # Add the required suppression group ID
    },
}

time.sleep(3)

#API request
response = requests.post(url, headers=headers, json=payload)

if response.status_code == 201:
    # Parse the JSON response
    response_data = response.json()

    # Get campaign ID
    campaign_id = response_data['id']
    print(f"Campaign created successfully with ID: {campaign_id}")

    # Verify campaign status
    print("Checking campaign status...")
    get_url = f"https://api.sendgrid.com/v3/marketing/singlesends/{campaign_id}"
    get_response = requests.get(get_url, headers=headers)
    print("Status Code (GET Campaign):", get_response.status_code)
    print("Response (GET Campaign):", get_response.json())

    # Schedule the campaign
    print("Scheduling campaign...")
    schedule_url = f"https://api.sendgrid.com/v3/marketing/singlesends/{campaign_id}/schedule"
    schedule_payload = {"send_at": schedule_time}
    schedule_response = requests.put(schedule_url, headers=headers, json=schedule_payload)

    print("Request URL:", schedule_url)
    print("Payload:", schedule_payload)
    print("Status Code (Schedule):", schedule_response.status_code)
    print("Response Text:", schedule_response.text)
    print("Response Headers:", schedule_response.headers)

else:
    print("Error creating campaign.")
    print("Status Code (Create):", response.status_code)
    print("Response (Create):", response.text)
