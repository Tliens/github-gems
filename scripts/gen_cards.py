#!/usr/bin/env python3
"""GitHub Gems 卡片生成器。

数据唯一来源：本文件 PROJECTS 数组。流程：
  1. 从 data/stars-cache.json 读 star 数（缺失的仓库自动 gh api 补拉）
  2. 校验：1000 <= stars <= 30000、未归档（不满足直接报错退出）
  3. 生成静态英文卡片 + JSON 数据岛，注入 index.html 的
     <!--GEMS:START/END--> 与 <!--GEMSJSON:START/END--> 标记之间

维护：增删项目只改 PROJECTS → python3 scripts/gen_cards.py → commit + push。
star 数需要刷新时：rm data/stars-cache.json 再跑（会用 gh 补拉全部）。
"""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(HERE, "index.html")
CACHE = os.path.join(HERE, "data", "stars-cache.json")
BAND = (1000, 30000)

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
    if n >= 10000: return f"{round(n/1000)}k"
    if n >= 1000:
        v = round(n/1000, 1)
        return (f"{v:.1f}".rstrip("0").rstrip(".")) + "k"
    return str(n)

def main():
    cache = load_cache()
    gems, problems = [], []
    ids = set()
    for prj in PROJECTS:
        if prj["id"] in ids: problems.append(f"duplicate id: {prj['id']}")
        ids.add(prj["id"])
        node = cache.get(prj["r"]) or fetch_repo(prj["r"], cache)
        if not node:
            problems.append(f"{prj['r']}: fetch failed"); continue
        s = node["stargazerCount"]
        if node["isArchived"]: problems.append(f"{prj['r']}: ARCHIVED ({s})")
        if not (BAND[0] <= s <= BAND[1]): problems.append(f"{prj['r']}: {s} outside band {BAND}")
        gems.append({"id":prj["id"],"n":prj["n"],"r":prj["r"],"s":s,"c":prj["c"],
                     "lv":prj["lv"],"p":prj["p"],"t":prj["t"],"de":prj["de"],"dz":prj["dz"]})
    json.dump(cache, open(CACHE,"w"), indent=1)

    if problems:
        print("PROBLEMS — fix before shipping:")
        for p in problems: print("  ✗", p)
        sys.exit(1)

    # 静态英文卡片（与页面 JS cardHTML 渲染逻辑保持一致）
    cards = []
    for g in sorted(gems, key=lambda x: -x["s"]):
        ic, en, _zh = CATS[g["c"]]
        cls = {1:"b1",2:"b2",3:"b3"}[g["lv"]]
        cards.append(
f'''<a class="card" href="https://github.com/{g['r']}" target="_blank" rel="noopener">
<div class="crow"><span class="nm">{g['n']}</span><span class="st">★ {fmt_k(g['s'])}</span></div>
<p class="ds">{g['de']}</p>
<div class="mta"><span class="badge cat">{ic} {en}</span><span class="badge {cls}">{LVS[g['lv']]}</span><span class="badge">{g['p']}</span></div>
</a>''')
    grid_html = "\n".join(cards)
    data_json = json.dumps(gems, ensure_ascii=False, separators=(",",":"))

    html = open(HTML, encoding="utf-8").read()
    html = re.sub(r"(<!--GEMS:START-->).*?(<!--GEMS:END-->)",
                  lambda m: m.group(1) + "\n" + grid_html + "\n" + m.group(2), html, flags=re.S)
    html = re.sub(r"(<!--GEMSJSON:START-->).*?(<!--GEMSJSON:END-->)",
                  lambda m: (m.group(1) + '\n<script type="application/json" id="gemsData">'
                             + data_json + "</script>\n" + m.group(2)), html, flags=re.S)
    open(HTML, "w", encoding="utf-8").write(html)

    bycat = {}
    for g in gems: bycat[g["c"]] = bycat.get(g["c"], 0) + 1
    print(f"OK: {len(gems)} gems injected")
    for k, v in sorted(bycat.items(), key=lambda x: -x[1]):
        print(f"  {CATS[k][0]} {k:<9} {v}")
    print(f"index.html size: {os.path.getsize(HTML)//1024} KB")

if __name__ == "__main__":
    main()
