import sqlite3
from bs4 import BeautifulSoup
import requests
from datetime import datetime
import pytz


def open_city_file():
    """Opens the cities file and reads the contents into a list to be compared to with job comments."""
    city_file = open("cities.txt")
    return city_file.read().splitlines()


def open_id_file():
    """Opens the blacklisted IDs text file, which contains known bad IDs from Ask HN (e.g. its associated
    comment contained null or otherwise bad data). This prevents the program from continually re-checking
    known bad IDs every time it runs."""
    try:
        id_file = open("bad_ids.txt", 'r')
    except FileNotFoundError:
        print("bad_ids.txt not found.")
        return []

    return id_file.read().splitlines()


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


def request_comment(url: str, ids: list, tag: str):
    """Makes a request to the API for specific comments, and attempts to pull a tag out. This is generalized to allow
    for either 'kids' or 'text' to be pulled. In the case of deleted comments and there is no 'text' value, exceptions
    handle what to do with them."""
    responses = list()
    try:
        for post_id in ids:
            post = requests.get(url + str(post_id) + ".json")  # top level Ask HN posts
            if tag == "text":
                responses.append([post.json()["time"], post.json()[tag]])
            elif tag == "kids":
                responses.append(post.json()[tag])
    except (requests.exceptions.ConnectionError, TypeError, KeyError):
        return "Error retrieving comment or its data."

    if tag == "text":
        return responses[0]
    elif tag == "kids":
        return responses


def check_ids(cursor: sqlite3.Cursor, job_ids: list, bad_ids: list):
    """Cleanses the list of job IDs to request by removing any that already have entries in the database.
    This massively cuts down on the time to retrieve new entries."""
    result = cursor.execute("SELECT id FROM jobs;")
    db_ids = [result[0] for result in result.fetchall()]
    cleansed_ids = []

    for i in range(len(job_ids)):
        keep = list()
        for job in job_ids[i]:
            if job not in db_ids and str(job) not in bad_ids:
                keep.append(job)
        cleansed_ids.append(keep)

    return cleansed_ids


def get_listings(job_ids: list):
    """Handles making requests for each of the job comment IDs passed in via job_ids. Saves each comment's ID and
    its text description into a list of lists job_listings."""
    job_listings = []  # list of lists, each entry is a list of its id and its description
    invalid_ids = []  # blacklist that will be kept track of to avoid continuously rechecking known bad job comment IDs
    month_count = 0

    for month in job_ids:
        month_count += 1
        job_count = 0
        for job_id in month:
            listing = request_comment("https://hacker-news.firebaseio.com/v0/item/", [job_id], "text")
            job_count += 1
            if listing == "Error retrieving comment or its data.":
                print("Skipped invalid comment in month (" + str(job_count) + "/" + str(len(month)) + ").")
                invalid_ids.append(job_id)
                continue

            print("Processed job #" + str(job_count) + "/" + str(len(month)) + " for month " +
                  str(month_count) + "/" + str(len(job_ids)) + ".")
            job_listings.append([job_id, listing[0], listing[1]])  # appends ID, time, and text

    write_invalid_ids(invalid_ids)
    return job_listings


def write_invalid_ids(invalid_ids: list):
    id_file = open("bad_ids.txt", 'r+')

    for bad_id in invalid_ids:
        id_file.write(str(bad_id) + "\n")

    id_file.close()


def parse_listings(job_listings: list, cities: list):
    """Parses each job for: ID, post date, title, location, skills, visa, remote/onsite, website, and description."""
    parsed = []  # list of lists, each entry here is a list of its parsed elements
    count = 0

    for job in job_listings:
        count += 1
        print("Parsing job " + str(count) + "/" + str(len(job_listings)))
        data = list()

        # ID: job[0] always contains the ID of comment; referenced to avoid requesting jobs that are already in database
        data.append(job[0])

        # Post Date: every post contains its date in unix time; convert to text date format
        data.append(datetime.fromtimestamp(job[1], pytz.utc).strftime("%m/%d/%Y, %H:%M:%S"))

        # Title: assumes first word; not all are one word but this ensures retrieval of *some* data for every job entry
        data.append(job[2].lstrip().split(' ', 1)[0])  # gets the first word (stripped of whitespace)

        # Location: check if any of the cities list exists in job comment
        data.append(check_location(job[2], cities))

        # Skills TODO: not sure how to identify skills yet, fall back to a default value for now
        data.append("Unknown Skills")

        # Visa: check if the keyword 'visa' exists in job comment
        data.append(check_visa(job[2]))

        # Remote/Onsite: check if keywords 'remote', 'onsite', or both exist in job comment
        data.append(check_remote(job[2]))

        # Website: uses BeautifulSoup to parse any <a href='website-name.com'> tags from job comment
        data.append(check_website(job[2]))

        # Description: insert the full job comment (stripped of HTML tags for cleanliness sake)
        data.append(BeautifulSoup(job[2], 'html.parser').get_text())

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
    bad_ids = open_id_file()
    conn, cursor = connect_db("jobs.db")
    table = "jobs(id INTEGER PRIMARY KEY, date TEXT, title TEXT, location TEXT, skills TEXT, visa TEXT, " \
            "onsite TEXT, website TEXT, description TEXT)"
    setup_db(cursor, table)
    print("Connected to database.")

    job_ids = request_comment("https://hacker-news.firebaseio.com/v0/item/",
                              [19055166, 19281834, 19543940, 19797594, 20083795, 20325925, 20584311, 20867123,
                               21126014, 21419536, 21683554, 21936440, 22225314], "kids")
    if job_ids == "Error retrieving comment or its data.":
        print("Error with URL - shutting down.")
        exit()

    print("Retrieved job IDs from API.")

    job_ids = check_ids(cursor, job_ids, bad_ids)
    job_listings = get_listings(job_ids)
    if len(job_listings) == 0:
        print("No new jobs to add to database. Shutting down.")
        exit()

    print("Retrieved new job postings from API.")

    job_listings = parse_listings(job_listings, cities)
    print("Parsed job postings.")

    response = write_db(cursor, "INSERT INTO jobs(id, date, title, location, skills, visa, onsite, website, "
                                "description) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?);", job_listings)
    if response == "Error":
        print("Error writing to database. Shutting down.")
    else:
        print("Wrote to database. Shutting down.")

    close_db(conn)


if __name__ == "__main__":
    main()
