import os
import sys
import re
import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import itertools
import pandas as pd

# Initiate the app ----------------------------------------------------------------
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
server = app.server
app.title="Talapas SU Calc"

# bootstrap components ------------------------------------------------------------

# the style arguments for the sidebar. We use position:fixed and a fixed width
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "20rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

# the styles for the main content position it to the right of the sidebar and
# add some padding.
CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

sidebar = html.Div(
    [
        html.H4("Compute Parameters"),
        html.Hr(),
        dbc.Nav(
            [html.P("Select type of node"),
            dbc.Select(
                id="node_type",
                options=[
                    {'label': 'Standard', 'value': 'std'},
                    {'label': 'GPU', 'value': 'gpu'},
                    {'label': 'High-Memory', 'value': 'fat'}
                ]),
            html.Br(),
            html.P("Number of nodes"),
            dbc.Input(
                id="node_count",
                value=1,
                type="number",
                debounce=True),
            html.P("Number of CPU(s)"),
            dbc.Input(
                id="input_cpu",
                value=1,
                type="number",
                debounce=True),
            html.P("Number of GPU(s)"),
            dbc.Input(
                id="input_gpu",
                value=0,
                type="number",
                debounce=True),
            html.P("Amount of RAM (GB)"),
            dbc.Input(
                id="input_ram",
                value=4,
                type="number",
                debounce=True),
            html.P("Job duration (hours)"),
            dbc.Input(
                id="job_duration",
                value=2.5,
                type="number",
                debounce=True),
            html.Hr(),
            dbc.Label("Return results in units of SU or dollars."),
            dbc.Label("Rate = $0.025 per SU"),
            dbc.RadioItems(
                id="input_units",
                value="units_dollars",
                options=[
                    {"label": "Service Units", "value": "units_su"},
                    {"label": "Dollars", "value": "units_dollars"}
                ]),
            html.Hr(),
            dbc.Label("View effect of frequency and time"),
            dbc.Button(
                "View",
                id="input_view",
                color = "primary")
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=SIDEBAR_STYLE,
)

content = html.Div(id="page-content", style=CONTENT_STYLE)

df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/solar.csv')


# app layout ----------------------------------------------------------------------
app.layout = html.Div([
    # title
    dbc.Row(
        dbc.Col(
            html.H1("UO Talapas Service Unit Calculator", style={"white-space": "nowrap"}),
            width={"size": 4, "offset": 4}
    )),
    # sidebar
    sidebar, content,

    # estimated cost alert
    dbc.Row(
        dbc.Col(
            dbc.Alert(id = "output_su", children = [], color="success", style = {"text-align": "center"}, is_open = False),
            width={"size": 5, "offset": 4}
        )
    ),

    # graph cost over time
    dbc.Row(
        dbc.Col(
            dcc.Graph(id='output_graph'),
            width={"size": 7, "offset": 3}
    )),

    # table of cost over time
    dbc.Row(
        dbc.Col(
            # html.H1("hello world", style={"white-space": "nowrap"}), 
            dash_table.DataTable(id='output_table'),
            width={"size": 7, "offset": 3}
        ))
    ]
)

# tips:
# dbc.Alert() children is an empty list right now. Once it receives all the information then the callback will add the price to the dbc.Alert children.

# vars and f(x) -------------------------------------------------------------------
su_dollar = 0.025 # number of dollars per service unit
# note: total gpu units in a node is hard-coded as 4 below.

# define top resource used
def top_resource(alloc_CPU, cpu_denominator, alloc_GPU, gpu_denominator, alloc_RAM, ram_denominator):
    return( max([alloc_CPU / cpu_denominator, alloc_GPU / gpu_denominator, alloc_RAM / ram_denominator]) )

def cost_graph(table):
    fig = go.Figure(data=[go.Mesh3d(z=table['Cost'], 
                                x=table['Number of Days'], 
                                y = table['Frequency'], 
                                opacity=1, 
                                intensity=table['Cost'], 
                                colorscale="Inferno")])
    fig.update_layout(
        title="Job cost over time and frequency",
        width=700, height=700,
        scene = dict(
        xaxis_title="Number of Days (X)",
        yaxis_title="Frequency (Y)",
        zaxis_title="Cost (Z)"
    ))

# plot_mesh3d(wat)

def cost_table(est_cost, max_days = 31, max_freq = 100, units = "units_su"):
    """ 
    Input: cost of job
    Output: a plot of job cost over time (x) and frequency (y)
    """
    df_surface = pd.DataFrame(columns=['Number of Days', 'Frequency'])
    for i in itertools.product(pd.Series(range(1, max_days)), pd.Series(range(1, max_freq))):
        temp_row = pd.Series(list(i), index=['Number of Days', 'Frequency'])
        df_surface = df_surface.append(temp_row, ignore_index=True)
    if units == "units_su":
        df_surface = df_surface.assign(Cost = df_surface['Number of Days'] * df_surface['Frequency'] * est_cost)
    elif units == "units_dollars":
        df_surface = df_surface.assign(Cost = df_surface['Number of Days'] * df_surface['Frequency'] * est_cost * su_dollar)
    else:
        print("incorrect unit type. Must be 'su' or 'dollars'. ")
    # surface_plot = plot_mesh3d(df_surface)
    return(df_surface)

# Service Units Equation = SUM over allocated nodes(max(AllocCPU/TotCPU, AllocRAM/TotRAM, AllocGRES/TotGRES) * NTF) * 28 Service Units/hour * job duration in hours

# app callbacks -------------------------------------------------------------------

# determine SU requested

# we input all 6 run types of run information
# we output 2 things: calculated SU and True that toggles dbc.Alert() to show up when all fields are selected.

@app.callback(
    [Output("output_su", 'children'),
    Output("output_su", "is_open"),
    Output("output_table", "data"),
    Output("output_table", "columns")],
    [Input('node_type', 'value'),
    Input('node_count', 'value'),
    Input('input_cpu', 'value'),
    Input('input_gpu', 'value'),
    Input('input_ram', 'value'),
    Input('job_duration', 'value'),
    Input('input_units', 'value'), 
    Input('input_view', 'n_clicks')]
)
def calc_cost(node_type, node_count, cpu, gpu, ram, duration, units, n_click):
    # do not return anything if no user input
    if node_type == None:
        table_data = [] # empty table
        table_columns = []
        return(None, False, table_data, table_columns)
        pass
    # adjust NTF, total RAM, total CPU by node type
    if node_type == 'std':
        node_factor = 1
        tot_cpu = 28
        tot_ram = 128
    if node_type == 'gpu':
        node_factor = 2
        tot_cpu = 28
        tot_ram = 256
    if node_type == 'fat':
        node_factor = 6
        tot_cpu = 56
        tot_ram = 1024
    # job_setup = "current setup = {} node type + {} number of nodes + {} number of cpu # + {} number of ram + {} hrs duration of job + {} total cpu + {} total ram".format(node_type, node_count, cpu, ram, duration, tot_cpu, tot_ram)
    # calculate service units
    max_resource = top_resource(
        alloc_CPU = cpu, cpu_denominator = tot_cpu,
        alloc_GPU = gpu, gpu_denominator = 4,
        alloc_RAM = ram, ram_denominator = tot_ram)
    su = ( (node_count * (max_resource * node_factor)) * 28 * duration )
    # adjust output msg by units selected
    if units == "units_su":
        est_cost  = "estimated service units: {}".format(su)
    if units == "units_dollars":
        est_cost = "estimated cost in dollars: {}".format(su * su_dollar)
    # plot the table upon button click
    if n_click == None or n_click % 2 == 0:
        table_data = [] # empty table
        table_columns = []
    elif (n_click % 2 == 1):
        tbl = cost_table(su, units = units)
        table_data = tbl.to_dict('records')
        table_columns = [{"name": i, "id": i} for i in tbl.columns]
    return(est_cost, True, table_data, table_columns)

# if you want an empty table, just return an empty list [] for output table's (data and columns) component id.

# unit tests ----------------------------------------------------------------------

# unit test incompatible with public deployment, but still passes for personal deploy to browser.

# Example 1 (CPU driven SU): User A submits a job that is allocated 14 cores and 32 GB of RAM on one standard compute node.  Each compute node has a total of 28 cores and 128GB of RAM.  The job runs for 10 hours.  The job would have consumed
# assert float( re.findall("[\d.]+", calc_cost('std', 1, 14, 0, 32, 10, "units_su") )[0]) == 140.0, "1 standard node using 14 cores and 28 GB RAM for 10 hrs does not equal 140 service units"

# Example 2 (Memory driven SU): User B submits a job that is allocated 7 cores and 128GB of RAM and one GPU on a GPU node. Each GPU node has a total of 28 cores and 256GB of RAM and 4 GPUs.  The job runs for 10 hours. Then the job would have consumed
# assert float( re.findall("[\d.]+", calc_cost('std', 1, 7, 1, 128, 10, "units_su") )[0]) == 280.0, "1 standard node using 7 cores and 128 GB RAM for 10 hrs does not equal 280 service units" # accommodate one gpu core

# Example 3 (GPU driven SU): User C submits a job to the GPU partition and that job is allocated 1 core, 16GB of RAM, and 3 GPUs. The nodes in the GPU partition have 28 cpus, 256 GB of RAM, and 4 GPUs. This job runs for 10 hours and will have consumed
# assert float( re.findall("[\d.]+", calc_cost('gpu', 1, 1, 3, 16, 10, "units_su") )[0]) == 420.0, "1 standard node using 7 cores and 128 GB RAM for 10 hrs does not equal 280 service units" # accommodate one gpu core

# Example 4 (CPU driven SU on Fat nodes): User D submits a job to the fat partition that is allocated 42 of the 56 available cpus and 512GB of memory.  The job finishes in 10 hours and will have consumed
# assert float( re.findall("[\d.]+", calc_cost('fat', 1, 42, 0, 512, 10, "units_su") )[0]) == 1260, "1 fat node using 42 cores and 512 GB RAM for 10 hrs does not equal 1260 service units"

# Example 5 (Memory driven SU on Fat nodes): User E submits a job to the fat partition that is allocated 4 of the 56 available cpus and 2TB (2048GB) of memory.  The job finishes in 10 hours and will have consumed
# assert float( re.findall("[\d.]+", calc_cost('fat', 1, 4, 0, 2048, 10, "units_su") )[0]) == 3360.0, "1 fat node using 4 cores and 2048 GB RAM for 10 hrs does not equal 3360 service units"

# Example 6 (Multiple standard nodes): User F submits a job that is allocated 16 standard nodes (28 cores and 128 GB of RAM per node, totaling 448 cores and 2048GB of memory).  The job runs for 10 hours and will have consumed
# assert float( re.findall("[\d.]+", calc_cost('std', 16, 28, 0, 128, 10, "units_su") )[0]) == 4480.0, "16 std nodes using 28 cores and 128 GB RAM for 10 hrs does not equal 4480 service units"

# run app --------------------------------------------------------------------------

if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False)

# deployment resources -------------------------------------------------------------

# sign up for account at heroku.

# installing heroku: https://dev.to/twiddlewakka/heroku-cli-on-wsl-26fp
    # curl https://cli-assets.heroku.com/install.sh | sh
    # `heroku apps` to log in. 


# configure project, env, and hosting on heroku: https://stackoverflow.com/questions/47949173/deploy-a-python-dash-app-to-heroku-using-conda-environments-instead-of-virtua

# lingering questions --------------------------------------------------------------
# how do i chain callbacks together? I want callback2 to retrieve the output of callback1 so I can modularize each component of the app.
# in bootstrap, how do I vertical offset?
# how can i learn enough CSS to build an app that is viewable on desktop and mobile?
# how do i not show a plot by default, and only display it upon the click of a button?
# how do i include a good looking navbar with bootstrap?
# how do i incorporate 2 sliders into a graph?
# how do i make multi-page app?