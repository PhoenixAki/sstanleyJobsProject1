Name: Sean Stanley

Dependencies:
- Python 3.7
- BeautifulSoup (beautifulsoup4 package in pycharm)
- requests (library for requesting data from APIs)

What it does:
- This app first pulls out the top comment on the post (the initial one by HN telling people to post job entries in reponse). It then pulls all the top level responses (all the job entries) and requests each one from the API. It puts them into a new list. Each job entry has its description pulled and cleansed of HTML tags by BeautifulSoup. It then sends this list off to another function to be written to job_listings.txt. 
- There are 2 test functions in /test/test_Main.py. One confirms that with a good URL there are over 100 results of job entries, and that with a bad URL it returns an error. The other function test confirms that data from job entries is properly written to job_listings.txt. **NOTE** I manually pulled out 1 job entry from the list of all job entries and directly checked this one, in order to have the test not take a long time every time it's ran (as it would be waiting for all 600+ job entry requests to finish).

What is missing:
- Job postings are not parsed for title, location, etc. The formal isntructions state to do this, but on Slack it was stated this is not necessary until the next sprint when we work with databases a bit, but I wanted to clarify here I am aware of that. Other than that, nothing should be missing from the requirements.
