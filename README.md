## Dependencies:
- Python 3.7 (I used 3.7.9)
- BeautifulSoup (beautifulsoup4 package in pycharm)
- requests (library for requesting data from APIs)
- datetime (for reading job posting dates)
- pytz (timezone information for datetime)
- Geotext (for location parsing)
- Geopy (for location lookup)
- Plotly (for map visualzation)
- Dash (for web page setup for map visualization)

## What It Does
- Main.py pulls the top comment on the 13 months of Ask HN job posts, and then pulls all the top level response IDs (all the job entries) from the API, storing them in a new list. This list of IDs is then cleansed to remove any jobs that already exist in the database, or known bad IDs. Afterwards, each job is requested from the API and then parsed. Once finished parsing, they are written to a database for storage.
- Plotting.py uses Plotly and Dash to visualize the job postings onto a map, with 4 filters and an HTML table below the filters. All 4 filters (company name, onsite/remote, visa sponsorship, and post date) are functional, though they work independent of each other (see the end of the README for why). Clicking any of the city markers on the map will populate the table with all of the jobs from that city. The table can be sorted, though the built-ini default sorting for the post date column does not work perfectly. Run Plotting.py and the web page will be loaded onto the localhost connection. On my PC this seems to default to 127.0.0.1:8050, but I do not know for sure that it will be specifically that for other systems.
- There are 7 tests in /test/test_Main.py. One confirms that with good URLs there are 13 months of data, over 100 results for each, and that with a bad URL it returns an error. The second test confirms that creating a table in a test database works properly. The third test confirms that inserting data into the test database works with good data, and returns an error message with bad data. The fourth test confirms that the data entered into the test database is actually there, by SELECT'ing it after and verifying its contents. The fifth test confirms that the parsing function works properly, by supplying a test dummy job entry and verifying that the various keywords and information is pulled properly. The sixth test simulates the user clicking on a city on the map visualization, and confirms that the proper data is displayed in the table. The seventh and final test confirms that the 4 filters work properly by checking that the number of jobs returned is in line with the database.

## What Is Missing
The vast majority of requirements have been met properly, with a few caveats. Here are the known bugs and inaccuracies:
- Title Parsing: Due to the title not being easy to dynamically pull from jobs, he first word of each job is assumed to be the title. This works fine for jobs with single-word titles, but obviously is not correct for any that have multiple word titles.
- Location Parsing: Location detection is limited to what Geotext can locate from each job. As a result, ~16% of jobs in the database simply have "Unknown Location" listed.
- Skills Parsing: Skill detection is limited to the list of skills I manually included in Main.py lines 112-114. I tried to be inclusive of any major skill or language I could think of, but about ~13% of jobs have "Unknown Skills" listed.
- Job Technology Filtering: I interpreted this to mean filtering based on the Skills previously mentioned, so that is what is displayed.
- Company Filtering: I interpreted this to mean the title of the job parsed above, so that is what is displayed.
- **Known Bug**: If you select a city on the map that has multiple pages in the table (Boston, for example), and you advance it to page 2 and then click another location, the table does not populate properly. To fix this, go back to the first city and return it to page 1 in the table. This appears to be a bug within Dash itself (where the table is generated from), as my code does nothing in relation to the table display.
- Multiple Filters: All 4 filters work independently, but they do *not* work simultaneously with each other. This was intentional, as the wording in the assignment did not state that they needed to work together. I did attempt to get it working, but had trouble forming the correct SQL statements to pull the correct jobs. As a result, using one filter after another one will only filter the map based on the second filter.
