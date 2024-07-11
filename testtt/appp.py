import os
import json
import xlrd
import networkx as nx
from flask import Flask, request, render_template, redirect, url_for
import numpy as np

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index'))
    
    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        graph_data = process_excel(file_path)
        return render_template('graph.html', graph_data=json.dumps(graph_data))
    
    return redirect(url_for('index'))

@app.route('/test')
def test_with_kevin():
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'kevin.xlsx')
    graph_data = process_excel(file_path)
    return render_template('graph.html', graph_data=json.dumps(graph_data))

def process_excel(file_path):
    workbook = xlrd.open_workbook(file_path)
    sheet = workbook.sheet_by_index(0)

    nodes = []
    edges = []

    # Assuming the Excel sheet has a specific format
    for row_idx in range(1, sheet.nrows):
        node_id = int(sheet.cell(row_idx, 0).value)
        node_name = sheet.cell(row_idx, 1).value
        node_category = sheet.cell(row_idx, 2).value
        nodes.append({'id': node_id, 'label': node_name, 'group': node_category})

        for col_idx in range(3, sheet.ncols):
            effect = sheet.cell(row_idx, col_idx).value
            if effect != 0:
                edges.append({'from': node_id, 'to': col_idx - 2, 'value': effect})

    return {'nodes': nodes, 'edges': edges}

if __name__ == '__main__':
    app.run(debug=True)
