#!/usr/bin/env python3
"""候选扩容核验：批量查 star/推送/归档，输出落在 1k–30k 区间的可用项。"""
import json, subprocess, sys

CANDS = [
    # apps
    "element-hq/element-web", "jitsi/jitsi-meet", "cryptomator/cryptomator", "espanso/espanso",
    "micro-editor/micro", "gethomepage/homepage", "blakeblackshear/frigate", "Focalboard/Focalboard",
    "dail8859/NotepadNext", "TriliumNext/Trilium", "wger-project/flutter", "swingmx?" ,
    # cli
    "aristocratos/btop", "fastfetch-cli/fastfetch", "o2sh/onefetch", "XAMPPRocky/tokei",
    "ClementTsang/bottom", "dalance/procs", "gpakosz/.tmux", "cmderdev/cmder", "cheat/cheat",
    # devtools
    "gitbutlerapp/gitbutler", "dbt-labs/dbt-core", "donnemartin/gitsome", "crate-ci/typos",
    "kyrylo?" ,
    # ai
    "huggingface/diffusers", "serengil/deepface", "RVC-Project/Retrieval-based-Voice-Conversion-WebUI",
    "stanford-oval/storm", "chroma-core/chroma", "getzep/graphiti", "ShishirPatil/gorilla",
    "microsoft/UFO",
    # selfhost
    "plausible/analytics", "traccar/traccar", "grocy/grocy", "bunkerity/bunkerweb",
    "openobserve/openobserve", "documenso/documenso", "onionshare/onionshare",
    # data
    "plotly/plotly.js", "vega/vega", "airbnb/visx",
    # web
    "vueuse/vueuse", "TanStack/table", "pmndrs/react-three-fiber", "vercel/ai-chatbot",
    "emotion-js/emotion", "radix-ui/primitives",
    # backend
    "pydantic/pydantic", "encode/django-rest-framework", "aio-libs/aiohttp", "jackc/pgx",
    "spf13/viper", "urfave/cli",
    # devops
    "argoproj/argo-cd", "aquasecurity/trivy", "derailed/k9s", "goharbor/harbor",
    "gruntwork-io/terragrunt", "fluxcd/flux2",
    # privacy
    "signalapp/Signal-Android", "bitwarden/clients", "standardnotes/app", "tutao/tutanota",
    # games / media
    "OpenEmu/OpenEmu", "dolphin-emu/dolphin", "PCSX2/pcsx2", "hrydgard/ppsspp",
    "minetest/minetest", "OpenRCT2/OpenRCT2", "libgdx/libgdx", "hajimehoshi/ebiten",
    "audacity/audacity", " strawberries-org/strawberries",
]
CANDS = [c for c in CANDS if "/" in c and " " not in c and "?" not in c]
FIELDS = "stargazerCount pushedAt isArchived owner{login avatarUrl}"

def gql(batch):
    parts = ", ".join(
        f'r{i}: repository(owner:"{r.split("/")[0]}", name:"{r.split("/")[1]}") {{ {FIELDS} }}'
        for i, r in enumerate(batch))
    q = "query { " + parts + " }"
    out = subprocess.run(["gh", "api", "graphql", "-f", "query=" + q], capture_output=True, text=True)
    if out.returncode != 0:
        return None
    try:
        return json.loads(out.stdout)["data"]
    except Exception:
        return None

results, failed = {}, []
for i in range(0, len(CANDS), 25):
    batch = CANDS[i:i+25]
    data = gql(batch)
    for j, r in enumerate(batch):
        node = (data or {}).get(f"r{j}")
        if not node:
            failed.append(r)
        else:
            results[r] = node

rows = sorted(results.items(), key=lambda kv: -kv[1]["stargazerCount"])
ok = []
for r, d in rows:
    s = d["stargazerCount"]
    tag = "✓" if 1000 <= s <= 30000 and not d["isArchived"] else "✗"
    if tag == "✓": ok.append(r)
    print(f'{tag} {r:<58} {s:>6}  {(d["pushedAt"] or "")[:10]}  arch={d["isArchived"]}')
print(f"\nin-band OK: {len(ok)}  failed: {failed}")
