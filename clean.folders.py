#!/usr/bin/env python3

import os
import re

def clean_folder_names(base_path):
    """
    Go through folders in the base path, clean names:
    - Replace spaces, dashes (-), underscores (_) with periods (.)
    - Preserve numbers and parentheses
    - Remove trailing junk like ., -, _
    - Ensure all names are in uppercase
    """
    print(f"Cleaning folder names in: {base_path}")
    
    for root, dirs, _ in os.walk(base_path):
        for dir_name in dirs:
            original_path = os.path.join(root, dir_name)

            # Replace spaces, dashes, and underscores with periods
            clean_name = re.sub(r"[\s\-_]+", ".", dir_name)
            
            # Remove any trailing junk characters like . or -
            clean_name = clean_name.rstrip('.-_')
            
            # Ensure the name is fully uppercase
            clean_name = clean_name.upper()
            
            # Only rename if the cleaned name is different
            if clean_name != dir_name:
                clean_path = os.path.join(root, clean_name)
                try:
                    os.rename(original_path, clean_path)
                    print(f"Renamed: '{original_path}' -> '{clean_path}'")
                except Exception as e:
                    print(f"Failed to rename '{original_path}': {e}")

if __name__ == "__main__":
    tv_directory = "/media/TV"

    if not os.path.exists(tv_directory):
        print(f"Error: The path {tv_directory} does not exist.")
        exit(1)

    clean_folder_names(tv_directory)
    print("Folder cleaning complete.")

