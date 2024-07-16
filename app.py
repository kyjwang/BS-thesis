import pandas as pd
import random 
from flask import Flask, request, render_template, jsonify

app = Flask(__name__)

# Function to read the Excel file and extract categories with assigned colors
def extract_categories_with_colors(file_path, sheet_name='Elements'):
    # Read the Excel file
    df_elements = pd.read_excel(file_path, sheet_name=sheet_name)
    
    # Extract unique categories
    categories = df_elements['Type'].unique()
    
    # Generate random colors for each category
    category_colors = {category: random_color() for category in categories}
    
    return category_colors

# Function to generate a random color
def random_color():
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))

 
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
            
            # Extract categories with assigned colors
            category_colors = extract_categories_with_colors(network_file)
            
            # Function to assign color based on category
            def assign_colors(category):
                return category_colors.get(category, '#d3d3d3')  # Default color if category not found
            
            # Create nodes
            for index, row in elements_df.iterrows():
                node = {
                    "id": row["Label"],
                    "label": row["Label"],
                    "color": assign_colors(row["Type"]),
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
            return render_template('main.html', graph_data=graph_data, category_colors=category_colors)
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
