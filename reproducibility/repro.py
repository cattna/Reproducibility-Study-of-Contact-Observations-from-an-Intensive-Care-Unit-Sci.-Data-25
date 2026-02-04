import lzma
import json
import os

def extract_hyperedges(shift='02'):
    history_file = f'data/histories/histories{shift}.json.xz'
    hyperedges = []  # List of sets (groups of IDs interacting)

    print(f"--- Extracting Hyperedges from Shift {shift} ---")

    if not os.path.exists(history_file):
        print(f"[ERROR] File {history_file} not found.")
        return

    with lzma.open(history_file, 'rt') as f:
        history = json.load(f)
        # history = {timestamp: {hcp_id: {contacts, state}}}

        # Sample first 1 hour (3600 seconds)
        for i, (ts, second_data) in enumerate(history.items()):
            if i >= 3600:
                break

            current_event = set()

            for hcp, info in second_data.items():
                contacts = info['contacts']
                if contacts:  # If there are contacts
                    current_event.add(hcp)
                    for c in contacts:
                        current_event.add(c)

            if len(current_event) > 2:  # Hyperedge requires at least 3 entities
                hyperedges.append(list(current_event))

    print(f"Successfully extracted {len(hyperedges)} hyper-events.")
    print(f"Example hyperedge at one second: {hyperedges[0] if hyperedges else 'Empty'}")

    # Save result
    with open('hypergraph_structure.json', 'w') as out:
        json.dump(hyperedges, out)

if __name__ == "__main__":
    extract_hyperedges()
