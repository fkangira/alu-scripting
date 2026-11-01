#!/usr/bin/python3
"""Print the first ten hot post titles for a subreddit."""

import os
import requests


def top_ten(subreddit):
    """Print hot titles in API order, or None for an invalid subreddit."""
    headers = {"User-Agent": os.getenv(
        "REDDIT_USER_AGENT", "linux:alu-api-advanced:v1.0 (by fkangira)")}
    base_url = "https://www.reddit.com"
    token = os.getenv("REDDIT_ACCESS_TOKEN")
    if token:
        base_url = "https://oauth.reddit.com"
        headers["Authorization"] = "Bearer " + token
    try:
        response = requests.get(
            "{}/r/{}/hot.json".format(base_url, subreddit),
            headers=headers, params={"limit": 10},
            allow_redirects=False)
        if response.status_code != 200:
            print(None)
            return
        posts = response.json().get("data", {}).get("children", [])
    except (requests.RequestException, ValueError):
        print(None)
        return
    for post in posts[:10]:
        print(post.get("data", {}).get("title"))
