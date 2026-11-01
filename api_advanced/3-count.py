#!/usr/bin/python3
"""Recursively count exact keywords in all hot Reddit post titles."""

from collections import Counter
import os
import requests


def count_words(subreddit, word_list, after=None, counts=None):
    """Print weighted keyword counts, sorted by count then alphabetically."""
    if counts is None:
        counts = Counter()
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
            return
        data = response.json().get("data", {})
    except (requests.RequestException, ValueError):
        return
    counts.update(word for post in data.get("children", [])
                  for word in post.get("data", {}).get("title", "")
                  .lower().split())
    next_page = data.get("after")
    if next_page:
        return count_words(subreddit, word_list, next_page, counts)
    weights = Counter(word.lower() for word in word_list)
    totals = {word: counts.get(word, 0) * weight
              for word, weight in weights.items()}
    for word, count in sorted(totals.items(),
                              key=lambda item: (-item[1], item[0])):
        if count:
            print("{}: {}".format(word, count))
