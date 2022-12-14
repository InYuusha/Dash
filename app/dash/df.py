import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import base64
import json
import os
import matplotlib.cm
import matplotlib.colors as mcolors
import numpy as np
import random
import plotly.graph_objects as go
import plotly.express as px
from skimage import data, transform


COLORMAP = 'plasma'
KEYPOINTS = ['Nose', 'L_Eye', 'R_Eye', 'L_Ear', 'R_Ear', 'Throat',
             'Withers', 'TailSet', 'L_F_Paw', 'R_F_Paw', 'L_F_Wrist',
             'R_F_Wrist', 'L_F_Elbow', 'R_F_Elbow', 'L_B_Paw', 'R_B_Paw',
             'L_B_Hock', 'R_B_Hock', 'L_B_Stiffle', 'R_B_Stiffle']
N_SUBSET = 3

img = data.chelsea()
img = img[::2, ::2]
images = [img, img[::-1], transform.rotate(img, 30)]
cmap = matplotlib.cm.get_cmap(COLORMAP, N_SUBSET)


def make_figure_image(i):
    fig = px.imshow(images[i % len(images)])
    fig.layout.xaxis.showticklabels = False
    fig.layout.yaxis.showticklabels = False
    fig.update_traces(hoverinfo='none', hovertemplate='')
    return fig


def draw_circle(center, radius, n_points=50):
    pts = np.linspace(0, 2 * np.pi, n_points)
    x = center[0] + radius * np.cos(pts)
    y = center[1] + radius * np.sin(pts)
    path = 'M ' + str(x[0]) + ',' + str(y[1])
    for k in range(1, x.shape[0]):
        path += ' L ' + str(x[k]) + ',' + str(y[k])
    path += ' Z'
    print(path)
    return path


def compute_circle_center(path):
    """
    See Eqn 1 & 2 pp.12-13 in REGRESSIONS CONIQUES, QUADRIQUES
    Régressions linéaires et apparentées, circulaire, sphérique
    Jacquelin J., 2009.
    """
    coords = [list(map(float, coords.split(','))) for coords in path.split(' ')[1::2]]
    x, y = np.array(coords).T
    n = len(x)
    sum_x = np.sum(x)
    sum_y = np.sum(y)
    sum_x2 = np.sum(x * x)
    sum_y2 = np.sum(y * y)
    delta11 = n * np.dot(x, y) - sum_x * sum_y
    delta20 = n * sum_x2 - sum_x ** 2
    delta02 = n * sum_y2 - sum_y ** 2
    delta30 = n * np.sum(x ** 3) - sum_x2 * sum_x
    delta03 = n * np.sum(y ** 3) - sum_y * sum_y2
    delta21 = n * np.sum(x * x * y) - sum_x2 * sum_y
    delta12 = n * np.sum(x * y * y) - sum_x * sum_y2

    # Eqn 2, p.13
    num_a = (delta30 + delta12) * delta02 - (delta03 + delta21) * delta11
    num_b = (delta03 + delta21) * delta20 - (delta30 + delta12) * delta11
    den = 2 * (delta20 * delta02 - delta11 * delta11)
    a = num_a / den
    b = num_b / den
    return a, b


def get_plotly_color(n):
    return mcolors.to_hex(cmap(n))


def create_dash(server):
    fig = make_figure_image(0)

    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

    app = dash.Dash(
        __name__, 
        external_stylesheets=external_stylesheets,
        server= server,
        url_base_pathname = "/dash/",
        meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
    )
    

    options = random.sample(KEYPOINTS, N_SUBSET)

    styles = {
        'pre': {
            'border': 'thin lightgrey solid',
            'overflowX': 'scroll'
        },
        
    }

    app.layout = html.Div([
        html.Div([
            dcc.Graph(
                id='canvas',
                config={'editable': True},
                figure=fig)
        ],
            className="six columns"
        ),
        html.A(html.Button('Logout'),
            href='/logout'),
        
        html.Div([
            html.H2("Controls"),
            dcc.RadioItems(id='radio',
                            options=[{'label': opt, 'value': opt} for opt in options],
                            value=options[0]
                        ),
            html.Button('Previous', id='previous'),
            html.Button('Next', id='next'),
            html.Button('Clear', id='clear'),
            html.Button('Save', id='save'),
            dcc.Store(id='store', data=0),
            html.P([
                html.Label('Keypoint label size'),
                dcc.Slider(id='slider',
                        min=3,
                        max=36,
                        step=1,
                        value=12)
                ], style={'width': '80%',
                        'display': 'inline-block'})
        ],
            className="six columns"
        ),
        html.Div([
            dcc.Markdown("""
                    **Instructions**\n
                    Click on the image to add a keypoint.
                """),
            html.Pre(id='click-data', style=styles['pre']),
        ],
            className='six columns'
        ),
        html.Div(id='placeholder', style={'display': 'none'}),
        html.Div(id='shapes', style={'display': 'none'})
    ],
    )


    @app.callback(Output('placeholder', 'children'),
                [Input('save', 'n_clicks')],
                [State('store', 'data')])
    def save_data(click_s, ind_image):
        if click_s:
            xy = {shape.name: compute_circle_center(shape.path) for shape in fig.layout.shapes}
            print(xy, ind_image)


    @app.callback(
        [Output('canvas', 'figure'),
        Output('radio', 'value'),
        Output('store', 'data'),
        Output('shapes', 'children')],
        [Input('canvas', 'clickData'),
        Input('canvas', 'relayoutData'),
        Input('next', 'n_clicks'),
        Input('previous', 'n_clicks'),
        Input('clear', 'n_clicks'),
        Input('slider', 'value')],
        [State('canvas', 'figure'),
        State('radio', 'value'),
        State('store', 'data'),
        State('shapes', 'children')]
        )
    def update_image(clickData, relayoutData, click_n, click_p, click_c, slider_val,
                 figure, option, ind_image, shapes):
        if not any(event for event in (clickData, click_n, click_p, click_c)):
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update

        if ind_image is None:
            ind_image = 0

        if shapes is None:
            shapes = []
        else:
            shapes = json.loads(shapes)
        n_bpt = options.index(option)

        ctx = dash.callback_context
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == 'clear':
            fig.layout.shapes = []
            return make_figure_image(ind_image), options[0], ind_image, '[]'
        elif button_id == 'next':
            ind_image = (ind_image + 1) % len(images)
            return make_figure_image(ind_image), options[0], ind_image, '[]'
        elif button_id == 'previous':
            ind_image = (ind_image - 1) % len(images)
            return make_figure_image(ind_image), options[0], ind_image, '[]'
        elif button_id == 'slider':
            for i in range(len(shapes)):
                center = compute_circle_center(shapes[i]['path'])
                new_path = draw_circle(center, slider_val)
                shapes[i]['path'] = new_path

        already_labeled = [shape['name'] for shape in shapes]
        key = list(relayoutData)[0]
        if option not in already_labeled and button_id != 'slider':
            if clickData:
                x, y = clickData['points'][0]['x'], clickData['points'][0]['y']
                circle = draw_circle((x, y), slider_val)
                color = get_plotly_color(n_bpt)
                shape = dict(type='path',
                            path=circle,
                            line_color=color,
                            fillcolor=color,
                            layer='above',
                            opacity=0.8,
                            name=option)
                shapes.append(shape)
        else:
            if 'path' in key and button_id != 'slider':
                ind_moving = int(key.split('[')[1].split(']')[0])
                path = relayoutData.pop(key)
                shapes[ind_moving]['path'] = path
        fig.update_layout(shapes=shapes)
        if 'range[' in key:
            xrange = relayoutData['xaxis.range[0]'], relayoutData['xaxis.range[1]']
            yrange = relayoutData['yaxis.range[0]'], relayoutData['yaxis.range[1]']
            fig.update_xaxes(range=xrange, autorange=False)
            fig.update_yaxes(range=yrange, autorange=False)
        elif 'autorange' in key:
            fig.update_xaxes(autorange=True)
            fig.update_yaxes(autorange=True)
        if button_id != 'slider':
            n_bpt += 1
        new_option = options[min(len(options) - 1, n_bpt)]
        return ({'data': figure['data'], 'layout': fig['layout']},
                new_option,
                ind_image,
                json.dumps(shapes))

    
    return app;
