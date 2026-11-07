import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { Presentation, PresentationFile } from 'file:///C:/Users/AAA/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
process.on('uncaughtException',e=>{console.error(e.message);process.exit(1);});
process.on('unhandledRejection',e=>{console.error(e?.message??e);process.exit(1);});
process.env.RUNTIME_NODE_MODULES='C:/Users/AAA/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';

const BASE=path.dirname(fileURLToPath(import.meta.url));
const ROOT=path.resolve(BASE,'../../..');
const WORK=path.dirname(BASE);
const SKILL='C:/Users/AAA/.codex/plugins/cache/openai-primary-runtime/presentations/26.1015.12040/skills/presentations';
const PY='C:/Users/AAA/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe';
const D=JSON.parse(await fs.readFile(path.join(BASE,'meeting_content.json'),'utf8'));
const {finalizePresentation,applyPresentationChartFont}=await import(pathToFileURL(path.join(SKILL,'container_tools/artifact_tool_utils.mjs')).href);
await fs.mkdir(path.join(BASE,'slide_render'),{recursive:true});
await fs.mkdir(path.join(WORK,'output'),{recursive:true});
const pres=Presentation.create({slideSize:{width:1600,height:900}});
const BLUE='#244F87',BLACK='#000000',GRAY='#626262',PALE='#D7D7D7';
function mixed(text,size=29,color=BLACK,bold=false){
 return [{runs:String(text).split(/([\x20-\x7E]+)/).filter(Boolean).map(run=>({run,style:{typeface:/^[\x20-\x7E]+$/.test(run)?'Times New Roman':'SimSun',fontSize:`${size}px`,color,bold}}))}];
}
function txt(slide,text,x,y,w,h,size=29,color=BLACK,align='left',bold=false){
 const s=slide.shapes.add({geometry:'textbox',name:text.slice(0,40),position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 s.text=mixed(text,size,color,bold);s.text.style={fontSize:size,typeface:'SimSun',alignment:align,verticalAlignment:'middle',insets:0,wrap:'square',autoFit:'none',color};
 return s;
}
function title(s,t){txt(s,t,58,27,1484,78,45.3);}
function takeaway(s,t,y=777){txt(s,t,58,y,1484,64,30.5,BLUE);}
function foot(s,t,n){if(t)txt(s,t,58,849,1440,27,19,GRAY);txt(s,`${n}`,1515,851,34,24,19,GRAY,'right');}
function table(s,values,x,y,w,h,widths,size=28,aligns=[]){
 const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,columnWidths:widths,values});
 t.styleOptions={headerRow:false,bandedRows:false};
 t.borders.assign({style:'solid',fill:'#FFFFFF',width:0});
 const rh=h/values.length;
 for(let r=0;r<values.length;r++){
  t.rows[r].height=rh;
  for(let c=0;c<values[0].length;c++){
   const cell=t.getCell(r,c);cell.fill='#FFFFFF';cell.text.set(mixed(values[r][c],size,BLACK,false));
   cell.text.style={fontSize:size,typeface:'SimSun',color:BLACK,alignment:aligns[c]??(c===0?'left':'center'),verticalAlignment:'middle',insets:{left:10,right:10,top:7,bottom:7},wrap:'square',autoFit:'none'};
  }
 }
 return t;
}
async function addImg(s,rel,x,y,w,h,alt){const b=await fs.readFile(path.join(ROOT,rel));s.images.add({blob:b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),contentType:'image/png',position:{left:x,top:y,width:w,height:h},fit:'contain',alt});}
function chart(s,categories,series,x,y,w,h,opts={}){
 const ch=s.charts.add('bar',{
 position:{left:x,top:y,width:w,height:h},categories,series,
 hasLegend:true,legend:{position:'bottom',overlay:false,textStyle:{fontSize:23,fill:BLACK}},
 barOptions:{direction:'column',grouping:'clustered',gapWidth:90},
 chartFill:'#FFFFFF',plotAreaFill:'#FFFFFF',chartLine:{fill:'none',width:0},plotAreaLine:{fill:'none',width:0},
 xAxis:{textStyle:{fontSize:24,fill:BLACK},line:{fill:PALE,width:1}},
 yAxis:{min:0,textStyle:{fontSize:21,fill:BLACK},numberFormatCode:'0.0',majorGridlines:{fill:'#E8E8E8',width:1},line:{fill:'none',width:0}},
 dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.00',textStyle:{fontSize:22,fill:BLACK}},
 ...opts});
 applyPresentationChartFont(ch,{fontFamily:'SimSun'});return ch;
}

for(let i=0;i<D.slides.length;i++){
 const dat=D.slides[i],s=pres.slides.add();s.background.fill='#FFFFFF';title(s,dat.title);
 switch(dat.kind){
 case 'system':
  txt(s,dat.lead,58,127,1484,48,28.5);
  txt(s,'单元格：平移漂移 [%] / 对齐轨迹误差 [m]，越低越好',58,192,1484,42,28);
  table(s,D.system_table,58,252,1484,430,[148,440,400,496],29);
  takeaway(s,'00/05/06 平移漂移均值 0.3887% 对 0.4727%，RAP-SLAM 低 17.8%',716);
  txt(s,'07/09/10 对齐轨迹误差均值 0.7215 m 对 0.7641 m，低 5.6%',58,790,1484,44,29);
  foot(s,dat.note,i+1);break;
 case 'trajectories':
  txt(s,'已有完整系统输出，固定校正前端与同一套回环配置',58,124,1484,42,28);
  await addImg(s,'docs/meeting_20261011/benchmark/attempt03/r01-00-RAP-SLAM/trajectory_plot.png',65,180,712,507,'KITTI00 existing RAP-SLAM full trajectory');
  await addImg(s,'docs/meeting_20261011/benchmark/attempt03/r01-05-RAP-SLAM/trajectory_plot.png',822,180,712,507,'KITTI05 existing RAP-SLAM full trajectory');
  txt(s,'00：ATE 3.741 m 降至 2.754 m',63,704,710,47,29,BLUE,'center');
  txt(s,'05：ATE 1.653 m 降至 1.295 m',824,704,710,47,29,BLUE,'center');
  takeaway(s,dat.takeaway,778);foot(s,'图中为首帧坐标轨迹，ATE 沿用统一整体刚体对齐的结果。图与指标来自既有系统运行。',i+1);break;
 case 'noise':
  txt(s,'既有结果：443904 参数、每任务 400 次更新，采用原始五步采样',58,124,1484,44,28);
  table(s,[['训练噪声下','原始平移 / 旋转','适配后平移 / 旋转'],['合成部分 1','3.03 cm / 0.095°','3.59 cm / 0.065°'],['合成部分 2','12.16 cm / 0.163°','4.57 cm / 0.105°'],['真实部分 1','16.35 cm / 0.291°','7.39 cm / 0.095°'],['真实部分 2','21.73 cm / 0.256°','2.57 cm / 0.113°']],58,181,1484,241,[430,527,527],26.5);
  txt(s,'16 次新噪声的平均平移误差 [cm]',58,432,1484,39,26);
  chart(s,['合成 1','合成 2','真实 1','真实 2'],[{name:'原始',values:[15.739,15.119,8.112,28.300],fill:'#B9B9B9'},{name:'适配',values:[14.206,12.432,7.589,24.944],fill:BLUE}],64,480,1472,252,{dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.00',textStyle:{fontSize:20,fill:BLACK}}});
  takeaway(s,dat.takeaway,766);foot(s,dat.note,i+1);break;
 case 'derivatives':
  txt(s,'10 月 12–13 日推进：固定前十层特征，双精度计算末两层与输出头',58,124,1484,45,28);
  table(s,[['验证环节','完成内容','结果'],['方向导数','速度与位姿目标，原始初始化','12 / 12 通过'],['低秩分支激活','A、B 矩阵及末端预测层','18 / 18 通过'],['完整局部导数','独立重建 A / B 矩阵乘积','32 / 32 通过'],['实际有限步长','负梯度下降，正梯度上升','两类目标均可重复'],['五步采样绑定','两路径、两噪声、两次重复','8 条完整数组一致']],58,198,1484,431,[345,714,425],28);
  txt(s,'位姿目标单步对照：198.330 降至 198.132；重复探针逐数组一致',58,666,1484,48,29);
  txt(s,'既有刚体对照：条件数 205.07 降至 1.002，迭代数由 12 降至 4',58,722,1484,36,25);
  takeaway(s,dat.takeaway,770);foot(s,'双精度末端为独立数值对照实现。方向导数、函数下降和采样绑定分别检验。',i+1);break;
 case 'fit':
  txt(s,'固定前缀与双精度末端，速度 V 和位姿 P 各完成 20 次保留更新',58,124,1484,45,28);
  chart(s,['速度目标 V','位姿目标 P'],[{name:'更新前',values:[100,100],fill:'#B9B9B9'},{name:'20 次更新后',values:[100*7.08712625394e-6/7.22996671078e-6,100*194.401887634/198.329989556],fill:BLUE}],74,199,1452,360,{yAxis:{min:0,max:105,majorUnit:20,textStyle:{fontSize:23,fill:BLACK},numberFormatCode:'0',majorGridlines:{fill:'#E8E8E8',width:1}},dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.0',textStyle:{fontSize:23,fill:BLACK}}});
  table(s,[['目标','更新前','更新后'],['速度 V','7.22997 × 10⁻⁶','7.08713 × 10⁻⁶'],['位姿 P','198.330','194.402']],58,588,1484,148,[490,497,497],28);
  takeaway(s,dat.takeaway,776);foot(s,dat.note,i+1);break;
 case 'context':
  txt(s,'冻结特征接口保留原始点行、噪声、尺度与锚帧约定',58,126,1484,44,29);
  table(s,[['接口','信息路径','完成的检查'],['逐点 D','使用点编码','与联合和分离输入逐行绑定'],['分离 I','各扫描独立处理','扰动第三视图，前两视图保持一致'],['联合 J','允许全局跨视图交互','扰动第三视图，联合特征产生响应']],58,215,1484,274,[280,486,718],28);
  txt(s,'轻量位姿头',58,541,1484,45,32);
  txt(s,'6150 个局部输出雅可比列均非零，全部 108 个方向检查通过',58,610,1484,57,31,BLUE);
  txt(s,'零初始化头精确保持基准位姿，冻结信息与物理单位位姿输出直接相连',58,691,1484,53,28);
  takeaway(s,dat.takeaway,781);foot(s,'已知合成输入上的接口与局部导数检查。实际位姿收益采用同输入几何与直接预测对照评价。',i+1);break;
 case 'joint':
  txt(s,'四个分组：00 / 05 / 07 / 09，共 29 视图、32 测量',58,124,1484,45,29);
  txt(s,'各组平均平移误差 [m]',58,184,1484,40,28);
  chart(s,['00（9 视图）','05（3 视图）','07（10 视图）','09（7 视图）'],[{name:'联合 RAP',values:[.783035,.076709,.155169,3.917151],fill:BLUE},{name:'独立 RAP',values:[.798717,.083672,.122062,3.910271],fill:'#949494'},{name:'实用同步几何',values:[.817210,.029842,.124498,3.900829],fill:'#739795'}],65,242,1470,350,{yAxis:{min:0,max:4.5,majorUnit:1,textStyle:{fontSize:22,fill:BLACK},numberFormatCode:'0.0',majorGridlines:{fill:'#E8E8E8',width:1}},dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.000',textStyle:{fontSize:20,fill:BLACK}}});
  txt(s,'全体均值：联合 1.483 m，独立 1.473 m，实用同步几何 1.472 m',58,624,1484,51,29);
  txt(s,'00 联合误差略低；其余分组差异指向稳定性与实际恢复能力',58,699,1484,51,29,BLUE);
  takeaway(s,dat.takeaway,781);foot(s,dat.note,i+1);break;
 case 'provenance':
  txt(s,'10 月 15–17 日完成模型身份与输入约定检查',58,124,1484,44,29);
  table(s,[['对象','本周完成内容','后续用途'],['3 份本地权重','匹配作者链接的托管文件身份','固定模型起点'],['十二层模型','本地配置与公开说明层数一致','聚焦输入和实际功能'],['RegX 固定包','2 条 Paris_02 记录、3 份点云','明确的多视图输入'],['变换方向','Xᵢ = Tᵢ Wᵢ，Qᵢ = Tᵢ⁻¹','独立构造与坐标恢复'],['读取与参考','公开输入与参考分别保存','同输入模型和几何比较']],58,208,1484,431,[332,688,464],28);
  txt(s,'默认演示路径与新契约分开，适配器直接读取已构造的视图点',58,684,1484,57,29);
  takeaway(s,dat.takeaway,775);foot(s,'采用已验证的自定义输入契约。源包的两条记录共享一个场景，数据角色按记录明确。',i+1);break;
 case 'regx':{
  txt(s,'输入 Xᵢ',58,126,704,48,31,BLACK,'center');txt(s,'已知逆变换 Qᵢ Xᵢ',828,126,704,48,31,BLACK,'center');
  const colors=[BLUE,'#D07338','#6D9C7C'];
  for(let side=0;side<2;side++){
   const key=side?'world':'input';
   const vals=D.clouds.flatMap(c=>c[key]);const minX=Math.floor(Math.min(...vals.map(v=>v[0]))/10)*10;const maxX=Math.ceil(Math.max(...vals.map(v=>v[0]))/10)*10;const minZ=Math.floor(Math.min(...vals.map(v=>v[1]))/5)*5;const maxZ=Math.ceil(Math.max(...vals.map(v=>v[1]))/5)*5;
   const ch=s.charts.add('scatter',{position:{left:side?832:62,top:197,width:702,height:486},series:D.clouds.map((c,j)=>({name:`视图 ${j+1}`,xValues:c[key].map(p=>p[0]),values:c[key].map(p=>p[1]),marker:{symbol:'circle',size:2,fill:colors[j]},line:{fill:'none',width:0}})),scatterOptions:{style:'marker'},hasLegend:true,legend:{position:'bottom',overlay:false,textStyle:{fontSize:23,fill:BLACK}},xAxis:{title:'X [m]',min:minX,max:maxX,crossesAt:minX,tickLabelPosition:'low',position:'bottom',textStyle:{fontSize:20,fill:BLACK},numberFormatCode:'0',majorGridlines:{fill:'#EFEFEF',width:1}},yAxis:{title:'Z [m]',min:minZ,max:maxZ,crossesAt:minZ,tickLabelPosition:'low',position:'left',textStyle:{fontSize:20,fill:BLACK},numberFormatCode:'0',majorGridlines:{fill:'#EFEFEF',width:1}},chartFill:'#FFFFFF',plotAreaFill:'#FFFFFF',chartLine:{fill:'none',width:0},dataLabels:{showValue:false}});
   applyPresentationChartFont(ch,{fontFamily:'SimSun'});
  }
  txt(s,'展示输入构造与坐标还原，配准预测器只读取左侧视图点',58,710,1484,47,29);
  takeaway(s,dat.takeaway,785);foot(s,dat.note+' 该图展示数据构造。',i+1);break;}
 case 'validation':
  txt(s,'Paris_02 全部两条记录进入构造、读取与独立数值检查',58,125,1484,45,29);
  table(s,[['检查项目','范围或结果','完成状态'],['源数据与视图','3 源点云，5 次视图出现','全部保留'],['点出现次数','56557','全部进入核验'],['正向坐标比较','169671 次','全部通过'],['逆向坐标比较','169671 次','全部通过'],['最大误差预算使用率','正向 0.66%，逆向 0.38%','低于预定上限'],['执行阶段','合成、构造、读取、独立验证','4 / 4 通过']],58,201,1484,453,[462,635,387],29);
  txt(s,'8 个输入文件在读取前完成固定，参考由构造与评价端单独持有',58,693,1484,47,29);
  takeaway(s,dat.takeaway,783);foot(s,'误差预算衡量坐标表示与逆变换算术。模型配准精度通过下一项明确的预测比较评价。',i+1);break;
 case 'plan':
  txt(s,'拟开展的工程与研究安排',58,124,1484,45,29);
  table(s,[['优先事项','具体工作','预期交付'],['完整轨迹目标','以 00/05 全局精度为开发重点','ATE、漂移、旋转和开销并报'],['成熟测量后端','评估直接点云因子接口与资源','固定 E0 前端的比较方案'],['RAP 的实际增量','共同观测下比较几何、独立与联合','正确对齐与恢复能力'],['小任务适配','复用已验证的导数和采样接口','有限预算的真实采样位姿比较']],58,211,1484,366,[322,647,515],28);
  txt(s,'工程方法可直接服务系统目标，方法贡献由增量对照支持',58,620,1484,51,31,BLUE);
  txt(s,'开发方案确定后冻结实现和数据角色，再检查六条完整序列',58,699,1484,48,29);
  takeaway(s,dat.takeaway,784);foot(s,'以上为下一阶段计划。GLIM 官方文档提供纯 LiDAR 与直接多扫描测量因子的具体实现参考。',i+1);break;
 case 'literature':
  table(s,[['论文模型','00 / 05 / 06','均值','技术启发'],['CT-ICP','0.49 / 0.25 / 0.27','0.337','连续时间运动模型'],['MULLS-SLAM','0.54 / 0.29 / 0.29','0.373','多几何误差与分层地图'],['SuMa++','0.64 / 0.40 / 0.46','0.500','动态表面与语义一致性'],['PIN-SLAM','0.8 / 0.3 / 0.4','0.50','全局一致的神经地图']],58,139,1484,273,[300,450,230,504],26.5);
  txt(s,'前三行为漂移 [%]，PIN-SLAM 为 ATE [m]。论文沿用各自设置，KISS-SLAM 为同数据实测',58,432,1484,43,24);
  const lit=[['RAP','生成配准点与原生五步采样','https://arxiv.org/abs/2512.01850'],['LoRA','有限参数更新与低秩适配','https://arxiv.org/abs/2106.09685'],['BALM','共享表面与紧凑地图优化','https://arxiv.org/abs/2209.08854'],['KISS-SLAM','完整系统与局部地图参照','https://arxiv.org/abs/2503.12660'],['GLIM','直接多扫描测量因子与纯 LiDAR 配置','https://koide3.github.io/glim/parameters.html']];
  lit.forEach((v,j)=>{txt(s,`${v[0]}：${v[1]}`,58,499+j*49,1260,44,28);const link=txt(s,'论文 / 文档',1350,499+j*49,190,44,25,'#4D8394','right');link.text.get('论文 / 文档').link={uri:v[2],isExternal:true};});
  takeaway(s,dat.takeaway,790);foot(s,'汇报日期 2026 年 10 月 18 日。新增实验与接口工作截至 10 月 17 日。',i+1);break;
 }
 const src=dat.sources.map(k=>path.join(ROOT,D.sources[k]));
 if(dat.kind==='plan'||dat.kind==='literature')src.push('https://koide3.github.io/glim/','https://koide3.github.io/glim/parameters.html');
 s.speakerNotes.text=dat.talk.join('\n\n')+'\n\n来源\n'+src.join('\n');
 const png=await pres.export({slide:s,format:'png',scale:1});
 await fs.writeFile(path.join(BASE,'slide_render',`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));
 console.log(`rendered ${i+1}`);
}
const candidate=path.join(BASE,'candidate.pptx');
await(await PresentationFile.exportPptx(pres)).save(candidate);
const finalName=process.env.MEETING_FINAL_NAME||'RAP_SLAM_组会汇报_20261018.pptx';
const final=path.join(WORK,'output',finalName);
const tableOwners=[1,3,4,5,6,8,10,11,12];
const result=await finalizePresentation({workspaceDir:WORK,candidatePath:candidate,finalPath:final,pythonExecutable:PY,integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','15240000,8572500','--validate-bullet-geometry','--validate-heading-fit',...tableOwners.flatMap(n=>['--require-native-table-slide',String(n)])],explicitTotalSlideCount:12,requiredNativeTableOwnerSlides:tableOwners,requiredNativeChartOwnerSlides:[3,5,7,9],materializeLiteralChartWorkbooks:true,nativeChartTargetApplication:'powerpoint',fontPolicy:{basis:'design',families:['SimSun','Times New Roman']},verifyArtifactToolImport:true,receiptPath:path.join(BASE,'presentation_validation_final.json')});
console.log(JSON.stringify(result));
