import boto3
import csv
import requests
import pickle
import os

API_KEY = "e6bc8eff15f74c6d928a897a0264635f"
PUT_BUCKET = "load.tlq"
RECURRING_CITIES_BUCKET = "recurring-cities.tlq"
RECURRING_CITIES_FILENAME = "recurring-cities.pkl"

def transform_row(record, recurring_cities):
    user_age = int(record[0])
    user_gender = record[1]
    user_number_of_apps = int(record[2])
    social_media_usage = float(record[3])
    productivity_usage = float(record[4])
    gaming_usage = float(record[5])
    user_city = record[6]

    total_app_usage = social_media_usage + productivity_usage + gaming_usage
    percent_social = social_media_usage / total_app_usage
    percent_productivity = productivity_usage / total_app_usage
    percent_gaming = gaming_usage / total_app_usage

    if user_city in recurring_cities:
        result_state, result_country = recurring_cities[user_city]
    else:
        response = requests.get(
            f"https://api.opencagedata.com/geocode/v1/json?q={user_city}&key={API_KEY}&limit=1"
        ).json()
        result_state = response['results'][0]['components'].get('state', 'N/A')
        result_country = response['results'][0]['components'].get('country', 'N/A')
        recurring_cities[user_city] = (result_state, result_country)

    return [
        user_age, user_gender, user_number_of_apps, social_media_usage,
        percent_social, productivity_usage, percent_productivity,
        gaming_usage, percent_gaming, total_app_usage, user_city,
        result_state, result_country
    ]

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    bucket_name = event['detail']['requestParameters']['bucketName']
    file_name = event['detail']['requestParameters']['key']
    tmp_file = f"/tmp/{file_name}"
    transformed_file = f"/tmp/transformed_{file_name}"

    # Load data from S3
    s3.download_file(bucket_name, file_name, tmp_file)

    # Load recurring cities cache
    recurring_cities = {}
    if s3.list_objects_v2(Bucket=RECURRING_CITIES_BUCKET, Prefix=RECURRING_CITIES_FILENAME).get('KeyCount', 0):
        s3.download_file(RECURRING_CITIES_BUCKET, RECURRING_CITIES_FILENAME, '/tmp/' + RECURRING_CITIES_FILENAME)
        with open('/tmp/' + RECURRING_CITIES_FILENAME, 'rb') as f:
            recurring_cities = pickle.load(f)

    # Transform data
    with open(tmp_file, 'r') as infile, open(transformed_file, 'w', newline='') as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        headers = next(reader)
        writer.writerow(headers + ["TotalUsage", "PercentSocialMedia", "PercentProductivity", "PercentGaming", "State", "Country"])
        for row in reader:
            writer.writerow(transform_row(row, recurring_cities))

    # Upload transformed file
    s3.upload_file(transformed_file, PUT_BUCKET, f"transformed_{file_name}")

    # Save recurring cities
    with open('/tmp/' + RECURRING_CITIES_FILENAME, 'wb') as f:
        pickle.dump(recurring_cities, f)
    s3.upload_file('/tmp/' + RECURRING_CITIES_FILENAME, RECURRING_CITIES_BUCKET, RECURRING_CITIES_FILENAME)

    return {"status": "success"}