import os
import sys
import re
import dash
import itertools
import dash_table
import pandas as pd
import plotly.graph_objs as go
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from dash_table.Format import Format, Scheme, Sign, Symbol

# Initiate the app ----------------------------------------------------------------
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
server = app.server
app.title="Talapas Calculator"

# app components ------------------------------------------------------------------

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

# assert su_cost('std', 1, 14, 0, 32, 10) == 140.0, "1 standard node using 14 cores and 28 GB RAM for 10 hrs does not equal 140 service units"

# assert su_cost('std', 1, 7, 1, 128, 10) == 280.0, "1 standard node using 7 cores and 128 GB RAM for 10 hrs does not equal 280 service units" # accommodate one gpu core

# assert su_cost('gpu', 1, 1, 3, 16, 10) == 420.0, "1 standard node using 7 cores and 128 GB RAM for 10 hrs does not equal 280 service units" # accommodate one gpu core


readme_content = dcc.Markdown(
"""

# About the calculator

* Input your requested parameters into the calculator as requested. To better approximate the price of a job, you should be familiar with the hardware specifications in Talapas (under Machine specifications below).

* Clicking the `View` button once will show how time and frequency affects job cost. Click it again to close the window.

* It is best not to change computing parameters while the graph is open because it will calculate a new matrix for every change in parameter.

* It is not informative to put negative numbers into the app.

# Example Calculations

Premise: service units are rooted around the concept that when using the base compute node, 1 CPU = 1 Service Unit

The idea here is that a job's usage effectively amounts to the largest fraction of resources utilized by the job on a node.  For instance, if a job uses all the available cores on a node but little memory then the job is using 100% of the node (i.e. there are no cores available for other jobs).  Likewise, if a job is only using one core but requires 100% of the memory on a node, that job is also using 100% of the node (there is insufficient memory for other jobs).

The service unit formula is normalized to give 28 SUs for one hour, corresponding to the number of SUs consumed when using one standard node (28 Broadwell cores) for one hour.  However, when using a rarified resource, a multiplicative factor applies. This resource may be a more recent generation of node (e.g. Skylake CPU), a node with specialized hardware (e.g. a GPU), or a node with a particular function (large memory server). The multiplicative factors for node types (NTFs) are based broadly around the cost disparity between these resources and include factors such as core count, core performance, and memory, and may be adjusted over time as part of the core facility rate setting process. 

* Example 1 (CPU driven SU): User A submits a job that is allocated 14 cores and 32 GB of RAM on one standard compute node.  Each compute node has a total of 28 cores and 128GB of RAM.  The job runs for 10 hours.  The job would have consumed 140 SU.

* Example 2 (Memory driven SU): User B submits a job that is allocated 7 cores and 128GB of RAM and one GPU on a GPU node. Each GPU node has a total of 28 cores and 256GB of RAM and 4 GPUs.  The job runs for 10 hours. Then the job would have consumed 280 SU.

* Example 3 (GPU driven SU): User C submits a job to the GPU partition and that job is allocated 1 core, 16GB of RAM, and 3 GPUs. The nodes in the GPU partition have 28 cpus, 256 GB of RAM, and 4 GPUs. This job runs for 10 hours and will have consumed 420 SU.

* Example 4 (CPU driven SU on Fat nodes): User D submits a job to the fat partition that is allocated 42 of the 56 available cpus and 512GB of memory.  The job finishes in 10 hours and will have consumed 1260 SU.

* Example 5 (Memory driven SU on Fat nodes): User E submits a job to the fat partition that is allocated 4 of the 56 available cpus and 2TB (2048GB) of memory.  The job finishes in 10 hours and will have consumed 3360 SU.

* Example 6 (Multiple standard nodes): User F submits a job that is allocated 16 standard nodes (28 cores and 128 GB of RAM per node, totaling 448 cores and 2048GB of memory).  The job runs for 10 hours and will have consumed 4480 SU.

# External resources for Talapas

* [Quick start guide](https://hpcrcf.atlassian.net/wiki/spaces/TCP/pages/7312376/Quick+Start+Guide)

* [Machine specifications](https://hpcrcf.atlassian.net/wiki/spaces/TCP/pages/6763193/Machine+Specifications)

* [Service Unit Calculations](https://hpcrcf.atlassian.net/wiki/spaces/TCP/pages/647299079/Service+Unit+Calculation)

* [Submit jobs with SLURM](https://hpcrcf.atlassian.net/wiki/spaces/TCP/pages/7286178/SLURM)
""")

readme_footer = dcc.Markdown(
"""
Application made by [Garth Kong](https://www.linkedin.com/in/garth-kong/), M.S.
"""
)

readme_modal = dbc.Modal([
    dbc.ModalHeader("UO Talapas Service Unit Calculator"),
    dbc.ModalBody(readme_content),
    dbc.ModalFooter(readme_footer),
    ],id="output_modal", size="xl",
)

sidebar = html.Div(
    [
        html.H4("Compute Parameters"),
        html.Hr(),
        dbc.Nav([
            dbc.FormGroup([
                dbc.Label("Select type of node"),
                dbc.Select(
                    id="node_type",
                    options=[
                        {'label': 'Standard', 'value': 'std'},
                        {'label': 'GPU', 'value': 'gpu'},
                        {'label': 'High-Memory', 'value': 'fat'}
                        ])]),
            dbc.FormGroup([
                dbc.Label("Number of nodes"),
                dbc.Input(
                    id="node_count",
                    value=1,
                    type="number",
                    debounce=True,
                    min=0)]),
            dbc.FormGroup([
                dbc.Label("Number of CPU(s)"),
                dbc.Input(
                    id="input_cpu",
                    value=1,
                    type="number",
                    debounce=True,
                    min=0)]),
            dbc.FormGroup([
                dbc.Label("Number of GPU(s)"),
                dbc.Input(
                    id="input_gpu",
                    value=0,
                    type="number",
                    debounce=True,
                    min=0)]),
            dbc.FormGroup([
                dbc.Label("Amount of RAM (GB)"),
                dbc.Input(
                    id="input_ram",
                    value=4,
                    type="number",
                    debounce=True,
                    min=0)]),
            dbc.FormGroup([
                dbc.Label("Job duration (hours)"),
                dbc.Input(
                    id="job_duration",
                    value=2.5,
                    type="number",
                    debounce=True)]),
            dbc.Label("Return results in units of SU or dollars."),
            dbc.RadioItems(
                id="input_units",
                value="units_dollars",
                options=[
                    {"label": "Service Units", "value": "units_su"},
                    {"label": "Dollars", "value": "units_dollars"}
                ]),
            html.Hr(),
            dbc.Label("View effects of frequency and time"),
            dbc.Button(
                "View (wait 10 seconds)",
                id="input_view",
                color = "primary"),
            html.Hr(),
            dbc.Button(
                "README",
                id="input_readme",
                color="primary"),
            readme_modal
            ],
            vertical=True, pills=True,
        ),
    ],
    style=SIDEBAR_STYLE,
)

content = html.Div(id="page-content", style=CONTENT_STYLE)

# app layout ----------------------------------------------------------------------
app.layout = html.Div([
    # app pages
    dcc.Location(id='url', refresh=False),
    dcc.Link('Navigate to home', href='/'),
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
            # dcc.Loading(id = 'loading_graph',children = [html.Div(dcc.Graph(id='output_graph'))], type = "default"),
            dcc.Graph(id='output_graph'),
            width={"offset": 3}
    )),

    # table of cost over time
    dbc.Row(
        dbc.Col(
            dash_table.DataTable(
                id='output_table', 
                style_table = {"height": 500, "overflowX": "scroll", "overflowY": "auto", "width": 900}, 
                style_as_list_view = True,
                style_header = {'backgroundColor': 'white', 'fontWeight': 'bold'},
                style_cell_conditional = [
                    {'if': {'column_id': 'Cost'}, 'width': 300},
                    {'if': {'column_id': 'Total Number of Jobs'}, 'width': 300},
                    {'if': {'column_id': 'Number of Days'}, 'width': 300}]),
            width={"size": 6, "offset": 4}
        ))
    ]
)

# tips:
# dbc.Alert() children is an empty list right now. Once it receives all the information then the callback will add the price to the dbc.Alert children.
# style_table height and width should be 100% to take over the size of the allocated grid. If the table is tiny, then you should adjust column width.
# however if you want overflow Y (vertical scrollbar), then you have to have a defined height.
# set a graph into a dcc.Loading children to get a loading screen.

# vars and f(x) -------------------------------------------------------------------
su_dollar = 0.025 # number of dollars per service unit
# note: total gpu units in a node is hard-coded as 4 below. Introduce a tot_gpu option if hardware changes in the future.

# define top resource used
def top_resource(alloc_CPU, cpu_denominator, alloc_GPU, gpu_denominator, alloc_RAM, ram_denominator):
    return( max([alloc_CPU / cpu_denominator, alloc_GPU / gpu_denominator, alloc_RAM / ram_denominator]) )

# calculate cost of job over time and frequency
def cost_table(est_cost, max_days = 32, max_freq = 101, units = "units_su"):
    """ 
    Input: cost of job
    Output: a plot of job cost over time (x) and frequency (y)
    """
    df_surface = pd.DataFrame(columns=['Number of Days', 'Total Number of Jobs'])
    for i in itertools.product(pd.Series(range(1, max_days)), pd.Series(range(1, max_freq))):
        temp_row = pd.Series(list(i), index=['Number of Days', 'Total Number of Jobs'])
        df_surface = df_surface.append(temp_row, ignore_index=True)
    if units == "units_su":
        df_surface = df_surface.assign(Cost = df_surface['Number of Days'] * df_surface['Total Number of Jobs'] * est_cost)
    elif units == "units_dollars":
        df_surface = df_surface.assign(Cost = df_surface['Number of Days'] * df_surface['Total Number of Jobs'] * est_cost * su_dollar)
    else:
        print("incorrect unit type. Must be 'units_su' or 'units_dollars'. ")
    return(df_surface)

def su_cost(node_type, node_count, cpu, gpu, ram, duration):
    """
    Calculates SU but only utilized for unit tests because different conda environments cannot use the app callback function as a standalone function.
    This is the exact same method used to get to SU calculations, but the output format is much more friendly for unit tests. This fx omits button clicks and dollar units.
    """
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
    return(su)

# Service Units Equation = SUM over allocated nodes(max(AllocCPU/TotCPU, AllocRAM/TotRAM, AllocGRES/TotGRES) * NTF) * 28 Service Units/hour * job duration in hours

# app callbacks -------------------------------------------------------------------

# readme callback
@app.callback(
    Output("output_modal", "is_open"),
    [Input("input_readme", "n_clicks")]
)
def readme(n_click):
    if n_click == None:
        return(False)
    if (n_click % 2 == 1):
        return(True)

# determine SU requested

# we input all 6 run types of run information
# we output 2 things: calculated SU and True that toggles dbc.Alert() to show up when all fields are selected.

@app.callback(
    [Output("output_su", 'children'),
    Output("output_su", "is_open"),
    Output("output_table", "data"),
    Output("output_table", "columns"),
    Output("output_graph", "figure")],
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
        fig = go.Figure(data=[go.Mesh3d(x=[],y=[],z=[])])
        return(None, False, table_data, table_columns, fig)
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
        est_cost  = "estimated service units: {}".format(round(su, 2))
    if units == "units_dollars":
        est_cost = "estimated cost in dollars: ${}".format(round(su * su_dollar, 2))
    # plot the table upon odd button click (1, 3, 5, ...)
    if n_click == None or n_click % 2 == 0:
        table_data = [] # empty table
        table_columns = []
        fig = go.Figure(data=[go.Mesh3d(x=[],y=[],z=[])])
    elif (n_click % 2 == 1):
        # build the table. data and styling goes here! Format() is a lifesaver.
        tbl = cost_table(su, units = units)
        table_data = tbl.to_dict('records')
        table_columns = [{"name": i, "id": i, "type": "numeric", "format": Format(precision=4)} for i in tbl.columns]
        # build the graph. data and styling goes here!
        fig = go.Figure(
            data=[go.Mesh3d(z=tbl['Cost'], 
            x=tbl['Number of Days'], 
            y = tbl['Total Number of Jobs'], 
            opacity=1, 
            intensity=tbl['Cost'], 
            colorscale="Inferno")])
        fig.update_layout(
            title="Job cost over time and frequency",
            scene = dict(
            xaxis_title="Number of Days (X)",
            yaxis_title="Total Number of Jobs (Y)",
            zaxis_title="Cost (Z)"),
            width=1000, height=800)
    return(est_cost, True, table_data, table_columns, fig)

# if you want an empty table, just return an empty list [] for output table's (data and columns) component id.

# unit tests ----------------------------------------------------------------------

# Example 1 (CPU driven SU): User A submits a job that is allocated 14 cores and 32 GB of RAM on one standard compute node.  Each compute node has a total of 28 cores and 128GB of RAM.  The job runs for 10 hours.  The job would have consumed
assert su_cost('std', 1, 14, 0, 32, 10) == 140.0, "1 standard node using 14 cores and 28 GB RAM for 10 hrs does not equal 140 service units"

# Example 2 (Memory driven SU): User B submits a job that is allocated 7 cores and 128GB of RAM and one GPU on a GPU node. Each GPU node has a total of 28 cores and 256GB of RAM and 4 GPUs.  The job runs for 10 hours. Then the job would have consumed
assert su_cost('std', 1, 7, 1, 128, 10) == 280.0, "1 standard node using 7 cores and 128 GB RAM for 10 hrs does not equal 280 service units" # accommodate one gpu core

# Example 3 (GPU driven SU): User C submits a job to the GPU partition and that job is allocated 1 core, 16GB of RAM, and 3 GPUs. The nodes in the GPU partition have 28 cpus, 256 GB of RAM, and 4 GPUs. This job runs for 10 hours and will have consumed
assert su_cost('gpu', 1, 1, 3, 16, 10) == 420.0, "1 standard node using 7 cores and 128 GB RAM for 10 hrs does not equal 280 service units" # accommodate one gpu core

# Example 4 (CPU driven SU on Fat nodes): User D submits a job to the fat partition that is allocated 42 of the 56 available cpus and 512GB of memory.  The job finishes in 10 hours and will have consumed
assert su_cost('fat', 1, 42, 0, 512, 10) == 1260, "1 fat node using 42 cores and 512 GB RAM for 10 hrs does not equal 1260 service units"

# Example 5 (Memory driven SU on Fat nodes): User E submits a job to the fat partition that is allocated 4 of the 56 available cpus and 2TB (2048GB) of memory.  The job finishes in 10 hours and will have consumed
assert su_cost('fat', 1, 4, 0, 2048, 10) == 3360.0, "1 fat node using 4 cores and 2048 GB RAM for 10 hrs does not equal 3360 service units"

# Example 6 (Multiple standard nodes): User F submits a job that is allocated 16 standard nodes (28 cores and 128 GB of RAM per node, totaling 448 cores and 2048GB of memory).  The job runs for 10 hours and will have consumed
assert su_cost('std', 16, 28, 0, 128, 10) == 4480.0, "16 std nodes using 28 cores and 128 GB RAM for 10 hrs does not equal 4480 service units"

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
# how do i set column width to a percentage? 

# dash resources --------------------------------------------------------------------

# dash datatable width, height, styling: https://dash.plotly.com/datatable/width https://dash.plotly.com/datatable/style