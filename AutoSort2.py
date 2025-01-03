#!/usr/bin/env python3

import os
import sys
import time
import re
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Thread


class DownloadHandler(FileSystemEventHandler):
    def __init__(self):
        self.skipped_files = []

    def on_created(self, event):
        if event.is_directory:
            return

        file_path = event.src_path
        if self.is_downloading(file_path):
            print(f"File {file_path} is still downloading. Skipping for now.")
            self.skipped_files.append(file_path)
        else:
            self.process_file(file_path)

    def is_downloading(self, file_path):
        """Check if the file is still being downloaded."""
        # Check for temporary file extensions (e.g., .part, .tmp, .crdownload)
        downloading_extensions = [".part", ".tmp", ".crdownload"]
        if any(file_path.endswith(ext) for ext in downloading_extensions):
            return True

        # Check last modification time
        try:
            last_mod_time = os.path.getmtime(file_path)
            current_time = time.time()
            if current_time - last_mod_time < 60:  # File modified in the last 60 seconds
                return True
        except FileNotFoundError:
            # File might not exist anymore
            return False

        # Check file locks (attempting to open in write mode)
        try:
            with open(file_path, "rb+") as f:
                pass
        except OSError:
            # File is likely locked for writing
            return True

        return False

    def process_file(self, file_path):
        # Ignore certain file extensions
        ignored_extensions = (
            ".idx",
            ".ignore",
            ".invalid",
            ".jpeg",
            ".jpg",
            ".nfo",
            ".png",
            ".sfv",
            ".srr",
            ".srt",
            ".sub",
            ".torrent",
        )
        if file_path.lower().endswith(ignored_extensions):
            return

        # Skip "sample" or excluded keywords
        excluded_keywords = ["sample", "exclude1", "exclude2", "exclude3"]
        if any(keyword in file_path.lower() for keyword in excluded_keywords):
            return

        # Get file name and base destination folder
        file_name = os.path.basename(file_path)
        base_destination_folder = "/media"

        # Detect if file is a TV show
        tv_show_pattern = re.compile(r"S\d{2}E\d{2}", re.IGNORECASE)
        is_tv_show = bool(tv_show_pattern.search(file_name))

        if is_tv_show:
            series_name_match = re.search(
                r"^(.*?)\s*[Ss]\d{2}[Ee]\d{2}", file_name)
            if series_name_match:
                series_name = series_name_match.group(1).strip()
                series_name = re.sub(
                    r"[\s\-_]+", ".", series_name
                )  # Replace spaces, - and _ with .
                series_name = series_name.rstrip(
                    ".-_"
                ).upper()  # Remove trailing junk and make uppercase
                destination_folder = os.path.join(
                    base_destination_folder, "TV", series_name
                )
            else:
                return  # Skip if series name can't be extracted
        elif any(
            keyword in file_name.lower()
            for keyword in ["720p", "1080p", "bluray", "webrip", "dvdrip"]
        ):
            destination_folder = os.path.join(
                base_destination_folder, "Movies"
            )
        else:
            return  # Skip if file doesn't match TV or Movie

        # Create destination folder and move file
        os.makedirs(destination_folder, exist_ok=True)
        destination_path = os.path.join(destination_folder, file_name)

        try:
            os.rename(file_path, destination_path)
            print(f"Moved {file_name} to {destination_path}")
        except Exception as e:
            print(f"Failed to move {file_name}: {e}")

    def process_existing_files(self, folder_path):
        for root, _, files in os.walk(folder_path):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                if not self.is_downloading(file_path):
                    self.process_file(file_path)
                else:
                    print(f"Skipping file {file_path} (still downloading).")
                    self.skipped_files.append(file_path)

    def retry_skipped_files(self):
        """Periodically check skipped files for completion."""
        while True:
            for file_path in self.skipped_files[:]:
                if not self.is_downloading(file_path):
                    print(f"Retrying file: {file_path}")
                    self.process_file(file_path)
                    self.skipped_files.remove(file_path)
            time.sleep(30)  # Retry every 30 seconds


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py /path/to/watch_folder")
        sys.exit(1)

    watch_folder = os.path.abspath(sys.argv[1])

    # Ensure /Downloads exists
    if not os.path.exists(watch_folder):
        os.makedirs(watch_folder)
        print(f"Created missing watch folder: {watch_folder}")

    print(f"Watching folder: {watch_folder}")
    destination_folder = "/media"

    event_handler = DownloadHandler()
    event_handler.watch_folder = watch_folder

    # Start retry thread for skipped files
    retry_thread = Thread(target=event_handler.retry_skipped_files, daemon=True)
    retry_thread.start()

    # Process existing files before starting observer
    event_handler.process_existing_files(watch_folder)

    observer = Observer()
    observer.schedule(event_handler, watch_folder, recursive=True)

    try:
        observer.start()
        print("Monitoring for new files... Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    print("File monitoring stopped.")

