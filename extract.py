import os
import tarfile


def extract_tgz_files(source_dir, target_dir):
    # Ensure the target directory exists
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    # Walk through the source directory
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if file.endswith('.tgz'):
                # Define the path to the current file
                file_path = os.path.join(root, file)

                # Define the extraction path
                extract_path = os.path.join(target_dir, file[:-4])  # Removing '.tgz' and use file name as folder name

                # Ensure the extraction path directory exists
                if not os.path.exists(extract_path):
                    os.makedirs(extract_path)

                # Extract the file
                with tarfile.open(file_path, 'r:gz') as tar:
                    tar.extractall(path=extract_path)

                print(f'Extracted {file} to {extract_path}')


# Specify the source and target directories
source_directory = 'apps'
target_directory = 'extracted_apps'

# Call the function to extract all .tgz files
extract_tgz_files(source_directory, target_directory)
