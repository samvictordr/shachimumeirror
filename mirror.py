import os
import time
import requests
import json
from datetime import datetime, timezone
from atproto import Client
from atproto_client.models.app.bsky.feed.post import Record as PostRecord
from atproto_client.models.app.bsky.embed.images import Image as EmbedImage, Main as EmbedImages
from tweepy import Client as TwitterClient, TooManyRequests

# Config
BLSKY_USERNAME = os.environ["BSKY_HANDLE"]
BLSKY_PASSWORD = os.environ["BSKY_APP_PASSWORD"]
TWITTER_BEARER = os.environ["TWITTER_BEARER"]
TARGET_USERNAME = "shachimu"
CHAR_LIMIT = 300
MEDIA_LIMIT = 4

# Gist cache config
GIST_ID = os.environ["GIST_ID"]
GIST_FILENAME = "tweet_cache.json"
GIST_TOKEN = os.environ["GIST_ACCESS"]

def load_cache():
    url = f"https://api.github.com/gists/{GIST_ID}"
    headers = {
        "Authorization": f"token {GIST_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"Failed to fetch Gist cache: {resp.status_code} {resp.text}")
        return {"last_tweet_id": None}
    content = resp.json()["files"][GIST_FILENAME]["content"]
    return json.loads(content)

def save_cache(cache_data):
    url = f"https://api.github.com/gists/{GIST_ID}"
    headers = {
        "Authorization": f"token {GIST_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {
        "files": {
            GIST_FILENAME: {
                "content": json.dumps(cache_data, indent=2)
            }
        }
    }
    resp = requests.patch(url, headers=headers, json=payload)
    if resp.status_code != 200:
        print(f"Failed to update Gist cache: {resp.status_code} {resp.text}")
        raise Exception("Failed to update cache on Gist")

# Init clients
twitter = TwitterClient(bearer_token=TWITTER_BEARER)
bluesky = Client()
bluesky.login(login=BLSKY_USERNAME, password=BLSKY_PASSWORD)

def get_latest_tweet(username):
    print(f"📡 Fetching latest tweet from @{username}...")

    for _ in range(3):
        try:
            user = twitter.get_user(username=username).data
            tweets = twitter.get_users_tweets(
                id=user.id,
                max_results=5,
                tweet_fields=["text", "attachments"],
                expansions=["attachments.media_keys"],
                media_fields=["url"]
            )
            break
        except TooManyRequests as e:
            reset_time = int(e.response.headers.get("x-rate-limit-reset", time.time() + 60))
            wait_time = reset_time - int(time.time())
            print(f"⏳ Rate limited. Waiting {wait_time} seconds...")
            time.sleep(wait_time + 1)
        except Exception as e:
            print(f"Error: {e}")
            raise

    if not tweets.data:
        raise Exception("No tweets found.")

    tweet = tweets.data[0]

    # Extract media keys from the tweet (if any)
    media_keys = tweet.attachments["media_keys"] if "attachments" in tweet.data else []
    media_dict = {m.media_key: m for m in tweets.includes.get("media", [])}

    # Match keys to actual media
    media_urls = [
        media_dict[key].url
        for key in media_keys
        if key in media_dict and media_dict[key].type == "photo"
    ][:MEDIA_LIMIT]

    return tweet.id, tweet.text, media_urls


def upload_media_to_bluesky(media_urls):
    blobs = []
    for url in media_urls:
        print(f"📸 Downloading media: {url}")
        response = requests.get(url)
        response.raise_for_status()
        blob = bluesky.com.atproto.repo.upload_blob(response.content).blob
        blobs.append(blob)
    return blobs

def create_post(text, blobs):
    print("📝 Creating post for Bluesky...")
    text = text.strip().replace("\n", " ")
    if len(text) > CHAR_LIMIT:
        text = text[:CHAR_LIMIT - 3] + "..."

    embed = None
    if blobs:
        embed = EmbedImages(
            images=[
                EmbedImage(
                    image=blob,
                    alt="Image"
                )
                for blob in blobs
            ]
        )

    record_data = PostRecord(
        createdAt=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        text=text,
        embed=embed
    )

    post = bluesky.com.atproto.repo.create_record(
        data={
            "repo": bluesky.me.did,
            "collection": "app.bsky.feed.post",
            "record": record_data.dict(by_alias=True)
        }
    )
    return post

def main():
    cache = load_cache()
    last_id = cache.get("last_tweet_id")

    tweet_id, tweet_text, media_urls = get_latest_tweet(TARGET_USERNAME)

    if str(tweet_id) == str(last_id):
        print("⏸ No new tweet found. Already posted.")
        return

    blobs = upload_media_to_bluesky(media_urls)
    post = create_post(tweet_text, blobs)

    cache["last_tweet_id"] = str(tweet_id)
    save_cache(cache)

    print(f"Posted to Bluesky: {post.uri}")

if __name__ == "__main__":
    main()
