'use strict';
// ── content module: builds the `sections` array ──────────────────────────────
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
  PageNumber, PageBreak, LevelFormat, TableOfContents
} = require('docx');
const fs   = require('fs');
const path = require('path');
const base = require('./gen_manual_v2');
const { archSvg, startupSvg, pipelineSvg, cardStateSvg, exportFlowSvg, templateStructSvg, imapSvg, pngBufs, sharp } = base;

// re-import all helpers (they live in gen_manual_v2.js as module-level fns)
// Since they're not exported, we redefine the minimal set needed here:
const { ImageRun } = require('docx');
const SHOTS = 'C:/Users/wangj.KEVIN/.gemini/antigravity/brain/2f8c1a6b-19c1-4ea8-8077-e359bc030c4a';
const OUT   = 'C:/Users/wangj.KEVIN/projects/ocr-new/WANGJ_OCR_V1.2_操作手册_详版.docx';

function img(file, w, h) {
  const fp = path.join(SHOTS, file);
  if (!fs.existsSync(fp)) return null;
  return new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 80, after: 80 },
    children: [new ImageRun({ type: 'png', data: fs.readFileSync(fp), transformation: { width: w, height: h }, altText: { title: file, description: file, name: file } })]
  });
}
function svgP(key, w, h) {
  return new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 80, after: 80 },
    children: [new ImageRun({ type: 'png', data: pngBufs[key], transformation: { width: w, height: h }, altText: { title: key, description: key, name: key } })]
  });
}
function h1(t) { return new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] }); }
function h2(t) { return new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] }); }
function h3(t) { return new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(t)] }); }
function p(text, opts) { return new Paragraph({ spacing: { before: 60, after: 60 }, children: [new TextRun({ text, ...opts })] }); }
function bp(text) { return p(text, { bold: true }); }
function sp() { return new Paragraph({ children: [] }); }
function pb() { return new Paragraph({ children: [new PageBreak()] }); }
function caption(text) { return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 40, after: 200 }, children: [new TextRun({ text, italics: true, color: '666666', size: 18 })] }); }
function note(text) { return new Paragraph({ shading: { fill: 'FFF9C4', type: ShadingType.CLEAR }, border: { left: { style: BorderStyle.SINGLE, size: 4, color: 'F9A825', space: 8 } }, spacing: { before: 100, after: 100 }, indent: { left: 360 }, children: [new TextRun({ text: '注意：' + text, size: 20, color: '5D4037' })] }); }
function tip(text) { return new Paragraph({ shading: { fill: 'E8F5E9', type: ShadingType.CLEAR }, border: { left: { style: BorderStyle.SINGLE, size: 4, color: '2E7D32', space: 8 } }, spacing: { before: 100, after: 100 }, indent: { left: 360 }, children: [new TextRun({ text: '提示：' + text, size: 20, color: '1B5E20' })] }); }
function code(text, color) { return new Paragraph({ shading: { fill: 'F5F5F5', type: ShadingType.CLEAR }, border: { left: { style: BorderStyle.SINGLE, size: 4, color: color || '1565C0', space: 8 } }, spacing: { before: 80, after: 80 }, indent: { left: 360 }, children: [new TextRun({ text, font: 'Courier New', size: 18, color: '1A237E' })] }); }
function bullet(text, opts) { return new Paragraph({ numbering: { reference: 'bullets', level: 0 }, spacing: { before: 40, after: 40 }, children: [new TextRun({ text, ...opts })] }); }
function numbered(text) { return new Paragraph({ numbering: { reference: 'numbers', level: 0 }, spacing: { before: 60, after: 60 }, children: [new TextRun(text)] }); }
function sub(text) { return new Paragraph({ numbering: { reference: 'subbullets', level: 0 }, spacing: { before: 30, after: 30 }, children: [new TextRun({ text, size: 20 })] }); }

const tblW = 9026;
const CB   = { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' };
const BORD = { top: CB, bottom: CB, left: CB, right: CB };
const HBORD = { top: { style: BorderStyle.SINGLE, size: 1, color: '4472C4' }, bottom: { style: BorderStyle.SINGLE, size: 2, color: '4472C4' }, left: CB, right: CB };

function tc(text, { bg, b, w, align, sz } = {}) {
  return new TableCell({ borders: BORD, width: w ? { size: w, type: WidthType.DXA } : undefined, shading: bg ? { fill: bg, type: ShadingType.CLEAR } : undefined, margins: { top: 80, bottom: 80, left: 120, right: 120 }, verticalAlign: 'center', children: [new Paragraph({ alignment: align || AlignmentType.LEFT, spacing: { before: 20, after: 20 }, children: [new TextRun({ text, bold: !!b, size: sz || 20 })] })] });
}
function hc(text, w) {
  return new TableCell({ borders: HBORD, width: { size: w, type: WidthType.DXA }, shading: { fill: '4472C4', type: ShadingType.CLEAR }, margins: { top: 80, bottom: 80, left: 120, right: 120 }, verticalAlign: 'center', children: [new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 20, after: 20 }, children: [new TextRun({ text, bold: true, color: 'FFFFFF', size: 20 })] })] });
}
function mkTable(cols, hdrs, rows) {
  return new Table({ width: { size: tblW, type: WidthType.DXA }, columnWidths: cols, rows: [
    new TableRow({ children: hdrs.map((l, i) => hc(l, cols[i])) }),
    ...rows.map((row, ri) => new TableRow({ children: row.map((txt, ci) => tc(txt, { w: cols[ci], bg: ri % 2 === 0 ? 'F5F5F5' : 'FFFFFF' })) }))
  ]});
}
function coverLine() { return new Paragraph({ border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: '4472C4', space: 1 } }, children: [new TextRun('')] }); }

// ── CONTENT ───────────────────────────────────────────────────────────────────
async function buildSections() {
  // pre-render SVGs
  const svgDefs = { arch: archSvg, startup: startupSvg, pipeline: pipelineSvg, cardState: cardStateSvg, exportFlow: exportFlowSvg, tmplStruct: templateStructSvg, imap: imapSvg };
  for (const [k, v] of Object.entries(svgDefs)) pngBufs[k] = await sharp(Buffer.from(v, 'utf8')).png().toBuffer();

  const S = []; // sections array

  // ── COVER ──────────────────────────────────────────────────────────────────
  S.push(
    new Paragraph({ spacing: { before: 1800 }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: 'WEWODON AI OCR LABORATORY', size: 22, color: '888888', font: 'Arial' })] }),
    new Paragraph({ spacing: { before: 400 }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: '智能实验方舱', size: 72, bold: true, color: '1565C0', font: 'Arial' })] }),
    new Paragraph({ spacing: { before: 200 }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: 'WANGJ-OCR V1.2 系统', size: 40, bold: true, color: '37474F', font: 'Arial' })] }),
    coverLine(),
    new Paragraph({ spacing: { before: 300, after: 120 }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: '技术说明与操作手册（详版）', size: 36, color: '555555', font: 'Arial' })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: 'Technical & Operational Manual — Detailed Edition', size: 24, color: '888888', italics: true, font: 'Arial' })] }),
    coverLine(),
    sp(),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 600 }, children: [new TextRun({ text: '版本：V1.2.0  ·  发布日期：2026年4月27日  ·  机密等级：内部使用', size: 20, color: '666666', font: 'Arial' })] }),
    pb()
  );

  // ── TOC ────────────────────────────────────────────────────────────────────
  S.push(h1('目录'), new TableOfContents('目录', { hyperlink: true, headingStyleRange: '1-3' }), pb());

  // ══════════════════════════════════════════════════════════════════════════
  // Chapter 1 — 系统概述
  // ══════════════════════════════════════════════════════════════════════════
  S.push(h1('第一章  系统概述'));

  S.push(h2('1.1  产品简介'));
  S.push(p('WANGJ-OCR（智能实验方舱）V1.2 是一套专为石油化工实验室设计的工业仪表图像自动识别系统。系统通过多路工业 RTSP 摄像头实时采集各仪表画面，利用自训练 YOLOv8 模型精确定位仪表显示屏区域，经 OpenCV 图像增强与透视校正后，调用基于 InternVL 架构的多模态大语言模型 EXP-OCR 进行语义化读数提取。识别结果以结构化 JSON 写入 SQLite 数据库，供前端实时展示和 Excel 报表导出。'));
  S.push(sp());
  S.push(p('系统覆盖实验室 9 台核心仪器（D0–D8），支持 6 类实验场景，每种场景均对应专用的 Excel 报表模板，满足 SY/T 行业标准检测记录格式要求。'));
  S.push(sp());

  S.push(h2('1.2  核心功能'));
  S.push(mkTable([2200, 6826],
    ['功能模块', '功能描述'],
    [
      ['自动抓拍', '多路工业相机按需触发；支持真实 RTSP 模式与本地 Mock 模拟模式，开发调试无需连接真实摄像头'],
      ['智能识别', 'YOLOv8 目标定位 → OpenCV 图像增强 → EXP-OCR 语义推理，全链路自动化，平均单次识别 5–15 秒'],
      ['实验管理', '支持 6 类实验类型，每次实验可包含多轮"快照集"（Measurement Set），历史记录可查、可删除'],
      ['字段级手动覆盖', '识别结果每个字段可独立开启 Manual Override，手动修改值后系统标注来源为"手动"，OCR 与手动值分别保留'],
      ['图像审计', '每次识别保存原始截图、Neural View（注意力热图）、Context View（全景图），支持可视化核验'],
      ['数据导出', '一键导出符合行业标准格式的 xlsx 报表，按实验类型自动套用模板，包含均值计算和检测人签署栏'],
      ['提示词模板', 'Prompt Template 全部存储于数据库，前端提供图形化编辑器，新增仪表类型无需修改代码'],
      ['模型配置', 'llama-server 参数（Temperature、Max Tokens 等）可在 Settings 面板实时调整并同步配置'],
    ]
  ));
  S.push(sp());

  S.push(h2('1.3  系统架构'));
  S.push(p('系统采用三层 B/S 架构：前端 React/Next.js（端口 3000）、后端 FastAPI（端口 8001）、AI 推理引擎 llama-server（端口 8080）三个独立进程协作，通过 HTTP REST API 和 SSE 事件流通信。'));
  S.push(sp());
  S.push(svgP('arch', 560, 368));
  S.push(caption('图 1-1  WANGJ-OCR V1.2 系统逻辑架构图'));
  S.push(pb());

  // ══════════════════════════════════════════════════════════════════════════
  // Chapter 2 — 技术规格
  // ══════════════════════════════════════════════════════════════════════════
  S.push(h1('第二章  技术规格'));

  S.push(h2('2.1  硬件环境要求'));
  S.push(mkTable([2000, 3500, 3526],
    ['硬件类型', '最低配置', '推荐配置'],
    [
      ['GPU 显卡', 'NVIDIA GTX 1080 Ti（显存 11 GB）', 'NVIDIA RTX 3060 Ti / 4090（显存 8 GB+）'],
      ['CPU', 'Intel Core i5 第10代', 'Intel Core i7-12700 或以上'],
      ['内存', '16 GB RAM', '32 GB RAM'],
      ['操作系统', 'Windows 10 x64', 'Windows 11 Pro x64（本文档环境）'],
      ['工业摄像头', '支持 RTSP 协议的 IP 摄像头', '海康/大华 4MP+ 工业摄像头 × 5 台'],
      ['存储空间', '100 GB 可用空间', '500 GB NVMe SSD'],
      ['网络', '局域网 100 Mbps', '千兆有线，相机与服务器同交换机'],
    ]
  ));
  S.push(sp());

  S.push(h2('2.2  软件依赖'));
  S.push(mkTable([2000, 2400, 4626],
    ['组件', '版本要求', '安装方式 / 备注'],
    [
      ['Python', '3.10 或更高', 'conda create -n ocr python=3.10'],
      ['Node.js', '18.x 或更高', 'npm install（在 frontend/ 目录）'],
      ['CUDA Toolkit', '13.1（与 llama.cpp 编译版本匹配）', '须与 GPU 驱动版本兼容；驱动需 ≥ 520.x'],
      ['llama-server', 'b8937 或更新版本', '需加载 EXP-OCR-V1.2.gguf；建议配合 --mmproj-offload'],
      ['Python 依赖包', '见 requirements.txt', 'pip install -r requirements.txt（含 fastapi、ultralytics、opencv-python、openpyxl 等）'],
    ]
  ));
  S.push(sp());

  S.push(h2('2.3  端口规划'));
  S.push(mkTable([1400, 2200, 5426],
    ['端口', '服务', '说明'],
    [
      ['3000', '前端 React/Next.js', '用户浏览器入口；生产部署可反代至 80/443'],
      ['8001', '后端 FastAPI / Uvicorn', '实验 CRUD、OCR 触发、导出 xlsx、SSE 实时推送'],
      ['8080', 'llama-server（EXP-OCR）', '视觉语言模型推理；--mmproj-offload 将投影层卸载至 GPU 以最大化吞吐'],
    ]
  ));
  S.push(sp());

  S.push(h2('2.4  仪表通道映射（D0–D8）'));
  S.push(p('9 台仪表与 5 路摄像头的映射关系如下。同一摄像头覆盖多台仪表时，YOLOv8 通过 Bounding Box 坐标自动区分。'));
  S.push(sp());
  S.push(svgP('imap', 544, 224));
  S.push(caption('图 2-1  D0–D8 仪表与相机通道对应关系'));
  S.push(sp());
  S.push(mkTable([700, 1900, 1700, 4726],
    ['ID', '仪表名称', '目标相机', 'V1.2 关键改进'],
    [
      ['D0', '混调器（Advanced Mixer）', 'F0', '自适应布局检测；高亮按钮状态识别 Auto/Manual 模式'],
      ['D1', '电子天平 1', 'F3', '严格零填充裁切；移除数值占位符 prompt 干扰'],
      ['D2', '电子天平 2', 'F3', '同 D1；YOLO 按坐标自动区分两台天平'],
      ['D3', '台式 pH 计', 'F3', 'pH + 温度 + mV 整合为单次快照；执行标准 SY/T 5107-2016'],
      ['D4', '水质矿化度检测仪', 'F5', 'OpenCV 自动旋转修正；Canny 边缘密度判断屏幕方向；黑屏 null 策略'],
      ['D5', '界面张力仪', 'F5', '自适应 5 行/6 行检测；Excel 支持多水面张力平均导出'],
      ['D6', '扭矩搅拌器', 'F7', '强制左边缘扫描，防止 4 位 RPM 首位窄字"1"被截断'],
      ['D7', '水浴锅', 'F7', 'YOLO 多框压制；强制取最小内屏 BBox，避免外框干扰'],
      ['D8', '旋转粘度计', 'F8', '100 r/min 表观粘度目标绑定；后端自动多次测量均值计算'],
    ]
  ));
  S.push(pb());

  // ══════════════════════════════════════════════════════════════════════════
  // Chapter 3 — 安装与启动
  // ══════════════════════════════════════════════════════════════════════════
  S.push(h1('第三章  安装与启动'));

  S.push(h2('3.1  环境准备'));
  S.push(numbered('安装 Python 3.10+，建议使用 conda 管理虚拟环境：'));
  S.push(code('conda create -n ocr python=3.10 && conda activate ocr'));
  S.push(numbered('在项目根目录安装 Python 依赖：'));
  S.push(code('pip install -r requirements.txt'));
  S.push(numbered('安装 Node.js 18+，进入 frontend/ 目录安装前端依赖：'));
  S.push(code('cd frontend && npm install'));
  S.push(numbered('将 llama-server.exe（b8937，CUDA 13.1 编译版本）放入项目根目录或系统 PATH。'));
  S.push(numbered('将 EXP-OCR-V1.2.gguf 权重文件放入 models/ 目录（或配置文件指定的路径）。'));
  S.push(numbered('在 Settings 面板配置各仪表对应的 RTSP 流地址（详见第七章）。初次使用可先开启 Mock 模式验证流程。'));
  S.push(sp());
  S.push(note('llama-server 和 GPU 驱动版本必须匹配 CUDA 13.1。版本不匹配会导致推理引擎无法加载模型。'));
  S.push(sp());

  S.push(h2('3.2  服务启动流程'));
  S.push(p('三个服务必须严格按顺序启动。每步等待控制台确认就绪后再执行下一步。'));
  S.push(sp());
  S.push(svgP('startup', 448, 160));
  S.push(caption('图 3-1  服务启动顺序'));
  S.push(sp());

  S.push(h3('Step 1 — 推理引擎（llama-server）'));
  S.push(p('双击运行 start_llama_server.bat，等待控制台出现以下就绪信号：'));
  S.push(code('llama server listening at http://127.0.0.1:8080', '1565C0'));
  S.push(sp());

  S.push(h3('Step 2 — 后端服务（FastAPI）'));
  S.push(p('运行 start_backend.bat，等待出现：'));
  S.push(code('Application startup complete.  Uvicorn running on http://0.0.0.0:8001', '2E7D32'));
  S.push(sp());

  S.push(h3('Step 3 — 前端界面（Next.js）'));
  S.push(p('运行 start_frontend.bat，首次启动需编译约 30 秒，出现以下信号后可访问：'));
  S.push(code('ready - started server on 0.0.0.0:3000  url: http://localhost:3000', 'E65100'));
  S.push(sp());
  S.push(tip('全部就绪后，在浏览器输入 http://localhost:3000 即可访问系统首页。端口冲突时，系统会自动在 llama_error.log 中记录详情。'));
  S.push(pb());

  // ══════════════════════════════════════════════════════════════════════════
  // Chapter 4 — 界面导航指南
  // ══════════════════════════════════════════════════════════════════════════
  S.push(h1('第四章  界面导航指南'));

  S.push(h2('4.1  系统首页'));
  S.push(p('访问 http://localhost:3000 进入系统首页。首页以蓝色渐变卡片展示系统定位，下方列出四大核心功能模块，底部有"为什么选择智能实验方舱"品牌介绍。'));
  const hp = img('step_01_landing_1777225631872.png', 460, 468);
  if (hp) S.push(hp);
  S.push(caption('图 4-1  系统门户首页（智能实验方舱）'));
  S.push(sp());
  S.push(bp('页面关键元素说明：'));
  S.push(bullet('顶部导航栏：首页 | 控制台（进入 Dashboard）'));
  S.push(bullet('"进入控制台"按钮：跳转至实验管理看板的主入口'));
  S.push(bullet('"了解更多"按钮：页面内滚动至功能介绍区域'));
  S.push(bullet('右上角 WEWODON 品牌标识：点击可返回首页'));
  S.push(sp());

  S.push(h2('4.2  实验管理控制台（Dashboard）'));
  S.push(p('控制台是系统的核心工作界面，分为三个区域：'));
  const db = img('step_02_dashboard_1777225652568.png', 460, 468);
  if (db) S.push(db);
  S.push(caption('图 4-2  实验管理控制台全览'));
  S.push(sp());
  S.push(mkTable([2000, 7026],
    ['界面区域', '功能说明'],
    [
      ['左侧实验列表栏（宽约 220px）', '显示所有历史实验，含名称、实验类型彩色标签（如"pH值"、"表观粘度"）和创建日期；点击某条记录即加载右侧工作区'],
      ['顶部标题栏', '显示实验名称和类型；右上角有"导出报表"按钮（详见第六章）'],
      ['右侧仪表工作区', '以 Measurement Set 分组展示仪表卡片网格；每组可独立新增（"NEW SET"按钮）'],
      ['顶栏状态区', '绿色圆点表示后端在线；SETTINGS 按钮打开配置面板；MOCK 标签指示当前是否为模拟模式'],
    ]
  ));
  S.push(sp());

  S.push(h2('4.3  仪表卡片结构'));
  S.push(p('每张仪表卡片代表一台物理仪器在一次识别周期内的完整数据单元，结构如下：'));
  S.push(svgP('cardState', 544, 112));
  S.push(caption('图 4-3  仪表卡片状态转换示意图'));
  S.push(sp());
  S.push(mkTable([2400, 6626],
    ['卡片区域', '说明'],
    [
      ['顶部标签行', '"SENSOR UNIT D*"显示仪表编号；右侧显示 Manual Override 开关'],
      ['右上角操作图标', '⚡ 触发识别 | 瞄准镜图标 查看审计图像 | 眼睛图标 切换显示模式'],
      ['图像区（黑色背景）', '识别前显示相机图标占位符；识别后展示 YOLO 裁切的仪表特写截图'],
      ['数据字段列表', '识别结果按"字段名 : 值"列出，支持逐字段手动编辑（开启 Manual Override 后）'],
      ['底部状态提示', 'OCR 错误时显示红色错误信息（如 "OCR ERRORS: ERRNO 22 INVALID ARG..."）'],
    ]
  ));
  S.push(pb());

  // ══════════════════════════════════════════════════════════════════════════
  // Chapter 5 — 实验操作全流程
  // ══════════════════════════════════════════════════════════════════════════
  S.push(h1('第五章  实验操作全流程'));

  S.push(h2('5.1  新建实验'));
  S.push(h3('Step 1 — 打开新建对话框'));
  S.push(p('点击左侧列表顶部的"＋ 新建"按钮，弹出"新建实验"对话框（两步向导）。'));
  const m1 = img('step_03_modal_open_1777225663470.png', 420, 428);
  if (m1) S.push(m1);
  S.push(caption('图 5-1  新建实验对话框（步骤一）'));
  S.push(sp());

  S.push(h3('Step 2 — 填写实验名称并选择类型'));
  S.push(p('在"实验名称"框输入本次实验标识（建议格式：项目-日期，如 "pH值-20260427"），然后从列表选择实验类型。系统内置 6 种类型：'));
  S.push(mkTable([3000, 6026],
    ['实验类型', '涉及仪表 / 说明'],
    [
      ['表面张力和界面张力测试', 'D0·D1·D2·D3·D4·D5·D6·D7（全场景，最复杂）'],
      ['运动粘度', '手动计时（玻璃毛细管），不调用 OCR，手动录入流经时间'],
      ['表观粘度', 'D8 旋转粘度计；100 r/min 目标转速'],
      ['水质矿化度', 'D4 水质矿化度检测仪'],
      ['pH 值', 'D3 台式 pH 计；执行标准 SY/T 5107-2016'],
      ['全场景仪表测试', 'D0–D8 全部仪表，用于日常调试和功能验证'],
    ]
  ));
  S.push(sp());
  const m2 = img('step_04_modal_typed_1777225674757.png', 420, 428);
  if (m2) S.push(m2);
  S.push(caption('图 5-2  填写实验名称'));
  S.push(sp());
  const m3 = img('step_05_modal_selected_1777225754358.png', 420, 428);
  if (m3) S.push(m3);
  S.push(caption('图 5-3  选择实验类型（全场景仪表测试已选中）'));
  S.push(sp());

  S.push(h3('Step 3 — 仪表字段配置'));
  S.push(p('点击"下一步"进入字段配置页。列出当前实验类型下所有仪表及其识别字段，字段右侧的彩色标签可单独开关，控制本次实验是否识别该字段。默认配置已经过优化，一般无需修改。'));
  const cfgfull = img('new_experiment_step3_full_list_1777222201236.png', 420, 428);
  if (cfgfull) S.push(cfgfull);
  S.push(caption('图 5-4  仪表字段配置页（D0–D8 全字段列表）'));
  S.push(sp());
  S.push(p('确认配置后点击"创建实验"按钮完成创建。实验会立即出现在左侧列表，右侧展示对应的仪表卡片网格。'));
  S.push(pb());

  S.push(h2('5.2  触发仪表识别'));
  const grid = img('step_06_experiment_created_v2_1777225795694.png', 460, 468);
  if (grid) S.push(grid);
  S.push(caption('图 5-5  实验创建后的仪表卡片（全场景测试，D0–D8 共 9 张，均处于空白等待状态）'));
  S.push(sp());
  S.push(h3('单卡触发'));
  S.push(p('点击任意仪表卡片右上角的 ⚡ 闪电图标，仅触发该单张卡片的识别流程。适合需要单独重测某台仪表的场景。'));
  S.push(sp());
  S.push(h3('批量触发（推荐）'));
  S.push(p('点击 Measurement Set 标题行右侧的整体触发按钮，对该组所有卡片同时发起识别请求。后端会为每张卡片创建独立异步任务，并行执行（受 GPU 显存限制，实际为排队推理）。'));
  S.push(sp());
  S.push(p('触发后卡片进入"抓拍中 → 推理中"状态，图像区显示动态进度动画：'));
  const run = img('step_07_running_actual_1777226074045.png', 460, 468);
  if (run) S.push(run);
  S.push(caption('图 5-6  识别进行中（部分卡片已完成抓拍，显示仪表截图；其余卡片排队推理）'));
  S.push(sp());
  S.push(p('识别全流程耗时参考（单卡，RTX 3060 Ti）：'));
  S.push(mkTable([2400, 3000, 3626],
    ['阶段', '耗时估算', '影响因素'],
    [
      ['RTSP 抓拍', '< 1 秒', '网络带宽，摄像头响应速度'],
      ['YOLOv8 目标检测', '0.5–1 秒', 'GPU 算力，图像分辨率'],
      ['OpenCV 图像处理', '< 0.5 秒', 'CPU 性能'],
      ['EXP-OCR 推理', '4–12 秒', 'GPU 显存，模型量化级别，Prompt 长度'],
      ['数据库写入 + 前端推送', '< 0.5 秒', '磁盘 I/O，SSE 连接状态'],
    ]
  ));
  S.push(pb());

  S.push(h2('5.3  查看识别结果'));
  S.push(p('识别完成后，卡片数据字段区自动填充读数，图像区展示 YOLO 裁切后的仪表特写。'));
  const res = img('step_08_result_final_v10_1777226522365.png', 460, 468);
  if (res) S.push(res);
  S.push(caption('图 5-7  识别结果展示（D6 扭矩搅拌器及 D7、D8 数据已填充，D3–D5 显示实时截图）'));
  S.push(sp());
  S.push(p('结果视图更多截图（D0 混调器 + D1/D2 天平详情）：'));
  const top = img('experiment_detail_top_cards_1777221435048.png', 460, 468);
  if (top) S.push(top);
  S.push(caption('图 5-8  D0 混调器（已识别转速、模式等参数）与 D1/D2 电子天平（已识别重量）'));
  S.push(sp());

  S.push(h2('5.4  Manual Override — 手动覆盖'));
  S.push(p('当 OCR 识别结果与真实读数存在偏差时，可启用手动覆盖功能：'));
  S.push(numbered('点击仪表卡片右上角的"Manual Override"开关，将其打开（变为橙色/黄色状态）。'));
  S.push(numbered('卡片数据字段变为可编辑文本框，直接输入正确数值后按 Enter 确认。'));
  S.push(numbered('手动录入的值会标注"Manual"来源，与 OCR 识别值在数据库中分开存储，不影响历史审计。'));
  S.push(numbered('若需恢复 OCR 值，关闭 Manual Override 开关后重新触发识别即可覆盖。'));
  S.push(sp());
  S.push(note('手动覆盖仅修改数据库中的 value 字段，原始截图和 Neural View 图像不受影响，审计记录始终保留。'));
  S.push(sp());

  S.push(h2('5.5  图像审计与数据核验'));
  S.push(p('点击仪表卡片右上角的"瞄准镜"图标（或点击截图区域），打开图像查看器。查看器提供三种视图切换：'));
  S.push(sp());
  const auditOpen = img('step_09_audit_open_actual_1777226539530.png', 460, 468);
  if (auditOpen) S.push(auditOpen);
  S.push(caption('图 5-9  点击卡片截图区域打开图像审计查看器（D4 水质仪）'));
  S.push(sp());
  S.push(mkTable([2200, 6826],
    ['查看模式', '用途说明'],
    [
      ['Neural View（神经注意力图）', '可视化 EXP-OCR 的注意力权重热图，高亮区域为模型重点关注的像素；用于判断模型是否聚焦于正确的数值区域'],
      ['Context View（上下文全景图）', '展示 YOLO 裁切前的相机全景原图，可确认 BBox 定位是否准确、相机角度是否合适'],
      ['原始截图', 'YOLO 裁切并经 OpenCV 处理后发送给 EXP-OCR 的实际输入图像'],
    ]
  ));
  S.push(sp());
  const nv = img('image_viewer_neural_view_d3_1777222420944.png', 460, 468);
  if (nv) S.push(nv);
  S.push(caption('图 5-10  Neural View 模式（D3–D8 全部仪表识别后，切换到 Neural View 查看注意力图）'));
  S.push(sp());
  const cv = img('image_viewer_context_view_d3_1777222452835.png', 460, 468);
  if (cv) S.push(cv);
  S.push(caption('图 5-11  Context View 模式（同一页面切换为全景上下文视图）'));
  S.push(sp());
  S.push(tip('当识别结果数值明显偏差时，首先查看 Neural View 确认注意力区域是否聚焦在屏幕数字上；若注意力散布于屏幕外，通常意味着 YOLO 裁切范围不准确，需检查相机对焦和摆放角度。'));
  S.push(pb());

  // ══════════════════════════════════════════════════════════════════════════
  // Chapter 6 — 实验数据导出
  // ══════════════════════════════════════════════════════════════════════════
  S.push(h1('第六章  实验数据导出'));

  S.push(h2('6.1  导出操作步骤'));
  S.push(p('实验完成（至少有一组识别结果）后，按以下步骤导出 Excel 报表：'));
  S.push(sp());
  S.push(svgP('exportFlow', 544, 112));
  S.push(caption('图 6-1  数据导出操作流程'));
  S.push(sp());
  S.push(numbered('在左侧实验列表中点击选中目标实验，确认右侧工作区已显示仪表卡片和识别数据。'));
  S.push(numbered('查看实验页面右上角是否出现"↑ 导出报表"按钮（仅在识别数据存在时出现）。'));
  const exportView = img('experiment_detail_top_cards_1777221435048.png', 460, 468);
  if (exportView) S.push(exportView);
  S.push(caption('图 6-2  导出按钮位置（页面右上角"↑ 导出报表"）'));
  S.push(sp());
  S.push(numbered('点击"↑ 导出报表"按钮，浏览器将自动开始下载 Excel 文件，文件名格式为：'));
  S.push(code('experiment_{实验ID}.xlsx   （示例：experiment_12.xlsx）'));
  S.push(numbered('下载完成后，用 Microsoft Excel 或 WPS 打开文件，核验数据格式是否符合要求。'));
  S.push(sp());
  S.push(note('导出按钮调用后端 GET /experiments/{id}/export 接口，后端动态生成 xlsx 并以流式响应返回。导出过程无需等待，通常 1–2 秒内完成下载。'));
  S.push(sp());

  S.push(h2('6.2  各实验类型导出格式'));
  S.push(p('系统根据实验类型自动选择不同的 Excel 模板格式，每种格式均符合对应的行业标准：'));
  S.push(mkTable([2600, 2400, 4026],
    ['实验类型', '报表标题', 'Excel 主要内容'],
    [
      ['ph_value', 'pH值检测原始记录', '检测日期/样品信息、各次 pH 读数 + 温度、算术平均值；执行标准 SY/T 5107-2016'],
      ['apparent_viscosity', '表观黏度检测原始记录', '3rpm / 6rpm / 100rpm 三组读数、自动计算表观粘度 η = (100rpm × 5.077)/1.704、各次均值；文件编号 WLD/CNAS-QP7080004'],
      ['kinematic_viscosity', '运动粘度检验原始记录', '毛细管型号/系数、多次流经时间 t、平均流经时间 t̄、运动粘度 ν = C×t̄；文件编号 WLD-QP5100113-02'],
      ['surface_tension', '表面张力和界面张力检测原始记录', '纯水表面张力验证 + 破胶液表面张力 + 界面张力三段；各段自动计算平均值；含检测人/审核人签署栏；执行标准 SY/T 5370-2018'],
      ['water_mineralization', '水质矿化度检测原始记录', '各次矿化度/电导率/温度读数、均值计算'],
      ['test（全场景测试）', '全相机测试拍照记录', '按相机位（F0–F8）列出所有字段、读数值、时间戳和图片路径'],
    ]
  ));
  S.push(sp());

  S.push(h2('6.3  Excel 报表字段详解'));

  S.push(h3('6.3.1  pH 值报表（ph_value）'));
  S.push(mkTable([2400, 2800, 3826],
    ['Excel 行/列', '字段来源', '说明'],
    [
      ['检测日期', 'manual_params.test_date', '实验手动参数，导出前在实验配置中填写'],
      ['样品编号', 'manual_params.sample_number', '同上'],
      ['被检样品名称', 'manual_params.sample_name', '同上'],
      ['室内温度 / 湿度', 'manual_params.room_temp / room_humidity', '环境参数，手动填写'],
      ['pH 值（每次）', 'ocr_data.ph_value（来自 D3 识别）', 'EXP-OCR 从 pH 计屏幕提取'],
      ['温度（每次）', 'ocr_data.temperature（来自 D3 识别）', 'pH 计温度补偿传感器读数'],
      ['算术平均值', '后端自动计算', '所有有效读数的平均值，自动写入对应单元格'],
      ['图片路径', 'image_path', 'YOLO 裁切图的本地路径，供审计追溯'],
    ]
  ));
  S.push(sp());

  S.push(h3('6.3.2  表观粘度报表（apparent_viscosity）'));
  S.push(mkTable([2400, 2800, 3826],
    ['Excel 列', '字段来源', '说明'],
    [
      ['3 rpm', 'readings[field_key=reading_3rpm]', '旋转粘度计 3 r/min 转速下的读数'],
      ['6 rpm', 'readings[field_key=reading_6rpm]', '旋转粘度计 6 r/min 转速下的读数'],
      ['100 rpm（α）', 'readings[field_key=reading_100rpm]', '100 r/min 目标转速读数，V1.2 重点识别字段'],
      ['表观粘度 η', '后端自动计算：η = (α × 5.077) / 1.704', '换算公式固定；单位 mPa·s'],
      ['平均表观粘度', '所有有效 run 的 η 均值', '多次实验后自动汇总'],
      ['图片路径（100rpm）', 'image_path（100rpm run）', '对应截图本地路径'],
    ]
  ));
  S.push(sp());

  S.push(h3('6.3.3  表面/界面张力报表（surface_tension）'));
  S.push(p('此类报表结构最复杂，分为三段，并包含签署区：'));
  S.push(mkTable([3200, 5826],
    ['报表段落', '说明'],
    [
      ['纯水表面张力验证段', '列出所有 water_surface_tension 字段的读数，并计算算术平均值；用于验证仪器标定精度'],
      ['破胶液表面张力段', '列出所有 fluid_surface_tension 读数及均值；显示样品密度参数'],
      ['破胶液界面张力段', '列出所有 fluid_interface_tension 读数及均值；显示煤油密度参数'],
      ['签署区', '含备注、检测人/检测时间、审核人/审核日期字段，由用户手动填写后存档'],
    ]
  ));
  S.push(sp());

  S.push(h2('6.4  图片路径说明'));
  S.push(p('每条识别记录均包含 image_path 字段，指向本地存储的 YOLO 裁切图文件，路径格式为：'));
  S.push(code('storage/images/exp_{实验ID}/d{仪表编号}_{时间戳}.jpg'));
  S.push(sp());
  S.push(p('Excel 报表中保留图片路径而非嵌入图片，原因是图片文件体积较大（每张约 200–800 KB），导出时保留路径可保持 xlsx 文件小巧。如需在 Excel 中查看图片，可使用 Excel 的 HYPERLINK 函数或 VBA 批量插入。'));
  S.push(sp());
  S.push(tip('建议将整个 storage/images/ 目录与导出的 xlsx 文件放在同一归档文件夹内，以便后续核查时能通过路径快速定位到对应截图。'));
  S.push(pb());

  // ══════════════════════════════════════════════════════════════════════════
  // Chapter 7 — 系统设置与配置
  // ══════════════════════════════════════════════════════════════════════════
  S.push(h1('第七章  系统设置与配置'));

  S.push(h2('7.1  设置面板概览'));
  S.push(p('点击顶栏右侧"SETTINGS"按钮，系统控制中心面板（System Control Center）从页面右侧滑出，覆盖工作区右侧约 320px 宽度。面板分为四个区域，从上到下依次为：'));
  S.push(bullet('Virtual Optics（虚拟光学 / Mock 模式）'));
  S.push(bullet('Storage Matrix（图像存储路径）'));
  S.push(bullet('仪器对照（相机通道映射）'));
  S.push(bullet('Neural Engine（推理引擎状态与参数）'));
  S.push(sp());
  const sett = img('step_10_settings_final_final_1777226395660.png', 440, 448);
  if (sett) S.push(sett);
  S.push(caption('图 7-1  系统控制中心面板（Settings）总览'));
  S.push(sp());

  S.push(h2('7.2  Virtual Optics — Mock 模式开关'));
  S.push(p('面板顶部的"VIRTUAL OPTICS"拨动开关控制摄像头数据来源：'));
  S.push(mkTable([2200, 6826],
    ['状态', '行为说明'],
    [
      ['ON（开启，蓝色）', '使用 Mock Camera 模式，从 storage/images/ 目录读取预先存储的图片文件代替真实抓拍。适合开发调试、演示和功能测试。'],
      ['OFF（关闭）', '使用真实 RTSP 摄像头，调用 CameraClient 通过网络获取实时图像。适用于正式实验采集。'],
    ]
  ));
  S.push(sp());
  S.push(note('初次部署时，建议先开启 Mock 模式，用预存图片完整走通识别流程，确认一切正常后再切换至真实模式。'));
  S.push(sp());

  S.push(h2('7.3  Storage Matrix — 存储路径'));
  S.push(p('配置图像文件的本地存储根目录（默认为项目 storage/ 子目录）。支持绝对路径（如 C:/OCR/storage）。修改后点击"SAVE"保存，重启后端服务生效。'));
  S.push(sp());

  S.push(h2('7.4  仪器对照 — 相机通道映射'));
  S.push(p('列出 D0–D8 全部仪表，每行右侧下拉框选择对应的摄像头通道编号（0–8）。此映射决定触发识别时系统向哪个摄像头发出拍摄请求。'));
  const settTop = img('settings_top_1777223322879.png', 440, 448);
  if (settTop) S.push(settTop);
  S.push(caption('图 7-2  仪器对照配置（相机通道映射）'));
  S.push(sp());
  S.push(p('配置完成后点击"保存手动修改"按钮。修改立即持久化至数据库，下次触发识别时生效，不影响当前正在运行的任务。'));
  S.push(sp());

  S.push(h2('7.5  Neural Engine — 推理引擎参数'));
  const settNeural = img('settings_prompt_templates_1777221762669.png', 440, 448);
  if (settNeural) S.push(settNeural);
  S.push(caption('图 7-3  Neural Engine 区域（显示 GPU 状态、模型信息及可调参数）'));
  S.push(sp());
  S.push(mkTable([2200, 6826],
    ['配置项', '说明'],
    [
      ['运算节点（GPU）', '显示可用 GPU 名称及当前显存使用率；绿色圆点表示 llama-server 正常在线'],
      ['QianFan-OCR 模型', '显示已加载的 GGUF 文件名及量化参数（如 INT8Q_Z2MF2T3S.8）'],
      ['Temperature', '推理采样温度（0.0–2.0）。建议 0–0.2 以获得稳定的 OCR 结果；过高会导致模型"发散"'],
      ['Max Tokens', 'EXP-OCR 单次推理最大输出 Token 数（默认约 2048）。对于字段较多的仪表（如 D0），适当增大'],
      ['SYNC CONFIGURATION', '将当前面板参数同步到后端配置文件；修改 Temperature/Tokens 后必须点击此按钮生效'],
    ]
  ));
  S.push(pb());

  // ══════════════════════════════════════════════════════════════════════════
  // Chapter 8 — 提示词模板管理
  // ══════════════════════════════════════════════════════════════════════════
  S.push(h1('第八章  提示词模板管理'));

  S.push(h2('8.1  进入模板管理'));
  S.push(p('提示词模板（Prompt Template）是 EXP-OCR 识别准确率的核心决定因素。系统提供图形化模板管理界面，无需修改代码即可新增和调整仪表识别逻辑。'));
  S.push(sp());
  S.push(p('进入路径：在系统任意页面点击顶栏右上角的"TEMPLATES"文字链接，跳转至仪器识别模板管理页面。'));
  S.push(sp());
  const tmplList = img('template_management_list_1777222812884.png', 460, 468);
  if (tmplList) S.push(tmplList);
  S.push(caption('图 8-1  仪器识别模板管理页面（显示系统内全部 14+ 个模板）'));
  S.push(sp());
  S.push(p('每张模板卡片显示：仪表名称、识别关键词（Keywords）和已配置的识别字段数量（字段：X 个）。点击任意卡片进入编辑页面。'));
  S.push(sp());

  S.push(h2('8.2  模板数据结构'));
  S.push(p('每个 Prompt Template 在数据库中以 JSON 形式存储，包含以下字段：'));
  S.push(svgP('tmplStruct', 544, 192));
  S.push(caption('图 8-2  Prompt Template 数据结构'));
  S.push(sp());

  S.push(h2('8.3  编辑现有模板'));
  const te0 = img('template_editor_d0_mixer_1777222826097.png', 460, 468);
  if (te0) S.push(te0);
  S.push(caption('图 8-3  D0 混调器模板编辑页面（显示仪器标识、关键词和 5 个识别字段）'));
  S.push(sp());
  S.push(p('编辑器界面说明：'));
  S.push(mkTable([2400, 6626],
    ['编辑项', '操作说明'],
    [
      ['仪器标识（instrument_type）', '唯一键，不建议修改已有仪表的标识，修改会导致历史数据关联断裂'],
      ['显示名称', '前端卡片和报表中显示的中文名称，可自由修改'],
      ['描述（description）', '注入 Prompt 的背景描述，帮助 EXP-OCR 理解仪表用途；建议用简洁专业的中文描述'],
      ['识别关键词', '辅助 YOLO 后分类的特征词，点击"＋"按钮添加，点击标签上的"×"删除'],
      ['读数字段配置', '列出所有字段（KEY / LABEL / UNIT / TYPE）；点击"＋添加字段"新增，拖拽调整顺序'],
    ]
  ));
  S.push(sp());
  const te3 = img('template_editor_d3_ph_meter_1777223014134.png', 440, 448);
  if (te3) S.push(te3);
  S.push(caption('图 8-4  D3 pH 计模板（回到控制台时前方显示实验列表的空白状态）'));
  S.push(sp());

  S.push(h2('8.4  字段配置详解'));
  S.push(p('每个识别字段（field）包含四个属性：'));
  S.push(mkTable([1600, 1800, 5626],
    ['属性', '示例值', '说明'],
    [
      ['KEY', 'current_speed', '字段唯一标识，写入数据库；命名建议：小写 + 下划线，英文语义明确'],
      ['LABEL', '当前转速', '前端卡片中显示的中文标签名'],
      ['UNIT', '转', '数值单位（可为空字符串）；显示在卡片数值后面'],
      ['TYPE', '数值 (Float)', '目前支持 Float（浮点数）和 String（字符串）两种类型'],
    ]
  ));
  S.push(sp());

  S.push(h2('8.5  新建自定义仪表模板'));
  S.push(p('如需接入新型号仪表，点击模板列表右上角"＋ 新增仪器模板"按钮：'));
  S.push(numbered('在"仪器标识"框输入唯一英文 ID（如 "D9" 或 "custom_balance"）。'));
  S.push(numbered('填写中文显示名称和仪表描述。'));
  S.push(numbered('添加若干识别关键词（仪表品牌名、型号、显示屏特征词等）。'));
  S.push(numbered('逐一添加识别字段（至少一个字段）。'));
  S.push(numbered('点击保存后，新模板立即出现在"新建实验"对话框的实验类型列表中。'));
  S.push(numbered('在 Settings 的仪器对照中为新仪表绑定对应摄像头通道。'));
  S.push(sp());
  S.push(note('Prompt Template 的识别准确率很大程度取决于 description 和字段 KEY 的质量。建议参考 D3（pH计）的模板风格来编写新仪表描述。'));
  S.push(pb());

  // ══════════════════════════════════════════════════════════════════════════
  // Chapter 9 — 仪表规格手册 D0–D8
  // ══════════════════════════════════════════════════════════════════════════
  S.push(h1('第九章  仪表规格手册（D0–D8）'));

  // D0
  S.push(h2('9.1  D0 — 混调器（Advanced Mixer）'));
  S.push(p('混调器（品牌：LABHTD / 青岛恒泰达）是乳化实验的核心搅拌设备，控制面板为触摸屏，显示当前运行参数。系统识别其多行参数数值，包括运行模式、各阶速度设定、剩余时长等。'));
  S.push(sp());
  S.push(mkTable([1600, 2200, 2200, 3026],
    ['参数名称', '说明', '典型值 / 示例', '备注'],
    [
      ['mode（模式）', '当前工作模式', 'Auto / Manual', '通过按钮高亮颜色判断；V1.2 自适应检测'],
      ['current_speed（当前转速）', '实时转速', '10000 rpm', ''],
      ['seg1_speed（一档转速）', '程序第一段设定转速', '10000', ''],
      ['total_time（总时长）', '程序总运行时长', '90 s', '计时模式'],
      ['remaining_time（剩余时长）', '倒计时剩余时间', '00:10', ''],
      ['一次方 / 二次方 / 三次方', '电机扭矩多项式校准系数', '10000 / 10000 / 22000', 'V1.2 左边缘扫描'],
    ]
  ));
  S.push(sp());
  const d0cap = img('instrument_card_d0_mixer_1777222254684.png', 380, 246);
  if (d0cap) S.push(d0cap);
  S.push(caption('图 9-1  D0 混调器 YOLO 裁切截图（触摸屏控制面板，品牌 LABHTD）'));
  S.push(sp());
  const d0full = img('instrument_d0_1777225339858.png', 460, 468);
  if (d0full) S.push(d0full);
  S.push(caption('图 9-2  D0 混调器识别完成后卡片视图（转速、模式、校准参数均已填充）'));
  S.push(pb());

  // D1/D2
  S.push(h2('9.2  D1 / D2 — 电子天平（Balance 1 / 2）'));
  S.push(p('D1 和 D2 是同一区域的两台电子分析天平，共用 F3 摄像头。YOLOv8 通过 Bounding Box X 坐标区分左侧（D1）和右侧（D2）。V1.2 针对天平读数屏采用严格零填充裁切策略，避免负号和小数点区域被截断。'));
  S.push(sp());
  S.push(mkTable([1600, 2200, 2200, 3026],
    ['参数名称', '说明', '典型值 / 示例', '备注'],
    [
      ['weight（重量）', '当前称量读数', '46.53 g', '精度 0.01 g；V1.2 移除数值 placeholder 干扰'],
    ]
  ));
  S.push(sp());
  const d1full = img('instrument_d1_1777225340373.png', 460, 468);
  if (d1full) S.push(d1full);
  S.push(caption('图 9-3  D1 电子天平（左）和 D2 电子天平（右）识别结果，重量已填充至卡片'));
  S.push(pb());

  // D3
  S.push(h2('9.3  D3 — 台式 pH 计'));
  S.push(p('D3 为实验室台式 pH 计（量程 0–14 pH），与 D1/D2 共用 F3 摄像头，位于画面右侧区域。V1.2 将 pH、温度、mV 三参数整合为单次快照识别，避免多次抓拍造成的时间差影响数据一致性。执行标准：SY/T 5107-2016。'));
  S.push(sp());
  S.push(mkTable([1600, 2200, 2200, 3026],
    ['参数名称', '说明', '典型值 / 示例', '备注'],
    [
      ['ph_value（pH 值）', '溶液酸碱度', '6.73', '精度 0.01；显示于屏幕最大数字区'],
      ['temperature（温度）', '溶液实测温度', '25.0 ℃', '温度补偿传感器'],
      ['mv（电势）', '电极电势', '100.0 mV', ''],
    ]
  ));
  S.push(sp());
  const d3cap = img('instrument_card_d3_ph_data_1777222352570.png', 380, 246);
  if (d3cap) S.push(d3cap);
  S.push(caption('图 9-4  D3 台式 pH 计 YOLO 裁切截图（显示 pH 6.73、温度 25.0°C、量程 100.0）'));
  S.push(sp());
  const d3full = img('instrument_d3_1777225341963.png', 460, 468);
  if (d3full) S.push(d3full);
  S.push(caption('图 9-5  D3 识别完成后卡片视图'));
  S.push(pb());

  // D4
  S.push(h2('9.4  D4 — 水质矿化度检测仪'));
  S.push(p('D4 为便携式水质矿化度检测仪，有时水平放置于工作台，导致仪器屏幕相对摄像头旋转 90° 或 180°。V1.2 集成了 OpenCV 自动旋转修正算法：通过 CLAHE 增强后的 Canny 边缘密度来判断屏幕方向并自动纠正。当屏幕完全黑屏（仪器关机）时强制返回 null，不写入无效数值。'));
  S.push(sp());
  S.push(mkTable([1600, 2200, 2200, 3026],
    ['参数名称', '说明', '典型值 / 示例', '备注'],
    [
      ['tds（矿化度）', '总溶解固体浓度', '50684 mg/L', ''],
      ['conductivity（电导率）', '溶液导电能力', '99068 μS/cm', ''],
      ['temperature（温度）', '检测时溶液温度', '25.0 ℃', ''],
    ]
  ));
  S.push(sp());
  const d4cap = img('instrument_card_d4_water_data_1777222353769.png', 300, 390);
  if (d4cap) S.push(d4cap);
  S.push(caption('图 9-6  D4 水质矿化度检测仪 YOLO 裁切截图（竖向屏幕）'));
  S.push(pb());

  // D5
  S.push(h2('9.5  D5 — 界面张力仪'));
  S.push(p('D5 界面张力仪用于测量液液界面张力，屏幕右侧显示多行数据。V1.2 针对屏幕可能显示 5 行或 6 行数据的情况进行了自适应行数检测。Excel 导出支持多次测量值的算术平均值自动计算。执行标准：SY/T 5370-2018。'));
  S.push(sp());
  S.push(mkTable([1600, 2200, 2200, 3026],
    ['参数名称', '说明', '典型值 / 示例', '备注'],
    [
      ['ift（界面/表面张力）', '测量目标张力值', '1.662 mN/m', '精度 0.001'],
      ['density_diff（密度差）', '两相密度差 Δρ', 'N/A', '部分型号不显示'],
      ['upper_level / lower_level', '上/下液面多次读数', '10', 'V1.2 自适应 5/6 行'],
      ['measurement_r', '单次测量值', '5.0', ''],
    ]
  ));
  S.push(sp());
  const d5cap = img('instrument_card_d5_tension_data_1777222355021.png', 380, 246);
  if (d5cap) S.push(d5cap);
  S.push(caption('图 9-7  D5 界面张力仪 YOLO 裁切截图（显示日期、张力值及多行测量数据）'));
  S.push(sp());
  const d5full = img('instrument_d5_1777225342960.png', 460, 468);
  if (d5full) S.push(d5full);
  S.push(caption('图 9-8  D5 界面张力仪在全场景实验中的卡片视图'));
  S.push(pb());

  // D6
  S.push(h2('9.6  D6 — 扭矩搅拌器'));
  S.push(p('D6 扭矩搅拌器以 4 位数字液晶屏显示 RPM。当转速如 1000、1100、1110 时，首位数字"1"字形较窄，若 YOLO 裁切时边界过于紧贴会导致"1"被截断识别为"110"。V1.2 对该仪表强制采用左边缘扫描策略，在生成裁切坐标时向左额外扩展 5–8 个像素以确保完整。'));
  S.push(sp());
  S.push(mkTable([1600, 2200, 2200, 3026],
    ['参数名称', '说明', '典型值 / 示例', '备注'],
    [
      ['rpm（转速）', '当前搅拌转速', '1110 rpm', 'V1.2 左边缘扫描修正'],
      ['torque（扭矩）', '当前扭矩占比', '0 %', ''],
      ['mode（运行状态）', '运行/停止', 'RUN / STOP', ''],
      ['一次方 / 二次方 / 三次方', '校准参数各阶系数', '10000 / 10000 / 22000', ''],
    ]
  ));
  S.push(sp());
  const d6full = img('instrument_d6_1777225359709.png', 460, 468);
  if (d6full) S.push(d6full);
  S.push(caption('图 9-9  D6 扭矩搅拌器识别结果（转速、扭矩及校准参数）'));
  S.push(pb());

  // D7
  S.push(h2('9.7  D7 — 水浴锅'));
  S.push(p('水浴锅屏幕为小型方形 LED 显示，YOLO 在检测时可能同时检测到仪器外框和屏幕内框两个 Bounding Box。V1.2 通过面积筛选和中心距离惩罚机制，强制选取最小的内屏 Box，确保裁切区域准确对准液晶数字显示区。'));
  S.push(sp());
  S.push(mkTable([1600, 2200, 2200, 3026],
    ['参数名称', '说明', '典型值 / 示例', '备注'],
    [
      ['set_temp（设定温度）', '目标水温设定值 SP', '26.8 ℃', ''],
      ['actual_temp（实测温度）', '当前水温 PV', '26.8 ℃', '精度 ±0.1 ℃；V1.2 YOLO 多框压制'],
    ]
  ));
  S.push(sp());
  const d7full = img('instrument_d7_1777225360202.png', 460, 468);
  if (d7full) S.push(d7full);
  S.push(caption('图 9-10  D7 水浴锅识别结果（设定温度 26.8°C，实测温度 26.8°C）'));
  S.push(pb());

  // D8
  S.push(h2('9.8  D8 — 旋转粘度计'));
  S.push(p('D8 旋转粘度计（品牌：LABHTD）用于测量液体表观粘度，手持式竖屏设计。V1.2 将 100 r/min 目标转速下的读数绑定为主要识别字段，支持多次实验的均值自动计算。表观粘度换算公式：η (mPa·s) = (α × 5.077) / 1.704，其中 α 为 100 rpm 时的仪器读数。'));
  S.push(sp());
  S.push(mkTable([1600, 2200, 2200, 3026],
    ['参数名称', '说明', '典型值 / 示例', '备注'],
    [
      ['reading_100rpm', '100 r/min 时的仪器原始读数 α', '0', '主目标字段；换算公式见上'],
      ['reading_6rpm', '6 r/min 读数', '0', '辅助字段'],
      ['reading_3rpm', '3 r/min 读数', '0', '辅助字段'],
      ['torque（扭矩%）', '当前扭矩占满量程百分比', '0 %', '超量程时报警'],
      ['spindle（转子号）', '已安装的转子编号', 'No.4 / L1–L4', ''],
    ]
  ));
  S.push(sp());
  const d8cap = img('instrument_card_d8_viscometer_data_1777222358564.png', 300, 390);
  if (d8cap) S.push(d8cap);
  S.push(caption('图 9-11  D8 旋转粘度计 YOLO 裁切截图（手持竖屏，显示多参数读数）'));
  S.push(sp());
  const d8full = img('instrument_d8_1777225360681.png', 460, 468);
  if (d8full) S.push(d8full);
  S.push(caption('图 9-12  D8 旋转粘度计识别完成后卡片视图'));
  S.push(pb());

  // ══════════════════════════════════════════════════════════════════════════
  // Chapter 10 — OCR 流水线技术说明
  // ══════════════════════════════════════════════════════════════════════════
  S.push(h1('第十章  OCR 流水线技术说明'));

  S.push(h2('10.1  流水线总览'));
  S.push(svgP('pipeline', 608, 120));
  S.push(caption('图 10-1  OCR 七级处理流水线'));
  S.push(sp());
  S.push(mkTable([1000, 2000, 6026],
    ['Stage', '名称', '核心实现'],
    [
      ['1', '触发请求', '前端 POST /experiments/{id}/readings/capture → 后端创建 TaskManager 异步任务'],
      ['2', 'RTSP 抓拍', 'CameraClient / MockCameraClient → 获取 JPEG 全景图 → 存入 storage/images/'],
      ['3', 'YOLOv8 检测', 'YOLOv8DetectorService.detect() → 面积权重 + 置信度权重 + 中心距离权重打分 → 取最优 BBox'],
      ['4', 'OpenCV 处理', 'CLAHE 增强 → 双边滤波 → 透视纠偏；D4 额外执行 Canny 旋转修正'],
      ['5', 'EXP-OCR 推理', 'LLMProvider.infer(image_b64, prompt) → POST llama-server /v1/chat/completions'],
      ['6', 'JSON 提取', 'PostProcessor：正则提取 JSON → 类型转换 → 超量程检测 → null 策略'],
      ['7', '结果入库', 'upsert_reading() → SQLite → SSE 事件流推送前端实时刷新'],
    ]
  ));
  S.push(sp());

  S.push(h2('10.2  YOLOv8 目标检测详解'));
  S.push(p('系统使用自定义训练权重 last.pt，该权重在实验室真实环境下对 D0–D8 共 9 类目标进行了标注训练。检测时采用三维评分机制选取最优框：'));
  S.push(bullet('面积权重（Area Score）：BBox 面积越接近预期仪表屏幕面积，得分越高；过大或过小均扣分'));
  S.push(bullet('置信度权重（Confidence Score）：YOLOv8 输出的类别置信度直接作为评分分量'));
  S.push(bullet('中心距离惩罚（Center Distance Penalty）：BBox 中心偏离图像中央越远，扣分越大（适用于 D7 多框压制）'));
  S.push(sp());

  S.push(h2('10.3  OpenCV 图像处理管线'));
  S.push(p('针对每台仪表 BBox 裁切后的区域，执行如下处理序列：'));
  S.push(numbered('CLAHE（Contrast Limited Adaptive Histogram Equalization）：以 8×8 tile 为单位进行局部对比度增强，适应工业现场光线不均匀的情况。'));
  S.push(numbered('双边滤波（Bilateral Filter）：在保持边缘锐度的前提下降低背景噪声，参数 d=9, sigmaColor=75, sigmaSpace=75。'));
  S.push(numbered('透视纠偏（Perspective Warp）：通过 Hough 直线检测识别仪表边框，计算透视变换矩阵并施加 warpPerspective 校正梯形畸变。'));
  S.push(numbered('D4 专项旋转修正：对水质仪图像计算 Canny 边缘在水平和垂直方向的密度比，若垂直边缘密度明显高于水平，则旋转 90°；若比值反转则旋转 270°。'));
  S.push(sp());

  S.push(h2('10.4  EXP-OCR 推理引擎'));
  S.push(p('EXP-OCR 是基于 InternVL 架构的多模态视觉语言模型，以 Q4_K_M 精度量化为 GGUF 格式，由 llama.cpp 的 llama-server 托管。系统以 Base64 编码的图像和结构化 Prompt 作为输入，要求模型返回严格的 JSON 格式读数。'));
  S.push(sp());
  S.push(p('Prompt 结构示例（以 D3 pH 计为例）：'));
  S.push(code('你是一位实验室仪表读数专家，正在识别【台式 pH 计】的显示屏。'));
  S.push(code('请从图像中提取以下字段并以 JSON 格式返回（无法识别的字段返回 null）：'));
  S.push(code('{"ph_value": <数值>, "temperature": <数值>, "mv": <数值>}'));
  S.push(sp());
  S.push(tip('Prompt 的质量直接影响识别准确率。在 Template 管理页面修改 description 和 fields 时，建议用"仪表专家"角色设定 + 明确的字段期望值范围，可显著减少模型的"幻觉"输出。'));
  S.push(pb());

  // ══════════════════════════════════════════════════════════════════════════
  // Chapter 11 — 常见问题与维护
  // ══════════════════════════════════════════════════════════════════════════
  S.push(h1('第十一章  常见问题与维护'));

  S.push(h2('11.1  故障排查快速参考'));
  S.push(mkTable([2200, 2800, 4026],
    ['故障描述', '可能原因', '处理建议'],
    [
      ['推理超时 / 卡片长时间 Loading', 'GPU 显存溢出；llama-server 崩溃', '检查 llama_error.log；重启 llama-server；必要时重启系统释放显存'],
      ['识别结果全为 null', '仪表黑屏/关机；YOLO 未检测到仪表；摄像头视角偏移', '确认仪表已开机并显示数值；在 Context View 中查看全景图；检查 YOLO BBox 是否定位准确'],
      ['识别数值偏差大（如丢失首位"1"）', '裁切边界过紧；相机焦距偏移', '确认使用最新 last.pt；在 yolo_debug.log 中查看 BBox 坐标；重新调整相机焦距并固定'],
      ['OCR 结果乱码 / 非数字', 'EXP-OCR 推理异常；Prompt 被干扰', '降低 Temperature 至 0.1；检查 Prompt 是否含特殊字符；重启 llama-server'],
      ['无法获取相机图像（RTSP 超时）', 'RTSP 链路中断；摄像头断电/断网', '检查摄像头电源和网线；ping 摄像头 IP；确认 RTSP 地址和端口配置正确'],
      ['前端卡片不更新（卡在 Processing）', '后端 SSE 事件流断开', '刷新浏览器页面；检查 8001 端口后端服务是否正常运行'],
      ['导出按钮不出现', '实验无识别读数', '至少执行一次识别并确认卡片有数值后再尝试导出'],
      ['导出的 xlsx 数值全为空', '识别数据字段名不匹配', '检查 Template 中 field KEY 是否与导出代码中的 field_key 一致'],
      ['D4 水质仪读数方向错误', '相机角度变化导致旋转方向判断失误', '检查 Context View 画面；调整摄像头角度使 D4 竖直朝上；或调整 CLAHE 参数阈值'],
      ['Settings 修改后不生效', '未点击"保存"或"SYNC CONFIGURATION"', '仪器对照修改后点击"保存手动修改"；Neural Engine 参数点击"SYNC CONFIGURATION"'],
    ]
  ));
  S.push(sp());

  S.push(h2('11.2  日志文件说明'));
  S.push(mkTable([2400, 6626],
    ['日志文件', '内容说明'],
    [
      ['llama_error.log', 'llama-server 的 stderr 输出，包含模型加载错误、显存分配失败等严重问题。首要排查文件。'],
      ['llama_stdout.log', 'llama-server 的 stdout 输出，记录每次推理请求的输入/输出摘要和性能指标。'],
      ['yolo_debug.log', 'YOLOv8 检测结果详细记录，包含每次推理的 BBox 坐标、类别和置信度。用于排查裁切偏差。'],
      ['yolo_debug_raw.log', 'YOLOv8 原始推理输出（未经后处理评分），包含所有候选框，用于深度调试。'],
    ]
  ));
  S.push(sp());

  S.push(h2('11.3  数据备份建议'));
  S.push(bullet('每日备份 backend/experiments.db（所有实验数据、读数记录和 Prompt 模板）'));
  S.push(bullet('定期备份 storage/images/ 目录（原始截图及处理后图像，用于审计追溯）'));
  S.push(bullet('备份时机：每次重要实验完成后立即备份；部署新版本前完整备份'));
  S.push(bullet('推荐方案：使用 Windows 任务计划程序 + Robocopy 定时增量同步到外部硬盘'));
  S.push(sp());
  S.push(code('robocopy C:\\ocr-new\\backend\\experiments.db D:\\backup\\ocr\\ /MIR /LOG:backup.log'));
  S.push(pb());

  // ══════════════════════════════════════════════════════════════════════════
  // Appendix
  // ══════════════════════════════════════════════════════════════════════════
  S.push(h1('附录'));

  S.push(h2('附录 A  关键 API 接口速查'));
  S.push(mkTable([2800, 1400, 4826],
    ['接口路径', '方法', '功能说明'],
    [
      ['/experiments', 'GET', '列出所有实验（含 readings 嵌套数据）'],
      ['/experiments', 'POST', '创建新实验（body: name, type, fields）'],
      ['/experiments/{id}', 'GET', '获取单个实验详情'],
      ['/experiments/{id}', 'DELETE', '删除实验及关联读数'],
      ['/experiments/{id}/readings/capture', 'POST（SSE）', '触发 OCR 识别；以 SSE 流式推送进度和结果'],
      ['/experiments/{id}/export', 'GET', '导出实验数据为 xlsx；按实验类型套用模板'],
      ['/readings/{id}', 'PUT', '手动更新某条读数的值（Manual Override）'],
      ['/config', 'GET / PUT', '读取 / 写入全局配置（相机映射、存储路径等）'],
      ['/templates', 'GET', '获取所有仪表 Prompt 模板列表'],
      ['/templates/{type}', 'GET / PUT', '获取 / 更新指定仪表的 Prompt 模板'],
    ]
  ));
  S.push(sp());

  S.push(h2('附录 B  Excel 导出字段映射总表'));
  S.push(mkTable([1600, 2200, 2000, 3226],
    ['实验类型', 'Excel 主字段', '来源（field_key）', 'DB 表'],
    [
      ['ph_value', 'pH 值 / 温度', 'ph_measurement → ocr_data.ph_value / temperature', 'readings'],
      ['apparent_viscosity', '3rpm / 6rpm / 100rpm / η', 'reading_3rpm / reading_6rpm / reading_100rpm', 'readings'],
      ['kinematic_viscosity', '流经时间 t', 'flow_time', 'readings'],
      ['surface_tension', '水表面张力 / 破胶液表面张力 / 界面张力', 'water_surface_tension / fluid_surface_tension / fluid_interface_tension', 'readings'],
      ['water_mineralization', '矿化度 / 电导率 / 温度', 'tds / conductivity / temperature', 'readings'],
      ['test', '所有字段（按相机位分组）', '各字段 field_key', 'readings'],
    ]
  ));
  S.push(sp());

  S.push(h2('附录 C  实验类型与仪表对应关系'));
  S.push(mkTable([2600, 6426],
    ['实验类型（type 字段值）', '涉及仪表 / 特殊说明'],
    [
      ['surface_tension', 'D0·D1·D2·D3·D4·D5·D6·D7（全场景张力测试）'],
      ['apparent_viscosity', 'D8 旋转粘度计（100 r/min 目标）'],
      ['kinematic_viscosity', '手动录入（不触发 OCR；需填写毛细管参数）'],
      ['ph_value', 'D3 台式 pH 计'],
      ['water_mineralization', 'D4 水质矿化度检测仪'],
      ['test', 'D0–D8 全部（调试专用，生产环境慎用）'],
    ]
  ));
  S.push(sp());

  // final note
  S.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 800 }, children: [new TextRun({ text: '─────────────────────────────────────', color: 'CCCCCC' })] }));
  S.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 200 }, children: [new TextRun({ text: '文档编制：WANGJ 视觉工程项目组  ·  版本 V1.2.0  ·  2026年4月27日', size: 18, color: '888888', italics: true })] }));
  S.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 100 }, children: [new TextRun({ text: 'WEWODON AI OCR LABORATORY  ·  本文档仅供内部使用', size: 18, color: 'AAAAAA', italics: true })] }));

  return S;
}

// ── assemble document ─────────────────────────────────────────────────────────
async function main() {
  const sections = await buildSections();

  const doc = new Document({
    styles: {
      default: { document: { run: { font: 'Arial', size: 22 } } },
      paragraphStyles: [
        { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
          run: { size: 40, bold: true, color: '1565C0', font: 'Arial' },
          paragraph: { spacing: { before: 480, after: 240 }, outlineLevel: 0,
            border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: 'D0D0D0', space: 4 } } } },
        { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
          run: { size: 28, bold: true, color: '37474F', font: 'Arial' },
          paragraph: { spacing: { before: 360, after: 160 }, outlineLevel: 1 } },
        { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
          run: { size: 24, bold: true, color: '546E7A', font: 'Arial' },
          paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 2 } },
      ]
    },
    numbering: {
      config: [
        { reference: 'bullets', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
        { reference: 'subbullets', levels: [{ level: 0, format: LevelFormat.BULLET, text: '–', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 1080, hanging: 360 } } } }] },
        { reference: 'numbers', levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      ]
    },
    sections: [{
      properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
      headers: { default: new Header({ children: [new Paragraph({ border: { bottom: { style: BorderStyle.SINGLE, size: 2, color: '4472C4', space: 4 } }, children: [ new TextRun({ text: 'WANGJ-OCR V1.2  智能实验方舱  |  技术与操作手册（详版）', size: 18, color: '888888', font: 'Arial' }) ] })] }) },
      footers: { default: new Footer({ children: [new Paragraph({ border: { top: { style: BorderStyle.SINGLE, size: 2, color: 'D0D0D0', space: 4 } }, alignment: AlignmentType.CENTER, children: [ new TextRun({ text: '第 ', size: 18, color: '888888' }), new TextRun({ children: [PageNumber.CURRENT], size: 18, color: '4472C4', bold: true }), new TextRun({ text: ' 页  |  内部保密文件，请勿外传', size: 18, color: '888888' }) ] })] }) },
      children: sections
    }]
  });

  const buf = await Packer.toBuffer(doc);
  fs.writeFileSync(OUT, buf);
  console.log('OK:', OUT);
}

main().catch(e => { console.error('ERROR:', e.message, '\n', e.stack); process.exit(1); });
