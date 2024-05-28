import csv
import logging
import argparse
import os

# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

def clean_header(header):
    # This will remove any BOM and extra whitespace around the header
    return header.replace('\ufeff', '').strip()

def create_migration_plan(input_file, output_base):
    migration_plans = {}
    try:
        with open(input_file, newline='', mode='r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            reader.fieldnames = [clean_header(field) for field in reader.fieldnames]

            fieldnames = [
                'uid', 'app_name', 'app_id', 'current_version', 'current_version_compatibility',
                'upgrade_status', 'upgrade_version', 'comment', 'download_link', 'latest_version_compatibility'
            ]

            for row in reader:
                uid = row.get('uid', 'N/A')
                app_name = row.get('label', 'N/A')
                app_id = row.get('app_id', 'N/A')  # Make sure 'app_id' is in the input CSV headers
                current_version = row.get('current_version', 'N/A')
                latest_version = row.get('latest_version', 'N/A')
                current_version_compatibility = row.get('current_version_compatibility', '')
                compatibility_9_and_8 = row.get('9_and_8_compatibility', 'none')
                found_in_splunkbase = row.get('found_in_splunkbase', 'false')
                download_link = row.get('download_link', 'N/A')
                latest_version_compatibility_str = row.get('latest_version_compatibility', '[]')
                latest_version_compatibility = latest_version_compatibility_str.strip("[]").replace("'", "").split(", ")

                if found_in_splunkbase.lower() == 'false':
                    upgrade_status = 'Check Manually'
                    comment = 'Not found in Splunkbase'
                    upgrade_version = 'None'
                else:
                    if '9.' in current_version_compatibility:
                        upgrade_status = 'OK'
                        comment = 'App compatible'
                        upgrade_version = 'None'
                    else:
                        if compatibility_9_and_8.lower() != 'none':
                            upgrade_status = 'update prior to upgrade'
                            upgrade_version = compatibility_9_and_8
                            comment = ''
                        else:
                            if any('9.' in version for version in latest_version_compatibility):
                                upgrade_status = 'update after upgrade'
                                comment = 'No cross compatibility version, latest version compatible with 9'
                                upgrade_version = latest_version
                            else:
                                upgrade_status = 'Not compatible with Splunk 9'
                                comment = 'Latest version compatibility issues'
                                upgrade_version = latest_version

                status_filename = upgrade_status.replace(" ", "_") + ".csv"
                if status_filename not in migration_plans:
                    migration_plans[status_filename] = []
                migration_plans[status_filename].append({
                    'uid': uid,
                    'app_name': app_name,
                    'app_id': app_id,
                    'upgrade_status': upgrade_status,
                    'current_version': current_version,
                    'upgrade_version': upgrade_version,
                    'current_version_compatibility': current_version_compatibility,
                    'latest_version_compatibility': latest_version_compatibility_str,
                    'comment': comment,
                    'download_link': download_link
                })

        for filename, data in migration_plans.items():
            output_file = os.path.join(output_base, filename)
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, mode='w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)

            print(f"Migration plan for {filename} written to {output_file} successfully.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

def main(platform):
    base_dir = 'migration_plan'
    platform_dir = os.path.join(base_dir, platform)
    input_file = os.path.join('enhanced', f'enhanced_apps_{platform}.csv')
    create_migration_plan(input_file, platform_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate migration plans based on the platform.')
    parser.add_argument('platform', choices=['indexer', 'searchhead'], help='Platform type: indexer or searchhead')
    args = parser.parse_args()
    main(args.platform)
