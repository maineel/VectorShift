from fastapi import APIRouter, HTTPException, Request
import requests
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis
import os
from dotenv import load_dotenv

load_dotenv()

HUBSPOT_AUTH_URL = "https://app.hubspot.com/oauth/authorize"
HUBSPOT_TOKEN_URL = "https://api.hubapi.com/oauth/v1/token"
HUBSPOT_API_BASE_URL = "https://api.hubapi.com"
CLIENT_ID = os.getenv("HUBSPOT_CLIENT_ID")
CLIENT_SECRET = os.getenv("HUBSPOT_CLIENT_SECRET")
REDIRECT_URI = os.getenv("HUBSPOT_REDIRECT_URI")

async def authorize_hubspot(user_id, org_id):
    try:
        scopes = [
            "oauth",
            "crm.objects.companies.read",
            "crm.objects.deals.read",
            "crm.objects.contacts.read",
        ]
        scope_string = " ".join(scopes)
        
        params = {
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "scope": scope_string,
            "response_type": "code",
            "state": f"{user_id}:{org_id}"  
        }
        
        auth_url = f"{HUBSPOT_AUTH_URL}?{requests.compat.urlencode(params)}"
        
        return {"auth_url": auth_url}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in authorization: {str(e)}")

async def oauth2callback_hubspot(request: Request):
    try:
        print("Request", request)
        code = request.query_params.get("code")
        state = request.query_params.get("state")
        if not code or not state:
            raise HTTPException(status_code=400, detail="Missing code or state in callback.")

        user_id, org_id = state.split(":")
        data = {
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "code": code,
        }
        response = requests.post(HUBSPOT_TOKEN_URL, data=data)
        response.raise_for_status()
        tokens = response.json()

        redis_access_token_key = f"{user_id}:{org_id}:hubspot_access_token"
        redis_access_token_value = tokens["access_token"]
        redis_refresh_token_key = f"{user_id}:{org_id}:hubspot_refresh_token"
        redis_refresh_token_value = tokens["refresh_token"]

        await add_key_value_redis(redis_access_token_key, redis_access_token_value)
        await add_key_value_redis(redis_refresh_token_key, redis_refresh_token_value)
        
        return {"Authorization successful. You can close this tab now."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in OAuth callback: {str(e)}")

async def get_hubspot_credentials(user_id, org_id):
    try:
        access_token = await get_value_redis(f"{user_id}:{org_id}:hubspot_access_token")
        if not access_token:
            print("Access token", access_token) 
            refresh_token = await get_value_redis(f"{user_id}:{org_id}:hubspot_refresh_token")
            if not refresh_token:
                print("Refresh token", refresh_token)
                raise HTTPException(status_code=401, detail="Missing credentials.")

            data = {
                "grant_type": "refresh_token",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "refresh_token": refresh_token.decode("utf-8"),
            }
            response = requests.post(HUBSPOT_TOKEN_URL, data=data)
            response.raise_for_status()
            tokens = response.json()

            redis_access_token_key = f"{user_id}:{org_id}:hubspot_access_token"
            redis_access_token_value = tokens["access_token"]
            redis_refresh_token_key = f"{user_id}:{org_id}:hubspot_refresh_token"
            redis_refresh_token_value = tokens["refresh_token"]

            await add_key_value_redis(redis_access_token_key, redis_access_token_value)
            await add_key_value_redis(redis_refresh_token_key, redis_refresh_token_value)
            
            access_token = tokens["access_token"]
        return access_token.decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in retrieving credentials: {str(e)}")

async def create_integration_item_metadata_object(response_json):
    try:
        return [
            {
                "id": item.get("id"),
                "name": item.get("properties", {}).get("firstname", "Unknown"),
                "properties": item.get("properties", {})
            }
            for item in response_json.get("results", [])
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in parsing response data: {str(e)}")

async def fetch_hubspot_data(credentials, scope):
    try:
        credentials = credentials.strip()
        headers = {"Authorization": f"Bearer {credentials}"}
        url = f"{HUBSPOT_API_BASE_URL}/{scope}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        response_json = response.json()
        return await create_integration_item_metadata_object(response_json)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching {scope} data: {str(e)}")

async def get_items_hubspot(credentials, scope):
    if scope not in ["crm/v3/objects/contacts", "crm/v3/objects/companies", "crm/v3/objects/deals"]:
        raise HTTPException(status_code=400, detail="Invalid scope provided.")
    return await fetch_hubspot_data(credentials, scope)
