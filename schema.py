import matplotlib.pyplot as plt
import networkx as nx

# Create a directed graph for the DFD
G = nx.DiGraph()

# Add nodes to the graph (these represent entities or processes in the DFD)
G.add_node("User", label="User")
G.add_node("Bot", label="Bot Platform")
G.add_node("API", label="Telegram API")
G.add_node("DB", label="Database")
G.add_node("OpenAI", label="OpenAI API")
G.add_node("Auth", label="Authentication")
G.add_node("Integration", label="Integration Credentials")

# Add edges (these represent the flow of data between entities/processes)
G.add_edge("User", "Auth", label="Login/Register")
G.add_edge("Auth", "DB", label="Store User Data")
G.add_edge("Auth", "Bot", label="Authenticate Bot")
G.add_edge("Bot", "API", label="Send/Receive Messages")
G.add_edge("API", "OpenAI", label="Query OpenAI for Response")
G.add_edge("OpenAI", "Bot", label="Response from OpenAI")
G.add_edge("Bot", "DB", label="Store Conversation")
G.add_edge("Bot", "Integration", label="Bot Integration Details")

# Adjust the positions of nodes to increase the gaps
pos = {
    "User": (0, 2),  # Increase y-coordinate for better separation
    "Auth": (1, 2),
    "Bot": (2, 2),
    "API": (3, 2),
    "OpenAI": (4, 2),
    "DB": (1, 1),
    "Integration": (2, 1)
}

# Draw the graph with labels
plt.figure(figsize=(12, 8))  # Increase figure size to accommodate more space
nx.draw_networkx_nodes(G, pos, node_size=3000, node_color="skyblue", alpha=0.6)
nx.draw_networkx_edges(G, pos, width=2, edge_color="gray", alpha=0.6, arrows=True)
nx.draw_networkx_labels(G, pos, font_size=12, font_weight="bold", font_color="black")
nx.draw_networkx_edge_labels(G, pos, edge_labels={(u, v): G[u][v]['label'] for u, v in G.edges()})

# Show the plot
plt.title("Data Flow Diagram (DFD) for Bot Platform")
plt.axis('off')  # Hide the axis
plt.show()
