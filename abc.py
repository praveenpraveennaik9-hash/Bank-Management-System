import mysql.connector

def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='your_username',
            password='your_password',
            database='your_database'
        )
        if connection.is_connected():
            print("Successfully connected to the database")
            return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None