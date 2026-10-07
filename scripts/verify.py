#!/usr/bin/env python3
"""核验候选项目：star 数 / 最近推送 / 是否归档。GraphQL 批量，50 个/批。"""
import json, subprocess, sys

CANDIDATES = [
    # apps 效率应用（即开即用）
    "ente-io/ente", "paperless-ngx/paperless-ngx", "zadam/trilium", "sissbruecker/linkding",
    "mealie-recipes/mealie", "wallabag/wallabag", "keepassxreboot/keepassxc", "pqrs-org/Karabiner-Elements",
    "Zettlr/Zettlr", "qarmin/czkawka", "lwouis/alt-tab-macos", "oliverschwendener/ueli",
    "Kunzisoft/KeePassDX", "beemdevelopment/Aegis", "kiwix/kiwix-desktop", "dynobo/normcap",
    "flameshot-org/flameshot", "KDE/kdenlive", "mltframework/shotcut", "olive-editor/olive",
    "LMMS/lmms", "mixxxdj/mixxx", "sonic-pi-net/sonic-pi", "VCVRack/Rack", "nukeop/nuclear",
    "zotero/zotero", "filebrowser/filebrowser", "drawdb-io/drawdb",
    # cli 命令行
    "ajeetdsouza/zoxide", "eza-community/eza", "Canop/broot", "bootandy/dust", "chmln/sd",
    "sharkdp/hyperfine", "dandavison/delta", "atuinsh/atuin", "sxyazi/yazi", "zellij-org/zellij",
    "jonas/tig", "casey/just", "jdx/mise", "direnv/direnv", "dbrgn/tealdeer", "dundee/gdu",
    "dlvhdr/gh-dash", "charmbracelet/mods", "sigoden/aichat", "schollz/croc", "mawww/kakoune",
    "wez/wezterm", "rust-lang/mdBook",
    # devtools
    "DevToysHQ/DevToys", "zealdocs/zeal", "mockoon/mockoon", "gitleaks/gitleaks",
    "pre-commit/pre-commit", "bcicen/ctop", "TwiN/gatus", "healthchecks/healthchecks",
    "glitchtip/glitchtip", "jlfwong/speedscope", "usebruno/bruno", "gchq/CyberChef",
    # ai
    "janhq/jan", "LibreTranslate/LibreTranslate", "SYSTRAN/faster-whisper", "rhasspy/piper",
    "SillyTavern/SillyTavern", "ItzCrazyKane/Perplexica", "onyx-dot-app/onyx", "TabbyML/tabby",
    "continuedev/continue", "danny-avila/LibreChat", "activepieces/activepieces",
    "windmill-labs/windmill", "block/goose", "LostRuins/koboldcpp",
    # selfhost
    "navidrome/navidrome", "FreshRSS/FreshRSS", "miniflux/v2", "linkwarden/linkwarden",
    "karakeep-app/karakeep", "go-vikunja/vikunja", "BookStackApp/BookStack", "docmost/docmost",
    "ArchiveBox/ArchiveBox", "haiwen/seafile", "searxng/searxng", "benbusby/whoogle-search",
    "umami-software/umami", "teableio/teable", "baserow/baserow", "Budibase/budibase",
    "goauthentik/authentik", "logto-io/logto", "pomerium/pomerium", "binwiederhier/ntfy",
    # data
    "duckdb/duckdb", "evidence-dev/evidence", "lightdash/lightdash", "questdb/questdb",
    "timescale/timescaledb", "typesense/typesense", "timqian/chart.xkcd", "terrastruct/d2",
    "plantuml/plantuml", "qdrant/qdrant",
    # web 前端与创意编码
    "livewire/livewire", "inertiajs/inertia", "honojs/hono", "elysiajs/elysia", "biomejs/biome",
    "oxc-project/oxc", "rolldown/rolldown", "argyleink/open-props", "roughjs/rough",
    "processing/p5.js", "metafizzy/zdog", "konvajs/konva", "BabylonJS/Babylon.js",
    "11ty/eleventy", "getzola/zola", "withastro/starlight", "shuding/nextra",
    "marp-team/marp", "quarto-dev/quarto", "facebook/stylex",
    # backend
    "litestar-org/litestar", "tiangolo/sqlmodel", "kysely-org/kysely", "sqlc-dev/sqlc",
    "ent/ent", "go-chi/chi", "99designs/gqlgen",
    # devops
    "dokku/dokku", "caprover/caprover", "Dokploy/dokploy", "basecamp/kamal", "opentofu/opentofu",
    "renovatebot/renovate", "containrrr/watchtower", "restic/restic", "borgbackup/borg",
    "kopia/kopia", "89luca89/distrobox", "jetify-com/devbox", "cachix/devenv",
    # design
    "Orama-Interactive/Pixelorama", "opentoonz/opentoonz", "wonderunit/storyboarder",
    "fontforge/fontforge", "GraphiteEditor/Graphite",
    # privacy
    "librewolf-community/librewolf-browser", "philc/vimium", "tridactyl/tridactyl", "ajayyy/SponsorBlock",
    # learn
    "ossu/computer-science", "TeachYourselfCS/teachyourselfcs", "up-for-grabs/up-for-grabs",
    "dair-ai/ML-YouTube-Courses", "dair-ai/prompt-engineering-guide",
    # games
    "Anuken/Mindustry", "veloren/veloren", "00-Evan/shattered-pixel-dungeon", "OpenRA/OpenRA",
    "CleverRaven/CataclysmDDA", "endless-sky/endless-sky", "supertuxkart/stk-code",
    "openttd/OpenTTD", "Heroic-Games-Launcher/HeroicGamesLauncher", "bottlesdevs/Bottles",
    "lutris/lutris", "0ad/0ad",
]

# 清理意外格式
CANDIDATES = [c for c in CANDIDATES if "/" in c and " " not in c]

FIELDS = "stargazerCount pushedAt isArchived description primaryLanguage{name} owner{avatarUrl}"

def fetch_batch(batch):
    parts = ", ".join(
        f'r{i}: repository(owner:"{r.split("/")[0]}", name:"{r.split("/")[1]}") {{ {FIELDS} }}'
        for i, r in enumerate(batch)
    )
    q = f"query {{{ parts }}}"
    out = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={q}"],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        print("gh stderr:", out.stderr[:500], file=sys.stderr)
        raise SystemExit(1)
    return json.loads(out.stdout)["data"]

results, errors = {}, []
def fetch_one(repo):
    o, n = repo.split("/")
    q = f'query {{ repository(owner:"{o}", name:"{n}") {{ {FIELDS} }} }}'
    out = subprocess.run(["gh", "api", "graphql", "-f", f"query={q}"], capture_output=True, text=True)
    if out.returncode != 0:
        return None
    try:
        return json.loads(out.stdout)["data"]["repository"]
    except Exception:
        return None

for i in range(0, len(CANDIDATES), 25):
    batch = CANDIDATES[i:i+25]
    try:
        data = fetch_batch(batch)
    except SystemExit:
        data = None
    if data is None:
        for repo in batch:
            node = fetch_one(repo)
            if node is None:
                errors.append(repo)
            else:
                results[repo] = node
        continue
    for j, repo in enumerate(batch):
        node = data.get(f"r{j}")
        if node is None:
            node = fetch_one(repo)
        if node is None:
            errors.append(repo)
            continue
        results[repo] = node

rows = sorted(results.items(), key=lambda kv: kv[1]["stargazerCount"], reverse=True)
print(f"{'repo':<50} {'stars':>7}  {'pushed':<10} {'arch':<5}")
ok, low, high, dead = 0, [], [], []
for repo, d in rows:
    s = d["stargazerCount"]
    pushed = (d["pushedAt"] or "")[:10]
    arch = "ARCH" if d["isArchived"] else ""
    tag = ""
    if d["isArchived"]:
        dead.append((repo, s)); tag = "✗"
    elif s < 1000:
        low.append((repo, s)); tag = "✗low"
    elif s > 30000:
        high.append((repo, s)); tag = "✗high"
    else:
        ok += 1; tag = "✓"
    print(f"{repo:<50} {s:>7}  {pushed:<10} {arch:<5} {tag}")

print(f"\n✓ in band: {ok} | over 30k: {len(high)} | under 1k: {len(low)} | archived: {len(dead)} | errors: {errors}")
json.dump(results, open("data/stars-cache.json", "w"), indent=1)
print("saved -> data/stars-cache.json")
