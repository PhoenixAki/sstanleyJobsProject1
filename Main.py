import requests
from bs4 import BeautifulSoup
import sqlite3


def connect_db():
    """Connects to the database. If it doesn't already exist, sqlite3 creates it."""
    conn = sqlite3.connect("testing.db")  # TODO change this back to jobs.db when done testing
    cursor = conn.cursor()
    return conn, cursor


def setup_db(cursor: sqlite3.Cursor):
    """Creates the table for job entries if it doesn't already exist. ID is the job posting's ID from the API request,
    and is included for the sake of sorting and checking if the job posting already exists in the table."""
    '''cursor.execute("CREATE TABLE IF NOT EXISTS jobs(id INTEGER PRIMARY KEY, title TEXT, location TEXT, skills TEXT, "
                   "visa TEXT, onsite TEXT, description TEXT, website TEXT);")'''  # TODO uncomment when done testing
    cursor.execute("CREATE TABLE IF NOT EXISTS testing(id INTEGER PRIMARY KEY, title TEXT, salary INTEGER, "
                   "description TEXT);")


def close_db(conn: sqlite3.Connection):
    """Saves any chances to the database, and safely closes the connection to it."""
    conn.commit()
    conn.close()


def get_job_ids(url):
    """Pulls the top level comment from Ask HN, and retrieves the ID of the job postings in the thread."""
    try:
        response = requests.get(url)  # top level Ask HN post
    except requests.exceptions.ConnectionError:
        return "Invalid URL"

    if response is not None:
        return response.json()["kids"]  # job listings are top level children of initial post


def check_ids(cursor: sqlite3.Cursor, job_ids: list):
    """Cleanses the list of job IDs to request by removing any that already have entries in the database.
    This massively cuts down on the time to retrieve new entries."""
    db_ids = cursor.execute("SELECT id FROM jobs;")

    for job_id in job_ids:
        if job_id in db_ids:
            job_ids.remove(job_id)


def get_listings(job_ids):
    job_listings = []
    count = 0

    for job in job_ids:
        listing = requests.get("https://hacker-news.firebaseio.com/v0/item/" + str(job) + ".json").json()
        if listing is not None:
            if listing.get("text") is not None:
                text = listing.get("text")
                text = BeautifulSoup(text, 'html.parser').get_text()  # cleanse text of HTML tags
                job_listings.append(text)
                count += 1

    return job_listings


def write_db(cursor: sqlite3.Cursor):
    cursor.execute("INSERT INTO testing(id, title, salary, description) VALUES(1, 'Title 1', 30000, "
                   "'This is the first test job entry for write_db.');")
    cursor.execute("INSERT INTO testing(id, title, salary, description) VALUES(2, 'Title 2', 40000, "
                   "'This is the second test job entry for write_db.');")
    cursor.execute("INSERT INTO testing(id, title, salary, description) VALUES(3, 'Title 3', 50000, "
                   "'This is the third test job entry for write_db.');")


def write_file(job_listings):
    file = open("job_listings.txt", "w", encoding="utf-8")
    count = 1

    for job in job_listings:
        file.write("Job " + str(count) + ": " + job + "\n\n")
        count += 1

    file.close()
    return file


def main():
    conn, cursor = connect_db()
    setup_db(cursor)
    write_db(cursor)

    '''job_ids = get_job_ids("https://hacker-news.firebaseio.com/v0/item/21936440.json")
    check_ids(cursor, job_ids)

    print("Got job ids")
    if job_ids == "Invalid URL":
        print("Error with URL - shutting down.")
        exit()

    job_listings = get_listings(job_ids)
    print("Got job listings")
    file = write_file(job_listings)
    print("Wrote to " + file.name + ". Shutting down.")'''

    close_db(conn)


if __name__ == "__main__":
    main()
