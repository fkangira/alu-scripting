# API advanced

Reddit API exercises using Python 3.4.3-compatible syntax and Requests.

| File | Function | Behavior |
| --- | --- | --- |
| `0-subs.py` | `number_of_subscribers(subreddit)` | Return total subscribers, or `0` for an unavailable subreddit. |
| `1-top_ten.py` | `top_ten(subreddit)` | Print up to ten hot titles in order, or `None` for an unavailable subreddit. |
| `2-recurse.py` | `recurse(subreddit, hot_list=None, after=None)` | Recursively follow `after` cursors and return all hot titles, or `None` when there are no results. |
| `3-count.py` | `count_words(subreddit, word_list, after=None, counts=None)` | Recursively read hot titles and print matching keyword counts. |

Every request sets a custom User-Agent and disables redirects. Non-success
responses, including redirects, access denials, and rate limits, use the
function's documented failure result. Network and JSON decoding errors do
the same. Importing a module makes no requests and prints nothing.

Keyword matching is case-insensitive and uses complete whitespace-delimited
tokens. Punctuation is preserved: `java.`, `java!`, and `java_` do not match
`java`. Every occurrence counts. Duplicate query words multiply the count.
Output uses lowercase words, descending counts, and alphabetical order for
ties. Words without matches are omitted. An invalid subreddit prints nothing
in `count_words`.

## Running

Install Requests for your Python version, then import the required function:

```sh
python3 -c 'f = __import__("0-subs").number_of_subscribers; print(f("programming"))'
python3 -c '__import__("1-top_ten").top_ten("programming")'
python3 -c 'print(__import__("2-recurse").recurse("programming"))'
python3 -c '__import__("3-count").count_words("programming", ["Python", "java", "JAVA"])'
```

Reddit can block unauthenticated requests even for valid subreddits. For
authorized live access, obtain an OAuth access token through your approved
Reddit application and set these environment variables before running:

```sh
export REDDIT_ACCESS_TOKEN='your-access-token'
export REDDIT_USER_AGENT='linux:your-app:v1.0 (by /u/your-reddit-username)'
```

With a token, requests use `https://oauth.reddit.com` and a Bearer header.
Without one, the functions use the public `.json` endpoints described in the
exercise. Never commit tokens, app secrets, or passwords.

References: [API documentation](https://www.reddit.com/dev/api/) and
[OAuth documentation](https://github.com/reddit-archive/reddit/wiki/OAuth2).

## Tests

From the repository root:

```sh
python3 test_api_advanced.py -v
```

The tests mock Reddit responses so results are deterministic, including
multi-page listings, invalid subreddits, duplicate keywords, punctuation,
sorting, error responses, OAuth headers, and independent repeated calls.
They do not require Reddit credentials or network access.
