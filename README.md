# GitHub Gems — 200 Open-Source Projects: Hidden Gems & Legends

**线上地址**：<https://github-gems.kuige.me/>（自定义域名；`https://tliens.github.io/github-gems/` 会 301 跳转）

一个手工精选的开源项目导航站，只收录 GitHub 上 **1k–30k star** 区间里「品质远超知名度」的宝藏：
既给刚接触 GitHub 的新手一条友好入门路径，也给只熟悉单一领域的开发者一张跨圈探索的「领域护照」。

- **176 个冷门宝藏 / 24 个封神之作 / 13 个领域**，每条都附中英双语推荐语与难度分级（即开即用 / 轻松上手 / 开发者向）
- **🏆 封神榜**：React、Linux、VS Code、Kubernetes 等殿堂级项目作为「路标」收录（独立 tier，不占 1k–30k 名额，`?t=L` 直达）；首页挂 [Octoverse 2025](https://octoverse.github.com) 官方数据背书（GitHub 3.95 亿公共仓库 / 1.8 亿开发者）
- **star 数全部经 GitHub API 实测核验**（见页面顶部日期），不是拍脑袋写的
- **200 个独立落地页** `gems/<id>.html`（独立 title/description/canonical，中英切换，同领域推荐内链），sitemap 324 URL
- 单文件 `index.html`，零依赖零构建，GitHub Pages 直接部署；中英双语（`?lang=` 深链）、亮暗主题、筛选/搜索/随机寻宝

## 入选标准

1. star 在 1,000–30,000 之间（低于 1k 质量无保证，高于 30k 通常已足够有名）
2. 24 个月内有更新、未归档
3. 有今天就能下载/部署/安装的成品
4. 好用程度远超流行度

**毕业机制**：上榜项目涨破 30k 后不删除，自动挂 🎓「已毕业」徽章继续保留（毕业日期记录在 `data/state.json`）；
归档 / 停更超 24 个月 / 掉破 1k 的项目带 ⚠️ 徽章并进入巡检 Issue，等人工裁决。

## 自动巡检（Star Patrol）

`.github/workflows/patrol.yml` 每周一 02:23 UTC 自动运行（也可手动 Dispatch）：

1. `scripts/patrol.py` 批量刷新全部 star / 归档 / 停更状态
2. 重建首页卡片、200 个落地页与 sitemap（宝藏毕业自动挂徽章；封神项目豁免区间校验与毕业）
3. 有变更自动 commit + push，Pages 随之重新部署
4. 有待裁决项（归档/停更/掉线）自动写入 `patrol` 标签的 Issue，人工处理后关闭

## 维护流程

项目数据唯一来源是 `scripts/gen_cards.py` 的 `PROJECTS`（宝藏）与 `LEGENDS`（封神）数组：

```bash
python3 scripts/gen_cards.py   # 校验 star 区间 + 重建卡片/落地页/sitemap（毕业线可用 GG_BAND_TOP=N 模拟）
git add -A && git commit -m "..." && git push   # push 后 Pages 约 1 分钟自动重新部署
```

- 增删项目：改对应数组（含双语描述），跑一次脚本即可；封神门槛 = star ≥ 30k，不够格会被巡检报告点名
- star 数手动刷新：`python3 scripts/patrol.py`（会用 `gh api` 重新拉取全量）
- 人工收录新项目时建议 `GG_STRICT=1 python3 scripts/gen_cards.py`：任何越界/归档直接报错退出
- 首页卡片与领域护照现在链向 `gems/<id>.html` 详情页；GitHub 仓库入口在详情页大按钮

## 收录申请

通过 [GitHub Issue](https://github.com/Tliens/github-gems/issues/new?template=submit-gem.yml) 提交，人工审核。
