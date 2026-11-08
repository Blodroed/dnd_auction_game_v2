from dash import html, dcc
import plotly.express as px
from dash import dash_table
import pandas as pd
import json
from pathlib import Path

header = html.Header(
    html.H1("D&D Auction Game Dashboard 🐉"),
    style={
        "textAlign": "center",
        "color": "var(--almond)",
        "fontFamily": "Quentin Caps, fantasy",
        "fontSize": "36px",
        "textShadow": "2px 2px 5px var(--licorice)",
        "backgroundColor": "var(--red-cmyk)",
        "padding": "10px"
    }
)

def create_agent_stats_panel(agent_stats=None):
    """
    Create the agent stats panel showing current performance metrics.
    
    Args:
        agent_stats (dict): Dictionary containing agent stats
        
    Returns:
        html.Div: Stats panel component
    """
    if agent_stats is None:
        agent_stats = {
            'gold': 0,
            'points': 0,
            'bid_winrate': 0.0,
            'current_strategy': 'Unknown',
            'rounds_played': 0,
            'total_bids': 0,
            'wins': 0,
            'gold_change': 0,
            'points_change': 0
        }
    
    return html.Div([
        html.H3("🎯 Agent Status", 
               style={"color": "var(--almond)", "textAlign": "center", "marginBottom": "20px"}),
        
        # Current Performance Metrics
        html.Div([
            html.Div([
                html.H4("💰", style={"fontSize": "24px", "margin": "0"}),
                html.P(f"{agent_stats.get('gold', 0)}", 
                      style={"fontSize": "20px", "fontWeight": "bold", "margin": "5px 0"}),
                html.P([
                    "Gold ",
                    html.Span(f"({agent_stats.get('gold_change', 0):+d})" if agent_stats.get('gold_change', 0) != 0 else "",
                             style={"color": "#4CAF50" if agent_stats.get('gold_change', 0) > 0 else 
                                           "#F44336" if agent_stats.get('gold_change', 0) < 0 else "#ccc"})
                ], style={"fontSize": "12px", "color": "#ccc", "margin": "0"})
            ], className="stat-card"),
            
            html.Div([
                html.H4("⭐", style={"fontSize": "24px", "margin": "0"}),
                html.P(f"{agent_stats.get('points', 0)}", 
                      style={"fontSize": "20px", "fontWeight": "bold", "margin": "5px 0"}),
                html.P([
                    "Points ",
                    html.Span(f"({agent_stats.get('points_change', 0):+d})" if agent_stats.get('points_change', 0) != 0 else "",
                             style={"color": "#4CAF50" if agent_stats.get('points_change', 0) > 0 else 
                                           "#F44336" if agent_stats.get('points_change', 0) < 0 else "#ccc"})
                ], style={"fontSize": "12px", "color": "#ccc", "margin": "0"})
            ], className="stat-card"),
            
            html.Div([
                html.H4("🎯", style={"fontSize": "24px", "margin": "0"}),
                html.P(f"{agent_stats.get('bid_winrate', 0):.1%}", 
                      style={"fontSize": "20px", "fontWeight": "bold", "margin": "5px 0"}),
                html.P("Win Rate", style={"fontSize": "12px", "color": "#ccc", "margin": "0"})
            ], className="stat-card"),
            
            html.Div([
                html.H4("🧠", style={"fontSize": "24px", "margin": "0"}),
                html.P(f"{agent_stats.get('current_strategy', 'Unknown')}", 
                      style={"fontSize": "14px", "fontWeight": "bold", "margin": "5px 0"}),
                html.P("Strategy", style={"fontSize": "12px", "color": "#ccc", "margin": "0"})
            ], className="stat-card")
        ], style={
            "display": "grid",
            "gridTemplateColumns": "1fr 1fr",
            "gap": "15px"
        })
    ], style={
        "backgroundColor": "#2a2a2a",
        "padding": "20px",
        "borderRadius": "10px",
        "border": "2px solid var(--kobicha)"
    })

def create_settings_verification_panel():
    """Create the settings verification panel with status indicators."""
    return html.Div([
        html.H3("🔍 Settings Verification", 
               style={"color": "var(--almond)", "textAlign": "center", "marginBottom": "20px"}),
        
        html.Div([
            html.Div([
                html.H4("✅", style={"fontSize": "24px", "margin": "0", "textAlign": "center"}),
                html.P(id="verification-status", children="LOADING...", 
                      style={"fontSize": "14px", "fontWeight": "bold", "margin": "5px 0", "textAlign": "center"}),
                html.P("Status", style={"fontSize": "12px", "color": "#ccc", "margin": "0", "textAlign": "center"})
            ], style={
                "backgroundColor": "var(--night)",
                "padding": "15px",
                "borderRadius": "8px",
                "border": "1px solid var(--kobicha)",
                "textAlign": "center"
            }),
            
            html.Div([
                html.H4("🎮", style={"fontSize": "24px", "margin": "0", "textAlign": "center"}),
                html.P(id="verification-bid-mode", children="LOADING...", 
                      style={"fontSize": "14px", "fontWeight": "bold", "margin": "5px 0", "textAlign": "center"}),
                html.P("Current Mode", style={"fontSize": "12px", "color": "#ccc", "margin": "0", "textAlign": "center"})
            ], style={
                "backgroundColor": "var(--night)",
                "padding": "15px",
                "borderRadius": "8px",
                "border": "1px solid var(--kobicha)",
                "textAlign": "center"
            }),
            
            html.Div([
                html.H4("🔄", style={"fontSize": "24px", "margin": "0", "textAlign": "center"}),
                html.P(id="verification-last-updated", children="LOADING...", 
                      style={"fontSize": "12px", "fontWeight": "bold", "margin": "5px 0", "textAlign": "center"}),
                html.P("Last Updated", style={"fontSize": "12px", "color": "#ccc", "margin": "0", "textAlign": "center"})
            ], style={
                "backgroundColor": "var(--night)",
                "padding": "15px",
                "borderRadius": "8px",
                "border": "1px solid var(--kobicha)",
                "textAlign": "center"
            }),
            
            html.Div([
                html.H4("📊", style={"fontSize": "24px", "margin": "0", "textAlign": "center"}),
                html.P(id="verification-issues-count", children="0", 
                      style={"fontSize": "20px", "fontWeight": "bold", "margin": "5px 0", "textAlign": "center"}),
                html.P("Issues", style={"fontSize": "12px", "color": "#ccc", "margin": "0", "textAlign": "center"})
            ], style={
                "backgroundColor": "var(--night)",
                "padding": "15px",
                "borderRadius": "8px",
                "border": "1px solid var(--kobicha)",
                "textAlign": "center"
            }),
        ], style={
            "display": "grid",
            "gridTemplateColumns": "1fr 1fr",
            "gap": "15px",
            "marginBottom": "20px"
        }),
        
        # Issues detail section (initially hidden)
        html.Div(id="verification-issues-detail", children=[], style={"display": "none"})
        
    ], style={
        "backgroundColor": "var(--eerie-black)",
        "padding": "20px",
        "borderRadius": "10px",
        "border": "2px solid var(--kobicha)"
    })

def create_settings_panel(current_settings=None):
    """
    Create the settings management panel for real-time agent configuration.
    
    Args:
        current_settings (dict): Current agent settings
        
    Returns:
        html.Div: Settings panel component
    """
    if current_settings is None:
        # Load default settings
        try:
            settings_path = Path(__file__).parent.parent / "data" / "settings.json"
            with open(settings_path, 'r') as f:
                current_settings = json.load(f)
        except:
            current_settings = {}
    
    strategy_config = current_settings.get('strategy', {})
    bid_config = current_settings.get('bid_modes', {})
    economy_config = current_settings.get('economy', {})
    
    return html.Div([
        html.H3("⚙️ Live Settings", 
               style={"color": "var(--almond)", "textAlign": "center", "marginBottom": "20px"}),
        
        # Strategy Settings
        html.Div([
            html.H4("🎯 Strategy Configuration", style={"color": "#FFD700", "fontSize": "16px"}),
            html.P("Adjust core bidding strategy parameters:", 
                   style={"fontSize": "12px", "color": "#ccc", "fontStyle": "italic", "marginBottom": "10px"}),
            
            html.Label([
                "Aggression Multiplier: ", 
                html.Span("(Higher = more aggressive bidding, 2.0 = balanced)", 
                         style={"fontSize": "10px", "color": "#aaa"})
            ], htmlFor="aggression-slider"),
            dcc.Slider(
                id="aggression-slider",
                min=0.5, max=5.0, step=0.1,
                value=strategy_config.get('aggression_multiplier', 2.0),
                marks={i: str(i) for i in range(1, 6)},
                tooltip={"placement": "bottom", "always_visible": True}
            ),
            
            html.Label([
                "Max Bid Ratio: ", 
                html.Span("(Maximum % of available gold to bid on single auction)", 
                         style={"fontSize": "10px", "color": "#aaa"})
            ], style={"marginTop": "10px"}, htmlFor="max-bid-ratio-slider"),
            dcc.Slider(
                id="max-bid-ratio-slider",
                min=0.1, max=1.0, step=0.05,
                value=strategy_config.get('max_bid_ratio', 0.8),
                marks={i/10: f"{i/10:.1f}" for i in range(1, 11, 2)},
                tooltip={"placement": "bottom", "always_visible": True}
            ),
            
            html.Label([
                "High Value Threshold: ", 
                html.Span("(Minimum expected value to consider 'high value')", 
                         style={"fontSize": "10px", "color": "#aaa"})
            ], style={"marginTop": "10px"}, htmlFor="high-value-input"),
            dcc.Input(
                id="high-value-input",
                name="high-value-threshold",
                type="number",
                value=strategy_config.get('high_value_threshold', 15.0),
                min=5, max=50, step=1,
                style={"width": "100px", "marginLeft": "10px"}
            )
        ], style={"marginBottom": "20px"}),
        
        # Bid Mode Settings  
        html.Div([
            html.H4("💰 Bid Mode Settings", style={"color": "#FFD700", "fontSize": "16px"}),
            html.P("Choose how bids are distributed across selected auctions:", 
                   style={"fontSize": "12px", "color": "#ccc", "fontStyle": "italic", "marginBottom": "10px"}),
            
            html.Label("Bidding Strategy:", htmlFor="bid-mode-dropdown"),
            dcc.Dropdown(
                id="bid-mode-dropdown",
                options=[
                    {"label": "🎯 Mean Green (Recommended) - Smart statistical bidding", "value": "MEAN_GREEN"},
                    {"label": "📊 Even Steven - Equal distribution across auctions", "value": "EVEN_STEVEN"},
                    {"label": "🔥 All or Nothing - Focus on few high-value auctions", "value": "ALL_OR_NOTHING"},
                    {"label": "📈 Higher Lower - Weight by auction value (50% to best)", "value": "HIGHER_LOWER"},
                    {"label": "💥 Aggressive Spread - Spend 85% aggressively", "value": "AGGRESSIVE_SPREAD"}
                ],
                value=bid_config.get('current_mode', 'MEAN_GREEN'),
                style={"color": "black", "marginBottom": "10px"}
            ),
            
            # Bid Mode Explanation
            html.Div(id="bid-mode-explanation", style={
                "backgroundColor": "#2a2a2a", 
                "padding": "10px", 
                "borderRadius": "5px",
                "marginBottom": "15px",
                "fontSize": "12px",
                "color": "#ddd"
            }),
            
            html.Label([
                "Focus Ratio: ", 
                html.Span("(How concentrated your bids are - lower = focus on fewer auctions)", 
                         style={"fontSize": "10px", "color": "#aaa"})
            ], htmlFor="focus-ratio-slider"),
            dcc.Slider(
                id="focus-ratio-slider",
                min=0.1, max=1.0, step=0.1,
                value=bid_config.get('focus_ratio', 0.6),
                marks={i/10: f"{i/10:.1f}" for i in range(1, 11, 2)},
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ], style={"marginBottom": "20px"}),
        
        # Economy Settings
        html.Div([
            html.H4("🏦 Economy Settings", style={"color": "#FFD700", "fontSize": "16px"}),
            html.P("Control spending behavior and gold management:", 
                   style={"fontSize": "12px", "color": "#ccc", "fontStyle": "italic", "marginBottom": "10px"}),
            
            html.Label([
                "Spending Ratio: ", 
                html.Span("(Percentage of available gold to spend per round)", 
                         style={"fontSize": "10px", "color": "#aaa"})
            ], htmlFor="spending-ratio-slider"),
            dcc.Slider(
                id="spending-ratio-slider",
                min=0.1, max=1.0, step=0.05,
                value=economy_config.get('spending_ratio', 0.75),
                marks={i/10: f"{i/10:.1f}" for i in range(1, 11, 2)},
                tooltip={"placement": "bottom", "always_visible": True}
            ),
            
            html.Label([
                "Min Reserve Gold: ", 
                html.Span("(Always keep at least this much gold)", 
                         style={"fontSize": "10px", "color": "#aaa"})
            ], style={"marginTop": "10px"}, htmlFor="min-reserve-input"),
            dcc.Input(
                id="min-reserve-input",
                name="min-reserve-gold",
                type="number",
                value=economy_config.get('min_reserve_gold', 5),
                min=0, max=50, step=1,
                style={"width": "100px", "marginLeft": "10px"}
            ),
            
            # Toggle switches
            html.Div([
                dcc.Checklist(
                    id="economy-toggles",
                    options=[
                        {"label": " Use Max Bet Limit", "value": "use_max_bet_limit"},
                        {"label": " Emergency Spending", "value": "emergency_spending"},
                    ],
                    value=[key for key, condition in [
                        ("use_max_bet_limit", economy_config.get('use_max_bet_limit', True)),
                        ("emergency_spending", economy_config.get('emergency_spend_threshold', 0) > 0)
                    ] if condition],
                    style={"marginTop": "15px"}
                )
            ])
        ])
    ], style={
        "backgroundColor": "#2a2a2a",
        "padding": "20px",
        "borderRadius": "10px",
        "border": "2px solid var(--kobicha)",
        "maxHeight": "600px",
        "overflowY": "auto"
    })

def create_layout(fig, points_fig, vulture_heatmap_fig=None, vulture_table=None, agent_stats=None, current_settings=None):
    """
    Create the comprehensive layout for the D&D Auction Game Agent Management Dashboard.

    Args:
        fig: Plotly figure for gold chart.
        points_fig: Plotly figure for points chart.
        vulture_heatmap_fig: Plotly figure for vulture opportunity heatmap.
        vulture_table: Dash DataTable for vulture opportunities.
        agent_stats: Dictionary containing agent performance stats.
        current_settings: Dictionary containing current agent settings.

    Returns:
        Dash HTML layout.
    """
    return html.Div([
        # Header
        html.Img(
            src="./assets/logo.png",
            style={
                "width": "20%",
                "height": "auto",
                "marginBottom": "20px",
                "display": "block",
                "marginLeft": "auto",
                "marginRight": "auto",
                "filter": "invert(100%)",
                "drop-shadow": "0px 0px 10px var(--licorice)"
            }
        ),
        
        # Top Management Section - Agent Stats (1/5) + Verification (1/5) + Settings (3/5)
        html.Div([
            # Agent Stats Panel (1/5 of flexbox)
            html.Div([
                html.Div(id="agent-stats-panel", children=[
                    create_agent_stats_panel(agent_stats)
                ])
            ], style={"flex": "1", "marginRight": "15px"}),
            
            # Settings Verification Panel (1/5 of flexbox)
            html.Div([
                html.Div(id="settings-verification-panel", children=[
                    create_settings_verification_panel()
                ])
            ], style={"flex": "1", "marginRight": "15px"}),
            
            # Settings Panel (3/5 of flexbox)
            html.Div([
                create_settings_panel(current_settings)
            ], style={"flex": "3"})
        ], style={
            "display": "flex",
            "marginBottom": "30px",
            "gap": "20px"
        }),
        
        # Vulture Mode Analysis Section
        html.Div([
            html.H2("🦅 VULTURE MODE - Dungeon Dice Analysis", 
                   style={"textAlign": "center", "color": "var(--almond)", "textShadow": "0 0 10px var(--licorice)",
                          "fontFamily": "Quentin Caps, fantasy", "fontSize": "28px"}),
            html.P("Heatmap shows dice combinations with exploitation potential. Green = Low competition, Red = High competition",
                   style={"textAlign": "center", "color": "var(--almond)", "fontSize": "14px", "fontStyle": "italic"}),
            
            # Vulture Heatmap
            html.Div([
                dcc.Graph(id="vulture-heatmap", 
                         figure=vulture_heatmap_fig if vulture_heatmap_fig else create_empty_vulture_heatmap(), 
                         style={"border-radius": "15px"})
            ], style={"marginBottom": "20px"}),
            
            # Vulture Opportunities Table
            html.Div([
                html.H3("🎯 Top Vulture Opportunities", 
                       style={"textAlign": "center", "color": "var(--almond)", "fontSize": "20px"}),
                html.Div(id="vulture-table-container", children=[
                    vulture_table if vulture_table else create_empty_opportunities_table()
                ])
            ], style={"marginBottom": "30px"})
            
        ], id="vulture-section", style={"marginBottom": "30px"}),
        
        # Bottom Charts Section - Gold (left half) + Points (right half)
        html.Div([
            # Gold Chart (Left Half)
            html.Div([
                dcc.Graph(id="gold-chart", figure=fig, style={"border-radius": "15px"})
            ], style={"flex": "1", "marginRight": "10px"}),
            
            # Points Chart (Right Half)
            html.Div([
                dcc.Graph(id="points-chart", figure=points_fig, style={"border-radius": "15px"})
            ], style={"flex": "1", "marginLeft": "10px"})
        ], style={
            "display": "flex",
            "gap": "20px",
            "marginBottom": "20px"
        }),
        
        # Update interval for real-time data
        dcc.Interval(id="interval", interval=1000, n_intervals=0),
        
        # Store components for settings updates
        dcc.Store(id="settings-store"),
        dcc.Store(id="agent-data-store")
        
    ], style={"padding": "20px"})

def create_chart_template():
    """
    Define a common template for chart layouts, using CSS colors and rounded corners.

    Returns:
        dict: A dictionary containing layout properties for charts.
    """
    return {
        "template": "plotly_dark",
        "title_font": dict(family="Papyrus, fantasy", size=24, color="var(--almond)"),
        "xaxis_title": "Round Number",
        "yaxis_title": "Value 🪙",
        "font": dict(family="Courier New, monospace", size=14, color="var(--almond)"),
        "plot_bgcolor": "#150A12",
        "paper_bgcolor": "var(--red-cmyk)",
        "legend": dict(
            title="Players",
            font=dict(size=12, color="var(--almond)"),
            bgcolor="rgba(0,0,0,0.5)",
            bordercolor="var(--kobicha)",
            borderwidth=1
        ),
        "hoverlabel": dict(
            font_size=12,
            font_family="Courier New, monospace",
            bgcolor="var(--kobicha)",
            bordercolor="var(--almond)",
            font_color="var(--almond)"
        ),
        "margin": dict(l=40, r=40, t=40, b=40)  # Use margins for spacing
    }

def apply_chart_template(fig, title):
    """
    Apply the chart template to a given figure.

    Args:
        fig: The Plotly figure to update.
        title: The title of the chart.
    """
    template = create_chart_template()
    fig.update_layout(**template, title=title)
    return fig

def create_vulture_heatmap(opportunity_matrix):
    """
    Create a heatmap visualization of vulture opportunities.
    
    Args:
        opportunity_matrix (pd.DataFrame): Matrix with dice types as columns and 
                                         dice numbers as rows, values are vulture scores
                                         
    Returns:
        plotly.graph_objects.Figure: Heatmap figure
    """
    import plotly.graph_objects as go
    
    if opportunity_matrix.empty:
        # Create empty heatmap
        fig = go.Figure()
        fig.add_annotation(
            text="No vulture data available yet.<br>Play some games to build the analysis!",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=16, color="white")
        )
        fig.update_layout(
            title="🦅 Vulture Opportunity Heatmap",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        return fig
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=opportunity_matrix.values,
        x=opportunity_matrix.columns,
        y=opportunity_matrix.index,
        colorscale=[
            [0, '#8B0000'],      # Dark red for low scores
            [0.3, '#FF4500'],    # Orange-red
            [0.6, '#FFD700'],    # Gold
            [1, '#00FF00']       # Bright green for high scores
        ],
        colorbar=dict(
            title="Vulture Score",
            tickmode="linear",
            tick0=0,
            dtick=0.2,
            len=0.7
        ),
        hovertemplate='<b>%{y}</b><br>%{x}<br>Vulture Score: %{z:.3f}<extra></extra>'
    ))
    
    # Add text annotations for values
    for i in range(len(opportunity_matrix.index)):
        for j in range(len(opportunity_matrix.columns)):
            value = opportunity_matrix.iloc[i, j]
            if value > 0:  # Only show non-zero values
                fig.add_annotation(
                    x=j, y=i,
                    text=f"{value:.2f}",
                    showarrow=False,
                    font=dict(color="white" if value < 0.5 else "black", size=10)
                )
    
    fig.update_layout(
        title="🦅 Vulture Opportunity Heatmap - Green Zones for Exploitation",
        xaxis_title="Die Type",
        yaxis_title="Number of Dice",
        font=dict(size=12),
        width=800,
        height=500,
        plot_bgcolor='rgba(0,0,0,0.1)'
    )
    
    return apply_chart_template(fig, "🦅 Vulture Opportunity Heatmap")

def create_empty_vulture_heatmap():
    """Create an empty vulture heatmap for initialization."""
    import plotly.graph_objects as go
    
    fig = go.Figure()
    fig.add_annotation(
        text="No vulture analysis data available yet.<br>Start playing games to build the heatmap!",
        xref="paper", yref="paper",
        x=0.5, y=0.5, xanchor='center', yanchor='middle',
        showarrow=False,
        font=dict(size=16, color="white")
    )
    fig.update_layout(
        title="🦅 Vulture Opportunity Heatmap",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=400
    )
    return apply_chart_template(fig, "🦅 Vulture Opportunity Heatmap")

def create_empty_opportunities_table():
    """Create an empty opportunities table for initialization."""
    return html.Div(
        "No vulture opportunities identified yet. Play some games to build the analysis!",
        style={
            "textAlign": "center", 
            "color": "var(--almond)", 
            "fontStyle": "italic",
            "padding": "40px",
            "backgroundColor": "#2a2a2a",
            "borderRadius": "10px",
            "border": "2px dashed #666"
        }
    )

def highlight_agent_in_chart(fig, agent_id, agent_name="DoomGuy666"):
    """
    Highlight the specified agent in the chart with special styling.
    
    Args:
        fig: Plotly figure to modify
        agent_id: The agent ID to highlight (e.g., "local_rand_id_234156")
        agent_name: The display name for the agent
        
    Returns:
        Modified Plotly figure
    """
    # Update traces to highlight our agent
    for trace in fig.data:
        if hasattr(trace, 'name') and trace.name and agent_id in str(trace.name):
            # Make our agent's line thicker and more prominent
            trace.update(
                line=dict(width=4, dash='solid'),
                marker=dict(size=8, symbol='star'),
                name=f"🎯 {agent_name} (YOU)"
            )
        else:
            # Make other agents' lines thinner and more transparent
            if hasattr(trace, 'line'):
                trace.update(
                    line=dict(width=2),
                    marker=dict(size=4),
                    opacity=0.7
                )
    
    return fig

def create_vulture_opportunities_table(opportunities_data):
    """
    Create a Dash DataTable for top vulture opportunities.

    Args:
        opportunities_data (list): List of dictionaries with opportunity data

    Returns:
        dash_table.DataTable: A Dash DataTable component.
    """
    import pandas as pd
    if opportunities_data is None or (isinstance(opportunities_data, pd.DataFrame) and opportunities_data.empty) or (isinstance(opportunities_data, list) and len(opportunities_data) == 0):
        return create_empty_opportunities_table()
    
    # Prepare data for table
    table_data = []
    
    # Handle DataFrame input
    if isinstance(opportunities_data, pd.DataFrame):
        # Convert DataFrame to list of dictionaries
        data_list = opportunities_data.head(10).to_dict('records')
    else:
        data_list = opportunities_data[:10] if isinstance(opportunities_data, list) else []
    
    for i, opp in enumerate(data_list):
        # Handle both dictionary and DataFrame row access
        if isinstance(opp, dict):
            dice_combo = opp.get('dice_combination', f"{opp.get('num_dice', 'N')}d{opp.get('die_type', 'A')}")
            vulture_score = opp.get('vulture_score', 0)
            avg_comp = opp.get('avg_competition', 0)
            no_bid_pct = opp.get('no_bid_percentage', 0)
        else:
            # Fallback for other formats
            dice_combo = f"{i+1}dX"
            vulture_score = 0
            avg_comp = 0
            no_bid_pct = 0
            
        table_data.append({
            'rank': i + 1,
            'dice_combination': dice_combo,
            'vulture_score': f"{vulture_score:.3f}",
            'avg_competition': f"{avg_comp:.1f}",
            'no_bid_percentage': f"{no_bid_pct*100:.1f}%",
            'recommendation': 'HIGH' if vulture_score > 0.7 else 
                            'MEDIUM' if vulture_score > 0.4 else 'LOW'
        })
    
    columns = [
        {"name": "Rank", "id": "rank"},
        {"name": "Dice", "id": "dice_combination"},
        {"name": "Vulture Score", "id": "vulture_score"},
        {"name": "Avg Competition", "id": "avg_competition"},
        {"name": "No Bid %", "id": "no_bid_percentage"},
        {"name": "Action", "id": "recommendation"}
    ]

    return dash_table.DataTable(
        id='vulture-opportunities-table',
        columns=[{"name": col["name"], "id": col["id"]} for col in columns],  # Type fix
        data=table_data,
        style_table={
            "margin": "0 auto",
            "width": "90%",
            "overflowX": "auto"
        },
        style_cell={
            "textAlign": "center",
            "fontFamily": "Courier New, monospace",
            "backgroundColor": "#1e1e1e",
            "color": "#f5f5f5",
            "border": "1px solid #444444",
            "padding": "8px",
        },
        style_header={
            "backgroundColor": "#4CAF50",
            "fontWeight": "bold",
            "color": "white",
            "borderBottom": "2px solid #444444"
        },
# Removed problematic style_data_conditional - will use CSS classes instead
    )