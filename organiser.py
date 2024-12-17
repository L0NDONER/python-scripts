#!/usr/bin/env python3

import os
import sys
import time
import re
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class DownloadHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return

        file_path = event.src_path
        time.sleep(5)  # Fixed delay to ensure file is ready
        self.process_file(file_path)

    def process_file(self, file_path):
        # Ignore certain file extensions
        ignored_extensions = ('.idx', '.ignore', '.invalid', '.jpeg', '.jpg',
                              '.nfo', '.png', '.sfv', '.srr', '.srt', '.sub', '.torrent')
        if file_path.lower().endswith(ignored_extensions):
            return

        # Skip "sample" or excluded keywords
        excluded_keywords = ['sample', 'exclude1', 'exclude2', 'exclude3']
        if any(keyword in file_path.lower() for keyword in excluded_keywords):
            return

        # Get file name and base destination folder
        file_name = os.path.basename(file_path)
        base_destination_folder = '/media'

        # Detect if file is a TV show
        tv_show_pattern = re.compile(r'S\d{2}E\d{2}', re.IGNORECASE)
        is_tv_show = bool(tv_show_pattern.search(file_name))

        if is_tv_show:
            series_name_match = re.search(r'^(.*?)\s*[Ss]\d{2}[Ee]\d{2}', file_name)
            if series_name_match:
                series_name = series_name_match.group(1).strip()
                # Clean series name: Replace spaces/dashes/underscores with periods and clean trailing junk
                series_name = re.sub(r"[\s\-_]+", ".", series_name)  # Replace spaces, - and _ with .
                series_name = series_name.rstrip('.-_').upper()  # Remove trailing junk and make uppercase
                destination_folder = os.path.join(base_destination_folder, 'TV', series_name)
            else:
                return  # Skip if series name can't be extracted
        elif any(keyword in file_name.lower() for keyword in ['720p', '1080p', 'bluray', 'webrip', 'dvdrip']):
            destination_folder = os.path.join(base_destination_folder, 'Movies')
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
                self.process_file(os.path.join(root, file_name))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py /path/to/watch_folder")
        sys.exit(1)

    watch_folder = os.path.abspath(sys.argv[1])
    print(f"Watching folder: {watch_folder}")
    destination_folder = '/media'

    event_handler = DownloadHandler()
    event_handler.watch_folder = watch_folder

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

