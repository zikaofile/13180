# -*- coding: utf-8 -*-
"""核验 CSV 备份：编码/BOM、行数、字段数、标签无空格、样例。"""
import csv

CSV = r"F:\syncthing\考试\自考\13180操作系统\13180操作系统-导入用.csv"

raw = open(CSV, "rb").read()
print("BOM:", raw[:3] == b"\xef\xbb\xbf", "| 字节数:", len(raw))

with open(CSV, encoding="utf-8-sig", newline="") as f:
    rows = list(csv.reader(f, delimiter="\t"))
print("总行数(含表头):", len(rows))
print("表头:", rows[0])
print("首字段非空:", sum(1 for r in rows[1:] if r[0].strip()))
bad = [i for i, r in enumerate(rows) if len(r) != 3]
print("列数不等于3的行:", bad[:10] if bad else "无")
spaces = [r[2] for r in rows[1:] if " " in r[2].strip()]
print("标签含空格的卡片:", len(spaces))

# 抽样打印第1、2、151行（末行）的正反面文本(去HTML标签)
import re
for idx in (1, 2, 151):
    r = rows[idx]
    text = re.sub(r"<[^>]+>", "", r[0])
    print("\n样例#%d 正面: %s" % (idx, text[:180]))
    text2 = re.sub(r"<[^>]+>", "", r[1])
    print("样例#%d 反面: %s" % (idx, text2[:180]))
    print("样例#%d 标签: %s" % (idx, r[2]))
