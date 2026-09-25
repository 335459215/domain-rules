#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规则冲突校验器（多版本） —— 保证「自定义规则在最前方、优先匹配」。

每个版本目录（domestic / overseas）下的结构：
    <version>/custom.list      自定义规则（权威副本，必须位于最前）
    <version>/supplement.list  补充规则（追加在后）
    <version>/<version>.list   合并产物（custom 在前 + supplement 在后，带注释）
    <version>/<version>.yaml   rule-provider 订阅格式（payload 与 .list 规则行一致）

检查项（对每个版本）：
  [1] 合并文件的规则行是否逐字以 custom.list 开头（自定义规则未被改动且在最前）
  [2] 补充规则是否被自定义规则完整覆盖（死规则）
  [3] 补充规则是否被自定义的 DOMAIN-KEYWORD 吞掉
  [4] 补充规则内部是否重复 / 被前一条完整覆盖
  [5] 补充规则与自定义规则是否存在「域集相交且策略不同」
  [6] yaml payload 是否与合并 .list 的规则行完全一致

用法：python3 scripts/check_rules.py [version ...]   默认检查全部版本
      退出码 0 = 全部通过
"""
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSIONS = ["domestic", "overseas"]
VALID_TYPES = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}


def parse_rule(line):
    """'TYPE,domain,policy' -> (TYPE, domain, policy)；非法返回 None"""
    parts = line.split(",")
    if len(parts) < 3:
        return None
    t, dom, pol = parts[0].strip(), parts[1].strip(), ",".join(parts[2:]).strip()
    if t not in VALID_TYPES or not dom or not pol:
        return None
    return (t, dom, pol)


def load_rules(path):
    """读取规则文件，跳过空行与 # 注释；返回规则列表"""
    rules = []
    with open(path, encoding="utf-8") as f:
        for ln, raw in enumerate(f, 1):
            s = raw.strip()
            if not s or s.startswith("#"):
                continue
            r = parse_rule(s)
            if r is None:
                sys.exit("✗ %s:%d 无法解析的规则行: %r" % (path, ln, raw.rstrip()))
            rules.append(r)
    return rules


def covers(u, s):
    """规则 u 的匹配域集是否 ⊇ 规则 s 的匹配域集（u 会完全吃掉 s）"""
    ut, ud, _ = u
    st, sd, _ = s
    if ut == "DOMAIN":
        return st == "DOMAIN" and sd == ud
    if ut == "DOMAIN-SUFFIX":
        if st == "DOMAIN":
            return sd == ud or sd.endswith("." + ud)
        if st == "DOMAIN-SUFFIX":
            return sd == ud or sd.endswith("." + ud)
        return False
    if ut == "DOMAIN-KEYWORD":
        return ud in sd          # DOMAIN-KEYWORD 是子串匹配
    return False


def intersects(u, s):
    """两条规则的匹配域集是否有交集"""
    ut, ud, _ = u
    st, sd, _ = s
    if ut == "DOMAIN":
        if st == "DOMAIN":
            return sd == ud
        if st == "DOMAIN-SUFFIX":
            return sd == ud or ud.endswith("." + sd)
        if st == "DOMAIN-KEYWORD":
            return sd in ud
        return False
    if ut == "DOMAIN-SUFFIX":
        if st == "DOMAIN":
            return sd == ud or sd.endswith("." + ud)
        if st == "DOMAIN-SUFFIX":
            return sd == ud or ud.endswith("." + sd) or sd.endswith("." + ud)
        if st == "DOMAIN-KEYWORD":
            return sd in ud
        return False
    if ut == "DOMAIN-KEYWORD":
        return ud in sd
    return False


def fmt(r):
    return "%s,%s,%s" % r


def check(version):
    vdir = os.path.join(ROOT, version)
    custom_p = os.path.join(vdir, "custom.list")
    supp_p = os.path.join(vdir, "supplement.list")
    merged_p = os.path.join(vdir, "%s.list" % version)
    yaml_p = os.path.join(vdir, "%s.yaml" % version)

    print("=" * 66)
    print("版本：%s" % version)
    print("=" * 66)
    fails = []

    for p in (custom_p, supp_p, merged_p, yaml_p):
        if not os.path.exists(p):
            print("✗ 缺少文件: %s" % os.path.relpath(p, ROOT))
            return ["[%s] 缺少 %s" % (version, os.path.basename(p))]

    custom = load_rules(custom_p)
    supp = load_rules(supp_p)
    merged = load_rules(merged_p)

    # ---- [1] 自定义规则必须逐字处于最前 ----
    ok1 = merged[:len(custom)] == custom and len(merged) == len(custom) + len(supp)
    if not ok1:
        fails.append("[1] %s.list 开头与 custom.list 不一致（自定义规则被改动或不在最前）" % version)
    print("[1] 自定义规则逐字位于最前 .................. %s (%d 条)"
          % ("PASS" if ok1 else "FAIL", len(custom)))
    print("    补充规则 ................................ %d 条" % len(supp))

    # ---- [2] 死规则 ----
    dead = [(s, [u for u in custom if covers(u, s)]) for s in supp]
    dead = [(s, h) for s, h in dead if h]
    for s, h in dead:
        print("    ✗ 死规则 %s  <= 已被 %s 完整覆盖" % (fmt(s), fmt(h[0])))
    print("[2] 无被自定义规则完整覆盖的死规则 ......... %s"
          % ("PASS" if not dead else "FAIL (%d)" % len(dead)))
    if dead:
        fails.append("[2] %d 条死规则" % len(dead))

    # ---- [3] 被自定义关键字吞掉 ----
    kw = [u for u in custom if u[0] == "DOMAIN-KEYWORD"]
    swallowed = [s for s in supp if any(k[1] in s[1] for k in kw)]
    for s in swallowed:
        print("    ✗ %s  <= 被自定义 DOMAIN-KEYWORD 吞掉" % fmt(s))
    print("[3] 无补充规则被自定义关键字吞掉 ........... %s"
          % ("PASS" if not swallowed else "FAIL (%d)" % len(swallowed)))
    if swallowed:
        fails.append("[3] %d 条被关键字吞掉" % len(swallowed))

    # ---- [4] 内部重复 / 自覆盖 ----
    seen, dup = {}, []
    for s in supp:
        k = (s[0], s[1])
        if k in seen:
            dup.append(s)
        seen[k] = True
    self_shadow = []
    for i, s in enumerate(supp):
        for e in supp[:i]:
            if covers(e, s):
                self_shadow.append((s, e))
    for s in dup:
        print("    ✗ 补充规则重复: %s" % fmt(s))
    for s, e in self_shadow:
        print("    ✗ 补充规则 %s  <= 被前一条 %s 覆盖" % (fmt(s), fmt(e)))
    ok4 = not dup and not self_shadow
    print("[4] 补充规则内部无重复/无自覆盖 ............ %s" % ("PASS" if ok4 else "FAIL"))
    if not ok4:
        fails.append("[4] 重复 %d / 自覆盖 %d" % (len(dup), len(self_shadow)))

    # ---- [5] 与自定义规则策略不同的相交（报告，不判失败） ----
    diff = [(u, s) for u in custom for s in supp if intersects(u, s) and u[2] != s[2]]
    same = [(u, s) for u in custom for s in supp if intersects(u, s) and u[2] == s[2]]
    for u, s in diff:
        print("    ! 策略不同（自定义在前，优先生效）: 自定义 %s || 补充 %s" % (fmt(u), fmt(s)))
    print("[5] 与自定义规则策略不同的相交 .............. %d 处（顺序保证自定义优先）" % len(diff))
    print("    与自定义规则策略相同的相交 .............. %d 处（无害）" % len(same))

    # ---- [6] yaml 与 list 一致 ----
    ypayload = []
    with open(yaml_p, encoding="utf-8") as f:
        for raw in f:
            s = raw.strip()
            if s.startswith("- "):
                r = parse_rule(s[2:])
                if r:
                    ypayload.append(r)
    ok6 = ypayload == merged
    print("[6] %s.yaml 与 %s.list 一致 ................. %s (%d 条)"
          % (version, version, "PASS" if ok6 else "FAIL", len(ypayload)))
    if not ok6:
        fails.append("[6] yaml/list 不一致")

    # ---- 汇总 ----
    print()
    print("策略组分布（全部 %d 条 = 自定义 %d + 补充 %d）:" % (len(merged), len(custom), len(supp)))
    for pol, n in Counter(p for _, _, p in merged).most_common():
        print("    %-12s %d" % (pol, n))
    print("规则类型分布:")
    for t, n in Counter(t for t, _, _ in merged).most_common():
        print("    %-16s %d" % (t, n))
    print()
    return fails


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    versions = args if args else VERSIONS
    all_fails = []
    for v in versions:
        all_fails.extend(check(v))
    if all_fails:
        print("✗ 校验未通过:")
        for f in all_fails:
            print("   -", f)
        return 1
    print("✓ 全部通过：自定义规则逐字位于最前，补充规则 0 冲突 / 0 死规则 / 0 重复")
    return 0


if __name__ == "__main__":
    sys.exit(main())
