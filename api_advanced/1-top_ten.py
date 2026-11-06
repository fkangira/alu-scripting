#!/usr/bin/python3
"""Print the titles of the first ten hot posts of a subreddit."""
import requests


def top_ten(subreddit):
    """Print the first 10 hot titles, or None for an invalid subreddit."""
    url = "https://www.reddit.com/r/{}/hot/.json".format(subreddit)
    headers = {"User-Agent": "linux:alu-api-advanced:v1.0 (by /u/fkangira)"}
    params = {"limit": 10}
    try:
        response = requests.get(url, headers=headers, params=params,
                                allow_redirects=False)
        if response.status_code in (301, 302, 303, 307, 308, 404):
            print("None")
            return
        results = response.json().get("data")
        for child in results.get("children")[:10]:
            print(child.get("data").get("title"))
    except Exception:
        print("None")
