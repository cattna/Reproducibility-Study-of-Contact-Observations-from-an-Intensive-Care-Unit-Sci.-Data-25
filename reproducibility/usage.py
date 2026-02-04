import cv2
import yaml
import os

def generate_risk_heatmap():
    yaml_file = 'supp/placement005.yaml'
    img_file = 'figures/iculayout.png'
    output_file = 'figures/risk_heatmap.png'

    if not os.path.exists(yaml_file) or not os.path.exists(img_file):
        print("Error: YAML file or layout image not found.")
        return

    with open(yaml_file, 'r') as f:
        placement = yaml.safe_load(f)

    anchors_data = placement.get('anchors', [])
    anchor_coords = {}

    if isinstance(anchors_data, list):
        for a in anchors_data:
            if isinstance(a, dict) and 'label' in a:
                anchor_coords[a['label']] = (int(a['x']), int(a['y']))
            elif isinstance(a, str):
                print(f"Warning: Anchor '{a}' has no coordinates!")
    elif isinstance(anchors_data, dict):
        for label, coords in anchors_data.items():
            if isinstance(coords, dict):
                anchor_coords[label] = (int(coords['x']), int(coords['y']))
            else:
                anchor_coords[label] = (int(coords[0]), int(coords[1]))

    image = cv2.imread(img_file)
    
    hotspots = {
        'b143': 6078, 'b142': 2449, 'b169': 2082, 
        'b059': 1738, 'b002': 1716
    }
    max_val = max(hotspots.values())

    print("--- Creating Spatial Risk Heatmap ---")

    for label, (x, y) in anchor_coords.items():
        if label in hotspots:
            intensity = hotspots[label] / max_val
            color = (0, 0, int(255 * intensity))
            radius = int(20 * intensity) + 5

            for r in range(radius, radius+11, 3):
                alpha = 0.2
                overlay = image.copy()
                cv2.circle(overlay, (x, y), r, color, -1)
                cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0, image)

            cv2.putText(image, f"{label}", (x+5, y-5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    os.makedirs('figures', exist_ok=True)
    cv2.imwrite(output_file, image)
    print(f"Risk heatmap saved to {output_file}")

if __name__ == "__main__":
    generate_risk_heatmap()