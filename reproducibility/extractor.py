import pandas as pd
import os

def generate_key_findings():
    report_file = 'final_hyperhai_risk_report.csv'
    hotspot_file = 'top_hcp_hotspots.csv'
    
    if not os.path.exists(report_file) or not os.path.exists(hotspot_file):
        print("[ERROR] Make sure the files 'final_hyperhai_risk_report.csv' and 'top_hcp_hotspots.csv' exist.")
        return

    # 1. Load Data
    df_hcp = pd.read_csv(report_file)
    df_geo = pd.read_csv(hotspot_file)

    # 2. Extract Data for Findings
    top_hcp = df_hcp.iloc[0]
    top_consistent = df_hcp[df_hcp['count'] >= 10].shape[0]
    top_anchor = df_geo.iloc[0]

    print("--- AUTOMATED KEY FINDINGS SUMMARY ---")
    
    # Finding 1: High-Risk Actors
    print(f"1. HIGH-RISK ACTORS: Individual '{top_hcp['HCP_ID']}' has the highest risk centrality ")
    print(f"   with an accumulation of {int(top_hcp['sum'])} group interaction events.")
    
    # Finding 2: Spatial Bottlenecks
    print(f"2. SPATIAL BOTTLENECKS: Anchor '{top_anchor['Anchor_ID']}' is the primary risk hotspot, ")
    print(f"   mediating {int(top_anchor['Cluster_Frequency'])} multi-person interactions.")
    
    # Finding 3: Temporal Consistency
    print(f"3. TEMPORAL CONSISTENCY: There are {top_consistent} HCPs who consistently appear in ")
    print(f"   high-risk clusters across at least 10 out of 14 shifts analyzed.")

if __name__ == "__main__":
    generate_key_findings()
