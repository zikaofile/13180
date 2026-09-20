# -*- coding: utf-8 -*-
"""核对章节取值与引号/换行模式。"""
import json, re, collections
ROWS = json.load(open(r"F:\syncthing\考试\自考\13180操作系统\_build\rows.json", encoding="utf-8"))
chs = collections.Counter(r["chapter"].strip() for r in ROWS)
for ch, n in chs.items():
    print("%3d  %s" % (n, ch))
print()
qpat = re.compile(r"[“\"]([^”\"]{1,24})[”\"]")
quoted = collections.Counter()
nl = 0
for r in ROWS:
    if "\n" in r["desc"]:
        nl += 1
    for m in qpat.finditer(r["desc"]):
        quoted[m.group(1)] += 1
print("含换行描述数:", nl)
print("引号片段TOP25:")
for k, v in quoted.most_common(25):
    print("  %3d %s" % (v, k))
