import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
from matplotlib.gridspec import GridSpec
from collections import namedtuple

Coordinates = namedtuple("Coordinates", ["x", "y"])

def plot_polar_with_points(azind_value, elind_value, color1, label1, azcom_value, elcom_value, color2, label2):
    fig = plt.figure(figsize=(6, 8)) 


    ax = fig.add_subplot( polar=True)
    ax.plot(azind_value, elind_value, marker='o', linestyle='None', color=color1, label=label1)
    ax.plot(azcom_value, elcom_value, marker='x', linestyle='None', color=color2, label=label2)
    ax.xaxis.grid(True, color="grey", alpha=0.6)
    ax.yaxis.grid(True, color="grey", alpha=0.6)
    ax.set_rlabel_position(90 + 22.5)
    ax.set_rlim(bottom=0, top=1)
    ax.set_rticks([0, 0.2, 0.4, 0.6, 0.8, 1])
    ax.set_theta_zero_location("N")
    ax.grid(True)
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.1f"))
    ax.set_title('Antenna Position', pad=15)
    ax.legend(loc='upper left')


    ax_table = fig.add_subplot()
    ax_table.axis('off')

    # table
    data = {'': [label1, label2],
            'Azimuth': [azind_value, azcom_value],
            'Elevation': [elind_value, elcom_value]}
    df = pd.DataFrame(data)
    table = ax_table.table(cellText=df.values, colLabels=df.columns, cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.5)

    fig.tight_layout()

    plt.show()

# data
azind_value = 95
elind_value = 77
color1 = 'b'
label1 = 'Indicated'

azcom_value = 100
elcom_value = 90
color2 = 'r'
label2 = 'Commanded'

plot_polar_with_points(azind_value, elind_value, color1, label1, azcom_value, elcom_value, color2, label2)
