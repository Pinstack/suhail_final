import yaml
import requests
from pathlib import Path

SAMPLES_PER_AXIS = 5  # 5x5 grid

provinces = yaml.safe_load((Path('provinces.yaml')).read_text())

for name, meta in provinces.items():
    print(f'\n{name}:')
    bbox = meta['bbox_z15']
    z = 15
    min_x, max_x = bbox['min_x'], bbox['max_x']
    min_y, max_y = bbox['min_y'], bbox['max_y']
    url_template = meta['tile_url_template']
    found = 0
    total = 0
    for i in range(SAMPLES_PER_AXIS):
        for j in range(SAMPLES_PER_AXIS):
            x = int(min_x + (max_x - min_x) * i / (SAMPLES_PER_AXIS - 1))
            y = int(min_y + (max_y - min_y) * j / (SAMPLES_PER_AXIS - 1))
            url = url_template.format(z=z, x=x, y=y)
            try:
                resp = requests.head(url, timeout=5)
                if resp.status_code == 200:
                    print(f'  OK:    {url}')
                    found += 1
                else:
                    print(f'  {resp.status_code}: {url}')
            except Exception as e:
                print(f'  ERR:   {url} ({e})')
            total += 1
    print(f'  Found {found}/{total} tiles (HTTP 200)') 