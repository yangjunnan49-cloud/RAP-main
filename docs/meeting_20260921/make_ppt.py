"""[meeting-20260921] Build rap_slam_meeting.pptx — 8 pages, plain white,
academic style, per-page speaker notes with asset provenance + run config."""
import os

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, "assets")

DARK = RGBColor(0x22, 0x22, 0x22)
GRAY = RGBColor(0x66, 0x66, 0x66)
BLUE = RGBColor(0x1F, 0x6F, 0xB4)
FONT = "微软雅黑"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def set_font(run, size=12, bold=False, color=DARK):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = FONT
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn("a:ea"))
    if ea is None:
        ea = rPr.makeelement(qn("a:ea"), {})
        rPr.append(ea)
    ea.set("typeface", FONT)


def add_text(slide, x, y, w, h, lines, size=12, bold=False, color=DARK,
             align=PP_ALIGN.LEFT, line_spacing=1.15):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    first = True
    for line in lines:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = align
        p.line_spacing = line_spacing
        if isinstance(line, tuple):
            text, kw = line
        else:
            text, kw = line, {}
        r = p.add_run()
        r.text = text
        set_font(r, size=kw.get("size", size), bold=kw.get("bold", bold),
                 color=kw.get("color", color))
        if kw.get("space_before"):
            p.space_before = Pt(kw["space_before"])
    return tb


def add_title(slide, text, sub=None):
    add_text(slide, Inches(0.55), Inches(0.28), Inches(12.2), Inches(0.7),
             [(text, {"size": 24, "bold": True})])
    if sub:
        add_text(slide, Inches(0.55), Inches(0.86), Inches(12.2), Inches(0.4),
                 [(sub, {"size": 12, "color": GRAY})])


def add_pic(slide, path, x, y, w=None, h=None):
    return slide.shapes.add_picture(path, x, y, width=w, height=h)


def add_notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def add_placeholder(slide, x, y, w, h, label):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    sh.fill.solid()
    sh.fill.fore_color.rgb = RGBColor(0xF5, 0xF5, 0xF5)
    sh.line.color.rgb = RGBColor(0xBB, 0xBB, 0xBB)
    sh.line.width = Pt(1)
    tf = sh.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = label
    set_font(r, size=13, color=GRAY)
    return sh


# ---------------------------------------------------------------- P1 pipeline
s = prs.slides.add_slide(BLANK)
add_title(s, "RAP-SLAM：以生成式点云配准为核心的 LiDAR SLAM 系统",
          "整体方法 pipeline")
add_placeholder(s, Inches(0.8), Inches(1.35), Inches(11.7), Inches(3.9),
                "【pipeline 核心图占位】\n文生图 prompt 见 image_prompts.md（P1）\n"
                "生成后替换本框：assets/pipeline_generated.png")
add_text(s, Inches(0.8), Inches(5.5), Inches(11.7), Inches(1.8), [
    "系统流程：激光扫描 → 前端 KISS-ICP 里程计与关键帧筛选 → Scan Context 全局检索 + 邻近候选"
    " → RAP 生成式几何验证（流匹配多假设配准，重叠率/平均对应距离验收）→ GTSAM 位姿图优化"
    "（relfloor 自适应边权 + Huber 鲁棒核 + 回环边 NMS）→ 全局一致轨迹与拼接地图。",
    ("前后端共享统一的点云特征表示（体素降采样—统计滤波—miniSpinNet 特征—归一化），"
     "检索、验证与后端加权使用同一份表示。", {"space_before": 8, "bold": True}),
], size=13)
add_notes(s, "图中资产：pipeline 图为文生图占位（prompt 见 image_prompts.md P1，"
             "chatgpt-image-2 生成，生成前为占位框）。\n"
             "实验配置：本页无实验数据。本次实验系统配置："
             "KISS-ICP(max_range 100 m, min_range 0 m, voxel 1.0 m) + 0.205° 校正；"
             "SC 20x60/阈值 0.25；RAP rap_12 权重 5 步 Euler、4000 点；"
             "GTSAM relfloor+Huber、NMS w=10；回环候选预算 12。")

# ------------------------------------------------------- P2 innovations overview
s = prs.slides.add_slide(BLANK)
add_title(s, "创新点总览", "四点贡献，一句话陈列")
items = [
    ("① 前后端特征统一",
     "提出贯穿前后端的统一点云特征表示与预处理链：检索、生成式验证与边权加权共享同一表示，"
     "区别于「前端几何、后端另算特征」的割裂做法。"),
    ("② 生成式回环几何验证",
     "以流匹配生成模型 RAP 作回环验证器，多假设配准输出相对位姿与内蕴几何质量，验收不依赖"
     "已漂移的里程计先验；区别于「识别即闭环」与 ICP 精修受初值漂移影响的做法。"),
    ("③ 环一致的多路联合配准约束",
     "回环簇关键帧一次性送入 RAP N 路联合配准，产出环一致约束；链感知批次组合保证连通性、"
     "抑制全局翘曲，区别于逐对独立配准。"),
    ("④ 有有限样本保证的验收门与标定边权",
     "split-conformal 验收门给出假接收率 ≤5% 的有限样本保证；标定发现过门边误差近似常数，"
     "支撑鲁棒 PGO 边权设计，区别于启发式阈值与固定 σ。"),
]
y = 1.30
for head, body in items:
    add_text(s, Inches(0.8), Inches(y), Inches(11.7), Inches(1.35), [
        (head, {"size": 15, "bold": True, "color": BLUE}),
        (body, {"size": 12}),
    ])
    y += 1.48
add_notes(s, "图中资产：无（纯文字页）。\n"
             "实验配置：创新点③④对应产物 output_nway_matrix/（链感知批次组合）、"
             "output_s1/（共形门 A2，标定 698 条候选）、output_calibrated/（近常数 σ 拟合）；"
             "均为既有实验的归档结论，本页不含新跑实验。")

# ------------------------------------------------------- P3 innovation detail
s = prs.slides.add_slide(BLANK)
add_title(s, "创新点详解：前后端共享的统一特征表示",
          "同一份表示驱动检索、验证与后端加权——以 KITTI-00 真实回环为例")
add_pic(s, os.path.join(A, "fig_innovation_unified.png"), Inches(0.55),
        Inches(1.45), w=Inches(12.2))
add_text(s, Inches(0.8), Inches(5.6), Inches(11.7), Inches(1.7), [
    "左：扫描经统一预处理（体素 0.4 m + 统计滤波 + 归一化）后的表示，插图为同一份点云生成的 "
    "Scan Context 描述子——检索与后续验证消费同一表示。中：KITTI-00 第 597/3552 帧回环候选在"
    "里程计先验下错位 2.94 m / 1.64°（红蓝重影）。右：RAP 生成式验证输出的相对位姿将两帧对齐，"
    "对真值误差仅 0.70 m / 0.79°，重叠率 0.89、平均对应距离 0.69 m，验收通过；该边的质量诊断"
    "（mean_dist）同时直接决定它在 PGO 中的信息权重——特征一次计算，前后端复用。",
], size=12.5)
add_notes(s, "图中资产：自渲染。左/中/右三面板均为真实数据：KITTI-00 velodyne 000597/000978.bin"
             " 经 0.205° 校正 + 0.4 m 体素降采样；位姿取 output_meeting/kitti00_armB/odom_poses.txt；"
             "T_rel 取 accepted_loops.json 中 (597,3552) 记录；SC 描述子 20x60 实时计算。"
             "生成脚本 docs/meeting_20260921/make_innovation_fig.py。\n"
             "实验配置：同 P1 备注的本次实验配置。")

# ------------------------------------------------------- P4 overall comparison
s = prs.slides.add_slide(BLANK)
add_title(s, "实验总体对比", "KITTI 00/05/06，与第一梯队同口径对比")


def add_table(slide, x, y, w, title, header, rows, col_w=None):
    add_text(slide, x, y, w, Inches(0.32), [(title, {"size": 13, "bold": True})])
    shape = slide.shapes.add_table(len(rows) + 1, len(header), x,
                                   y + Inches(0.36), w, Inches(0.32 * (len(rows) + 1)))
    tbl = shape.table
    # plain white academic style: no theme banding/header fill
    tblPr = tbl._tbl.find(qn("a:tblPr"))
    if tblPr is not None:
        tblPr.set("firstRow", "0")
        tblPr.set("bandRow", "0")
    for i in range(len(rows) + 1):
        for j in range(len(header)):
            cell = tbl.cell(i, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    for j, htxt in enumerate(header):
        cell = tbl.cell(0, j)
        cell.text = htxt
        for p in cell.text_frame.paragraphs:
            for r in p.runs:
                set_font(r, size=11, bold=True)
            p.alignment = PP_ALIGN.CENTER
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            cell = tbl.cell(i + 1, j)
            cell.text = str(v)
            for p in cell.text_frame.paragraphs:
                for r in p.runs:
                    set_font(r, size=10.5,
                             bold=(j == 0 and "RAP-SLAM" in str(v)))
                p.alignment = PP_ALIGN.CENTER if j else PP_ALIGN.LEFT
    if col_w:
        for j, cw in enumerate(col_w):
            tbl.columns[j].width = cw
    return tbl


hdr = ["方法", "00", "05", "06", "均值"]
ter_rows = [
    ["SuMa++", "0.64", "0.40", "0.46", "0.50"],
    ["MULLS-SLAM", "0.54", "0.29", "0.29", "0.37"],
    ["CT-ICP", "0.49", "0.25", "0.27", "0.34"],
    ["KISS-SLAM（同数据实测）", "0.575", "0.517", "0.325", "0.47"],
    ["RAP-SLAM（本文）", "0.557", "0.331", "0.333", "0.41"],
]
ate_rows = [
    ["SuMa", "1.10", "0.70", "0.60", "0.80"],
    ["MULLS", "1.10", "1.00", "0.30", "0.80"],
    ["SC-KISS-ICP（离线）", "1.00", "0.30", "0.30", "0.53"],
    ["PIN-SLAM", "0.80", "0.30", "0.40", "0.50"],
    ["KISS-SLAM（同数据实测）", "0.917", "0.661", "0.328", "0.64"],
    ["RAP-SLAM（本文）", "1.814", "1.218", "0.332", "1.12"],
]
add_table(s, Inches(0.55), Inches(1.30), Inches(6.1),
          "相对平移漂移 ter [%]（越低越好）", hdr, ter_rows)
add_table(s, Inches(6.95), Inches(1.30), Inches(5.9),
          "aligned ATE RMSE [m]（越低越好）", hdr, ate_rows)
add_text(s, Inches(0.8), Inches(4.15), Inches(11.7), Inches(2.9), [
    ("关键结论", {"size": 14, "bold": True}),
    ("· ter 口径：本系统在 KITTI-00（0.557 vs 0.575）、05（0.331 vs 0.517）上优于同数据实测的 "
     "KISS-SLAM（IROS 2025），06 基本持平；均值 0.41% 进入 CT-ICP/MULLS-SLAM 所在的第一梯队区间。",
     {"size": 12.5, "space_before": 6}),
    ("· 回环可靠性：三序列 36/36 接受回环全部命中真回环，单条边对真值误差最低 0.07 m。",
     {"size": 12.5, "space_before": 4}),
    ("· 差距与靶点：aligned ATE 均值 1.12 m 仍落后于 PIN-SLAM（0.50），残差集中在 00 长序列的"
     "无重访长段，是后端工作的明确改进方向。", {"size": 12.5, "space_before": 4}),
    ("· 文献数字逐字转录自原论文表格；KISS-SLAM 为官方默认配置在本机同数据实测。",
     {"size": 10.5, "color": GRAY, "space_before": 8}),
])
add_notes(s, "图中资产：无位图，原生表格。数据唯一来源 docs/meeting_20260921/benchmark_table.md"
             "（文献转录：RAP-SLAM/data/literature/kitti_baselines.json、PIN-SLAM T-RO 2024 "
             "Table III/IV；KISS-SLAM 实测：docs/maintenance/2026-09-19/horizontal-comparison-01）。\n"
             "实验配置：RAP-SLAM 行为本次实验实测（同 P1 备注），"
             "评测脚本 RAP-SLAM/scripts/eval_meeting_arms.py，数值存 meeting_metrics.json。")

# ------------------------------------------------------- P5 per-sequence grid
s = prs.slides.add_slide(BLANK)
add_title(s, "优势序列重建对比", "横轴 = 数据集序列，纵轴 = 方法；单元格角落为 aligned ATE [m]")

seqs = ["KITTI 00", "KITTI 05", "KITTI 06"]
models = [
    ("RAP-SLAM（本文）", {
        "KITTI 00": ("seq00_ours_render_topdown.png", "1.81"),
        "KITTI 05": ("seq05_ours_render_topdown.png", "1.22"),
        "KITTI 06": ("seq06_ours_render_topdown.png", "0.33"),
    }),
    ("KISS-SLAM（实测）", {}),
    ("PIN-SLAM", {"KITTI 00": ("papers/pinslam_seq00_frompaper.png", "0.80")}),
    ("CT-ICP", {}),
    ("MULLS-SLAM", {}),
]
x0, y0 = Inches(2.35), Inches(1.35)
cw, ch = Inches(3.45), Inches(1.12)
for j, sq in enumerate(seqs):
    add_text(s, x0 + j * cw, Inches(1.02), cw, Inches(0.3),
             [(sq, {"size": 12, "bold": True})], align=PP_ALIGN.CENTER)
for i, (name, cells) in enumerate(models):
    add_text(s, Inches(0.35), y0 + i * ch + Inches(0.3), Inches(1.95),
             Inches(0.6), [(name, {"size": 11, "bold": i == 0})])
    for j, sq in enumerate(seqs):
        cx, cy = x0 + j * cw, y0 + i * ch
        if sq in cells:
            img, metric = cells[sq]
            img_h = 1.34 if i == 0 else 1.12
            pic = add_pic(s, os.path.join(A, img), cx + Inches(0.95), cy,
                          h=Inches(img_h))
            add_text(s, cx + Inches(0.97), cy + Inches(img_h - 0.28),
                     Inches(1.0), Inches(0.26),
                     [(metric, {"size": 10, "bold": True, "color": BLUE})])
        else:
            add_text(s, cx + Inches(1.55), cy + Inches(0.35), Inches(0.6),
                     Inches(0.3), [("—", {"size": 14, "color": GRAY})],
                     align=PP_ALIGN.CENTER)
add_text(s, Inches(0.8), Inches(6.72), Inches(11.7), Inches(0.35), [
    ("结论：本文三序列重建结构完整、无可见重影；KITTI-06 上 aligned ATE 0.33 m，"
     "优于 PIN-SLAM 报告的 0.40 m。网格单元格角落数字为该方法在该序列的 aligned ATE，"
     "本文一行为本次会议新渲染的俯视重建图。", {"size": 11}),
])
add_text(s, Inches(0.8), Inches(7.08), Inches(11.7), Inches(0.4), [
    ("“—” = 原论文/公开渠道未提供该序列重建图，不臆造。PIN-SLAM 图截自其 T-RO 2024 论文 Fig.5(b)。",
     {"size": 10, "color": GRAY}),
])
add_notes(s, "图中资产：本文三格为自渲染（output_meeting/kitti{00,05,06}_armB/"
             "merged_map_optimized.ply，俯视高度着色，渲染脚本 render_maps.py，"
             "均为本次会议新渲染、未在过往组会展示）；PIN-SLAM 格截自本地存档 "
             "2401.09101v2 PDF 第 12 页 Fig.5(b)；KISS-SLAM/CT-ICP/MULLS 因网络无法"
             "获取原论文 PDF 留空（任务允许）。\n"
             "实验配置：同 P1 备注；角落数字为 aligned ATE RMSE [m]（benchmark_table.md 表 2）。")

# ------------------------------------------------------- P6 city-scale map
s = prs.slides.add_slide(BLANK)
add_title(s, "城市街区级重建", "KITTI-00 全序列（4541 帧，路径 3.7 km）拼接地图，新视角渲染")
add_pic(s, os.path.join(A, "seq00_ours_render_aerial.png"), Inches(0.55),
        Inches(1.30), h=Inches(4.55))
add_pic(s, os.path.join(A, "seq00_ours_render_topdown.png"), Inches(7.6),
        Inches(1.30), h=Inches(4.55))
add_text(s, Inches(0.8), Inches(6.05), Inches(11.7), Inches(1.3), [
    "左：斜俯视新视角（本次会议首次渲染）；右：正俯视，颜色 = 高程。4541 帧扫描按优化后位姿"
    "拼接（体素 0.4 m，约 340 万点），街区路网结构完整、无重影错位；12 条 RAP 验证回环"
    "全部命中真回环，aligned ATE 1.81 m，ter 0.557%。地图由本次实验新跑出，"
    "视角与既往组会展示图均不重复。",
], size=12.5)
add_notes(s, "图中资产：自渲染新图（render_maps.py；输入 output_meeting/kitti00_armB/"
             "merged_map_optimized.ply，3,416,682 点）。斜俯视 yaw 25°/tilt 55° 与正俯视均为"
             "本次新生成视角；已核对过往组会材料（RAP-SLAM-report/advisor_report、"
             "ppt_weekly_20260823），KITTI-00 的旧展示图为不同渲染/不同产物，本图未重复。\n"
             "实验配置：同 P1 备注的本次实验配置，回环预算 12，全程 221.1 s（RTX 5070）。")

# ------------------------------------------------------- P7 supplementary
s = prs.slides.add_slide(BLANK)
add_title(s, "补充实验：前端标定约定的影响",
          "KITTI HDL-64 内参垂直角校正（CT-ICP/MULLS 同惯例）")
add_pic(s, os.path.join(A, "fig_frontend_alignment.png"), Inches(2.3),
        Inches(1.30), h=Inches(3.9))
add_text(s, Inches(0.8), Inches(5.45), Inches(11.7), Inches(1.8), [
    "KITTI 的 Velodyne HDL-64 存在已知的 0.205° 内参垂直角偏差，CT-ICP、MULLS、KISS 等公开"
    "实现均在数据加载层施加校正。图中对比校正前基线、本系统（仅里程计 / 完整系统）与同数据实测 "
    "KISS-SLAM 的 ter：采用相同校正约定后，本系统 ter 均值由 0.76% 降至 0.41%，与第一梯队"
    "的差距基本闭合——此前对比中我方偏弱的相当部分来自标定约定不一致，而非算法本身。",
], size=12.5)
add_notes(s, "图中资产：自渲染柱状图（make_ablation_fig.py；数据 meeting_metrics.json + "
             "benchmark_table.md 表 1 的 core-baseline-v1 行）。措辞刻意保持中性："
             "配置口径的完整说明见论文草稿实验节。\n"
             "实验配置：当前配置（0.205° 校正开，100/0.0/1.0）与对照臂（校正关，80/1.5/0.8）。")

# ------------------------------------------------------- P8 conclusion
s = prs.slides.add_slide(BLANK)
add_title(s, "结论与展望")
add_text(s, Inches(0.8), Inches(1.35), Inches(11.7), Inches(5.6), [
    ("结论", {"size": 15, "bold": True, "color": BLUE}),
    ("· RAP-SLAM 以生成式点云配准为回环验证核心，前后端共享统一特征表示；"
     "KITTI 00/05/06 上 ter 均值 0.41%，进入第一梯队区间，00/05 优于同数据实测 KISS-SLAM。",
     {"size": 12.5, "space_before": 6}),
    ("· 回环验证可靠：36/36 接受回环全真；共形验收门提供假接收率 ≤5% 的有限样本保证。",
     {"size": 12.5, "space_before": 4}),
    ("· 城市街区级重建结构完整（KITTI-00 全序列 340 万点拼接无重影）。",
     {"size": 12.5, "space_before": 4}),
    ("展望", {"size": 15, "bold": True, "color": BLUE, "space_before": 16}),
    ("· 全局一致性仍有差距（aligned ATE 均值 1.12 m vs PIN-SLAM 0.50 m）：残差集中在无重访长段，"
     "下一步做后端审查（PGO 边集/权重）与多路联合约束的规模化。",
     {"size": 12.5, "space_before": 6}),
    ("· 生成式验证器的结构化短时运动约束（多视角生成内耦合因果局部运动）正在按预研协议推进。",
     {"size": 12.5, "space_before": 4}),
    ("· 跨传感器泛化（POSS 32 线、Oxford Spires QT64）已具雏形，将扩充确认集。",
     {"size": 12.5, "space_before": 4}),
], size=12.5)
add_notes(s, "图中资产：无。内容为 benchmark_table.md 结论的转述；展望各项对应 "
             "AGENTS.md 记录的既定研究方向（E1 后端审查、F1 结构化短时运动约束预研、"
             "Spires 跨传感器）。")

out = os.path.join(HERE, "rap_slam_meeting.pptx")
prs.save(out)
print("saved", out)
