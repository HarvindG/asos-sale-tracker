"""
Establishes a connection to the database.
"""
from os import environ

from cryptography.fernet import Fernet
from dotenv import load_dotenv
import pandas as pd
from pandas import DataFrame
from psycopg2 import connect
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor

SELECT_ALL_QUERY = """SELECT prices.price_id, prices.updated_at,
                prices.price, products.product_id, products.product_name,
                products.product_url, products.website_name, products.image_url,
                products.product_availability, users.user_id, users.email,
                users.first_name, users.last_name, users.password, subscriptions.subscription_id
                FROM prices
                JOIN products ON products.product_id = prices.product_id
                JOIN subscriptions ON subscriptions.product_id = products.product_id
                JOIN users ON users.user_id = subscriptions.user_id
                ORDER BY product_id, updated_at DESC;"""

COLUMNS = {"price_id": "Price ID", "updated_at": "Updated At",
           "price": "Price", "product_id": "Product ID",
           "product_name": "Product Name", "product_url": "Product URL",
           "image_url": "Image URL", "product_availability": "Product Availability",
           "website_name": "Website Name", "user_id": "User ID",
           "first_name": "User FirstName", "last_name": "User LastName",
           "email": "User Email", "subscription_id": "Subscription ID"}

load_dotenv()

fernet = Fernet(environ["FERNET_KEY"].encode())


def get_database_connection() -> connection:
    """
    Return a connection our database.
    """
    try:
        return connect(
            user=environ["DB_USER"],
            password=environ["DB_PASSWORD"],
            host=environ["DB_HOST"],
            port=environ["DB_PORT"],
            database=environ["DB_NAME"]
        )
    except ConnectionError as error:
        return error


def load_all_database_info(db_conn: connection) -> DataFrame:
    """
    Extract all data from the database.
    """

    with db_conn.cursor(cursor_factory=RealDictCursor) as cur:

        cur.execute(SELECT_ALL_QUERY)

        result = cur.fetchall()

        return pd.DataFrame(result).rename(columns=COLUMNS)


def get_user_info(conn: connection) -> list[dict]:
    """
    Gets all of the information from the users table in the RDS,
    adds a password and account type to each user 
    and returns a list of all users.
    """

    admin = {"user_id": 0,
             "email": "admin@saletracker.co.uk",
             "type": "admin",
             "first_name": "Admin",
             "last_name": "Admin"}
    password = "adminPassword"
    admin["password"] = fernet.encrypt(password.encode()).decode()

    all_users = []
    all_users.append(admin)

    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM users;")
    users = cur.fetchall()

    for user in users:
        user["type"] = 'user'
        all_users.append(user)

    return all_users


if __name__ == "__main__":

    conn = get_database_connection()
