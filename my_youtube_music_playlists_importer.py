#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# my_youtube_music_playlists_importer.py
#
# Imports playlists from JSON files (exported from Spotify) into YouTube Music.
#
# License: MIT
# Date: 2025-09-07 (Sanitized)
#
# This script is provided for educational purposes.
# It is free to use and modify under the MIT License.
# The author provides no warranty and is not responsible for any use or misuse.
# The code is clean and contains no malicious components.
#
# Trademark disclaimer
#
# YouTube and YouTube Music are registered trademarks of Google LLC.
# This project is not affiliated with, sponsored, or endorsed by Google in any way.
# All references to YouTube Music are made solely for informational and educational purposes.
# -----------------------------------------------------------------------------

"""
my_youtube_music_playlists_importer.py

Usage:
    python my_youtube_music_playlists_importer.py [--playlists_file <path_to_json>] [--allow_duplicates] [--delete_if_exists]

Options:
    --playlists_file <path>   Path to the JSON file. Defaults to 'spotify_playlists.json'.
    --allow_duplicates          Allow adding duplicate tracks to playlists.
    --delete_if_exists          Delete existing playlists with the same name before creating new ones.
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from textwrap import dedent # <-- Import the dedent function

import unicodedata
import ytmusicapi
from dotenv import load_dotenv
from ytmusicapi import YTMusic

# Ensure minimum Python version for compatibility
if sys.version_info < (3, 10):
    print("This script requires Python 3.10 or higher.")
    sys.exit(1)


def load_env():
    """
    Load optional environment variables from .env file.

    Returns:
        dict: Dictionary containing configuration variables.
    """
    load_dotenv()
    config = {}

    # Optional variables
    config["AUTH_GENERATED_FILE"] = os.getenv("AUTH_GENERATED_FILE", "").strip() or "./browser.json"
    config["YT_API_DELAY_SECONDS"] = float(os.getenv("YT_API_DELAY_SECONDS", "1").strip())
    config["YT_API_MAX_RETRIES"] = int(os.getenv("YT_API_MAX_RETRIES", "3").strip())
    config["LOG_DIR"] = os.getenv("LOG_DIR", "").strip()
    config["LOG_LEVEL"] = os.getenv("LOG_LEVEL", "INFO").strip().upper() or "INFO"

    return config


def setup_logging(log_dir: Path, log_level: str):
    """
    Configure logging to console and file.

    Args:
        log_dir (Path): Directory to store log file.
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).

    Returns:
        Logger: Configured logger instance.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    logfile_path = log_dir / "my_youtube_music_playlists_importer.log"

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(logfile_path, encoding='utf-8')
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Log file: {logfile_path}")
    return logger


def sanitize_playlist_name(name: str) -> str:
    """
    Sanitize a playlist name to be safe for filenames, removing invalid/emoji characters,
    but keeping accents, original case, and trimming spaces.

    Args:
        name (str): Original playlist name.
    Returns:
        str: Sanitized playlist name.
    """

    # Remove emoji and non-printable characters
    def is_valid_char(c):
        cat = unicodedata.category(c)
        # Exclude emoji (So, Sk, Cs, Co, Cn), but keep accents and printable letters/numbers
        return not (cat.startswith('C') or cat.startswith('S'))

    name = ''.join(c for c in name if is_valid_char(c))
    # Remove invalid filename chars (but keep accents)
    name = re.sub(r'[\\/*?:"<>|]', '', name)
    return name.strip()


def import_playlists_from_json(json_file: Path, ytmusic: YTMusic, logger, allow_duplicates: bool,
                               delete_if_exists: bool, api_delay: float, api_max_retries: int):
    """
    Import playlists from a Spotify-exported JSON file into YouTube Music.

    Args:
        json_file (Path): Path to JSON file.
        ytmusic (YTMusic): Authenticated YTMusic instance.
        logger (Logger): Logger instance for logging.
        allow_duplicates (bool): Whether to allow duplicate tracks in playlists.
        delete_if_exists (bool): Whether to delete existing playlists before importing.
        api_delay (float): Delay in seconds between API requests.
        api_max_retries (int): Max number of retries for 409 Conflict errors.

    Returns:
        tuple: (total_playlists_created (int), total_playlists_existing (int),
                total_tracks_success (int), total_tracks_skipped_duplicates (int),
                total_tracks_failed (int))
    """
    with json_file.open('r', encoding='utf-8') as f:
        playlists = json.load(f)

    total_playlists_created = 0
    total_playlists_existing = 0
    total_playlists_deleted = 0
    total_tracks_success = 0
    total_tracks_failed = 0
    total_tracks_skipped_duplicates = 0

    existing_playlists = ytmusic.get_library_playlists(limit=1000)

    for playlist in playlists:
        name = sanitize_playlist_name(playlist['playlist_name'])
        description = playlist.get('description', '')

        # Check if playlist already exists
        existing = next((p for p in existing_playlists if p['title'].lower() == name.lower()), None)
        playlist_id = None
        if existing:
            playlist_id = existing['playlistId']
            if delete_if_exists:
                logger.info(f"Deleting existing playlist: '{name}' (ID: {playlist_id}) as --delete_if_exists is set")
                try:
                    ytmusic.delete_playlist(playlist_id)
                    total_playlists_deleted += 1
                    logger.info(f"Deleted playlist: '{name}'")
                    playlist_id = None  # Reset to force creation
                except Exception as e:
                    logger.error(f"Failed to delete playlist '{name}'. Exception: {e}")
                    continue
            else:
                logger.info(f"Using existing playlist: '{name}' (ID: {playlist_id})")
                total_playlists_existing += 1

        if not existing or delete_if_exists:
            logger.info(f"Creating new playlist: '{name}'...")
            playlist_id = ytmusic.create_playlist(name, description, privacy_status="PRIVATE")
            logger.info(f"Playlist created with ID: {playlist_id}")
            total_playlists_created += 1

        # Get current playlist items to check for duplicates
        # noinspection PyBroadException
        try:
            current_tracks = ytmusic.get_playlist(playlist_id, limit=1000).get('tracks', [])
        except Exception:
            logger.debug(f"No existing tracks for playlist '{name}' (ID: {playlist_id}).")
            current_tracks = []

        for track in playlist['tracks']:
            query = f"{track['name']} {track['artist']}"
            logger.info(f"Searching for track: '{track['name']}' by '{track['artist']}' in YouTube Music")
            logger.debug(f"Search query value: '{query}'")

            search_results = ytmusic.search(query, filter="songs")
            if search_results:
                logger.info("Track found")
            logger.debug(f"Search results found: {len(search_results)}")

            if search_results:
                video_id = search_results[0]['videoId']

                # Check for duplicates unless allowed
                duplicate_found = any(
                    t['videoId'] == video_id or
                    (t['title'].lower() == track['name'].lower() and ', '.join(
                        [a['name'] for a in t['artists']]).lower() == track['artist'].lower())
                    for t in current_tracks
                )

                if duplicate_found and not allow_duplicates:
                    logger.warning(
                        f"The playlist '{name}' already has the track: '{track['name']}' by '{track['artist']}'. "
                        f"Skipping duplication")
                    total_tracks_skipped_duplicates += 1
                    continue

                # Add track to playlist with retry logic
                for attempt in range(api_max_retries):
                    try:
                        logger.debug(
                            f"Adding track with ID: '{video_id}' ('{track['name']}' by '{track['artist']}') "
                            f"to playlist with ID: '{playlist_id}' ('{name}'), attempt {attempt + 1}")
                        ytmusic.add_playlist_items(playlist_id, [video_id])
                        logger.info(f"Added: {track['name']} by {track['artist']}")
                        total_tracks_success += 1
                        break
                    except Exception as e:
                        if "409" in str(e) and attempt < api_max_retries - 1:
                            backoff_time = 2 ** attempt
                            logger.warning(
                                f"409 Conflict when adding track with ID: '{video_id}' "
                                f"('{track['name']}' by '{track['artist']}'). "
                                f"Retrying in {backoff_time}s (attempt {attempt + 1})...")
                            time.sleep(backoff_time)
                        else:
                            logger.error(
                                f"Failed to add with ID: '{video_id}' "
                                f"('{track['name']}' by '{track['artist']}') "
                                f"to playlist with ID: '{playlist_id}' ('{name}'). Exception: {e}")
                            total_tracks_failed += 1
                            break

                time.sleep(api_delay)  # Delay between adding tracks
            else:
                logger.warning(f"Track not found: {track['name']} by {track['artist']}")
                total_tracks_failed += 1

    return (total_playlists_created, total_playlists_existing, total_playlists_deleted,
            total_tracks_success, total_tracks_skipped_duplicates, total_tracks_failed)


def main():
    """
    Entry point for script execution. Parses arguments, loads configuration,
    initializes logging and YTMusic client, and runs import process.
    """
    start_time = time.time()

    # --- Authentication headers are now stored directly in the script ---
    # IMPORTANT: You must paste your own, current header values here for the script to work.
    headers_raw_string = dedent("""
        accept: */*
        accept-encoding: gzip, deflate, br, zstd
        accept-language: en,en-US;q=0.9,bn;q=0.8
        authorization:
        cache-control: no-cache
        content-length: 2502
        content-type: application/json
        cookie:
        origin: https://music.youtube.com
        pragma: no-cache
        priority: u=1, i
        referer: https://music.youtube.com/
        sec-ch-ua: "Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"
        sec-ch-ua-arch: "x86"
        sec-ch-ua-bitness: "64"
        sec-ch-ua-form-factors: "Desktop"
        sec-ch-ua-full-version: "139.0.7258.155"
        sec-ch-ua-full-version-list: "Not;A=Brand";v="99.0.0.0", "Google Chrome";v="139.0.7258.155", "Chromium";v="139.0.7258.155"
        sec-ch-ua-mobile: ?0
        sec-ch-ua-model: ""
        sec-ch-ua-platform: "Windows"
        sec-ch-ua-platform-version: "19.0.0"
        sec-ch-ua-wow64: ?0
        sec-fetch-dest: empty
        sec-fetch-mode: same-origin
        sec-fetch-site: same-origin
        user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36
        x-browser-channel: stable
        x-browser-copyright: Copyright 2025 Google LLC. All rights reserved.
        x-browser-validation:
        x-browser-year: 2025
        x-client-data:
        x-goog-authuser: 0
        x-goog-visitor-id:
        x-origin: https://music.youtube.com
        x-youtube-bootstrap-logged-in: true
        x-youtube-client-name: 67
        x-youtube-client-version: 1.20250903.03.00
    """).strip()

    config = load_env()

    parser = argparse.ArgumentParser(description="Import Spotify-exported playlists (JSON files) into YouTube Music.")
    parser.add_argument("--playlists_file", type=str, default="spotify_playlists.json",
                        help="Path to the JSON file containing exported playlists. Defaults to 'spotify_playlists.json'.")
    parser.add_argument("--allow_duplicates", action="store_true",
                        help="Allow adding duplicate tracks to playlists.")
    parser.add_argument("--delete_if_exists", action="store_true",
                        help="Delete existing playlists with the same name before creating new ones.")
    args = parser.parse_args()

    # Determine log directory and logging
    log_dir = Path(config["LOG_DIR"]).expanduser().resolve() if config["LOG_DIR"] else Path(__file__).parent
    logger = setup_logging(log_dir, config["LOG_LEVEL"])

    # Get YouTube Music API delay and retries from config
    api_delay = config["YT_API_DELAY_SECONDS"]
    api_max_retries = config["YT_API_MAX_RETRIES"]

    # Retrieve auth generated file name from config
    auth_generated_file = config["AUTH_GENERATED_FILE"]

    # Validate and resolve playlists file path
    playlists_file = Path(args.playlists_file).expanduser().resolve()
    if not playlists_file.exists():
        logger.error(f"Error: Playlists file not found: {playlists_file}")
        logger.error("Please make sure 'spotify_playlists.json' is in the same directory, or specify the path using --playlists_file")
        sys.exit(1)

    # Initialize YTMusic
    try:
        logger.info("Initializing YouTube Music API with embedded headers...")
        ytmusicapi.setup(filepath=auth_generated_file, headers_raw=headers_raw_string)
        ytmusic = YTMusic(auth_generated_file)
        logger.info("YouTube Music API initialized successfully.")
    except Exception as e:
        logger.exception(f"Failed to initialize YTMusic. Exception: {e}")
        sys.exit(1)

    # Import playlists
    (total_playlists_created, total_playlists_existing, total_playlists_deleted,
     total_tracks_success, total_tracks_skipped_duplicates, total_tracks_failed) = import_playlists_from_json(
        playlists_file, ytmusic, logger, args.allow_duplicates, args.delete_if_exists, api_delay, api_max_retries)

    elapsed_time = time.time() - start_time
    logger.info(f"Script execution completed in: {elapsed_time:.2f} seconds.")
    logger.info(f"Playlists already existing (not deleted): {total_playlists_existing}")
    logger.info(f"Playlists created: {total_playlists_created}")
    logger.info(f"Playlists deleted: {total_playlists_deleted}")
    logger.info(f"Total tracks skipped (duplicate prevention): {total_tracks_skipped_duplicates}")
    logger.info(f"Total tracks successfully added: {total_tracks_success}")
    logger.info(f"Total tracks failed to add (request error or not found): {total_tracks_failed}")


if __name__ == "__main__":
    main()