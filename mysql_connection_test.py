"""
MySQL Connection Test
"""

import os
import mysql.connector
from mysql.connector import Error


def test_connection():
    connection = None

    try:
        connection = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DATABASE", "BankDB"),
            auth_plugin="mysql_native_password",
        )

        if connection.is_connected():
            print("MySQL connection successful.")
            print(f"Connected database: {connection.database}")

    except Error as error:
        print("MySQL connection error:", error)

    finally:
        if connection is not None and connection.is_connected():
            connection.close()
            print("MySQL connection closed.")


if __name__ == "__main__":
    test_connection()