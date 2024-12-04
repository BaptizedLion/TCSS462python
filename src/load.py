import boto3
import csv
import pymysql

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    bucket_name = event['detail']['requestParameters']['bucketName']
    file_name = event['detail']['requestParameters']['key']
    tmp_file = f"/tmp/{file_name}"

    # Load database connection details
    db_config = {
        "host": "your-db-host",
        "user": "your-username",
        "password": "your-password",
        "database": "mobiledata"
    }

    # Download file from S3
    s3.download_file(bucket_name, file_name, tmp_file)

    # Connect to Aurora database
    connection = pymysql.connect(**db_config)
    cursor = connection.cursor()

    # Check/Create table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS data (
        userID INT AUTO_INCREMENT PRIMARY KEY,
        userAge INT,
        userGender VARCHAR(10),
        userNumberOfApps INT,
        userSocialMediaUsage FLOAT,
        userPercentOfSocialMedia FLOAT,
        userProductivityAppUsage FLOAT,
        userPercentOfProductivityAppUsage FLOAT,
        userGamingAppUsage FLOAT,
        userPercentOfGamingAppUsage FLOAT,
        userTotalAppUsage FLOAT,
        userCity VARCHAR(100),
        resultState VARCHAR(100),
        resultCountry VARCHAR(100)
    );
    """
    cursor.execute(create_table_sql)
    connection.commit()

    # Insert data
    insert_sql = """
    INSERT INTO data (
        userAge, userGender, userNumberOfApps, userSocialMediaUsage, 
        userPercentOfSocialMedia, userProductivityAppUsage, 
        userPercentOfProductivityAppUsage, userGamingAppUsage, 
        userPercentOfGamingAppUsage, userTotalAppUsage, userCity, 
        resultState, resultCountry
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    with open(tmp_file, 'r') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip header
        for row in reader:
            cursor.execute(insert_sql, row)
    connection.commit()

    return {"status": "data loaded successfully"}