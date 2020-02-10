import Main


def test_get_jobs_ids():
    # ensures that a valid URL returns the IDs of job posts, and bad URL does not attempt to pull them
    good_result = Main.get_job_ids("https://hacker-news.firebaseio.com/v0/item/21936440.json")
    bad_result = Main.get_job_ids("http://obviously-bad-url-for-testing.json")
    assert len(good_result) > 100
    assert bad_result == "Invalid URL"


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
    assert Main.write_db(cursor, "testing(id, description) VALUES(?, ?)", [[123, 'Test Description']],
                         " OR REPLACE") == "Success"
    assert Main.write_db(cursor, "testing(id, description) VALUES(?, ?)", [['asdf', 456]], " OR REPLACE") == "Error"


def test_pull_data():
    """Tests that pulling data after insertion works properly, confirming that data is saved to the db."""
    conn, cursor = Main.connect_db("testing.db")
    Main.setup_db(cursor, "testing(id INTEGER PRIMARY KEY, description TEXT)")
    Main.write_db(cursor, "testing(id, description) VALUES(?, ?)", [[123, 'Test Description']], " OR REPLACE")
    conn.commit()
    result = cursor.execute("SELECT id FROM testing;").fetchone()
    assert result == (123,)
