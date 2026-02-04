import pandas as pd
import matplotlib.pyplot as plt
import glob
import os

def plot_top_10_hcp_trends():
    report_path = 'final_hyperhai_risk_report.csv'
    if not os.path.exists(report_path):
        print(f"[ERROR] File '{report_path}' tidak ditemukan. Jalankan report.py terlebih dahulu.")
        return

    report_df = pd.read_csv(report_path)
    top_10_ids = report_df['HCP_ID'].head(10).tolist()
    print(f"Processing trends for Top 10 HCPs: {', '.join(top_10_ids)}")

    all_files = sorted(glob.glob('hcp_risk_shift_*.csv'))
    if not all_files:
        print("[ERROR] Tidak ada file 'hcp_risk_shift_*.csv' ditemukan.")
        return

    data_list = []
    for filename in all_files:
        try:
            shift_num = int(filename.split('_')[-1].split('.')[0])
            df = pd.read_csv(filename)
            for hcp_id in top_10_ids:
                val = df[df['HCP_ID'] == hcp_id]['Event_Count'].values
                data_list.append({
                    'Shift': shift_num,
                    'HCP_ID': hcp_id,
                    'Risk': val[0] if len(val) > 0 else 0
                })
        except Exception as e:
            print(f"[WARNING] Failed to process {filename}: {e}")

    df_trend = pd.DataFrame(data_list)

    plt.figure(figsize=(14, 8))
    colormap = plt.cm.get_cmap('tab10', 10)

    for i, hcp_id in enumerate(top_10_ids):
        subset = df_trend[df_trend['HCP_ID'] == hcp_id]
        if not subset.empty:
            plt.plot(subset['Shift'], subset['Risk'],
                     label=hcp_id,
                     color=colormap(i),
                     marker='o', linewidth=2, markersize=5, alpha=0.8)

    plt.axvspan(10, 13, color='gray', alpha=0.1, label='Weekend Period')
    plt.title('Weekly Risk Trends: Top 10 High-Risk HCPs', fontsize=18, fontweight='bold', pad=25)
    plt.xlabel('Shift Number (1 - 14)', fontsize=13)
    plt.ylabel('Hyper-event Count (Centrality)', fontsize=13)
    plt.xticks(range(1, 15))
    plt.legend(title="HCP ID", bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)
    plt.grid(True, linestyle=':', alpha=0.6)

    if not os.path.exists('figures'):
        os.makedirs('figures')

    output_path = 'figures/top_10_hcp_risk_trend.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"[SUCCESS] Top 10 HCP risk trend plot saved at: {output_path}")

if __name__ == "__main__":
    plot_top_10_hcp_trends()
