import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, Header, HeadingLevel, ImageRun, ImportedXmlComponent,
  LevelFormat, PageBreak, PageNumber, Packer, Paragraph, ShadingType, Table, TableCell,
  TableRow, TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node create_weekly_script.js /absolute/path/output.docx");
const T = String.raw;
const deckImage = T`E:\githouse\RAP-main\working files\weekly_20261101\review_v3\page-3.png`;
const mechanismImage = T`E:\githouse\RAP-main\working files\decks\rap_slam_weekly-b5533638\media\mcv1_mechanism.png`;
const palette = { primary: "0B6B4F", dark: "17231E", muted: "65736C", light: "E9F3EE", orange: "B96238", orangeLight: "FAEEE7", border: "DDE6E1", gray: "F3F6F4" };
const font = { ascii: "Arial", hAnsi: "Arial", cs: "Arial", eastAsia: "Microsoft YaHei" };
const run = (text, options = {}) => new TextRun({ text, font, size: 22, color: palette.dark, ...options });
const para = (children, options = {}) => new Paragraph({
  spacing: { after: 140, line: 320 },
  ...options,
  children: Array.isArray(children) ? children : [children],
});
const body = (text, options = {}) => para(run(text), { indent: { firstLine: 440 }, ...options });
const plain = (text, options = {}) => para(run(text), options);
const h1 = (text) => para(run(text, { bold: true, size: 30, color: palette.primary }), {
  heading: HeadingLevel.HEADING_1, spacing: { before: 320, after: 170 },
});
const h2 = (text) => para(run(text, { bold: true, size: 25, color: palette.dark }), {
  heading: HeadingLevel.HEADING_2, spacing: { before: 260, after: 130 },
});
const label = (text) => para(run(text, { bold: true, color: palette.primary }), { spacing: { before: 100, after: 80 } });
const speech = (text) => para(run(text), {
  indent: { left: 360, right: 180 }, spacing: { after: 160, line: 340 },
  border: { left: { style: "single", size: 14, color: palette.primary, space: 10 } },
});
const pageBreak = () => para(new PageBreak(), { spacing: { after: 0 } });
const cell = (text, width, options = {}) => new TableCell({
  children: [para(run(text, { size: 20, ...options.run }), { spacing: { after: 40, line: 280 } })],
  width: { size: width, type: WidthType.DXA },
  margins: { top: 100, bottom: 100, left: 120, right: 120 },
  ...options.cell,
});
const makeTable = (widths, rows) => new Table({
  width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA },
  columnWidths: widths,
  rows: rows.map((row, i) => new TableRow({ children: row.map((text, j) => cell(text, widths[j], {
    run: { bold: i === 0, color: i === 0 ? palette.primary : palette.dark },
    cell: i === 0 ? { shading: { type: ShadingType.CLEAR, fill: palette.light } } : {},
  })) })),
});
const callout = (text, fill = palette.light) => new Table({
  width: { size: 9400, type: WidthType.DXA }, columnWidths: [9400],
  rows: [new TableRow({ children: [new TableCell({
    children: [para(run(text, { bold: true, size: 23, color: palette.primary }), { spacing: { after: 40, line: 320 } })],
    width: { size: 9400, type: WidthType.DXA },
    margins: { top: 160, bottom: 160, left: 200, right: 200 },
    shading: { type: ShadingType.CLEAR, fill },
  })] })],
});
const xmlEscape = (value) => String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
const toc = (entries) => {
  const cached = entries.map(({ title, level, page }) => {
    const indent = Math.max(0, level - 1) * 360;
    return `<w:p><w:pPr><w:pStyle w:val="TOC${level}"/><w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9000"/></w:tabs><w:ind w:left="${indent}"/></w:pPr><w:r><w:t>${xmlEscape(title)}</w:t></w:r><w:r><w:tab/></w:r><w:r><w:t>${page}</w:t></w:r></w:p>`;
  }).join("");
  return ImportedXmlComponent.fromXmlString(`<w:sdt xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:sdtPr><w:alias w:val="目录"/></w:sdtPr><w:sdtContent><w:p><w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/><w:instrText xml:space="preserve"> TOC \\o &quot;1-2&quot; \\h \\z \\u </w:instrText><w:fldChar w:fldCharType="separate"/></w:r></w:p>${cached}<w:p><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p></w:sdtContent></w:sdt>`).root[0];
};
const question = (q, a) => [
  para(run(T`问：${q}`, { bold: true, color: palette.primary }), { spacing: { before: 190, after: 80 } }),
  para([run("答：", { bold: true }), run(a)], { indent: { left: 220 }, spacing: { after: 150, line: 320 } }),
];
const bullet = (text) => para(run(text), { numbering: { reference: "bullets", level: 0 }, spacing: { after: 100, line: 310 } });

const tocEntries = [
  { title: "一、技术背景与核心概念", level: 1, page: 3 },
  { title: "1.1 KISS-ICP、KISS-SLAM 与 RAP-SLAM", level: 2, page: 3 },
  { title: "1.2 三项精度指标怎么解释", level: 2, page: 3 },
  { title: "1.3 本周实验结果的业务含义", level: 2, page: 4 },
  { title: "二、逐页汇报稿", level: 1, page: 5 },
  { title: "第 1 页：总体表现", level: 2, page: 5 },
  { title: "第 2 页：技术路径与候选覆盖", level: 2, page: 5 },
  { title: "第 3 页：05＋09 真实点云轨迹", level: 2, page: 6 },
  { title: "第 4 页：本周机制验证", level: 2, page: 7 },
  { title: "第 5 页：论文收口", level: 2, page: 8 },
  { title: "三、组会问答准备", level: 1, page: 9 },
  { title: "四、一分钟总结与数字速查", level: 1, page: 10 },
];

const children = [
  para(run("RAP-SLAM", { bold: true, size: 52, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { before: 2600, after: 220 } }),
  para(run("周报知识点与逐页汇报稿", { bold: true, size: 38, color: palette.dark }), { alignment: AlignmentType.CENTER, spacing: { after: 260 } }),
  para(run("2026-11-01 · 配套五页组会周报", { size: 24, color: palette.muted }), { alignment: AlignmentType.CENTER, spacing: { after: 420 } }),
  para(run("", {}), { border: { bottom: { style: "single", size: 18, color: palette.primary, space: 1 } }, spacing: { after: 360 } }),
  para(run("建议汇报时长：10–12 分钟", { bold: true, size: 24, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 160 } }),
  para(run("内容包括技术背景、逐页口头稿、指图顺序、过渡句与问答准备。", { size: 22, color: palette.muted }), { alignment: AlignmentType.CENTER }),
  pageBreak(),
  para(run("目录", { bold: true, size: 32, color: palette.primary }), { heading: HeadingLevel.HEADING_1, spacing: { after: 180 } }),
  plain("目录页码可在 Word／WPS 中右键“更新域”刷新。", { spacing: { after: 140 } }),
  toc(tocEntries),
  para(run("使用方式", { bold: true, size: 24, color: palette.primary }), { spacing: { before: 260, after: 120 } }),
  plain("正式口播只读各页“汇报稿”；“指图顺序”和“过渡句”用于控制节奏。问答部分不必在主动汇报中展开。"),
  pageBreak(),
  h1("一、技术背景与核心概念"),
  h2("1.1 KISS-ICP、KISS-SLAM 与 RAP-SLAM"),
  body("可以先用一句话区分三者：KISS-ICP 负责连续帧的里程计，KISS-SLAM 在其上补齐回环与全局优化，RAP-SLAM 保留这条成熟前端链路，重点增强回环相对位姿的估计与筛选。"),
  makeTable([1800, 3500, 4100], [
    ["对象", "主要负责", "在本项目中的角色"],
    ["KISS-ICP", "连续点云帧到局部地图的配准与局部建图", "稳定的里程计前端，提供连续位姿"],
    ["KISS-SLAM", "KISS-ICP＋回环检测＋位姿图优化", "完整 SLAM 系统对比目标"],
    ["RAP-SLAM", "学习增强的回环相对位姿、候选扩展与几何门控", "增强非局部约束，再交给 GTSAM PGO 优化全局轨迹"],
  ]),
  plain(""),
  callout("汇报主线：前端连续估计沿用 KISS-ICP；系统级对比看 KISS-SLAM；我们的探索集中在回环相对位姿与非局部约束。"),
  label("完整数据流"),
  body("点云进入 KISS-ICP 前端后形成关键帧；Scan Context 与邻近关系提供候选；RAP 估计候选之间的相对位姿；几何门控过滤不可靠约束；通过的回环边进入 GTSAM 位姿图优化，最终影响全局轨迹。"),
  h2("1.2 三项精度指标怎么解释"),
  makeTable([1500, 4300, 3600], [
    ["指标", "直观含义", "汇报时怎么说"],
    ["ATE", "整段估计轨迹与 GT 的全局位置偏差，单位 m", "看整条轨迹是否贴近真实路线"],
    ["ter", "局部相对运动中的平移误差，单位 %", "看走同样一段距离时平移估计准不准"],
    ["rer", "局部相对运动中的旋转误差，单位 °/100 m", "看每行驶 100 m 累积多少方向偏差"],
  ]),
  plain(""),
  body("三项指标同时下降，说明改善不只体现在全局位置，也覆盖局部平移和旋转。六序列均值用于说明系统整体趋势，单个序列则用于展示具体场景中的轨迹形态。"),
  h2("1.3 本周实验结果的业务含义"),
  makeTable([3000, 2700, 3700], [
    ["结果", "数字", "它说明什么"],
    ["六序列平均", "ATE／ter／rer 分别下降 7.25%／6.59%／11.1%", "系统级精度优势覆盖三类误差"],
    ["候选覆盖", "61 → 69 → 96；RAP 仍有 27 对独有覆盖", "RAP 能为后续门控提供额外候选来源"],
    ["固定门控", "正确接受 37 → 37；错误接受 9 → 8", "覆盖扩大时正确接受没有损失"],
    ["机制验证", "70 正确、65 错误与 20 非回环输出均局部满秩", "几何可解与地点身份需要分开处理"],
    ["Adapter", "40／40 更新通过；V／P loss 均约降 1.98%", "训练与反传链路可运行，可继续围绕任务目标优化"],
  ]),
  pageBreak(),
  h1("二、逐页汇报稿"),
  h2("第 1 页：总体表现"),
  label("建议用时：约 1 分钟"),
  speech("先看六序列平均结果。相比 KISS-SLAM，RAP-SLAM 的 ATE 从 0.6990 米降到 0.6483 米，下降 7.25%；相对平移误差下降 6.59%，相对旋转误差下降 11.1%。这三项分别对应全局轨迹、局部平移和局部旋转，因此当前改善不是只优化了单一指标，而是系统精度的同步提升。下面的横向条形图给出公开方法的位置，绿色是 RAP-SLAM，深灰是 KISS-SLAM。"),
  label("指图顺序"),
  bullet("先指上方三项绿色降幅，再指下方两张条形图中的绿色 RAP-SLAM。"),
  bullet("强调“六序列平均”和“三项同步改善”，不需要逐个朗读公开方法数值。"),
  label("过渡句"),
  speech("接下来解释我们的系统与 KISS-ICP、KISS-SLAM 的关系，以及本周候选覆盖为什么继续扩大。"),
  h2("第 2 页：技术路径与候选覆盖"),
  label("建议用时：约 2 分钟"),
  speech("左侧是技术关系。KISS-ICP 是连续帧到局部地图的里程计前端；KISS-SLAM 在此基础上加入回环和位姿图优化，是完整系统对比目标。我们的路线不是重写成熟前端，而是在同一前端之后，用 RAP 增强回环相对位姿，再经过几何门控和 GTSAM PGO 影响全局轨迹。右侧是本周新增的候选结果：仅用特征 F 时覆盖 61 个正确回环，加入普通图关系到 69 个，再加入 RAP 的两视图候选后达到 96 个。其中 RAP 仍有 27 对独有覆盖，说明它提供了普通特征和图关系之外的候选来源。固定门控下，正确接受保持 37 个，错误接受由 9 个降为 8 个。"),
  label("指图顺序"),
  bullet("沿左侧三个框自上而下讲，不要先陷入模块细节。"),
  bullet("右侧先读 61、69、96，再读 37 → 37 与 9 → 8，突出“覆盖扩大、正确不降”。"),
  label("过渡句"),
  speech("候选和门控最终要落到轨迹效果，下面直接用 05 和 09 的真实点云看全局与局部差异。"),
  h2("第 3 页：05＋09 真实点云轨迹"),
  label("建议用时：约 2 分钟"),
  speech("这一页统一使用真实点云作为背景，黑线是 GT，绿色是 RAP-SLAM，橙色是 KISS-SLAM。每幅图只放 GT 和一种方法，避免多条轨迹重叠。05 的全局 ATE 是 0.359 对 0.661 米，下降 45.6%；在 1140 到 1259 帧的同一转弯中，平均误差是 0.405 对 1.125 米，下降 64.0%。09 的全局 ATE 是 1.204 对 1.259 米，下降约 4.4%；在 210 到 329 帧的代表性转弯中，平均误差是 0.762 对 0.891 米，下降约 14.5%。这里主要想说明，系统平均优势在具体道路结构和转弯区域中也能被直接观察。"),
  label("指图顺序"),
  bullet("05：先指左侧两幅小图中的橙框，再移到右侧两幅局部点云图，比较绿线与橙线相对黑线的位置。"),
  bullet("09：按同样顺序快速带过，以数值和轨迹形态为主，不重复解释颜色。"),
  para(new ImageRun({ type: "png", data: fs.readFileSync(deckImage), transformation: { width: 600, height: 338 } }), { alignment: AlignmentType.CENTER, spacing: { before: 120, after: 60 } }),
  para(run("图 1　05＋09 双序列真实点云与轨迹页", { size: 18, color: palette.muted }), { alignment: AlignmentType.CENTER, spacing: { after: 160 } }),
  label("过渡句"),
  speech("轨迹图说明结果，下一页进一步说明本周在机制上定位到了什么，以及下一步为什么集中在独立身份证据。"),
  h2("第 4 页：本周机制验证"),
  label("建议用时：约 2 分钟"),
  speech("本周完成了三层验证。第一层是输入与时间链，200 对、273 个扫描的输入、索引和相对时间关系完成一致性检查。第二层是 1813 个候选上的图补充与门控对照。第三层是机制分析：在 PCS1 A 的输出中，70 个正确回环、65 个错误回环以及 20 个非回环的可用输出都满足局部满秩。这说明满秩描述的是给定对应关系后局部几何求解是否可解，但它不能单独证明两个观测属于同一个地点。重复结构里，不同身份也可能各自形成低残差、满秩的几何解。因此下一步不再扫阈值，而是补充能够独立区分地点身份的证据。右侧 Adapter 的 40 次更新全部通过 Armijo，V 和 P 的训练 loss 都下降约 1.98%，说明优化链路已经可用。"),
  label("指图顺序"),
  bullet("先读顶部三个规模数字，再指左图的“结构 A／结构 B”和右侧 70、65、20 三组柱。"),
  bullet("Adapter 只用一句话带过，除非老师追问训练细节。"),
  para(new ImageRun({ type: "png", data: fs.readFileSync(mechanismImage), transformation: { width: 600, height: 181 } }), { alignment: AlignmentType.CENTER, spacing: { before: 100, after: 60 } }),
  para(run("图 2　局部满秩与地点身份的机制边界", { size: 18, color: palette.muted }), { alignment: AlignmentType.CENTER }),
  h2("第 5 页：论文收口"),
  label("建议用时：约 1 分钟"),
  speech("最后整理论文素材。当前已经有四类主体内容：六序列系统精度结果、05 和 09 的真实点云轨迹主图、候选覆盖与门控消融，以及局部满秩的机制反例。剩余工作集中在两项：一是把独立身份证据与现有候选、门控结果联表，补全重复结构下的机制论证；二是做系统复测与实时性优化，把 p99 从 137.4 毫秒压到 100 毫秒以内，同时保持平均 ATE 和 ter 优势，并处理 07、10 的保护项。整体故事线已经从系统结果延伸到候选覆盖和机制解释，接下来主要是证据补齐与系统收口。"),
  label("收尾句"),
  speech("本周的核心进展是：系统精度优势已经可视化，候选覆盖继续扩大，机制问题也被收敛到一个明确的验证目标。"),
  pageBreak(),
  h1("三、组会问答准备"),
  ...question("KISS-ICP 和 KISS-SLAM 到底是什么关系？", "KISS-ICP 是里程计前端，解决连续帧与局部地图的配准；KISS-SLAM 是完整系统，在其上增加回环检测和位姿图优化。我们的系统精度对比对象是 KISS-SLAM，而前端复用的是 KISS-ICP 这条成熟链路。"),
  ...question("为什么不直接重写前端？", "当前主要增益来自非局部约束。保留稳定前端可以把研究问题集中在回环候选、相对位姿和全局优化，也便于与 KISS-SLAM 做同口径系统比较。"),
  ...question("RAP 独有 27 对覆盖意味着什么？", "它表示这 27 个正确回环进入了 RAP 扩展后的候选池，但没有出现在当前的 F＋普通图候选中。这说明 RAP 提供额外候选来源；是否成为系统边仍由几何门控与后续优化决定。"),
  ...question("为什么局部满秩还不能证明回环正确？", "满秩回答的是局部几何问题是否可解，身份正确性回答的是两个观测是否属于同一地点。重复结构中，错误的地点匹配也可能有充分的几何约束，因此需要独立身份证据补充判别。"),
  ...question("候选覆盖从 61 增到 96，为什么没有全部转成正确接受？", "候选覆盖和接受数量是两级指标。覆盖表示系统看到了更多潜在回环，接受还要满足固定门控。当前结果的重点是覆盖明显扩大，同时正确接受保持 37、错误接受由 9 降为 8。"),
  ...question("系统精度提升能否全部归因于 RAP 单模块？", "本次周报以系统组合结果为主，消融用于说明候选覆盖和门控作用。更稳妥的表述是“RAP-SLAM 系统相比 KISS-SLAM 三项平均误差下降”，而不是把全部系统增益简单归结为一个模块。"),
  ...question("Adapter 的 loss 下降是否已经带来配准增益？", "当前可以直接确认的是训练、反传和更新链路可用，40 次更新全部通过，V／P loss 均下降约 1.98%。它提供了后续围绕相对位姿目标继续优化的工程基础。"),
  ...question("下一轮最优先做什么？", "优先补独立身份证据，并与现有候选和门控结果联表；系统侧同步优化 p99，目标是不损失平均精度优势的前提下达到 100 毫秒以内。"),
  pageBreak(),
  h1("四、一分钟总结与数字速查"),
  label("一分钟压缩版"),
  speech("本周 RAP-SLAM 的系统结果和机制分析都向前推进了一步。六序列平均 ATE、ter、rer 相比 KISS-SLAM 分别下降 7.25%、6.59% 和 11.1%。05 与 09 的真实点云轨迹进一步展示了全局和局部改善。机制上，普通图关系把正确候选覆盖从 61 扩到 69，RAP 扩展到 96，并保留 27 对独有覆盖；固定门控下正确接受不下降，错误接受少 1 个。同时，我们确认了局部满秩不能单独认证地点身份，因此下一阶段聚焦独立身份证据，并完成实时性与系统复测。论文主线已经具备系统结果、轨迹主图、候选消融和机制解释四类素材。"),
  label("关键数字速查"),
  makeTable([3600, 5800], [
    ["主题", "数字"],
    ["六序列平均", "ATE 0.6483 vs 0.6990 m；ter 0.44695% vs 0.47849%；rer 0.13761 vs 0.15481 °/100 m"],
    ["05 全局／局部", "ATE 0.359 vs 0.661 m；局部平均误差 0.405 vs 1.125 m"],
    ["09 全局／局部", "ATE 1.204 vs 1.259 m；局部平均误差 0.762 vs 0.891 m"],
    ["候选与门控", "61 → 69 → 96；RAP 独有 27；正确接受 37 → 37；错误接受 9 → 8"],
    ["机制验证", "70 正确＋65 错误＋20 非回环可用输出均局部满秩"],
    ["Adapter", "443,904 可训练参数；40／40 更新通过；V／P loss 均约降 1.98%"],
    ["实时性目标", "p99 137.4 → ≤100 ms；保持平均 ATE、ter 优势"],
  ]),
  plain(""),
  callout("主动汇报时突出结果与下一步；指标口径和模块归因留在问答中解释，节奏会更清楚。"),
];

const doc = new Document({
  features: { updateFields: true },
  styles: { paragraphStyles: [
    { id: "TOC1", name: "toc 1", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { font, size: 22, color: palette.dark }, paragraph: { spacing: { after: 90, line: 290 } } },
    { id: "TOC2", name: "toc 2", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { font, size: 20, color: palette.muted }, paragraph: { spacing: { after: 70, line: 270 } } },
  ] },
  numbering: { config: [{ reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 480, hanging: 240 } } } }] }] },
  sections: [{
    properties: { titlePg: true, page: { margin: { top: 1100, bottom: 1100, left: 1200, right: 1200 } } },
    headers: {
      first: new Header({ children: [plain("", { spacing: { after: 0 } })] }),
      default: new Header({ children: [para(run("RAP-SLAM 周报知识点与逐页汇报稿 · 2026-11-01", { size: 18, color: palette.muted }), { alignment: AlignmentType.RIGHT, spacing: { after: 60 }, border: { bottom: { style: "single", size: 6, color: palette.border, space: 4 } } })] }),
    },
    footers: {
      first: new Footer({ children: [plain("", { spacing: { after: 0 } })] }),
      default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 18, color: palette.muted }), { alignment: AlignmentType.CENTER })] }),
    },
    children,
  }],
});

fs.writeFileSync(outputPath, await Packer.toBuffer(doc));
