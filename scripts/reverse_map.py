import json
import os
import sys
import argparse
import numpy as np
import cv2

# Tileset category mapping
# You can adjust these based on your specific tilesets
TILE_CATEGORIES = {
    "Grass": "ground",
    "Water": "ground", # Water can be base layer
    "Fences": "overlay",
    "House": "overlay",
    "Basic_Grass_Biom_things": "overlay",
    "Objects": "overlay"
}

LAYER_MAPPING = {
    "Grass": "Ground",
    "Water": "water",
    "Fences": "Fences",
    "House": "Objects",
    "Basic_Grass_Biom_things": "Objects",
    "Objects": "Objects"
}

def load_tileset(tileset_def, base_path):
    image_path = os.path.join(base_path, tileset_def['image'])
    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        print(f"Warning: Could not load tileset image {image_path}")
        return []

    tile_width = tileset_def['tilewidth']
    tile_height = tileset_def['tileheight']
    margin = tileset_def.get('margin', 0)
    spacing = tileset_def.get('spacing', 0)
    firstgid = tileset_def['firstgid']
    name = tileset_def['name']
    
    tiles = []
    
    if len(img.shape) == 2: # Grayscale
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
    elif img.shape[2] == 3: # RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    
    rows = (img.shape[0] - margin) // (tile_height + spacing)
    cols = (img.shape[1] - margin) // (tile_width + spacing)
    expected_count = tileset_def.get('tilecount', rows * cols)
    
    count = 0
    for r in range(rows):
        for c in range(cols):
            if count >= expected_count:
                break
            
            y = margin + r * (tile_height + spacing)
            x = margin + c * (tile_width + spacing)
            
            tile_img = img[y:y+tile_height, x:x+tile_width]
            
            # Normalize alpha to 0-1
            alpha = tile_img[:, :, 3].astype(float) / 255.0
            rgb = tile_img[:, :, :3].astype(float)
            
            tiles.append({
                'gid': firstgid + count,
                'img': tile_img, # Keep original for reference
                'rgb': rgb,
                'alpha': alpha,
                'tileset': name,
                'category': TILE_CATEGORIES.get(name, "overlay")
            })
            count += 1
            
    return tiles

def composite_tile(ground_tile, overlay_tile):
    # Composite overlay on top of ground
    # Result = Ground * (1 - OverlayAlpha) + Overlay * OverlayAlpha
    
    # Expand dims for broadcasting
    alpha = overlay_tile['alpha'][:, :, np.newaxis]
    
    comp = ground_tile['rgb'] * (1.0 - alpha) + overlay_tile['rgb'] * alpha
    return comp

def main():
    parser = argparse.ArgumentParser(description='Reverse engineer Tiled map from image')
    parser.add_argument('input_image', help='Path to input image')
    parser.add_argument('output_json', help='Path to output map.json')
    parser.add_argument('--width', type=int, default=24, help='Target map width in tiles (default: 24)')
    parser.add_argument('--height', type=int, default=24, help='Target map height in tiles (default: 24)')
    
    args = parser.parse_args()

    # Base paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    assets_dir = os.path.join(project_root, 'public', 'assets')
    
    # Load map.json
    map_json_path = os.path.join(assets_dir, 'map.json')
    if not os.path.exists(map_json_path):
        print(f"Error: map.json not found at {map_json_path}")
        sys.exit(1)
        
    with open(map_json_path, 'r') as f:
        map_data = json.load(f)
        
    tilesets_data = map_data['tilesets']
    tile_width = map_data['tilewidth']
    tile_height = map_data['tileheight']
    
    # Load all tiles
    all_tiles = []
    for ts in tilesets_data:
        all_tiles.extend(load_tileset(ts, assets_dir))
        
    print(f"Loaded {len(all_tiles)} tiles.")
    
    # Separate tiles
    ground_tiles = [t for t in all_tiles if t['category'] == 'ground']
    overlay_tiles = [t for t in all_tiles if t['category'] == 'overlay']
    
    # Add an "Empty" overlay tile (fully transparent)
    empty_overlay = {
        'gid': 0,
        'rgb': np.zeros((tile_height, tile_width, 3)),
        'alpha': np.zeros((tile_height, tile_width)),
        'tileset': 'None',
        'category': 'overlay'
    }
    overlay_tiles.insert(0, empty_overlay)
    
    # Ensure we have ground tiles
    if not ground_tiles:
        print("Warning: No ground tiles found. Using all tiles as ground candidates.")
        ground_tiles = all_tiles

    # Load and resize input image
    input_img = cv2.imread(args.input_image, cv2.IMREAD_UNCHANGED)
    if input_img is None:
        print(f"Error: Could not load input image {args.input_image}")
        sys.exit(1)
        
    if input_img.shape[2] == 3:
        input_img = cv2.cvtColor(input_img, cv2.COLOR_BGR2BGRA)
        
    target_w_px = args.width * tile_width
    target_h_px = args.height * tile_height
    
    print(f"Resizing input image from {input_img.shape[1]}x{input_img.shape[0]} to {target_w_px}x{target_h_px}...")
    resized_img = cv2.resize(input_img, (target_w_px, target_h_px), interpolation=cv2.INTER_AREA)
    
    # Convert input to float for comparison
    input_rgb = resized_img[:, :, :3].astype(float)
    
    # Prepare result grids
    cols = args.width
    rows = args.height
    
    result_layers = {
        "water": [0] * (cols * rows),
        "Ground": [0] * (cols * rows),
        "tree": [0] * (cols * rows),
        "Fences": [0] * (cols * rows),
        "Objects": [0] * (cols * rows)
    }
    
    # Heuristic:
    # 1. Iterate over all cells
    # 2. Find best (Ground, Overlay) pair
    
    print("Processing map tiles...")
    
    for r in range(rows):
        for c in range(cols):
            y = r * tile_height
            x = c * tile_width
            
            cell_rgb = input_rgb[y:y+tile_height, x:x+tile_width]
            
            best_error = float('inf')
            best_ground = None
            best_overlay = None
            
            # Optimization: 
            # First find best ground assuming no overlay
            # This works because most tiles are just ground
            # And for tiles with overlay, the visible ground part should still match
            
            # Step 1: Find best ground candidate (top 5)
            ground_candidates = []
            for g_tile in ground_tiles:
                # Diff with pure ground
                diff = np.sum(np.abs(g_tile['rgb'] - cell_rgb))
                ground_candidates.append((diff, g_tile))
            
            ground_candidates.sort(key=lambda x: x[0])
            top_grounds = [x[1] for x in ground_candidates[:5]] # Check top 5 grounds
            
            # Step 2: Try combinations with all overlays
            for g_tile in top_grounds:
                for o_tile in overlay_tiles:
                    # Skip if overlay is empty (already checked in pure ground calculation implicitly? No, we need explicit empty overlay)
                    
                    # Quick check: if overlay is empty, we just use the pre-calculated diff
                    if o_tile['gid'] == 0:
                        comp_rgb = g_tile['rgb']
                    else:
                        comp_rgb = composite_tile(g_tile, o_tile)
                    
                    diff = np.sum(np.abs(comp_rgb - cell_rgb))
                    
                    if diff < best_error:
                        best_error = diff
                        best_ground = g_tile
                        best_overlay = o_tile
                        
            # Assign results
            idx = r * cols + c
            
            if best_ground:
                l_name = LAYER_MAPPING.get(best_ground['tileset'], "Ground")
                result_layers[l_name][idx] = best_ground['gid']
                
            if best_overlay and best_overlay['gid'] != 0:
                l_name = LAYER_MAPPING.get(best_overlay['tileset'], "Objects")
                result_layers[l_name][idx] = best_overlay['gid']

    # Construct output
    output_map = map_data.copy()
    output_map['width'] = cols
    output_map['height'] = rows
    
    new_layers = []
    ordered_names = ["water", "Ground", "tree", "Fences", "Objects"]
    
    # Create layers
    layer_id = 1
    for name in ordered_names:
        layer_data = result_layers.get(name, [0] * (cols * rows))
        new_layers.append({
            "data": layer_data,
            "height": rows,
            "id": layer_id,
            "name": name,
            "opacity": 1,
            "type": "tilelayer",
            "visible": True,
            "width": cols,
            "x": 0,
            "y": 0
        })
        layer_id += 1
        
    output_map['layers'] = new_layers
    
    with open(args.output_json, 'w') as f:
        json.dump(output_map, f, indent=2)
        
    print(f"Done. Map saved to {args.output_json}")

if __name__ == "__main__":
    main()
