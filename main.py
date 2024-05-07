import csv
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def fetch_redirect_url(url):
    try:
        response = requests.get(url, allow_redirects=False, verify=False)
        if response.status_code in [301, 302, 303, 307, 308]:
            return response.headers['Location']
    except Exception as e:
        logging.error(f"Error fetching redirect URL for {url}: {e}")
    return None


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


def main():
    input_file = 'apps.csv'
    output_file = 'enhanced_app_data.csv'
    results = []

    try:
        with open(input_file, newline='', mode='r') as csvfile:
            reader = csv.DictReader(csvfile)
            fieldnames = reader.fieldnames + ['uid', 'appid', 'is_archived', 'current_version', 'latest_version',
                                              'release_published_time', 'latest_version_compatibility',
                                              'current_version_compatibility', 'latest_version_installed',
                                              'is_current_version_compatible_9', 'download_link']

            for row in reader:
                redirect_url = fetch_redirect_url(row['details'])
                if redirect_url:
                    app_id = extract_app_id(redirect_url)
                    app_details, download_link = fetch_app_details(app_id)
                    current_version_compatibility = find_version_compatibility(app_details.get('releases', []),
                                                                               row['version'])

                    row.update({
                        'uid': app_details.get('uid', 'N/A'),
                        'appid': app_details.get('appid', 'N/A'),
                        'is_archived': app_details.get('is_archived', 'N/A'),
                        'current_version': row['version'],
                        'latest_version': app_details.get('release', {}).get('title', 'N/A'),
                        'release_published_time': app_details.get('release', {}).get('published_time', 'N/A'),
                        'latest_version_compatibility': app_details.get('release', {}).get('splunk_compatibility',
                                                                                           'N/A'),
                        'current_version_compatibility': current_version_compatibility,
                        'latest_version_installed': str(
                            row['version'] == app_details.get('release', {}).get('title', 'N/A')),
                        'is_current_version_compatible_9': str("9.1" in current_version_compatibility),
                        'download_link': download_link
                    })
                    results.append(row)

        with open(output_file, mode='w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        logging.info(f"Data written to {output_file} successfully.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
