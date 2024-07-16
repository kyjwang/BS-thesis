import pandas as pd
import random 
import math
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

# Function to calculate positions of nodes in a circle with category starting points
def calculate_positions(elements_df):
    categories = elements_df['Type'].unique()
    num_categories = len(categories)
    angle_step_category = 2 * math.pi / num_categories  # Angle step for categories
    large_radius = 300  # Radius for the large circle of categories
    small_radius = 50  # Radius for the smaller circles of nodes

    category_positions = {}

    for i, category in enumerate(categories):
        # Calculate starting point for each category on the larger circle
        category_angle = i * angle_step_category
        category_center_x = large_radius * math.cos(category_angle)
        category_center_y = large_radius * math.sin(category_angle)

        nodes_in_category = elements_df[elements_df['Type'] == category]
        num_nodes = len(nodes_in_category)
        angle_step_node = 2 * math.pi / num_nodes  # Angle step for nodes within each category
        positions = []

        for j, node in enumerate(nodes_in_category.itertuples()):
            # Calculate position for each node within the smaller circle around the category center
            node_angle = j * angle_step_node
            x = category_center_x + small_radius * math.cos(node_angle)
            y = category_center_y + small_radius * math.sin(node_angle)
            positions.append((node.Label, x, y))

        category_positions[category] = positions

    return category_positions

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
            category_positions = calculate_positions(elements_df)
            # Function to assign color based on category
            def assign_colors(category):
                return category_colors.get(category, '#d3d3d3')  # Default color if category not found
            
            for category, positions in category_positions.items():
                for label, x, y in positions:
                    node = {
                        "id": label,
                        "label": label,
                        "color": assign_colors(category),
                        "shape": "dot",
                        "size": 20,
                        "x": x,
                        "y": y,
                        "fixed": {"x": True, "y": True}  # Initially fix the nodes
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
