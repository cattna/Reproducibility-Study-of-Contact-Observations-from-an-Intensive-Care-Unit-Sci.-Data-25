import json
import pandas as pd
from collections import Counter

def analyze_hyperhai_risk():
    input_file = 'spatial_hypergraph_final.json'

    with open(input_file, 'r') as f:
        data = json.load(f)

    print(f"--- Analyzing Risk from {len(data)} Hyper-events ---")

    all_members = []
    spatial_events_count = 0

    for event in data:
        all_members.extend(event['members'])
        if event.get('centroid_location') is not None:
            spatial_events_count += 1

    member_counts = Counter(all_members)

    hcp_centrality = {k: v for k, v in member_counts.items() if not k.startswith('b')}
    anchor_centrality = {k: v for k, v in member_counts.items() if k.startswith('b')}

    print(f"Total Spatial Interactions (with Location): {spatial_events_count}")
    print(f"Total Social Interactions (HCP only): {len(data) - spatial_events_count}")
    print(f"Number of HCPs Involved: {len(hcp_centrality)}")
    print(f"Number of Anchors Involved: {len(anchor_centrality)}")

    df_hcp = pd.DataFrame(hcp_centrality.items(), columns=['HCP_ID', 'Event_Count'])
    print("\n--- Top 5 High-Risk HCPs (Centrality) ---")
    print(df_hcp.sort_values(by='Event_Count', ascending=False).head(5))

    df_loc = pd.DataFrame(anchor_centrality.items(), columns=['Anchor_ID', 'Usage_Count'])
    print("\n--- Top 5 Risk Hotspots (Locations) ---")
    print(df_loc.sort_values(by='Usage_Count', ascending=False).head(5))

    df_hcp.to_csv('hcp_risk_ranking.csv', index=False)
    print("\n[SUCCESS] Risk analysis results saved to 'hcp_risk_ranking.csv'")

if __name__ == "__main__":
    analyze_hyperhai_risk()