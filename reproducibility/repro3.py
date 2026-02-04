import lzma
import json
import yaml
import os
import sys

def build_spatial_hypergraph(shift='02'):
    try:
        with open('supp/placement005.yaml', 'r') as f:
            placement = yaml.safe_load(f)

        anchor_coords = {}
        anchors_data = placement.get('anchors', {})
        if isinstance(anchors_data, list):
            for a in anchors_data:
                anchor_coords[a['label']] = (a['x'], a['y'])
        elif isinstance(anchors_data, dict):
            for label, coords in anchors_data.items():
                if isinstance(coords, dict):
                    anchor_coords[label] = (coords['x'], coords['y'])
                else:
                    anchor_coords[label] = (coords[0], coords[1])

        print(f"Successfully mapped {len(anchor_coords)} anchor coordinates.")
    except Exception as e:
        print(f"[ERROR] Failed to read YAML: {e}")
        return

    history_file = f'data/histories/histories{shift}.json.xz'
    if not os.path.exists(history_file):
        print(f"[ERROR] File {history_file} not found.")
        return

    spatial_hypergraph = []
    print(f"--- Building Spatial Hypergraph for Shift {shift} ---")

    with lzma.open(history_file, 'rt') as f:
        history = json.load(f)

        for i, (ts, second_data) in enumerate(history.items()):
            if i >= 3600:
                break

            for hcp, info in second_data.items():
                contacts = info['contacts']
                if contacts:
                    event_members = set([hcp] + contacts)
                    if len(event_members) >= 3:
                        coords = [anchor_coords[m] for m in event_members if m in anchor_coords]
                        spatial_hypergraph.append({
                            'time_t': i,
                            'members': list(event_members),
                            'centroid_location': coords[0] if coords else None
                        })

    output_path = 'spatial_hypergraph_final.json'
    with open(output_path, 'w') as out:
        json.dump(spatial_hypergraph, out)

    print(f"Success! {len(spatial_hypergraph)} hyper-events saved to {output_path}")
    if spatial_hypergraph:
        print(f"Example data: {spatial_hypergraph[0]}")

if __name__ == "__main__":
    shift_arg = sys.argv[1] if len(sys.argv) > 1 else '02'
    build_spatial_hypergraph(shift=shift_arg)
