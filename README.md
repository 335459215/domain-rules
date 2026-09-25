# domain-rules

个人域名分流规则库（Clash / mihomo / Clash.Meta / Clash Verge / OpenClash 通用）。

规则分两个版本，**互相独立、可分别订阅**：

| 版本 | 目录 | 状态 |
|---|---|---|
| 国外版（overseas） | `overseas/` | ✅ 已完成，185 条用户规则 + 128 条补充规则 |
| 国内版（domestic） | `domestic/` | ⬜ 待建设 |

---

## 一、优先级约定（最重要）

`overseas/overseas.list` 由两部分拼成，顺序即优先级：

```
【第一部分】用户指定规则 185 条   ← 逐字保留，顺序不变
【第二部分】补充规则   128 条   ← 全部追加在后
```

Clash / mihomo 的 `rules` 是**自上而下、首个命中即生效**。因此：

- 用户指定规则永远先被匹配，**补充规则在任何情况下都不会覆盖它**；
- 补充规则只对用户规则没覆盖到的域名生效。

这一点由 `scripts/check_rules.py` 机器校验，不是口头承诺：

```bash
python3 scripts/check_rules.py
```

```
[1] 用户规则前缀逐字一致 .................... PASS (185 条)
[2] 无被用户规则完整覆盖的死规则 ............ PASS
[3] 无补充规则被用户关键字吞掉 .............. PASS
[4] 补充规则内部无重复/无自覆盖 ............ PASS
[5] 与用户规则策略不同的相交 ................ 0 处
[6] overseas.yaml 与 overseas.list 一致 ..... PASS (313 条)
✓ 校验全部通过：用户规则未被改动且位于最前，补充规则 0 冲突 / 0 死规则 / 0 重复
```

校验项含义：

| 项 | 含义 |
|---|---|
| [1] | `overseas.list` 的规则行必须**逐字**以 `user-rules/base.list` 开头——防止用户规则被无意改动或位置被挤到后面 |
| [2] | 没有补充规则被某条用户规则完全覆盖（否则它是永远命中的死规则） |
| [3] | 没有补充规则被用户的 `DOMAIN-KEYWORD`（amazon / tmdb / missav / javbus / javdb / sehuatang / sukebei / siliconflow / themoviedb）子串吞掉 |
| [4] | 补充规则内部无重复、无「后一条被前一条完整覆盖」 |
| [5] | 补充规则与用户规则的匹配域集**没有策略不同的相交**（0 处 = 即使打乱顺序也不会冲突） |
| [6] | 订阅用的 yaml 与 list 内容一致 |

> 注：[5] 报告为 0 是因为 4 处相交全部策略相同（`lain.bgm.tv`↔`bgm.tv`、`translate.google.com`↔`google.com`、`translate.googleapis.com`/`translation.googleapis.com`↔`googleapis.com`），属于无害重复；若策略不同，则仅靠「用户规则在前」兜底，校验器会打印提示。

---

## 二、目录结构

```
domain-rules/
├── README.md                      # 本文件
├── user-rules/
│   └── base.list                  # 用户指定规则的权威副本（185 条，纯规则行，无注释）
├── overseas/
│   ├── overseas.list              # 国外版完整规则（带分节注释，313 条）
│   └── overseas.yaml              # rule-provider 订阅格式（payload 313 条）
├── domestic/                      # 国内版（待建设）
└── scripts/
    └── check_rules.py             # 冲突校验器
```

`user-rules/base.list` 是**唯一权威副本**：改规则只改这里，`overseas.list` 的第一部分必须始终与它一致（校验器 [1] 会盯着）。

---

## 三、怎么用

### 方式 A：rule-provider 远程订阅（推荐，改规则不用改配置）

```yaml
rule-providers:
  overseas:
    type: http
    behavior: classical
    url: "https://raw.githubusercontent.com/335459215/domain-rules/main/overseas/overseas.yaml"
    path: ./ruleset/overseas.yaml
    interval: 86400

rules:
  - RULE-SET,overseas,MATCH          # 放在 rules 最前面
  # ... 你原有的其它规则
  - GEOIP,CN,直连
  - MATCH,🚀 默认代理
```

> `behavior: classical` 是关键——它让 provider 内的规则**按文件顺序逐条匹配**，而不是 Clash 默认的 domain 集合快速匹配。只有 `classical` 才能保住「用户规则在前」的优先级语义。用 `domain` 行为会退化成集合匹配，顺序失效。

### 方式 B：直接粘贴 rules 段

把 `overseas/overseas.list` 里去掉 `#` 注释行后的内容，粘到配置的 `rules:` 下面（放在最前面）。

### 依赖的策略组

规则里用到的 policy 名必须在你配置里存在，否则 mihomo 会启动报错：

```
🚀 默认代理   直连   🗽 美国自动   🐙 GitHub   🎵 TikTok
🗼 日本自动   🦁 狮城自动   🌈 Google   🤖 ChatGPT
```

共 9 个。`🌈 Google` 一节假设该组是通用 Google 代理；若你的 `🌈 Google` 只给翻译用，删掉补充规则里「Google 生态」整节即可（用户规则的 3 条翻译规则不受影响）。

---

## 四、补充规则说明（128 条）

按用户已有策略组归类补充，**没有新增任何策略组**：

| 分节 | 策略组 | 条数 | 内容 |
|---|---|---|---|
| Google 生态 | 🌈 Google | 19 | google.com / googleapis / gstatic / gvt1-2 / 1e100 / google.dev / goo.gl / youtube / youtu.be / ytimg / ggpht / googlevideo / googlesyndication / google-analytics / googletagmanager / deepmind |
| AI 服务 | 🗽 美国自动 | 19 | anthropic / claude.ai / claude.com / claudeusercontent / perplexity / grok / x.ai / huggingface.co / hf.co / ollama / replicate / stability / midjourney / poe / character.ai / elevenlabs / civitai / copilot.microsoft.com |
| GitHub 生态 | 🐙 GitHub | 4 | githubassets.com / ghcr.io / github.dev / githubstatus.com |
| 容器 / CDN / 开发 | 🚀 默认代理 | 11 | docker.com / docker.io / quay.io / gcr.io / k8s.io / jsdelivr.net / cdnjs.com / pages.dev / workers.dev / stackoverflow / stackexchange |
| 包索引 | 🗽 美国自动 | 5 | npmjs.org / npmjs.com / nodejs.org / yarnpkg.com / files.pythonhosted.org（与既有 `pypi.org` 同策略） |
| 影视元数据补充 | 🗽 美国自动 | 15 | plex.tv / www.plex.tv / status.plex.tv / clips.plex.tv / jellyfin.org / emby.media / trakt.tv / myanimelist.net / anilist.co / kitsu.io / rottentomatoes / letterboxd / metacritic / subdl / addic7ed |
| 日本补充 | 🗼 日本自动 | 8 | pixiv.net / pximg.net / fantia.jp / booth.pm / toranoana.jp / nyaa.si / nicovideo.jp / nimg.jp |
| Bangumi 补全 | 🦁 狮城自动 | 1 | `bgm.tv`（补上用户只写了 `lain.bgm.tv` 的其余子域，如同策略） |
| IP 查询 / DeepL 系 | 🦁 狮城自动 | 3 | ipinfo.io / ip-api.com / linguee.com |
| Deezer / Spotify CDN | 🦁 + 🚀 | 4 | dzcdn.net（狮城，与既有 deepl.com 同组）/ spotify.com / scdn.co / pscdn.co |
| 音乐元数据 / 歌词 | 🚀 默认代理 | 10 | last.fm / lastfm.freetls.fastly.net / discogs / bandcamp / bcbits / soundcloud / sndcdn / lrclib / musixmatch / navidrome |
| 流媒体 | 🚀 默认代理 | 10 | netflix / netflix.net / nflxvideo / nflxso / nflxext / nflximg / disneyplus / disney-plus.net / dssott / bamgrid |
| 社交 / 百科 | 🚀 默认代理 | 13 | discord / discordapp / discord.gg / discord.media / discordapp.net / reddit / redd.it / redditstatic / redditmedia / wikipedia / wikimedia / imgur / medium |
| Telegram 生态 | 🚀 默认代理 | 5 | telegra.ph / telegram.dog / telegram-cdn.org / telesco.pe / fragment.com |
| 网易云 | 直连 | 1 | music.163.com |

### 补充依据

域名归属均经过联网核实，主要来源：

- 官方文档 / API 参考页（Anthropic `platform.claude.com`、Gemini `ai.google.dev/api`、AniList `graphql.anilist.co`、Trakt `api.trakt.tv`、Discogs `api.discogs.com`、LRCLIB `lrclib.net/docs`、SubDL `subdl.com/api-doc`）
- 厂商域名清单（Netify 的 Netflix / Disney+ / SoundCloud 域名页）
- 社区规则库（Surge-conf 的 Disney+ list、Clash 分流指南）
- 已在线的公网 DNS / 站点本身（可直接访问确认存在）

### 刻意没做的事

- **没有动用户任何一条规则**，包括那些被更宽规则覆盖后已属冗余的（如 `DOMAIN,api.themoviedb.org` 被 `DOMAIN-SUFFIX,themoviedb.org` 覆盖、`DOMAIN-SUFFIX,api.openai.com` 被 `openai.com` 覆盖、`DOMAIN-SUFFIX,c1.jdbstatic.com` 被 `jdbstatic.com` 覆盖）。保留原样，仅在此说明。
- **没有新增策略组**，补充规则全部挂到用户已有的 9 个组上。
- **没有加宽到可能误伤国内服务的域名**（如 `fastly.net`、`cloudfront.net` 这类公共 CDN 后缀）。
- **plex.tv 用显式 DOMAIN 而非 DOMAIN-SUFFIX**：因为用户有 `DOMAIN,v4.plex.tv,直连` / `DOMAIN,v6.plex.tv,直连`，用后缀宽匹配会与「本地发现走直连」的意图相抵，显式列名更稳。

---

## 五、已知冗余（用户规则内部，保留未动）

以下条目被同一份列表里更早的更宽规则覆盖，命中时不会走到，但**按约定原样保留**：

| 冗余条目 | 已被覆盖于 |
|---|---|
| `DOMAIN,api.themoviedb.org` | `DOMAIN-SUFFIX,themoviedb.org` |
| `DOMAIN,image.tmdb.org` | `DOMAIN-SUFFIX,tmdb.org` |
| `DOMAIN,www.themoviedb.org` | `DOMAIN-SUFFIX,themoviedb.org` |
| `DOMAIN,api.thetvdb.com` | `DOMAIN-SUFFIX,thetvdb.com` |
| `DOMAIN-SUFFIX,api.deepl.com`、`api-free.deepl.com` | `DOMAIN-SUFFIX,deepl.com` |
| `DOMAIN-SUFFIX,api.openai.com` | `DOMAIN-SUFFIX,openai.com` |
| `DOMAIN-SUFFIX,api.fanyi.baidu.com` | `DOMAIN-SUFFIX,fanyi.baidu.com` |
| `DOMAIN-SUFFIX,c1.jdbstatic.com` | `DOMAIN-SUFFIX,jdbstatic.com` |
| `DOMAIN-SUFFIX,artworks.thetvdb.com` | `DOMAIN-SUFFIX,thetvdb.com` |
| `DOMAIN,app.plex.tv` 等 12 条 plex.tv | 彼此互不覆盖（不同主机名），非冗余 |

---

## 六、维护流程

1. 要改用户规则 → 编辑 `user-rules/base.list`
2. 要加补充规则 → 编辑 `overseas/overseas.list` 第二部分（**只许加在第一部分之后**）
3. 同步 `overseas/overseas.yaml` 的 payload
4. 跑 `python3 scripts/check_rules.py`，必须全 PASS 再提交

---

## 七、国内版（domestic）

待建设。预留方向：国内流媒体 / CDN / 公共 DNS / 国内 AI 与云服务 / 更新源镜像 走 `直连`，结构与国外版一致（用户规则在前 + 补充在后 + 同一套校验脚本）。
