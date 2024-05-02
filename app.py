import json
import xlrd
from flask import Flask, render_template, request, redirect, url_for, send_file, session
import networkx as nx
import numpy as np
import random
from pyvis.network import Network
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

from openpyxl import load_workbook

file = xlrd.open_workbook("network.xlsx")
categories = file.sheet_by_index(0)
network = file.sheet_by_index(1)


@app.route('/')
def hello_world():
    return render_template('intro.html')


@app.route('/', methods=['POST', 'GET'])
def main():
    if request.method == 'POST':
        category_dict = {}
        for row in range(categories.nrows):
            if row > 0:
                _data = categories.row_slice(row)
                node = _data[0].value
                category = _data[1].value
                category_dict[node] = category

        mylist = list(category_dict.keys())
        session['nodes'] = mylist
        myvar = "[" + str(session['nodes'])[1:-1] + "]" if "nodes" in session else None
        return render_template('main.html', myvar=myvar)


@app.route('/graph/', methods=['GET', 'POST'])
def graph():
    G = nx.DiGraph()
    category_dict = {}
    nodes_val = None

    if request.method == "POST":
        nodes_val = request.get_json()

    if nodes_val is not None:
        print(nodes_val)
    else:
        nodes_val = {'data': [
            {"node": "wellbeing explicit in school curriculum", "value": 1},
            {"node": "wellbeing explicit in school curriculum", "value": 1},
            {"node": "wellbeing explicit in school curriculum", "value": 1}
        ]}

    for row in range(network.nrows):
        if row > 0:
            _data = network.row_slice(row)
            _Node1 = _data[0].value
            _Node2 = _data[1].value
            if _Node2 == nodes_val['data'][0]["node"]:
                weight = float(nodes_val['data'][0]["value"])
            elif _Node2 == nodes_val['data'][1]["node"]:
                weight = float(nodes_val['data'][1]["value"])
            elif _Node2 == nodes_val['data'][2]["node"]:
                weight = float(nodes_val['data'][2]["value"])
            else:
                weight = float(_data[2].value)
            G.add_weighted_edges_from([(_Node1, _Node2, weight)])

    for row in range(categories.nrows):
        if row > 0:
            _data = categories.row_slice(row)
            node = _data[0].value
            category = _data[1].value
            category_dict[node] = category

    pr = nx.pagerank(G, alpha=0.65)
    pr_list = list(pr)
    pr_keys = list(pr.keys())
    pr_values = list(pr.values())

    nt = Network(height='100%', width='100%', directed=True, font_color='#FF000000')
    nt.from_nx(G, show_edge_weights=False)

    edu_x = 900
    edu_y = 0

    fam_x = 600
    fam_y = 300

    cor_x = 600
    cor_y = 0

    rel_x = 150
    rel_y = 0

    soc_x = 0
    soc_y = 0

    ski_x = 150
    ski_y = 200

    wor_x = 150
    wor_y = 500

    hel_x= 500
    hel_y= 500
    for node in nt.nodes:
        node['size'] = 40
        node['level'] = 1
        node['title'] = node['label']
        # node['x'] = x
        # node['y'] = y
        # x += 200
        # if x >= 2200:
        #     x = 10
        #     y += 200
        index = pr_keys.index(node['label'])
        if 0.1 > abs(pr_values[index]) >= 0.01:
            node['borderWidth'] = 5
            node['borderWidthSelected'] = 5
        elif 1 > abs(pr_values[index]) >= 0.1:
            node['borderWidth'] = 10
            node['borderWidthSelected'] = 10
        elif abs(pr_values[index]) >= 1:
            node['borderWidth'] = 15
            node['borderWidthSelected'] = 15
        else:
            node['borderWidth'] = 0
            node['borderWidthSelected'] = 0

        if str(node['label']) in category_dict.keys():
            if category_dict[node['label']] == "education":
                node['color'] = '#0033cc'
                node['x'] = edu_x
                node['y'] = edu_y
                edu_x += 100
                if edu_x > 1200:
                    edu_x = 950
                    edu_y += 100
            elif category_dict[node['label']] == "family":
                node['color'] = '#ff6699'
                node['x'] = fam_x
                node['y'] = fam_y
                fam_x += 100
                if fam_x > 1200:
                    fam_x = 650
                    fam_y += 100
            elif category_dict[node['label']] == "core":
                node['color'] = '#99ccff'
                node['x'] = cor_x
                node['y'] = cor_y
                cor_x += 100
                if cor_x > 800:
                    cor_x = 550
                    cor_y += 100
            elif category_dict[node['label']] == "relationships":
                node['color'] = '#009933'
                node['x'] = rel_x
                node['y'] = rel_y
                rel_x += 100
                if rel_x > 500:
                    rel_x = 200
                    rel_y += 100
            elif category_dict[node['label']] == "work":
                node['color'] = '#ff9900'
                node['x'] = wor_x
                node['y'] = wor_y
                wor_x += 100
            elif category_dict[node['label']] == "social":
                node['color'] = '#ff3300'
                node['x'] = soc_x
                node['y'] = soc_y
                soc_y += 120
            elif category_dict[node['label']] == "skills":
                node['color'] = '#99cc00'
                node['x'] = ski_x
                node['y'] = ski_y
                ski_x += 100
                if ski_x > 500:
                    ski_x = 200
                    ski_y += 100
            elif category_dict[node['label']] == "health":
                node['color'] = '#ffff00'
                node['x'] = hel_x
                node['y'] = hel_y
                if hel_x > 700:
                    hel_x += 100
            else:
                node['color'] = 'brown'
                node['x'] = random.randrange(0, 2200, 100)
                node['y'] = random.randrange(0, 1000, 100)

    previous_pr = pr_values
    nt.set_edge_smooth(smooth_type='diagonalCross')
    nt.toggle_physics(False)
    nt.inherit_edge_colors(True)
    # nt.hrepulsion(spring_length=1000,node_distance=1000)
    # nt.force_atlas_2based(gravity=-200)
    nt.barnes_hut(overlap=1, gravity=-500)
    nt = Network(height='100%', width='100%', directed=True)
    nt.from_nx(G)

    # Check if the file exists before saving
    if not os.path.exists('templates/nx.html'):
        nt.save_graph('templates/nx.html')
    
    return render_template("nx.html")


if __name__ == '__main__':
    app.run(debug=True)
