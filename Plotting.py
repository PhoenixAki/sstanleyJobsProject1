import Main
from datetime import datetime
import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input, State
import plotly.graph_objects as go


mapboxtoken = "pk.eyJ1IjoicGhvZW5peGFraSIsImEiOiJjazdkOXQwNXYwMXg0M2xsYzQ5aGQyZTM1In0.pHC_MJXMDXCo9-o-EirQFw"
app = dash.Dash()
app.title = "Job Postings (Feb 2019 - Feb 2020)"
app.layout = html.Div([
    html.Div([
        # Map
        dcc.Graph(
            id="job-map",
        )], className='map'
    ),

    html.Div([
        # Onsite/Remote Filter
        html.Label("Onsite Filter (show only jobs that are remote, onsite, or both):"),
        dcc.Dropdown(
            id='onsite-dropdown',
            options=[
                {'label': 'Onsite', 'value': 'Onsite'},
                {'label': 'Remote', 'value': 'Remote'},
                {'label': 'Both', 'value': 'Both'}
            ],
            style={'width': '500px'},
            searchable=False,
        ),
        html.Button(id='onsite-button', n_clicks=0, children='submit onsite filter')
        ], className='onsite-dropdown'
    ),

    html.Div([
        # Date Range Filter
        html.Label("Date Filter (show jobs posted in a specific date range):"),
        dcc.DatePickerRange(
            id='date-input',
            min_date_allowed=datetime(2019, 2, 1),
            max_date_allowed=datetime(2020, 2, 29),
            initial_visible_month=datetime(2020, 2, 1),
            end_date=datetime(2020, 2, 29)
        ),
        html.Button(id='date-button', n_clicks=0, children='submit date filter')
        ], className='date-input'
    ),

    html.Div([
        # Skills Filter
        html.Label("Skills Filter (show jobs by recommended skills): "),
        dcc.Input(id="skills-input", value="", type="text"),
        html.Button(id='skills-button', n_clicks=0, children='submit skills filter')
        ], className='skills-input'
    ),

    html.Div([
        # Title Filter
        html.Label("Company Filter (show jobs by company name): "),
        dcc.Input(id="title-input", value="", type="text"),
        html.Button(id='title-button', n_clicks=0, children='submit title filter')
        ], className='title-input'
    ),

    html.Div([
        # Job Information Table
        html.H3("JOB DETAILS (click a location to list all jobs there):"),
        dash_table.DataTable(
            id='data-table',
            columns=[
                {"name": "City", "id": "city"},
                {"name": "Post Date", "id": "post-date"},
                {"name": "Title", "id": "title"},
                {"name": "Skills", "id": "skills"},
                {"name": "Visa Sponsorship", "id": "visa"},
                {"name": "Onsite/Remote", "id": "onsite"},
                {"name": "Website", "id": "website"}
            ],
            style_table={"width": "1500px"},
            sort_action='native'
        )], className='data-table'
    )
])


# Graph Click Event Callback
@app.callback(Output('data-table', 'data'), [Input('job-map', 'clickData')])
def update_table(click_data: dict):
    """Callback function that updates the Datatable element with a list of jobs retrieved from get_job_details."""
    if click_data is None:
        return [{}]
    else:
        return get_job_details(click_data)


def get_job_details(click_data):
    """Parses click_data for a city name and pulls jobs from the database that are in that city. Those jobs
    are then appended into a list of dictionaries to be fed into the datatable rows."""
    city = click_data.get("points")[0].get("hovertext")
    conn, cursor = Main.connect_db("jobs.db")
    jobs = cursor.execute("SELECT * FROM jobs WHERE location LIKE '%" + city + "%';").fetchall()
    table_data = []

    for job in jobs:
        table_data.append(
            {"city": job[3].split(',')[0],
             "post-date": job[1],
             "title": job[2],
             "skills": job[4],
             "visa": job[5],
             "onsite": job[6],
             "website": job[7]
             }
        )

    Main.close_db(conn)
    return table_data


# Filter Callback
@app.callback(Output('job-map', 'figure'),
              [Input('skills-button', 'n_clicks'), Input('title-button', 'n_clicks'),
               Input('onsite-button', 'n_clicks'), Input('date-button', 'n_clicks')],
              [State('skills-input', 'value'), State('title-input', 'value'),
               State('onsite-dropdown', 'value'), State('date-input', 'start_date'), State('date-input', 'end_date')]
              )
def update_graph(skills_n_clicks, title_n_clicks, onsite_n_clicks, date_n_clicks, skills_value, title_value,
                 onsite_value, start_date, end_date):
    """Callback function that updates the graph based on filters. This function determines which filter
    triggered the callback, and passes appropriate information to db_exec for further handling."""
    trigger = dash.callback_context.triggered[0]['prop_id'].split(',')[0]
    if trigger == "title-button.n_clicks":
        jobs = db_exec("title", title_value)
    elif trigger == "skills-button.n_clicks":
        jobs = db_exec('skills', skills_value)
    elif trigger == "date-button.n_clicks":
        jobs = db_exec("date", [start_date, end_date])
    elif trigger == "onsite-button.n_clicks":
        jobs = db_exec("onsite", onsite_value)
    else:
        print("Error in filter callback function.")
        return

    return setup_map(jobs)


def db_exec(column: str, input_value):
    """Takes in a column name and filter value and forms the correct SQL statement based on those. The resulting
    list of jobs is returned (or sent for further parsing, if date filter)."""
    conn, cursor = Main.connect_db("jobs.db")

    if column == "date" and input_value[0] is not None and input_value[1] is not None:
        return calc_date(cursor, input_value)
    elif input_value != "" and (column == "title" or column == "skills"):
        return cursor.execute("SELECT * FROM jobs WHERE " + column + " LIKE '%" + input_value + "%';").fetchall()
    elif column == "onsite" and input_value is not None:
        return cursor.execute("SELECT * FROM jobs WHERE onsite='" + input_value + "';").fetchall()
    else:
        return cursor.execute("SELECT * FROM jobs;").fetchall()


def calc_date(cursor, dates: list):
    """Takes in a start and end date for a range and returns a list of jobs that are in that range."""
    start = datetime.strptime(dates[0], "%Y-%m-%d")
    end = datetime.strptime(dates[1], "%Y-%m-%d")
    all_jobs = cursor.execute("SELECT * FROM jobs;").fetchall()
    filtered_jobs = list()

    for job in all_jobs:
        job_date = datetime.strptime(job[1], "%m/%d/%Y, %H:%M:%S")
        if end >= job_date >= start:  # if job is in range, add to filtered list
            filtered_jobs.append(job)

    return filtered_jobs


def setup_map(jobs: list):
    """Takes in a filtered list of jobs and re-forms the map visualization with their data."""
    lats = []
    longs = []
    text = []

    for job in jobs:
        if job[3] == "Unknown Location":
            continue
        loc = job[3].split(',')
        text.append(loc[0])
        lats.append(loc[1])
        longs.append(loc[2])

    mapbox = go.Scattermapbox(lat=lats, lon=longs, hovertext=text, hoverinfo='text',
                              marker=dict(symbol='marker', size=15, color='blue'))
    layout = go.Layout(title_text='Job Postings', title_x=0.5, width=1600, height=700,
                       mapbox=dict(center=dict(lat=42.25, lon=-71), accesstoken=mapboxtoken, zoom=7, style='light'))
    fig = go.Figure(data=[mapbox], layout=layout)

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
