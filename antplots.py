import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
from collections import namedtuple
import math
from django.conf import settings


Coordinates = namedtuple("Coordinates", ["x", "y"])

def format_y_axis(x, pos):
    return f"{x*90:.0f}°"

def init_plot(azind_value, elind_value, color1, label1, azcom_value, elcom_value, color2, label2):

    azind_value = math.radians(azind_value)
    azcom_value = math.radians(azcom_value)
    elind_value = elind_value / 90
    elcom_value = elcom_value / 90

    fig = plt.figure(figsize=(6, 8))
    ax = fig.add_subplot(polar=True)
    ax.plot(azind_value, elind_value, marker='o', linestyle='None', color=color1, label=label1)
    ax.plot(azcom_value, elcom_value, marker='x', linestyle='None', color=color2, label=label2)
    ax.xaxis.grid(True, color="grey", alpha=0.6)
    ax.yaxis.grid(True, color="grey", alpha=0.6)
    ax.set_rlabel_position(90 + 22.5)
    ax.set_rlim(bottom=0, top=1)
    ax.set_rticks([0, 30/90, 60/90, 90/90])  
    ax.set_theta_zero_location("N")
    ax.grid(True)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(format_y_axis))
    ax.set_title('Antenna Position', pad=15)
    plt.tight_layout()
    ax.legend(loc='upper left', bbox_to_anchor=(0, 1.1))

    ax_table = fig.add_subplot()
    ax_table.axis('off')
    # table
    data = {'': [label1, label2],
            'Azimuth': [math.degrees(azind_value), math.degrees(azcom_value)],
            'Elevation': [elind_value * 90, elcom_value * 90]}
    df = pd.DataFrame(data)
    table = ax_table.table(cellText=df.values, colLabels=df.columns, cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.5)
    fig.tight_layout()
    plt.show()

    # test data


azind_value = 22
elind_value = 50
color1 = 'b'
label1 = 'Indicated'
azcom_value = 40
elcom_value = 20
color2 = 'r'
label2 = 'Commanded'
init_plot(azind_value, elind_value, color1, label1, azcom_value, elcom_value, color2, label2)