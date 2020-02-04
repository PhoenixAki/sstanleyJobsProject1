import requests
from bs4 import BeautifulSoup


def get_job_ids(url):
    try:
        response = requests.get(url)  # top level Ask HN post
    except requests.exceptions.ConnectionError:
        return "Invalid URL"

    if response is not None:
        return response.json()["kids"]  # job listings are top level children of initial post


def get_listings(job_ids):
    job_listings = []
    count = 0

    for job in job_ids:
        listing = requests.get("https://hacker-news.firebaseio.com/v0/item/" + str(job) + ".json").json()  # pull listing
        if listing is not None:
            if listing.get("text") is not None:
                text = listing.get("text")
                text = BeautifulSoup(text, 'html.parser').get_text()  # cleanse text of HTML tags
                job_listings.append(text)
                count += 1

    return job_listings


def write_file(job_listings):
    file = open("job_listings.txt", "w", encoding="utf-8")
    count = 1

    for job in job_listings:
        file.write("Job " + str(count) + ": " + job + "\n\n")
        count += 1

    file.close()
    return file


def main():
    job_ids = get_job_ids("https://hacker-news.firebaseio.com/v0/item/21936440.json")
    print("Got job ids")
    if job_ids == "Invalid URL":
        print("Error with URL - shutting down.")
        exit()

    job_listings = get_listings(job_ids)
    print("Got job listings")
    file = write_file(job_listings)
    print("Wrote to " + file.name + ". Shutting down.")


if __name__ == "__main__":
    main()
