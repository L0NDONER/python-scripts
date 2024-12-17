#!/usr/bin/env python3

# Import necessary libraries
import os
import sys
import time
import re
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Define the file system event handler


class DownloadHandler(FileSystemEventHandler):
    # Method triggered on file creation
    def on_created(self, event):
        # Ignore if the event is for a directory
        if event.is_directory:
            return
        # Process the newly created file
        self.process_file(event.src_path)

    # Method to process a file
    def process_file(self, file_path):
        # Ignore if the file is not in the specified folder or has certain extensions
        ignored_extensions = ('.idx', '.ignore', '.invalid', '.jpeg', '.jpg', '.nfo', '.png', '.sfv', '.srr', '.srt', '.sub', '.torrent')

        # Skip processing if the filename contains "sample" or any of the excluded keywords
        excluded_keywords = ['exclude1', 'exclude2', 'exclude3']
        if "sample" in file_path.lower() or any(keyword in file_path.lower() for keyword in excluded_keywords):
            return

        if not file_path.startswith(self.watch_folder) or file_path.lower().endswith(ignored_extensions):
            return

        # Get the file name from the path
        file_name = os.path.basename(file_path)

        # Check if it's a TV show based on filename patterns
        tv_show_pattern = re.compile(r'S\d{2}E\d{2}', re.IGNORECASE)
        is_tv_show = bool(tv_show_pattern.search(file_name))

        # Define keywords for categorizing as Movies
        movie_keywords = ['720p', '1080p', 'bluray', 'webrip', 'dvdrip']

        # Define base destination folder
        base_destination_folder = '/media'

        # Determine the destination based on TV show or movie
        if is_tv_show:
            # Extract series name from the filename (assuming a format like 'SeriesName S01E01')
            series_name_match = re.search(
                r'^(.*?)\s*[Ss]\d{2}[Ee]\d{2}', file_name)
            if series_name_match:
                series_name = series_name_match.group(1).strip()
                # Define the series folder
                series_folder = os.path.join(
                    base_destination_folder, 'TV', series_name)
            else:
                return  # Unable to determine series name, skip processing

            # Ensure the series folder exists
            os.makedirs(series_folder, exist_ok=True)

            # Define the full destination path
            destination_path = os.path.join(series_folder, file_name)

        elif any(keyword in file_name.lower() for keyword in movie_keywords):
            category = 'Movies'
            destination_path = os.path.join(
                base_destination_folder, category, file_name)
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        else:
            category = 'Other'
            return  # Skip processing for "Other" category

        # Move the file to the appropriate category/series folder
        try:
            os.rename(file_path, destination_path)
            print(f"Moved {file_name} to {destination_path}")
        except Exception as e:
            print(f"Error moving {file_name}: {e}")

    # Method to process existing files in a folder
    def process_existing_files(self, folder_path):
        for root, dirs, files in os.walk(folder_path):
            for file_name in files:
                self.process_file(os.path.join(root, file_name))


# Main block
if __name__ == "__main__":
    # Check if the correct number of command-line arguments is provided
    if len(sys.argv) != 2:
        print("Usage: python script.py /path/to/folder")
        sys.exit(1)

    # Set the destination folder
    destination_folder = '/media'

    # Initialize the event handler and observer
    event_handler = DownloadHandler()
    observer = Observer()

    # Get the folder path from the command-line argument
    watch_folder = os.path.abspath(sys.argv[1])
    event_handler.watch_folder = watch_folder
    event_handler.destination_folder = destination_folder

    # Schedule the event handler with the observer
    observer.schedule(event_handler, watch_folder, recursive=True)

    # Print a message indicating the start of the watching process
    print(f"Watching {watch_folder} for new downloads...")

    # Process existing files in the Downloads folder
    event_handler.process_existing_files(watch_folder)

    try:
        # Start the observer and keep it running
        observer.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # Stop the observer when a keyboard interrupt is received
        observer.stop()
    # Wait for the observer to finish
    observer.join()
