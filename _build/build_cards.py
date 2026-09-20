# -*- coding: utf-8 -*-
"""生成《13180操作系统》Anki 知识库。

卡片设计（按用户要求）：
- 正面：D列知识点 + E列描述挖空版 + 以标签形式展示 A章节/B知识点要求/C章内小结
- 反面：E列完整描述（挖空处高亮）+ 挖空答案 + G列教材页码
- 真实 Anki 标签 = A章节 / B要求 / C小结（去空格），可按章节筛选复习
"""
import json
import re
import html as _html
import csv as _csv

import genanki

ROWS = json.load(open(r"F:\syncthing\考试\自考\13180操作系统\_build\rows.json", encoding="utf-8"))

# ---------------------------------------------------------------- 常量
OUT_APKG = r"F:\syncthing\考试\自考\13180操作系统\13180操作系统-大纲考点.apkg"
OUT_CSV = r"F:\syncthing\考试\自考\13180操作系统\13180操作系统-导入用.csv"
MAX_BLANKS = 3

# 操作系统术语词典（配合 D 列知识点名共同作为挖空候选）
TERMS = """
操作系统 系统软件 硬件资源 软件资源 中央处理器 内存 外存储器 输入输出设备 裸机 虚拟机 系统调用
并发性 共享性 虚拟性 异步性 并发 并行 互斥共享 同时共享 临界资源 可重入 虚拟内存 虚拟外设 多道程序 多道批处理
批处理系统 分时系统 实时系统 硬实时 软实时 通用操作系统 网络操作系统 分布式操作系统 嵌入式操作系统 个人计算机操作系统
单用户单任务 时间片 时间片轮转 响应时间 前台作业 后台作业 交互性 多路性 独占性 及时性 作业吞吐率 吞吐率
作业 进程 线程 进程控制块 程序 程序段 数据段 进程状态 就绪 运行 阻塞 挂起 创建 终止 原语 中断 中断处理
中断向量 中断响应 中断屏蔽 中断嵌套 时钟中断 定时器 特权指令 非特权指令 内核态 用户态 管态 目态
系统调用 广义指令 陷入 软中断 处理器 寄存器 程序计数器 堆栈指针 程序状态字
进程调度 作业调度 低级调度 中级调度 高级调度 调度算法 先来先服务 短作业优先 短进程优先 时间片轮转调度 优先级调度
多级反馈队列 静态优先级 动态优先级 剥夺 非剥夺 抢占 周转时间 带权周转时间 平均周转时间 等待时间 响应比 高响应比优先
多处理器调度 负载共享 主从模式 实时调度 单调速率 最早截止时间
存储管理 地址空间 逻辑地址 物理地址 地址变换 重定位 静态重定位 动态重定位 存储保护 越界 越权 内存碎片 外部碎片 内部碎片
分区管理 固定分区 动态分区 可变分区 首次适应 循环首次适应 最佳适应 最坏适应 空闲分区表 空闲分区链 紧凑 拼接 内存紧缩
覆盖技术 交换技术 对换 页式存储 页 页框 块 页表 页表项 页内地址 页面 页号 页框号 逻辑页号 物理块号 快表 联想寄存器
段式存储 段 段表 段内地址 段号 段表项 段页式存储 虚拟存储 虚拟存储器 请求分页 请求调页 预调页 缺页 缺页中断 页面置换
页面置换算法 最佳置换 先进先出 最近最久未使用 时钟算法 二次机会 抖动 颠簸 工作集 驻留集 局部性 局部性原理
文件系统 文件 记录 文件控制块 文件目录 目录项 目录文件 路径名 绝对路径 相对路径 当前目录 多级目录 树形目录 文件属性
顺序文件 索引文件 索引顺序文件 直接文件 哈希文件 文件的物理结构 连续文件 链接文件 串联文件 索引文件结构 位示图 空闲块表 空闲链表
成组链接法 空闲分区 打开文件表 文件共享 硬链接 软链接 符号链接 文件保护 存取控制 访问权限 磁盘高速缓存 磁盘调度
设备管理 设备驱动程序 设备控制器 通道 DMA 中断方式 程序查询方式 轮询 I/O控制方式 缓冲 缓冲技术 单缓冲 双缓冲 循环缓冲 缓冲池
SPOOLing 假脱机 虚拟设备 独占设备 共享设备 字符设备 块设备 设备分配 设备独立性 逻辑设备 物理设备 磁盘 磁道 扇区 柱面
寻道时间 旋转延迟时间 传输时间 先来先服务磁盘调度 最短寻道时间优先 扫描算法 电梯算法 循环扫描 磁盘驱动调度
进程同步 进程互斥 临界区 临界段 同步机制 信号量 记录型信号量 P操作 V操作 wait操作 signal操作 生产者消费者 哲学家就餐
读者写者 管程 条件变量 死锁 死锁的必要条件 互斥 占有并等待 不可剥夺 循环等待 死锁预防 死锁避免 死锁检测 死锁解除 安全状态 银行家算法
可用资源向量 安全序列 资源分配图 剥夺资源 进程撤销 饥饿 公平 上锁 关锁
""".split()

# ---------------------------------------------------------------- 文本清洗
CJK = r"\u4e00-\u9fff"
CJK_RE = re.compile("([%s])\\s+(?=[%s])" % (CJK, CJK))
DIGIT_RE = re.compile(r"(\d)\s+(?=\d)")


def clean_text(s):
    """轻量去 OCR 噪音：多空格折叠、中文字符间空格删除、数字间空格删除（前瞻式，可处理连续链）。"""
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    s = CJK_RE.sub(r"\1", s)
    s = DIGIT_RE.sub(r"\1", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def norm_term(s):
    """术语规范化：去空白与尾部标点。"""
    s = re.sub(r"\s+", "", s)
    return s.rstrip("。.，,；;：:、）)")


def build_term_pattern(term):
    """允许字符间有 0~1 个空格/制表符（兼容 OCR 噪音），不跨换行。"""
    return re.compile("".join(re.escape(c) + r"[ \t]*" for c in term))


# 合法术语字符（中文/字母，不含数字与符号），用于过滤 D 列进词典
TERM_OK = re.compile(r"^[\u4e00-\u9fffA-Za-z]{2,12}$")

# D 列全部知识点名 → 通用词典（每行挖空时排除该行自身的 D）
all_d = set()
for r in ROWS:
    t = norm_term(r["knowledge"])
    if TERM_OK.match(t):
        all_d.add(t)
COMMON_DICT = set(TERMS) | all_d
COMMON_DICT = {t for t in COMMON_DICT if TERM_OK.match(t)}

# 括号内英文别名
ALIAS_RE = re.compile(r"[（(]\s*([A-Za-z][A-Za-z ._-]{1,40}?)\s*[）)]")
# 引号短语
QUOTE_RE = re.compile(r"[“\"]([^”\"]{2,24})[”\"]")


def alias_ok(text):
    return (len(text) >= 2 and not re.search(r"\d|=|,|，|、|…|\.\.", text)
            and text.count(" ") <= 1)


def quote_ok(text):
    return ("\n" not in text and len(text.strip()) >= 2
            and re.search(r"[\u4e00-\u9fffA-Za-z]", text))


def find_first(pattern, text, start=0):
    m = pattern.search(text, start)
    return m


def collect_candidates(e, own_d):
    """返回候选 [(start, end, answer_text, kind)]，按优先级排序。"""
    cands = []
    for m in ALIAS_RE.finditer(e):
        alias = m.group(1).strip()
        if alias_ok(alias):
            cands.append((m.start(1), m.end(1), alias, "alias"))
    for m in QUOTE_RE.finditer(e):
        q = m.group(1).strip()
        if quote_ok(q):
            cands.append((m.start(1), m.end(1), q, "quote"))
    # 全部词典术语（含本行 D）首次出现位置：短术语若被更长术语覆盖则丢弃，
    # 避免把"数据"挖进"数据元素"、把"排序"挖进"堆排序"这类半词错误。
    allm = []
    for t in sorted(COMMON_DICT, key=len):
        if len(t) < 2:
            continue
        m = build_term_pattern(t).search(e)
        if m:
            allm.append((m.start(0), m.end(0), t, t == own_d))
    kept = []
    for i, (s, e2, t, is_own) in enumerate(allm):
        if any(s2 <= s and e2_ >= e2 and len(t2) > len(t)
               for j, (s2, e2_, t2, _) in enumerate(allm) if j != i):
            continue
        kept.append((s, e2, t, is_own))
    for s, e2, t, is_own in kept:
        if is_own:
            continue
        if any(s <= b and e2 >= a for a, b, _, _ in cands):
            continue
        cands.append((s, e2, t, "term"))
    # 按 (span长度降序, 优先级) 稳定排序，避免同词重复
    cands.sort(key=lambda c: (-(c[1] - c[0]), {"alias": 0, "quote": 1, "term": 2}[c[3]]))
    return cands


def pick_blanks(cands, e):
    """挑出互不重叠的至多 MAX_BLANKS 个挖空点。"""
    chosen = []
    for a, b, ans, kind in cands:
        if len(chosen) >= MAX_BLANKS:
            break
        if any(not (b <= x or a >= y) for x, y, _, _ in chosen):
            continue
        chosen.append((a, b, ans, kind))
    return chosen


def build_html(e, chosen):
    """生成：正面填空版 + 反面完整版(挖空处高亮) + 挖空答案列表。

    e: 清洗后的描述文本；chosen: [(start,end,answer,kind)]
    返回 (front_html, back_html, answers_line, has_blank)
    """
    if not e:
        return "", "", "", False

    # --- 正面：挖空处替换为 ______（按出现位置排序，答案顺序与之对应） ---
    spans = sorted(chosen, key=lambda c: c[0])
    parts = []
    pos = 0
    for a, b, ans, kind in spans:
        parts.append(_html.escape(e[pos:a]))
        parts.append('<span class="blank">______</span>')
        pos = b
    parts.append(_html.escape(e[pos:]))
    front = "".join(parts)

    # --- 反面：所有被挖答案的出现处高亮（长答案优先，避免嵌套/重叠） ---
    hit_spans = []
    for a, b, ans, kind in chosen:
        pat = build_term_pattern(ans) if kind in ("term",) else re.compile(
            re.escape(ans) if kind == "alias" else re.escape(ans))
        for m in pat.finditer(e):
            hit_spans.append((m.start(), m.end(), ans))
    hit_spans.sort(key=lambda s: (-(s[1] - s[0]), s[0]))
    kept = []
    for a, b, ans in hit_spans:
        if any(not (b <= x or a >= y) for x, y, _ in kept):
            continue
        kept.append((a, b, ans))
    kept.sort()
    parts = []
    pos = 0
    for a, b, ans in kept:
        parts.append(_html.escape(e[pos:a]))
        parts.append('<span class="hit">%s</span>' % _html.escape(ans))
        pos = b
    parts.append(_html.escape(e[pos:]))
    back = "".join(parts)

    answers = "；".join(a for _, _, a, _ in spans)
    return front, back, answers, bool(chosen)


# ---------------------------------------------------------------- Anki 模型
MODEL_ID = 1318017000001
DECK_ID = 1318017000002

css = """
.card { font-family: "Microsoft YaHei","PingFang SC","Noto Sans SC",sans-serif;
  font-size:17px; line-height:1.75; color:#222; }
.top { margin-bottom:12px; }
.chip { display:inline-block; font-size:12px; padding:2px 12px; border-radius:12px; margin:2px 6px 2px 0; }
.c1 { background:#e3f2fd; color:#1565c0; }
.c2 { background:#e8f5e9; color:#2e7d32; }
.c3 { background:#fff3e0; color:#e65100; }
h1 { font-size:20px; color:#0d47a1; border-bottom:2px solid #e3e3e3; padding-bottom:6px; margin:6px 0 12px; }
.q { background:#f4f7fb; padding:12px 14px; border-radius:8px; border-left:4px solid #1565c0; }
.blank { color:#c62828; font-weight:bold; text-decoration:underline dotted #c62828; }
.a { background:#f4fbf5; padding:12px 14px; border-radius:8px; border-left:4px solid #2e7d32; }
.hit { color:#c62828; font-weight:bold; background:#ffecec; padding:0 3px; border-radius:3px; }
.ansbox { background:#fff8e1; padding:6px 12px; border-radius:6px; color:#795548;
  font-size:14px; margin-top:10px; border:1px dashed #e6c66b; }
.ansbox b { color:#c62828; }
.pg { margin-top:10px; font-size:13px; color:#8a8a8a; }
.note { color:#9e9e9e; font-size:14px; font-style:italic; }
"""

FRONT_TPL = """
<div class="top">
  {{#章节}}<span class="chip c1">章节：{{章节}}</span>{{/章节}}
  {{#要求}}<span class="chip c2">{{要求}}</span>{{/要求}}
  {{#小结}}<span class="chip c3">{{小结}}</span>{{/小结}}
</div>
{{#知识点}}<h1>{{知识点}}</h1>{{/知识点}}
{{#描述填空}}<div class="q">{{描述填空}}</div>{{/描述填空}}
"""

BACK_TPL = """
<div class="top">
  {{#章节}}<span class="chip c1">章节：{{章节}}</span>{{/章节}}
  {{#要求}}<span class="chip c2">{{要求}}</span>{{/要求}}
  {{#小结}}<span class="chip c3">{{小结}}</span>{{/小结}}
</div>
{{#知识点}}<h1>{{知识点}}</h1>{{/知识点}}
{{#描述答案}}<div class="a">{{描述答案}}</div>{{/描述答案}}
{{^描述答案}}<div class="note">{{#知识点}}（大纲未提供该知识点描述，请查阅教材对应页码）{{/知识点}}{{^知识点}}（大纲未提供该题答案，请对照教材核对）{{/知识点}}</div>{{/描述答案}}
{{#挖空答案}}<div class="ansbox">挖空答案：<b>{{挖空答案}}</b></div>{{/挖空答案}}
{{#页码}}<div class="pg">教材页码：P{{页码}}</div>{{/页码}}
"""

model = genanki.Model(
    MODEL_ID,
    "13180大纲考点卡",
    fields=[
        {"name": "章节"},
        {"name": "要求"},
        {"name": "小结"},
        {"name": "知识点"},
        {"name": "描述填空"},
        {"name": "描述答案"},
        {"name": "挖空答案"},
        {"name": "页码"},
    ],
    templates=[
        {
            "name": "大纲考点卡",
            "qfmt": FRONT_TPL,
            "afmt": BACK_TPL,
        }
    ],
    css=css,
)

deck = genanki.Deck(DECK_ID, "13180操作系统")


def sanitize_tag(s):
    return re.sub(r"\s+", "", s)


# ---------------------------------------------------------------- 生成卡片
notes = []
stats = {"total": 0, "with_desc": 0, "no_desc": 0, "with_blank": 0,
         "no_blank": 0, "skipped_no_knowledge": 0, "blank_count": {}}

for r in ROWS:
    d = norm_term(r["knowledge"])
    if not d:
        if r["desc"].strip():
            stats["skipped_no_knowledge"] += 1
        continue
    stats["total"] += 1

    chapter = re.sub(r"^作系统", "操作系统", clean_text(r["chapter"]))
    req = clean_text(r["requirement"])
    summ = clean_text(r["summary"])
    e = clean_text(r["desc"])
    page = r["page"]

    front_desc, back_desc, answers, has_blank = "", "", "", False
    if e:
        stats["with_desc"] += 1
        cands = collect_candidates(e, d)
        chosen = pick_blanks(cands, e)
        if not chosen:
            # 保底挖空：该行自身 D 术语首次出现
            p = build_term_pattern(d)
            m = p.search(e)
            if m:
                chosen = [(m.start(0), m.end(0), d, "term")]
        front_desc, back_desc, answers, has_blank = build_html(e, chosen)
        if has_blank:
            stats["with_blank"] += 1
            stats["blank_count"][len(chosen)] = stats["blank_count"].get(len(chosen), 0) + 1
        else:
            stats["no_blank"] += 1
    else:
        stats["no_desc"] += 1
        # 无描述：若 D 是长题干（课后习题），转为"题卡"：正面显示题干
        if len(d) > 24:
            front_desc = norm_term(d)
            d = ""

    tags = [sanitize_tag(chapter), sanitize_tag(req), sanitize_tag(summ), "13180操作系统"]
    tags = [t for t in tags if t]

    page_str = str(int(page)) if isinstance(page, (int, float)) and page is not None else (str(page).strip() if page else "")

    note = genanki.Note(
        model=model,
        fields=[chapter, req, summ, d, front_desc, back_desc, answers, page_str],
        tags=tags,
        guid=genanki.guid_for(str(r["excel_row"]), d, e[:40]),
    )
    notes.append(note)

# 同一行号不会重复；guid 唯一性校验
guids = [n.guid for n in notes]
assert len(guids) == len(set(guids)), "guid 冲突"

for n in notes:
    deck.add_note(n)
pkg = genanki.Package(deck)
pkg.write_to_file(OUT_APKG)


def csv_chips(ch, req, summ):
    parts = []
    if ch:
        parts.append('<span class="chip c1">章节：%s</span>' % _html.escape(ch))
    if req:
        parts.append('<span class="chip c2">%s</span>' % _html.escape(req))
    if summ:
        parts.append('<span class="chip c3">%s</span>' % _html.escape(summ))
    return '<div class="top">%s</div>' % "".join(parts) if parts else ""


# ---------------------------------------------------------------- CSV 备份
with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
    w = _csv.writer(f, delimiter="\t")
    w.writerow(["Front", "Back", "Tags"])
    for n in notes:
        ch, req, summ, d, front_desc, back_desc, answers, page = n.fields
        head = csv_chips(ch, req, summ) + (("<h1>%s</h1>" % _html.escape(d)) if d else "")
        front_html = head
        if front_desc:
            front_html += '<div class="q">%s</div>' % front_desc
        back_html = head
        if back_desc:
            back_html += '<div class="a">%s</div>' % back_desc
        else:
            note = "（大纲未提供该题答案，请对照教材核对）" if not d else "（大纲未提供该知识点描述，请查阅教材对应页码）"
            back_html += '<div class="note">%s</div>' % note
        if answers:
            back_html += '<div class="ansbox">挖空答案：<b>%s</b></div>' % _html.escape(answers)
        if page:
            back_html += '<div class="pg">教材页码：P%s</div>' % _html.escape(page)
        w.writerow([front_html, back_html, " ".join(n.tags)])

print("卡片总数:", stats["total"])
print("含描述:", stats["with_desc"], "| 无描述(只有知识点):", stats["no_desc"])
print("含挖空:", stats["with_blank"], "| 无挖空:", stats["no_blank"])
print("挖空数分布:", stats["blank_count"])
print("跳过(有E无D):", stats["skipped_no_knowledge"])
print("已写出:", OUT_APKG)
print("已写出:", OUT_CSV)
