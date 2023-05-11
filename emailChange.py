import requests
from requests.auth import HTTPBasicAuth

import json
import logging

#log file
logging.basicConfig(filename='output.log', encoding='utf-8', level=logging.INFO)

API_VERSION = '1.36'
AUTH_SERVICE = 'https://auth.brightspace.com/'

#read config variables
def get_config():
    with open('config.json', 'r') as f:
        return json.load(f)

#update config variables
def put_config(config):
    with open('config.json', 'w') as f:
        json.dump(config, f, sort_keys=True, indent=4)

#get access token and change the refresh_token
def trade_in_refresh_token(config):
    response = requests.post(
        '{}/core/connect/token'.format(AUTH_SERVICE),
        # Content-Type 'application/x-www-form-urlencoded'
        data={
            'grant_type': 'refresh_token',
            'refresh_token': config['refresh_token'],
            'scope': 'users:userdata:*'
        },
        auth=HTTPBasicAuth(config['client_id'], config['client_secret'])
    )

    config['refresh_token'] = response.json()['refresh_token']
    put_config(config)
    return response.json()

#make valence api call (GET)
def apicall_with_auth(endpoint, method='get', userData={}):
    headers = {'Authorization': 'Bearer {}'.format(token_response['access_token'])}
    if method == 'get':
        response = requests.get(endpoint, headers=headers)
    elif method=='put':
        response = requests.put(endpoint, headers=headers, data=userData)
    if response.status_code != 200:
        response.raise_for_status()

    return response

#main run

config = get_config()
token_response = trade_in_refresh_token(config)

#users get api call returns a paged result, hasMoreResult tells if there are more pages 
hasMoreItems = True
bookmark = ""

#looping each user
while (hasMoreItems):
    response = apicall_with_auth(f"{config['bspace_url']}/d2l/api/lp/{API_VERSION}/users/?bookmark={bookmark}")
    userData=response.json()['Items']
    for user in userData:
        userId = user['UserId']

        #replacing user's email adress
        newEmail = user['ExternalEmail']
        if (newEmail is not None) and ('@' in newEmail):
            startIndex = newEmail.find('@')
            newEmail = newEmail[:startIndex+1]+'localhost.local'
        else:
            logging.info(f"{userId} has no email or incorrect!")

        #update info for a user
        updateUserData = {
            "OrgDefinedId": user['OrgDefinedId'],
            "FirstName": user["FirstName"],
            "MiddleName": user['MiddleName'],
            "LastName": user['LastName'],
            "ExternalEmail": newEmail,
            "UserName": user['UserName'],
            "Activation": {"IsActive": user['Activation']["IsActive"]},
            "Pronouns": None
        }
        #calling update for a user
        makeUpdate = apicall_with_auth(f"{config['bspace_url']}/d2l/api/lp/{API_VERSION}/users/{userId}", "put", json.dumps(updateUserData))
        print(userId)
        logging.info(f"{userId} email changed")

    #next page
    bookmark = response.json()['PagingInfo']["Bookmark"] 
    logging.info(f"Bookmark: {bookmark}")  
