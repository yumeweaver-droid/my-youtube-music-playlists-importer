#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# my_youtube_music_playlists_importer.py
#
# Imports playlists from JSON files (exported from Spotify) into YouTube Music.
#
# License: MIT
# Date: 2025-07-03
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
    python my_youtube_music_playlists_importer.py --playlists_file <path_to_json_file> [--allow_duplicates] [--delete_if_exists]

Options:
    --playlists_file <path_to_json_file>   Path to the JSON file containing exported playlists.
    --allow_duplicates                      Allow adding duplicate tracks to playlists.
    --delete_if_exists                      Delete existing playlists with the same name before creating new ones.
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from pathlib import Path

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
    Load and validate required and optional environment variables from .env file.

    Returns:
        dict: Dictionary containing configuration variables.
    Raises:
        ValueError: If any required variable is missing or empty.
    """
    load_dotenv()
    required_vars = ["HEADERS_RAW_FILE"]
    config = {}

    for var in required_vars:
        val = os.getenv(var)
        if not val or not val.strip():
            raise ValueError(f"Missing required environment variable: {var}")
        config[var] = val.strip()

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

    config = load_env()

    parser = argparse.ArgumentParser(description="Import Spotify-exported playlists (JSON files) into YouTube Music.")
    parser.add_argument("--playlists_file", type=str,
                        help="Path to the JSON file containing exported playlists.")
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
        logger.error(f"Error: playlists_file not found: {playlists_file}")
        sys.exit(1)

    # Validate headers file
    header_raw_file = Path(config["HEADERS_RAW_FILE"]).expanduser().resolve()
    if not header_raw_file.exists() or not header_raw_file.is_file():
        logger.error(f"Headers file not found or invalid: {header_raw_file}")
        sys.exit(1)
    logger.info(f"Using headers file: {header_raw_file}")

    # Read headers file content
    try:
        with header_raw_file.open('r', encoding='utf-8') as f:
            headers_raw_file_content = f.read()
    except Exception as e:
        logger.exception(f"Failed to read headers file: {header_raw_file}. Exception: {e}")
        sys.exit(1)

    # Initialize YTMusic
    try:
        ytmusicapi.setup(filepath=auth_generated_file, headers_raw=headers_raw_file_content)
        ytmusic = YTMusic(auth_generated_file)
    except Exception as e:
        logger.exception(f"Failed to initialize YTMusic with headers file: {header_raw_file}. Exception: {e}")
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
