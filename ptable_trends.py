from __future__ import absolute_import
from bokeh.models import (ColumnDataSource, LinearColorMapper, LogColorMapper, 
	ColorBar, BasicTicker)
from bokeh.plotting import figure
from bokeh.io import output_file, show
from bokeh.sampledata.periodic_table import elements
from bokeh.transform import dodge
from csv import reader
from matplotlib.colors import Normalize, LogNorm, to_hex
from matplotlib.cm import plasma, inferno, magma, viridis, ScalarMappable
from pandas import options
import argparse
options.mode.chained_assignment = None

output_file('ptable_trends.html')

#Parse arguments
parser = argparse.ArgumentParser(description='Plot periodic trends as a heat '
	'map over the periodic table of elements')
parser.add_argument('filename',type=str,help='Filename (with extension) of '
	'CSV-formatted data')
parser.add_argument('--width',type=int,default=1050,help='Width (in pixels) of '
	'figure')
parser.add_argument('--cmap_choice',type=int,default=0,choices=range(0,4),
	help='Color palette choice: 0 = Plasma, 1 = Inferno, 2 = Magma, 3 = Viridis')
parser.add_argument('--alpha',type=float,default=0.65,help='Alpha value '
	'for color scale (ranges from 0 to 1)')
parser.add_argument('--log_scale',type=int,default=0,choices=range(0,2),
	help='Keyword for linear (0) or logarithmic (1) color bar')
parser.add_argument('--cbar_height',type=int,help='Height (in pixels) of color '
	'bar')

args = parser.parse_args()
filename = args.filename
width = args.width
cmap_choice = args.cmap_choice
alpha = args.alpha
log_scale = args.log_scale
cbar_height = args.cbar_height

#Error handling
if width < 0:
	raise argparse.ArgumentTypeError('--width must be a positive integer')
if alpha < 0 or alpha > 1:
	raise argparse.ArgumentTypeError('--alpha must be between 0 and 1')
if cbar_height is not None and cbar_height < 0:
	raise argparse.ArgumentTypeError('--cbar_height must be a positive integer')

#Assign color palette based on input argument
if cmap_choice == 0:
	cmap = plasma
	bokeh_palette = 'Plasma256'
elif cmap_choice == 1:
	cmap = inferno
	bokeh_palette = 'Inferno256'
elif cmap_choice == 2:
	cmap = magma
	bokeh_palette = 'Magma256'
elif cmap_choice == 3:
	cmap = viridis
	bokeh_palette = 'Viridis256'
	
#Define number of and groups
period_label = ['1', '2', '3', '4', '5', '6', '7']
group_range = [str(x) for x in range(1, 19)]

#Read in data from CSV file
data_elements = []
data_list = []
for row in reader(open(filename)):
	data_elements.append(row[0])
	data_list.append(row[1])
data = [float(i) for i in data_list]

if len(data) != len(data_elements):
	raise ValueError('Unequal number of atomic elements and data points')

period_label.append('blank')
period_label.append('La')
period_label.append('Ac')

count = 0
for i in range(56,70):
    elements.period[i] = 'La'
    elements.group[i] = str(count+4)
    count += 1

count = 0
for i in range(88,102):
    elements.period[i] = 'Ac'
    elements.group[i] = str(count+4)
    count += 1

#Define matplotlib and bokeh color map
if log_scale == 0:
	color_mapper = LinearColorMapper(palette = bokeh_palette, low=min(data), 
		high=max(data))
	norm = Normalize(vmin = min(data), vmax = max(data))
elif log_scale == 1:
	for data_element in data_elements:
		if data_element < 0:
			raise ValueError('Entry for element '+data_element+' is negative but'
			' log-scale is selected')
	color_mapper = LogColorMapper(palette = bokeh_palette, low=min(data), 
		high=max(data))
	norm = LogNorm(vmin = min(data), vmax = max(data))
color_scale = ScalarMappable(norm=norm, cmap=cmap).to_rgba(data,alpha=None)

#Define color for blank entries
blank_color = '#c4c4c4'
color_list = []
for i in range(len(elements)):
	color_list.append(blank_color)

#Compare elements in dataset with elements in periodic table
for i, data_element in enumerate(data_elements):
	element_entry = elements.symbol[elements.symbol.str.lower() == data_element.lower()]
	if element_entry.empty == False:
		element_index = element_entry.index[0]
	else:
		print('WARNING: Invalid chemical symbol: '+data_element)
	if color_list[element_index] != blank_color:
		print('WARNING: Multiple entries for element '+data_element)
	color_list[element_index] = to_hex(color_scale[i])

#Define figure properties for visualizing data
source = ColumnDataSource(
    data=dict(
        group=[str(x) for x in elements['group']],
        period=[str(y) for y in elements['period']],
        sym=elements['symbol'],
        atomic_number=elements['atomic number'],
        type_color=color_list
    )
)

#Plot the periodic table
p = figure(x_range=group_range, y_range=list(reversed(period_label)),
	tools='save')
p.plot_width = width
p.outline_line_color = None
p.toolbar_location='above'
p.rect('group', 'period', 0.9, 0.9, source=source,
       alpha=alpha, color='type_color')
p.axis.visible = False
text_props = {
    'source': source,
    'angle': 0,
    'color': 'black',
    'text_align': 'left',
    'text_baseline': 'middle'
}
x = dodge("group", -0.4, range=p.x_range)
y = dodge("period", 0.3, range=p.y_range)
p.text(x=x, y='period', text='sym',
       text_font_style='bold', text_font_size='15pt', **text_props)
p.text(x=x, y=y, text='atomic_number',
       text_font_size='9pt', **text_props)
color_bar = ColorBar(color_mapper=color_mapper,
	ticker=BasicTicker(desired_num_ticks=10),border_line_color=None,
	label_standoff=6,location=(0,0),orientation='vertical',
    scale_alpha=alpha)

if cbar_height is not None:
	color_bar.height = cbar_height

p.add_layout(color_bar,'right')
p.grid.grid_line_color = None
show(p)
