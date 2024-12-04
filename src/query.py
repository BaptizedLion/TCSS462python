import json
import pymysql

def lambda_handler(event, context):
    db_config = {
        "host": "your-db-host",
        "user": "your-username",
        "password": "your-password",
        "database": "mobiledata"
    }

    connection = pymysql.connect(**db_config)
    cursor = connection.cursor()

    query = "SELECT "
    aggregations = event.get("aggregations", [])
    if aggregations:
        query += ", ".join([f"{agg['function']}({agg['column']}) AS {agg['function']}_{agg['column']}" for agg in aggregations])
    else:
        query += "*"
    query += " FROM data"

    filters = event.get("filters", [])
    if filters:
        query += " WHERE " + " AND ".join([f"{f['column']} = %s" for f in filters])

    group_by = event.get("group", [])
    if group_by:
        query += " GROUP BY " + ", ".join(group_by)

    values = [f["value"] for f in filters]
    cursor.execute(query, values)

    result = cursor.fetchall()
    return json.dumps(result, default=str)
