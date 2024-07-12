import pandas as pd
from flask import Flask, request, render_template, jsonify

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'network_info' in request.files:
            network_file = request.files['network_info']
            xls = pd.ExcelFile(network_file)
            elements_df = pd.read_excel(xls, sheet_name='Elements')
            connections_df = pd.read_excel(xls, sheet_name='Connections')
            
            nodes = []
            edges = []

            # Define color map for different types
            color_map = {
                'dirt': '#ff9999',
                'activities': '#99ff99',
                'life': '#9999ff',
                # Add other types if needed
            }
            
            # Create nodes
            for index, row in elements_df.iterrows():
                node = {
                    "id": row["Label"],
                    "label": row["Label"],
                    "color": color_map.get(row["Type"], '#d3d3d3'),
                    "shape": "dot",
                    "size": 20
                }
                nodes.append(node)
            
            # Create edges
            for index, row in connections_df.iterrows():
                if pd.notna(row['From']) and pd.notna(row['To']):
                    edge = {
                        "from": row["From"],
                        "to": row["To"],
                        "width": row.get("Label2", 1)
                    }
                    edges.append(edge)

            graph_data = {"nodes": nodes, "edges": edges}
            print(graph_data)  # Debugging print
            return render_template('main.html', graph_data=graph_data)
    return render_template('intro.html')

@app.route('/graph', methods=['POST'])
def graph():
    data = request.get_json()
    nodes = data['nodes']
    edges = data['edges']
    interventions = data.get('interventions', [])
    
    # Apply interventions to nodes (if necessary)
    for intervention in interventions:
        for node in nodes:
            if node['id'] == intervention['node']:
                node['size'] += int(intervention['value'])  # Example intervention effect
    
    graph_data = {"nodes": nodes, "edges": edges}
    print(graph_data)  # Debugging print
    return jsonify(graph_data)

if __name__ == "__main__":
    app.run(debug=True)
