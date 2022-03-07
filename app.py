from dash import Dash, html, dcc, Input, Output, dash_table, State
import plotly.express as px
import pandas as pd
import base64
import pymongo
import json

from scrapy_controller import crawl

db = \
    pymongo.MongoClient('mongodb+srv://user:uzrJlKmF3AugY6dG@cluster0.770v5.mongodb.net')[
        'AMAZON']

df = pd.DataFrame(db.products.find({}))
category_count_df = df.groupby('category').size().sort_values(ascending=False)
category_price_df = df.groupby('category', dropna=True)['price'].mean().sort_values(
    ascending=False)

category_brand_df = df.groupby(['category', 'brand']).size()
category_brand__price_df = df.groupby(['category', 'brand'], dropna=True)['price'].mean()

app = Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width"}, ]
    , external_stylesheets=['https://fonts.googleapis.com/css2?family=Open+Sans']
)
app.css.config.serve_locally = True
app.title = "Dashboard Amazon"


def DataValue(value, text):
    return html.Div(
        className='general_information__item',
        children=[
            html.Div(
                value,
                className='value'
            ),
            html.Div(
                text,
                className='label'
            )
        ]
    )


app.layout = html.Div(
    className='page_content',
    children=[
        Header := html.Header([
            html.Img(src='assets/icon.svg', className='icon'),
            html.H1('AMAZON PRODUCT DASHBOARD'),
        ]),
        html.Div(
            [
                html.Div([
                    html.H2('Crawl Data from Amazon Websites'),
                    html.Label('Crawling Mode :'),
                    TypeCrawl := dcc.RadioItems(['Category', 'Product', 'Comment'],
                                                'Category', inline=True),
                    html.Label('Page Number Limit :'),
                    PageLimit := dcc.Input(value=1, type='number', style={
                        'line-height': '2em',
                        'text-align': 'center'
                    }),
                    html.Label('Crawl URL:'),
                    URL_INPUT := dcc.Textarea(style={'height': '100'}),
                    html.Div([
                        Upload := dcc.Upload(
                            id='upload-data',
                            children=html.Div([
                                'Drag and Drop or ',
                                html.A('Select Files')
                            ]),
                            className='upload_box'
                        ),
                        UploadedFile := html.Div(),
                    ]),
                    CrawlBtn := html.Button('Start Crawl', className='crawl_btn'),
                    dcc.Loading(children=[
                        Download := dcc.Download(),
                    ],
                        fullscreen=True)
                ], className='left_side__content')
            ],
            className='left_side'
        )
        , html.Div(
            className='right_side',
            children=[
                GeneralInformation := html.Div(
                    className='general_information',
                    children=[
                        DataValue(num_product := df.shape[0],
                                  'products crawl on database'),
                        DataValue(num_brands := df['brand'].nunique(),
                                  'number of brands on database'),
                        DataValue(df['category'].nunique(),
                                  'number of category on database')
                    ]
                ),
                CategoryBarCharts := html.Div(
                    className='content_box',
                    children=[
                        html.Div([
                            html.H3('Top Category'),
                            CategoryListSlider := dcc.Slider(
                                min=0, max=df['category'].nunique(), value=20,
                                tooltip={"placement": "bottom", "always_visible": True},
                                className='slider'
                            ),
                        ], className='content_box__header'),
                        html.Div([
                            CategoryBarContent := dcc.Graph(style={'flex': 1}),
                            CategoryTabs := dcc.Tabs(
                                [
                                    dcc.Tab(label='Number Products', value='count'),
                                    dcc.Tab(label='Price Mean', value='price')
                                ], value='count', vertical=True
                            ),
                        ], className='content_box__body--category')
                    ],
                )
                ,
                CategoryBrandGroup := html.Div(
                    className="content_box",
                    children=[
                        html.Div(
                            children=[
                                html.H3('Compare Brands between Category'),
                                CategoryDropdown := dcc.Dropdown(
                                    category_list := category_count_df.index,
                                    value=category_list[0]
                                ),
                            ], className='content_box__header compare_brand'
                        ),
                        CategoryBrandPriceBarChart := dcc.Graph(),
                        CategoryBrandPieChart := dcc.Graph(),
                    ]
                ),
                ProductTableGroup := html.Div(
                    className="content_box content_box--table",
                    children=[
                        html.H2('Products Table'),
                        html.Label('Filter By Category'),
                        CategoryFilter := dcc.Dropdown(
                            options=df['category'].unique(),
                            value=['Tablets'],
                            multi=True
                        ),
                        html.Label('Filter By Brand'),
                        BrandFilter := dcc.Dropdown(
                            options=df['brand'].unique(),
                            multi=True
                        ),
                        ProductTable := dash_table.DataTable(
                            page_size=20,
                            style_cell={
                                'overflow': 'hidden',
                                'textOverflow': 'ellipsis',
                                'maxWidth': 0,
                                'textAlign': 'center'
                            },
                            tooltip_duration=None,
                            style_cell_conditional=[
                                {
                                    'if': {'column_id': 'title'},
                                    'width': '40%'
                                },
                            ],
                        )
                    ]
                ),
                ProductReviewFilter := html.Div(
                    className="content_box content_box--table",
                    children=[
                        html.H2('Review Table'),
                        html.Div(children=[
                            html.Label('Search product review by ASIN'),
                            ASIN_INPUT := dcc.Input(type='text'),
                            SummitBtn := html.Button('Submit')
                        ], style={
                            'display': 'flex',
                            'justifyContent': 'space-between'
                        }),
                        dcc.Loading([
                            ReviewPieChart := html.Div(),
                            Review := dash_table.DataTable(
                                style_cell={
                                    'overflow': 'hidden',
                                    'textOverflow': 'ellipsis',
                                    'maxWidth': 0,
                                    'textAlign': 'center'
                                },
                                tooltip_duration=None,
                                style_cell_conditional=[
                                    {
                                        'if': {'column_id': 'summary'},
                                        'width': '40%'
                                    },
                                ],
                                sort_action='native'
                            )
                        ]),
                    ]
                )
            ]),
    ]
)


@app.callback(
    Output(UploadedFile, 'children'),
    Input(Upload, 'filename')
)
def upload_file(name):
    return name


@app.callback(
    Output(Download, "data"),
    Input(CrawlBtn, "n_clicks"),
    State(PageLimit, 'value'),
    State(TypeCrawl, 'value'),
    State(URL_INPUT, 'value'),
    State(Upload, 'contents'),
    prevent_initial_call=True,
)
def start_crawl(click, limit, type, urls, contents):
    if contents:
        data = base64.b64decode(contents.split(',')[1])
        urls = data.decode().split('\n')
    else:
        urls = [urls]

    result = crawl(type, limit, urls)
    return dict(content=json.dumps(result), filename='type.json')


@app.callback(
    Output(CategoryBarContent, 'figure'),
    Input(CategoryTabs, 'value'),
    Input(CategoryListSlider, 'value'),
)
def update_category_bar(type, value):
    fig = {}

    if type == 'count':
        fig = px.bar(category_count_df[:value], text_auto=True, height=600
                     )
        fig.update_layout(yaxis_title="Number of Products")
        fig.update_traces(textangle=0, textposition="outside", cliponaxis=False)
    elif type == 'price':
        fig = px.bar(category_price_df[:value], text_auto=True,
                     )

        fig.update_layout(yaxis_title="Price Average")
        fig.update_traces(marker_color='indianred', textangle=0, textposition="outside",
                          cliponaxis=False)

    return fig


@app.callback(
    Output(CategoryBrandPieChart, 'figure'),
    Output(CategoryBrandPriceBarChart, 'figure'),
    Input(CategoryDropdown, 'value')
)
def update_category_brand(category):
    top_10 = category_brand_df[category].sort_values(ascending=False)[:10]

    pie = px.pie(
        top_10.to_frame(name='number_of_products').reset_index(),
        values='number_of_products', names='brand')
    pie.update_layout(title="Number of Products of Brands in Category")
    pie.update_traces(textinfo='label+value')

    bar = px.bar(
        category_brand__price_df.loc[category, top_10.index].to_frame().reset_index(1)
        , x='brand', y='price', text_auto=True)

    bar.update_layout(yaxis_title="Price Average")
    bar.update_traces(marker_color='indianred', textangle=0, textposition="outside",
                      cliponaxis=False)
    return pie, bar


@app.callback(
    Output(BrandFilter, 'options'),
    Input(CategoryFilter, 'value')
)
def update_brand_options(categories):
    return df[df['category'].isin(categories)]['brand'].unique()


columns = ['asin', 'category', 'title', 'brand', 'price', 'stars_1', 'stars_2', 'stars_3',
           'stars_4', 'stars_5']


@app.callback(
    Output(ProductTable, 'data'),
    Output(ProductTable, 'tooltip_data'),
    Input(CategoryFilter, 'value'),
    Input(BrandFilter, 'value')
)
def update_table_filter(categories, brands):
    if brands:
        raw_data = df[df['category'].isin(categories) & (df['brand'].isin(brands))]
    else:
        raw_data = df[df['category'].isin(categories)]

    table_data = raw_data[columns].to_dict('records')
    tooltip_data = [
        {
            column: {'value': str(value), 'type': 'markdown'}
            for column, value in row.items()
        } for row in table_data
    ]

    return table_data, tooltip_data


@app.callback(
    Output(Review, 'data'),
    Output(Review, 'tooltip_data'),
    Output(ReviewPieChart, 'children'),
    Input(SummitBtn, 'n_clicks'),
    State(ASIN_INPUT, 'value'),
    prevent_initial_call=True
)
def get_review(_, asin):
    query = db.reviews.find({'asin': asin}, projection={
        '_id': False, 'asin': False
    })

    data = list(query)

    tooltip_data = [
        {
            column: {'value': str(value), 'type': 'markdown'}
            for column, value in row.items()
        } for row in data
    ]

    ratings = df.loc[df['asin'] == asin][
        ['stars_5', 'stars_4', 'stars_3', 'stars_2', 'stars_1']].T

    ratings.columns = ['count']

    fig = px.pie(ratings.reset_index(), values='count', names='index',
                 color_discrete_sequence=px.colors.sequential.RdBu)
    fig.update_layout(title="Product Review Rating Percentages")
    fig.update_traces(textinfo='label+percent')

    graph = dcc.Graph(figure=fig)
    return data, tooltip_data, graph


if __name__ == '__main__':
    app.run_server()
