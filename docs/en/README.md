# My YouTube Music Playlists Importer

Imports your playlists from JSON files (exported from other platforms) into YouTube Music for migration, backup
restoration, or multi-platform synchronization.

---

## Description

`my_youtube_music_playlists_importer.py` is a command-line Python script designed to import your playlists into YouTube
Music from JSON files generated
by [My Spotify Playlists Downloader](https://github.com/novama/my-spotify-playlists-downloader) or similar tools.

This script connects to your YouTube Music account via `ytmusicapi` and performs:

- Creation of playlists (or updating existing ones)
- Searching and adding tracks by name and artist
- Duplicate prevention (optional)
- Retry logic for transient API errors (e.g. HTTP 409 Conflict)

This tool is ideal for:

- Migrating your music library from Spotify to YouTube Music
- Rebuilding playlists after switching platforms
- Keeping multi-platform backups synchronized
- Learning about YouTube Music API automation with Python

The project is released under the MIT License and intended for educational and personal use.

---

## Features

- Imports playlists from a **JSON file exported by Spotify downloader scripts**
- Optionally **deletes existing playlists** with the same name before importing
- **Duplicate prevention logic** (default behavior)
- Optional flag to **allow duplicates** in imported playlists
- Implements **retry with backoff** for transient 409 Conflict errors
- Delay between API calls to avoid rate limiting (configurable)
- **Logging** to console and file for auditability and debugging
- **Portable** – works on Windows, macOS, and Linux

---

## Requirements

- Python 3.10 or higher
- [ytmusicapi](https://ytmusicapi.readthedocs.io/)
- A **YouTube Music account** (Premium not required)
- Your **authenticated request headers** exported from browser to authenticate `ytmusicapi`
- Playlist data files in JSON format (exported from other platforms)

Install dependencies with:

```shell
pip install -r requirements.txt
```

---

## Setup

1. **Clone the repository**

    ```shell
    git clone https://github.com/yourusername/my_youtube_music_playlists_importer.git
    cd my_youtube_music_playlists_importer
    ```

2. **Create your `.env` file**

   Copy the provided example:

    ```shell
    cp .env.example .env
    ```

3. **Edit `.env` and set your variables**

**Required:**

- `HEADERS_RAW_FILE`: Path to your raw headers text file exported from browser DevTools.

**Optional:**

- `AUTH_GENERATED_FILE`: Path to generated auth file (default: ./browser.json)
- `YT_API_DELAY_SECONDS`: Delay between adding tracks (default: 1)
- `YT_API_MAX_RETRIES`: Max retries for 409 Conflict errors (default: 3)
- `LOG_DIR`: Directory to store logs (default: script location)
- `LOG_LEVEL`: Logging level (default: INFO)

### `ytmusicapi` Browser Authentication

This script uses **browser-based authentication** with `ytmusicapi`, which requires copying your YouTube Music request
headers from your browser after successfully logging in to [music.youtube.com](https://music.youtube.com).

#### Why is this needed?

Unlike official APIs, YouTube Music does not provide a direct developer authentication method.
`ytmusicapi` works by simulating your browser session, allowing it to perform actions on your behalf using your existing
login cookies and headers.

#### How to extract your YouTube Music headers

1. **Log in** to your YouTube Music account in your browser (preferably Chrome or Firefox).
2. Open **Developer Tools (F12)**.
3. Go to the **Network** tab.
4. Refresh the page to capture requests.
5. Look for a **POST** request to `music.youtube.com` and inspect its headers. The simplest way is to filter
   by `browse`.
6. Copy all the **Request Headers** (in Firefox: right click > copy > copy request headers).

For a detailed step-by-step guide, see
the [ytmusicapi setup documentation](https://ytmusicapi.readthedocs.io/en/latest/setup/browser.html).

#### Saving your headers

Once you have copied the correct request headers:

- Create a file named `headers_raw.txt` in your project directory.
- Paste the headers content into this file and save it.

> ⚠️ **Important security note:**
> This file contains authentication information tied to your Google account. Keep it **private**, do not commit it to
> version control, and store it securely.

---

## JSON file structure example

The input JSON file must contain a list of playlists, each with at least the following structure:

```json
[
  {
    "playlist_name": "My Favorite Songs",
    "description": "Optional description of this playlist",
    "tracks": [
      {
        "name": "Song Title",
        "artist": "Artist Name"
      },
      {
        "name": "Another Song",
        "artist": "Another Artist"
      }
    ]
  },
  {
    "playlist_name": "Chill Vibes",
    "description": "",
    "tracks": [
      {
        "name": "Chill Song 1",
        "artist": "Chill Artist"
      }
    ]
  }
]
````

### ✅ **Required fields**

- `playlist_name`: Name of the playlist to create or update
- Each track object must include:

  - `name`: Track title
  - `artist`: Track artist

### ℹ️ **Optional fields**

- `description`: Playlist description (can be empty)

> ⚠️ **Note:**
> The file exported by [My Spotify Playlists Downloader](https://github.com/novama/my-spotify-playlists-downloader) is
> compatible by default.
> If using your own exporter, ensure it produces JSON with this structure.

---

## Usage

### Import playlists into YouTube Music

```shell
python my_youtube_music_playlists_importer.py --playlists_file /path/to/playlists.json
```

### Allow duplicate tracks in playlists

```shell
python my_youtube_music_playlists_importer.py --playlists_file /path/to/playlists.json --allow_duplicates
```

### Delete existing playlists with same name before importing

```shell
python my_youtube_music_playlists_importer.py --playlists_file /path/to/playlists.json --delete_if_exists
```

---

## Output Summary

At completion, the script logs:

- Total playlists created
- Total playlists deleted
- Total playlists existing (not deleted)
- Total tracks added successfully
- Total tracks skipped due to duplicate prevention
- Total tracks failed to add (e.g. not found or API error)
- Total execution time

---

## Disclaimer

This script is provided for educational purposes only.
Use it responsibly with your own YouTube Music account.
The author assumes no liability for misuse or data loss caused by its usage.
The code is clean and free of malicious components.

## Trademark Disclaimer

YouTube and YouTube Music are registered trademarks of Google LLC.
This project is **not affiliated with, sponsored, or endorsed by Google** in any way.
All references to YouTube Music are made solely for informational and educational purposes.

---

## License

This project is licensed under the [MIT License](../../LICENSE).
