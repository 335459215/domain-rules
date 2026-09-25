#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规则冲突校验器 —— 保证「用户规则优先、补充规则不冲突」。

检查项：
  [1] overseas.list 的规则行是否以 user-rules/base.list 逐字开头（用户规则未被改动且在最前）
  [2] 补充规则是否被用户规则完整覆盖（死规则）
  [3] 补充规则是否被用户的 DOMAIN-KEYWORD 吞掉
  [4] 补充规则内部是否重复 / 被前一条完整覆盖
  [5] 补充规则与用户规则是否存在「域集相交且策略不同」（策略不同只允许靠顺序兜底，
      这里只报告不判失败，因为用户规则在前必然优先生效）
  [6] overseas.yaml 的 payload 是否与 overseas.list 的规则行完全一致

用法：python3 scripts/check_rules.py    退出码 0 = 全部通过
"""
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_LIST = os.path.join(ROOT, "user-rules", "base.list")
OVER_LIST = os.path.join(ROOT, "overseas", "overseas.list")
OVER_YAML = os.path.join(ROOT, "overseas", "overseas.yaml")

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


def main():
    base = load_rules(BASE_LIST)
    over = load_rules(OVER_LIST)
    fails = []

    # ---- [1] 用户规则必须逐字处于最前 ----
    if over[:len(base)] != base:
        fails.append("[1] overseas.list 开头与 user-rules/base.list 不一致"
                     "（用户规则被改动或不在最前）")
    n_user, n_sup = len(base), len(over) - len(base)
    sup = over[len(base):]
    print("[1] 用户规则前缀逐字一致 .................... %s (%d 条)" % ("PASS" if not fails else "FAIL", n_user))
    print("    补充规则 ................................ %d 条" % n_sup)

    # ---- [2] 死规则 ----
    dead = [(s, [u for u in base if covers(u, s)]) for s in sup]
    dead = [(s, h) for s, h in dead if h]
    for s, h in dead:
        print("    ✗ 死规则 %s  <= 已被 %s 完整覆盖" % (fmt(s), fmt(h[0])))
    print("[2] 无被用户规则完整覆盖的死规则 ............ %s" % ("PASS" if not dead else "FAIL (%d)" % len(dead)))
    if dead:
        fails.append("[2] %d 条死规则" % len(dead))

    # ---- [3] 被用户关键字吞掉 ----
    kw = [u for u in base if u[0] == "DOMAIN-KEYWORD"]
    swallowed = [s for s in sup if any(k[1] in s[1] for k in kw)]
    for s in swallowed:
        print("    ✗ %s  <= 被用户 DOMAIN-KEYWORD 吞掉" % fmt(s))
    print("[3] 无补充规则被用户关键字吞掉 .............. %s" % ("PASS" if not swallowed else "FAIL (%d)" % len(swallowed)))
    if swallowed:
        fails.append("[3] %d 条被关键字吞掉" % len(swallowed))

    # ---- [4] 补充规则内部重复 / 自覆盖 ----
    seen = {}
    dup = []
    for s in sup:
        k = (s[0], s[1])
        if k in seen:
            dup.append(s)
        seen[k] = True
    self_shadow = []
    for i, s in enumerate(sup):
        for e in sup[:i]:
            if covers(e, s):
                self_shadow.append((s, e))
    for s in dup:
        print("    ✗ 补充规则重复: %s" % fmt(s))
    for s, e in self_shadow:
        print("    ✗ 补充规则 %s  <= 被前一条 %s 覆盖" % (fmt(s), fmt(e)))
    ok4 = not dup and not self_shadow
    print("[4] 补充规则内部无重复/无自覆盖 ............ %s" % ("PASS" if ok4 else "FAIL"))
    if not ok4:
        fails.append("[4] 内部重复 %d / 自覆盖 %d" % (len(dup), len(self_shadow)))

    # ---- [5] 与用户规则策略不同的相交（报告，不判失败） ----
    diff = [(u, s) for u in base for s in sup if intersects(u, s) and u[2] != s[2]]
    same = [(u, s) for u in base for s in sup if intersects(u, s) and u[2] == s[2]]
    for u, s in diff:
        print("    ! 策略不同(用户在前优先生效): 用户 %s || 补充 %s" % (fmt(u), fmt(s)))
    print("[5] 与用户规则策略不同的相交 ................ %d 处（顺序保证用户优先）" % len(diff))
    print("    与用户规则策略相同的相交 ................ %d 处（无害）" % len(same))

    # ---- [6] yaml 与 list 一致 ----
    if os.path.exists(OVER_YAML):
        ypayload = []
        with open(OVER_YAML, encoding="utf-8") as f:
            for raw in f:
                s = raw.strip()
                if s in ("payload:",) or not s:
                    continue
                if s.startswith("- "):
                    r = parse_rule(s[2:])
                    if r:
                        ypayload.append(r)
        ok6 = ypayload == over
        print("[6] overseas.yaml 与 overseas.list 一致 ..... %s (%d 条)" % ("PASS" if ok6 else "FAIL", len(ypayload)))
        if not ok6:
            fails.append("[6] yaml/list 不一致")
    else:
        ok6 = False
        print("[6] overseas.yaml 缺失 ..................... FAIL")
        fails.append("[6] yaml 缺失")

    # ---- 汇总 ----
    print()
    print("策略组分布（全部 %d 条）:" % len(over))
    for pol, n in Counter(p for _, _, p in over).most_common():
        print("    %-12s %d" % (pol, n))
    print("规则类型分布:")
    for t, n in Counter(t for t, _, _ in over).most_common():
        print("    %-16s %d" % (t, n))

    if fails:
        print("\n✗ 校验未通过:")
        for f in fails:
            print("   -", f)
        return 1
    print("\n✓ 校验全部通过：用户规则未被改动且位于最前，补充规则 0 冲突 / 0 死规则 / 0 重复")
    return 0


if __name__ == "__main__":
    sys.exit(main())
