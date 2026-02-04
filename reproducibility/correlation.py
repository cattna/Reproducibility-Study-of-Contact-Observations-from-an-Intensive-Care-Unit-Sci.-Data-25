import json
import pandas as pd
import os

def map_top_hcp_hotspots():
    report_file = 'final_hyperhai_risk_report.csv'
    json_file = 'spatial_hypergraph_final.json'
    
    # 1. Load Top 10 HCP IDs from the final report
    if not os.path.exists(report_file):
        print(f"[ERROR] File '{report_file}' not found!")
        return

    report_df = pd.read_csv(report_file)
    if 'HCP_ID' not in report_df.columns:
        print(f"[ERROR] Column 'HCP_ID' not found in {report_file}")
        return

    top_10_ids = set(report_df['HCP_ID'].head(10).tolist())
    if not top_10_ids:
        print("[INFO] No Top 10 HCP found in the final report.")
        return

    # 2. Scan Spatial Hypergraph
    if not os.path.exists(json_file):
        print(f"[ERROR] File '{json_file}' not found!")
        return

    with open(json_file, 'r') as f:
        try:
            hyper_data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to read JSON: {e}")
            return

    hotspot_counts = {}  # Anchor_ID: Count

    for event in hyper_data:
        members = set(event.get('members', []))
        if not members.isdisjoint(top_10_ids):
            for m in members:
                if m.startswith('b'):  # Anchor / location
                    hotspot_counts[m] = hotspot_counts.get(m, 0) + 1

    if not hotspot_counts:
        print("[INFO] No interaction hotspots found for Top 10 HCP.")
        return

    # 3. Sort Hotspots
    df_hotspots = pd.DataFrame(hotspot_counts.items(), columns=['Anchor_ID', 'Cluster_Frequency'])
    df_hotspots = df_hotspots.sort_values(by='Cluster_Frequency', ascending=False)

    print("\n--- Locations of High-Risk Interactions (Top 10 HCP) ---")
    print(df_hotspots.head(5))

    df_hotspots.to_csv('top_hcp_hotspots.csv', index=False)
    print("\n[SUCCESS] Interaction hotspots saved to 'top_hcp_hotspots.csv'")

if __name__ == "__main__":
    map_top_hcp_hotspots()
