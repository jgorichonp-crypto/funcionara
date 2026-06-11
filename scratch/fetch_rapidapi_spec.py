import requests
import json

def fetch_spec():
    # RapidAPI public API endpoint to get API metadata/specs
    # Use the slug from the URL: tiktok-creative-center-api
    api_slug = "tiktok-creative-center-api"
    url = f"https://rapidapi.com/api/v1/apis/{api_slug}/specification"
    
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            spec_data = response.json()
            # print all paths
            paths = spec_data.get("paths", {})
            print("Found paths in specification:")
            for path in paths:
                print(f" - {path}")
            return spec_data
        else:
            print(f"Error: {response.text[:500]}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Try another common endpoint for RapidAPI specifications
    print("Trying alternative spec URL...")
    url_alt = f"https://rapidapi.com/api/v1/apis/slug/{api_slug}"
    try:
        response = requests.get(url_alt, headers={"User-Agent": "Mozilla/5.0"})
        print(f"Alt Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Response keys:", list(data.keys()))
            # Print endpoint details
            endpoints = data.get("endpoints", [])
            print(f"Found {len(endpoints)} endpoints in alternative metadata:")
            for ep in endpoints:
                print(f" - {ep.get('route')} ({ep.get('method')}) : {ep.get('name')}")
        else:
            print(f"Error: {response.text[:500]}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    fetch_spec()
