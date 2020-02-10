**Bold parts are new/relevant to sprint 2**

Name: Sean Stanley

Dependencies:
- Python 3.7
- BeautifulSoup (beautifulsoup4 package in pycharm)
- requests (library for requesting data from APIs)

What it does:
- This app first pulls out the top comment on the post (the initial one by HN telling people to post job entries in reponse). It then pulls all the top level responses (all the job entries) and requests each one from the API. It puts them into a new list. Each job entry has its description pulled and cleansed of HTML tags by BeautifulSoup. It then sends this list off to another function to be written to job_listings.txt. 
- **There are 4 test functions in /test/test_Main.py.** One confirms that with a good URL there are over 100 results of job entries, and that with a bad URL it returns an error. **The second confirms that creating a table in a test database works properly. The third confirms that inserting data into the test database works with good data, and returns an error message with bad data that results in an exception. The fourth confirms that the data entered into the test database is actually there, by SELECT'ing it after and verifying that it is what it should be.**

What is missing:
- **Job postings are "kinda sorta" being parsed. Due to the inconsistent formatting of the job postings (most use | to separate information at the start but not all, and the ones that do have different ordering of them) it was difficult to find any patterns to be able to rely on for grabbing the right data from each entry. For now, I have it performing simple checks (until I can figure out the best way to do this) and relying on default values for any times the correct info can not be found.**
