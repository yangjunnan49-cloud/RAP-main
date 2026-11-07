from pathlib import Path
import json, hashlib, zipfile
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
SOURCE=Path('C:/Users/AAA/Downloads/RAP_SLAM_组会讲解与问答_20261011 (1).docx')
EXPECTED='6f1c500f3ee9b289df493c3dcb596419878347e1783478b560d110654513b55f'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
D=json.loads((BASE/'meeting_content.json').read_text(encoding='utf-8'))
doc=Document(SOURCE)
pending_page=False
for node in list(doc.element.body):
    if node.tag!=qn('w:sectPr'):doc.element.body.remove(node)

def para(t,style=None,bold=False,size=None):
    p=doc.add_paragraph(style=style)
    r=p.add_run(t)
    if bold:r.bold=True
    if size:r.font.size=Pt(size)
    return p
def heading(t,level=1):
    global pending_page
    p=doc.add_heading(t,level=level)
    p.paragraph_format.keep_with_next=True
    if pending_page:p.paragraph_format.page_break_before=True;pending_page=False
    return p
def page():
    global pending_page
    pending_page=True
def table(values,widths=None,size=10.5):
    tab=doc.add_table(rows=1,cols=len(values[0]))
    tab.alignment=WD_TABLE_ALIGNMENT.CENTER
    tab.autofit=False
    if widths:
        for c,w in zip(tab.columns,widths):c.width=Inches(w)
    for ri,vals in enumerate(values):
        cells=tab.rows[0].cells if ri==0 else tab.add_row().cells
        if widths:
            for c,w in zip(cells,widths):c.width=Inches(w)
        for ci,(cell,val) in enumerate(zip(cells,vals)):
            cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            p=cell.paragraphs[0];p.paragraph_format.space_after=Pt(2);p.paragraph_format.space_before=Pt(2);p.paragraph_format.line_spacing=1.08
            p.alignment=WD_ALIGN_PARAGRAPH.LEFT if ci==0 else WD_ALIGN_PARAGRAPH.CENTER
            r=p.add_run(str(val));r.font.name='Times New Roman';r.font.size=Pt(size);r.bold=(ri==0)
            r._element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'SimSun')
            props=cell._tc.get_or_add_tcPr()
            margins=OxmlElement('w:tcMar')
            for tag in ['top','left','bottom','right']:
                e=OxmlElement('w:'+tag);e.set(qn('w:w'),'85');e.set(qn('w:type'),'dxa');margins.append(e)
            props.append(margins)
            if ri==0:
                sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'EEEEEE');props.append(sh)
        if ri==0:
            trpr=tab.rows[0]._tr.get_or_add_trPr();rep=OxmlElement('w:tblHeader');trpr.append(rep)
        for row in tab.rows:
            trpr=row._tr.get_or_add_trPr()
            if trpr.find(qn('w:cantSplit')) is None:trpr.append(OxmlElement('w:cantSplit'))
    borders=OxmlElement('w:tblBorders')
    for edge in ['top','left','bottom','right','insideH','insideV']:
        e=OxmlElement('w:'+edge);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'5');e.set(qn('w:color'),'D9D9D9');borders.append(e)
    tab._tbl.tblPr.append(borders)
    if len(values)<=8:
        for r in tab.rows[:-1]:
            for c in r.cells:
                for p in c.paragraphs:p.paragraph_format.keep_with_next=True
    doc.add_paragraph().paragraph_format.space_after=Pt(0)
    return tab
def link(label,url,paragraph=None,font_size=10.5):
    p=paragraph if paragraph is not None else doc.add_paragraph();p.paragraph_format.space_after=Pt(4)
    rel=p.part.relate_to(url,'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink',is_external=True)
    hyp=OxmlElement('w:hyperlink');hyp.set(qn('r:id'),rel)
    run=OxmlElement('w:r');rp=OxmlElement('w:rPr');c=OxmlElement('w:color');c.set(qn('w:val'),'245387');rp.append(c)
    f=OxmlElement('w:rFonts');f.set(qn('w:ascii'),'Times New Roman');f.set(qn('w:hAnsi'),'Times New Roman');f.set(qn('w:eastAsia'),'SimSun');rp.append(f)
    sz=OxmlElement('w:sz');sz.set(qn('w:val'),str(round(2*font_size)));rp.append(sz);run.append(rp)
    text=OxmlElement('w:t');text.text=label;run.append(text);hyp.append(run);p._p.append(hyp)
    return p
def caption(t):
    p=para(t,size=10);p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.space_after=Pt(8)

para('RAP SLAM 组会讲解与实验思路',style='Title')
para('汇报日期 2026年10月18日    建议用时 15至20分钟')
para('内容整合 10月11日系统与适配结果    本周进展截至10月17日')
heading('本次汇报重点')
para('完整系统已形成固定配置的六序列比较基线。原生小任务适配保留四组新噪声均值改善的信号。本周进一步完成双精度末端的导数、函数下降、五步采样绑定与40次保留更新，并完成非局部多视图对照和RegX输入参考契约。下一步围绕全局轨迹精度，采用成熟测量后端与同输入增量比较组织开发。')
heading('开场口稿',2)
para('这次将上次尚未汇报的工作和最近一周的新进展整合在一起。前一阶段，我们建立了完整系统比较，也在原生小任务适配上看到正向信号。本周继续把适配的数值链路推进到可复现梯度、实际下降和连续更新，同时完成真实非局部多视图比较，以及独立的输入与参考接口。下面先简要介绍系统基础，再重点讲本周推进了哪些技术环节，以及下一步怎样回到完整轨迹收益。')
heading('讲述顺序与时间',2)
table([['PPT页','内容','建议时间']]+[[str(i+1),s['title'],f"{s['time']:.1f} 分钟"] for i,s in enumerate(D['slides'])],[.55,5.2,1.02],9.5)
para('逐页口稿合计约17分钟。问答、术语和完整数据位于后文，供现场按需展开。',size=10.5)
page()

for i,s in enumerate(D['slides']):
    heading(f"第{i+1}页  {s['title']}")
    timing=para(f"建议讲述时间 {s['time']:.1f} 分钟",size=10)
    timing.paragraph_format.keep_with_next=True
    for t in s['talk']:para(t)
    if i==0:
        table(D['system_table'],[.5,1.8,1.8,2.67],9.6)
        para('单元格为平移漂移[%]和对齐轨迹误差[m]。系统成绩来自10月11日完整比较，GeoTransformer来自此前同输入受控替换。',size=10)
    elif i==2:
        table([['16个新噪声','原始平移[cm]','适配平移[cm]','均值改善','平移旋转共同不差'],['合成部分1','15.739','14.206','9.7%','9/16'],['合成部分2','15.119','12.432','17.8%','11/16'],['真实部分1','8.112','7.589','6.4%','5/16'],['真实部分2','28.300','24.944','11.9%','12/16']],[1.4,1.25,1.25,1.0,1.87],9.7)
    elif i==3:
        table([['数值环节','范围','结果'],['双精度末端方向导数','速度与位姿目标','12/12'],['低秩分支激活','A、B与末端层','18/18'],['局部矩阵导数重建','完整A/B乘积','32/32'],['五步采样绑定','两噪声两路径两重复','8条逐数组一致']],[2.5,2.6,1.67],10)
        para('既有刚体对照也为该路线提供基础：12个刚体参数的目标全部收敛，单位缩放将初始条件数从205.07降到1.002，迭代数由12降到4。',size=10.5)
    elif i==4:
        table([['训练目标','更新前','20次更新后'],['速度V','7.22996671078 × 10⁻⁶','7.08712625394 × 10⁻⁶'],['位姿P','198.329989556','194.401887634']],[1.4,2.68,2.69],10.3)
    elif i==6:
        table([['分组','视图/测量','联合RAP[m]','独立RAP[m]','实用同步几何[m]'],['00','9/8','0.783035','0.798717','0.817210'],['05','3/2','0.076709','0.083672','0.029842'],['07','10/12','0.155169','0.122062','0.124498'],['09','7/10','3.917151','3.910271','3.900829'],['全体','29/32','1.482851','1.472642','1.471863']],[.6,1.12,1.5,1.5,2.05],9.7)
    elif i==9:
        table([['核验项目','数量或结果'],['样本记录与源点云','2条记录 3份点云'],['视图与点出现次数','5次视图出现 56557点出现次数'],['正向坐标比较','169671次 全部通过'],['逆向坐标比较','169671次 全部通过'],['最大误差预算使用率','正向0.66% 逆向0.38%'],['固定执行阶段','4个阶段全部通过']],[3.0,3.77],10.2)
    elif i==10:
        table([['阶段','工作重点','预期交付'],['工程可行性','直接点云测量因子接口与资源','固定E0前端的比较范围'],['有限开发','优先处理00/05全局精度','ATE及安全开销对照'],['RAP增量','共同输入的几何与模型比较','正确对齐或恢复能力'],['完整评价','冻结后检查六条完整序列','逐序列指标与运行开销']],[1.08,3.16,2.53],10)

page()
heading('导师可能追问的答法')
for q,a in D['qa']:
    heading(q,2);para(a)

page()
heading('此前系统与地图试验的技术脉络')
para('这部分保留原材料中的实验理由，便于解释本周工作的来源。各项结果对应其固定构造和数据范围。')
table([['路线','主要观察','形成的技术选择'],['逐帧传播与回环参考诊断','固定插值漂移改善不足0.001个百分点。参考回环替换使07/09/10的ATE改善16.0%。','回环和完整轨迹联动评价。'],['外部匹配器与信息权重','71对严格成功RAP46、Geo44。信息权重开发组ATE改善0.71%。','增加强匹配器不自动形成系统收益，保留完整轨迹对照。'],['局部运动与学习读出','58窗口RAP平移中位9.49cm。联合读出0.888m、分离1.392m，同点几何约0.097m。','转向生成器实际输出与有限参数适配。'],['地图精修','06六自由度精修端点平移误差降低75.7%。05保护旋转后反而增加18.6%。','位姿指标参与方案选择，留出残差单独分析。'],['参考位置重建分组','48扫描约28.8万点，三案例训练代价仍偏好原始位姿。','继续重视测量关系与参考的一致性。']],[1.2,3.2,2.37],9.5)
heading('刚体数值对照',2)
table([['对照','迭代/求值','最大平移误差','初始条件数'],['原始单位直接位姿','12/14','3.28 × 10⁻¹⁰ m','205.07'],['原始单位点输出解码','12/14','3.28 × 10⁻¹⁰ m','205.07'],['单位缩放直接位姿','4/6','5.39 × 10⁻¹² m','1.002'],['单位缩放点输出解码','4/6','5.40 × 10⁻¹² m','1.002']],[2.4,1.0,2.1,1.27],9.7)
para('已知变换、固定锚帧、双精度和线搜索构成该数值对照。其结果为损失与解码的工程实现提供可检查的基准。')

page()
heading('基础知识与关键术语')
for t,p in D['glossary']:heading(t,2);para(p)

page()
heading('相关论文与技术资料')
for name,role,url in D['references']:
    p=doc.add_paragraph();p.paragraph_format.space_after=Pt(2);p.paragraph_format.keep_with_next=True
    p.add_run(name+'  ').bold=True;p.add_run(role)
    link(url,url)

page()
heading('完整系统三次成绩')
rr=json.loads((ROOT/'docs/meeting_20261011/benchmark/attempt03/results.json').read_text(encoding='utf-8'))['rows']
grid=[['序列','模型','第1次漂移/ATE','第2次漂移/ATE','第3次漂移/ATE']]
for seq in ['00','05','06','07','09','10']:
    for model in ['RAP-SLAM','KISS-SLAM']:
        line=[seq,model]
        for rep in [1,2,3]:
            r=next(x for x in rr if x['sequence']==seq and x['model']==model and x['rep']==rep)
            line.append(f"{r['ter']:.6f} / {r['ate']:.6f}")
        grid.append(line)
table(grid,[.42,1.07,1.76,1.76,1.76],8.7)
para('漂移单位为百分比，ATE单位为米。三次使用独立进程和固定配置，表中保留每次完整成绩。')
heading('论文横向定位',2)
table([['模型与指标','00','05','06','均值'],['CT-ICP 漂移[%]','0.49','0.25','0.27','0.337'],['MULLS-SLAM 漂移[%]','0.54','0.29','0.29','0.373'],['SuMa++ 漂移[%]','0.64','0.40','0.46','0.500'],['PIN-SLAM ATE[m]','0.8','0.3','0.4','0.50']],[2.77,1,1,1,1],9.8)
para('论文表沿用各自预处理与实验设置。KISS-SLAM是本项目的同数据完整系统实测对照，GeoTransformer是既有在线候选受控替换对照。',size=10.3)

page()
heading('配套图像')
p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
p.add_run().add_picture(str(ROOT/'docs/meeting_20261011/benchmark/attempt03/r01-00-RAP-SLAM/trajectory_plot.png'),width=Inches(3.22))
p.add_run(' ')
p.add_run().add_picture(str(ROOT/'docs/meeting_20261011/benchmark/attempt03/r01-05-RAP-SLAM/trajectory_plot.png'),width=Inches(3.22))
caption('图1  00与05的已有完整系统轨迹  对应PPT第2页')
p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
p.add_run().add_picture(str(BASE/'slide_render/slide-09.png'),width=Inches(6.72))
caption('图2  RegX已知视图变换与逆变换的构造示意  对应PPT第9页')

page()
heading('结果证据入口')
para('以下链接用于查阅各项结果。优先阅读报告，再按需要查看结果和验证文件。')
evidence=[]
for key,rel in D['sources'].items():
    name={'benchmark':'完整系统报告','benchmark_data':'完整系统36次结果','e0':'前端开发比较','heldout':'后续系统序列比较','native':'原生小任务适配','noise':'16次新噪声','rigid':'刚体条件对照','dtc':'双精度末端导数','step':'有限步下降','active':'激活分支导数','sampler':'五步采样绑定','fit':'40次更新与留出阶段状态','context':'冻结上下文接口','head':'位姿头局部导数','joint':'非局部多视图比较','identity':'权重身份','reply':'公开模型说明','reference':'RegX方向契约','contract':'RegX全点数值报告','adoption':'独立接口接入约定','review':'项目全局复核','strategy':'工程开发策略','mechanism':'近期机制评估'}[key]
    sub=rel.split('/')
    date=next((p for p in sub if p.startswith('2026-')), '2026-10-11')
    evidence.append((name,date+'  '+sub[-2],(ROOT/rel).as_uri()))
et=table([['结果','可打开的报告']]+[[n,label] for n,label,url in evidence],[2.0,4.77],9.0)
for r,(name,label,url) in zip(et.rows[1:],evidence):
    p=r.cells[1].paragraphs[0]
    for child in list(p._p):
        if child.tag!=qn('w:pPr'):p._p.remove(child)
    link(label,url,p,9.0)

upd=doc.settings.element.find(qn('w:updateFields'))
if upd is None:upd=OxmlElement('w:updateFields');doc.settings.element.append(upd)
upd.set(qn('w:val'),'true')
out=BASE.parent/'output/RAP_SLAM_组会讲解与问答_20261018.docx'
out.parent.mkdir(exist_ok=True)
doc.save(out)

editable={'word/document.xml','word/_rels/document.xml.rels','word/settings.xml','docProps/core.xml','docProps/app.xml'}
with zipfile.ZipFile(SOURCE) as a,zipfile.ZipFile(out) as b:
    preserve=[p for p in a.namelist() if p not in editable and not p.startswith('word/media/') and p!='[Content_Types].xml']
    checks=[{'part':p,'byte_identical':a.read(p)==b.read(p)} for p in preserve]
    assert all(c['byte_identical'] for c in checks),[c for c in checks if not c['byte_identical']]
audit={'reference_unchanged':hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED,'preserve_parts':checks,'output':str(out),'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'page_geometry_matches':all(getattr(x,k)==getattr(y,k) for x,y in zip(doc.sections,Document(SOURCE).sections) for k in ['page_width','page_height','top_margin','bottom_margin','left_margin','right_margin'])}
(BASE/'word_package_check.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in audit.items() if k!='preserve_parts'},ensure_ascii=False))
