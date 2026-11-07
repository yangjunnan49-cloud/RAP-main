import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, Header, HeadingLevel, ImportedXmlComponent,
  Packer, PageNumber, Paragraph, ShadingType, Table, TableCell, TableRow,
  TextRun, WidthType, convertInchesToTwip,
} from "docx";

const T = String.raw;
const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node create.js /absolute/path/output.docx");

const font = {
  ascii: "Times New Roman",
  hAnsi: "Times New Roman",
  cs: "Times New Roman",
  eastAsia: "SimSun",
};
const run = (text, options = {}) => new TextRun({ text, font, size: 22, ...options });
const para = (children, options = {}) => new Paragraph({
  spacing: { after: 120, line: 300 },
  ...options,
  children: Array.isArray(children) ? children : [children],
});
const p = (text) => para(run(text), { indent: { firstLine: convertInchesToTwip(0.33) } });
const pn = (text) => para(run(text)); // 无缩进（问答、列表）
const h1 = (text) => para(run(text, { bold: true, size: 32 }), { heading: HeadingLevel.HEADING_1, spacing: { before: 320, after: 160 } });
const h2 = (text) => para(run(text, { bold: true, size: 26 }), { heading: HeadingLevel.HEADING_2, spacing: { before: 240, after: 120 } });
const bq = (text) => para(run(text, { bold: true, color: "8A0000" }), { indent: { left: convertInchesToTwip(0.3) }, spacing: { after: 60 } });
const bp = (text) => para(run(text), { indent: { left: convertInchesToTwip(0.3) }, spacing: { after: 120 } });
const pageBreak = () => new Paragraph({ children: [new TextRun({ children: ["page"], break: 1 })] });

const toc = (entries) => {
  const xmlEscape = (v) => String(v)
    .replaceAll("&", "&amp;").replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;").replaceAll('"', "&quot;");
  const cached = entries.map(({ title, level, page }) => {
    const indent = Math.max(0, level - 1) * 360;
    return `<w:p><w:pPr><w:pStyle w:val="TOC${level}"/>
      <w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9000"/></w:tabs>
      <w:ind w:left="${indent}"/></w:pPr>
      <w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:eastAsia="SimSun"/></w:rPr><w:t>${xmlEscape(title)}</w:t></w:r><w:r><w:tab/></w:r><w:r><w:t>${page}</w:t></w:r></w:p>`;
  }).join("");
  return ImportedXmlComponent.fromXmlString(`<w:sdt xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:sdtPr><w:alias w:val="目录"/></w:sdtPr>
    <w:sdtContent>
      <w:p><w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/>
        <w:instrText xml:space="preserve"> TOC \\o &quot;1-2&quot; \\h \\z \\u </w:instrText>
        <w:fldChar w:fldCharType="separate"/></w:r></w:p>
      ${cached}
      <w:p><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>
    </w:sdtContent>
  </w:sdt>`).root[0];
};

// ---------- 内容 ----------
const children = [];

children.push(h1("RAP 课题组会口稿（2026-09-30）"));
children.push(pn("用途：配合同目录 PPT《rap_weekly_20260930.pptd》使用。第一部分是开场与逐页口稿，第二部分是预判问答，第三部分是术语速查，第四部分是表述红线。建议会前通读第二、四部分；会上照第一部分的骨架讲。"));
children.push(pn("页码为估计值，在 Word 中右键目录 → 更新域 即可刷新。"));

children.push(toc([
  { title: "一、开场白（约 1 分钟）", level: 1, page: 1 },
  { title: "二、逐页口稿（对应 PPT 第 1–6 页）", level: 1, page: 2 },
  { title: "三、预判问答（老师可能提的问题与建议回答）", level: 1, page: 5 },
  { title: "四、知识补充：术语速查", level: 1, page: 10 },
  { title: "五、表述红线（会上不能说的话）", level: 1, page: 12 },
]));

children.push(h1("一、开场白（约 1 分钟）"));
children.push(p("老师好，我汇报这段时间的工作。这阶段我没有去堆新的模型改动，而是把系统的误差来源彻底归因了一遍：共做了 11 项实验与审计，其中 9 项是阴性结果。但这些阴性结果不是白做的——每一项都排除了一类解释。现在的结论是：前端里程计没有明显问题，指标矛盾集中在回环位姿写入轨迹的方式上；下一步有一个定义清楚、成本很低、成败标准预先注册好的诊断实验。另外，上次组会老师问的 RAP 和 KISS-ICP 的发表出处、引用情况，我这次专门补查并做了一页汇总。"));

children.push(h1("二、逐页口稿（对应 PPT 第 1–6 页）"));

children.push(h2("第 1 页：阶段工作总览"));
children.push(p("这页是实验清单，全部可追溯到我们维护目录里的冻结记录。每一项实验都遵循同一套流程：先把输入身份和代码哈希冻结，生成不含真值的中间结果并密封，由独立的校验脚本复核，最后评估器才允许读真值。右边信号列：加号是正向，减号是负向，正负号是诊断价值。"));
children.push(p("需要说明的心态问题：11 项里 9 项阴性。 my view 是这些阴性结果共同回答了'瓶颈不在哪'——特征信息、强度信息、点选择约定、支持结构、时间持续性、因果传输，这六类解释全部被排除。C2 那项是机制证据：把输入特征打乱后，模型输出的位姿在 6/7 个普通对上显著改变，说明 RAP 确实在用我们给它的特征，不存在'模型根本没读到输入'的低级问题。"));

children.push(h2("第 2 页：全系统指标审计结果"));
children.push(p("这张表是六条 KITTI 序列上里程计和全系统两条轨迹线的指标。首先看一个稳定现象：回环让 ATE 下降、但让 ter 上升，两组三序列的均值都是这样。这说明两个指标的目标存在冲突，任何'改进'必须讲清楚优化的是哪个口径。"));
children.push(p("最有信息量的是上界检验：我们把 58 条已经接受的回环逐条换成真值位姿——相当于假设环已经做到完美——单条对 ter 的最大改善只有 0.0074 个百分点。也就是说，就算把回环位姿全部做准，ter 也基本不会动。所以 ter 的矛盾不在'环准不准'，而在环进入图之后的轨迹重建。这就是下一步传播诊断的依据。"));
children.push(p("另外两个现象：09 序列上 10 个严格意义上错误的环（平移差 3.6 到 4.1 米）反而让全局 ATE 改善了 0.13 米——说明'单个环位姿准不准'和'对图有没有用'是两回事；10 序列 11 次尝试 0 接受，因为 15 米检索半径内就没有真值重访，这是检索缺口。"));

children.push(h2("第 3 页：论文出处、引用与团队地位"));
children.push(p("这页直接回答上次组会的提问。RAP 今年 12 月挂 arXiv，已被 ECCV 2026 接收，引用目前约 10 次——它是刚发表的顶会新工作，不是我们通常说的'久经检验的 SOTA'。KISS-ICP 发在 IEEE RA-L 2023，被引约 790；KISS-SLAM 发在 IROS 2025。三篇都是波恩大学 Stachniss 实验室的工作，这个组在 LiDAR SLAM 领域的地位不用多说，SuMa、PIN-SLAM 都是他们做的。"));
children.push(p("下面'口径说明'是回应'指标弱于 SOTA'：上次的对比是全系统对全系统，这次我们补了同数据的口径——我们的里程计 ter 和 KISS-SLAM 全系统 ter 在 07、09、10 三个序列上是同一水平，07 和 09 还略好。我要强调这是描述性对比，两条管线不同，不构成受控的优越性声明；它能说明的是'前端没有大幅差距'，真正的差距在回环段。"));

children.push(h2("第 4 页：RAP 模型解剖"));
children.push(p("左边是 RAP 的完整流程：输入 2 到 16 个无序点云，不要位姿初值；每个视角做体素降采样和离群剔除，用最远点采样选关键点，MiniSpinNet 提 32 维局部特征；然后把所有视角规范化到一个单位立方体里消掉全局位姿和尺度；核心是一个 10 层、7300 万参数的扩散 Transformer，学一个条件速度场；采样走 10 步欧拉积分，每一步都做一次 SE(3) 刚性投影，最后按视角切分、用 Kabsch 算法恢复每个视角的位姿。"));
children.push(p("右边上面是训练数据解析：17 个数据集、10 万多个多视角实例，训练成本是 32 张 A100 跑 3 天。右边下面是关键——我们部署和论文的差异：论文用的是自适应体素加 FPS 采样，我们本地管线用的是固定 0.4 米体素加固定点数随机采样；本地权重是 12 层，论文写的是 10 层；而且本地权重的训练数据划分未知。这些差异我们专门做过一个实验（P0）去对齐论文配方，结果信号仍然是阴性，所以差异存在，但没有证据说它是性能问题的原因。"));

children.push(h2("第 5 页：SLAM-RAP 系统拆解"));
children.push(p("这是我们系统的数据流：KISS-ICP 做里程计，关键帧检索给出候选对，RAP 对候选对生成环位姿，门控接受后进 g2o 位姿图优化，最后把优化后的关键帧校正值以分段常数的方式传播到每一帧。解剖后发现的核心事实是接口 gap：RAP 原生输出的是点级联合结构——多视角全局一致的生成点云——但我们的系统只从里面取一条相对位姿，塞进稀疏图。RAP 最核心的能力在接口处被收窄成了一个位姿。"));
children.push(p("基于这个解剖，我们做的机制实验链共同指向一个结论：瓶颈是候选平移的生成——41 个最难的正样本对里，37 个的最佳位姿旋转误差在 5 度以内、但平移误差超过 1 米。也就是模型'方向看对了、距离没估准'，这不是特征信息能解决的。下一步是固定位姿传播诊断：只把分段常数传播改成相邻关键帧间的 SE(3) 插值，其他全部不动。门限预先写死：两组均值 ter 各降至少 0.01 个百分点、ATE 退化不超过 2%。注意这即便成功也只是工程收益，插值本身有 2020 年的先验，不是我们的原创贡献。"));

children.push(h2("第 6 页：途径与立场"));
children.push(p("左边四条途径按优先级排：传播诊断是下一项；RAP 点级结构进图接口是第二条，但要配等预算的几何对照，否则说不清收益来自哪；检索补齐和外部匹配器对照是条件触发的备选项。右边红框是我们的路线立场：非最后手段不微调、不重训练。理由有三：RAP 训练要 32 张 A100 跑 3 天，训练代码和数据策划代码没有开源，本地根本复现不了它的训练管线；我们的证据链显示输入侧干预全部阴性，没有证据表明微调有目标可挖；RAP 的定位是 zero-shot 通用配准，为我们的任务微调违背它的设计用法。"));
children.push(p("最后需要老师拍板一件事：是否同意'传播诊断 → 接口利用 → 检索或外部对照 → 微调垫底'这个优先级。"));

children.push(h1("三、预判问答（老师可能提的问题与建议回答）"));

children.push(h2("Q1：RAP 这篇论文到底发在哪？什么级别？"));
children.push(bq("建议回答："));
children.push(bp("RAP《Register Any Point: Scaling 3D Point Cloud Registration by Flow Matching》，波恩大学和斯坦福等，2025 年 12 月挂 arXiv（2512.01850），已被 ECCV 2026 接收。ECCV 是计算机视觉三大顶会之一。引用目前约 10 次——它是这个月刚正式发表的论文，引用积累才刚开始。所以它的'地位'要客观看：团队和方向是一流的，但'经过长期检验的 SOTA'这个表述目前不适用。"));

children.push(h2("Q2：KISS-ICP 和 KISS-SLAM 发在哪？引用量如何？"));
children.push(bq("建议回答："));
children.push(bp("KISS-ICP 发在 IEEE Robotics and Automation Letters（RA-L）2023 年第 8 卷，被引约 790（arXiv 页面）/ 568（Semantic Scholar），是点到点 ICP 路线的标杆工作，很多系统的默认前端。KISS-SLAM 发在 IROS 2025（DOI 10.1109/IROS60139.2025.11246613），发表约一年半，是 LiDAR-only SLAM 的新强基线，卖点是零调参跨传感器泛化。三篇都是波恩大学 PRBonn（Stachniss 组）的工作。"));

children.push(h2("Q3：为什么我们的指标比 KISS-SLAM 差？"));
children.push(bq("建议回答："));
children.push(bp("要分口径。上次的对比是全系统 ter 对全系统 ter。这次审计补了同数据口径：我们的里程计 ter 在 07/09/10 上是 0.3838/0.5194/0.5285%，KISS-SLAM 全系统 ter 是 0.3866/0.5421/0.5250%——07、09 我们略好，10 只差 0.0035 个百分点，量级相当。我们的差距集中在回环段：回环使 ter 上升、ATE 下降，这是两个指标目标冲突的表现。必须向老师承认边界：这是描述性对比，两条管线不同，不是受控实验；它排除的是'前端有大幅差距'这个解释，而不是证明我们全面领先。"));

children.push(h2("Q4：RAP 论文里 KITTI 配对成功率 100%，为什么到你们系统里效果一般？"));
children.push(bq("建议回答："));
children.push(bp("三个层面的差异。第一，论文的 100% 是配对注册成功率，阈值 2 米/5 度，且是平衡采样的配对基准；我们的系统是在线检索候选、严格 1 米/5 度判据、还包含检索召回这一层。第二，部署差异：我们本地管线的点选择方式和论文配方不一致，本地权重是 12 层而论文写 10 层，权重训练划分未知——这些我们审计过但因果未验证。第三，系统指标不是配对成功率的线性叠加：09 序列上严格错误的环反而改善了全局 ATE，说明 pair 层面和系统层面之间隔着图优化和轨迹传播，这正是我们下一步要诊断的环节。"));

children.push(h2("Q5：有老师建议'深度解析 RAP、训练特殊层适配任务'，你们做了吗？"));
children.push(bq("建议回答："));
children.push(bp("拆解已经做了，成果就是 PPT 第 4、5 页；'训练特殊层'我们没有做，而且建议明确放在最后手段。理由有三条，都可以展开："));
children.push(bp("（1）成本与可行性：RAP 训练用 32 张 A100 跑 3 天，训练代码和数据策划代码官方未开源，本地无法复现其训练管线；在不了解其数据配比的情况下微调，本质上是盲调。"));
children.push(bp("（2）证据不支持：我们系统性地检验过输入侧的所有可挖信号——特征信息（C1/C3）、强度信息（I1）、对齐论文配方的点选择（P0）、支持结构（C4–C6/M1）——全部阴性。也就是说没有证据表明模型缺的是'任务适配'，微调大概率是堆工作量碰运气。"));
children.push(bp("（3）范式冲突：RAP 的设计定位是 zero-shot 通用配准模型，论文自己的卖点就是免微调泛化；为我们的特定任务微调，既违背其用法，也引入新的不可控变量，破坏结果可复现性。"));
children.push(bp("如果老师坚持，我们的承诺是：等免训练路线全部穷尽、且出现明确可检验的假设之后，把微调作为单独立项来评估。"));

children.push(h2("Q6：九个阴性结果，是不是说明这段时间白干了？"));
children.push(bq("建议回答："));
children.push(bp("恰恰相反，归因靠的就是阴性结果。在动手改任何东西之前，必须知道瓶颈在哪。这九项阴性结果分别排除了：特征信息量不足、强度通道可利用、点选择约定是主因、支持点特征可救回候选、时间持续性约束有效、因果传输有效、后端调参有效。排除完之后，归因收敛到两个具体事实：一是候选平移生成不足（37/41 失败对旋转合格、平移超差），二是回环校正传播方式存疑。这比同时开十条线赌一条能通，要便宜和可靠得多。"));

children.push(h2("Q7：下一步是什么？什么时候能看到正向指标？"));
children.push(bq("建议回答："));
children.push(bp("下一项是固定位姿传播诊断：只把关键帧校正从分段常数改成相邻关键帧间的 SE(3) 插值，其余完全不动。这是一个 CPU 上的只读诊断，预计一天内出结果。成败标准事先写死：两组均值 ter 各降至少 0.01 个百分点、ATE 退化不超过 2%、单序列 ter 恶化不超过 0.01 个百分点。需要向老师讲清楚：这即便过了门限，也只是工程收益，不是原创贡献；但它如果能把全系统 ter 压到里程计水平以下，我们的系统指标故事就完整了——里程计不输 KISS-SLAM，回环不再拖 ter，同时 ATE 保持改善。"));

children.push(h2("Q8：09 上那些'错误'的环为什么还留在系统里？不会把图带崩吗？"));
children.push(bq("建议回答："));
children.push(bp("这正是我们这期最重要的一个发现：09 序列 10 个严格错误的环（平移差 3.6–4.1 米）进入图之后，全局 ATE 反而改善了 0.13 米，ter 恶化 0.074 个百分点。图优化对回环误差有平均化能力，单个环的 pair 误差不等于图的误差。所以门控策略不能简单地按'严格对标签'砍——砍了这些环，ATE 会变差。这也是为什么我们把'严格对标签'从验收标准里降级为机制诊断指标。当然，这不等于错误的环都安全——我们不声称这套结论可以外推，这是 09 一个序列上的观察。"));

children.push(h2("Q9：和 KISS-SLAM 的对比公平吗？"));
children.push(bq("建议回答："));
children.push(bp("不完全受控，我们如实标注了。两条管线的检索、门控、图优化、传播方式都不同，KISS-SLAM 的局部里程计我们也没有单独隔离出来跑。所以我们只把它用作'量级参照'：说明前端没有大幅差距，而不声明优劣。如果老师要求严格对比，我们可以把 KISS-SLAM 的前端单独跑一遍同口径 ter——这需要排期，因为它不在当前冻结的诊断路径上。"));

children.push(h2("Q10：毕业论文的实验部分怎么办？写作还停着吗？"));
children.push(bq("建议回答："));
children.push(bp("写作保持暂停是有意的：在原创性突破未确立之前写论文，会倒逼我们去包装不成熟的结果，这是 methodological 风险。目前的计划是：传播诊断出结果后，系统指标故事（前端不输基线＋回环不拖 ter＋ATE 改善）就有了完整证据链，可以作为工程章节成稿；方法章节等 RAP 特异性的机制有阳性结果再启动。如果到期末方法章节仍无阳性结果，系统级充分归因＋完整的阴性证据链本身也构成一篇方法论扎实的硕士论文，这个备选方案希望老师认可。"));

children.push(h2("Q11（备用）：引用量还能再涨吗？要不要盯一下 RAP 的后续版本？"));
children.push(bq("建议回答："));
children.push(bp("RAP 官方仓库的 TODO 里有 v1.5 计划（换特征骨干、支持 4D 配准）和训练代码开源计划。建议保持跟踪：训练代码一旦开源，'微调'的可行性论证就需要重做，我们的'最后手段'立场也会重新评估。目前 v1.1 权重就是我们在用的版本。"));

children.push(h1("四、知识补充：术语速查"));
children.push(pn("会上被问到术语时可以照此解释；全部用一句话版本。"));

const terms = [
  ["ter / rer", "KITTI 官方里程计评测指标：把轨迹切成 100–800 米分段，计算平均相对平移误差（ter，%）和相对旋转误差（rer，°/100m）。它衡量局部一致性。"],
  ["ATE", "绝对轨迹误差：整条轨迹与真值对齐后的平均偏差，衡量全局一致性。ATE 与 ter 可能方向相反——回环常常降 ATE 但升 ter。"],
  ["回环（loop closure）", "机器人回到曾到过的地方时，用新观测约束旧位姿，消除累积漂移。回环位姿的误差会通过图优化传播到整条轨迹。"],
  ["位姿图优化 / g2o", "把每个关键帧看作图的节点、相对位姿测量看作边，最小化整体误差。g2o 是常用求解器。"],
  ["分段常数传播", "我们只优化关键帧位姿，关键帧之间的普通帧沿用'前一个关键帧的校正值'。校正在关键帧边界会跳变，这是被怀疑的 ter 恶化来源（未验证）。"],
  ["ICP / KISS-ICP", "迭代最近点：交替找对应点、解最优刚体变换。KISS-ICP 是'把朴素点到点 ICP 的各个细节做对'的系统（自适应阈值、鲁棒核、运动补偿），参数极少。"],
  ["flow matching（流匹配）", "一类生成模型：学一个速度场，把噪声点'运输'到目标点云。RAP 用它把多视角点云一步生成到配准后的状态，位姿是副产品。"],
  ["DiT / 交替注意力", "Diffusion Transformer。RAP 里 10 层结构，每层先在单个视角内部做自注意力（整合本视角结构），再对所有视角的token做全局注意力（跨视角融合）。"],
  ["刚性投影 / Kabsch / SVD", "流采样每步的'纠偏'：把当前预测用最优刚体变换（Kabsch 算法，基于 SVD）拉回 SE(3) 流形上，保证每个视角严格刚体。"],
  ["SE(3) 插值（Exp/Log）", "两个刚体变换之间的平滑过渡：C_s = C_a·Exp(α·Log(C_a⁻¹C_b))。下一步诊断要换上的传播方式。"],
  ["miniSpinNet / FPS / voxel", "miniSpinNet：轻量旋转不变局部描述子网络，3DMatch 预训练，输出 32 维。FPS：最远点采样，保证点分布均匀。voxel：体素降采样，控制点数。"],
  ["GT-free bank / 独立校验器", "我们的实验方法学：评估器读真值之前，所有中间结果先生成、哈希密封，再由独立脚本复核；防止'看到答案再调方法'。"],
  ["oracle 上界", "用真值替换某一步输入（如把环位姿换成 GT）来衡量这一步的潜在收益。是不可执行的理论上界，不能当作可实现的改进。"],
  ["ECCV / RA-L / IROS", "ECCV：欧洲计算机视觉会议，视觉三大顶会之一。RA-L：IEEE 机器人与自动化快报，机器人领域主流期刊（可被 ICRA/IROS 接收）。IROS：智能机器人与系统会议。CCF 分级：ECCV B 类，IROS C 类，RA-L 未单列但认可度等同主流期刊。"],
];
{
  const widths = [2400, 6400];
  const cell = (text, header) => new TableCell({
    children: [para(run(text, { bold: !!header, size: 20 }), { spacing: { after: 40, line: 264 } })],
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    width: { size: header ? widths[0] : widths[1], type: WidthType.DXA },
    shading: header ? { type: ShadingType.CLEAR, fill: "F2F2F2" } : undefined,
  });
  children.push(new Table({
    width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      new TableRow({ children: [cell("术语", true), cell("一句话解释", true)] }),
      ...terms.map(([k, v]) => new TableRow({ children: [cell(k), cell(v)] })),
    ],
  }));
}

children.push(h1("五、表述红线（会上不能说的话）"));
const redlines = [
  "不能说'我们的系统超过 KISS-SLAM'——只能说'同口径下里程计 ter 量级相当，07/09 略优'，并主动声明这是描述性、非受控对比。",
  "不能说'微调一定没用'——只能说'目前没有证据支持微调有目标可挖，列为最后手段'。",
  "不能把传播诊断说成'预期能提升'——它是假设检验，两种结果都有明确后续动作。",
  "不能说'阴性结果证明这条路走不通'——只能说'证明这个具体协议、这个形态下没有信号'。",
  "不能把 09 上'错误环改善 ATE'说成'错误环是好的'——只能说'严格对标签不能替代图效用评估'。",
  "不能承诺原创性突破的时间点—— owner's 目标是 RAP 特异性原创贡献，目前未确立，论文写作保持暂停。",
  "E0 的 07/09/10 是工程迁移结果，不能再称为新方法的'独立确认'。",
  "所有数字以冻结报告为准；会上被追问细节时，回答'以维护目录中的冻结记录为准'，不凭记忆报数。",
];
for (const item of redlines) children.push(pn("· " + item));

const doc = new Document({
  features: { updateFields: true },
  styles: {
    default: {
      document: { run: { font, size: 22 } },
    },
    paragraphStyles: [
      { id: "TOC1", name: "TOC 1", basedOn: "Normal", run: { size: 22 }, paragraph: { spacing: { after: 60, line: 280 } } },
      { id: "TOC2", name: "TOC 2", basedOn: "Normal", run: { size: 22 }, paragraph: { spacing: { after: 40, line: 280 }, indent: { left: 360 } } },
    ],
  },
  sections: [{
    headers: { default: new Header({ children: [para(run("RAP 课题组会口稿（2026-09-30）", { size: 18, color: "808080" }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT] }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});

fs.writeFileSync(outputPath, await Packer.toBuffer(doc));
console.log("written:", outputPath);
