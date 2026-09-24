"""
Banking Database Management System
"""

import os
from decimal import Decimal, InvalidOperation

import mysql.connector
from mysql.connector import Error


DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE", "BankDB"),
    "auth_plugin": "mysql_native_password",
}

connection = None
cursor = None


def connect_database():
    """Connect to MySQL and create the database if it does not exist."""
    global connection, cursor

    try:
        server_config = DB_CONFIG.copy()
        database_name = server_config.pop("database")

        connection = mysql.connector.connect(**server_config)
        cursor = connection.cursor()

        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{database_name}`"
        )
        connection.commit()

        cursor.close()
        connection.close()

        connection = mysql.connector.connect(
            database=database_name,
            **server_config,
        )
        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Bank (
                Acc_No BIGINT PRIMARY KEY,
                Name VARCHAR(100) NOT NULL,
                Mobile VARCHAR(20) NOT NULL,
                Email VARCHAR(100) NOT NULL,
                Address VARCHAR(150),
                City VARCHAR(50),
                Country VARCHAR(50),
                Balance DECIMAL(12, 2) NOT NULL DEFAULT 0.00
            )
            """
        )
        connection.commit()
        print("Database and Bank table are ready.")

    except Error as error:
        print("Database connection/setup error:", error)
        connection = None
        cursor = None


def close_database():
    """Close the cursor and database connection."""
    global connection, cursor

    if cursor is not None:
        cursor.close()

    if connection is not None and connection.is_connected():
        connection.close()

    cursor = None
    connection = None


def read_decimal(prompt, minimum=None):
    """Read a valid decimal value from the user."""
    while True:
        try:
            value = Decimal(input(prompt).strip())

            if minimum is not None and value < minimum:
                print(f"Value must be at least {minimum}.")
                continue

            return value

        except InvalidOperation:
            print("Please enter a valid numeric value.")


def print_records(records):
    """Display records in a readable format."""
    if not records:
        print("No records found.")
        return

    headers = [
        "Acc_No",
        "Name",
        "Mobile",
        "Email",
        "Address",
        "City",
        "Country",
        "Balance",
    ]

    print("-" * 150)
    print(" | ".join(f"{header:<18}" for header in headers))
    print("-" * 150)

    for record in records:
        formatted = []
        for index, value in enumerate(record):
            if index == 7:
                formatted.append(f"{value:<18.2f}")
            else:
                formatted.append(f"{str(value):<18.18}")
        print(" | ".join(formatted))

    print("-" * 150)


def create_account():
    """Insert one or more customer accounts."""
    while True:
        try:
            account_number = int(input("Enter Account Number: ").strip())
            name = input("Enter Name: ").strip().upper()
            mobile = input("Enter Mobile Number: ").strip()
            email = input("Enter Email: ").strip().lower()
            address = input("Enter Address: ").strip().upper()
            city = input("Enter City: ").strip().upper()
            country = input("Enter Country: ").strip().upper()
            balance = read_decimal(
                "Enter Initial Balance: ",
                minimum=Decimal("0.00"),
            )

            query = """
                INSERT INTO Bank
                (Acc_No, Name, Mobile, Email, Address, City, Country, Balance)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            values = (
                account_number,
                name,
                mobile,
                email,
                address,
                city,
                country,
                balance,
            )

            cursor.execute(query, values)
            connection.commit()
            print("Account created successfully.")

        except ValueError:
            print("Account number must be a valid integer.")
        except Error as error:
            connection.rollback()
            print("Unable to create account:", error)

        answer = input("Do you want to add another account? (Y/N): ").strip().lower()
        if answer == "n":
            break


def display_sorted(sort_column):
    """Display all accounts sorted by a selected column."""
    allowed_columns = {
        "account": "Acc_No",
        "name": "Name",
        "balance": "Balance",
    }

    column = allowed_columns.get(sort_column)

    if column is None:
        print("Invalid sorting option.")
        return

    try:
        cursor.execute(f"SELECT * FROM Bank ORDER BY {column}")
        records = cursor.fetchall()
        print_records(records)
    except Error as error:
        print("Unable to display records:", error)


def search_account():
    """Search for an account by account number."""
    try:
        account_number = int(
            input("Enter the Account Number to search: ").strip()
        )

        cursor.execute(
            "SELECT * FROM Bank WHERE Acc_No = %s",
            (account_number,),
        )
        record = cursor.fetchone()

        if record:
            print_records([record])
        else:
            print("Record not found.")

    except ValueError:
        print("Account number must be a valid integer.")
    except Error as error:
        print("Search error:", error)


def update_account():
    """Update customer details except account number."""
    try:
        account_number = int(
            input("Enter the Account Number to update: ").strip()
        )

        cursor.execute(
            "SELECT * FROM Bank WHERE Acc_No = %s",
            (account_number,),
        )
        record = cursor.fetchone()

        if record is None:
            print("Record not found.")
            return

        fields = [
            ("Name", "Name", lambda: input("Enter Name: ").strip().upper()),
            ("Mobile", "Mobile", lambda: input("Enter Mobile: ").strip()),
            ("Email", "Email", lambda: input("Enter Email: ").strip().lower()),
            ("Address", "Address", lambda: input("Enter Address: ").strip().upper()),
            ("City", "City", lambda: input("Enter City: ").strip().upper()),
            ("Country", "Country", lambda: input("Enter Country: ").strip().upper()),
            (
                "Balance",
                "Balance",
                lambda: read_decimal(
                    "Enter Balance: ",
                    minimum=Decimal("0.00"),
                ),
            ),
        ]

        updates = {}

        for prompt_name, column_name, reader in fields:
            answer = input(f"Change {prompt_name}? (Y/N): ").strip().lower()
            if answer == "y":
                updates[column_name] = reader()

        if not updates:
            print("No changes were requested.")
            return

        set_clause = ", ".join(f"{column} = %s" for column in updates)
        values = list(updates.values())
        values.append(account_number)

        query = f"UPDATE Bank SET {set_clause} WHERE Acc_No = %s"
        cursor.execute(query, tuple(values))
        connection.commit()

        print("Account updated successfully.")

    except ValueError:
        print("Account number must be a valid integer.")
    except Error as error:
        connection.rollback()
        print("Update error:", error)


def delete_account():
    """Delete an account by account number."""
    try:
        account_number = int(
            input("Enter the Account Number to delete: ").strip()
        )

        cursor.execute(
            "SELECT * FROM Bank WHERE Acc_No = %s",
            (account_number,),
        )
        record = cursor.fetchone()

        if record is None:
            print("Record not found.")
            return

        confirmation = input(
            "Are you sure you want to delete this account? (Y/N): "
        ).strip().lower()

        if confirmation != "y":
            print("Deletion cancelled.")
            return

        cursor.execute(
            "DELETE FROM Bank WHERE Acc_No = %s",
            (account_number,),
        )
        connection.commit()
        print("Account deleted successfully.")

    except ValueError:
        print("Account number must be a valid integer.")
    except Error as error:
        connection.rollback()
        print("Delete error:", error)


def credit_account():
    """Credit money into an account."""
    try:
        account_number = int(
            input("Enter the Account Number to credit: ").strip()
        )
        amount = read_decimal(
            "Enter the amount to credit: ",
            minimum=Decimal("0.01"),
        )

        cursor.execute(
            """
            UPDATE Bank
            SET Balance = Balance + %s
            WHERE Acc_No = %s
            """,
            (amount, account_number),
        )

        if cursor.rowcount == 0:
            print("Record not found.")
            connection.rollback()
            return

        connection.commit()
        print("Amount credited successfully.")

    except ValueError:
        print("Account number must be a valid integer.")
    except Error as error:
        connection.rollback()
        print("Credit error:", error)


def debit_account():
    """Debit money while maintaining a minimum balance of Rs. 1000."""
    try:
        account_number = int(
            input("Enter the Account Number to debit: ").strip()
        )
        amount = read_decimal(
            "Enter the amount to debit: ",
            minimum=Decimal("0.01"),
        )

        cursor.execute(
            "SELECT Balance FROM Bank WHERE Acc_No = %s",
            (account_number,),
        )
        record = cursor.fetchone()

        if record is None:
            print("Record not found.")
            return

        current_balance = Decimal(str(record[0]))
        minimum_balance = Decimal("1000.00")

        if current_balance - amount < minimum_balance:
            print(
                "Transaction declined. A minimum balance of Rs. 1000 "
                "must remain after the transaction."
            )
            return

        cursor.execute(
            """
            UPDATE Bank
            SET Balance = Balance - %s
            WHERE Acc_No = %s
            """,
            (amount, account_number),
        )
        connection.commit()
        print("Amount debited successfully.")

    except ValueError:
        print("Account number must be a valid integer.")
    except Error as error:
        connection.rollback()
        print("Debit error:", error)


def sorting_menu():
    """Display the sorting menu."""
    while True:
        print("\n--- Sort Accounts ---")
        print("a. Sort by Account Number")
        print("b. Sort by Name")
        print("c. Sort by Balance")
        print("d. Back")

        choice = input("Enter your choice (a/b/c/d): ").strip().lower()

        if choice == "a":
            display_sorted("account")
        elif choice == "b":
            display_sorted("name")
        elif choice == "c":
            display_sorted("balance")
        elif choice == "d":
            break
        else:
            print("Invalid choice.")


def transaction_menu():
    """Display the transaction menu."""
    while True:
        print("\n--- Transactions ---")
        print("a. Credit into Account")
        print("b. Debit from Account")
        print("c. Back")

        choice = input("Enter your choice (a/b/c): ").strip().lower()

        if choice == "a":
            credit_account()
        elif choice == "b":
            debit_account()
        elif choice == "c":
            break
        else:
            print("Invalid choice.")


def main_menu():
    """Display and handle the main menu."""
    while True:
        print("\n" + "=" * 60)
        print("BANKING DATABASE MANAGEMENT SYSTEM".center(60))
        print("Customized by Banoth Praveen".center(60))
        print("=" * 60)
        print("1. Insert Account")
        print("2. Display Accounts")
        print("3. Search Account")
        print("4. Update Account")
        print("5. Delete Account")
        print("6. Transactions")
        print("7. Exit")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            create_account()
        elif choice == "2":
            sorting_menu()
        elif choice == "3":
            search_account()
        elif choice == "4":
            update_account()
        elif choice == "5":
            delete_account()
        elif choice == "6":
            transaction_menu()
        elif choice == "7":
            print("Exiting application.")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    connect_database()

    if connection is not None and cursor is not None:
        try:
            main_menu()
        finally:
            close_database()
    else:
        print("Application could not start because database setup failed.")
