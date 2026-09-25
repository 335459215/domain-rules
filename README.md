# domain-rules

个人域名分流规则库（Clash / mihomo / Clash.Meta / Clash Verge / OpenClash 通用）。

**两个独立的订阅文件，一个国内一个国外。** 你发的自定义规则**同时是两个版本的基底，且都放在各自订阅文件的最前方，优先匹配。**

| 版本 | 订阅文件 | 自定义 | 补充 | 合计 |
|---|---|---|---|---|
| 国内版 | `domestic/domestic.yaml` | 185 | 128 | 313 |
| 国外版 | `overseas/overseas.yaml` | 185 | 128 | 313 |

```
国内版订阅：
https://raw.githubusercontent.com/335459215/domain-rules/main/domestic/domestic.yaml

国外版订阅：
https://raw.githubusercontent.com/335459215/domain-rules/main/overseas/overseas.yaml
```

---

## 一、优先级：自定义规则在最前方

每个版本文件都由两部分按顺序拼成：

```
【第一部分】自定义规则 185 条   ← 你发的规则，逐字保留、顺序不变、位于最前
【第二部分】补充规则   128 条   ← 我补的，全部追加在后
```

Clash / mihomo 的 `rules` 是**自上而下、首个命中即生效**。所以：

- **自定义规则永远先被匹配，补充规则在任何域名上都不会覆盖它**；
- 补充规则只对自定义规则没覆盖到的域名生效。

这不是口头承诺，由 `scripts/check_rules.py` 机器校验（实跑输出见下）：

```bash
python3 scripts/check_rules.py            # 检查全部版本
python3 scripts/check_rules.py domestic   # 只检查国内版
python3 scripts/check_rules.py overseas   # 只检查国外版
```

```
==================================================================
版本：domestic
==================================================================
[1] 自定义规则逐字位于最前 .................. PASS (185 条)
    补充规则 ................................ 128 条
[2] 无被自定义规则完整覆盖的死规则 ......... PASS
[3] 无补充规则被自定义关键字吞掉 ........... PASS
[4] 补充规则内部无重复/无自覆盖 ............ PASS
[5] 与自定义规则策略不同的相交 .............. 0 处（顺序保证自定义优先）
    与自定义规则策略相同的相交 .............. 3 处（无害）
[6] domestic.yaml 与 domestic.list 一致 .... PASS (313 条)

==================================================================
版本：overseas
==================================================================
[1] 自定义规则逐字位于最前 .................. PASS (185 条)
    补充规则 ................................ 128 条
[2] 无被自定义规则完整覆盖的死规则 ......... PASS
[3] 无补充规则被自定义关键字吞掉 ........... PASS
[4] 补充规则内部无重复/无自覆盖 ............ PASS
[5] 与自定义规则策略不同的相交 .............. 0 处（顺序保证自定义优先）
    与自定义规则策略相同的相交 .............. 4 处（无害）
[6] overseas.yaml 与 overseas.list 一致 .... PASS (313 条)

✓ 全部通过：自定义规则逐字位于最前，补充规则 0 冲突 / 0 死规则 / 0 重复
```

校验项含义：

| 项 | 含义 |
|---|---|
| [1] | `<version>.list` 的规则行必须**逐字**以 `<version>/custom.list` 开头——防止自定义规则被改动或被挤到后面 |
| [2] | 没有补充规则被某条自定义规则完全覆盖（否则它是永远命中的死规则） |
| [3] | 没有补充规则被自定义的 `DOMAIN-KEYWORD`（amazon / tmdb / themoviedb / missav / javbus / javdb / sehuatang / sukebei / siliconflow）子串吞掉 |
| [4] | 补充规则内部无重复、无「后一条被前一条完整覆盖」 |
| [5] | 补充规则与自定义规则的匹配域集**没有策略不同的相交**（0 处 = 即使打乱顺序也不会给出不同出口） |
| [6] | 订阅用 yaml 的 payload 与 list 的规则行完全一致 |

> [5] 报 0：相交的几处策略全部相同（`lain.bgm.tv`↔`bgm.tv`、`translate.google.com`↔`google.com`、`translate.googleapis.com`↔`googleapis.com`），属无害重复。若真出现策略不同，校验器会打印 `!` 提示，此时靠「自定义在前」兜底。

---

## 二、目录结构

```
domain-rules/
├── README.md                      # 本文件
├── domestic/                      # 国内版
│   ├── custom.list                # 自定义规则权威副本（185 条，纯规则行）
│   ├── supplement.list            # 国内版补充规则（128 条，带分节注释）
│   ├── domestic.list              # 合并产物（自定义在前 + 补充在后，带注释）
│   └── domestic.yaml              # 订阅文件（payload 313 条）
├── overseas/                      # 国外版
│   ├── custom.list                # 自定义规则权威副本（185 条，与国内版相同）
│   ├── supplement.list            # 国外版补充规则（128 条，带分节注释）
│   ├── overseas.list              # 合并产物
│   └── overseas.yaml              # 订阅文件（payload 313 条）
└── scripts/
    └── check_rules.py             # 冲突校验器
```

**两个版本的 `custom.list` 内容完全相同**，都是你发的那 185 条。

### 维护流程

1. 改自定义规则 → 编辑 `domestic/custom.list` 和 `overseas/custom.list`（**两份必须同步改**）
2. 加补充规则 → 编辑对应版本的 `supplement.list`（**只许追加，不许插到自定义规则前面**）
3. 重新生成合并产物与 yaml
4. 跑 `python3 scripts/check_rules.py`，必须全 PASS 再提交

---

## 三、怎么用

### 方式 A：rule-provider 远程订阅（推荐）

```yaml
rule-providers:
  domestic:
    type: http
    behavior: classical
    url: "https://raw.githubusercontent.com/335459215/domain-rules/main/domestic/domestic.yaml"
    path: ./ruleset/domestic.yaml
    interval: 86400
  overseas:
    type: http
    behavior: classical
    url: "https://raw.githubusercontent.com/335459215/domain-rules/main/overseas/overseas.yaml"
    path: ./ruleset/overseas.yaml
    interval: 86400

rules:
  # 国内版：自定义规则在前，先匹配
  - RULE-SET,domestic,MATCH
  # 国外版：兜底
  - RULE-SET,overseas,MATCH
  - GEOIP,CN,直连
  - MATCH,🚀 默认代理
```

> **`behavior: classical` 是关键。** 它让 provider 内规则**按文件顺序逐条匹配**；用默认的 `domain` 行为会退化成集合匹配，文件顺序失效，「自定义规则在最前优先」就保不住了。
>
> 两个 provider 串联时，`domestic` 放前面 → 自定义规则（国内服务直连）先命中，剩下的才轮到 `overseas` 的补充规则。两个文件的第一部分都是同一份自定义规则，重复无害（同一出口）。

### 方式 B：直接粘贴 rules 段

把 `domestic/domestic.list`（或 `overseas/overseas.list`）去掉 `#` 注释行后的内容，粘到配置 `rules:` 的最前面。

### 依赖的策略组

规则里用到的 policy 名必须在你配置里存在，否则 mihomo 启动报错：

```
🚀 默认代理   直连   🗽 美国自动   🐙 GitHub   🎵 TikTok
🗼 日本自动   🦁 狮城自动   🌈 Google   🤖 ChatGPT
```

共 9 个。`🌈 Google` 一节假设该组是通用 Google 代理；若只给翻译用，删掉国外版补充规则里「Google 生态」整节即可（自定义的 3 条翻译规则不受影响）。

---

## 四、补充规则说明

两个版本各 128 条补充，**全部挂你已有的 9 个策略组，没有新增组**。

### 国内版（128 条，全部 `直连`）

| 分节 | 内容 |
|---|---|
| 国内视频 / 直播 | bilibili / bilivideo / hdslb / douyin / ixigua / pstatp / snssdk / amemv / douban / doubanio / youku / iqiyi / mgtv / hunantv / sohu / le / 1905 / cctv / cntv / huya / douyu |
| 国内音乐 | 163 / 126.net / kuwo / kugou / ximalaya / xmcdn / migu |
| 国内云 / 更新源 / 镜像 | aliyun / aliyuncs / alicdn / myqcloud / qcloud / huaweicloud / hwclouds / baidubce / bcebos / ustc.edu.cn / tsinghua.edu.cn / npm.elemecdn.com / mirrors.cloud.tencent.com / npmmirror / cnpmjs.org / ubuntu.org.cn / deepin / uniontech / kylinos / openeuler / openkylin |
| 国内社交 / 工具 / 云盘 | weibo / zhihu / csdn / jianshu / juejin / baidu / bdimg / bdstatic / sinajs / dingtalk / alipay / 189.cn / 10086.cn / 10010.com / quark / uc.cn / ele.me / meituan / dianping / ctrip / 12306 / 360.cn / so.com / sogou / toutiao / bytecdn / bytedance / volccdn / ipip.net / ip.cn / ip138 / ipshudi / hao123 / sm.cn / chinaso / cn.bing.com |

自定义规则里已有的直连项（自有域名 `131452188.xyz` / `11180215.xyz` / `plex.direct` / `re0.me` / `dian115.com`、`qyapi.weixin.qq.com`、`api.siliconflow.cn`、`frodo.double.com`、`fanyi.baidu.com`、`amazon.cn`）**没有重复添加**。

### 国外版（128 条）

| 分节 | 策略组 | 条数 | 内容 |
|---|---|---|---|
| Google 生态 | 🌈 Google | 19 | google.com / googleapis / gstatic / gvt1-2 / 1e100 / google.dev / goo.gl / youtube / youtu.be / ytimg / ggpht / googlevideo / googlesyndication / google-analytics / googletagmanager / deepmind |
| AI 服务 | 🗽 美国自动 | 19 | anthropic / claude.ai / claude.com / claudeusercontent / perplexity / grok / x.ai / huggingface.co / hf.co / ollama / replicate / stability / midjourney / poe / character.ai / elevenlabs / civitai / copilot.microsoft.com |
| 影视元数据补充 | 🗽 美国自动 | 15 | plex.tv / www.plex.tv / status.plex.tv / clips.plex.tv / jellyfin.org / emby.media / trakt.tv / myanimelist.net / anilist.co / kitsu.io / rottentomatoes / letterboxd / metacritic / subdl / addic7ed |
| 社交 / 百科 | 🚀 默认代理 | 13 | discord / discordapp / discord.gg / discord.media / discordapp.net / reddit / redd.it / redditstatic / redditmedia / wikipedia / wikimedia / imgur / medium |
| 容器 / CDN / 开发 | 🚀 默认代理 | 11 | docker.com / docker.io / quay.io / gcr.io / k8s.io / jsdelivr.net / cdnjs.com / pages.dev / workers.dev / stackoverflow / stackexchange |
| 音乐元数据 / 歌词 | 🚀 默认代理 | 10 | last.fm / lastfm.freetls.fastly.net / discogs / bandcamp / bcbits / soundcloud / sndcdn / lrclib / musixmatch / navidrome |
| 流媒体 | 🚀 默认代理 | 10 | netflix / netflix.net / nflxvideo / nflxso / nflxext / nflximg / disneyplus / disney-plus.net / dssott / bamgrid |
| 日本补充 | 🗼 日本自动 | 8 | pixiv.net / pximg.net / fantia.jp / booth.pm / toranoana.jp / nyaa.si / nicovideo.jp / nimg.jp |
| 包索引 | 🗽 美国自动 | 5 | npmjs.org / npmjs.com / nodejs.org / yarnpkg.com / files.pythonhosted.org（与既有 `pypi.org` 同策略） |
| GitHub 生态 | 🐙 GitHub | 4 | githubassets.com / ghcr.io / github.dev / githubstatus.com |
| Telegram 生态 | 🚀 默认代理 | 5 | telegra.ph / telegram.dog / telegram-cdn.org / telesco.pe / fragment.com |
| Deezer / Spotify CDN | 🦁 + 🚀 | 4 | dzcdn.net（狮城，与既有 `deepl.com` 同组）/ spotify.com / scdn.co / pscdn.co |
| IP 查询 / DeepL 系 | 🦁 狮城自动 | 3 | ipinfo.io / ip-api.com / linguee.com |
| Bangumi 补全 | 🦁 狮城自动 | 1 | `bgm.tv`（补上自定义里只写了 `lain.bgm.tv` 的其余子域，同策略） |

### 补充依据

域名归属均经过联网核实：

- 官方文档 / API 参考页（Anthropic `platform.claude.com`、Gemini `ai.google.dev/api`、AniList `graphql.anilist.co`、Trakt `api.trakt.tv`、Discogs `api.discogs.com`、LRCLIB `lrclib.net/docs`、SubDL `subdl.com/api-doc`、HuggingFace `huggingface.co/docs/hub`、Deezer `developers.deezer.com`）
- 厂商域名清单（Netify 的 Netflix / Disney+ / SoundCloud / Discord 域名页）
- 社区规则库（Surge-conf 的 Disney+ list、Clash 分流指南）

### 刻意没做的事

- **没有动你任何一条规则**，包括那些被同一份列表里更宽的规则覆盖后已属冗余的（见下节）。保留原样。
- **没有新增策略组**，补充规则全部挂到你已有的 9 个组上。
- **没有加宽到可能误伤国内服务的公共 CDN 后缀**（如 `fastly.net`、`cloudfront.net`）。
- **`plex.tv` 用显式 DOMAIN 而非 DOMAIN-SUFFIX**：因为自定义规则有 `DOMAIN,v4.plex.tv,直连` / `DOMAIN,v6.plex.tv,直连`（本地发现走直连），用后缀宽匹配会和这个意图相抵。

---

## 五、已知冗余（自定义规则内部，保留未动）

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

> `DOMAIN,app.plex.tv` 等 12 条 plex.tv 主机名彼此互不覆盖，**不是**冗余。

---

## 六、一个待你确认的疑点

自定义规则里有 `DOMAIN,frodo.double.com,直连`。豆瓣 App 的 API 域名实际是 **`frodo.douban.com`**（`com.douban.frodo` 是豆瓣 App 的包名，网上大量抓包示例用的都是 `frodo.douban.com`）。`double.com` 无法确认是否真实存在。

**我按约定原样保留了 `frodo.double.com`，没有擅自改。** 如果这确实是笔误，告诉我，我改成 `frodo.douban.com` 并重跑校验。
