import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, Header, HeadingLevel, ImportedXmlComponent,
  Packer, PageBreak, PageNumber, Paragraph, ShadingType, Table, TableCell,
  TableRow, TextRun, WidthType, convertInchesToTwip,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_speaker_notes.js /absolute/path/output.docx");
fs.mkdirSync(path.dirname(outputPath), { recursive: true });
const T = String.raw;
const palette = { dark: "17231E", primary: "0B6B4F", primaryLight: "E9F3EE", muted: "65736C", border: "DCE5E0", orange: "B96238", fill: "F5F8F6" };
const font = { ascii: "Arial", hAnsi: "Arial", cs: "Arial", eastAsia: "Microsoft YaHei" };
const run = (text, options = {}) => new TextRun({ text, font, size: 22, color: palette.dark, ...options });
const para = (children, options = {}) => new Paragraph({ spacing: { after: 150, line: 330 }, ...options, children: Array.isArray(children) ? children : [children] });
const body = (text) => para(run(text), { indent: { firstLine: convertInchesToTwip(0.31) }, alignment: AlignmentType.JUSTIFIED });
const plain = (text, options = {}) => para(run(text, options), { alignment: AlignmentType.JUSTIFIED });
const h1 = (text) => para(run(text, { bold: true, size: 31, color: palette.primary }), { heading: HeadingLevel.HEADING_1, spacing: { before: 120, after: 220 }, keepNext: true });
const h2 = (text) => para(run(text, { bold: true, size: 25, color: palette.dark }), { heading: HeadingLevel.HEADING_2, spacing: { before: 240, after: 120 }, keepNext: true });
const h3 = (text) => para(run(text, { bold: true, size: 22, color: palette.primary }), { heading: HeadingLevel.HEADING_3, spacing: { before: 180, after: 90 }, keepNext: true });
const bullet = (text) => para(run(text), { numbering: { reference: "bullets", level: 0 }, spacing: { after: 90, line: 315 } });
const note = (text) => para(run(text, { size: 19, color: palette.muted, italics: true }), { spacing: { after: 130, line: 290 } });
const pageBreak = () => new Paragraph({ children: [new PageBreak()] });
const xmlEscape = (v) => String(v).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
const toc = (entries) => {
  const cached = entries.map(({ title, level = 1, page }) => `<w:p><w:pPr><w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9000"/></w:tabs><w:ind w:left="${(level - 1) * 360}"/></w:pPr><w:r><w:t>${xmlEscape(title)}</w:t></w:r><w:r><w:tab/></w:r><w:r><w:t>${page}</w:t></w:r></w:p>`).join("");
  return ImportedXmlComponent.fromXmlString(`<w:sdt xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:sdtPr><w:alias w:val="目录"/></w:sdtPr><w:sdtContent><w:p><w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/><w:instrText xml:space="preserve"> TOC \\o &quot;1-3&quot; \\h \\z \\u </w:instrText><w:fldChar w:fldCharType="separate"/></w:r></w:p>${cached}<w:p><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p></w:sdtContent></w:sdt>`).root[0];
};
const widths = [1900, 2700, 4400];
const cell = (text, i, header = false) => new TableCell({
  width: { size: widths[i], type: WidthType.DXA },
  margins: { top: 100, bottom: 100, left: 120, right: 120 },
  shading: header ? { type: ShadingType.CLEAR, fill: palette.primaryLight } : undefined,
  children: [para(run(text, { size: 19, bold: header, color: header ? palette.primary : palette.dark }), { spacing: { after: 20, line: 280 } })],
});
const table = (headers, rows) => new Table({
  width: { size: 9000, type: WidthType.DXA }, columnWidths: widths,
  rows: [new TableRow({ tableHeader: true, children: headers.map((x, i) => cell(x, i, true)) }), ...rows.map(row => new TableRow({ children: row.map((x, i) => cell(x, i)) }))],
});
const slideIntro = (page, title, minutes) => {
  children.push(h1(`第 ${page} 页｜${title}`));
  children.push(note(`对应 PPT 第 ${page} 页。建议讲解 ${minutes}。以下内容分为可直接口述的讲稿与备用技术解释。`));
};

const children = [
  para(run("RAP-SLAM 每周组会汇报", { bold: true, size: 42, color: palette.primary }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 2300, after: 260 } }),
  para(run("逐页讲稿、技术解释与术语说明", { size: 28, color: palette.dark }), { alignment: AlignmentType.CENTER, spacing: { after: 500 } }),
  para(run("对应 2026-10-25 版七页汇报 PPT", { size: 21, color: palette.muted }), { alignment: AlignmentType.CENTER, spacing: { after: 180 } }),
  para(run("用途：汇报准备、现场讲述、问答备查", { size: 20, color: palette.muted }), { alignment: AlignmentType.CENTER }),
  pageBreak(),
  h1("目录"),
  note("目录页码为预排结果；在 Word/WPS 中右键目录并选择“更新域”即可刷新。"),
  toc([
    { title: "一、项目整体说明与汇报主线", page: 3 },
    { title: "二、第 1 页：总体表现与横向对比", page: 5 },
    { title: "三、第 2 页：优势序列 05 与 09", page: 7 },
    { title: "四、第 3 页：六序列轨迹与局部放大", page: 8 },
    { title: "五、第 4 页：已完成工作与系统能力", page: 10 },
    { title: "六、第 5 页：LoRA／MLP Adapter 训练复盘", page: 12 },
    { title: "七、第 6 页：当前差距与优化入口", page: 14 },
    { title: "八、第 7 页：下一阶段目标与预期", page: 15 },
    { title: "九、专业术语速查", page: 17 },
    { title: "十、常见提问与回答要点", page: 19 },
    { title: "十一、数据口径与实验记录索引", page: 21 },
  ]),
  pageBreak(),
  h1("一、项目整体说明与汇报主线"),
  h2("1. 项目要解决什么问题"),
  body(T`RAP-SLAM 的目标是在激光雷达 SLAM 中同时估计车辆或传感器的连续运动轨迹，并构建一致的环境地图。系统不仅要判断“相邻两帧怎样移动”，还要在车辆再次经过相近区域时识别回环，并求出可靠的相对位姿约束，用来修正长时间运行中累计的轨迹漂移。`),
  body(T`当前系统采用“几何前端＋学习配准模块＋位姿图后端”的组合路线。KISS-ICP 负责局部里程计，关键帧和候选检索负责寻找潜在回环，RAP 模型提供回环相对位姿候选，几何接受规则筛选约束，最后由 GTSAM 对位姿图进行联合优化。RAP 目前是系统中的回环约束来源之一，不是对整套 KISS-SLAM 或局部里程计的简单替换。`),
  h2("2. 一条数据怎样经过系统"),
  bullet(T`点云输入与预处理：读取 LiDAR 扫描，统一坐标、数值精度和前端算术口径。`),
  bullet(T`局部里程计：通过 KISS-ICP 估计相邻时刻运动，形成连续但会逐渐漂移的轨迹。`),
  bullet(T`候选检索：结合空间邻近与 Scan Context 等描述信息，找出可能构成回环的关键帧对。`),
  bullet(T`RAP 配准与几何筛选：预测候选相对位姿，剔除几何上不可靠的约束。`),
  bullet(T`位姿图优化：将局部里程计边和回环边放入同一图优化问题，调整整段轨迹。`),
  bullet(T`评测：对优化后的轨迹计算 ATE、ter、rer，并统计完整运行耗时和逐帧尾延迟。`),
  h2("3. 本次汇报的核心结论"),
  body(T`本次汇报采用当前表现最优且已完成独立复核的 raw-core 口径。六序列平均结果上，RAP-SLAM 相比本地同跑 KISS-SLAM 的 ATE、ter、rer 分别下降 7.25%、6.59% 和 11.1%。优势主要集中在 00、05、09，05 的提升最明显；06、07、10 仍存在逐序列差距。效率方面，当前平均吞吐低于 KISS-SLAM，p99 帧耗时是最明确的优化对象。`),
  body(T`Adapter 追加实验则说明另一个层面的问题：LoRA 与 final MLP 的训练链路可以有效优化，训练 loss 确实下降约 1.98%，但这一变化没有转化为有意义的最终配准收益。因此，项目当前主线是保持平均精度优势、治理逐序列短板并降低尾延迟；训练线后续需要新的任务和监督目标，而不是简单增加更新次数。`),
  h2("4. 阅读所有数字时必须保留的口径"),
  bullet(T`“本地同跑”指 RAP-SLAM 与 KISS-SLAM 在本地固定输入和实验协议下运行，可直接支撑二者之间的相对比较。`),
  bullet(T`“公开文献值”来自各方法论文，PPT 仅将它们统一到 00／05／06／07／09／10 六序列重新求算术平均；它们不是本地统一重跑结果。`),
  bullet(T`三重复均值用于总体性能表，表示三个进程重复后的平均，不等于三个独立场景，也不代表最佳单次运行。`),
  bullet(T`轨迹图使用 r1 单次运行以便逐帧定位误差；总体指标仍使用三重复均值，两种口径不混用。`),
  pageBreak(),
];

slideIntro(1, "总体表现与横向对比", "约 1.5 分钟");
children.push(
  h2("可直接口述的讲稿"),
  body(T`先看总体结果。在当前六条 KITTI 序列上，RAP-SLAM 相比本地同跑的 KISS-SLAM，三项平均误差都下降。ATE 从 0.6990 米降到 0.6483 米，下降 7.25%；ter 从 0.47849% 降到 0.44695%，下降 6.59%；rer 从 0.15481 度每百米降到 0.13761，下降 11.1%。这说明提升同时覆盖全局轨迹、相对平移和相对旋转，而不是只对某一个误差维度有效。`),
  body(T`下半部分把比较范围扩展到更多公开方法。按相同六序列重算后，我们的 ATE 和 ter 都处于较有竞争力的位置，并且优于多项经典或近期基线。但这里不把结论扩大为“全面超过所有方法”：SC-KISS-ICP、PIN-SLAM 的公开 ATE 更低，CT-ICP、MULLS-SLAM 的公开 ter 也更低。我们的核心结论是，相对本地强基线 KISS-SLAM 有稳定平均提升，同时已经进入公开方法的有竞争力区间。`),
  h2("三项指标分别说明什么"),
  body(T`ATE（Absolute Trajectory Error，绝对轨迹误差）衡量整段估计轨迹相对真值轨迹的全局偏差。这里使用平移部分的 RMSE，单位为米。计算前进行 SE(3) 对齐，即只估计旋转和平移，不做尺度缩放。ATE 对回环修正、长距离漂移和全局一致性较敏感。`),
  body(T`ter（relative translational error）是相对平移漂移，单位为百分比，可直观理解为每行驶 100 米平均产生多少米的相对平移误差。rer（relative rotational error）是相对旋转漂移，单位为度每百米。它们来自 KITTI 风格的分段评价，更关注局部运动在不同轨迹长度上的累计误差，与 ATE 的全局意义不同。`),
  body(T`改善率统一按（KISS－RAP）÷KISS 计算。误差越低越好，因此正值表示 RAP-SLAM 更优。平均值是六条序列先分别得到结果，再做算术平均，不按帧数加权，避免长序列支配结论。`),
  h2("横向表格怎样讲才准确"),
  bullet(T`RAP 与 KISS 的数值是本地三重复均值；其余方法是论文公开值。`),
  bullet(T`表格解决了“序列集合一致”的问题，但没有完全统一代码版本、运行环境、参数调优和失败处理。`),
  bullet(T`因此可用于定位大致竞争力，不宜把不同来源的小数点差异解释为严格的同条件排名。`),
  h2("本页一句话收束"),
  plain(T`“三项平均误差同步下降，是我们当前最明确的系统级优势；横向结果说明有竞争力，但强基线仍然存在。”`, { bold: true, color: palette.primary }),
  pageBreak(),
);

slideIntro(2, "优势序列 05 与 09", "约 1 分钟");
children.push(
  h2("可直接口述的讲稿"),
  body(T`把总体结果拆到序列，05 是最突出的优势案例。RAP-SLAM 的 ATE 为 0.359 米，KISS-SLAM 为 0.661 米，下降 45.6%；ter 从 0.5173% 降到 0.3211%，下降 37.9%；rer 从 0.2133 度每百米降到 0.1046，下降 51.0%。三项指标同向且幅度较大，说明这里不是依靠单个指标或单次运行来表达优势。`),
  body(T`09 也保持三项同向改善：ATE、ter、rer 分别下降 4.3%、4.2% 和 8.0%。幅度不如 05，但它说明优势并不只出现在一个序列。00 同样三项改善，只是 ter 的提升很小，所以汇报中重点展开 05 和 09。`),
  h2("为什么同时看 ATE 与相对误差"),
  body(T`如果只看 ATE，可能把一次全局修正误认为所有局部运动都更好；如果只看 ter 或 rer，又可能忽略整段轨迹的漂移。05 的三项同步下降说明全局轨迹与局部相对运动都受益。对后续机制分析而言，这类序列更值得优先检查回环边在何时被接受、修正了哪一段轨迹，以及局部前端是否也有共同贡献。`),
  h2("读图说明"),
  bullet(T`灰色条始终以 KISS-SLAM 为满刻度，绿色条表示 RAP-SLAM，因此每行比较的是相对比例。`),
  bullet(T`图中显示的是三重复均值，不挑选某一条最优重复。`),
  bullet(T`“三项全胜”指这三项误差都更低，不等于所有场景、所有耗时指标都更好。`),
  h2("本页一句话收束"),
  plain(T`“05 证明系统可以获得大幅度、跨指标的提升，09 和 00 则说明这种优势具有一定的序列覆盖。”`, { bold: true, color: palette.primary }),
  pageBreak(),
);

slideIntro(3, "六序列轨迹与局部放大", "约 1.5 分钟");
children.push(
  h2("可直接口述的讲稿"),
  body(T`这一页把数值差异还原到轨迹形状。黑色是 GT，绿色是 RAP-SLAM，灰色是 KISS-SLAM。上排是 00、05、09 优势序列，下排是 06、07、10 当前短板。每条序列左图是完整轨迹，右图是橙色框对应区域的局部放大。05 的局部差异最直观：RAP 的轨迹更贴近 GT，对应它较大的 ATE 改善。06、07、10 的放大图则用于定位当前仍需要追平的部分。`),
  body(T`这些图不是为了凭视觉挑选有利区域。放大窗口由逐帧位置误差差异自动确定：优势序列寻找 KISS 误差相对 RAP 更大的连续窗口，劣势序列寻找 RAP 误差相对 KISS 更大的连续窗口。窗口位置、帧范围和局部平均误差都保留在图题与生成记录中。`),
  h2("轨迹在绘图前做了什么处理"),
  body(T`原始预测轨迹和 GT 不保证直接使用同一个初始坐标规约。绘图先按照评测口径处理 KITTI 相机到 LiDAR 的标定关系，再分别做首帧规约化，最后用相同的 SE(3) Umeyama 对齐把预测位置对齐到 GT。对齐只消除整体坐标系差异，不逐帧修改形状，也不做非刚性拉伸。六个序列的 G／K 轨迹 RMSE 均与 results06.json 中 r1 的 ATE 数值逐条核对。`),
  h2("FULL 与 ZOOM 的数字怎样理解"),
  bullet(T`FULL 标题中的 ATE 是整条序列的全局 RMSE，单位米。`),
  bullet(T`ZOOM 标题中的两个数是该窗口内逐帧位置误差的平均值，顺序为 RAP｜KISS，不是重新计算的局部 ATE RMSE。`),
  bullet(T`06 的窗口为 440–500 帧，07 为 120–180 帧，10 为 364–429 帧；它们用于问题定位，不代替全序列结论。`),
  h2("本页一句话收束"),
  plain(T`“轨迹图同时展示优势和短板：05 的贴合改善最清晰，06／07／10 的局部窗口给出了后续排查入口。”`, { bold: true, color: palette.primary }),
  pageBreak(),
);

slideIntro(4, "已完成工作与系统能力", "约 1.5 分钟");
children.push(
  h2("可直接口述的讲稿"),
  body(T`当前结果不是只调了一个模块，而是把输入、前端、完整对比和独立评测连成了一条可追溯链路。最明确的工程提升来自 E0 前端校正。在 07、09、10 上，平均 ATE 从 1.2177 米降到 0.7215 米，下降 40.7%；平均 ter 从 0.9595% 降到 0.5056%，下降 47.3%。这部分收益属于前端校正，不能记成新训练出来的 RAP 能力。`),
  body(T`在此基础上，我们完成了 6 序列、2 系统、3 重复的 36 组完整 raw-core 运行。预测结果先封存，再读取 GT 计算指标，并对 44,388 个 KITTI 分段做独立复核。这样可以把“系统真的改善”与“评测脚本或数据口径造成的差异”分开。`),
  h2("E0 与 raw-core 是什么"),
  body(T`E0 是前端输入与算术校正的一组工作，其中包括 KITTI Velodyne 的 0.205 度内在垂直角校正，以及 float32 前端算术口径恢复。它解决的是进入配准和 SLAM 主干之前的数据与实现一致性。raw-core 表示当前汇报约定的轨迹核心运行范围，用于统一两套系统的测量边界；它不等于包含所有命令行副产物、文件整理和外围操作的完整墙钟成本。`),
  h2("其他三项工作分别贡献什么"),
  bullet(T`输入核对：12,296 次扫描的输入字节与坐标逐项检查，保证后续比较使用相同数据与精度口径。`),
  bullet(T`并行与原生诊断：P0 完成 72 组采集／验证；N2 把两次原生运行首个可见差异定位到 ICP 返回，属于差异定位，不是性能提升。`),
  bullet(T`公开输入 GPU 链路：402 个模型张量完整加载，两个公开案例、56,557 个点出现次数完成真实前向与输出封存，证明链路可运行，不自动等于新配准收益。`),
  h2("本页一句话收束"),
  plain(T`“这一阶段最大的资产，是前端实际收益和一套可追溯的对比评测基础。”`, { bold: true, color: palette.primary }),
  pageBreak(),
);

slideIntro(5, "LoRA／MLP Adapter 训练复盘", "约 2 分钟");
children.push(
  h2("可直接口述的讲稿"),
  body(T`Adapter 这条线现在可以分成两个结论。第一，优化本身有效。两个模型都严格加载了 344 个检查点张量，443,904 个可训练值提升为 float64。V、P 两臂各完成 20 次保留更新，40 次全部通过参数、梯度、更新规则和 Armijo 条件检查。V 的 loss 下降 1.9757%，P 的 loss 下降 1.9806%，所以不能说训练没有起作用。`),
  body(T`第二，loss 的下降没有转化为最终配准收益。追加实验已经补齐 U、V20、P20 在 fit00 和全部 16 个 eval 噪声上的 51 例预测，并先封存再评估。训练后的平移均值只改善约 9 到 26 微米，远未达到实质性增益；联合不恶化只覆盖 3 到 5 个噪声，低于预设的 12 个。准确说法是“优化器优化了一个目标，但这个目标的下降没有带来稳定、显著的位姿改善”。`),
  h2("LoRA、final MLP 与 Adapter 分别是什么"),
  body(T`Adapter 是附加或开放给训练的一部分参数，用来在保留原模型主体的条件下调整行为。LoRA（Low-Rank Adaptation）把权重增量表示成低秩矩阵 A、B 的乘积，从而减少需要学习的参数。final MLP 是模型末端的多层感知机输出头，直接影响最终预测。该实验开放的是 LoRA A／B 与 final MLP 等共 443,904 个可训练值，不是重新训练整个模型。`),
  body(T`初始 B=0 时，A 的梯度在结构上为 0，这是低秩分支的已知性质，不应直接误判为反传失效。后续通过临时激活和导数检查确认了局部 A／B 梯度可用。本页的训练是固定前缀、双精度尾部的影子函数实验，不等于原始 native／AdamW 路径已经修复。`),
  h2("V／P、Armijo 与 51 例怎样解释"),
  bullet(T`V／P 是实验协议中两类原始目标及对应训练臂的标记，分别训练和评估；汇报时直接沿用 V／P，避免把不同目标混为一谈。`),
  bullet(T`Armijo 条件是一种下降充分性检查。40／40 通过说明每次实际更新都满足预定的数值下降要求，但不保证下游任务指标改善。`),
  bullet(T`U 是未适配基线，V20／P20 是训练后的两臂。每个臂有 1 个 fit00 诊断案例和 16 个 eval 噪声案例，因此 3×17=51 例；fit00 不计入 16 噪声门禁。`),
  bullet(T`“联合不恶化”要求平移和旋转等条件共同满足，不能仅凭某一项均值略降就判定有效。`),
  h2("后续为什么不简单增加更新次数"),
  body(T`当前瓶颈不是“没有完成训练”，而是训练目标与最终配准质量之间缺少有效对应。继续在相同证据上增加步数、改步长、挑选噪声或放宽阈值，会改变原实验问题，不能据此宣称修复。后续应提出新的监督目标，使 loss 更直接对应相对位姿误差或最终配准质量，再经过共同输入的强几何对照，最后才进入真实序列和系统级 ATE／ter／rer 评估。`),
  h2("本页一句话收束"),
  plain(T`“这条线已经证明‘能训练、能降 loss’，追加实验进一步说明‘还需要让训练目标真正服务于配准’。”`, { bold: true, color: palette.primary }),
  pageBreak(),
);

slideIntro(6, "当前差距与优化入口", "约 1.5 分钟");
children.push(
  h2("可直接口述的讲稿"),
  body(T`当前最大的系统差距是效率。RAP-SLAM 平均吞吐为 11.39 FPS，KISS-SLAM 为 27.09 FPS，约为我们的 2.38 倍。更关键的是 p99 帧耗时：RAP-SLAM 为 137.36 毫秒，KISS-SLAM 为 69.42 毫秒。平均 FPS 高于 10 并不表示每一帧都能稳定满足 10 Hz，因为长尾帧会超过 100 毫秒预算并造成队列积压。`),
  body(T`精度方面，06、07、10 的 ATE 仍分别比 KISS-SLAM 高 6.9%、2.9% 和 6.4%；07 的 ter 和 10 的 rer 也未达到保护要求。因此后续不是只追求平均值继续下降，而是要在保持平均优势的同时，消除具体序列和具体指标上的退步。`),
  h2("FPS、p99 与稳定 10 Hz 的区别"),
  body(T`FPS 是单位时间处理帧数，通常反映平均吞吐。p99 表示 99% 的帧耗时不超过该值，剩下约 1% 更慢，用于观察尾延迟。10 Hz 对应每帧 100 毫秒时间预算。如果平均处理很快但偶发长帧过多，在线系统仍会积压。下一阶段把 p99 先压到 100 毫秒以内，是进入稳定 10 Hz 验证的必要步骤，但还需要逐帧到达和队列测量来确认。`),
  h2("串行帧时钟告诉我们什么"),
  body(T`当前串行帧时钟中，准备与独立前端占 46.8%，地图与闭环占 53.2%。两个部分都接近一半，说明只优化单个小函数很难解决整体问题。后续需要分别压缩两条链路，再验证并行是否真正减少关键路径耗时。并行不自动等于提速，因为数据依赖、同步和 GPU／CPU 资源竞争仍可能限制收益。`),
  h2("本页一句话收束"),
  plain(T`“效率要抓住 p99 和两条耗时链路，精度要抓住 06／07／10，而不是只看六序列平均。”`, { bold: true, color: palette.primary }),
  pageBreak(),
);

slideIntro(7, "下一阶段目标与预期", "约 1 分钟");
children.push(
  h2("可直接口述的讲稿"),
  body(T`下一阶段设定两个同步目标。第一，保持平均精度优势，平均 ATE 不高于 0.6483 米，平均 ter 不高于 0.44695%，并重点消除 07 ter 和 10 rer 的保护失败。第二，把 p99 从 137.4 毫秒压到 100 毫秒以内，至少下降 27.2%，随后再向 KISS-SLAM 的 69.4 毫秒靠近。`),
  body(T`具体工作分三项：分链路压缩准备／前端与地图／闭环耗时；围绕 06、07、10 的分段误差和图边作用定位退化来源；在相同输入和工作量下，比较联合 RAP、独立两视图 RAP 和强几何基线，确认收益来自哪里。最终验收不只看 p99，还要用完整逐帧到达和队列测量验证稳定在线 10 Hz。`),
  h2("为什么强调“保护”"),
  body(T`保护是优化时的约束：不允许为了改善平均值或某一个序列，让既定关键指标出现不可接受的退步。平均 ATE 与 ter 是总体保护线，07 ter 和 10 rer 是当前已知的逐序列保护点。只有精度保护和实时性目标同时满足，才可以把优化视为系统级进展。`),
  h2("预期结果的边界"),
  bullet(T`100 毫秒是阶段目标，不是已经完成的结果。`),
  bullet(T`“稳定 10 Hz”需要在线到达与队列证据，不能由离线平均 FPS 直接替代。`),
  bullet(T`机制比较必须保持输入、初始化和工作量口径一致，否则无法判断增益来自模型、额外计算还是其他因素。`),
  h2("整场汇报的结束语"),
  plain(T`“我们已经有可量化、可追溯的平均精度优势。下一步是在不牺牲这项优势的前提下，把逐序列短板和尾延迟压下来，并用完整在线测量证明系统可用性。”`, { bold: true, color: palette.primary }),
  pageBreak(),
  h1("九、专业术语速查"),
  table(["术语", "中文／全称", "本项目中的含义与讲解口径"], [
    ["SLAM", "同步定位与建图", "同时估计传感器轨迹并构建环境地图；本项目重点关注轨迹精度与在线运行能力。"],
    ["LiDAR", "激光雷达", "输出三维点云扫描，是系统的主要观测输入。"],
    ["Odometry", "里程计", "根据连续扫描估计局部运动；长期累计会产生漂移。"],
    ["Loop closure", "回环", "再次访问相近区域时建立非相邻约束，用于修正全局漂移。"],
    ["Registration", "点云配准", "求两个点云或视图之间的旋转和平移，使其落到共同坐标关系下。"],
    ["Pose graph", "位姿图", "节点表示位姿，边表示相对位姿约束；后端通过联合优化调整轨迹。"],
    ["GTSAM", "图优化库", "当前后端使用的优化工具，用于融合里程计边和回环边。"],
    ["KISS-ICP", "局部 ICP 前端", "负责局部点云配准和里程计，是当前系统的重要几何基础。"],
    ["KISS-SLAM", "本地强基线", "用于同输入、同实验协议比较；PPT 中的 K 即 KISS-SLAM。"],
    ["GT", "Ground Truth／真值", "评测使用的参考轨迹；预测先封存再读取 GT，避免评测选择偏差。"],
    ["ATE", "绝对轨迹误差", "全局轨迹位置 RMSE，单位米；本报告使用 SE(3) 对齐结果。"],
    ["ter", "相对平移误差", "KITTI 风格分段相对漂移，单位百分比，越低越好。"],
    ["rer", "相对旋转误差", "KITTI 风格分段旋转漂移，单位度每百米，越低越好。"],
    ["SE(3)", "三维刚体变换群", "只包含旋转和平移；用于轨迹对齐，不做尺度改变。"],
    ["Umeyama 对齐", "刚体／相似变换估计", "这里关闭尺度校正，以位置求整体旋转和平移，使预测与 GT 坐标规约一致。"],
    ["raw-core", "轨迹核心测量范围", "本次统一对比的运行边界，不包含所有 CLI 与外围副产物。"],
    ["FPS", "每秒处理帧数", "平均吞吐指标；不能单独证明稳定逐帧实时。"],
    ["p99", "第 99 百分位耗时", "用于描述尾延迟；当前 137.36 ms 高于 10 Hz 的 100 ms 帧预算。"],
    ["LoRA", "低秩适配", "通过低秩 A／B 矩阵学习权重增量，是 Adapter 训练的一部分。"],
    ["MLP", "多层感知机", "final MLP 是模型输出头，本实验与 LoRA 参数一起训练。"],
    ["loss", "训练目标损失", "优化器直接降低的量；其下降不必然带来最终位姿或系统指标改善。"],
    ["Armijo", "充分下降条件", "用于检查每次参数更新是否满足预定下降要求，不等同于泛化验证。"],
    ["heldout／eval", "保留评估", "不参与当前拟合的噪声或数据，用于检查训练结果是否超出拟合案例。"],
    ["U／V20／P20", "未训练与训练臂", "U 为未适配基线；V20／P20 分别完成 20 次保留更新。"],
    ["联合不恶化", "多条件安全门禁", "要求平移、旋转及逐噪声条件共同满足，不能用单项均值改善代替。"],
  ]),
  pageBreak(),
  h1("十、常见提问与回答要点"),
  h2("1. 你们是不是已经全面超过 KISS-SLAM？"),
  body(T`不是。当前六序列平均 ATE、ter、rer 都优于本地同跑 KISS-SLAM，00／05／09 三项同向改善；但 06／07／10 仍有部分指标差距，吞吐和 p99 也明显落后。准确结论是“平均精度领先，效率和逐序列一致性仍需提升”。`),
  h2("2. 公开方法表格能否当成严格排行榜？"),
  body(T`不能完全等同。表格统一了六序列算术平均，但其他方法仍来自各自论文，不是本地统一重跑。它适合说明竞争力区间；严格同条件结论仍以本地 RAP 与 KISS 的对比为主。`),
  h2("3. 05 的提升主要来自哪里？"),
  body(T`结果上已经确认全局和相对误差同步改善，但不能只凭指标把全部收益归因于某一个模块。需要继续结合前端变化、回环边接受位置和图优化作用做分解。E0 前端校正与 RAP 回环贡献应在汇报中分开表述。`),
  h2("4. 轨迹图是否挑选了有利区域？"),
  body(T`窗口按预定误差差异规则自动选取，优势与劣势序列使用对称规则，并同时展示完整轨迹。局部图用于定位，不替代全序列 ATE，也不手工删除不利帧。`),
  h2("5. Adapter 的 loss 下降为什么仍说没有收益？"),
  body(T`因为训练目标和最终任务指标不同。loss 下降约 1.98% 只说明优化器在既定目标上有效；完整 16 噪声评估中，平移均值只改善约 9–26 微米，且联合不恶化未达门禁，所以没有形成有实际意义的配准收益。`),
  h2("6. 是否说明 LoRA／MLP 路线不可行？"),
  body(T`不能扩大为普遍不可行。已经完成的是固定合成任务、固定 20 次更新和双精度影子策略的负面对照。它说明当前目标与策略没有产生所需收益，后续需要不同科学假设和新对照，而不是给所有 Adapter 方法下结论。`),
  h2("7. 平均 11.39 FPS 为什么还不能说稳定 10 Hz？"),
  body(T`平均吞吐不能覆盖尾延迟和排队。p99 为 137.36 毫秒，说明慢帧超过 100 毫秒预算。稳定在线 10 Hz 还需要逐帧到达、处理时间和队列长度的完整测量。`),
  h2("8. 下一阶段最重要的验收结果是什么？"),
  body(T`在平均 ATE 和 ter 不退化、07／10 保护点改善的同时，把 p99 压到 100 毫秒以内，并用在线队列数据验证稳定 10 Hz。精度保护与实时性必须一起通过。`),
  pageBreak(),
  h1("十一、数据口径与实验记录索引"),
  body(T`以下项目记录用于备查。讲稿中的性能数字以当前 PPT 和这些已保存实验记录为依据；文献横向值与本地同跑结果保持分开。`),
  table(["记录", "路径", "主要用途"], [
    ["S1 raw-core", "docs/maintenance/2026-10-20/raw-input-contract-01/results06.json", "六序列 RAP／KISS 的 ATE、ter、rer、重复运行与轨迹 r1 校验。"],
    ["横向文献对比", "docs/maintenance/2026-09-19/horizontal-comparison-01/COMPARISON_TABLE_V1.md", "公开方法的逐序列 ter 与 ATE 文献值来源。"],
    ["轨迹图生成记录", "working files/decks/rap_slam_weekly-b5533638/media/trajectory_atlas_details.json", "六序列放大窗口、局部平均误差与 r1 ATE。"],
    ["E0-H1", "docs/maintenance/2026-09-27/e0-heldout-01/REPORT.md", "07／09／10 前端校正的 ATE 与 ter 改善。"],
    ["Adapter 追加实验", "docs/maintenance/2026-10-25/shadow-adapter-restart-01/REPORT.md", "40 次更新、loss 下降、51 例预测和 16 噪声最终配准结论。"],
    ["项目阶段复盘", "docs/maintenance/2026-10-16/broad-state-review-01/REPORT.md", "系统结构、已有工程收益、模型证据边界和后续决策。"],
  ]),
  h2("汇报时的最终口径提醒"),
  bullet(T`把“已经测得的提升”“数值链路通过”“下一阶段目标”分开讲。`),
  bullet(T`把“公开论文值”与“本地同跑”分开讲。`),
  bullet(T`把“训练 loss 下降”与“最终配准／系统收益”分开讲。`),
  bullet(T`把“平均 FPS”与“稳定在线 10 Hz”分开讲。`),
  note("文档结束。建议汇报前按每页“可直接口述的讲稿”通读一遍，技术解释和问答部分作为备查，不必全部现场展开。"),
);

const doc = new Document({
  creator: "Kimi Work",
  title: "RAP-SLAM 每周组会汇报逐页讲稿、技术解释与术语说明",
  description: "对应2026-10-25版七页RAP-SLAM组会PPT",
  features: { updateFields: true },
  numbering: { config: [{ reference: "bullets", levels: [{ level: 0, format: "bullet", text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 520, hanging: 260 } } } }] }] },
  styles: { default: { document: { run: { font, size: 22, color: palette.dark }, paragraph: { spacing: { after: 150, line: 330 } } } } },
  sections: [{
    properties: { page: { margin: { top: 1300, bottom: 1300, left: 1440, right: 1440 } } },
    headers: { default: new Header({ children: [para(run("RAP-SLAM 组会汇报｜逐页讲稿与术语说明", { size: 17, color: palette.muted }), { alignment: AlignmentType.RIGHT, spacing: { after: 40 } })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 18, color: palette.muted }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(doc));
