import Main


def test_get_jobs_ids():
    """Tests that a value URL returns the IDs of the child comments, and that a bad URL returns an error message."""
    good_ids = [19055166, 19281834, 19543940, 19797594, 20083795, 20325925, 20584311, 20867123, 21126014, 21419536,
                21683554, 21936440, 22225314]
    good_result = Main.request_comment("https://hacker-news.firebaseio.com/v0/item/", good_ids, "kids")
    bad_result = Main.request_comment("http://obviously-bad-url-for-testing.json", [12345], "kids")
    assert len(good_result) == 13  # ensures that 13 months of data is retrieved
    assert len(good_result[0]) > 100  # ensures that for a given month, a large number of comment IDs is retrieved
    assert bad_result == "Error retrieving comment or its data."


def test_table_create():
    """Tests that adding a table succeeds by SELECT'ing that table back out after."""
    conn, cursor = Main.connect_db("testing.db")
    Main.setup_db(cursor, "testing(id INTEGER PRIMARY KEY, description TEXT)")
    result = cursor.execute("SELECT * FROM sqlite_master WHERE type='table' AND name='testing';")
    assert len(result.fetchall()) == 1


def test_write_db():
    """Tests that inserting data to a table works properly. Good data should be added, bad data should be rejected."""
    conn, cursor = Main.connect_db("testing.db")
    Main.setup_db(cursor, "testing(id INTEGER PRIMARY KEY, description TEXT)")
    assert Main.write_db(cursor, "INSERT OR REPLACE INTO testing(id, description) VALUES(?, ?);",
                         [[123, 'Test Description']]) == "Success"
    assert Main.write_db(cursor, "INSERT OR REPLACE INTO testing(id, description) VALUES(?, ?);",
                         [['Test Description', 456]]) == "Error"


def test_pull_data():
    """Tests that pulling data after insertion works properly, confirming that data is saved to the db."""
    conn, cursor = Main.connect_db("testing.db")
    Main.setup_db(cursor, "testing(id INTEGER PRIMARY KEY, description TEXT)")
    Main.write_db(cursor, "INSERT OR REPLACE INTO testing(id, description) VALUES(?, ?);", [[123, 'Test Description']])
    conn.commit()
    result = cursor.execute("SELECT id FROM testing;").fetchone()
    assert result == (123,)


def test_parse_data():
    """Tests that the correct info is parsed from a sample job entry. A slice is taken from response to simplify testing
    on the parts of the listing that are actually pulled out by parse_listings; the final index (description) is
    formatted by BeautifulSoup and difficult to compare to from a test standpoint after the fact."""

    # test_entry with ID of 123, unix time of 796996800 (my birthday of 4/4/1995, set to 12PM), and sample description
    test_entry = [123, 796996800, "TestCompanyName | Detroit | Visa Support | Remote + Onsite | "
                                  "<a href='https://test-website-name.com'> </a> | TestCompanyName is seeking "
                                  "programmers with at least 3 years experience in the industry for performing "
                                  "PyTest commands on student's projects. sql is also preferred. Apply at "
                                  "the website above."]

    # dummy list of cities provided as opposed to opening the full file since this is a direct test
    parsed = Main.parse_listings([test_entry])
    assert parsed[0][:-1] == [123, '04/04/1995, 12:00:00', 'TestCompanyName', 'Detroit', 'sql,', 'Yes',
                              'Remote and Onsite', 'https://test-website-name.com']
