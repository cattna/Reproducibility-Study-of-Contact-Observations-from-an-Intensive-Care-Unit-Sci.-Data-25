import pandas as pd
import glob
import os

def generate_final_report():
    # 1. Find all per-shift HCP risk files
    all_files = glob.glob('hcp_risk_shift_*.csv')
    if not all_files:
        print("[ERROR] No 'hcp_risk_shift_*.csv' files found.")
        return

    li = []
    for filename in all_files:
        try:
            df = pd.read_csv(filename, index_col=False)
        except Exception as e:
            print(f"[WARN] Failed to read {filename}: {e}")
            continue

        if 'HCP_ID' not in df.columns or 'Event_Count' not in df.columns:
            print(f"[WARN] File {filename} does not contain HCP_ID or Event_Count. Skipped.")
            continue

        # Add shift number from filename
        shift_num = os.path.splitext(os.path.basename(filename))[0].split('_')[-1]
        df['Shift'] = shift_num
        li.append(df)

    if not li:
        print("[ERROR] No valid HCP data to merge.")
        return

    # 2. Merge all data
    full_df = pd.concat(li, axis=0, ignore_index=True)

    # 3. Consistency analysis (who appears most frequently in Top 10 across shifts)
    consistency = full_df.groupby('HCP_ID')['Event_Count'].agg(['sum', 'count', 'mean'])
    consistency = consistency.sort_values(by='sum', ascending=False)

    print("\n--- FINAL HYPERHAI RESEARCH REPORT ---")
    print("Top 10 HCPs with Highest Accumulated Risk (1 Week):")
    print(consistency.head(10))

    # 4. Save for publication / paper
    consistency.to_csv('final_hyperhai_risk_report.csv')
    print("\n[SUCCESS] Final report saved as 'final_hyperhai_risk_report.csv'")

if __name__ == "__main__":
    generate_final_report()