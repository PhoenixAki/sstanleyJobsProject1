import sqlite3
import time
from geotext import GeoText
from geopy import Nominatim
from bs4 import BeautifulSoup
import requests
from datetime import datetime
import pytz


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
    """Creates the table for job entries if it doesn't already exist."""
    cursor.execute("CREATE TABLE IF NOT EXISTS " + table + ";")


def close_db(conn: sqlite3.Connection):
    """Saves any chances to the database, and safely closes the connection to it."""
    conn.commit()
    conn.close()


def request_comment(url: str, ids: list, tag: str):
    """Makes a request to the given URL, and attempts to pull a tag out. This is generalized to allow for
    either 'kids' from a parent comment, or 'text' from a single comment to be pulled."""
    responses = []
    try:
        for post_id in ids:
            post = requests.get(url + str(post_id) + ".json")  # top level Ask HN posts
            if tag == "text":
                responses.append([post.json()["time"], post.json()["text"]])
            elif tag == "kids":
                responses.append(post.json()["kids"])
    except (requests.exceptions.ConnectionError, TypeError, KeyError):
        return "Error retrieving comment or its data."

    if tag == "text":
        return responses[0]
    elif tag == "kids":
        return responses


def check_ids(cursor: sqlite3.Cursor, job_ids: list):
    """Cleanses the list of job IDs by removing known bad ids and duplicates already in the database.
    This massively cuts down on the time to retrieve new entries."""
    jobs = cursor.execute("SELECT id FROM jobs;").fetchall()
    db_ids = [job[0] for job in jobs]
    ids = cursor.execute("SELECT id FROM bad_ids;").fetchall()
    bad_ids = [bad_id[0] for bad_id in ids]
    good_ids = []

    for i in range(len(job_ids)):
        keep = []
        for job in job_ids[i]:
            if job not in db_ids and job not in bad_ids:
                keep.append(job)
        good_ids.append(keep)

    return good_ids


def get_listings(cursor: sqlite3.Cursor, job_ids: list):
    """Makes requests for each of the job comment IDs passed in. Each comment's ID and
    text description are saved into a list of job_listings."""
    job_listings = []  # each entry is a list of its id and its description
    bad_ids = []  # keeps track of bad job IDs to avoid requesting them in the future
    month_count = 0

    for month in job_ids:
        month_count += 1
        job_count = 0
        for job_id in month:
            listing = request_comment("https://hacker-news.firebaseio.com/v0/item/", [job_id], "text")
            job_count += 1
            if listing == "Error retrieving comment or its data.":
                print("Skipped invalid comment (job #" + str(job_count) + "/" + str(len(month)) + ", month " +
                      str(month_count) + "/" + str(len(job_ids)) + ").")
                bad_ids.append(job_id)
                continue

            print("Processed job #" + str(job_count) + "/" + str(len(month)) + " for month " +
                  str(month_count) + "/" + str(len(job_ids)) + ".")
            job_listings.append([job_id, listing[0], listing[1]])  # appends ID, time, and text

    write_db(cursor, "INSERT INTO bad_ids(id) VALUES(?);", bad_ids)
    return job_listings


def parse_listings(job_listings: list, cursor=None):
    """Parses each job for: ID, post date, title, location, skills, visa, remote/onsite, website, and description."""
    lookup = Nominatim(user_agent="sstanley_jobs_project")  # for geopy lookup of locations
    parsed = []  # contains list of jobs with parsed elements
    skills = ["Java", "Python", "C++", "C#", " C ", "Go", "Ruby", "Web Development", "HTML", "CSS",
              "Software Engineer", "Javascript", "SQL", "React", "Nodejs", "Android", "iOS", "Swift",
              "AWS", "MongoDB", "Kotlin"]
    count = 0

    for job in job_listings:
        count += 1
        print("Parsing job " + str(count) + "/" + str(len(job_listings)))

        parsed.append([
            # ID: job[0] contains the ID of comment; referenced to avoid requesting jobs that are already in database
            job[0],

            # Post Date: job[1] always contains comment date in unix time; convert to text date format
            datetime.fromtimestamp(job[1], pytz.utc).strftime("%m/%d/%Y, %H:%M:%S"),

            # Title: assumes first word; not all are one word but this ensures retrieval of some data for every job
            job[2].lstrip().split(' ', 1)[0],  # gets the first word (stripped of whitespace),

            # Location: check for city names in text and lookup coordinates via Geopy (if not cached)
            check_location(job[2], cursor, lookup),

            # Skills: check job for appearances of above list of possible skills
            check_skills(job[2].lower(), skills),

            # Visa: check if the keyword 'visa' exists in job comment
            check_visa(job[2]),

            # Remote/Onsite: check if keywords 'remote', 'onsite', or both exist in job comment
            check_remote(job[2].lower()),

            # Website: uses BeautifulSoup to parse any <a href='https://website-name.com'> tags from job comment
            check_website(job[2]),

            # Description: insert the full job comment (stripped of HTML tags for cleanliness sake)
            BeautifulSoup(job[2], 'html.parser').get_text()
        ])

    return parsed


def check_remote(job: str):
    """Helper function for checking whether a job supports remote or onsite working (or both)."""
    if "remote" in job and "onsite" in job:
        return "Both"
    elif "remote" in job:
        return "Remote"
    elif "onsite" in job:
        return "Onsite"
    else:
        return "Unknown Remote/Onsite"


def check_location(job: str, cursor: sqlite3.Cursor, nom: Nominatim):
    """Helper function for checking if the location of a job is listed. If so, the coordinates are looked up via
    Geopy (if not in the location cache)."""
    response = GeoText(job)  # Pull city names with GeoText
    if len(response.cities) > 0:
        location = response.cities[0]  # assume first city is job location
    else:
        return "Unknown Location"

    if cursor is None:  # None if coming from test_Main.py, to avoid using GeoPy service for tests
        return location

    # Cross-check with cache and look up coordinates with Geopy if needed
    cache = cursor.execute("SELECT * FROM cache WHERE name='" + location + "';").fetchall()

    if len(cache) == 1:  # if in cache, use that information
        print(location + " is in cache, using its coordinates.")
        values = [location, str(cache[0][1]), str(cache[0][2])]
        return ', '.join(values)  # comma separated string of name, latitude, and longitude
    else:  # if not in cache, lookup with Geopy
        print(location + " is not in cache, using Nominatim.")
        time.sleep(1)  # 1-second delay to follow Nominatim's TOS
        lookup = nom.geocode(location, exactly_one=True)  # only pull first result

        if lookup is None:
            return "Unknown Location"
        else:
            print("Found " + location + " via Nominatim, using its coordinates.")
            values = [location, str(lookup.latitude), str(lookup.longitude)]
            write_db(cursor, "INSERT INTO cache(name, latitude, longitude) VALUES(?, ?, ?);", [values])
            print("Wrote " + location + " to cache.")
            return ', '.join(values)  # comma separated string of name, latitude, and longitude


def check_skills(job: str, skills: list):
    """Helper function for checking if a job contains any of the given list of skills."""
    skill_list = []
    for skill in skills:
        if skill.lower() in job:
            skill_list.append(skill.strip())

    if len(skill_list) == 0:
        return "Unknown Skills"
    else:
        return ', '.join(skill_list)  # comma separated string of skills


def check_visa(job: str):
    """Helper function for checking if a job supports visa sponsorships or not."""
    if "visa" in job.lower():
        return "Yes"
    else:
        return "No"


def check_website(job: str):
    """Helper function for checking if a job has a website posted in it. Uses BeautifulSoup to find <a href> tags
    and returns value of the first appearing one."""
    soup = BeautifulSoup(job, 'html.parser')
    tags = soup.find_all('a')
    if len(tags) > 0:
        return tags[0].get('href')
    else:
        return "Unknown Website"


def write_db(cursor: sqlite3.Cursor, statement: str, values: list):
    """Writes data to the given database and ensures that only good data goes in, and bad data gets rejected."""
    try:
        for value in values:
            if type(value) == int:
                value = [value]
            cursor.execute(statement, value)
    except Exception as e:
        print("Exception: " + str(e))
        return "Error"
    return "Success"


def main():
    conn, cursor = connect_db("jobs.db")
    print("Connected to database.")

    setup_db(cursor, "jobs(id INTEGER PRIMARY KEY, date TEXT, title TEXT, location TEXT, skills TEXT, "
                     "visa TEXT, onsite TEXT, website TEXT, description TEXT)")
    setup_db(cursor, "cache(name TEXT PRIMARY KEY, latitude REAL, longitude REAL)")
    setup_db(cursor, "bad_ids(id INTEGER PRIMARY KEY)")
    print("Setup jobs, cache, and bad_ids tables.")

    job_ids = request_comment("https://hacker-news.firebaseio.com/v0/item/",
                              [19055166, 19281834, 19543940, 19797594, 20083795, 20325925, 20584311, 20867123,
                               21126014, 21419536, 21683554, 21936440, 22225314], "kids")
    if job_ids == "Error retrieving comment or its data.":
        print("Error with URL - shutting down.")
        exit()

    print("Retrieved job IDs from API.")

    job_ids[0] = job_ids[0]
    job_ids = check_ids(cursor, job_ids)
    if not any(job_ids):
        print("No new jobs to add to database. Shutting down.")
        exit()

    job_listings = get_listings(cursor, job_ids)
    print("Retrieved new job postings from API.")

    job_listings = parse_listings(job_listings, cursor)
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
