import csv
import logging
import argparse  # Import argparse for command-line parsing

# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

def clean_header(header):
    # This will remove any BOM and extra whitespace around the header
    return header.replace('\ufeff', '').strip()

def create_migration_plan(input_file, output_file):
    migration_plan = []
    try:
        with open(input_file, newline='', mode='r', encoding='utf-8-sig') as csvfile:  # utf-8-sig handles BOM
            reader = csv.DictReader(csvfile)
            reader.fieldnames = [clean_header(field) for field in reader.fieldnames]  # Clean each field name

            fieldnames = [
                'uid', 'app_name', 'current_version', 'current_version_compatibility', 'upgrade_status',
                'upgrade_version', 'comment', 'download_link', 'latest_version_compatibility'
            ]

            for row in reader:
                uid = row.get('uid', 'N/A')
                app_name = row.get('label', 'N/A')
                current_version = row.get('current_version', 'N/A')
                latest_version = row.get('latest_version', 'N/A')
                current_version_compatibility = row.get('current_version_compatibility', '')
                compatibility_9_and_8 = row.get('9_and_8_compatibility', 'none')
                found_in_splunkbase = row.get('found_in_splunkbase', 'false')
                download_link = row.get('download_link', 'N/A')
                latest_version_compatibility_str = row.get('latest_version_compatibility', '[]')
                latest_version_compatibility = latest_version_compatibility_str.strip("[]").replace("'", "").split(", ")

                # Process conditions for migration
                # Append to migration_plan
                migration_plan.append({
                    'uid': uid,
                    'app_name': app_name,
                    'upgrade_status': upgrade_status,
                    'current_version': current_version,
                    'upgrade_version': upgrade_version,
                    'current_version_compatibility': current_version_compatibility,
                    'latest_version_compatibility': latest_version_compatibility_str,
                    'comment': comment,
                    'download_link': download_link
                })

        with open(output_file, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(migration_plan)

        print(f"Migration plan written to {output_file} successfully.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

def main(platform):
    if platform == "indexer":
        input_file = 'enhanced/enhanced_apps_indexer.csv'
        output_file = 'migration_plan/indexer_plan.csv'
    elif platform == "searchhead":
        input_file = 'enhanced/enhanced_apps_searchhead.csv'
        output_file = 'migration_plan/searchhead_plan.csv'

    create_migration_plan(input_file, output_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate migration plans based on the platform.')
    parser.add_argument('platform', choices=['indexer', 'searchhead'], help='Platform type: indexer or searchhead')
    args = parser.parse_args()
    main(args.platform)
