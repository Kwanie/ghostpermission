import plotly.graph_objects as go

def build_permission_graph(payload: dict) -> go.Figure:
    """
    Dynamically builds a Plotly network graph showing the App branching 
    out to its requested permissions.
    """
    # Extract data from the payload
    app_name = payload.get("app_name", "Analyzed App")
    permissions = payload.get("permissions", [])
    
    # Clean up Android permission prefixes so they fit on the screen nicely
    clean_perms = [p.split('.')[-1] for p in permissions] if permissions else ["No Permissions"]
    
    # 1. Define Node Positions (App on left, Permissions spread vertically on right)
    pos = {app_name: (0, 0.5)}
    
    y_spacing = 1.0 / (len(clean_perms) + 1)
    for i, perm in enumerate(clean_perms):
        pos[perm] = (1, 1.0 - (i + 1) * y_spacing)
        
    # 2. Build Edge (Line) Coordinates
    edge_x = []
    edge_y = []
    for perm in clean_perms:
        x0, y0 = pos[app_name]
        x1, y1 = pos[perm]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        
    # 3. Build Node Coordinates and Styling
    node_x = []
    node_y = []
    node_text = []
    node_colors = []
    
    for node, (x, y) in pos.items():
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)
        
        # Style the App node vs the Permission nodes
        if node == app_name:
            node_colors.append('#151B28') # Dark background for the App
        else:
            # Check if it's a high-risk location/camera perms to color it red, else yellow
            if "LOCATION" in node or "CAMERA" in node or "CONTACTS" in node or "SMS" in node:
                node_colors.append('#ef4444') # Red
            else:
                node_colors.append('#f59e0b') # Yellow

    fig = go.Figure()
    
    # Draw Edges (Dotted Cyan Lines)
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y,
        mode='lines',
        line=dict(width=1.5, color='#00F0FF', dash='dot'),
        hoverinfo='none'
    ))
    
    # Draw Nodes (Circles)
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        marker=dict(
            color=node_colors,
            size=22,
            line=dict(width=2, color='#00F0FF') # Cyan border
        ),
        text=node_text,
        textposition=["middle right" if n != app_name else "bottom center" for n in node_text],
        textfont=dict(color="white", size=11, family="sans-serif")
    ))
    
    # Hide the axes and grid to make it look like a seamless canvas
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        margin=dict(l=20, r=120, t=20, b=20),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.2, 1.5]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=300
    )
    
    return fig