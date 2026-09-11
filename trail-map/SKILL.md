---
name: trail-map
description: Generate a styled trail map from a GPX file. Clones the map-creator repo if needed, fetches OSM base map data around the GPX track, renders the trail with waypoints on the map, then optionally styles it into a hand-drawn illustration via GPT Image. Use when user says "trail map", "gpx map", "draw my trail", "map from gpx", "render gpx", "hiking map", "running map", or provides a .gpx file and asks for a map.
---

# Trail Map Skill

Generate a beautiful trail map from a GPX file, with optional GPT Image hand-drawn styling.

## Step 0: Ensure map-creator repo exists

```bash
MAP_CREATOR_DIR="${MAP_CREATOR_DIR:-$HOME/dev/3rd-party/map-creator}"
if [ ! -d "$MAP_CREATOR_DIR" ]; then
  echo "Cloning map-creator repo..."
  git clone git@github.com:Hatari130/map-creator.git "$MAP_CREATOR_DIR"
else
  echo "map-creator repo exists at $MAP_CREATOR_DIR"
fi
```

## Step 1: Install dependencies

```bash
/opt/miniconda3/envs/claude-sandbox/bin/pip install osmnx geopandas matplotlib shapely requests python-dotenv 2>&1 | tail -3
```

## Step 2: Identify the GPX file

Ask the user for the GPX file path if not provided. Default search location: `~/Downloads/*.gpx`.

## Step 3: Parse GPX and gather parameters

Extract from the GPX file:
- Track points (lat/lon) from `<trk>/<trkseg>/<trkpt>`
- Waypoints from `<wpt>` elements (name, lat, lon)
- Track bounds (min/max lat/lon) to compute map center and fetch radius
- Creator metadata if available (e.g., COROS, Garmin, Strava)

Ask or infer from user:
- **title**: Map title. Default: derive from GPX `<name>` or filename + city.
- **author**: Author credit. Default: "reachlin 2026" (current year).
- **style**: Whether to run GPT Image styling. Default: yes if OPENAI_API_KEY available.
- **output_dir**: Where to save. Default: `~/Downloads/`.

## Step 4: Generate the base map

Write and run a Python script using `/opt/miniconda3/envs/claude-sandbox/bin/python` that:

1. Parses the GPX file using `xml.etree.ElementTree`
2. Computes map center and fetch radius from track bounds (add 1500m padding)
3. Fetches OSM data via `osmnx`:
   - Road network: `ox.graph_from_point(center, dist=radius, network_type="drive")`
   - Map features: `ox.features_from_point(center, dist=radius, tags={...})` for buildings, parks, water, forests
4. Renders using matplotlib with the map-creator warm paper theme:
   ```python
   THEME = {
       "bg": "#F7F1E7", "building": "#D8CDBA", "park": "#B9C9A6",
       "road_major": "#A98F6D", "road_minor": "#D0B993", "road_tiny": "#E2D1B0",
       "water": "#9BC9D2", "text": "#29241E", "muted": "#766B5D", "panel": "#FFF9ED",
   }
   ```
5. Draws layers in order: water → parks → buildings → roads → trail (red with glow) → waypoints → start/end markers
6. Adds title, distance info, author credit
7. Saves at 230 DPI

**CJK Font handling**: Try `/System/Library/Fonts/STHeiti Medium.ttc` for Chinese text. If not available or text contains CJK characters that won't render, use English labels instead. Never output box characters.

**Waypoint translation** (if using English labels): 水源→Water, 厕所→Restroom, 岔路→Junction, 补给→Aid Station, 起点→Start, 终点→End, 打卡点→Checkpoint.

**Trail styling**:
- Glow layer: trail color with linewidth=5.0, alpha=0.25
- Main line: `#C0392B` crimson, linewidth=2.2, alpha=0.85
- Start marker: green circle. End marker: red square.
- Waypoint markers: dark triangles with labels.

## Step 5: GPT Image styling (optional)

If the user wants styling and `OPENAI_API_KEY` is available in `~/.claude/.env`:

```python
from dotenv import load_dotenv
import os
load_dotenv(os.path.expanduser("~/.claude/.env"))
api_key = os.environ.get("OPENAI_API_KEY")
```

Call the OpenAI Image Edit API:

```python
response = requests.post(
    "https://api.openai.com/v1/images/edits",
    headers={"Authorization": f"Bearer {api_key}"},
    data={"model": "gpt-image-2", "prompt": prompt, "size": "1536x1024"},
    files={"image": (filename, image_file, "image/png")},
    timeout=180,
)
```

The styling prompt should:
- Request hand-drawn illustration / outdoor adventure magazine style
- **Strictly preserve** trail route, waypoint positions, and all text labels
- Request watercolor mountains, paper texture, ink-style roads
- Keep all English labels exactly as shown — do not translate or alter
- Request the author credit be preserved
- Emphasize: accuracy first, then artistic styling

## Step 6: Output

Save both files to the output directory:
- `{name}_trail_map.png` — data-accurate base map
- `{name}_trail_map_styled.png` — GPT Image styled version (if requested)

Show the user the final image(s) using the Read tool.

## Important notes

- The Overpass API (used by osmnx) is free with no API key needed
- For very long trails (>50km), increase the fetch radius but use `network_type="drive"` to keep data manageable
- Adjust figure aspect ratio to match the trail's bounding box shape
- Always lock the matplotlib axis view after drawing roads (osmnx may change limits)
- Cache OSM data when possible to avoid redundant API calls
