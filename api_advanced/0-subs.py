#!/usr/bin/python3
"""Query Reddit for the total number of subscribers to a subreddit."""

import os
import requests


def number_of_subscribers(subreddit):
    """Return the subscriber count, or zero for an unavailable subreddit."""
    headers = {"User-Agent": os.getenv(
        "REDDIT_USER_AGENT", "linux:alu-api-advanced:v1.0 (by fkangira)")}
    base_url = "https://www.reddit.com"
    token = os.getenv("REDDIT_ACCESS_TOKEN")
    if token:
        base_url = "https://oauth.reddit.com"
        headers["Authorization"] = "Bearer " + token
    try:
        response = requests.get(
            "{}/r/{}/about.json".format(base_url, subreddit),
            headers=headers, allow_redirects=False)
        if response.status_code != 200:
            return 0
        return response.json().get("data", {}).get("subscribers", 0)
    except (requests.RequestException, ValueError):
        return 0
