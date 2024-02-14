"""
API.
"""
from os import environ, _Environ
from datetime import datetime


from boto3 import client
from cryptography.fernet import Fernet
from mypy_boto3_ses import SESClient
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
from tempfile import mkdtemp
from psycopg2 import connect, extras
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor
from selenium.webdriver.chrome.options import Options

from extract import scrape_asos_page
from scrape_test import scrape_data

load_dotenv()

app = Flask(__name__, template_folder='./templates')

fernet = Fernet(environ["FERNET_KEY"].encode())

app.secret_key = environ.get('FLASK_SECRET_KEY', 'a_default_secret_key')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = mkdtemp()
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 6000
Session(app)


EMAIL_SELECTION_QUERY = "SELECT email FROM users;"
PRODUCT_URL_SELECTION_QUERY = "SELECT product_name, size FROM products;"
INSERT_USER_DATA_QUERY = "INSERT INTO users(email, first_name, last_name, password) VALUES (%s, %s, %s, %s)"
INSERT_INTO_PRODUCTS_QUERY = """
                INSERT INTO products (product_name, product_url, image_url, product_availability, website_name, size) 
                VALUES (%s, %s, %s, %s, %s, %s)
                """
PRODUCT_ID_QUERY = "SELECT product_id FROM products WHERE product_url = (%s) AND size = (%s)"
INSERT_INTO_PRICES_QUERY = "INSERT INTO prices (updated_at, product_id, price) VALUES (%s, %s, %s)"
SELECT_SUB_BY_PRODUCT_AND_USER_QUERY = "SELECT * FROM subscriptions WHERE user_id = (%s) AND product_id = (%s);"
INSERT_INTO_SUBSCRIPTIONS_QUERY = "INSERT INTO subscriptions (user_id, product_id) VALUES (%s, %s);"
SELECT_USERS_BY_EMAIL_QUERY = "SELECT user_id, password, email, first_name, last_name FROM users WHERE email = (%s);"
SELECT_USERS_BY_ID_QUERY = "SELECT user_id, password, email, first_name, last_name FROM users WHERE user_id = (%s);"
GET_PRODUCTS_FROM_EMAIL_QUERY = """
                SELECT DISTINCT ON (prices.product_id) users.first_name, products.product_name,products.product_url, products.product_id, products.image_url, products.product_availability, products.size, prices.price
                FROM users
                JOIN subscriptions ON users.user_id = subscriptions.user_id
                JOIN products ON subscriptions.product_id = products.product_id
                JOIN prices ON products.product_id = prices.product_id
                WHERE users.email = (%s)
                ORDER BY prices.product_id, prices.updated_at DESC;  
                """
GET_SUBS_BY_ID_QUERY = """
                SELECT subscriptions.user_id, users.email, users.first_name, users.last_name
                FROM subscriptions
                JOIN users ON subscriptions.user_id = users.user_id
                WHERE users.user_id = (%s);
                """
GET_PROD_ID_BY_PROD_NAME_QUERY = "SELECT product_id FROM products WHERE product_name = (%s) AND size = (%s);"
DELETE_SUBSCRIPTIONS_QUERY = "DELETE FROM subscriptions WHERE product_id = (%s) AND user_id = (%s);"


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


def insert_user_data(conn: connection, data_user: dict):
    """
    Inserts user data into users table in required database.
    """
    cur = conn.cursor(cursor_factory=extras.RealDictCursor)

    cur.execute(EMAIL_SELECTION_QUERY)
    rows = cur.fetchall()

    emails = [row["email"] for row in rows]

    if data_user['email'] in emails:
        conn.commit()
        cur.close()

    else:
        cur.execute(INSERT_USER_DATA_QUERY, (data_user["email"],
                                             data_user["first_name"],
                                             data_user["last_name"],
                                             data_user["password"]))

        conn.commit()
        cur.close()

        ses_client = get_ses_client(environ)

        ses_client.verify_email_address(
            EmailAddress=data_user['email'])


def insert_product_data_and_price_data(conn: connection, data_product: dict):
    """
    Inserts product data into products table in the required database.
    Also inserts price data into the prices table if product has just been
    added for the first time.
    """

    cur = conn.cursor(cursor_factory=extras.RealDictCursor)

    cur.execute(PRODUCT_URL_SELECTION_QUERY)
    rows = cur.fetchall()
    current_timestamp = datetime.now()

    print(data_product)
    in_database = False
    for product in rows:
        if data_product['name'] == product['product_name'] and data_product["sizes"] == product['size']:
            in_database = True
            break

    if in_database is True:
        conn.commit()
        cur.close()

    else:
        cur.execute(INSERT_INTO_PRODUCTS_QUERY, (data_product.get('name', 'Unknown'),
                                                 data_product['url'],
                                                 data_product['image'],
                                                 data_product['availability'],
                                                 data_product['website_name'],
                                                 data_product["sizes"]))

        cur.execute(PRODUCT_ID_QUERY,
                    (data_product["url"], data_product["sizes"]))

        product_id = cur.fetchone()

        price_query = INSERT_INTO_PRICES_QUERY
        cur.execute(price_query, (current_timestamp,
                                  product_id["product_id"],
                                  data_product["price"]))
        conn.commit()
        cur.close()


def insert_subscription_data(conn: connection, user_id: str, product_data: dict) -> None:
    """
    Inserts subscription data into the subscription table.
    """

    cur = conn.cursor(cursor_factory=extras.RealDictCursor)

    user_query = SELECT_USERS_BY_ID_QUERY
    cur.execute(user_query, (user_id,))
    user_id = cur.fetchone().get('user_id')

    cur.execute(PRODUCT_ID_QUERY, (product_data['url'], product_data['sizes']))
    product_id = cur.fetchone().get('product_id')

    cur.execute(SELECT_SUB_BY_PRODUCT_AND_USER_QUERY, (user_id, product_id))

    if cur.fetchone() is None:
        cur.execute(INSERT_INTO_SUBSCRIPTIONS_QUERY, (user_id, product_id))

        conn.commit()


def get_products_from_email(conn: connection, email: str) -> list:
    """
    Returns list of products the user has subscribed to.
    """
    cur = conn.cursor(cursor_factory=extras.RealDictCursor)

    cur.execute(GET_PRODUCTS_FROM_EMAIL_QUERY, (email,))

    return cur.fetchall()


def get_ses_client(config: _Environ) -> SESClient:
    """
    Returns an SES client to send emails to users.
    """

    return client('ses',
                  aws_access_key_id=config['AWS_ACCESS_KEY'],
                  aws_secret_access_key=config['AWS_SECRET_ACCESS_KEY'])


@app.route("/")
def index():
    """
    Displays the HTML homepage.
    """

    return render_template('/login_page.html')


@app.route("/logged_in")
def logged_in_index():
    """
    Loads the login index.
    """

    return render_template("/index.html")


@app.route("/login", methods=["POST", "GET"])
def login():
    """
    Logs a user into their Sale Tracker account.
    """

    error_message = None
    connection = get_database_connection()

    if request.method == "GET":
        return render_template("/login/login_page.html")

    if request.method == "POST":

        email = request.form.get('email')
        password = request.form.get('password')

        with connection.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(SELECT_USERS_BY_EMAIL_QUERY, (email,))
            user = cur.fetchone()

            if user and fernet.decrypt(user["password"].encode()).decode() == password:
                session['user_id'] = user['user_id']

                return redirect(url_for(("logged_in_index")))
            if not user:
                error_message = "Invalid email. No account with that email address."
                return render_template("/login/login_page.html", error=error_message)
            else:
                error_message = "Invalid password. Please try again."
                return render_template("/login/login_page.html", error=error_message)

    return render_template("/login/login_page.html")


@app.route("/create_account", methods=["POST", "GET"])
def create_account():
    """
    Creates a user account for Sale Tracker.
    """
    error_message = None
    connection = get_database_connection()

    if request.method == "GET":
        return render_template("/login/create_account.html")

    if request.method == "POST":
        password = request.form.get('password')
        re_enter_password = request.form.get('re-enter-password')
        first_name = request.form.get('firstName').capitalize()
        last_name = request.form.get('lastName').capitalize()
        email = request.form.get("email")

        with connection.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(SELECT_USERS_BY_EMAIL_QUERY, (email,))
            user = cur.fetchone()

            if user:
                error_message = "User with that email already exists."

                return render_template("/login/create_account.html", error=error_message)

        if password != re_enter_password:
            error_message = "Passwords do not match. Please try again."
            return render_template("/login/create_account.html", error=error_message)

        encrypted_password = fernet.encrypt(password.encode()).decode()

        user_data = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'password': encrypted_password
        }

        insert_user_data(connection, user_data)

        return render_template("/login/created.html")

    return render_template("/login/create_account.html")


@app.route('/logout')
def logout():
    """
    Logs out the user.
    """
    session.pop('user_id', None)
    return redirect(url_for('index'))


@app.route("/size", methods=["POST", "GET"])
def choose_size():
    """
    Makes a user choose the size of the product they want to track.
    """

    connection = get_database_connection()
    if request.method == "GET":
        return render_template('/submission_form/choose_size.html')

    if request.method == "POST":
        if 'user_id' not in session:
            return redirect(url_for('login'))
        product_data = session.get('product_data')
        if product_data is None:
            # Handle the case where product_data is not available
            return "Product data is not available", 400

        if 'url' not in session:
            return redirect(url_for('login'))
        size = request.form.get("size")

        product_data["sizes"] = size

        if "Out of stock" in size:
            product_data['availability'] = False

        insert_product_data_and_price_data(connection, product_data)
        insert_subscription_data(
            connection, session["user_id"], product_data)

        return render_template('submitted_form/submitted_form.html')


@app.route('/addproducts', methods=["POST", "GET"])
def submit():
    """
    Handles data submissions.
    """
    connection = get_database_connection()
    if request.method == 'POST':

        if 'user_id' not in session:
            return redirect(url_for('login'))

        url = request.form.get('url')

        header = {
            'user-agent': environ["USER_AGENT"]
        }

        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument(f'user-agent={environ["USER_AGENT"]}')

        product_data = scrape_data(url, chrome_options)
        print(product_data)
        session['product_data'] = product_data
        session['url'] = url

        if product_data["sizes"] == "One Size":
            insert_product_data_and_price_data(connection, product_data)
            insert_subscription_data(connection, session["user_id"], url)
            return render_template('/submitted_form/submitted_form.html')
        else:
            return render_template('/submission_form/choose_size.html', sizes=product_data["sizes"])

    if request.method == "GET":
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return render_template('/submission_form/input_website.html')


@app.route('/subscriptions', methods=["GET", "POST"])
def subscriptions():
    """
    Displays the unsubscribe HTML page.
    """
    conn = get_database_connection()
    if request.method == "GET":
        if 'user_id' not in session:
            return redirect(url_for('login'))

        cur = conn.cursor(cursor_factory=extras.RealDictCursor)

        cur.execute(GET_SUBS_BY_ID_QUERY, (session["user_id"],))

        result = cur.fetchall()

        if not result:
            return render_template('/subscriptions/not_subscribed.html')

        email = result[0]["email"]

        user_products = get_products_from_email(conn, email)
        print(user_products)

        for user in user_products:
            if user["product_availability"] == True:
                user["available"] = "In Stock"
            else:
                user["available"] = "Out of Stock"

        user_first_name = [product["first_name"]
                           for product in user_products][0]

        num_of_products = len(user_products)

    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template('subscriptions/product_list.html',
                           names=user_products,
                           firstname=user_first_name,
                           user_email=email,
                           num_products=num_of_products)


@app.route('/delete_subscription', methods=["POST"])
def delete_subscription():
    """
    Deletes subscriptions.
    """
    conn = get_database_connection()
    product_name = request.form.get("product_name")
    email = request.form.get('user_email')
    size = request.form.get('size')

    cur = conn.cursor(cursor_factory=extras.RealDictCursor)
    cur.execute(GET_PROD_ID_BY_PROD_NAME_QUERY, (product_name, size))
    product_id = cur.fetchone()['product_id']

    cur.execute(SELECT_USERS_BY_EMAIL_QUERY, (email,))
    user_id = cur.fetchone()['user_id']

    cur.execute(DELETE_SUBSCRIPTIONS_QUERY,
                (product_id, user_id))
    conn.commit()

    return redirect(url_for('subscriptions'))


@app.route("/submitted", methods=["POST"])
def submitted_form():
    """
    Displays the submitted form HTML page.
    """
    return render_template('/submitted_form/submitted_form.html')


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
