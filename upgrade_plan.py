import csv
import logging

# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')


def create_migration_plan(input_file, output_file):
    migration_plan = []

    try:
        with open(input_file, newline='', mode='r') as csvfile:
            reader = csv.DictReader(csvfile)
            fieldnames = [
                'app_name', 'current_version', 'current_version_compatibility', 'upgrade_status',
                'upgrade_version', 'comment', 'download_link', 'latest_version_compatibility'
            ]

            for row in reader:
                app_name = row.get('label', 'N/A')
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
                                upgrade_version = ''
                            else:
                                if any('8.' in version for version in latest_version_compatibility):
                                    upgrade_status = 'Not compatible with Splunk 9'
                                    comment = 'Latest version is only compatible with Splunk 8'
                                    upgrade_version = ''
                                else:
                                    upgrade_status = 'Not compatible with Splunk 9'
                                    if latest_version_compatibility:
                                        highest_version = max(latest_version_compatibility,
                                                              key=lambda v: [int(x) if x.isdigit() else x for x in
                                                                             v.split('.')])
                                    else:
                                        highest_version = 'compatibility not available'
                                    comment = f'Compatibility support stopped at Splunk {highest_version}'
                                    upgrade_version = 'None' if highest_version == 'compatibility not available' else ''

                migration_plan.append({
                    'app_name': app_name,
                    'current_version': current_version,
                    'current_version_compatibility': current_version_compatibility,
                    'upgrade_status': upgrade_status,
                    'upgrade_version': upgrade_version,
                    'comment': comment,
                    'download_link': download_link,
                    'latest_version_compatibility': latest_version_compatibility_str
                })

        with open(output_file, mode='w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(migration_plan)

        print(f"Migration plan written to {output_file} successfully.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")


# Generate the migration plan CSV file
create_migration_plan('enhanced_app_data.csv', 'migration_plan.csv')
