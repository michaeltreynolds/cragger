"""Truncate the sentence_embeddings table via Supabase Management API."""
import json
import requests

with open('config.secret.json', 'r') as f:
    secrets = json.load(f)

url = f"https://api.supabase.com/v1/projects/{secrets['SUPABASE_PROJECT_REF']}/database/query"
headers = {
    "Authorization": f"Bearer {secrets['SUPABASE_ACCESS_TOKEN']}",
    "Content-Type": "application/json"
}

resp = requests.post(url, headers=headers, json={"query": "TRUNCATE TABLE sentence_embeddings;"})
print(f"Status: {resp.status_code}")
print(resp.text[:300])

if resp.status_code in (200, 201):
    print("Table truncated successfully!")
else:
    print("TRUNCATE FAILED")
