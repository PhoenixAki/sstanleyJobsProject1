import Main
import requests


def test_get_jobs_ids():
    # ensures that a valid URL returns the IDs of job posts, and bad URL does not attempt to pull them
    good_result = Main.get_job_ids("https://hacker-news.firebaseio.com/v0/item/21936440.json")
    bad_result = Main.get_job_ids("http://obviously-bad-url-for-testing.json")
    assert len(good_result) > 100
    assert bad_result == "Invalid URL"


def test_write_file():
    # writes the first job entry to a file, re-opens it, and confirms the entry is there
    # for this sprint, the comparison assumes CodeWeavers is still the first entry, if that changes the test will break
    result = Main.get_job_ids("https://hacker-news.firebaseio.com/v0/item/21936440.json")
    job = requests.get("https://hacker-news.firebaseio.com/v0/item/" + str(result[0]) + ".json").json()["text"]
    jobs = [job]
    Main.write_file(jobs)
    file = open("job_listings.txt", "r")
    line = file.readline()
    assert "CodeWeavers | St Paul, MN, USA |" in line
