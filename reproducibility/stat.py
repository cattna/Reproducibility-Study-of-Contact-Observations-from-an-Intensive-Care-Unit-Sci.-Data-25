import subprocess

def run_full_repro_suite():
    shifts = [f"{i:02d}" for i in range(1, 15)]
    print(f"Starting massive processing for {len(shifts)} shifts...")

    for s in shifts:
        print(f"\n>>> Processing Shift {s}...")

        try:
            res1 = subprocess.run(
                ['python', 'repro3.py', s],
                capture_output=True,
                text=True
            )
            if res1.returncode != 0:
                print(f"[ERROR] Hypergraph build failed for Shift {s}")
                print(res1.stderr)
                continue
        except Exception as e:
            print(f"[EXCEPTION] Failed to run repro3.py for Shift {s}: {e}")
            continue

        try:
            res2 = subprocess.run(
                ['python', 'analysis.py', s],
                capture_output=True,
                text=True
            )
            if res2.returncode != 0:
                print(f"[ERROR] Risk analysis failed for Shift {s}")
                print(res2.stderr)
            else:
                print(f"[SUCCESS] Shift {s} processed successfully.")
        except Exception as e:
            print(f"[EXCEPTION] Failed to run analysis.py for Shift {s}: {e}")

    print("\n[DONE] Check hcp_risk_shift_*.csv files in your folder.")

if __name__ == "__main__":
    run_full_repro_suite()
