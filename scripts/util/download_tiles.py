import aiohttp
import asyncio
import os

TILE_Z = 15
TILE_XS = [20631, 20632, 20633]
TILE_YS = [14060, 14061, 14062]
TILE_URL = "https://tiles.suhail.ai/maps/riyadh/{z}/{x}/{y}.vector.pbf"
SAVE_DIR = "temp_tiles"

os.makedirs(SAVE_DIR, exist_ok=True)

async def fetch_tile(z, x, y):
    url = TILE_URL.format(z=z, x=x, y=y)
    save_path = os.path.join(SAVE_DIR, f"{z}_{x}_{y}.pbf")
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                with open(save_path, "wb") as f:
                    f.write(await resp.read())
                print(f"Downloaded {save_path}")
            else:
                print(f"Failed to download {url} (status {resp.status})")

async def main():
    tasks = [fetch_tile(TILE_Z, x, y) for x in TILE_XS for y in TILE_YS]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main()) 