# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt
import flask
import glob
import pandas as pd
import geopandas as gpd
import numpy as np
import json
from io import open
from pyproj import Proj, transform
import fiona
from fiona.crs import from_epsg
from toolz import groupby, compose, pluck
from dotenv import load_dotenv
import os
from csv import DictReader
from flask_caching import Cache


#dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
#load_dotenv(dotenv_path)


MAPBOX_KEY = "pk.eyJ1Ijoibmlja2ZvcmZpbnNraSIsImEiOiJjam51cTNxY2wwMTJ2M2xrZ21wbXZrN2F1In0.RooxCuqsNotDzEP2EeuJng"

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = 'RSD Contract QAQC'

cache = Cache(app.server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory'
})


def make_table_rows(df):
    return df.to_dict("rows")


def make_test_result_columns():
    columns = []
    for k, v in check_result_names.iteritems():
        columns.append({'name': [k, 'Value'], 'id': k})
        columns.append({'name': [k, 'Result'], 'id': v})
    return columns


def generate_table(df):

    return html.Div([

                dt.DataTable(
                        id='qaqc-table',
                        filtering=True,
                        sorting=True,
                        row_selectable="multi",
                        columns=[
                                {'name': ['', 'Centroid X'], 'id': 'centroid_x', 'hidden': True},
                                {'name': ['', 'Centroid Y'], 'id': 'centroid_y', 'hidden': True}
                            ]+[
                                {'name': ['Class Counts', c], 'id': 'class{}count'.format(c)} 
                                for c in las_classes.keys()
                            ]+make_test_result_columns(),  
                        data=make_table_rows(df),
                        merge_duplicate_headers=True,
                        style_table={
                            'maxHeight': '90vh',
                            'overflowY': 'scroll'
                        },
                        style_cell={
                            'backgroundColor': 'rgb(50, 50, 50)',
                            'border': 'lightgrey',
                            'color': colors['text'],
                            'margin-top': '1px',
                            'margin-bottom': '1px',
                        },
                        style_header={'textAlign': 'center'},
                        style_data_conditional=[
                            {
                                'if': {'column_id': c},
                                'textAlign': 'left'
                            } for c in []  # enter fields you wante left aligned
                        ] + [
                            {
                                "if": {"row_index": 4},
                                "backgroundColor": "#ffffcc",
                                'color': colors['background']
                            }
                        ] + [
                            {
                            'if': {
                                'column_id': t,
                                'filter': '{} eq "PASSED"'.format(t)
                                },
                            'backgroundColor': colors['pass_green'],
                            'color': 'white',
                            } for t in check_result_columns
                        ] + [
                            {
                            'if': {
                                'column_id': t,
                                'filter': '{} eq "FAILED"'.format(t)
                                },
                            'backgroundColor': colors['fail_red'],
                            'color': 'white',
                            } for t in check_result_columns
                        ],
                        style_as_list_view=False,
                    ),
                html.Div(id='qaqc-table-container')
                ])


def make_bathy_hist_data():
    mu, sigma = 0, 0.1 # mean and standard deviation
    s = np.random.normal(mu, sigma, 1000)
    hist, bin_edges = np.histogram(s, bins=100)
    return (hist, bin_edges)


def get_qaqc_map(check_name, check_label, map_style, contract_tile_csv, qaqc_results_csv):
    # groupby returns a dictionary mapping the values of the first field
    # 'classification' onto a list of record dictionaries with that
    # classification value.
    listpluck = compose(list, pluck)

    selected_contract_field = 'Notes'
    contract_tiles = groupby(selected_contract_field, contract_tile_csv)

    selected_qaqc_field = check_label
    qaqc_results = groupby(selected_qaqc_field, qaqc_results_csv)

    contract_tiles = [
        {
            "type": "scattermapbox",
            "lat": listpluck("centroid_y", tile),
            "lon": listpluck("centroid_x", tile),
            "mode": "markers",
            "name": field,
            "marker": {
                "size": 5,
                "opacity": 1,
                "color": map_colors['tiles'][field],
            },
            "text": listpluck("Las_Name", tile),
            'hoverinfo': "name+text",
        }
        for field, tile in contract_tiles.items()
    ]

    qaqc_tiles = [
        {
            "type": "scattermapbox",
            "lat": listpluck("centroid_y", tile),
            "lon": listpluck("centroid_x", tile),
            "mode": "markers",
            "name": '{} ({})'.format(field, check_name),
            "marker": {
                "size": 8,
                "opacity": 0.7,
                "color": map_colors['check_result'][field],
            },
            'hoverinfo': "name",
        }
        for field, tile in qaqc_results.items()
    ]

    tiles = [
        dict(
            type='scattermapbox',
            lon=tile_coords_x,
            lat=tile_coords_y,
            mode='lines',
            #fill='toself',
            line=dict(width=0.8, color='rgb(34, 57, 94)'),
            name='Contrator Tiles',
            hovermode='closest',
            hoverinfo='none'
            )
        ]

    return {
        "data":  qaqc_tiles + contract_tiles + tiles,
        "layout": {
            'legend': dict(
                x=0,
                y=0,
                traceorder='normal',
                font=dict(
                    family='sans-serif',
                    size=12,
                    color=colors['text']
                ),
                bgcolor='rgba(26,26,26,1)',
            ),
            'margin': {'l': 0, 'r': 0, 't': 0, 'b':0},
            'showlegend': True,
            "autosize": True,
            "hovermode": "closest",
            "mapbox": {
                'layers': [],
                "accesstoken": MAPBOX_KEY,
                "bearing": 0,
                "center": {
                    "lat": 41.35,
                    "lon": -70.2
                },
                "pitch": 0,
                "zoom": 10,
                "style": map_style,
            }
        }
    }


def get_tile_geojson_file():
    qaqc_dir = r'C:\QAQC_contract\nantucket'
    las_tiles_geojson = os.path.join(qaqc_dir, 'tiles.json')
    with open(las_tiles_geojson, encoding='utf-8') as f:
        geojson_data = json.load(f)
    return geojson_data


def get_contract_tile_csv():
    fin = open(r'C:\QAQC_contract\nantucket\tiles_centroids.csv', 'r')
    reader = DictReader(fin)
    tile_centroids = [line for line in reader]
    fin.close()
    return tile_centroids


def get_tiles_df():
    df = pd.read_csv(r'C:\QAQC_contract\nantucket\tiles_centroids.csv')
    return df


def get_qaqc_df():
    df = pd.read_csv(r'C:\QAQC_contract\nantucket\qaqc_tile_collection_results.csv')
    return df


def get_qaqc_results_csv():
    fin = open(r'C:\QAQC_contract\nantucket\qaqc_tile_collection_results.csv', 'r')
    reader = DictReader(fin)
    qaqc_results = [line for line in reader]
    fin.close()
    return qaqc_results


def gen_tile_coords(shp):
    input = gpd.read_file(shp).to_crs({'init': 'epsg:4326'})  # wgs84 (temporary)

    coords = []
    for index, row in input.iterrows():
        for pt in list(row['geometry'].exterior.coords): 
            coords.append(list(pt))
        coords.append([None, None])
    
    coords = np.asarray(coords, dtype=np.str)
    x = coords[:, 0]
    y = coords[:, 1]

    return x.tolist(), y.tolist()


tiles_shp = r'C:\QAQC_contract\nantucket\EXTENTS\final\Nantucket_TileGrid.shp'
tile_coords_x, tile_coords_y = gen_tile_coords(tiles_shp)

las_classes = {
        0: ('Created, never classified' ,'las00'),
        1: ('Unclassified1', 'las01'),
        2: ('Ground', 'las02'),
        3: ('Low Vegetation', 'las03'),
        4: ('Medium Vegetation', 'las04'),
        5: ('High Vegetation', 'las05'),
        6: ('Building', 'las06'),
        7: ('Low Point (noise)', 'las07'),
        8: ('Model Key-point (mass point)', 'las08'),
        9: ('Water', 'las09'),
        26: ('Bathymetry', 'las26'),
        27: ('Water Surface', 'las27'),
    }

map_colors = {
    'tiles': {
        'Outside AOI and no Bathy': 'rgb(67, 67, 67)',
        'Project Area/Found Bathy': 'rgb(0, 119, 224)',
        'automated ground run only/no review': 'rgb(32, 140, 37)',
    },
    'check_result': {
        'PASSED': 'rgb(101,255,0)',
        'FAILED': 'rgb(255,0,0)',
    },
}

colors = {
    'background': '#373D42',
    'text': '#B1C4D2',
    'header': '#0968AA',
    'button_background': '#75777a',
    'pass_green': '#3D9970',
    'fail_red': '#ff4d4d'
}

map_button_style = {
    'color': colors['text'],
    'border-color': colors['text'],
    'background-color': colors['button_background'],
    'border-radius': '50px',
    'padding': '0px',
    'line-height': '1px',
}

input_text_style = {
    'color': colors['text'],
    'border-color': colors['text'],
    'background-color': colors['button_background'],
    'border-radius': '5px',
    'padding': '0px',
    'line-height': '1px',
}

map_control_label_style = {
    'color': colors['text'],
    'margin-top': '1em',
}

checks_to_do = {
    'naming_convention': False,
    'version': False,
    'pdrf': False,
    'gps_time': False,
    'hor_datum': False,
    'ver_datum': False,
    'point_source_ids': False,
    'create_dz': True,
    'create_hillshade': False,
}


check_result_columns = [
    'naming_convention_passed',
    'version_passed',
    'pdrf_passed',
    'gps_time_passed',
    'hor_datum_passed',
    'ver_datum_passed',
    'point_source_ids_passed',
    'create_dz_passed',
    'create_hillshade_passed',
]


check_labels = {
    'naming_convention': 'Naming Convention',
    'version': 'Version',
    'pdrf': 'Record Type (PDRF)',
    'gps_time': 'GPS Time Type',
    'hor_datum': 'Horizontal Datum',
    'ver_datum': 'Vertical Datum',
    'point_source_ids': 'Point Source IDs',
    'create_dz': 'Dz Ortho Created',
    'create_hillshade': 'Hillshade Ortho Created',
}

check_result_names = {
    'naming_convention': 'naming_convention_passed',
    'version': 'version_passed',
    'pdrf': 'pdrf_passed',
    'gps_time': 'gps_time_passed',
    'hor_datum': 'hor_datum_passed',
    'ver_datum': '',
    'point_source_ids': '',
    'create_dz': '',
    'create_hillshade': '',
}

tabs_styles = {
    'height': '44px',
}

tab_style = {
    'borderBottom': '1px solid #d6d6d6',
    'padding': '6px',
    'fontWeight': 'bold',
    'color': '#373D42',
}

tab_selected_style = {
    'borderTop': '1px solid #d6d6d6',
    'borderBottom': '1px solid #d6d6d6',
    'backgroundColor': '#119DFF',
    'color': 'white',
    'padding': '6px'
}


def get_check_layer_options():
    options = []
    for check in checks_to_do.keys():
        options.append({'label': check_labels[check], 'value': check})

    return options


def gen_text_input(label, placeholder, value):
    return html.Div([html.Div(
                    style={'color': colors['text'], 'margin':0},
                    children=label),
                dcc.Input(
                    style={'margin-bottom': '5px'},
                    placeholder=placeholder,
                    type='text',
                    value=value,
                    className='twelve columns',
                )
            ])


def gen_dir_file_select(label, placeholder):
    return html.Div(
        [
            dcc.Upload(html.A(label)),
            dcc.Input(
                id='contractor-tile-shp',
                style={'margin-bottom': '5px', 'margin-right': '0px'},
                placeholder=placeholder,
                type='text',
                value='',
                className='twelve columns')
         ]
        )


def get_qaqc_settings_tab():
    return html.Div(
        style={
            'textAlign': 'Left',
            'color': colors['header'],
            'height': '90vh',
        },
        children=[

            html.Div([
                html.H4('Project Metadata'),
                gen_text_input('Project ID', 'e.g., MA1601_TB_C', 'MA1601_TB_C'),
                gen_text_input('Contractor Name', 'e.g., Dewberry', 'Dewberry'),
                gen_text_input('UTM Zone', '', '19'),
            ], className='four columns'),

            html.Div([
                html.H4('Directory & File Settings'),
                gen_dir_file_select('QAQC Directory', '...'),
                gen_dir_file_select('QAQC Arc Geodatabase', '...'),
                gen_dir_file_select('Las Tile Directory', '...'),
                gen_dir_file_select('Contractor Tile Shapefile', '...'),
                gen_dir_file_select('Dz Ortho Classification Scheme', 'e.g., .../noaa_topobathy_dz_v01.xml'),
                gen_dir_file_select('Dz Export Settings', '...'),
                gen_dir_file_select('Dz Classes Lyr', '...'),
            ], className='four columns'),

            html.Div([

            ], className='four columns'),

        ], className='row'),


def get_tile_overview_tab():
    return html.Div(style={}, children=[
        html.Div(style={}, children=[

            html.H6(
                style={'color': colors['text'], 'margin':0},
                children='Las Tests'),
            dcc.Graph(
                style={'height': '30vh', 'padding': 0},
                id='pre-check-results',
                figure={
                    'data': [
                        {
                            'x': [340] * 8,
                            'y': range(1,9),
                            'type': 'bar', 'name': 'PASSED', 'orientation': 'h'
                        },
                        {
                            'x': [11] * 8,
                            'y': range(1,9),
                            'type': 'bar', 'name': 'FAILED', 'orientation': 'h'
                        },
                    ],
                    'layout': {
                        'margin': {'l': 150, 'r': 5, 't':0},
                        'xaxis': {
                            'title': 'Number of LAS Files'
                        },
                        'yaxis': {
                            'title': None,
                            'titlefont':{
                                'family': 'Courier New, monospace',
                                'size': 20,
                                'color': colors['text']},
                            'tickvals': range(1, len(checks_to_do.keys())+1),
                            'ticktext': checks_to_do.keys()
                        },
                        'legend': {'orientation': 'h',
                                   'x': 0,
                                   'y': 1.25},
                        'barmode': 'stack',
                        'plot_bgcolor': colors['background'],
                        'paper_bgcolor': colors['background'],
                        'font': {
                            'color': colors['text']
                        },
                    }
                }
            ),

            html.H6(
                style={'color': colors['text'], 'margin':0},
                children='Class Counts'),
            dcc.Graph(
                style={'height': '20vh'},
                id='class-code-hist',
                figure={
                    'data': [
                        {
                            'values': [2,5,12,43,54,7789,3434,34,343,1],
                            'labels': ['{}:{}'.format(c, v) for c, v in
                                       zip([1,2,3,4,25,26,27,44,56,66],
                                           [2,5,12,43,54,7789,3434,34,343,1])],
                            'textinfo': 'none',
                            'hoverinfo': 'label+percent+value',
                            'type': 'pie',
                            'name': 'SF'},
                    ],
                    'layout': {
                        'title': None,
                        'margin': {'l': 150, 'r': 25, 't': 0, 'b':25},
                        'plot_bgcolor': colors['background'],
                        'paper_bgcolor': colors['background'],
                        'font': {
                            'color': colors['text']
                        },
                        'legend': {
                            'x': -25.0,
                            'y': 1.15},
                    }
                }
            ),

            html.H6(
                style={'color': colors['text'], 'margin':0},
                children='Bathymetry Histogram'),
            dcc.Graph(
                style={'height': '25vh'},
                id='depth-hist',
                figure={
                    'data': [
                        {'x': make_bathy_hist_data()[1],
                         'y': make_bathy_hist_data()[0], 'type': 'bar', 'name': 'SF'},
                    ],
                    'layout': {
                        'title': None,
                        'margin': {'l': 150, 'r': 25, 't': 5, 'b':50},
                        'plot_bgcolor': colors['background'],
                        'paper_bgcolor': colors['background'],
                        'font': {
                            'color': colors['text']
                        },
                        'xaxis': {
                            'title': 'Depth (m)',
                            'titlefont':{
                                'family': 'Calibri',
                                'size': 20,
                                'color': colors['text']},
                        },
                        'yaxis': {
                            'title': 'Frquency',
                            'titlefont':{
                                'family': 'Calibri',
                                'size': 20,
                                'color': colors['text']},
                        },
                    }
                }
            )

        ], className='three columns'),

        html.Div([
            dcc.Graph(
                id='qaqc_map',
                style={'height': '90vh'}
            ),
        ], className='seven columns'),

        html.Div(style={'margin-left': '1em'}, children=[

            html.P(
                style=map_control_label_style,
                children='Test Result to Display:'),

            dcc.Dropdown(
                style=map_button_style,
                id='CheckResultLayers',
                options=get_check_layer_options(),
                placeholder='Select a Layer',
                value='version'),

            html.P(
                style=map_control_label_style,
                children='Map Style:'),

            dcc.Dropdown(
                style=map_button_style,
                id='MapStyleSelector',
                options=[
                    {'label': 'streets', 'value': 'streets'},
                    {'label': 'dark', 'value': 'dark'},
                    {'label': 'satellite', 'value': 'satellite'},
                ],
                placeholder='Select a Layer',
                value='dark'),

            html.P(
                style=map_control_label_style,
                children='Select Tiles with FAILED Results:'),

            dcc.Checklist(
                style={
                    'color': colors['text'],
                },
                options=[{'label': v, 'value': k} for k, v in check_labels.iteritems()],
                values=['trajectory']
            ),

            html.P(
                style=map_control_label_style,
                children='Select Tiles with Classes:'),

            dcc.Checklist(
                style={
                    'color': colors['text'],
                },
                options=[{'label': '{}: {}'.format(str(k).zfill(2), v[0]), 'value': v[1]} for k, v in las_classes.iteritems()],
                values=['trajectory']
            )

        ], className='two columns'),

    ], className='row')


html_directory = r'C:\DEV\Tomcat_7081_modified\apache-tomcat-7.0.81\webapps\nick_app'
list_of_htmls = [os.path.basename(x) for x in glob.glob('{}\*.html'.format(html_directory))]
print list_of_htmls
static_image_route = '//127.0.0.1:6080/nick_app/'

# Add a static image route that serves images from desktop
# Be *very* careful here - you don't want to serve arbitrary files
# from your computer or server
@app.server.route('{}<html_path>.html'.format(static_image_route))
def serve_image(html_path):
    html_name = '{}.html'.format(html_path)
    if html_name not in list_of_htmls:
        raise Exception('"{}" is excluded from the allowed static files'.format(html_path))
    return flask.send_from_directory(html_directory, html_name)


def get_tile_point_cloud_tab():
    return html.Div([
                dcc.Dropdown(
                    id='image-dropdown',
                    options=[{'label': i, 'value': i} for i in list_of_htmls],
                    value=list_of_htmls[0],
                    className='row'
                ),
                html.Div([
                    html.Iframe(id='potree', style={'height': '85vh', 'width': '100%'})
                ], className='row'),
            ], className='row')


def get_qaqc_result_table_tab():
    return html.Div([
        generate_table(get_qaqc_df())
    ], className='row')


def get_qaqc_log_tab():
    return html.Div([
        generate_table(get_qaqc_df())
    ], className='row')


app.config['suppress_callback_exceptions']=True
app.layout = html.Div(
    style={'backgroundColor': colors['background']},
    children=[
        html.Div(
            style={'backgroundColor':'#00ADEF'},
            children=[
                html.Div(
                    style={'margin-left': 0},
                    children=[

                        dcc.Tabs(
                            id="tabs-header",
                            value='qaqc_settings-tab',
                            style=tabs_styles,
                            children=[

                                dcc.Tab(
                                    style=tab_style,
                                    selected_style=tab_selected_style,
                                    label='Settings',
                                    value='qaqc_settings-tab'),

                                dcc.Tab(
                                    style=tab_style,
                                    selected_style=tab_selected_style,
                                    label='Graphs & Map',
                                    value='tile-overview-tab'),

                                dcc.Tab(
                                    style=tab_style,
                                    selected_style=tab_selected_style,
                                    label='Point Clouds',
                                    value='tile-point-cloud-tab'),

                                dcc.Tab(
                                    style=tab_style,
                                    selected_style=tab_selected_style,
                                    label='Query Table',
                                    value='qaqc-results-table-tab'),

                                dcc.Tab(
                                    style=tab_style,
                                    selected_style=tab_selected_style,
                                    label='Log',
                                    value='qaqc-log-tab'),

                            ], className='twelve columns'),

                    ], className='twelve columns'),

            ], className='row'),

        html.Div(id='tabs-content', className='row')

    ], className='no gutters')

@app.callback(
    dash.dependencies.Output('potree', 'src'),
    [dash.dependencies.Input('image-dropdown', 'value')])
def update_html_src(value):
    return static_image_route + value


#@app.callback(dash.dependencies.Output('tabs-content', 'children'),
#              [dash.dependencies.Input('tabs-header', 'value')])
#def update_selected_rows_indices():
#    map_aux = get_tiles_df().copy()

#    rows = map_aux.to_dict('records')
#    return rows

@app.callback(
    dash.dependencies.Output('qaqc-table-container', "children"),
    [dash.dependencies.Input('qaqc-table', "data")])
def update_graph(rows):
    if rows is None:
        dff = df
    else:
        dff = pd.DataFrame(rows)

    return html.Div()


@app.callback(dash.dependencies.Output('tabs-content', 'children'),
              [dash.dependencies.Input('tabs-header', 'value')])
def render_content(tab):
    if tab == 'qaqc_settings-tab':
        return get_qaqc_settings_tab()
    elif tab == 'tile-overview-tab':
        return get_tile_overview_tab()
    elif tab == 'tile-point-cloud-tab':
        return get_tile_point_cloud_tab()
    elif tab == 'qaqc-results-table-tab':
        return get_qaqc_result_table_tab()
    elif tab == 'qaqc-log-tab':
        return get_qaqc_log_tab()


@app.callback(
    dash.dependencies.Output('qaqc_map', 'figure'),
    [dash.dependencies.Input('CheckResultLayers', 'value'),
     dash.dependencies.Input('MapStyleSelector', 'value')])
def update_map_layer(input1, input2):
    print input1, input2
    figure=get_qaqc_map(check_labels[input1],
                        check_result_names[input1],
                        input2,
                        get_contract_tile_csv(),
                        get_qaqc_results_csv())

    return figure


if __name__ == '__main__':

    app.run_server(debug=True)  # port=6080, 