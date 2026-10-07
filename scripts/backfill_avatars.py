#!/usr/bin/env python3
"""一次性回填作者头像：为 stars-cache.json 中每个仓库补 owner avatarUrl。"""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_cards import ALL_PROJECTS, CACHE

def main():
    cache = json.load(open(CACHE))
    repos = [p["r"] for p in ALL_PROJECTS if p["r"] in cache and not cache[p["r"]].get("avatar")]
    print(f"backfilling {len(repos)} avatars")
    for i in range(0, len(repos), 50):
        batch = repos[i:i+50]
        parts = ", ".join(
            f'r{j}: repository(owner:"{r.split("/")[0]}", name:"{r.split("/")[1]}") {{ owner {{ avatarUrl }} }}'
            for j, r in enumerate(batch))
        q = "query { " + parts + " }"
        out = subprocess.run(["gh", "api", "graphql", "-f", "query=" + q], capture_output=True, text=True)
        if out.returncode != 0:
            print("batch failed:", out.stderr[:200]); continue
        data = json.loads(out.stdout)["data"]
        for j, r in enumerate(batch):
            node = data.get(f"r{j}")
            if node and node.get("owner", {}).get("avatarUrl"):
                cache[r]["avatar"] = node["owner"]["avatarUrl"]
        print(f"  batch {i//50+1}: done")
    json.dump(cache, open(CACHE, "w"), indent=1)
    have = sum(1 for r in repos if cache.get(r, {}).get("avatar"))
    print(f"avatars filled: {have}/{len(repos)}")

if __name__ == "__main__":
    main()
