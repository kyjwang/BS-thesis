import pandas as pd
import random 
import math
from flask import Flask, request, render_template, jsonify
import networkx as nx

app = Flask(__name__)

# Function to read the Excel file and extract categories with assigned colors
def extract_categories_with_colors(file_path, sheet_name='Elements'):
    df_elements = pd.read_excel(file_path, sheet_name=sheet_name)
    categories = df_elements['Type'].unique()
    category_colors = {category: random_color() for category in categories}
    return category_colors

def random_color():
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))

def assign_size(value):
    if -1.0 <= value < 0:
        return 15
    elif 0 <= value < 0.01:
        return 25
    elif 0.01 <= value < 0.1:
        return 35
    elif 0.1 <= value < 0.5:
        return 45
    elif 0.5 <= value < 1.0:
        return 55
    elif -10 < value < -1.0:
        return 8
    elif value <= -10: 
        return 2
    elif 1.0 <= value < 10 :
        return 68
    elif 10 <= value:
        return 80

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
            
            category_colors = extract_categories_with_colors(network_file)
            category_positions = calculate_positions(elements_df)
            categories = elements_df['Type'].unique()
            def assign_colors(category):
                return category_colors.get(category, '#d3d3d3')  # Default color if category not found
            
            # Create a graph for PageRank calculation
            G = nx.DiGraph()

            for category, positions in category_positions.items():
                for label, x, y in positions:
                    node = {
                        "id": label,
                        "label": label,
                        "color": assign_colors(category),
                        "category" : category,
                        "shape": "dot",
                        "size": 25,  # Size will be updated later based on PageRank
                        "x": x,
                        "y": y,
                        "fixed": {"x": True, "y": True}  
                    }
                    nodes.append(node)
                    G.add_node(label) 

            # Create edges
            for index, row in connections_df.iterrows():
                if pd.notna(row['From']) and pd.notna(row['To']):
                    edge = {
                        "from": row["From"],
                        "to": row["To"],
                        "width": row.get("Label2", 1)  # If no weight is provided, default is 1
                    }
                    edges.append(edge)
                    G.add_edge(row["From"], row["To"], weight=row.get("Label2", 1))  
            pagerank_scores = nx.pagerank(G, weight='weight')
            for node in nodes:
                node_id = node['id']
                if node_id in pagerank_scores:
                    node['size'] = assign_size(pagerank_scores[node_id]) 
            graph_data = {"nodes": nodes, "edges": edges}
            
        return render_template('main.html', graph_data=graph_data, category_colors=category_colors, categories=categories, pagerank_scores = pagerank_scores)
    return render_template('intro.html')

@app.route('/graph', methods=['POST'])
def graph():
    data = request.get_json()
    nodes = data['nodes']
    edges = data['edges']
    intervention = data.get('interventions', None)
    pagerank_scores = data['pagerank_scores']
  
    def find_node_by_id(node_id, nodes):
        for node in nodes:
            if node['id'] == node_id:
                return node
        return None

    # Recursive function to propagate size change through connected nodes
    def propagate_size_change(node_id, size_change, nodes, edges, visited=None):
        if visited is None:
            visited = set()

        visited.add(node_id)

        current_node = find_node_by_id(node_id, nodes)
        if current_node:
            pagerank_scores[node_id] += size_change
            current_node['size'] = assign_size(pagerank_scores[node_id])
       
        for edge in edges:
            if edge['from'] == node_id:  # If the current node has an outgoing edge
                to_node = edge['to']
                if to_node not in visited: 
                    weights = float(edge['width']) # Ensure no cycles
                    propagate_size_change(to_node, size_change * weights, nodes, edges, visited)
    
    if intervention:
        node_id = intervention['node']
        size_change = int(intervention['value'])
        propagate_size_change(node_id, size_change, nodes, edges)
    
    graph_data = {"nodes": nodes, "edges": edges}
    return jsonify({
        "graph_data": graph_data,
        "pagerank_scores": pagerank_scores
    })

    

if __name__ == "__main__":
    app.run(debug=True)
