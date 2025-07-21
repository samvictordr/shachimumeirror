## Bluesky Mirror
> [!CAUTION]
> While it does not explicitly violate Bluesky's Terms of Service, automated bots and mirror accounts **may still be flagged or taken down** at any time. Use responsibly. 

## A GitHub Actions-based mirror that cross-posts from X to Bluesky, purely serverless.

### Overview
A simple, serverless setup to mirror posts from a specific X account to Bluesky using GitHub Actions. It runs on a scheduled cron job and uses a GitHub Gist as a lightweight way to keep track of the last post it mirrored. I built it to automatically cross-post Shachimu’s tweets to Bluesky, no manual effort needed.

The app fetches the latest tweet from the specified X account, set in the `TARGET_USERNAME` variable in the mirror script. If the tweet ID matches the cached ID (stored in a GitHub Gist), it skips posting. Otherwise, it posts the tweet to Bluesky and updates the cached ID.

#### Environment Variables (GitHub Secrets)
This should explain what all the env vars in the workflow file and the mirror script are for.

| Name               | Description                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| `BSKY_HANDLE`       | Your Bluesky handle (e.g., `yourname.bsky.social`). this is where mirrored posts will be posted.                          |
| `BSKY_APP_PASSWORD` | App password generated from Bluesky (used for login)                        |
| `TWITTER_BEARER`    | Twitter/X API Bearer Token                                                  |
| `GIST_ID`           | ID of the GitHub Gist used for caching mirrored tweet IDs                   |
| `GIST_ACCESS`       | GitHub Personal Access Token with Gist access (for reading/writing cache)   |


#### GitHub Actions Workflow
The workflow file is `.github/workflows/mirror.yml`. It's set to run every hour.

---
### TL;DR
You can't be too lazy. Read it all.

### License
This project is [GPL v3](LICENSE).
