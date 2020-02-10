import sqlite3
import requests


def open_city_file():
    city_file = open("cities.txt")
    cities = []

    for line in city_file:
        cities.append(line.lower())

    return cities


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


def get_job_ids(url: str):
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
    result = cursor.execute("SELECT id FROM jobs;")
    db_ids = [result[0] for result in result.fetchall()]

    job_ids = [job for job in job_ids if job not in db_ids]
    return job_ids


def get_listings(job_ids: list):
    job_listings = []  # list of lists, each entry here is a list of its id and its description
    count = 0

    for job in job_ids:
        listing = requests.get("https://hacker-news.firebaseio.com/v0/item/" + str(job) + ".json").json()
        print("Processing job #" + str(count) + "/" + str(len(job_ids)))
        count += 1
        if listing is not None and listing.get("text") is not None:
            text = listing.get("text")
            job_listings.append([job, text])  # appends ID and then text

    return job_listings


def parse_listings(job_listings: list, cities: list):
    parsed = []  # list of lists, each entry here is a list of its parsed elements

    for job in job_listings:
        count = 0
        checks = [False] * 6
        data = [job[0], "Unknown Title", "Unknown Location", "Unknown Skills", "Unknown Visa Sponsorship",
                "Unknown Remote/Onsite", "Unknown Website", "Unknown Description"]  # default values

        # setup new entry and append ID to start
        split = job[1].split('|')

        for part in split:
            count += 1
            if count == len(split)-1:
                data[7] = split[-1]
                break

            # title
            if checks[0] is False:
                checks[0] = True
                data[1] = part  # assuming first split entry is always title for now
                continue

            # location
            if checks[1] is False:
                for city in cities:
                    if city in part.lower():
                        checks[1] = True
                        data[2] = part
                        continue

            # skills
            if checks[2] is False and "skills" in part.lower():
                checks[2] = True
                data[3] = part
                continue

            # visa
            if checks[3] is False and "visa" in part.lower():
                checks[3] = True
                data[4] = "Yes"
                continue

            # remote/onsite info
            if checks[4] is False:
                if "remote" in part.lower() and "onsite" in part.lower():
                    data[5] = "Remote and Onsite"
                    checks[4] = True
                    continue
                elif "remote" in part.lower():
                    data[5] = "Remote"
                    checks[4] = True
                    continue
                elif "onsite" in part.lower():
                    data[5] = "Onsite"
                    checks[4] = True
                    continue

            # website
            if checks[5] is False and "http" in part.lower():
                checks[5] = True
                data[6] = part
                continue

        parsed.append(data)

    return parsed


def write_db(cursor: sqlite3.Cursor, table: str, values: list, replace: str):
        try:
            for value in values:
                cursor.execute("INSERT" + replace + " INTO " + table + ";", value)
        except Exception as e:
            print("Exception: " + str(e))
            return "Error"

        return "Success"


def main():
    cities = open_city_file()  # text file with city names used to match text in job entries
    conn, cursor = connect_db("jobs.db")
    setup_db(cursor, "jobs(id INTEGER PRIMARY KEY, title TEXT, location TEXT, skills TEXT, "
                     "visa TEXT, onsite TEXT, website TEXT, description TEXT)")
    print("Connected to database.")

    job_ids = get_job_ids("https://hacker-news.firebaseio.com/v0/item/21936440.json")
    if job_ids == "Invalid URL":
        print("Error with URL - shutting down.")
        exit()

    print("Retrieved job IDs from API.")

    job_ids = check_ids(cursor, job_ids)
    if len(job_ids) == 0:
        print("No new jobs to add to database. Shutting down.")
        exit()

    job_listings = get_listings(job_ids)
    print("Retrieved new job postings from API.")

    job_listings = parse_listings(job_listings, cities)
    print("Parsed job postings.")

    response = write_db(cursor, "jobs(id, title, location, skills, visa, onsite, website, description) "
                                "VALUES(?, ?, ?, ?, ?, ?, ?, ?)", job_listings, "")
    if response is not "Error":
        print("Wrote to database. Shutting down.")
    else:
        print("Error writing to database. Shutting down.")
        exit()

    close_db(conn)


if __name__ == "__main__":
    main()
