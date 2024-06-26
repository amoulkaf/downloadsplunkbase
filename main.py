import csv
import requests
import logging
import argparse  # Import argparse for command-line parsing

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_redirect_url(url):
    try:
        response = requests.get(url, allow_redirects=False, verify=False)
        if response.status_code in [301, 302, 303, 307, 308]:
            return response.headers['Location'], None
        elif response.status_code == 404:
            logging.warning(f"Received 404 for URL {url}")
            return None, "404"
    except Exception as e:
        logging.error(f"Error fetching redirect URL for {url}: {e}")
        return None, None
    return None, None

def fetch_app_details(app_id):
    try:
        api_url = f"https://splunkbase.splunk.com/api/v1/app/{app_id}/?order=latest&include=support,created_by,categories,icon,screenshots,rating,releases,documentation,releases.content,releases.splunk_compatibility,releases.cim_compatibility,releases.install_method_single,releases.install_method_distributed,release,release.content,release.cim_compatibility,release.install_method_single,release.install_method_distributed,release.splunk_compatibility"
        response = requests.get(api_url, verify=False)
        if response.status_code == 200:
            return response.json(), api_url
    except Exception as e:
        logging.error(f"Error fetching app details for app ID {app_id}: {e}")
    return {}, None

def extract_app_id(url):
    return url.split('/')[-1]

def find_version_compatibility(releases, version):
    for release in releases:
        if release.get('title') == version:
            return release.get('splunk_compatibility', 'N/A')
    return 'N/A'

def find_9_and_8_compatibility(releases):
    for release in releases:
        splunk_compatibility = release.get('splunk_compatibility', [])
        if any("9." in version for version in splunk_compatibility) and any("8." in version for version in splunk_compatibility):
            return release.get('title')
    return 'none'

def main(platform):
    if platform == "indexer":
        input_file = 'app_input/apps-indexer.csv'
        output_file = 'enhanced/enhanced_apps_indexer.csv'
        private_apps_file = 'enhanced/private_apps_indexer.csv'
    elif platform == "searchhead":
        input_file = 'app_input/apps-shc.csv'
        output_file = 'enhanced/enhanced_apps_shc.csv'
        private_apps_file = 'enhanced/private_apps_shc.csv'

    results = []
    private_apps = []

    try:
        with open(input_file, newline='', mode='r') as csvfile:
            reader = csv.DictReader(csvfile)
            fieldnames = reader.fieldnames + ['uid', 'appid', 'is_archived', 'current_version', 'latest_version',
                                              'release_published_time', 'latest_version_compatibility',
                                              'current_version_compatibility', 'latest_version_installed',
                                              'is_current_version_compatible_9', 'download_link', 'found_in_splunkbase',
                                              '9_and_8_compatibility']
            for row in reader:
                redirect_url, status = fetch_redirect_url(row['details'])
                if redirect_url:
                    app_id = extract_app_id(redirect_url)
                    app_details, download_link = fetch_app_details(app_id)
                    if app_details:
                        current_version_compatibility = find_version_compatibility(app_details.get('releases', []), row['version'])
                        compatibility_9_and_8 = find_9_and_8_compatibility(app_details.get('releases', []))

                        row.update({
                            'uid': app_details.get('uid', 'N/A'),
                            'appid': app_details.get('appid', 'N/A'),
                            'is_archived': app_details.get('is_archived', 'N/A'),
                            'current_version': row['version'],
                            'latest_version': app_details.get('release', {}).get('title', 'N/A'),
                            'release_published_time': app_details.get('release', {}).get('published_time', 'N/A'),
                            'latest_version_compatibility': app_details.get('release', {}).get('splunk_compatibility', 'N/A'),
                            'current_version_compatibility': current_version_compatibility,
                            'latest_version_installed': str(row['version'] == app_details.get('release', {}).get('title', 'N/A')),
                            'is_current_version_compatible_9': str("9.1" in current_version_compatibility),
                            'download_link': download_link,
                            'found_in_splunkbase': 'yes',
                            '9_and_8_compatibility': compatibility_9_and_8
                        })
                    else:
                        row.update({
                            'found_in_splunkbase': 'false',
                            '9_and_8_compatibility': 'none'
                        })
                    results.append(row)
                else:
                    row.update({
                        'found_in_splunkbase': 'false',
                        '9_and_8_compatibility': 'none'
                    })
                    results.append(row)
                    if status == "404":
                        private_apps.append(row)

        # Writing data to the main CSV
        with open(output_file, mode='w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

        # Writing data to the private apps CSV
        with open(private_apps_file, mode='w', newline='') as csvfile:
            private_fieldnames = reader.fieldnames + ['found_in_splunkbase', '9_and_8_compatibility']
            writer = csv.DictWriter(csvfile, fieldnames=private_fieldnames)
            writer.writeheader()
            writer.writerows(private_apps)

        logging.info(f"Data written to {output_file} and {private_apps_file} successfully.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process platform type for app details extraction.')
    parser.add_argument('platform', choices=['indexer', 'searchhead'], help='Platform type: indexer or searchhead')
    args = parser.parse_args()
    main(args.platform)
