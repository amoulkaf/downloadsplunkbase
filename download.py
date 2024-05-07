import csv
import requests
import json
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def authenticate():
    with open('login.json', 'r') as file:
        login_data = json.load(file)

    login_url = "https://splunkbase.splunk.com/api/account:login/"
    payload = {
        'username': login_data['username'],
        'password': login_data['password']
    }
    response = requests.post(login_url, data=payload)
    if response.status_code == 200:
        logging.info("Authentication successful.")
        return response.cookies.get_dict()
    else:
        raise Exception(f"Authentication failed with status code: {response.status_code}")

def download(app, cookies, downloaded_apps, skipped_apps):
    directory = "apps"
    if not os.path.exists(directory):
        os.makedirs(directory)

    uid = app['uid']
    appid = app['appid']
    latest_version = app['latest_version']
    current_version = app['current_version']
    file_name = os.path.join(directory, f"{appid}.tgz")

    # Download only if the latest version is different from the current version
    if latest_version != current_version:
        download_url = f"http://splunkbase.splunk.com/app/{uid}/release/{latest_version}/download/"
        response = requests.get(download_url, cookies=cookies)
        if response.status_code == 200:
            with open(file_name, 'wb') as file:
                file.write(response.content)
            downloaded_apps.append((appid, 'Downloaded'))
            logging.info(f"Successfully downloaded {file_name}")
        else:
            logging.error(f"Failed to download {file_name}. Status code: {response.status_code}")
            skipped_apps.append((appid, 'Failed to download'))
    else:
        skipped_apps.append((appid, 'Skipped, latest version is same as current version'))
        logging.info(f"Skipped {file_name}, as the latest version is the same as the current version.")

def main():
    input_file = 'enhanced_app_data.csv'
    download_report = 'download_report.csv'
    cookies = authenticate()
    downloaded_apps = []
    skipped_apps = []

    try:
        with open(input_file, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for app in reader:
                download(app, cookies, downloaded_apps, skipped_apps)

        # Writing the download report
        with open(download_report, mode='w', newline='') as csvfile:
            fieldnames = ['appid', 'status']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for app, status in downloaded_apps + skipped_apps:
                writer.writerow({'appid': app, 'status': status})
        logging.info(f"Download report saved to {download_report}.")
    except Exception as e:
        logging.error(f"An error occurred while processing downloads: {e}")

if __name__ == "__main__":
    main()
