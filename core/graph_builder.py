import plotly.graph_objects as go

from core.graph_status import STATUS_STYLE, permission_statuses


def build_permission_graph(payload: dict, findings=None) -> go.Figure:
    """Network graph: the app on the left, each requested permission on the right, styled by what we found."""
    app_name = payload.get("app_name", "Analyzed App")
    permissions = list(payload.get("permissions", []))
    status = permission_statuses(permissions, findings)

    count = max(len(permissions), 1)
    y_spacing = 1.0 / (count + 1)
    positions = {p: (1, 1.0 - (i + 1) * y_spacing) for i, p in enumerate(permissions)}   # keyed by FULL name: no clashes

    fig = go.Figure()
    edge_x, edge_y = [], []
    for p in permissions:
        edge_x += [0, positions[p][0], None]
        edge_y += [0.5, positions[p][1], None]
    fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode="lines", hoverinfo="none", showlegend=False,
                             line=dict(width=1.5, color="#00F0FF", dash="dot")))
    fig.add_trace(go.Scatter(x=[0], y=[0.5], mode="markers+text", name="The app", text=[app_name],
                             textposition="bottom center", hoverinfo="text", hovertext=[app_name],
                             marker=dict(size=26, color="#151B28", line=dict(width=2, color="#00F0FF")),
                             textfont=dict(color="white", size=12)))

    for key in ("high", "review", "justified", "ok", "unchecked"):
        members = [p for p in permissions if status[p] == key]
        if not members:
            continue
        legend_text, symbol, colour = STATUS_STYLE[key]
        fig.add_trace(go.Scatter(
            x=[positions[p][0] for p in members], y=[positions[p][1] for p in members],
            mode="markers+text", name=legend_text,
            text=[p.split(".")[-1] for p in members], textposition="middle right",
            hoverinfo="text", hovertext=[f"{p}<br>{legend_text}" for p in members],
            marker=dict(size=20, symbol=symbol, color=colour, line=dict(width=2, color="#00F0FF")),
            textfont=dict(color="white", size=11)))

    if not permissions:
        fig.add_annotation(x=1, y=0.5, text="No permissions found", showarrow=False, font=dict(color="white"))

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=-0.02, font=dict(color="white", size=11)),
        margin=dict(l=20, r=140, t=20, b=60),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.2, 1.6]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 1]),
        height=max(320, 34 * count + 140),
    )
    return fig
