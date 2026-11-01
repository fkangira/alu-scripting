#!/usr/bin/python3
"""Recursively collect every hot post title using Reddit pagination."""

import os
import requests


def recurse(subreddit, hot_list=None, after=None):
    """Return all hot titles, or None when the subreddit has no results."""
    if hot_list is None:
        hot_list = []
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
            headers=headers, params={"limit": 100, "after": after},
            allow_redirects=False, timeout=15)
        if response.status_code != 200:
            return None
        data = response.json().get("data", {})
    except (requests.RequestException, ValueError):
        return None
    hot_list.extend(post.get("data", {}).get("title")
                    for post in data.get("children", []))
    next_page = data.get("after")
    if next_page:
        return recurse(subreddit, hot_list, next_page)
    return hot_list or None
