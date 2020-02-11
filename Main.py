import sqlite3
from bs4 import BeautifulSoup
import requests


def open_city_file():
    """Opens the cities file and reads the contents into a list to be compared to with job comments."""
    city_file = open("cities.txt")
    return city_file.read().splitlines()


def connect_db(db_name: str):
    """Connects to the database. If it doesn't already exist, sqlite3 creates it."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    return conn, cursor


def setup_db(cursor: sqlite3.Cursor, table: str):
    """Creates the table for job entries if it doesn't already exist. ID is the job posting's ID from the API request,
    and is included for the sake of sorting and checking if the job posting already exists in the table."""
    cursor.execute("CREATE TABLE IF NOT EXISTS " + table + ";")


def close_db(conn: sqlite3.Connection):
    """Saves any chances to the database, and safely closes the connection to it."""
    conn.commit()
    conn.close()


def request_comment(url: str, tag: str):
    """Makes a request to the API for a specific comment, and attempts to pull a tag out. This is generalized to allow
    for either 'kids' or 'text' to be pulled. In the case of deleted comments and there is no 'text' value, exceptions
    handle what to do with them."""
    try:
        response = requests.get(url)  # top level Ask HN post
        try:
            return response.json()[tag]
        except (TypeError, KeyError):
            return "Null Response or Invalid Key"
    except requests.exceptions.ConnectionError:
        return "Invalid URL"


def check_ids(cursor: sqlite3.Cursor, job_ids: list):
    """Cleanses the list of job IDs to request by removing any that already have entries in the database.
    This massively cuts down on the time to retrieve new entries."""
    result = cursor.execute("SELECT id FROM jobs;")
    db_ids = [result[0] for result in result.fetchall()]

    job_ids = [job for job in job_ids if job not in db_ids]
    return job_ids


def get_listings(job_ids: list):
    """Handles making requests for each of the job comment IDs passed in via job_ids. Saves each comment's ID and
    its text description into a list of lists job_listings."""
    job_listings = []  # list of lists, each entry is a list of its id and its description
    count = 0

    for job in job_ids:
        listing = request_comment("https://hacker-news.firebaseio.com/v0/item/" + str(job) + ".json", "text")
        count += 1
        if listing == "Null Response or Invalid Key":
            print("Skipping invalid/null comment (" + str(count) + "/" + str(len(job_ids)) + ").")
            continue

        print("Processing job (" + str(count) + "/" + str(len(job_ids)) + ").")
        job_listings.append([job, listing])  # appends ID and then text

    return job_listings


def parse_listings(job_listings: list, cities: list):
    """Parses each job for: ID, title, location, skills, visa, remote/onsite status, website, and description."""
    parsed = []  # list of lists, each entry here is a list of its parsed elements

    for job in job_listings:
        data = list()

        # ID: job[0] always contains the ID of comment; referenced to avoid requesting jobs that are already in database
        data.append(job[0])

        # Title: assumes first word; not all are one word but this ensures retrieval of *some* data for every job entry
        data.append(job[1].lstrip().split(' ', 1)[0])  # gets the first word (stripped of whitespace)

        # Location: check if any of the cities list exists in job comment
        data.append(check_location(job[1], cities))

        # Skills TODO: not sure how to identify skills yet, fall back to a default value for now
        data.append("Unknown Skills")

        # Visa: check if the keyword 'visa' exists in job comment
        data.append(check_visa(job[1]))

        # Remote/Onsite: check if keywords 'remote', 'onsite', or both exist in job comment
        data.append(check_remote(job[1]))

        # Website: uses BeautifulSoup to parse any <a href='website-name.com'> tags from job comment
        data.append(check_website(job[1]))

        # Description: insert the full job comment (stripped of HTML tags for cleanliness sake)
        data.append(BeautifulSoup(job[1], 'html.parser').get_text())

        parsed.append(data)

    return parsed


def check_remote(job: str):
    """Helper function for checking whether or not a job supports remote or only onsite working (or both)."""
    if "remote" in job.lower() and "onsite" in job.lower():
        return "Remote and Onsite"
    elif "remote" in job.lower():
        return "Remote"
    elif "onsite" in job.lower():
        return "Onsite"
    else:
        return "Unknown Remote/Onsite"  # if not found


def check_location(job: str, cities: list):
    """Helper function for checking if the location of a job is listed in the city list retrieved from cities.txt."""
    for city in cities:
        if " " + city.lower() + " " in job.lower() or " " + city.lower() + ", " in job.lower():
            return city
    return "Unknown Location"  # if not found


def check_visa(job: str):
    """Helper function for checking if a job supports visa sponsorships or not."""
    if "visa" in job.lower():
        return "Yes"
    else:
        return "No"


def check_website(job: str):
    """Helper function for checking if a job has a website posted in it. Uses BeautifulSoup to find all <a href> tags
    and returns their values."""
    soup = BeautifulSoup(job, 'html.parser')
    tags = soup.find_all('a')
    if len(tags) > 0:
        return tags[0].get('href')
    else:
        return "Unknown Website"


def write_db(cursor: sqlite3.Cursor, statement: str, values: list):
    """Writes data to the database and ensures that only good data goes in, and bad data gets rejected with
    an exception and error message."""
    try:
        for value in values:
            cursor.execute(statement, value)
    except Exception as e:
        print("Exception: " + str(e))
        return "Error"
    return "Success"


def main():
    cities = open_city_file()
    conn, cursor = connect_db("jobs.db")
    table = "jobs(id INTEGER PRIMARY KEY, title TEXT, location TEXT, skills TEXT, visa TEXT, " \
            "onsite TEXT, website TEXT, description TEXT)"
    setup_db(cursor, table)
    print("Connected to database.")

    job_ids = request_comment("https://hacker-news.firebaseio.com/v0/item/21936440.json", "kids")
    if job_ids == "Invalid URL":
        print("Error with URL - shutting down.")
        exit()

    print("Retrieved job IDs from API.")

    job_ids = check_ids(cursor, job_ids)
    job_listings = get_listings(job_ids)
    if len(job_listings) == 0:
        print("No new jobs to add to database. Shutting down.")
        exit()

    print("Retrieved new job postings from API.")

    job_listings = parse_listings(job_listings, cities)
    print("Parsed job postings.")

    response = write_db(cursor, "INSERT INTO jobs(id, title, location, skills, visa, onsite, website, description) "
                                "VALUES(?, ?, ?, ?, ?, ?, ?, ?);", job_listings)
    if response != "Error":
        print("Wrote to database. Shutting down.")
    else:
        print("Error writing to database. Shutting down.")
        exit()

    close_db(conn)


if __name__ == "__main__":
    main()
