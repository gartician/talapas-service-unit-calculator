import os
import sys
import re
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly_express as px

# Initiate the app ----------------------------------------------------------------
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.title="Talapas SU Calc"

# bootstrap components ------------------------------------------------------------

# the style arguments for the sidebar. We use position:fixed and a fixed width
# SIDEBAR_STYLE = {
#     "position": "fixed",
#     "top": 0,
#     "left": 0,
#     "bottom": 0,
#     "width": "16rem",
#     "padding": "2rem 1rem",
#     "background-color": "#f8f9fa",
# }

# the styles for the main content position it to the right of the sidebar and
# add some padding.
# CONTENT_STYLE = {
#     "margin-left": "18rem",
#     "margin-right": "2rem",
#     "padding": "2rem 1rem",
# }

# sidebar = html.Div(
#     [
#         html.H3("Compute Parameters", className="display-4"),
#         html.Hr(),
#         html.P(
#             "Select the list of things you need and <tab> through each option.", className="lead"
#         ),
#         dbc.Nav(
#             [dbc.DropdownMenu(
#                 label='type of node',
#                 children=[
#                 dbc.DropdownMenuItem("Standard"),
#                 dbc.DropdownMenuItem("GPU"),
#                 dbc.DropdownMenuItem("High-Memory"),
#                 ]),
#                 dbc.NavLink("Page 1", href="/page-1", id="page-1-link"),
#                 dbc.NavLink("Page 2", href="/page-2", id="page-2-link"),
#                 dbc.NavLink("Page 3", href="/page-3", id="page-3-link"),
#             ],
#             vertical=True,
#             pills=True,
#         ),
#     ],
#     style=SIDEBAR_STYLE,
# )

# content = html.Div(id="page-content", style=CONTENT_STYLE)

# app layout ----------------------------------------------------------------------
app.layout = html.Div(children=[
    # title
    html.H1("UO Talapas Service Unit Calculator", style={"text-align": "center"}),
    
    # sidebar 
    # dcc.Location(id="url"), sidebar, content,
    # type of node = standard, gpu, fat
    html.Br(), html.Br(), html.Br(),
    html.Label('Node type'),
    dcc.Dropdown(
        id='node_type',
        multi=False,
        style={"width": "40%"},
        value='std',
        clearable=False,
        options=[
            {'label': 'Standard', 'value': 'std'},
            {'label': 'GPU', 'value': 'gpu'},
            {'label': 'High-Memory', 'value': 'fat'}
        ]),
    html.Br(),
    # number of nodes
    html.Label('Number of nodes'),
    dcc.Input(
        id='node_count',
        value=1,
        type="number",
        debounce=True),
    html.Br(),
    # allocated cpu 
    html.Label('Allocated CPU'),
    dcc.Input(
        id='input_cpu',
        value=1,
        type="number",
        debounce=True),
    html.Br(),
    # allocated gpu
    html.Label('Allocated GPU'),
    dcc.Input(
        id="input_gpu",
        value=0,
        type="number",
        debounce=True),
    html.Br(),
    # allocated ram
    html.Label('Allocated RAM (GB)'),
    dcc.Input(
        id="input_ram",
        value=4,
        type="number",
        debounce=True),
    html.Br(),
    # job duration
    html.Label('Job duration (hrs)'),
    dcc.Input(
        id="job_duration",
        value=2.5,
        type="number",
        debounce=True),
    html.Br(),
    # frequency
    html.Label('Frequency'),
    dcc.Input(
        id="job_frequency",
        value=1,
        type="number",
        debounce=True),
    html.Br(),
    # frequency per time 
    html.Label('Frequency per time'),
    dcc.Dropdown(
        id='job_time',
        multi=False,
        style={"width": "40%"},
        clearable=True,
        options=[
            {'label': 'Daily', 'value': 'daily'},
            {'label': 'Weekly', 'value': 'weekly'},
            {'label': 'Monthly', 'value': 'monthly'},
            {'label': 'Quarterly', 'value': 'quarterly'},
            {'label': 'Bi-annually', 'value': 'bi_annually'},
            {'label': 'Annually', 'value': 'annually'}
        ]),
    # ESTIMATED COST
    html.Div(id='output_su', style={"width": "25%", "float": "left"}),
    html.Br(),
    # GRAPH OVER TIME
    # html.Div(
    #     [html.H3('This is my graph')],
    #     dcc.Graph(id='output_graph')
    # ),
    # html.Br(),
    # TABLE OVER TIME
    ]
)
# Garth: set up a basic layout + basic components. DONE!
# Garth: pass all the unit tests. DONE!
# Garth: make x-axis (time) a slider underneath the graph so users can see short and long-term use.
# Garth: make the above into a table
# Garth: styling (move to bootstrap or stick with dcc?)

# vars and f(x) -------------------------------------------------------------------
su_dollar = 0.025 # converts SU to dollars

def top_resource(alloc_CPU, cpu_denominator, alloc_GPU, gpu_denominator, alloc_RAM, ram_denominator):
    return( max([alloc_CPU / cpu_denominator, alloc_GPU / gpu_denominator, alloc_RAM / ram_denominator]) )

# Service Units Equation = SUM over allocated nodes(max(AllocCPU/TotCPU, AllocRAM/TotRAM, AllocGRES/TotGRES) * NTF) * 28 Service Units/hour * job duration in hours

# app callbacks -------------------------------------------------------------------

# determine SU requested
@app.callback(
    Output(component_id="output_su", component_property='children'),
    [Input(component_id='node_type', component_property='value'),
    Input(component_id='node_count', component_property='value'),
    Input(component_id='input_cpu', component_property='value'),
    Input(component_id='input_gpu', component_property='value'),
    Input(component_id='input_ram', component_property='value'),
    Input(component_id='job_duration', component_property='value'),
    Input(component_id='job_frequency', component_property='value')]
)
def calc_cost(node_type, node_count, cpu, gpu, ram, duration, frequency):
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
    job_setup = "current setup = {} node type + {} number of nodes + {} number of cpu # + {} number of ram + {} hrs duration of job + {} frequency of job + {} total cpu + {} total ram".format(node_type, node_count, cpu, ram, duration, frequency, tot_cpu, tot_ram)
    max_resource = top_resource(
        alloc_CPU = cpu, cpu_denominator = tot_cpu, 
        alloc_GPU = gpu, gpu_denominator = 4, 
        alloc_RAM = ram, ram_denominator = tot_ram)
    su = ( (node_count * (max_resource * node_factor)) * 28 * duration )
    if frequency > 1:
        su = su * frequency
        # est_cost = su * su_dollar * frequency
    else:
        su = su
        # est_cost = su * su_dollar
    return(su)
    # return("estimated cost: {}".format(est_cost))

# plot graph of job over time and frequency
# @app.callback(
#     Output('output_graph', 'children'),
#     [Input(component_id='node_type', component_property='value'),
#     Input(component_id='node_count', component_property='value'),
#     Input(component_id='input_cpu', component_property='value'),
#     Input(component_id='input_gpu', component_property='value'),
#     Input(component_id='input_ram', component_property='value'),
#     Input(component_id='job_duration', component_property='value'),
#     Input(component_id='job_frequency', component_property='value'),
#     Input(component_id='job_time', component_property='value')])
# def calc_cost_time(node_type, node_count, cpu, gpu, ram, duration, frequency, over_time):
#     if over_time == None:
#         return(None)
#     if over_time == "daily":
#         print('it will cost {} dollars per day '.format(cost) )
#     if over_time == "weekly":
#         print("it will cost {} dollars per week ".format(cost * 7) )
#     if over_time == "monthly":
#         print("it will cost {} dollars per month (30 days) ".format(cost * 30))
#     if over_time == "bi_annual":
#         print("it will cost {} dollars per year".format(cost * 2))
#     if over_time == "quarterly":
#         print("it will cost {} dollars per year ".format(cost * 4))
#     if over_time == "annually":
#         print("it will cost {} dollars per year ".format(cost))

# unit tests ----------------------------------------------------------------------

# Example 1 (CPU driven SU): User A submits a job that is allocated 14 cores and 32 GB of RAM on one standard compute node.  Each compute node has a total of 28 cores and 128GB of RAM.  The job runs for 10 hours.  The job would have consumed
assert float( re.findall("[\d.]+", calc_cost('std', 1, 14, 0, 32, 10, 1) )[0]) == 140.0, "1 standard node using 14 cores and 28 GB RAM for 10 hrs does not equal 140 service units"

# Example 2 (Memory driven SU): User B submits a job that is allocated 7 cores and 128GB of RAM and one GPU on a GPU node. Each GPU node has a total of 28 cores and 256GB of RAM and 4 GPUs.  The job runs for 10 hours. Then the job would have consumed
assert float( re.findall("[\d.]+", calc_cost('std', 1, 7, 1, 128, 10, 1) )[0]) == 280.0, "1 standard node using 7 cores and 128 GB RAM for 10 hrs does not equal 280 service units" # accommodate one gpu core

# Example 3 (GPU driven SU): User C submits a job to the GPU partition and that job is allocated 1 core, 16GB of RAM, and 3 GPUs. The nodes in the GPU partition have 28 cpus, 256 GB of RAM, and 4 GPUs. This job runs for 10 hours and will have consumed
assert float( re.findall("[\d.]+", calc_cost('gpu', 1, 1, 3, 16, 10, 1) )[0]) == 420.0, "1 standard node using 7 cores and 128 GB RAM for 10 hrs does not equal 280 service units" # accommodate one gpu core

# Example 4 (CPU driven SU on Fat nodes): User D submits a job to the fat partition that is allocated 42 of the 56 available cpus and 512GB of memory.  The job finishes in 10 hours and will have consumed
assert float( re.findall("[\d.]+", calc_cost('fat', 1, 42, 0, 512, 10, 1) )[0]) == 1260, "1 fat node using 42 cores and 512 GB RAM for 10 hrs does not equal 1260 service units"

# Example 5 (Memory driven SU on Fat nodes): User E submits a job to the fat partition that is allocated 4 of the 56 available cpus and 2TB (2048GB) of memory.  The job finishes in 10 hours and will have consumed
assert float( re.findall("[\d.]+", calc_cost('fat', 1, 4, 0, 2048, 10, 1) )[0]) == 3360.0, "1 fat node using 4 cores and 2048 GB RAM for 10 hrs does not equal 3360 service units"

# Example 6 (Multiple standard nodes): User F submits a job that is allocated 16 standard nodes (28 cores and 128 GB of RAM per node, totaling 448 cores and 2048GB of memory).  The job runs for 10 hours and will have consumed
assert float( re.findall("[\d.]+", calc_cost('std', 16, 28, 0, 128, 10, 1) )[0]) == 4480.0, "16 std nodes using 28 cores and 128 GB RAM for 10 hrs does not equal 4480 service units"

# run app --------------------------------------------------------------------------

if __name__ == '__main__':
    app.run_server(debug=True)