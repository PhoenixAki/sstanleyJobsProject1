import Main
import dash
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
        dcc.Graph(id="Job Map")
        ], className='map'
    ),

    html.Div([
        # Skills Filter
        html.Label("Enter skills to filter jobs by: "),
        dcc.Input(id="skills-input", value="", type="text"),
        html.Button(id='skills-button', n_clicks=0, children='submit')
        ], className='skills-input'
    ),

    html.Div([
        # Title Filter
        html.Label("Enter a company name to filter jobs by: "),
        dcc.Input(id="title-input", value="", type="text"),
        html.Button(id='title-button', n_clicks=0, children='submit')
        ], className='title-input'
    )
])


@app.callback(Output('Job Map', 'figure'),
              [Input('skills-button', 'n_clicks'), Input('title-button', 'n_clicks')],
              [State('skills-input', 'value'), State('title-input', 'value')]
              )
def filter_trigger(skills_n_clicks, title_n_clicks, skills_value, title_value):
    trigger = dash.callback_context.triggered[0]['prop_id'].split(',')[0]
    if trigger == "title-button.n_clicks":
        print("Title Input Value: " + title_value)
        return db_exec("title", title_value)
    elif trigger == "skills-button.n_clicks":
        print("Skills Input Value: " + skills_value)
        return db_exec('skills', skills_value)


def db_exec(column: str, input_value: str):
    conn, cursor = Main.connect_db("jobs.db")
    if input_value != "":
        jobs = cursor.execute("SELECT * FROM jobs WHERE " + column + " LIKE '%" + str(input_value) + "%';").fetchall()
    else:
        jobs = cursor.execute("SELECT * FROM jobs;").fetchall()

    Main.close_db(conn)
    return setup_map(jobs)


def setup_map(jobs: list):
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
    layout = go.Layout(title_text='Job Postings', title_x=0.5, width=1600, height=800,
                       mapbox=dict(center=dict(lat=42, lon=-71.5), accesstoken=mapboxtoken, zoom=6, style='light'))
    fig = go.Figure(data=[mapbox], layout=layout)

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
