#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#%% Package Imports

import numpy as np
import pandas as pd
import pickle
from scipy import stats as st
import copy

from bokeh.layouts import (
    row, 
    column,
    Spacer,
    widgetbox
    )
from bokeh.models import (
    ColumnDataSource,
    BoxSelectTool, 
    LassoSelectTool,
    HoverTool,
    Select,
    PreText,
    MultiSelect
    )
from bokeh.plotting import (
    figure, 
    curdoc,
    )

#%% Load Static Map Datasource

map_path = "/Users/edf/Repositories/EnergyAtlas/JointPlot/data/pkl/map_source.pkl"
map_source = pickle.load(open(map_path,"rb")) 

#%% Load Scatter Plot Dependenant Variable Fits 

yhat_path = "/Users/edf/Repositories/EnergyAtlas/JointPlot/data/pkl/yhat.pkl"
yhat_source = pd.read_pickle(yhat_path)

#%% Load Scatter Plot Independent Variable Values

xp_path = "/Users/edf/Repositories/EnergyAtlas/JointPlot/data/pkl/xp.pkl"
xp_source = pd.read_pickle(xp_path)

#%% Create Reference Data Frame

ref_path = "/Users/edf/Repositories/EnergyAtlas/JointPlot/data/pkl/input_table_medium.pkl"
df = pd.read_pickle(ref_path)

#%% Create Axis Map

axis_map = {
    "Energy Consumption [MBTU]": "consumption",
    "Building Size [sq.ft.]": "size",
    "Energy Consumption Intensity [MBTU / sq.ft.]" : "intensity",
    "Construction Vintage [Year]" : "year"
}

#%% Create Plot Columnar Data Source

plot_source = ColumnDataSource(data=dict(
    x = [],
    y = []
))

#%% Create Stats Widget

stats = PreText(text=str(df.describe()), width=700)

#%% Create Mult-Select Widget

nm = np.unique(df['name'])
menu = list(zip(nm,nm))
del menu[0:2]
multi_select = MultiSelect(title='Select City:', value=[], options=menu[3:],
                           height=150)

#%% Create Map Plot

def create_map(map_source):
    
    MAP_TOOLS="pan,wheel_zoom,hover,save,reset"
    
    m = figure(title="Los Angeles County Neighborhoods", tools=MAP_TOOLS, 
               plot_width=800, plot_height=1000, min_border=50, 
               x_axis_location="above", y_axis_location="left",webgl=True,
               toolbar_location="below")
    m.background_fill_color = "#fafafa"
    m.xaxis.major_label_orientation = np.pi/4
    m.yaxis.axis_label = "Latitude [DD]"
    m.xaxis.axis_label = "Longitude [DD]"
    m.patches('lon','lat', source=map_source,
              fill_color='color',
              fill_alpha='alpha',
              line_color='#3A5785', line_width=0.5)     
    hover = m.select_one(HoverTool)
    hover.point_policy = "follow_mouse"
    hover.tooltips = [
        ("Neighborhood Name", "@name"),
        ("Total Megaparcel Count [Megaparcels]", "@count"),
        ("Mean Square Footage Per Megaparcel [sq.ft.]", "@avg_sqft"),
        ("Mean Annual Energy Consumption [MBTU / Megaparcel]", "@avg_consumption"),
        ("Mean Annual Energy Consumption Intensity [MBTU / sq.ft.]", "@avg_intensity")
    ]

    return m

#%% Create Scatter Plot

def create_scatter(plot_source):

    PLOT_TOOLS="pan,wheel_zoom,box_zoom,box_select,lasso_select,save,reset"
    
    p = figure(tools=PLOT_TOOLS, plot_width=700, plot_height=700, 
               min_border=50, min_border_left=50, toolbar_location="below", 
               x_axis_location="above", y_axis_location="left", 
               title="Pairwise Scatterplot", webgl=True)        
    p.background_fill_color = "#fafafa"
    p.xaxis.major_label_orientation = np.pi/4
    p.yaxis.axis_label = y_axis.value
    p.xaxis.axis_label = x_axis.value
    p.select(BoxSelectTool).select_every_mousemove = False
    p.select(LassoSelectTool).select_every_mousemove = False  
    r = p.circle('x', 'y', source=plot_source, size=3, color="#3A5785", alpha=1.0, 
             selection_color="orange", nonselection_alpha=1.0, 
             selection_alpha=1.0)
    
    return p, r
    
#%% Create Y axis histogram

def create_x_histogram(plot_source):
    
    HIST_TOOLS="pan,wheel_zoom,box_zoom,save,reset"
        
    xhist0, xedges0 = np.histogram(np.array(plot_source.data['x']), bins=20)
    px = figure(tools=HIST_TOOLS, toolbar_location='left', plot_width=700, 
                plot_height=300, min_border=50, title="X-Axis Histogram",
                y_axis_location='right', x_axis_location="below",
                webgl=True)
    px.background_fill_color = "#fafafa"
    px.xaxis.major_label_orientation = np.pi/4
    px.xaxis.axis_label = x_axis.value
    px.yaxis.axis_label = 'Frequency Count'
    xh = px.quad(bottom=0, left=xedges0[:-1], right=xedges0[1:], top=xhist0, 
            color="white", line_color="#3A5785")
    
    return px, xh
    
#%% Create Y axis histogram

def create_y_histogram(plot_source):
    
    HIST_TOOLS="pan,wheel_zoom,box_zoom,save,reset"
    
    yhist0, yedges0 = np.histogram(np.array(plot_source.data['y']), bins=20)
    py = figure(tools=HIST_TOOLS, toolbar_location='above', plot_width=300, 
                plot_height=700, min_border=50, title="Y-Axis Histogram",
                y_axis_location="right", x_axis_location='below',
                webgl=True)     
    py.background_fill_color = "#fafafa"
    py.xaxis.major_label_orientation = np.pi/4
    py.xaxis.axis_label = 'Frequency Count' 
    py.yaxis.axis_label = y_axis.value
    yh = py.quad(left=0, bottom=yedges0[:-1], top=yedges0[1:], right=yhist0, 
            color="white", line_color="#3A5785")
    
    return py, yh
    
#%% Update X axis
    
def update_x_axis(attr, old, new):
    
    p.xaxis.axis_label = x_axis.value
    px.xaxis.axis_label = x_axis.value
    plot_source.data['x'] = df[axis_map[new]].values
    xhist0, xedges0 = np.histogram(np.array(plot_source.data['x']), bins=20)  
    xh.data_source.data['right'] = xedges0[1:]
    xh.data_source.data['left'] = xedges0[:-1]
    xh.data_source.data['top'] = xhist0  

#%% Update Y axis

def update_y_axis(attr, old, new):
    
    p.yaxis.axis_label = y_axis.value
    py.yaxis.axis_label = y_axis.value
    plot_source.data['y'] = df[axis_map[new]].values
    yhist0, yedges0 = np.histogram(np.array(plot_source.data['y']), bins=20)  
    yh.data_source.data['top'] = yedges0[1:]
    yh.data_source.data['bottom'] = yedges0[:-1]
    yh.data_source.data['right'] = yhist0  
    
#%% Update Stats Panel Widget

def update_stats(inds):
        
    if len(inds) == 0 or len(inds) == len(df['size'].values):
        stats.text = str(df.describe())
    else:
        stats.text = str(df.ix[inds].describe())
        
#%% Update Map

def update_map(inds):
            
    if len(inds) == 0 or len(inds) == len(df['size'].values):
#        map_source.data['lon'] = neighborhood_lon
#        map_source.data['lat'] = neighborhood_lat
#        map_source.data['avg_consumption'] = neighborhood_avg
#        map_source.data['name'] = neighborhood_names
        map_source.data['color'] = np.asarray(["white"]*len(map_source.data['name']), dtype=object)
    else:
        color = np.asarray(["white"]*len(map_source.data['name']), dtype=object)
        alpha = np.asarray([1.0]*len(map_source.data['name']))
        cur_names, cur_counts = np.unique(np.array(df['name'][inds]), return_counts=True)
        map_inds = np.in1d(map_source.data['name'], cur_names)
        ranks = st.rankdata(cur_counts, "average")/len(cur_counts)
        color[map_inds] = 'orange'
        alpha[np.where(map_inds)] = ranks
        map_source.data['color'] = color
        map_source.data['alpha'] = alpha
    
#%% Update Selection    
    
def update_plot_selection(attr, old, new):
    
    inds = np.array(new['1d']['indices'], dtype=int)
    update_stats(inds)
    update_map(inds)
    
    return inds
    
#%% Update Map Selection    
      
def update_map_selection(attr, old, new):
    
    inds = np.in1d(df['name'], np.array(new)).nonzero()[0]
    selection_copy = copy.copy(plot_source.selected)
    selection_copy['1d']['indices'] = inds
    plot_source.selected = selection_copy

    # There seems to be a delay between when the selection is made and when it
    # is rendered...
    
    return inds
    
#%% Update Plot Source Data

def update_data():
    
    plot_source.data['x'] = df[axis_map[x_axis.value]].values
    plot_source.data['y'] = df[axis_map[y_axis.value]].values
        
#%% Create Axes Selector Widgets

x_axis = Select(title='X-Axis', value='Building Size [sq.ft.]', 
                options=sorted(axis_map.keys()))
y_axis = Select(title='Y-Axis', value='Energy Consumption [MBTU]', 
                options=sorted(axis_map.keys()))

#%% Generate Plot Variables

inds = np.asarray([], dtype=int)
update_data()
p, r = create_scatter(plot_source)
px, xh = create_x_histogram(plot_source)
py, yh = create_y_histogram(plot_source)
m = create_map(map_source)

#%% Generate Layout

sizing_mode = 'fixed'
widgets = widgetbox([x_axis, y_axis], sizing_mode=sizing_mode)
layout = row(column(row(widgets, Spacer(width=50), stats), 
                    column(row(p, py), row(px, Spacer(width=300,height=300)))), 
                    column(multi_select, m))
curdoc().add_root(layout)
curdoc().title = "Selection Histogram"

x_axis.on_change('value', update_x_axis)
y_axis.on_change('value', update_y_axis)
multi_select.on_change('value', update_map_selection)
plot_source.on_change('selected', update_plot_selection)
