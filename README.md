Name: Sean Stanley

Dependencies:
- Python 3.7
- BeautifulSoup (beautifulsoup4 package in pycharm)
- requests (library for requesting data from APIs)
- datetime (for reading job posting dates)
- pytz (timezone information for datetime)

What it does:
- This app first pulls out the top comment on the 13 months of Ask HN job posts (the initial one by HN telling people to post job entries in reponse). It then pulls all the top level responses (all the job entries) and requests each one from the API, and then puts them into a new list. It then sends this list off to another function to be parsed for data. After being parsed for various criteria, they are written to a database for storage. Upon startup, the app checks the existing database IDs so that jobs aren't re-requested later on if already in the database. There is also a bad_ids.txt file which contains known bad IDs (return None or otherwise garbage data from the API) which is compared with as well.
- There are 5 test functions in /test/test_Main.py. One confirms that with good URLs there are 13 months of data, and over 100 results for each, and that with a bad URL it returns an error. The second confirms that creating a table in a test database works properly. The third confirms that inserting data into the test database works with good data, and returns an error message with bad data that results in an exception. The fourth confirms that the data entered into the test database is actually there, by SELECT'ing it after and verifying that it is what it should be. The fifth confirms that the parsing function works properly, by supplying a test dummy job entry and verifying that the various keywords and information is pulled properly.

What is missing:
All is in place except for the parsing of skills, which falls back to default values currently. Detail on each piece of data:
- Title: For now, the first word of each job is inserted as the title. This works fine for jobs with single-word titles, but obviously is not correct for any that have multiple word titles.
- Location: Location is determined by comparing with a text file (cities.txt). The only real limitation to this working properly is not having a list of cities extensive enough (this list was massively increased in sprint 3, to where ~75% of jobs find a city match now, up from ~60% previously).
- Skills: Completely un-implemented due to not knowing a proper approach to finding skills/requirements. A default value is used for insertion.
- Visa + Remote/Onsite: Simple check for if the keywords exist in the job.
- Website: BeautifulSoup is used to extract <a> tags and pull the value of each href usage.
- Description: BeautifulSoup is used to extract any remaining HTML tags, and the resulting description string is inserted.
