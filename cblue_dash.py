import dash
import dash_core_components as dcc
import dash_html_components as html

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


colors = {
    'background': '#373D42',
    'text': '#B1C4D2',
    'header': '#0968AA',
    'button_background': '#75777a',
    'pass_green': '#3D9970',
    'fail_red': '#ff4d4d'
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


def gen_dir_file_select(label, placeholder):
    return html.Div(
        [
            dcc.Upload(html.A(label)),
            dcc.Input(
                id=label.replace(' ', '-'),
                style={'margin-bottom': '5px', 'margin-right': '0px'},
                placeholder=placeholder,
                type='text',
                value='',
                className='twelve columns')
        ]
    )


def get_settings_tab():
    return html.Div(

        style={
            'textAlign': 'Left',
            'color': colors['header'],
            'height': '90vh',
        },

        children=[
            html.Div([
                html.H6('Directories'),
                gen_dir_file_select('Trajectory Files', '...'),
                gen_dir_file_select('Las Files', '...'),
                gen_dir_file_select('Output', '...'),
            ], className='four columns'),
            html.Div([
                html.H6('Environmental Parameters'),

            ], className='four columns'),
        ], className='row'),


def get_map_tab():
    return html.Div(

        style={
            'textAlign': 'Left',
            'color': colors['header'],
            'height': '90vh',
        },

        children=[
            html.Div([
                html.H6('Directories'),
                gen_dir_file_select('Trajectory Files', '...'),
                gen_dir_file_select('Las Files', '...'),
                gen_dir_file_select('Output', '...'),
            ], className='four columns'),
        ], className='row'),


def get_results_tab():
    return html.Div(

        style={
            'textAlign': 'Left',
            'color': colors['header'],
            'height': '90vh',
        },

        children=[
            html.Div([
                html.H6('Directories'),
                gen_dir_file_select('Trajectory Files', '...'),
                gen_dir_file_select('Las Files', '...'),
                gen_dir_file_select('Output', '...'),
            ], className='four columns'),
        ], className='row'),


tab_ids = {
    'Settings': 'settings-tab',
    'Map': 'map-tab',
    'Results': 'results-tab',
}

tab_contents = {
    'settings-tab': get_settings_tab(),
    'map-tab': get_map_tab(),
    'results-tab': get_results_tab(),
}

app.layout = html.Div(
    style={'backgroundColor': colors['background']},
    children=[
        html.Div(
            style={'backgroundColor': colors['background']},
            children=[
                html.Div(
                    style={'margin-left': 0},
                    children=[
                        dcc.Tabs(
                            id="tabs-header",
                            value=list(tab_ids.values())[0],
                            style=tabs_styles,
                            children=[
                                dcc.Tab(
                                    style=tab_style,
                                    selected_style=tab_selected_style,
                                    label=label,
                                    value=value)
                                for label, value in tab_ids.items()],
                            className='twelve columns'),
                    ], className='nine columns'),
            ], className='row'),
        html.Div(id='tabs-content', className='row')
    ], className='no gutters')


@app.callback(dash.dependencies.Output('tabs-content', 'children'),
              [dash.dependencies.Input('tabs-header', 'value')])
def render_content(tab):
    return tab_contents[tab]


if __name__ == '__main__':
    app.run_server(debug=True)
