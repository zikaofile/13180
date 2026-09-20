# -*- coding: utf-8 -*-
"""验证 .apkg 内容：笔记数、字段完整性、挖空一致性、标签合法性，并抽样人工检查。"""
import json, os, re, sqlite3, zipfile, collections

APKG = r"F:\syncthing\考试\自考\13180操作系统\13180操作系统-大纲考点.apkg"
TMP = r"F:\syncthing\考试\自考\13180操作系统\_build\verify_tmp"

# 1) apkg = zip；取出 collection.anki2
with zipfile.ZipFile(APKG) as z:
    names = z.namelist()
    z.extract("collection.anki2", TMP)

con = sqlite3.connect(os.path.join(TMP, "collection.anki2"))
cur = con.cursor()

notes = list(cur.execute("SELECT id, flds, tags, mid FROM notes"))
cards = list(cur.execute("SELECT id, nid FROM cards"))
print("笔记数:", len(notes), "| 卡片数:", len(cards))

# 模型字段名
cols = json.loads(cur.execute("SELECT models FROM col").fetchone()[0])
for mid, m in cols.items():
    pass
# 取所有模型字段名（本项目只有1个模型）
model_cols = {}
for mid, m in cols.items():
    model_cols[int(mid)] = [f["name"] for f in m["flds"]]

issues = []
blank_re = re.compile(r"______")
hit_re = re.compile(r'<span class="hit">(.*?)</span>')
no_desc_cnt = 0
no_blank_cnt = 0
blank_ok = 0
per_chapter = collections.Counter()
per_req = collections.Counter()

samples = []
for nid, flds, tags, mid in notes:
    parts = flds.split("\x1f")
    names = model_cols.get(mid, [])
    field = dict(zip(names, parts))
    ch, req, summ, d, front_desc, back_desc, answers, page = (
        field.get("章节", ""), field.get("要求", ""), field.get("小结", ""),
        field.get("知识点", ""), field.get("描述填空", ""), field.get("描述答案", ""),
        field.get("挖空答案", ""), field.get("页码", ""))
    per_chapter[ch] += 1
    per_req[req] += 1

    # 标签不能含空格
    for t in tags.split():
        if " " in t:
            issues.append("标签含空格: %r" % t)

    # 描述类卡片：正反面一致性
    if front_desc:
        blanks = blank_re.findall(front_desc)
        n_blank = len(blanks)
        if n_blank == 0:
            no_blank_cnt += 1
        # 挖空答案数量 = 正面空位数
        ans_list = [a for a in re.split(r"[；;]", answers) if a.strip()] if answers else []
        if n_blank and n_blank != len(ans_list):
            issues.append("卡片%d 空位数(%d)与答案数(%d)不符" % (nid, n_blank, len(ans_list)))
        # 每个答案都在反面高亮中出现
        for a in ans_list:
            if back_desc.find(">%s<" % re.escape(a)) == -1 and a not in back_desc:
                issues.append("卡片%d 答案[%s]未出现在反面" % (nid, a))
        # 反面高亮数 ≥ 空位数
        hits = hit_re.findall(back_desc)
        if n_blank and len(hits) < n_blank:
            issues.append("卡片%d 高亮数(%d)<空位数(%d)" % (nid, len(hits), n_blank))
        if n_blank:
            blank_ok += 1
        if len(samples) < 12 and n_blank == 0 and front_desc:
            samples.append(("无挖空卡片", nid, ch, req, summ, d, front_desc, back_desc, answers, page))
    else:
        no_desc_cnt += 1
        if len(samples) < 14:
            samples.append(("无描述卡片", nid, ch, req, summ, d, front_desc, back_desc, answers, page))

con.close()

print("含挖空且一致性通过:", blank_ok)
print("无挖空卡片数:", no_blank_cnt, "| 无描述卡片数:", no_desc_cnt)
print("问题数:", len(issues))
for i in issues[:20]:
    print("  ISSUE:", i)

# 半词挖空扫描：挖空两侧都是汉字（可能挖进复合词内部）
print("\n===== 半词挖空扫描 =====")
halfword = []
for nid, flds, tags, mid in notes:
    parts = flds.split("\x1f")
    field = dict(zip(model_cols.get(mid, []), parts))
    front = field.get("描述填空", "")
    plain = re.sub(r"<[^>]+>", "", front)
    for m in re.finditer(r"([\u4e00-\u9fff])______([\u4e00-\u9fff])", plain):
        halfword.append((nid, field.get("章节"), field.get("知识点"),
                         plain[max(0, m.start() - 15):m.end() + 15]))
print("半词挖空数:", len(halfword))
for h in halfword[:25]:
    print("  ", h)

print("\n章节分布:", dict(per_chapter))
print("要求分布:", dict(per_req))

# 抽样展示：每章一张代表性卡片
import collections as _c
seen_ch = _c.OrderedDict()
for nid, flds, tags, mid in notes:
    parts = flds.split("\x1f")
    field = dict(zip(model_cols.get(mid, []), parts))
    ch = field.get("章节", "")
    if ch not in seen_ch and field.get("描述填空"):
        seen_ch[ch] = (nid, field, tags)
print("\n===== 各章抽样卡片（正面/反面）=====")
for ch, (nid, field, tags) in seen_ch.items():
    print("\n### [%s] %s | 要求:%s | 小结:%s | 标签:%s" % (ch, field["知识点"], field["要求"], field["小结"], tags))
    print("正面:", field["描述填空"][:220])
    print("反面:", field["描述答案"][:220])
    print("答案:", field["挖空答案"], "| 页码:", field["页码"])

print("\n===== 抽样明细（前6条无挖空/无描述卡片）=====")
for s in samples[:6]:
    print("\n### %s %s %s %s" % (s[0], s[1], s[2], s[4]))
    print("  要求:%s 小结:%s 页码:%s" % (s[3], s[5], s[9]))
    print("  正面:%r" % s[6][:150])
    print("  反面:%r" % s[7][:150])
