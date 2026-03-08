import json
import os
import sys
import numpy as np
import cv2

def load_tileset(tileset_def, base_path):
    image_path = os.path.join(base_path, tileset_def['image'])
    # Load image with alpha channel
    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        print(f"Error: Could not load tileset image {image_path}")
        return []

    tile_width = tileset_def['tilewidth']
    tile_height = tileset_def['tileheight']
    margin = tileset_def.get('margin', 0)
    spacing = tileset_def.get('spacing', 0)
    firstgid = tileset_def['firstgid']
    
    tiles = []
    
    rows = (img.shape[0] - margin) // (tile_height + spacing)
    cols = (img.shape[1] - margin) // (tile_width + spacing)
    
    # Calculate expected tile count
    expected_count = tileset_def.get('tilecount', rows * cols)
    
    count = 0
    for r in range(rows):
        for c in range(cols):
            if count >= expected_count:
                break
            
            y = margin + r * (tile_height + spacing)
            x = margin + c * (tile_width + spacing)
            
            tile_img = img[y:y+tile_height, x:x+tile_width]
            tiles.append({
                'gid': firstgid + count,
                'img': tile_img,
                'tileset': tileset_def['name']
            })
            count += 1
            
    return tiles

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 reverse_map.py <input_image_path> <output_json_path>")
        sys.exit(1)

    input_image_path = sys.argv[1]
    output_json_path = sys.argv[2]
    
    # Base paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    assets_dir = os.path.join(project_root, 'public', 'assets')
    
    # Load existing map.json to get tileset definitions
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
        
    print(f"Loaded {len(all_tiles)} tiles from {len(tilesets_data)} tilesets.")
    
    # Load input image
    input_img = cv2.imread(input_image_path, cv2.IMREAD_UNCHANGED)
    if input_img is None:
        print(f"Error: Could not load input image {input_image_path}")
        sys.exit(1)
        
    # Handle alpha channel if input doesn't have it
    if input_img.shape[2] == 3:
        input_img = cv2.cvtColor(input_img, cv2.COLOR_BGR2BGRA)
        
    map_h, map_w, _ = input_img.shape
    cols = map_w // tile_width
    rows = map_h // tile_height
    
    print(f"Map size: {cols}x{rows} tiles")
    
    # Initialize layers
    # We'll use the layers defined in map.json as template if possible, or create standard ones
    # Standard layers based on generate_map.cjs: Ground, Fences, Objects (and maybe Water)
    # Let's try to map to the layers found in map.json
    
    layers_map = {
        "water": {"id": 1, "data": [0] * (cols * rows)},
        "Ground": {"id": 2, "data": [0] * (cols * rows)},
        "tree": {"id": 3, "data": [0] * (cols * rows)}, # Seems to be for trees?
        "Fences": {"id": 4, "data": [0] * (cols * rows)},
        "Objects": {"id": 5, "data": [0] * (cols * rows)},
    }
    
    # Helper to find layer for a tileset
    def get_layer_for_tileset(ts_name):
        if ts_name == "Water": return "water"
        if ts_name == "Grass": return "Ground"
        if ts_name == "Fences": return "Fences"
        if ts_name == "House": return "Objects"
        if ts_name == "Basic_Grass_Biom_things": return "Objects"
        # "tree" layer? Maybe "Basic_Grass_Biom_things" contains trees? 
        # In map.json, layer "tree" (id 8) exists. Let's check what tiles are in it.
        # But for now, let's map to Objects if unsure.
        return "Objects"

    # Default grass GID (pick a random one or fixed one)
    # From map.json, Grass starts at 1. GID 2 is a good candidate.
    DEFAULT_GRASS_GID = 2 
    
    # Process each cell
    for r in range(rows):
        for c in range(cols):
            y = r * tile_height
            x = c * tile_width
            
            cell_img = input_img[y:y+tile_height, x:x+tile_width]
            
            best_match = None
            min_diff = float('inf')
            
            # Optimization: Pre-filter tiles? No, 200 tiles is small enough.
            
            for tile in all_tiles:
                tile_img = tile['img']
                
                # Resize tile if needed (shouldn't be if tileset is correct)
                if tile_img.shape != cell_img.shape:
                    continue
                
                # Compare
                # If tile has transparency, only compare non-transparent pixels?
                # Or just direct difference?
                # If we are matching an overlay (like fence), the input image has Fence+Grass.
                # The tile image has Fence+Transparent.
                # Direct difference will be large on the transparent parts (0 vs GrassColor).
                # So we must use alpha masking for comparison.
                
                # Extract alpha
                tile_alpha = tile_img[:, :, 3] / 255.0
                
                # If tile is fully transparent, skip
                if np.sum(tile_alpha) == 0:
                    continue
                
                # Calculate difference on visible pixels only
                # We want to match the FOREGROUND of the tile to the IMAGE
                # Diff = sum(abs(Tile_RGB - Image_RGB) * Tile_Alpha)
                
                diff = np.sum(np.abs(tile_img[:, :, :3].astype(float) - cell_img[:, :, :3].astype(float)) * tile_alpha[:, :, np.newaxis])
                
                # Normalize by number of visible pixels to avoid bias towards small tiles
                visible_pixels = np.sum(tile_alpha)
                if visible_pixels > 0:
                    score = diff / visible_pixels
                else:
                    score = float('inf')
                
                if score < min_diff:
                    min_diff = score
                    best_match = tile
            
            if best_match:
                idx = r * cols + c
                layer_name = get_layer_for_tileset(best_match['tileset'])
                
                # Assign to specific layer
                if layer_name in layers_map:
                    layers_map[layer_name]["data"][idx] = best_match['gid']
                    
                # Handle under-layers
                if layer_name == "Fences" or layer_name == "Objects" or layer_name == "tree":
                    # Put default grass underneath
                    layers_map["Ground"]["data"][idx] = DEFAULT_GRASS_GID
                elif layer_name == "water":
                    # Ensure ground is empty? Or just let it be 0
                    layers_map["Ground"]["data"][idx] = 0
                elif layer_name == "Ground":
                    # Ensure other layers are empty (already 0)
                    pass

    # Construct output JSON
    output_map = map_data.copy()
    output_map['width'] = cols
    output_map['height'] = rows
    
    # Update layers
    # We need to preserve the order and properties of layers from map.json if possible
    # But we re-generated data.
    
    # Map our generated data back to the layers structure
    # We iterate over existing layers in map_data and update their data
    # If a layer in map_data matches one of our keys, we update it.
    # If a layer is missing in map_data but present in layers_map, we should add it.
    
    existing_layer_names = [l['name'] for l in output_map['layers']]
    
    # Update existing layers
    for layer in output_map['layers']:
        l_name = layer['name']
        if l_name in layers_map:
            layer['data'] = layers_map[l_name]['data']
            layer['width'] = cols
            layer['height'] = rows
            layer['visible'] = True
            layer['opacity'] = 1
        else:
            # Clear data for unknown layers or keep as is?
            layer['data'] = [0] * (cols * rows)
            layer['width'] = cols
            layer['height'] = rows

    # Add missing layers
    # We want a specific order: water, Ground, tree, Fences, Objects
    ordered_layers = ["water", "Ground", "tree", "Fences", "Objects"]
    
    # We need to insert them in the correct order or append?
    # Appending is safer than inserting in arbitrary positions if we don't know the full list
    # But for Tiled, order matters (render order).
    # Let's rebuild the layers list based on our ordered_layers + any others found
    
    new_layers_list = []
    
    # First, try to find existing layers and put them in a dict
    existing_layers_dict = {l['name']: l for l in output_map['layers']}
    
    current_max_id = max([l.get('id', 0) for l in output_map['layers']] + [0])
    
    for l_name in ordered_layers:
        if l_name in existing_layers_dict:
            new_layers_list.append(existing_layers_dict[l_name])
        elif l_name in layers_map:
            # Create new layer
            current_max_id += 1
            new_layer = {
                "data": layers_map[l_name]['data'],
                "height": rows,
                "id": current_max_id,
                "name": l_name,
                "opacity": 1,
                "type": "tilelayer",
                "visible": True,
                "width": cols,
                "x": 0,
                "y": 0
            }
            new_layers_list.append(new_layer)
            
    # Add any other layers that were in the original map but not in our ordered list
    for l_name in existing_layer_names:
        if l_name not in ordered_layers:
            new_layers_list.append(existing_layers_dict[l_name])
            
    output_map['layers'] = new_layers_list

    with open(output_json_path, 'w') as f:
        json.dump(output_map, f, indent=2)
        
    print(f"Successfully generated map at {output_json_path}")

if __name__ == "__main__":
    main()
