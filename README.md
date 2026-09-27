# 💎 GitHub Gems — 137 Underrated Open-Source Projects

**线上地址**：<https://github-gems.kuige.me/>

一个手工精选的开源项目导航站，只收录 GitHub 上 **1k–30k star** 区间里「品质远超知名度」的宝藏：
既给刚接触 GitHub 的新手一条友好入门路径，也给只熟悉单一领域的开发者一张跨圈探索的「领域护照」。

- **137 个项目 / 13 个领域**，每条都附中英双语推荐语与难度分级（即开即用 / 轻松上手 / 开发者向）
- **star 数全部经 GitHub API 实测核验**（见页面顶部日期），不是拍脑袋写的
- 单文件 `index.html`，零依赖零构建，GitHub Pages 直接部署；中英双语（`?lang=` 深链）、亮暗主题、筛选/搜索/随机寻宝

## 入选标准

1. star 在 1,000–30,000 之间（低于 1k 质量无保证，高于 30k 通常已足够有名）
2. 24 个月内有更新、未归档
3. 有今天就能下载/部署/安装的成品
4. 好用程度远超流行度

## 维护流程

项目数据唯一来源是 `scripts/gen_cards.py` 的 `PROJECTS` 数组：

```bash
python3 scripts/gen_cards.py   # 校验 star 区间 + 重新注入卡片与 JSON 数据岛
git add -A && git commit -m "..." && git push   # push 后 Pages 约 1 分钟自动重新部署
```

- 增删项目：只改 `PROJECTS`（含双语描述），跑一次脚本即可
- star 数刷新：`rm data/stars-cache.json` 后重跑（会用 `gh api` 重新拉取）
- 生成器会强制校验：star 超出 1k–30k、仓库归档都会直接报错退出，防止标准被悄悄破坏

## 收录申请

通过 [GitHub Issue](https://github.com/Tliens/github-gems/issues/new?template=submit-gem.yml) 提交，人工审核。
