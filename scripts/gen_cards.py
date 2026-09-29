#!/usr/bin/env python3
"""GitHub Gems 卡片生成器。

数据唯一来源：本文件 PROJECTS（1k–30k 宝藏）+ LEGENDS（封神榜）数组，合并为 ALL_PROJECTS。流程：
  1. 从 data/stars-cache.json 读 star 数（缺失的仓库自动 gh api 补拉）
  2. 校验：1000 <= stars <= 30000、未归档（不满足直接报错退出）
  3. 生成静态英文卡片 + JSON 数据岛，注入 index.html 的
     <!--GEMS:START/END--> 与 <!--GEMSJSON:START/END--> 标记之间

维护：增删项目只改对应数组 → python3 scripts/gen_cards.py → commit + push。
star 数需要刷新时：rm data/stars-cache.json 再跑（会用 gh 补拉全部）。
"""
import json, os, re, shutil, subprocess, sys
from datetime import date, timezone, datetime

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(HERE, "index.html")
CACHE = os.path.join(HERE, "data", "stars-cache.json")
STATE = os.path.join(HERE, "data", "state.json")   # 毕业记录 {repo: 毕业日期}
GEMS_DIR = os.path.join(HERE, "gems")
SITEMAP = os.path.join(HERE, "sitemap.xml")
BASE = "https://github-gems.kuige.me"
BAND_TOP = int(os.environ.get("GG_BAND_TOP", "30000"))  # 测试可用 GG_BAND_TOP=29000 模拟毕业
BAND = (1000, BAND_TOP)
TODAY = date.today().isoformat()
# 严格模式（人工收录新项目时用）：任何问题直接退出。默认宽松：
# 归档/掉出区间的项目带徽章继续渲染，进巡检报告等人工处理。
STRICT = os.environ.get("GG_STRICT") == "1"

# 这些英文字符串与 index.html JS 里的 L.en 字典保持一致（badge 文案）
EN_GRAD, EN_ARCH, EN_LEGEND = "Graduated", "Archived", "Legend"

# id, n=显示名, r=owner/repo, c=分类, lv=难度(1即开即用/2轻松上手/3开发者向), p=平台, t=搜索标签, de/dz=英/中描述
P = lambda id,n,r,c,lv,p,t,de,dz: dict(id=id,n=n,r=r,c=c,lv=lv,p=p,t=t,de=de,dz=dz)

PROJECTS = [
# ---------- apps 效率与日常 ----------
P("ente","Ente","ente-io/ente","apps",1,"iOS·Android·Win·mac·Linux",["photos","privacy","backup","相册"],
  "End-to-end encrypted photos — a self-hostable Google Photos alternative you truly own.",
  "端到端加密相册服务：照片真正属于你，可自建。"),
P("keepassxc","KeePassXC","keepassxreboot/keepassxc","apps",1,"Win·mac·Linux",["password","security","密码"],
  "Offline password manager: one encrypted file holds all your secrets.",
  "离线密码管理器：一个加密文件装下所有密码。"),
P("karabiner","Karabiner-Elements","pqrs-org/Karabiner-Elements","apps",2,"macOS",["keyboard","remap","键盘"],
  "Remap anything on a macOS keyboard — the power tool every Mac tinkerer ends up installing.",
  "macOS 键盘深度改造：任何按键都能重新定义，Mac 玩家的终点站。"),
P("alttab","AltTab","lwouis/alt-tab-macos","apps",1,"macOS",["window","switcher","窗口"],
  "Gives macOS real Windows-style Alt-Tab window switching. Why did we wait so long?",
  "让 macOS 拥有 Windows 式 Alt-Tab 窗口切换，为何不早点装？"),
P("zotero","Zotero","zotero/zotero","apps",1,"Win·mac·Linux",["research","papers","文献"],
  "The reference manager for research: collect, annotate and cite papers without pain.",
  "科研文献管理神器：收集、标注、引用一条龙。"),
P("zettlr","Zettlr","Zettlr/Zettlr","apps",1,"Win·mac·Linux",["markdown","writing","笔记"],
  "Markdown writing app designed for scholars, theses and very long documents.",
  "为学术写作与长文打造的 Markdown 编辑器。"),
P("ueli","Ueli","oliverschwendener/ueli","apps",1,"Win·mac",["launcher","spotlight","启动器"],
  "Keystroke launcher for Windows & macOS — a free Spotlight that opens anything in 3 keys.",
  "Win/mac 键盘启动器：三下按键打开一切的免费 Spotlight。"),
P("normcap","NormCap","dynobo/normcap","apps",1,"Win·mac·Linux",["ocr","screenshot","截图"],
  "Screenshot → text. Small OCR utility that quietly saves your day, again and again.",
  "截图即取字：小而美的 OCR，一次次悄悄救场。"),
P("kiwix","Kiwix","kiwix/kiwix-desktop","apps",1,"Win·mac·Linux·Android",["offline","wikipedia","离线"],
  "Carry all of Wikipedia (plus many sites) fully offline on a laptop or USB stick.",
  "把整个维基百科离线装进电脑或 U 盘。"),
P("aegis","Aegis","beemdevelopment/Aegis","apps",1,"Android",["2fa","authenticator","两步验证"],
  "2FA app for Android: encrypted, exports openly, backs up — what Google Authenticator should be.",
  "安卓双因素认证应用：加密、可导出、能备份，官方器该有的样子。"),
P("keepassdx","KeePassDX","Kunzisoft/KeePassDX","apps",1,"Android",["password","keepass","密码"],
  "KeePass for Android: manage that one encrypted vault from your phone.",
  "安卓端 KeePass：手机上管理同一个密码库。"),
P("mealie","Mealie","mealie-recipes/mealie","apps",2,"Docker·Web",["recipes","cooking","食谱"],
  "Self-hosted recipe manager with a slick app — your cookbook, backed up forever.",
  "自建食谱管理与膳食规划，体验顺滑的私人菜谱本。"),
P("wallabag","Wallabag","wallabag/wallabag","apps",2,"Web·Docker",["read-later","稍后读"],
  "Self-hosted read-it-later: save articles from the firehose, read them calmly.",
  "自建「稍后读」：把刷到的文章存下来，安静地读完。"),

# ---------- media 影音创作 ----------
P("shotcut","Shotcut","mltframework/shotcut","media",1,"Win·mac·Linux",["video","editor","剪辑"],
  "Full-featured free video editor — no watermark, no paywall, no account.",
  "功能齐全的免费视频剪辑：无水印、无付费墙、无需注册。"),
P("kdenlive","Kdenlive","KDE/kdenlive","media",1,"Win·mac·Linux",["video","editor","剪辑"],
  "Professional open-source video editing from KDE — a serious free Premiere alternative.",
  "KDE 出品的专业开源剪辑软件，认真的免费剪辑选择。"),
P("mixxx","Mixxx","mixxxdj/mixxx","media",1,"Win·mac·Linux",["dj","music","打碟"],
  "Free DJ software that talks to real controllers — mix your first set tonight.",
  "免费 DJ 软件，支持真机打碟控制器，今晚就开工。"),
P("lmms","LMMS","LMMS/lmms","media",1,"Win·mac·Linux",["music","daw","编曲"],
  "Music production workstation: beats, synths, mixing — the free FL Studio.",
  "免费音乐工作站：编曲、合成、混音一体。"),
P("sonicpi","Sonic Pi","sonic-pi-net/sonic-pi","media",2,"Win·mac·Linux·Raspberry Pi",["live-coding","music","音乐"],
  "Live-code music on stage: write Ruby, hear synths. A coding instrument.",
  "用写代码的方式现场演奏音乐——一件真正的编程乐器。"),
P("vcvrack","VCV Rack","VCVRack/Rack","media",2,"Win·mac·Linux",["synth","modular","合成器"],
  "A full Eurorack modular synth in software — patch cables included, soldering not.",
  "软件里的虚拟模块合成器：接线上瘾，无需电烙铁。"),

# ---------- cli 命令行神器 ----------
P("hyperfine","Hyperfine","sharkdp/hyperfine","cli",2,"CLI",["benchmark","性能"],
  "One command to benchmark anything — settle 'which is faster' with numbers.",
  "一行命令做性能对比：用数字终结「到底谁更快」。"),
P("eza","eza","eza-community/eza","cli",2,"CLI",["ls","files","文件"],
  "The modern ls: colors, icons, git status — folders finally look alive.",
  "ls 的现代替身：彩色、图标、Git 状态，目录终于有生气了。"),
P("broot","broot","Canop/broot","cli",2,"CLI·mac·Linux",["tree","navigate","目录"],
  "Navigate huge directory trees interactively — never cd-guess again.",
  "在超大目录树里交互式穿梭，告别瞎猜路径。"),
P("dust","dust","bootandy/dust","cli",2,"CLI",["disk","du","磁盘"],
  "du, but instantly understandable — see what's eating your disk.",
  "直观版 du：一眼看清谁在吃你的硬盘。"),
P("tig","tig","jonas/tig","cli",2,"CLI",["git","history","日志"],
  "Git in the terminal, visually: browse history, stage hunks, chase blame.",
  "终端里的 Git 可视化：翻历史、暂存代码块、追责行。"),
P("direnv","direnv","direnv/direnv","cli",2,"CLI·mac·Linux",["env","dotenv","环境变量"],
  "Per-directory environment variables that load and unload automatically.",
  "进入目录自动加载对应环境变量，离开自动卸载。"),
P("kakoune","Kakoune","mawww/kakoune","cli",3,"CLI·mac·Linux",["editor","vim","编辑器"],
  "Modal editor with selection-first editing — Vim's most interesting rethink.",
  "「先选后改」的模态编辑器：对 Vim 最有意思的一次重新思考。"),
P("tealdeer","tealdeer","dbrgn/tealdeer","cli",2,"CLI",["tldr","docs","手册"],
  "Command examples on demand — tldr pages in milliseconds.",
  "毫秒级返回命令用法示例的 tldr 客户端。"),
P("ghdash","gh-dash","dlvhdr/gh-dash","cli",2,"CLI",["github","pr","看板"],
  "Your GitHub PRs and issues as a terminal dashboard — triage without the browser.",
  "终端里的 GitHub PR/Issue 看板：不开浏览器也能分诊。"),
P("aichat","aichat","sigoden/aichat","cli",2,"CLI",["llm","ai","助手"],
  "All-in-one LLM CLI: chat, roleplay, shell integration, 20+ providers.",
  "命令行 AI 助手：聊天、角色、Shell 集成，20+ 平台通吃。"),
P("sd","sd","chmln/sd","cli",2,"CLI",["sed","replace","替换"],
  "Find & replace for humans — regex without the sed headache.",
  "对人友好的查找替换：告别 sed 的转义地狱。"),
P("wezterm","WezTerm","wez/wezterm","cli",2,"Win·mac·Linux",["terminal","gpu","终端"],
  "GPU-accelerated terminal with Lua scripting — fast, cross-platform, hackable.",
  "GPU 加速 + Lua 可编程的跨平台终端。"),

# ---------- devtools 开发者工具 ----------
P("gitleaks","gitleaks","gitleaks/gitleaks","devtools",3,"CLI·CI",["security","secrets","密钥"],
  "Scan git history for leaked API keys and passwords — before attackers do.",
  "扫描 Git 历史里泄漏的密钥密码，赶在攻击者之前。"),
P("precommit","pre-commit","pre-commit/pre-commit","devtools",3,"CLI",["git","hooks","钩子"],
  "One config, all languages: lint and format automatically before every commit.",
  "一份配置管所有语言：每次提交前自动检查格式。"),
P("mockoon","Mockoon","mockoon/mockoon","devtools",1,"Win·mac·Linux",["api","mock","接口"],
  "Mock API servers in a few clicks — build UIs without waiting for the backend.",
  "点几下就起的本地 Mock API 服务器：不用再等后端。"),
P("zeal","Zeal","zealdocs/zeal","devtools",1,"Win·Linux",["docs","offline","文档"],
  "Offline API documentation for 200+ languages — instant answers on a plane.",
  "离线 API 文档浏览器：飞机上也能秒查 200+ 技术栈文档。"),
P("speedscope","speedscope","jlfwong/speedscope","devtools",1,"Web",["performance","flamegraph","性能"],
  "Drop a profile file, get an interactive flamegraph — profiling made visual.",
  "拖入性能文件，得到可交互火焰图。"),
P("yq","yq","mikefarah/yq","devtools",2,"CLI",["yaml","jq","配置"],
  "yq is for YAML what jq is for JSON: slice, filter, convert everything.",
  "处理 YAML 的 jq：切片、过滤、转换一把梭。"),
P("fx","fx","antonmedv/fx","devtools",2,"CLI",["json","viewer","格式化"],
  "Interactive JSON explorer in the terminal — fold, query, transform.",
  "终端里的交互式 JSON 浏览器：折叠、查询、变换。"),

# ---------- ai AI 与本地模型 ----------
P("llamafile","llamafile","Mozilla-Ocho/llamafile","ai",1,"Win·mac·Linux",["llm","local","本地"],
  "A whole LLM zipped into one executable — download, run, done.",
  "把完整大模型打包进单个可执行文件：下载即用。"),
P("fasterwhisper","faster-whisper","SYSTRAN/faster-whisper","ai",3,"Python",["speech","whisper","语音识别"],
  "Whisper speech recognition, 4× faster with half the memory.",
  "提速 4 倍、省一半内存的 Whisper 语音识别。"),
P("whisperx","whisperX","m-bain/whisperX","ai",3,"Python",["speech","transcribe","字幕"],
  "Whisper plus word-level timestamps and speaker diarization — podcast-ready.",
  "Whisper 加强版：词级时间戳 + 说话人分离，出字幕就靠它。"),
P("funasr","FunASR","modelscope/FunASR","ai",3,"Python",["speech","chinese","中文"],
  "Alibaba's open speech-recognition toolkit — first-class Chinese accuracy.",
  "阿里开源语音识别工具箱：中文效果一流。"),
P("cosyvoice","CosyVoice","FunAudioLLM/CosyVoice","ai",3,"Python",["tts","voice-clone","克隆"],
  "Multi-lingual TTS with zero-shot voice cloning from a few seconds of audio.",
  "多语言语音合成 + 几秒素材即可零样本声音克隆。"),
P("f5tts","F5-TTS","SWivid/F5-TTS","ai",3,"Python",["tts","voice","合成"],
  "A few seconds of reference audio → surprisingly natural cloned speech.",
  "几秒参考音频，克隆出人意料的自然语音。"),
P("edgetts","edge-tts","rany2/edge-tts","ai",3,"Python",["tts","microsoft","合成"],
  "Use Microsoft Edge's online neural voices from Python, for free.",
  "在 Python 里白嫖 Edge 的在线神经网络语音。"),
P("sherpa","sherpa-onnx","k2-fsa/sherpa-onnx","ai",3,"C++·Android·iOS",["speech","offline","端侧"],
  "Speech recognition and TTS running fully offline — from servers to phones.",
  "完全离线的语音识别与合成，从服务器到手机全落地。"),
P("transformersjs","transformers.js","huggingface/transformers.js","ai",3,"JS·Web",["llm","browser","浏览器"],
  "Run Transformer models straight in the browser via WebGPU — no server.",
  "在浏览器里直接跑 Transformer 模型，无需服务器。"),
P("webllm","WebLLM","mlc-ai/web-llm","ai",2,"Web",["llm","browser","本地"],
  "Chat with local LLMs entirely in-browser — private by construction.",
  "纯浏览器内跑大模型对话，天然私密。"),
P("kotaemon","kotaemon","Cinnamon/kotaemon","ai",2,"Web·Docker",["rag","documents","知识库"],
  "A beautiful open RAG UI: chat with your PDFs and docs, locally.",
  "颜值在线的开源 RAG 界面：和本地文档对话。"),
P("invokeai","InvokeAI","invoke-ai/InvokeAI","ai",2,"Win·mac·Linux",["image","diffusion","绘画"],
  "A professional-grade Stable Diffusion studio for serious image work.",
  "专业级 Stable Diffusion 创作工作台。"),
P("forge","SD WebUI Forge","lllyasviel/stable-diffusion-webui-forge","ai",2,"Web",["image","diffusion","绘画"],
  "The WebUI branch that runs bigger models on less VRAM.",
  "更省显存、跑更大模型的 WebUI 分支（ControlNet 作者出品）。"),
P("libretranslate","LibreTranslate","LibreTranslate/LibreTranslate","ai",2,"Docker·API",["translate","翻译"],
  "Self-hosted neural machine translation — your data never leaves the server.",
  "自建神经机器翻译：数据不出门。"),
P("activepieces","Activepieces","activepieces/activepieces","ai",2,"Docker",["automation","zapier","自动化"],
  "Open-source Zapier: connect your apps and automate the boring parts.",
  "开源 Zapier：连接应用，自动化无聊的部分。"),
P("koboldcpp","KoboldCpp","LostRuins/koboldcpp","ai",2,"Win·mac·Linux",["llm","local","本地"],
  "Run local LLMs from a single executable — no install, no ceremony.",
  "单文件本地跑大模型：无需安装，开箱即用。"),

# ---------- selfhost 自托管服务 ----------
P("karakeep","Karakeep","karakeep-app/karakeep","selfhost",2,"Docker·Web",["bookmarks","ai","书签"],
  "AI-assisted bookmark hoarding: save links, get auto-tags and archived snapshots.",
  "AI 书签仓：链接自动打标签、存快照，囤得安心。"),
P("archivebox","ArchiveBox","ArchiveBox/ArchiveBox","selfhost",2,"Docker·CLI",["archive","web","存档"],
  "Your own internet archive — save pages before they vanish.",
  "自建互联网档案馆：在网页消失前存下来。"),
P("linkwarden","Linkwarden","linkwarden/linkwarden","selfhost",2,"Docker·Web",["bookmarks","team","书签"],
  "Collaborative bookmark manager with auto-screenshots and full-page archives.",
  "团队书签管理：自动截图 + 全页存档。"),
P("linkding","linkding","sissbruecker/linkding","selfhost",2,"Docker·Web",["bookmarks","书签"],
  "Minimalist bookmark service — runs happily on a Raspberry Pi.",
  "极简书签服务，树莓派都能愉快运行。"),
P("navidrome","Navidrome","navidrome/navidrome","selfhost",2,"Docker·Web",["music","streaming","音乐"],
  "Your music library becomes a streaming service, from your own server.",
  "把私人音乐库变成自家流媒体服务。"),
P("freshrss","FreshRSS","FreshRSS/FreshRSS","selfhost",2,"Docker·Web",["rss","reader","订阅"],
  "Self-hosted RSS aggregator — the Google Reader successor we deserved.",
  "自建 RSS 聚合器：我们配得上的 Google Reader 继任者。"),
P("miniflux","miniflux","miniflux/v2","selfhost",2,"Docker",["rss","minimalist","订阅"],
  "Opinionated, minimalist RSS server in Go — boring in the best way.",
  "极简主义 RSS 服务：Go 编写，无聊得恰到好处。"),
P("seafile","Seafile","haiwen/seafile","selfhost",2,"Win·mac·Linux·Docker",["files","sync","同步"],
  "Enterprise-grade file sync and sharing — rock-solid reliability.",
  "企业级文件同步共享，稳如老狗。"),
P("docmost","Docmost","docmost/docmost","selfhost",2,"Docker",["wiki","docs","知识库"],
  "Open-source Confluence alternative for team knowledge.",
  "开源 Confluence 替代：团队知识库。"),
P("bookstack","BookStack","BookStackApp/BookStack","selfhost",2,"PHP·Docker",["wiki","books","知识库"],
  "A wiki organized like a bookshelf: books, chapters, pages.",
  "像书架一样组织的 Wiki：书 → 章 → 页。"),
P("teable","Teable","teableio/teable","selfhost",2,"Docker",["database","airtable","表格"],
  "Open-source Airtable: a no-code database with a spreadsheet face.",
  "开源 Airtable：披着表格外衣的数据库。"),
P("budibase","Budibase","Budibase/budibase","selfhost",2,"Docker",["low-code","internal tools","低代码"],
  "Build internal tools and admin panels in minutes, not sprints.",
  "几分钟搭出内部工具与管理后台。"),
P("authentik","authentik","goauthentik/authentik","selfhost",3,"Docker",["sso","login","认证"],
  "Self-hosted single sign-on: one login for every app you run.",
  "自建统一登录（SSO）：一个账号走天下。"),
P("logto","Logto","logto-io/logto","selfhost",3,"Docker",["auth","login","认证"],
  "Developer-friendly auth infra: polished login box plus user management.",
  "为开发者做的认证方案：漂亮登录框 + 用户管理。"),
P("healthchecks","Healthchecks","healthchecks/healthchecks","selfhost",2,"Docker",["cron","monitoring","监控"],
  "A dead-man's switch for cron jobs — ping me, or I alert.",
  "定时任务的死人开关：到点不 ping 就报警。"),
P("windmill","Windmill","windmill-labs/windmill","selfhost",3,"Docker",["workflow","automation","自动化"],
  "Turn scripts into workflows, schedules and internal apps.",
  "把脚本变成工作流、定时任务和内部应用。"),
P("vikunja","Vikunja","go-vikunja/vikunja","selfhost",2,"Docker",["todo","kanban","待办"],
  "Self-hosted todo lists and kanban — migrate from Todoist in one click.",
  "自建待办与看板，一键从 Todoist 迁移。"),
P("librephotos","LibrePhotos","LibrePhotos/librephotos","selfhost",2,"Docker",["photos","ai","相册"],
  "Self-hosted photos with face recognition and auto-organization.",
  "自建相册：人脸识别、自动整理。"),

# ---------- data 数据与可视化 ----------
P("typesense","Typesense","typesense/typesense","data",3,"Docker",["search","engine","搜索"],
  "Typo-tolerant search engine that's up and useful in minutes.",
  "容错搜索引擎：几分钟上手，马上可用。"),
P("timescaledb","TimescaleDB","timescale/timescaledb","data",3,"PostgreSQL",["timeseries","postgres","时序"],
  "Turns PostgreSQL into a time-series powerhouse — keep your SQL.",
  "给 PostgreSQL 装上时序引擎，SQL 原封不动。"),
P("questdb","QuestDB","questdb/questdb","data",3,"Docker",["timeseries","sql","时序"],
  "Blazing-fast open-source time-series database with familiar SQL.",
  "飞快的开源时序数据库，SQL 照写。"),
P("d2","D2","terrastruct/d2","data",3,"CLI·Web",["diagram","architecture","图表"],
  "Text in, beautiful architecture diagrams out — the modern diagramming language.",
  "文字进、架构图出的现代图表语言。"),
P("plantuml","PlantUML","plantuml/plantuml","data",3,"Java·Web",["uml","diagram","图表"],
  "The classic text-to-diagram engine: UML and much more, still undefeated.",
  "经典文本绘图引擎：UML 到流程图，老而弥坚。"),
P("chartxkcd","chart.xkcd","timqian/chart.xkcd","data",3,"JS",["charts","hand-drawn","图表"],
  "Hand-drawn, xkcd-flavored charts — serious data, disarming style.",
  "手绘漫画风图表：严肃数据，亲切画风。"),
P("evidence","Evidence","evidence-dev/evidence","data",3,"JS",["bi","sql","报表"],
  "BI as code: SQL + Markdown compile into a data app.",
  "用代码写 BI：SQL + Markdown 编译成数据应用。"),
P("lightdash","Lightdash","lightdash/lightdash","data",3,"Docker",["bi","dbt","报表"],
  "The BI layer built for dbt — metrics straight from your models.",
  "紧贴 dbt 的 BI 工具：指标直接来自你的模型。"),

# ---------- web 前端与创意编码 ----------
P("babylon","Babylon.js","BabylonJS/Babylon.js","web",3,"JS",["3d","webgpu","游戏"],
  "A powerhouse WebGL/WebGPU 3D engine with a lovely playground.",
  "强大的 WebGL/WebGPU 3D 引擎，附带游乐场。"),
P("p5js","p5.js","processing/p5.js","web",3,"JS",["creative","coding","创意"],
  "Creative coding made friendly — artists write code with it every day.",
  "最友好的创意编程库：艺术家每天都在用它写代码。"),
P("biome","Biome","biomejs/biome","web",3,"JS",["lint","format","格式化"],
  "Lint and format JS/TS in one Rust-powered tool — absurdly fast.",
  "一个 Rust 工具搞定 Lint + 格式化，快得离谱。"),
P("oxc","oxc","oxc-project/oxc","web",3,"Rust",["toolchain","linter","工具链"],
  "A Rust-built JavaScript toolchain: linter, transformer, resolver.",
  "Rust 写的 JS 工具链全家桶。"),
P("rolldown","Rolldown","rolldown/rolldown","web",3,"Rust",["bundler","vite","打包"],
  "The Rust bundler becoming the engine of the next Vite.",
  "将成为下一代 Vite 内核的 Rust 打包器。"),
P("eleventy","Eleventy","11ty/eleventy","web",3,"JS",["ssg","blog","博客"],
  "A simple static site generator with zero framework baggage.",
  "零框架包袱的简洁静态站生成器。"),
P("zola","Zola","getzola/zola","web",3,"Rust",["ssg","blog","博客"],
  "Static sites from a single binary — no Node, no npm, no mess.",
  "单文件静态站生成器：没有 Node，没有 npm，没有烦恼。"),
P("livewire","Laravel Livewire","livewire/livewire","web",3,"PHP",["laravel","dynamic","全栈"],
  "Dynamic Laravel interfaces without writing JavaScript — the full-stack shortcut.",
  "Laravel 全栈捷径：不写 JS 也能做动态页面。"),
P("inertia","Inertia.js","inertiajs/inertia","web",3,"JS",["spa","monolith","单页"],
  "Build SPAs without building an API — the glue you didn't know you wanted.",
  "不写 API 层的单页应用方案：意想不到的胶水。"),
P("elysia","Elysia","elysiajs/elysia","web",3,"TS",["framework","bun","框架"],
  "An ergonomic web framework tuned for Bun — fast and delightful.",
  "为 Bun 量身调校的高性能框架，写着上瘾。"),
P("nextra","Nextra","shuding/nextra","web",3,"JS",["docs","next.js","文档"],
  "The docs/blog framework behind half the sleek Next.js sites you've seen.",
  "你见过的一半精致 Next.js 文档站都是它。"),
P("starlight","Starlight","withastro/starlight","web",3,"JS",["docs","astro","文档"],
  "Astro's docs framework: fast, accessible, i18n-ready out of the box.",
  "Astro 出品文档框架：快、无障碍、自带国际化。"),
P("marp","Marp","marp-team/marp","web",2,"CLI·VSCode",["slides","markdown","幻灯片"],
  "Write slides in Markdown, present anywhere — decks at the speed of thought.",
  "用 Markdown 写幻灯片，想到哪写到哪。"),
P("mdbook","mdBook","rust-lang/mdBook","web",3,"Rust",["book","docs","文档"],
  "Markdown → books and docs sites, from a single binary.",
  "Markdown 变电子书与文档站，单文件搞定。"),
P("konva","Konva","konvajs/konva","web",3,"JS",["canvas","2d","画布"],
  "Declarative canvas: interactive 2D graphics without raw canvas pain.",
  "声明式 Canvas：交互式 2D 图形，告别原生画布之苦。"),
P("openprops","Open Props","argyleink/open-props","web",3,"CSS",["css","variables","设计"],
  "A drawer of supercharged CSS variables — design tokens, ready to use.",
  "现成的 CSS 变量设计令牌抽屉，拿来就用。"),

# ---------- backend 后端与数据库 ----------
P("chi","chi","go-chi/chi","backend",3,"Go",["router","http","路由"],
  "The lightweight Go router that std-net always wanted to be.",
  "轻量 Go 路由器：标准库一直想成为的样子。"),
P("sqlmodel","SQLModel","tiangolo/sqlmodel","backend",3,"Python",["orm","sqlalchemy","数据库"],
  "SQLAlchemy meets Pydantic — type-safe models for FastAPI folks.",
  "SQLAlchemy 遇见 Pydantic：FastAPI 一家的类型安全 ORM。"),
P("sqlc","sqlc","sqlc-dev/sqlc","backend",3,"Go",["sql","typesafe","查询"],
  "Write SQL, get type-safe Go code generated — the compiler checks your queries.",
  "写 SQL，生成类型安全的 Go 代码：编译期帮你查错。"),
P("ent","ent","ent/ent","backend",3,"Go",["orm","graph","数据库"],
  "Facebook's entity framework for Go: schemas as graphs, migrations included.",
  "Facebook 出品的 Go 实体框架：图式建模，迁移齐活。"),
P("kysely","Kysely","kysely-org/kysely","backend",3,"TS",["sql","query","查询"],
  "Type-safe SQL query builder with zero runtime cost.",
  "零运行时开销的类型安全 SQL 构建器。"),
P("gqlgen","gqlgen","99designs/gqlgen","backend",3,"Go",["graphql","api","接口"],
  "Schema-first GraphQL server for Go — codegen does the boring parts.",
  "Schema 优先的 Go GraphQL 服务端：无聊部分交给代码生成。"),
P("litestar","Litestar","litestar-org/litestar","backend",3,"Python",["framework","async","框架"],
  "A fast, thoughtfully async Python web framework.",
  "又快又讲究的异步 Python Web 框架。"),

# ---------- devops 运维与部署 ----------
P("renovate","Renovate","renovatebot/renovate","devops",3,"CI",["dependencies","bot","依赖"],
  "A bot that PRs updates for every outdated dependency — all of them.",
  "依赖更新机器人：每个过时包都自动发 PR。"),
P("kamal","Kamal","basecamp/kamal","devops",3,"CLI",["deploy","paaS","部署"],
  "From 37signals: deploy anything anywhere with one command.",
  "37signals 出品：一条命令把应用部署到任何服务器。"),
P("caprover","CapRover","caprover/caprover","devops",2,"Docker",["paas","deploy","部署"],
  "Your own mini-PaaS: one-click apps, free TLS, web UI.",
  "自建迷你 PaaS：一键装应用、自动 HTTPS、网页管理。"),
P("gatus","Gatus","TwiN/gatus","devops",2,"Docker",["monitoring","health","监控"],
  "A health dashboard for endpoints and cron jobs — if it's down, you know.",
  "端点健康监控面板：一挂就知道。"),
P("kopia","Kopia","kopia/kopia","devops",1,"Win·mac·Linux",["backup","encrypted","备份"],
  "Encrypted, deduplicated, incremental backups with a friendly GUI.",
  "加密去重增量备份，还带友好图形界面。"),
P("borg","BorgBackup","borgbackup/borg","devops",2,"CLI",["backup","dedupe","备份"],
  "The classic deduplicating backup archiver — trusted for a decade.",
  "去重备份老牌选手，十年口碑。"),
P("devbox","Devbox","jetify-com/devbox","devops",2,"CLI",["environment","nix","环境"],
  "Instant, portable dev environments — shell in, project-ready.",
  "秒起可移植开发环境：进 shell 即开工。"),
P("devenv","devenv","cachix/devenv","devops",3,"CLI",["environment","nix","环境"],
  "Fast, declarative dev shells without learning Nix the language.",
  "声明式开发环境：不用先学 Nix 语言。"),
P("distrobox","Distrobox","89luca89/distrobox","devops",2,"Linux",["container","distro","容器"],
  "Use any Linux distro inside your terminal, seamlessly — Ubuntu tools on Arch, no reboot.",
  "在终端里无缝使用任意发行版：Arch 上跑 Ubuntu 工具，无需重启。"),

# ---------- design 设计与图标 ----------
P("graphite","Graphite","GraphiteEditor/Graphite","design",1,"Web",["graphics","procedural","节点"],
  "A procedural, node-based graphics editor that runs in your browser.",
  "浏览器里的程序化节点图形编辑器，设计师的游乐场。"),
P("tabler","Tabler Icons","tabler/tabler-icons","design",1,"Web·SVG",["icons","ui","图标"],
  "5,000+ free MIT icons in one consistent style — the quiet workhorse of UI.",
  "近五千枚 MIT 开源图标：风格统一的 UI 无名功臣。"),
P("lucide","Lucide","lucide-icons/lucide","design",1,"Web·SVG",["icons","ui","图标"],
  "The beautifully consistent icon set half the web quietly uses.",
  "半个互联网都在悄悄用的图标库。"),
P("iconify","Iconify","iconify/iconify","design",2,"Web·JS",["icons","framework","图标"],
  "One framework, 200,000+ icons from every major set.",
  "一个框架装下 20 万+ 枚图标，主流图标集全都在。"),
P("svgo","SVGO","svg/svgo","design",3,"CLI·JS",["svg","optimize","优化"],
  "Squeezes SVG files smaller without losing quality.",
  "SVG 瘦身优化器：去掉字节，不掉质量。"),
P("pixelorama","Pixelorama","Orama-Interactive/Pixelorama","design",1,"Win·mac·Linux",["pixel-art","drawing","像素"],
  "A polished free pixel-art editor built with Godot.",
  "Godot 打造的免费像素画编辑器，打磨精细。"),
P("opentoonz","OpenToonz","opentoonz/opentoonz","design",1,"Win·mac·Linux",["animation","2d","动画"],
  "2D animation software with studio pedigree — Ghibli's toolchain cousin.",
  "有吉卜力背景的 2D 动画软件，专业血统。"),
P("fontforge","FontForge","fontforge/fontforge","design",2,"Win·mac·Linux",["font","typeface","字体"],
  "The open-source font editor — design your own typeface from scratch.",
  "开源字体设计软件：从零造一款自己的字体。"),

# ---------- privacy 隐私与安全 ----------
P("vimium","Vimium","philc/vimium","privacy",1,"Chrome",["vim","keyboard","键盘"],
  "Vim keys in your browser — navigate the web without touching the mouse.",
  "浏览器里的 Vim 键位：全程不碰鼠标上网。"),
P("tridactyl","Tridactyl","tridactyl/tridactyl","privacy",1,"Firefox",["vim","keyboard","键盘"],
  "Vim bindings for Firefox, deeply hackable.",
  "Firefox 的 Vim 键位，深度可魔改。"),
P("sponsorblock","SponsorBlock","ajayyy/SponsorBlock","privacy",1,"Chrome·Firefox",["youtube","sponsor","跳过"],
  "Crowd-sourced timestamps that auto-skip YouTube sponsor segments.",
  "全网共建时间戳，自动跳过 YouTube 赞助广告段。"),
P("adguard","AdGuard extension","AdguardTeam/AdGuardBrowserExtension","privacy",1,"Chrome·Firefox",["ads","blocker","广告"],
  "The open-source AdGuard extension — no 'acceptable ads' deals.",
  "开源广告过滤扩展：没有「可接受广告」的交易。"),
P("privacybadger","Privacy Badger","EFForg/privacybadger","privacy",1,"Chrome·Firefox",["tracking","eff","追踪"],
  "EFF's tracker blocker that learns as you browse.",
  "电子前哨基金会出品：边浏览边学会反追踪。"),
P("pomerium","Pomerium","pomerium/pomerium","privacy",3,"Docker",["zero-trust","proxy","零信任"],
  "Identity-aware proxy: zero-trust access to your internal apps.",
  "身份感知代理：零信任访问内部应用。"),

# ---------- games 游戏与娱乐 ----------
P("mindustry","Mindustry","Anuken/Mindustry","games",1,"Win·mac·Linux",["factory","rts","塔防"],
  "Factory towers + RTS + deep modding — the strategy game you sink 200 hours into.",
  "工厂+塔防+RTS：一进去就是 200 小时的策略游戏。"),
P("openra","OpenRA","OpenRA/OpenRA","games",1,"Win·mac·Linux",["rts","red-alert","红警"],
  "Command & Conquer and Red Alert, rebuilt modern and cross-platform.",
  "红色警戒等经典 RTS 的现代化重制。"),
P("cataclysm","Cataclysm DDA","CleverRaven/Cataclysm-DDA","games",1,"Win·mac·Linux",["roguelike","survival","生存"],
  "The deepest survival roguelike ever made — infinitely replayable.",
  "深度无可比拟的末日生存 Roguelike。"),
P("heroic","Heroic","Heroic-Games-Launcher/HeroicGamesLauncher","games",1,"Win·mac·Linux",["games","epic","启动器"],
  "Epic, GOG and Amazon games in one clean launcher.",
  "Epic/GOG/亚马逊游戏，一个启动器全搞定。"),
P("lutris","Lutris","lutris/lutris","games",1,"Linux",["games","launcher","启动器"],
  "The one launcher that keeps Linux gaming organized.",
  "Linux 游戏的大管家。"),
P("bottles","Bottles","bottlesdevs/Bottles","games",1,"Linux",["wine","windows","兼容"],
  "Run Windows apps and games on Linux through tidy, managed bottles.",
  "Linux 上优雅运行 Windows 程序与游戏。"),
P("veloren","Veloren","veloren/veloren","games",1,"Win·mac·Linux",["rpg","voxel","体素"],
  "A community-built multiplayer voxel RPG — open-source Zelda energy.",
  "社区开发的多人体素 RPG：开源塞尔传说。"),
P("endlesssky","Endless Sky","endless-sky/endless-sky","games",1,"Win·mac·Linux",["space","trading","太空"],
  "Trade and fight across the galaxy — the Escape Velocity spirit, alive.",
  "银河贸易与战斗：经典精神续作，仍在生长。"),
P("openttd","OpenTTD","openttd/OpenTTD","games",1,"Win·mac·Linux",["tycoon","transport","运输"],
  "The transport-empire tycoon, 20+ years strong and still shipping.",
  "运输大亨开源版：二十年常青，仍在更新。"),
P("spd","Shattered Pixel Dungeon","00-Evan/shattered-pixel-dungeon","games",1,"Android·iOS·Desktop",["roguelike","pixel","像素"],
  "A roguelike polished to a mirror shine that fits in your pocket.",
  "打磨到发亮的口袋 Roguelike。"),
P("stk","SuperTuxKart","supertuxkart/stk-code","games",1,"Win·mac·Linux",["racing","kart","赛车"],
  "A mascot kart racer with actual online multiplayer.",
  "吉祥物卡丁车竞速，还带联机。"),
]

# ---------- 封神榜：耳熟能详的殿堂级项目 ----------
# 与宝藏的差异只在 tier="L"：不做 1k–30k 区间校验、不参与毕业，走同一套核验/巡检/落地页管道
LEGENDS = [
P("vscode","VS Code","microsoft/vscode","apps",1,"Win·mac·Linux",["editor","ide","编辑器"],
  "The world's default code editor: free, fast, endlessly extensible.",
  "全球默认的代码编辑器：免费、快、扩展无穷。"),
P("obs","OBS Studio","obsproject/obs-studio","apps",1,"Win·mac·Linux",["streaming","recording","录屏"],
  "The standard for streaming and screen recording, on every platform.",
  "直播与录屏的事实标准，全平台通用。"),
P("ffmpeg","FFmpeg","FFmpeg/FFmpeg","media",2,"Win·mac·Linux",["video","encoding","转码"],
  "The engine behind nearly every video player, converter and stream you've used.",
  "你用过的几乎所有播放器、转码器背后的引擎。"),
P("fzf","fzf","junegunn/fzf","cli",2,"CLI·mac·Linux",["fuzzy","search","搜索"],
  "Fuzzy-find anything: history, files, branches — one keystroke away.",
  "万能模糊搜索：历史、文件、分支，一键即达。"),
P("ripgrep","ripgrep","BurntSushi/ripgrep","cli",2,"CLI",["grep","search","文本搜索"],
  "grep rebuilt in Rust: far faster, smarter defaults, respects .gitignore.",
  "Rust 重写的 grep：快得多、默认更聪明、自动尊重 .gitignore。"),
P("ohmyzsh","Oh My Zsh","ohmyzsh/ohmyzsh","cli",2,"macOS·Linux",["zsh","shell","终端"],
  "The zsh framework behind a decade of beautiful terminals.",
  "十年来源亮终端背后的 zsh 框架。"),
P("git","Git","git/git","devtools",3,"C·CLI",["vcs","scm","版本控制"],
  "The version-control system the whole industry runs on (official mirror).",
  "全行业在用的版本控制系统（官方镜像）。"),
P("prettier","Prettier","prettier/prettier","devtools",3,"JS·CLI",["format","style","格式化"],
  "The opinionated formatter that ended every code-style argument.",
  "有主见的代码格式化器，终结所有风格争论。"),
P("transformers","Transformers","huggingface/transformers","ai",3,"Python",["llm","models","模型"],
  "The library behind modern AI: one API for hundreds of thousands of models.",
  "现代 AI 背后的库：一个 API 调用海量模型。"),
P("ollama","Ollama","ollama/ollama","ai",1,"Win·mac·Linux",["llm","local","本地"],
  "One command to run any open model locally — local AI's front door.",
  "一条命令本地跑任意开源模型，本地 AI 的入口。"),
P("pytorch","PyTorch","pytorch/pytorch","ai",3,"Python·C++",["deep-learning","框架"],
  "The deep-learning framework most AI research is written in.",
  "大部分 AI 研究所用的深度学习框架。"),
P("homeassistant","Home Assistant","home-assistant/core","selfhost",2,"Python·Docker",["smart-home","iot","智能家居"],
  "The local-first smart home hub that answers to no vendor.",
  "本地优先、不听命于任何厂商的智能家居中枢。"),
P("mermaid","Mermaid","mermaid-js/mermaid","data",3,"JS",["diagram","flowchart","图表"],
  "Diagrams as code: flowcharts from plain text, rendered everywhere.",
  "图表即代码：纯文本变流程图，处处可渲染。"),
P("echarts","Apache ECharts","apache/echarts","data",3,"JS·Web",["charts","visualization","可视化"],
  "Born at Baidu, now a global visualization standard under Apache.",
  "出自百度，现已是 Apache 旗下的全球可视化标准。"),
P("react","React","facebook/react","web",3,"JS",["ui","frontend","前端"],
  "The UI library that reshaped how every interface gets built.",
  "重塑了所有界面构建方式的 UI 库。"),
P("vue","Vue.js","vuejs/vue","web",3,"JS",["ui","frontend","前端"],
  "The progressive framework beloved for gentle ramps and first-class docs.",
  "渐进式框架：上手平缓、文档一流。"),
P("tailwind","Tailwind CSS","tailwindlabs/tailwindcss","web",3,"CSS",["styling","utility","样式"],
  "Utility-first CSS that changed how teams style the web.",
  "原子化 CSS：改变了团队给网页写样式的方式。"),
P("vite","Vite","vitejs/vite","web",3,"TS",["bundler","dev-server","构建"],
  "The dev server that made frontend tooling feel instant.",
  "让前端工具链重新变快的开发服务器。"),
P("redis","Redis","redis/redis","backend",3,"C",["database","cache","缓存"],
  "The in-memory data store behind a decade of real-time everything.",
  "撑起十年实时业务的内存数据库。"),
P("kubernetes","Kubernetes","kubernetes/kubernetes","devops",3,"Go",["containers","orchestration","容器"],
  "The container orchestrator that became the cloud's operating system.",
  "容器编排的事实标准：云时代的操作系统。"),
P("ansible","Ansible","ansible/ansible","devops",3,"Python",["automation","iac","自动化"],
  "Agentless automation that turned server config into readable YAML.",
  "无代理自动化：服务器配置变成可读的 YAML。"),
P("linux","Linux kernel","torvalds/linux","devops",3,"C",["kernel","os","内核"],
  "The kernel running most of the internet, Android and the supercomputers (mirror).",
  "运行着大半互联网、Android 和超算的内核（镜像）。"),
P("fontawesome","Font Awesome","FortAwesome/Font-Awesome","design",1,"Web·SVG",["icons","font","图标"],
  "The icon set that has armed two decades of the web.",
  "武装了二十年互联网的图标库。"),
P("godot","Godot","godotengine/godot","games",2,"C++·All platforms",["engine","gamedev","游戏引擎"],
  "The open game engine behind a wave of indie hits — entirely yours to modify.",
  "一批独立爆款背后的开源游戏引擎，完全可魔改。"),
]
for _p in LEGENDS: _p["tier"] = "L"
ALL_PROJECTS = PROJECTS + LEGENDS

CATS = {
 "apps":("🧰","Everyday Apps","效率与日常"), "media":("🎬","Photo · Audio · Video","影音创作"),
 "cli":("⌨️","Terminal Gems","命令行神器"), "devtools":("🛠️","Developer Tools","开发者工具"),
 "ai":("🤖","AI & Local Models","AI 与本地模型"), "selfhost":("🏠","Self-Hosted","自托管服务"),
 "data":("📊","Data & Viz","数据与可视化"), "web":("🌐","Frontend & Creative","前端与创意编码"),
 "backend":("⚙️","Backend & Databases","后端与数据库"), "devops":("🚀","DevOps & Deploy","运维与部署"),
 "design":("🖌️","Design & Icons","设计与图标"), "privacy":("🔐","Privacy & Security","隐私与安全"),
 "games":("🎮","Games & Fun","游戏与娱乐"),
}
LVS = {1:"Ready to use", 2:"Easy setup", 3:"For developers"}

def load_cache():
    if os.path.exists(CACHE):
        return json.load(open(CACHE))
    return {}

def fetch_repo(repo, cache):
    out = subprocess.run(["gh","api",f"repos/{repo}"], capture_output=True, text=True)
    if out.returncode != 0:
        print(f"  !! gh api failed for {repo}: {out.stderr[:120]}")
        return None
    d = json.loads(out.stdout)
    node = {"stargazerCount": d["stargazers_count"], "pushedAt": d["pushed_at"],
            "isArchived": d["archived"], "description": d.get("description")}
    cache[repo] = node
    return node

def fmt_k(n):
    if n >= 1000000:
        v = round(n/1000000, 1)
        return (f"{v:.1f}".rstrip("0").rstrip(".")) + "M"
    if n >= 10000: return f"{round(n/1000)}k"
    if n >= 1000:
        v = round(n/1000, 1)
        return (f"{v:.1f}".rstrip("0").rstrip(".")) + "k"
    return str(n)

GEM_CSS = """
:root{--bg:#f7f7fb;--bg2:#fff;--fg:#191927;--fg2:#5b5b70;--line:#e4e4ef;--acc:#7c3aed;--acc2:#0ea5e9;
--chip:#efeafd;--card:#fff;--shadow:0 1px 3px rgba(25,25,40,.07),0 8px 24px rgba(25,25,40,.06);
--glowA:rgba(124,58,237,.16);--good:#16a34a;--warn:#d97706}
html[data-theme=dark]{--bg:#0d0d14;--bg2:#14141d;--fg:#ececf5;--fg2:#9d9db3;--line:#262636;--acc:#a78bfa;
--acc2:#38bdf8;--chip:#1d1d2b;--card:#15151f;--shadow:0 1px 3px rgba(0,0,0,.5),0 10px 30px rgba(0,0,0,.35);
--glowA:rgba(167,139,250,.13);--good:#4ade80;--warn:#fbbf24}
*{box-sizing:border-box}body{margin:0;font:16px/1.7 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--fg);-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}.wrap{max-width:760px;margin:0 auto;padding:0 20px}
header{border-bottom:1px solid var(--line)}.hbar{display:flex;align-items:center;gap:12px;height:56px}
.brand{font-weight:800;font-size:17px}.hbar .sp{flex:1}
.hbtn{border:1px solid var(--line);background:var(--bg2);color:var(--fg);border-radius:9px;padding:6px 12px;font-size:13px;font-weight:600;cursor:pointer}
.crumb{color:var(--fg2);font-size:13.5px;margin:26px 0 10px}.crumb a:hover{color:var(--acc)}
h1{font-size:34px;letter-spacing:-.02em;margin:0 0 10px;display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}
h1 .st{color:var(--warn);font-size:18px}
.badges{display:flex;gap:7px;flex-wrap:wrap;margin:0 0 18px}
.badge{font-size:12px;font-weight:700;border-radius:7px;padding:3px 9px;background:var(--chip);color:var(--fg2)}
.badge.cat{color:var(--acc)}.badge.b1{background:color-mix(in srgb,#16a34a 14%,transparent);color:var(--good)}
.badge.b2{background:color-mix(in srgb,#d97706 15%,transparent);color:var(--warn)}
.badge.b3{background:color-mix(in srgb,#7c3aed 13%,transparent);color:var(--acc)}
.badge.grad{background:color-mix(in srgb,#d97706 15%,transparent);color:var(--warn)}
.badge.arch{background:color-mix(in srgb,#dc2626 13%,transparent);color:#dc2626}
.badge.legend{background:color-mix(in srgb,#f59e0b 16%,transparent);color:#f59e0b}
.lead{font-size:19px;line-height:1.6;margin:0 0 14px}
.extra{color:var(--fg2);font-size:14.5px;margin:0 0 10px}
.vline{color:var(--fg2);font-size:13px;margin:0 0 24px}.vline b{color:var(--fg)}
.btns{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:40px}
.bigbtn{display:inline-flex;align-items:center;gap:8px;background:linear-gradient(120deg,var(--acc),var(--acc2));color:#fff;border-radius:12px;padding:12px 20px;font-size:15px;font-weight:700;box-shadow:0 6px 20px var(--glowA)}
.ghost{display:inline-flex;align-items:center;border:1px solid var(--line);border-radius:12px;padding:12px 18px;font-size:14px;font-weight:600;color:var(--fg2)}
.ghost:hover{border-color:var(--acc);color:var(--acc)}
h2{font-size:20px;letter-spacing:-.01em;margin:0 0 16px}
.minis{display:grid;grid-template-columns:1fr 1fr;gap:10px;padding-bottom:40px}
@media(max-width:640px){.minis{grid-template-columns:1fr}}
.mini{display:block;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px;transition:.15s}
.mini:hover{transform:translateY(-2px);border-color:var(--acc)}
.mrow{display:flex;align-items:baseline;gap:8px}.mn{font-weight:700;font-size:14.5px}.ms{margin-left:auto;color:var(--warn);font-size:12px;font-weight:700}
.md{display:block;color:var(--fg2);font-size:13px;margin-top:3px}
footer{border-top:1px solid var(--line);margin-top:20px;padding:22px 0 36px;color:var(--fg2);font-size:13px}
footer a{color:var(--acc);font-weight:600}
.brand .blogo{width:28px;height:28px;border-radius:8px;display:block;border:1px solid var(--line)}
.fscard{position:fixed;left:18px;bottom:18px;z-index:70;width:62px;height:62px;padding:0;border:1px solid var(--line);border-radius:16px;background:var(--bg2);box-shadow:0 10px 30px rgba(0,0,0,.25);cursor:pointer;transition:.18s}
.fscard img{width:100%;height:100%;border-radius:15px;display:block}
.fscard:hover{transform:translateY(-4px);border-color:var(--acc)}
.fsmodal{position:fixed;inset:0;z-index:90;display:flex;align-items:center;justify-content:center;padding:20px}
.fsmodal[hidden]{display:none}
.fsback{position:absolute;inset:0;background:rgba(10,10,18,.55);backdrop-filter:blur(6px)}
.fsbox{position:relative;max-width:470px;width:100%;background:var(--bg2);border:1px solid var(--line);border-radius:20px;padding:26px 26px 24px;box-shadow:0 24px 70px rgba(0,0,0,.4);animation:fsin .22s ease}
@keyframes fsin{from{opacity:0;transform:translateY(14px) scale(.97)}to{opacity:1;transform:none}}
.fsx{position:absolute;top:10px;right:12px;border:none;background:none;color:var(--fg2);font-size:26px;cursor:pointer;line-height:1}
.fsavatar{width:88px;height:88px;border-radius:20px;display:block;margin:0 auto 12px;border:1px solid var(--line)}
.fsbox h3{margin:0 0 2px;font-size:19px;text-align:center;letter-spacing:-.01em}
.fsname{text-align:center;color:var(--acc);font-weight:700;font-size:13px;margin:0 0 14px}
.fsbox p{color:var(--fg2);font-size:14px;line-height:1.75;margin:0 0 12px}
.fsbtns{display:flex;gap:10px;margin-top:16px}
.fsbtns a{flex:1;display:flex;align-items:center;justify-content:center;gap:8px;border-radius:12px;padding:12px 14px;font-weight:700;font-size:14px;transition:.15s;white-space:nowrap}
.fsfollow{background:#0f1419;color:#fff;border:1px solid #0f1419}
html[data-theme=dark] .fsfollow{background:#e7e9ea;color:#0f1419;border-color:#e7e9ea}
.fsdiscuss{border:1px solid var(--line);color:var(--fg);background:var(--bg)}
.fsdiscuss:hover{border-color:var(--acc);color:var(--acc)}
.fsfollow:hover{transform:translateY(-2px);opacity:.92}
"""

GEM_TPL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__TITLE__</title>
<meta name="description" content="__DESC__">
<link rel="canonical" href="__BASE__/gems/__ID__.html">
<link rel="alternate" hreflang="en" href="__BASE__/gems/__ID__.html?lang=en">
<link rel="alternate" hreflang="zh" href="__BASE__/gems/__ID__.html?lang=zh">
<link rel="alternate" hreflang="x-default" href="__BASE__/gems/__ID__.html">
<link rel="icon" type="image/png" href="../favicon.png">
<meta property="og:type" content="website">
<meta property="og:site_name" content="GitHub Gems">
<meta property="og:title" content="__NAME__ — GitHub Gem">
<meta property="og:description" content="__DE__">
<meta property="og:url" content="__BASE__/gems/__ID__.html">
<meta property="og:image" content="__BASE__/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="__NAME__ — GitHub Gem">
<meta name="twitter:description" content="__DE__">
<meta name="twitter:image" content="__BASE__/og-image.png">
<script type="application/ld+json">__JSONLD__</script>
<style>__CSS__</style>
</head>
<body>
<header><div class="wrap hbar">
<a class="brand" href="../index.html"><img class="blogo" src="../fengshen.webp" alt="封神传说">GitHub Gems</a><span class="sp"></span>
<button class="hbtn" id="btnTheme">🌗 Theme</button>
<button class="hbtn" id="btnLang">中文</button>
</div></header>
<main class="wrap">
<p class="crumb"><a href="../index.html" data-en="All gems" data-zh="全部宝藏">All gems</a> / <a href="../index.html?c=__CATID__" data-en="__CATEN__" data-zh="__CATZH__">__CATEN__</a> / __NAME__</p>
<h1>__NAME__ <span class="st">★ __STARSK__</span></h1>
<div class="badges">
<span class="badge cat">__CATICON__ <span data-en="__CATEN__" data-zh="__CATZH__">__CATEN__</span></span>
<span class="badge __LVCLS__" data-en="__LVEN__" data-zh="__LVZH__">__LVEN__</span>
<span class="badge">__PLAT__</span>__BADGES__
</div>
<p class="lead" data-en="__DE__" data-zh="__DZ__">__DE__</p>
<p class="extra" data-en="__EXTRA_EN__" data-zh="__EXTRA_ZH__">__EXTRA_EN__</p>
<p class="vline"><span data-en="Star count live-verified" data-zh="star 数实测核验">Star count live-verified</span> <b>__DATE__</b> · <span data-en="repo" data-zh="仓库">repo</span> <b>__REPO__</b></p>
<div class="btns">
<a class="bigbtn" href="https://github.com/__REPO__" target="_blank" rel="noopener">★ GitHub ↗</a>
<a class="ghost" href="../index.html" data-en="← All gems" data-zh="← 全部宝藏">← All gems</a>
</div>
<h2 data-en="More in __CATEN__" data-zh="更多「__CATZH__」宝藏">More in __CATEN__</h2>
<div class="minis">__RELATED__</div>
</main>
<button class="fscard" id="fsCard" aria-label="Fengshen Legend" title="封神传说">
<img src="../fengshen.webp" alt="封神传说">
</button>
<div class="fsmodal" id="fsModal" hidden>
<div class="fsback"></div>
<div class="fsbox" role="dialog" aria-modal="true">
<button class="fsx" id="fsClose" aria-label="Close">×</button>
<img class="fsavatar" src="../fengshen.webp" alt="封神传说">
<h3><span data-en="The legend behind this site" data-zh="这个网站的故事">The legend behind this site</span></h3>
<p class="fsname">封神传说 · Fengshen Legend</p>
<p data-en="GitHub Gems (codename 封神传说 — Investiture of the Gods) is a hand-curated discovery directory for open source: 💎 137 hidden gems live-verified from GitHub's 1k–30k star sweet spot, and 🏆 24 legendary projects as landmarks. Every star count is checked against the GitHub API — nothing guessed." data-zh="GitHub Gems（代号「封神传说」）是一个人工精选的开源发现站：💎 137 个实测核验的 1k–30k star 冷门宝藏，🏆 24 个殿堂级封神之作作为路标。所有 star 数均经 GitHub API 实测，拒绝道听途说。">GitHub Gems (codename 封神传说 — Investiture of the Gods) is a hand-curated discovery directory for open source: 💎 137 hidden gems live-verified from GitHub's 1k–30k star sweet spot, and 🏆 24 legendary projects as landmarks. Every star count is checked against the GitHub API — nothing guessed.</p>
<p data-en="In the Chinese classic Investiture of the Gods, the sage Jiang Ziya fishes with a straight hook — not for fish, but for the worthy, whose names he writes onto the list that makes them immortal. That is our metaphor: underrated gems get seen, great works get crowned. A star is not the end; being discovered is." data-zh="《封神演义》里，姜子牙直钩垂钓——钓的不是鱼，是值得封神的人，然后把他们一一写上封神榜。这就是我们的寓意：让被低估的宝藏被看见，让传世之作加冕。star 不是终点，被发现才是。">In the Chinese classic Investiture of the Gods, the sage Jiang Ziya fishes with a straight hook — not for fish, but for the worthy, whose names he writes onto the list that makes them immortal. That is our metaphor: underrated gems get seen, great works get crowned. A star is not the end; being discovered is.</p>
<div class="fsbtns">
<a class="fsfollow" href="https://x.com/kuige_me" target="_blank" rel="noopener">𝕏 <span data-en="Follow me on X" data-zh="去 X 上关注我">Follow me on X</span></a>
<a class="fsdiscuss" href="https://x.com/kuige_me/status/2104877134682398724" target="_blank" rel="noopener">💬 <span data-en="Join the discussion" data-zh="去讨论">Join the discussion</span></a>
</div>
</div>
</div>

<footer><div class="wrap"><span data-en="Hand-picked underrated open-source projects. Stars live-verified." data-zh="人工精选的冷门优质开源项目，star 数实测核验。">Hand-picked underrated open-source projects. Stars live-verified.</span></div></footer>
<script type='module' src='https://static.cloudflareinsights.com/beacon.min.js' data-cf-beacon='{"token": "948f2535a9dd4775a436c677b3c950e4"}'></script>
<script type="module">
const TITLE_EN = __TITLE_EN_JSON__, TITLE_ZH = __TITLE_ZH_JSON__;
let lang = new URLSearchParams(location.search).get('lang') || localStorage.getItem('gg-lang') || 'en';
const apply = () => {
  document.documentElement.lang = lang;
  document.querySelectorAll('[data-en]').forEach(el => { el.textContent = lang === 'zh' ? el.dataset.zh : el.dataset.en; });
  document.title = lang === 'zh' ? TITLE_ZH : TITLE_EN;
  document.getElementById('btnLang').textContent = lang === 'zh' ? 'EN' : '中文';
  const u = new URL(location.href); u.searchParams.delete('lang');
  if (lang === 'zh') u.searchParams.set('lang', 'zh');
  history.replaceState(null, '', u.pathname + (u.search || '') + location.hash);
};
document.getElementById('btnLang').onclick = () => { lang = lang === 'zh' ? 'en' : 'zh'; localStorage.setItem('gg-lang', lang); apply(); };
const cycle = () => {
  const cur = document.documentElement.getAttribute('data-theme') || 'auto';
  const next = { auto:'light', light:'dark', dark:'auto' }[cur];
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('gg-theme', next);
  document.getElementById('btnTheme').textContent = { auto:'🌗 Auto', light:'☀️ Light', dark:'🌙 Dark' }[next];
};
document.getElementById('btnTheme').onclick = cycle;
document.documentElement.setAttribute('data-theme', localStorage.getItem('gg-theme') || 'auto');
document.getElementById('btnTheme').textContent = { auto:'🌗 Auto', light:'☀️ Light', dark:'🌙 Dark' }[localStorage.getItem('gg-theme') || 'auto'];
const fsm = document.getElementById('fsModal');
document.getElementById('fsCard').onclick = () => { fsm.hidden = false; };
document.getElementById('fsClose').onclick = () => { fsm.hidden = true; };
fsm.addEventListener('click', e => { if (e.target.classList.contains('fsback')) fsm.hidden = true; });
document.addEventListener('keydown', e => { if (e.key === 'Escape') fsm.hidden = true; });
apply();
</script>
</body>
</html>
"""

def hesc(s):
    import html as _h
    return _h.escape(str(s), quote=True)

def build_gem_page(g, gems):
    ic, en, zh = CATS[g["c"]]
    lv_en, lv_zh = LVS[g["lv"]], {1:"即开即用",2:"轻松上手",3:"开发者向"}[g["lv"]]
    cls = {1:"b1",2:"b2",3:"b3"}[g["lv"]]
    de_short = g["de"][:72].rsplit(" ", 1)[0] + ("…" if len(g["de"]) > 72 else "")
    bad = ""
    if g.get("L"): bad += '<span class="badge legend">🏆 <span data-en="Legend" data-zh="封神">Legend</span></span>'
    if g.get("g"): bad += f'<span class="badge grad">🎓 <span data-en="Graduated {g["g"]}" data-zh="已毕业 {g["g"]}">Graduated {g["g"]}</span></span>'
    if g.get("a"): bad += f'<span class="badge arch">⚠️ <span data-en="Archived" data-zh="已归档">Archived</span></span>'
    rel = [x for x in gems if x["c"] == g["c"] and x["id"] != g["id"]]
    rel = sorted(rel, key=lambda x: -x["s"])[:6]
    related = "".join(
        f'<a class="mini" href="{x["id"]}.html"><span class="mrow"><span class="mn">{hesc(x["n"])}</span>'
        f'<span class="ms">★ {fmt_k(x["s"])}</span></span>'
        f'<span class="md" data-en="{hesc(x["de"])}" data-zh="{hesc(x["dz"])}">{hesc(x["de"])}</span></a>'
        for x in rel)
    if g.get("L"):
        extra_en = f"One of GitHub's legendary open-source projects, featured on GitHub Gems as a beacon in {en} — star count live-verified against the GitHub API on {TODAY}."
        extra_zh = f"GitHub Gems「{zh}」领域收录的殿堂级开源项目：作为路标与新宝藏一起呈现，star 数于 {TODAY} 经 GitHub API 实测核验。"
    else:
        extra_en = f"Part of {en} on GitHub Gems — hand-picked open-source projects in the 1k–30k star band, live-verified against the GitHub API on {TODAY}."
        extra_zh = f"收录于 GitHub Gems「{zh}」领域：人工精选 1k–30k star 区间的开源宝藏，star 数于 {TODAY} 经 GitHub API 实测核验。"
    jsonld = json.dumps({"@context":"https://schema.org","@graph":[
        {"@type":"WebPage","name":f'{g["n"]} — GitHub Gem',"url":f"{BASE}/gems/{g['id']}.html",
         "inLanguage":["en","zh"],"description":g["de"]},
        {"@type":"BreadcrumbList","itemListElement":[
            {"@type":"ListItem","position":1,"name":"GitHub Gems","item":f"{BASE}/"},
            {"@type":"ListItem","position":2,"name":en,"item":f"{BASE}/?c={g['c']}"},
            {"@type":"ListItem","position":3,"name":g["n"],"item":f"{BASE}/gems/{g['id']}.html"}]}]},
        ensure_ascii=False, separators=(",",":"))
    desc = f'{g["de"]} | {g["dz"]} | ★{g["s"]} {en} open-source gem'
    page = (GEM_TPL
        .replace("__CSS__", GEM_CSS)
        .replace("__TITLE_EN_JSON__", json.dumps(f'{g["n"]} — {de_short} | GitHub Gems'))
        .replace("__TITLE_ZH_JSON__", json.dumps(f'{g["n"]} · GitHub 宝藏项目推荐'))
        .replace("__TITLE__", hesc(f'{g["n"]} — {de_short} | GitHub Gems'))
        .replace("__DESC__", hesc(desc))
        .replace("__JSONLD__", jsonld)
        .replace("__BASE__", BASE)
        .replace("__ID__", g["id"]).replace("__NAME__", hesc(g["n"]))
        .replace("__REPO__", hesc(g["r"]))
        .replace("__STARS__", str(g["s"])).replace("__STARSK__", fmt_k(g["s"]))
        .replace("__CATID__", g["c"]).replace("__CATICON__", ic)
        .replace("__CATEN__", hesc(en)).replace("__CATZH__", hesc(zh))
        .replace("__LVEN__", lv_en).replace("__LVZH__", lv_zh).replace("__LVCLS__", cls)
        .replace("__PLAT__", hesc(g["p"])).replace("__BADGES__", bad)
        .replace("__DE__", hesc(g["de"])).replace("__DZ__", hesc(g["dz"]))
        .replace("__EXTRA_EN__", hesc(extra_en)).replace("__EXTRA_ZH__", hesc(extra_zh))
        .replace("__DATE__", TODAY).replace("__RELATED__", related))
    return page

def write_sitemap(gems):
    alt = ('<xhtml:link rel="alternate" hreflang="en" href="{0}"/>'
           '<xhtml:link rel="alternate" hreflang="zh" href="{1}"/>')
    urls = [
        f'<url><loc>{BASE}/</loc><changefreq>weekly</changefreq><priority>1.0</priority>{alt.format(BASE+"/", BASE+"/?lang=zh")}</url>',
        f'<url><loc>{BASE}/?lang=zh</loc><changefreq>weekly</changefreq><priority>0.9</priority>{alt.format(BASE+"/", BASE+"/?lang=zh")}</url>',
    ]
    for g in sorted(gems, key=lambda x: x["n"].lower()):
        loc = f"{BASE}/gems/{g['id']}.html"
        urls.append(f'<url><loc>{loc}</loc><changefreq>weekly</changefreq><priority>0.8</priority>{alt.format(loc, loc+"?lang=zh")}</url>')
        urls.append(f'<url><loc>{loc}?lang=zh</loc><changefreq>weekly</changefreq><priority>0.7</priority>{alt.format(loc, loc+"?lang=zh")}</url>')
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
           + "\n".join(urls) + "\n</urlset>\n")
    open(SITEMAP, "w", encoding="utf-8").write(xml)

def main():
    cache = load_cache()
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    grads = state.setdefault("graduated", {})
    gems, problems, new_grads = [], [], []
    ids = set()
    for prj in ALL_PROJECTS:
        if prj["id"] in ids: problems.append(f"duplicate id: {prj['id']}")
        ids.add(prj["id"])
        legend = prj.get("tier") == "L"
        node = cache.get(prj["r"]) or fetch_repo(prj["r"], cache)
        if not node:
            problems.append(f"{prj['r']}: fetch failed"); continue
        s = node["stargazerCount"]
        g = a = None
        if s > BAND_TOP and not legend:
            if prj["r"] not in grads:      # 毕业：自动记录日期，页面挂徽章，不删除
                grads[prj["r"]] = TODAY
                new_grads.append(f"{prj['r']}: {s}")
            g = grads[prj["r"]]
        elif prj["r"] in grads and s <= BAND_TOP and not legend:
            del grads[prj["r"]]            # 数据回落（几乎不可能），撤销毕业
        if node["isArchived"]:
            a = True
            problems.append(f"{prj['r']}: ARCHIVED ({s}) — 建议移除，等人工裁决")
        if not legend and s < BAND[0]:
            problems.append(f"{prj['r']}: {s} below {BAND[0]} — 建议移除，等人工裁决")
        if legend and s < BAND_TOP:
            problems.append(f"{prj['r']}: legend below {BAND_TOP} ({s}) — 不够格，建议降级或移除")
        item = {"id":prj["id"],"n":prj["n"],"r":prj["r"],"s":s,"c":prj["c"],
                "lv":prj["lv"],"p":prj["p"],"t":prj["t"],"de":prj["de"],"dz":prj["dz"]}
        if legend: item["L"] = 1
        if g: item["g"] = g
        if a: item["a"] = True
        gems.append(item)
    json.dump(cache, open(CACHE,"w"), indent=1)
    json.dump(state, open(STATE,"w"), indent=1)

    report = {"date": TODAY, "problems": problems, "newGraduates": new_grads}
    json.dump(report, open(os.path.join(HERE, "data", "patrol-report.json"), "w"), indent=1)

    if problems:
        print("PROBLEMS (kept with badges, pending review):")
        for p in problems: print("  ✗", p)
        if STRICT: sys.exit(1)

    # 静态英文卡片（与页面 JS cardHTML 渲染逻辑保持一致）
    cards = []
    for g in sorted(gems, key=lambda x: -x["s"]):
        ic, en, _zh = CATS[g["c"]]
        cls = {1:"b1",2:"b2",3:"b3"}[g["lv"]]
        extra = ""
        if g.get("L"): extra += f'<span class="badge legend">🏆 {EN_LEGEND}</span>'
        if g.get("g"): extra += f'<span class="badge grad">🎓 {EN_GRAD}</span>'
        if g.get("a"): extra += f'<span class="badge arch">⚠️ {EN_ARCH}</span>'
        cards.append(
f'''<a class="card" href="gems/{g['id']}.html">
<div class="crow"><span class="nm">{g['n']}</span><span class="st">★ {fmt_k(g['s'])}</span></div>
<p class="ds">{g['de']}</p>
<div class="mta"><span class="badge cat">{ic} {en}</span><span class="badge {cls}">{LVS[g['lv']]}</span><span class="badge">{g['p']}</span>{extra}</div>
</a>''')
    grid_html = "\n".join(cards)
    data_json = json.dumps({"d": TODAY, "g": gems}, ensure_ascii=False, separators=(",",":"))

    html = open(HTML, encoding="utf-8").read()
    html = re.sub(r"(<!--GEMS:START-->).*?(<!--GEMS:END-->)",
                  lambda m: m.group(1) + "\n" + grid_html + "\n" + m.group(2), html, flags=re.S)
    html = re.sub(r"(<!--GEMSJSON:START-->).*?(<!--GEMSJSON:END-->)",
                  lambda m: (m.group(1) + '\n<script type="application/json" id="gemsData">'
                             + data_json + "</script>\n" + m.group(2)), html, flags=re.S)
    open(HTML, "w", encoding="utf-8").write(html)

    # 落地页矩阵：整目录重建（含删除已下架项目）
    if os.path.isdir(GEMS_DIR): shutil.rmtree(GEMS_DIR)
    os.makedirs(GEMS_DIR)
    for g in gems:
        open(os.path.join(GEMS_DIR, g["id"] + ".html"), "w", encoding="utf-8").write(build_gem_page(g, gems))
    write_sitemap(gems)

    bycat = {}
    for g in gems: bycat[g["c"]] = bycat.get(g["c"], 0) + 1
    print(f"OK: {len(gems)} gems injected (+{len(gems)} landing pages, sitemap {2 + len(gems)*2} URLs)")
    for k, v in sorted(bycat.items(), key=lambda x: -x[1]):
        print(f"  {CATS[k][0]} {k:<9} {v}")
    if new_grads:
        print("🎓 new graduates:"); [print("  ", x) for x in new_grads]
    print(f"index.html size: {os.path.getsize(HTML)//1024} KB")

if __name__ == "__main__":
    main()
