import json
import pandas as pd
from collections import Counter
import sys
import os

def analyze(shift_arg):
    input_file = 'spatial_hypergraph_final.json'
    output_file_hcp = f'hcp_risk_shift_{shift_arg}.csv'
    output_file_anchor = f'anchor_risk_shift_{shift_arg}.csv'

    if not os.path.exists(input_file):
        print(f"[ERROR] File '{input_file}' not found for Shift {shift_arg}!")
        return

    # Read JSON data
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to read JSON: {e}")
        return

    print(f"--- Analyzing Risk for Shift {shift_arg} ({len(data)} Hyper-events) ---")

    # Collect all members
    all_members = []
    spatial_events_count = 0

    for event in data:
        members = event.get('members', [])
        all_members.extend(members)
        if event.get('centroid_location') is not None:
            spatial_events_count += 1

    member_counts = Counter(all_members)

    # Separate HCPs and Anchors
    hcp_centrality = {k: v for k, v in member_counts.items() if not k.startswith('b')}
    anchor_centrality = {k: v for k, v in member_counts.items() if k.startswith('b')}

    print(f"Total Spatial Interactions (with Location): {spatial_events_count}")
    print(f"Total Social Interactions (HCP only, without location): {len(data) - spatial_events_count}")

    # HCP
    if hcp_centrality:
        df_hcp = pd.DataFrame(hcp_centrality.items(), columns=['HCP_ID', 'Event_Count'])
        df_hcp.to_csv(output_file_hcp, index=False)
        print(f"[SUCCESS] HCP risk analysis saved to '{output_file_hcp}'")
        print("\nTop 5 High-Risk HCPs:")
        print(df_hcp.sort_values(by='Event_Count', ascending=False).head(5))
    else:
        print(f"[INFO] No HCP found in Shift {shift_arg}. CSV file not created.")
        df_hcp = pd.DataFrame(columns=['HCP_ID', 'Event_Count'])  # empty placeholder

    # Anchor / location
    if anchor_centrality:
        df_anchor = pd.DataFrame(anchor_centrality.items(), columns=['Anchor_ID', 'Usage_Count'])
        df_anchor.to_csv(output_file_anchor, index=False)
        print(f"[SUCCESS] Location risk analysis saved to '{output_file_anchor}'")
        print("\nTop 5 Risk Hotspots (Locations):")
        print(df_anchor.sort_values(by='Usage_Count', ascending=False).head(5))
    else:
        print(f"[INFO] No Anchor found in Shift {shift_arg}. CSV file not created.")
        df_anchor = pd.DataFrame(columns=['Anchor_ID', 'Usage_Count'])  # empty placeholder

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analysis.py <shift_number>")
        sys.exit(1)

    shift_arg = sys.argv[1]
    analyze(shift_arg)
