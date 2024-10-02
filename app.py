import pandas as pd
import random 
import math
from flask import Flask, request, render_template, jsonify

app = Flask(__name__)

# Function to read the Excel file and extract categories with assigned colors
def extract_categories_with_colors(file_path, sheet_name='Elements'):
    df_elements = pd.read_excel(file_path, sheet_name=sheet_name)
    categories = df_elements['Type'].unique()
    category_colors = {category: random_color() for category in categories}
    return category_colors

def random_color():
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))

def calculate_positions(elements_df):
    categories = elements_df['Type'].unique()
    category_radii = {}
    total_radius = 0
    num_categories = len(categories)

    # Calculate the radius of each category's circle
    for category in categories:
        num_nodes = len(elements_df[elements_df['Type'] == category])
        small_radius = num_nodes * 15  
        category_radii[category] = small_radius
        total_radius += small_radius

    large_radius = num_categories * 60 
    category_positions = {}
    current_angle = 0 

    for i, category in enumerate(categories):
        #the space between the small circles are depend on their size
        small_radius = category_radii[category]
        angle_step_category = 2 * math.pi * (small_radius/total_radius)
        current_angle += angle_step_category/2
        category_center_x = large_radius * math.cos(current_angle)
        category_center_y = large_radius * math.sin(current_angle)
        
        # Get all nodes in the category
        nodes_in_category = elements_df[elements_df['Type'] == category]
        num_nodes = len(nodes_in_category)
        angle_step_node = 2 * math.pi / num_nodes
        positions = []

        for j, node in enumerate(nodes_in_category.itertuples()):
            # Calculate position for each node within the smaller circle around the category center
            node_angle = j * angle_step_node
            x = category_center_x + small_radius * math.cos(node_angle)
            y = category_center_y + small_radius * math.sin(node_angle)
            positions.append((node.Label, x, y))

        category_positions[category] = positions
        current_angle += angle_step_category/2 # Update the angle for the next category

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
            categories = elements_df['Type'].unique()
            def assign_colors(category):
                return category_colors.get(category, '#d3d3d3')  # Default color if category not found
            
            for category, positions in category_positions.items():
                for label, x, y in positions:
                    node = {
                        "id": label,
                        "label": label,
                        "color": assign_colors(category),
                        "category" : category,
                        "shape": "dot",
                        "size": 25,
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
            return render_template('main.html', graph_data=graph_data, category_colors=category_colors, categories=categories)
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
    return jsonify(graph_data)

@app.route('/filter_graph', methods=['POST'])
def filter_graph():
        data = request.get_json()
        nodes = data['nodes']
        edges = data['edges']
        selected_categories = data['categories']  # Get selected categories

        print("Received categories:", selected_categories)  # Debugging print

        # Filter nodes based on selected categories
        filtered_nodes = [node for node in nodes if node['category'] in selected_categories]
        print("Filtered nodes:", filtered_nodes)  # Debugging print

        # Filter edges
        filtered_edges = [edge for edge in edges if
                          any(node['id'] == edge['from'] for node in filtered_nodes) and
                          any(node['id'] == edge['to'] for node in filtered_nodes)]
        print("Filtered edges:", filtered_edges)  # Debugging print

        graph_data = {"nodes": filtered_nodes, "edges": filtered_edges}

        return jsonify(graph_data)

    

if __name__ == "__main__":
    app.run(debug=True)
