Name: Sean Stanley

Dependencies:
- Python 3.7
- BeautifulSoup (beautifulsoup4 package in pycharm)
- requests (library for requesting data from APIs)

What it does:
- This app first pulls out the top comment on the post (the initial one by HN telling people to post job entries in reponse). It then pulls all the top level responses (all the job entries) and requests each one from the API. It puts them into a new list. Each job entry has its description pulled and cleansed of HTML tags by BeautifulSoup. It then sends this list off to another function to be written to job_listings.txt. 
- There are 4 test functions in /test/test_Main.py. One confirms that with a good URL there are over 100 results of job entries, and that with a bad URL it returns an error. The second confirms that creating a table in a test database works properly. The third confirms that inserting data into the test database works with good data, and returns an error message with bad data that results in an exception. The fourth confirms that the data entered into the test database is actually there, by SELECT'ing it after and verifying that it is what it should be.

What is missing:
All is in place except for the parsing, which is is *mostly* working. Detail on each piece of data:
- Title: For now, the first word of each job is inserted as the title. This works fine for jobs with single-word titles, but obviously is not correct for any that have multiple word titles.
- Location: Location is determined by comparing with a text file (cities.txt). The only real limitation to this working properly is not having a list of cities extensive enough.
- Skills: Completely un-implemented due to not knowing a proper approach to finding skills/requirements. A default value is used for insertion.
- Visa + Remote/Onsite: Simple check for if the keywords exist in the job.
- Website: BeautifulSoup is used to extract <a> tags and pull the value of each href usage.
