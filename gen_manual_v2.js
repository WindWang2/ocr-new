'use strict';
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
  VerticalAlign, PageNumber, PageBreak, LevelFormat, TableOfContents
} = require('docx');
const fs = require('fs');
const path = require('path');
const sharp = require('sharp');

const SHOTS = 'C:/Users/wangj.KEVIN/.gemini/antigravity/brain/2f8c1a6b-19c1-4ea8-8077-e359bc030c4a';
const OUT   = 'C:/Users/wangj.KEVIN/projects/ocr-new/WANGJ_OCR_V1.2_操作手册_详版.docx';

// ─── helpers ─────────────────────────────────────────────────────────────────
const pngBufs = {};

function img(file, w, h, align) {
  const fp = path.join(SHOTS, file);
  if (!fs.existsSync(fp)) return null;
  return new Paragraph({
    alignment: align || AlignmentType.CENTER,
    spacing: { before: 80, after: 80 },
    children: [new ImageRun({
      type: 'png', data: fs.readFileSync(fp),
      transformation: { width: w, height: h },
      altText: { title: file, description: file, name: file }
    })]
  });
}

function svgP(key, w, h) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 80, after: 80 },
    children: [new ImageRun({
      type: 'png', data: pngBufs[key],
      transformation: { width: w, height: h },
      altText: { title: key, description: key, name: key }
    })]
  });
}

function h1(t) { return new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] }); }
function h2(t) { return new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] }); }
function h3(t) { return new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(t)] }); }

function p(text, opts) {
  return new Paragraph({ spacing: { before: 60, after: 60 }, children: [new TextRun({ text, ...opts })] });
}
function bp(text) { return p(text, { bold: true }); }
function sp() { return new Paragraph({ children: [] }); }
function pb() { return new Paragraph({ children: [new PageBreak()] }); }

function caption(text) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 40, after: 200 },
    children: [new TextRun({ text, italics: true, color: '666666', size: 18 })]
  });
}

function note(text) {
  return new Paragraph({
    shading: { fill: 'FFF9C4', type: ShadingType.CLEAR },
    border: { left: { style: BorderStyle.SINGLE, size: 4, color: 'F9A825', space: 8 } },
    spacing: { before: 100, after: 100 }, indent: { left: 360 },
    children: [new TextRun({ text: '⚠ ' + text, size: 20, color: '5D4037' })]
  });
}

function tip(text) {
  return new Paragraph({
    shading: { fill: 'E8F5E9', type: ShadingType.CLEAR },
    border: { left: { style: BorderStyle.SINGLE, size: 4, color: '2E7D32', space: 8 } },
    spacing: { before: 100, after: 100 }, indent: { left: 360 },
    children: [new TextRun({ text: '✓ ' + text, size: 20, color: '1B5E20' })]
  });
}

function code(text, color) {
  return new Paragraph({
    shading: { fill: 'F5F5F5', type: ShadingType.CLEAR },
    border: { left: { style: BorderStyle.SINGLE, size: 4, color: color || '1565C0', space: 8 } },
    spacing: { before: 80, after: 80 }, indent: { left: 360 },
    children: [new TextRun({ text, font: 'Courier New', size: 18, color: color ? '1A237E' : '1A237E' })]
  });
}

function bullet(text, opts) {
  return new Paragraph({
    numbering: { reference: 'bullets', level: 0 },
    spacing: { before: 40, after: 40 },
    children: [new TextRun({ text, ...opts })]
  });
}

function numbered(text) {
  return new Paragraph({
    numbering: { reference: 'numbers', level: 0 },
    spacing: { before: 60, after: 60 },
    children: [new TextRun(text)]
  });
}

const tblW = 9026;
const CB = { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' };
const BORD = { top: CB, bottom: CB, left: CB, right: CB };
const HBORD = {
  top: { style: BorderStyle.SINGLE, size: 1, color: '4472C4' },
  bottom: { style: BorderStyle.SINGLE, size: 2, color: '4472C4' },
  left: CB, right: CB
};

function tc(text, { bg, b, w, align, sz } = {}) {
  return new TableCell({
    borders: BORD, width: w ? { size: w, type: WidthType.DXA } : undefined,
    shading: bg ? { fill: bg, type: ShadingType.CLEAR } : undefined,
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({
      alignment: align || AlignmentType.LEFT,
      spacing: { before: 20, after: 20 },
      children: [new TextRun({ text, bold: !!b, size: sz || 20 })]
    })]
  });
}

function hc(text, w) {
  return new TableCell({
    borders: HBORD, width: { size: w, type: WidthType.DXA },
    shading: { fill: '4472C4', type: ShadingType.CLEAR },
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 20, after: 20 },
      children: [new TextRun({ text, bold: true, color: 'FFFFFF', size: 20 })]
    })]
  });
}

function mkTable(cols, headerLabels, rows) {
  const headerRow = new TableRow({ children: headerLabels.map((l, i) => hc(l, cols[i])) });
  const dataRows = rows.map((row, ri) =>
    new TableRow({ children: row.map((txt, ci) => tc(txt, { w: cols[ci], bg: ri % 2 === 0 ? 'F5F5F5' : 'FFFFFF' })) })
  );
  return new Table({ width: { size: tblW, type: WidthType.DXA }, columnWidths: cols, rows: [headerRow, ...dataRows] });
}

function divider() {
  return new Paragraph({
    border: { bottom: { style: BorderStyle.SINGLE, size: 2, color: 'E0E0E0', space: 4 } },
    spacing: { before: 200, after: 200 },
    children: [new TextRun('')]
  });
}

// ─── SVG definitions ──────────────────────────────────────────────────────────

const archSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="700" height="460" viewBox="0 0 700 460">
<defs><marker id="arr" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#546E7A"/></marker></defs>
<rect width="700" height="460" fill="#FAFAFA" rx="6"/>
<rect x="14" y="12" width="672" height="85" rx="6" fill="#E3F2FD" stroke="#1565C0" stroke-width="1.5"/>
<text x="350" y="30" text-anchor="middle" font-family="Arial" font-size="11" font-weight="bold" fill="#0D47A1">表现层 (Frontend) · React / Next.js · Port 3000</text>
<rect x="28" y="38" width="158" height="46" rx="5" fill="#1976D2"/><text x="107" y="58" text-anchor="middle" font-family="Arial" font-size="10" fill="white">Web 用户界面</text><text x="107" y="74" text-anchor="middle" font-family="Arial" font-size="9" fill="#BBDEFB">React Components</text>
<rect x="206" y="38" width="158" height="46" rx="5" fill="#1976D2"/><text x="285" y="58" text-anchor="middle" font-family="Arial" font-size="10" fill="white">状态管理</text><text x="285" y="74" text-anchor="middle" font-family="Arial" font-size="9" fill="#BBDEFB">Zustand / Context</text>
<rect x="384" y="38" width="158" height="46" rx="5" fill="#1976D2"/><text x="463" y="58" text-anchor="middle" font-family="Arial" font-size="10" fill="white">API 通讯 / SSE</text><text x="463" y="74" text-anchor="middle" font-family="Arial" font-size="9" fill="#BBDEFB">fetch / EventSource</text>
<line x1="350" y1="97" x2="350" y2="118" stroke="#546E7A" stroke-width="2" marker-end="url(#arr)"/>
<rect x="14" y="120" width="672" height="85" rx="6" fill="#E8F5E9" stroke="#2E7D32" stroke-width="1.5"/>
<text x="350" y="138" text-anchor="middle" font-family="Arial" font-size="11" font-weight="bold" fill="#1B5E20">应用服务层 (Backend) · FastAPI / Uvicorn · Port 8001</text>
<rect x="28" y="145" width="158" height="46" rx="5" fill="#388E3C"/><text x="107" y="165" text-anchor="middle" font-family="Arial" font-size="10" fill="white">API 路由网关</text><text x="107" y="181" text-anchor="middle" font-family="Arial" font-size="9" fill="#C8E6C9">FastAPI Router</text>
<rect x="206" y="145" width="158" height="46" rx="5" fill="#388E3C"/><text x="285" y="165" text-anchor="middle" font-family="Arial" font-size="10" fill="white">流水线编排引擎</text><text x="285" y="181" text-anchor="middle" font-family="Arial" font-size="9" fill="#C8E6C9">MultiInstrumentPipeline</text>
<rect x="384" y="145" width="158" height="46" rx="5" fill="#388E3C"/><text x="463" y="165" text-anchor="middle" font-family="Arial" font-size="10" fill="white">任务管理器 + 导出</text><text x="463" y="181" text-anchor="middle" font-family="Arial" font-size="9" fill="#C8E6C9">task_manager / xlsx</text>
<line x1="350" y1="205" x2="350" y2="226" stroke="#546E7A" stroke-width="2" marker-end="url(#arr)"/>
<rect x="14" y="228" width="672" height="85" rx="6" fill="#FFF3E0" stroke="#E65100" stroke-width="1.5"/>
<text x="350" y="246" text-anchor="middle" font-family="Arial" font-size="11" font-weight="bold" fill="#BF360C">算法与推理层 (AI Engine) · llama-server · Port 8080</text>
<rect x="28" y="253" width="158" height="46" rx="5" fill="#F57C00"/><text x="107" y="273" text-anchor="middle" font-family="Arial" font-size="10" fill="white">YOLOv8 目标检测</text><text x="107" y="289" text-anchor="middle" font-family="Arial" font-size="9" fill="#FFE0B2">last.pt · D0-D8 定位</text>
<rect x="206" y="253" width="158" height="46" rx="5" fill="#F57C00"/><text x="285" y="273" text-anchor="middle" font-family="Arial" font-size="10" fill="white">OpenCV 图像处理</text><text x="285" y="289" text-anchor="middle" font-family="Arial" font-size="9" fill="#FFE0B2">CLAHE · 透视纠偏</text>
<rect x="384" y="253" width="158" height="46" rx="5" fill="#F57C00"/><text x="463" y="273" text-anchor="middle" font-family="Arial" font-size="10" fill="white">EXP-OCR 语义推理</text><text x="463" y="289" text-anchor="middle" font-family="Arial" font-size="9" fill="#FFE0B2">GGUF · Q4_K_M</text>
<line x1="350" y1="313" x2="350" y2="334" stroke="#546E7A" stroke-width="2" marker-end="url(#arr)"/>
<rect x="14" y="336" width="672" height="85" rx="6" fill="#F3E5F5" stroke="#6A1B9A" stroke-width="1.5"/>
<text x="350" y="354" text-anchor="middle" font-family="Arial" font-size="11" font-weight="bold" fill="#4A148C">基础设施与存储</text>
<rect x="28" y="361" width="158" height="46" rx="5" fill="#7B1FA2"/><text x="107" y="381" text-anchor="middle" font-family="Arial" font-size="10" fill="white">RTSP 工业相机</text><text x="107" y="397" text-anchor="middle" font-family="Arial" font-size="9" fill="#E1BEE7">F0·F3·F5·F7·F8</text>
<rect x="206" y="361" width="158" height="46" rx="5" fill="#7B1FA2"/><text x="285" y="381" text-anchor="middle" font-family="Arial" font-size="10" fill="white">SQLite 数据库</text><text x="285" y="397" text-anchor="middle" font-family="Arial" font-size="9" fill="#E1BEE7">experiments.db</text>
<rect x="384" y="361" width="158" height="46" rx="5" fill="#7B1FA2"/><text x="463" y="381" text-anchor="middle" font-family="Arial" font-size="10" fill="white">本地存储系统</text><text x="463" y="397" text-anchor="middle" font-family="Arial" font-size="9" fill="#E1BEE7">storage/images/</text>
</svg>`;

const startupSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="560" height="200" viewBox="0 0 560 200">
<defs><marker id="sa" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#546E7A"/></marker></defs>
<rect width="560" height="200" fill="#FAFAFA" rx="4"/>
<rect x="20" y="60" width="140" height="80" rx="8" fill="#1565C0"/>
<text x="90" y="90" text-anchor="middle" font-family="Arial" font-size="11" font-weight="bold" fill="white">Step 1</text>
<text x="90" y="107" text-anchor="middle" font-family="Arial" font-size="10" fill="#BBDEFB">llama-server.exe</text>
<text x="90" y="122" text-anchor="middle" font-family="Arial" font-size="9" fill="#BBDEFB">Port 8080</text>
<text x="90" y="155" text-anchor="middle" font-family="Arial" font-size="8" fill="#888">EXP-OCR 推理引擎</text>
<line x1="160" y1="100" x2="200" y2="100" stroke="#546E7A" stroke-width="2.5" marker-end="url(#sa)"/>
<rect x="210" y="60" width="140" height="80" rx="8" fill="#2E7D32"/>
<text x="280" y="90" text-anchor="middle" font-family="Arial" font-size="11" font-weight="bold" fill="white">Step 2</text>
<text x="280" y="107" text-anchor="middle" font-family="Arial" font-size="10" fill="#C8E6C9">start_backend.bat</text>
<text x="280" y="122" text-anchor="middle" font-family="Arial" font-size="9" fill="#C8E6C9">Port 8001</text>
<text x="280" y="155" text-anchor="middle" font-family="Arial" font-size="8" fill="#888">FastAPI 后端服务</text>
<line x1="350" y1="100" x2="390" y2="100" stroke="#546E7A" stroke-width="2.5" marker-end="url(#sa)"/>
<rect x="400" y="60" width="140" height="80" rx="8" fill="#E65100"/>
<text x="470" y="90" text-anchor="middle" font-family="Arial" font-size="11" font-weight="bold" fill="white">Step 3</text>
<text x="470" y="107" text-anchor="middle" font-family="Arial" font-size="10" fill="#FFE0B2">start_frontend.bat</text>
<text x="470" y="122" text-anchor="middle" font-family="Arial" font-size="9" fill="#FFE0B2">Port 3000</text>
<text x="470" y="155" text-anchor="middle" font-family="Arial" font-size="8" fill="#888">React 前端界面</text>
<text x="280" y="188" text-anchor="middle" font-family="Arial" font-size="8" fill="#c00">* 必须严格按顺序启动，后端就绪后再启动前端</text>
</svg>`;

const pipelineSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="760" height="150" viewBox="0 0 760 150">
<defs><marker id="pa" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#546E7A"/></marker></defs>
<rect width="760" height="150" fill="#FAFAFA" rx="4"/>
<rect x="8"   y="35" width="86" height="70" rx="6" fill="#1565C0"/><text x="51" y="68" text-anchor="middle" font-family="Arial" font-size="9" fill="white" font-weight="bold">触发请求</text><text x="51" y="82" text-anchor="middle" font-family="Arial" font-size="8" fill="#BBDEFB">用户点击</text><text x="51" y="95" text-anchor="middle" font-family="Arial" font-size="8" fill="#BBDEFB">识别按钮</text><text x="51" y="122" text-anchor="middle" font-family="Arial" font-size="8" fill="#888">Step 1</text>
<line x1="94" y1="70" x2="106" y2="70" stroke="#546E7A" stroke-width="2" marker-end="url(#pa)"/>
<rect x="108" y="35" width="86" height="70" rx="6" fill="#0288D1"/><text x="151" y="68" text-anchor="middle" font-family="Arial" font-size="9" fill="white" font-weight="bold">RTSP 抓拍</text><text x="151" y="82" text-anchor="middle" font-family="Arial" font-size="8" fill="#B3E5FC">相机客户端</text><text x="151" y="95" text-anchor="middle" font-family="Arial" font-size="8" fill="#B3E5FC">获取图像</text><text x="151" y="122" text-anchor="middle" font-family="Arial" font-size="8" fill="#888">Step 2</text>
<line x1="194" y1="70" x2="206" y2="70" stroke="#546E7A" stroke-width="2" marker-end="url(#pa)"/>
<rect x="208" y="35" width="86" height="70" rx="6" fill="#F57C00"/><text x="251" y="68" text-anchor="middle" font-family="Arial" font-size="9" fill="white" font-weight="bold">YOLO 检测</text><text x="251" y="82" text-anchor="middle" font-family="Arial" font-size="8" fill="#FFE0B2">last.pt</text><text x="251" y="95" text-anchor="middle" font-family="Arial" font-size="8" fill="#FFE0B2">定位仪表区域</text><text x="251" y="122" text-anchor="middle" font-family="Arial" font-size="8" fill="#888">Step 3</text>
<line x1="294" y1="70" x2="306" y2="70" stroke="#546E7A" stroke-width="2" marker-end="url(#pa)"/>
<rect x="308" y="35" width="86" height="70" rx="6" fill="#E64A19"/><text x="351" y="68" text-anchor="middle" font-family="Arial" font-size="9" fill="white" font-weight="bold">图像处理</text><text x="351" y="82" text-anchor="middle" font-family="Arial" font-size="8" fill="#FFCCBC">CLAHE 增强</text><text x="351" y="95" text-anchor="middle" font-family="Arial" font-size="8" fill="#FFCCBC">透视纠偏</text><text x="351" y="122" text-anchor="middle" font-family="Arial" font-size="8" fill="#888">Step 4</text>
<line x1="394" y1="70" x2="406" y2="70" stroke="#546E7A" stroke-width="2" marker-end="url(#pa)"/>
<rect x="408" y="35" width="86" height="70" rx="6" fill="#7B1FA2"/><text x="451" y="68" text-anchor="middle" font-family="Arial" font-size="9" fill="white" font-weight="bold">EXP-OCR</text><text x="451" y="82" text-anchor="middle" font-family="Arial" font-size="8" fill="#E1BEE7">VLM 语义</text><text x="451" y="95" text-anchor="middle" font-family="Arial" font-size="8" fill="#E1BEE7">多模态推理</text><text x="451" y="122" text-anchor="middle" font-family="Arial" font-size="8" fill="#888">Step 5</text>
<line x1="494" y1="70" x2="506" y2="70" stroke="#546E7A" stroke-width="2" marker-end="url(#pa)"/>
<rect x="508" y="35" width="86" height="70" rx="6" fill="#2E7D32"/><text x="551" y="68" text-anchor="middle" font-family="Arial" font-size="9" fill="white" font-weight="bold">JSON 提取</text><text x="551" y="82" text-anchor="middle" font-family="Arial" font-size="8" fill="#C8E6C9">读数解析</text><text x="551" y="95" text-anchor="middle" font-family="Arial" font-size="8" fill="#C8E6C9">逻辑验证</text><text x="551" y="122" text-anchor="middle" font-family="Arial" font-size="8" fill="#888">Step 6</text>
<line x1="594" y1="70" x2="606" y2="70" stroke="#546E7A" stroke-width="2" marker-end="url(#pa)"/>
<rect x="608" y="35" width="86" height="70" rx="6" fill="#37474F"/><text x="651" y="68" text-anchor="middle" font-family="Arial" font-size="9" fill="white" font-weight="bold">结果入库</text><text x="651" y="82" text-anchor="middle" font-family="Arial" font-size="8" fill="#B0BEC5">SQLite 写入</text><text x="651" y="95" text-anchor="middle" font-family="Arial" font-size="8" fill="#B0BEC5">前端渲染</text><text x="651" y="122" text-anchor="middle" font-family="Arial" font-size="8" fill="#888">Step 7</text>
</svg>`;

const cardStateSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="680" height="140" viewBox="0 0 680 140">
<defs><marker id="ca" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#546E7A"/></marker></defs>
<rect width="680" height="140" fill="#FAFAFA" rx="4"/>
<rect x="10" y="40" width="110" height="52" rx="6" fill="#607D8B"/><text x="65" y="63" text-anchor="middle" font-family="Arial" font-size="10" fill="white" font-weight="bold">空白等待</text><text x="65" y="80" text-anchor="middle" font-family="Arial" font-size="9" fill="#CFD8DC">Idle</text>
<line x1="120" y1="66" x2="148" y2="66" stroke="#546E7A" stroke-width="2" marker-end="url(#ca)"/>
<text x="134" y="58" text-anchor="middle" font-family="Arial" font-size="8" fill="#888">点击⚡</text>
<rect x="150" y="40" width="110" height="52" rx="6" fill="#0288D1"/><text x="205" y="63" text-anchor="middle" font-family="Arial" font-size="10" fill="white" font-weight="bold">抓拍中</text><text x="205" y="80" text-anchor="middle" font-family="Arial" font-size="9" fill="#B3E5FC">Capturing</text>
<line x1="260" y1="66" x2="288" y2="66" stroke="#546E7A" stroke-width="2" marker-end="url(#ca)"/>
<text x="274" y="58" text-anchor="middle" font-family="Arial" font-size="8" fill="#888">图像就绪</text>
<rect x="290" y="40" width="110" height="52" rx="6" fill="#F57C00"/><text x="345" y="63" text-anchor="middle" font-family="Arial" font-size="10" fill="white" font-weight="bold">推理中</text><text x="345" y="80" text-anchor="middle" font-family="Arial" font-size="9" fill="#FFE0B2">Processing</text>
<line x1="400" y1="66" x2="428" y2="66" stroke="#546E7A" stroke-width="2" marker-end="url(#ca)"/>
<text x="414" y="58" text-anchor="middle" font-family="Arial" font-size="8" fill="#888">OCR完成</text>
<rect x="430" y="40" width="110" height="52" rx="6" fill="#2E7D32"/><text x="485" y="63" text-anchor="middle" font-family="Arial" font-size="10" fill="white" font-weight="bold">识别完成</text><text x="485" y="80" text-anchor="middle" font-family="Arial" font-size="9" fill="#C8E6C9">Done</text>
<line x1="540" y1="66" x2="568" y2="66" stroke="#546E7A" stroke-width="2" marker-end="url(#ca)"/>
<text x="554" y="58" text-anchor="middle" font-family="Arial" font-size="8" fill="#888">异常</text>
<rect x="570" y="40" width="100" height="52" rx="6" fill="#C62828"/><text x="620" y="63" text-anchor="middle" font-family="Arial" font-size="10" fill="white" font-weight="bold">错误</text><text x="620" y="80" text-anchor="middle" font-family="Arial" font-size="9" fill="#FFCDD2">Error</text>
<text x="340" y="124" text-anchor="middle" font-family="Arial" font-size="9" fill="#888">* 错误状态可点击重新触发；Done 状态可手动覆盖数值后再次识别</text>
</svg>`;

const exportFlowSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="680" height="140" viewBox="0 0 680 140">
<defs><marker id="ea" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#546E7A"/></marker></defs>
<rect width="680" height="140" fill="#FAFAFA" rx="4"/>
<rect x="10"  y="40" width="140" height="52" rx="6" fill="#1565C0"/><text x="80"  y="63" text-anchor="middle" font-family="Arial" font-size="10" fill="white" font-weight="bold">打开实验页面</text><text x="80"  y="80" text-anchor="middle" font-family="Arial" font-size="9" fill="#BBDEFB">已有识别结果</text>
<line x1="150" y1="66" x2="178" y2="66" stroke="#546E7A" stroke-width="2" marker-end="url(#ea)"/>
<rect x="180" y="40" width="140" height="52" rx="6" fill="#1976D2"/><text x="250" y="63" text-anchor="middle" font-family="Arial" font-size="10" fill="white" font-weight="bold">点击"导出报表"</text><text x="250" y="80" text-anchor="middle" font-family="Arial" font-size="9" fill="#BBDEFB">右上角 ↑ 按钮</text>
<line x1="320" y1="66" x2="348" y2="66" stroke="#546E7A" stroke-width="2" marker-end="url(#ea)"/>
<rect x="350" y="40" width="140" height="52" rx="6" fill="#388E3C"/><text x="420" y="63" text-anchor="middle" font-family="Arial" font-size="10" fill="white" font-weight="bold">后端生成 xlsx</text><text x="420" y="80" text-anchor="middle" font-family="Arial" font-size="9" fill="#C8E6C9">按实验类型套模板</text>
<line x1="490" y1="66" x2="518" y2="66" stroke="#546E7A" stroke-width="2" marker-end="url(#ea)"/>
<rect x="520" y="40" width="150" height="52" rx="6" fill="#37474F"/><text x="595" y="63" text-anchor="middle" font-family="Arial" font-size="10" fill="white" font-weight="bold">浏览器自动下载</text><text x="595" y="80" text-anchor="middle" font-family="Arial" font-size="9" fill="#B0BEC5">experiment_N.xlsx</text>
<text x="340" y="124" text-anchor="middle" font-family="Arial" font-size="9" fill="#888">* 导出无需额外操作，直接下载；文件名格式为 experiment_{实验ID}.xlsx</text>
</svg>`;

const templateStructSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="680" height="240" viewBox="0 0 680 240">
<rect width="680" height="240" fill="#FAFAFA" rx="4"/>
<text x="340" y="22" text-anchor="middle" font-family="Arial" font-size="12" font-weight="bold" fill="#333">Prompt Template 数据结构</text>
<rect x="20" y="36" width="640" height="42" rx="4" fill="#E3F2FD" stroke="#1565C0" stroke-width="1"/>
<text x="40" y="53" font-family="Courier New" font-size="10" fill="#1565C0" font-weight="bold">instrument_type</text>
<text x="40" y="70" font-family="Arial" font-size="9" fill="#555">仪表唯一标识（如 "D0"），与相机映射和实验配置关联</text>
<text x="340" y="53" font-family="Courier New" font-size="10" fill="#1565C0" font-weight="bold">display_name</text>
<text x="340" y="70" font-family="Arial" font-size="9" fill="#555">前端显示名称（如 "超级昆美搅拌器"）</text>
<rect x="20" y="84" width="640" height="42" rx="4" fill="#E8F5E9" stroke="#2E7D32" stroke-width="1"/>
<text x="40" y="101" font-family="Courier New" font-size="10" fill="#2E7D32" font-weight="bold">keywords [ ]</text>
<text x="40" y="118" font-family="Arial" font-size="9" fill="#555">识别关键词列表，辅助 YOLO 后分类（如 ["mixer", "control", "昆美"]）</text>
<text x="340" y="101" font-family="Courier New" font-size="10" fill="#2E7D32" font-weight="bold">description</text>
<text x="340" y="118" font-family="Arial" font-size="9" fill="#555">仪表功能说明，注入 Prompt 上下文</text>
<rect x="20" y="132" width="640" height="95" rx="4" fill="#FFF3E0" stroke="#E65100" stroke-width="1"/>
<text x="40" y="150" font-family="Courier New" font-size="10" fill="#E65100" font-weight="bold">fields [ ] — 识别字段数组（每项）：</text>
<rect x="40" y="158" width="140" height="24" rx="3" fill="#F57C00"/><text x="110" y="175" text-anchor="middle" font-family="Courier New" font-size="9" fill="white">key</text>
<text x="188" y="175" font-family="Arial" font-size="9" fill="#555">字段唯一键，写入数据库（如 "current_speed"）</text>
<rect x="40" y="188" width="140" height="24" rx="3" fill="#F57C00"/><text x="110" y="205" text-anchor="middle" font-family="Courier New" font-size="9" fill="white">label / unit</text>
<text x="188" y="205" font-family="Arial" font-size="9" fill="#555">前端展示标签和单位（如 "当前转速" / "rpm"）</text>
<rect x="420" y="158" width="140" height="24" rx="3" fill="#BF360C"/><text x="490" y="175" text-anchor="middle" font-family="Courier New" font-size="9" fill="white">type</text>
<text x="568" y="175" font-family="Arial" font-size="9" fill="#555">数值类型：Float / String</text>
<rect x="420" y="188" width="140" height="24" rx="3" fill="#BF360C"/><text x="490" y="205" text-anchor="middle" font-family="Courier New" font-size="9" fill="white">prompt_hint</text>
<text x="568" y="205" font-family="Arial" font-size="9" fill="#555">注入 Prompt 的提示文字</text>
</svg>`;

const imapSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="680" height="280" viewBox="0 0 680 280">
<rect width="680" height="280" fill="#FAFAFA" rx="4"/>
<text x="340" y="24" text-anchor="middle" font-family="Arial" font-size="12" font-weight="bold" fill="#333">仪表 D0-D8 相机通道映射关系</text>
<rect x="10" y="36" width="100" height="30" rx="4" fill="#37474F"/><text x="60" y="56" text-anchor="middle" font-family="Arial" font-size="10" font-weight="bold" fill="white">相机 F0</text>
<rect x="150" y="36" width="100" height="30" rx="4" fill="#37474F"/><text x="200" y="56" text-anchor="middle" font-family="Arial" font-size="10" font-weight="bold" fill="white">相机 F3</text>
<rect x="290" y="36" width="100" height="30" rx="4" fill="#37474F"/><text x="340" y="56" text-anchor="middle" font-family="Arial" font-size="10" font-weight="bold" fill="white">相机 F5</text>
<rect x="430" y="36" width="100" height="30" rx="4" fill="#37474F"/><text x="480" y="56" text-anchor="middle" font-family="Arial" font-size="10" font-weight="bold" fill="white">相机 F7</text>
<rect x="570" y="36" width="100" height="30" rx="4" fill="#37474F"/><text x="620" y="56" text-anchor="middle" font-family="Arial" font-size="10" font-weight="bold" fill="white">相机 F8</text>
<line x1="60"  y1="66" x2="60"  y2="88" stroke="#546E7A" stroke-width="1.5"/>
<line x1="200" y1="66" x2="200" y2="88" stroke="#546E7A" stroke-width="1.5"/>
<line x1="340" y1="66" x2="340" y2="88" stroke="#546E7A" stroke-width="1.5"/>
<line x1="480" y1="66" x2="480" y2="88" stroke="#546E7A" stroke-width="1.5"/>
<line x1="620" y1="66" x2="620" y2="88" stroke="#546E7A" stroke-width="1.5"/>
<rect x="10"  y="90" width="100" height="44" rx="4" fill="#1565C0"/><text x="60"  y="109" text-anchor="middle" font-family="Arial" font-size="10" fill="white" font-weight="bold">D0</text><text x="60"  y="124" text-anchor="middle" font-family="Arial" font-size="9" fill="#BBDEFB">混调器</text>
<rect x="120" y="90" width="100" height="44" rx="4" fill="#1565C0"/><text x="170" y="109" text-anchor="middle" font-family="Arial" font-size="10" fill="white" font-weight="bold">D1</text><text x="170" y="124" text-anchor="middle" font-family="Arial" font-size="9" fill="#BBDEFB">电子天平1</text>
<line x1="200" y1="66" x2="170" y2="90" stroke="#546E7A" stroke-width="1" stroke-dasharray="3,2"/>
<rect x="230" y="90" width="100" height="44" rx="4" fill="#1565C0"/><text x="280" y="109" text-anchor="middle" font-family="Arial" font-size="10" fill="white" font-weight="bold">D2</text><text x="280" y="124" text-anchor="middle" font-family="Arial" font-size="9" fill="#BBDEFB">电子天平2</text>
<line x1="200" y1="66" x2="280" y2="90" stroke="#546E7A" stroke-width="1" stroke-dasharray="3,2"/>
<rect x="340" y="90" width="100" height="44" rx="4" fill="#00695C"/><text x="390" y="109" text-anchor="middle" font-family="Arial" font-size="10" fill="white" font-weight="bold">D3</text><text x="390" y="124" text-anchor="middle" font-family="Arial" font-size="9" fill="#B2DFDB">台式pH计</text>
<line x1="340" y1="66" x2="390" y2="90" stroke="#546E7A" stroke-width="1" stroke-dasharray="3,2"/>
<rect x="460" y="90" width="100" height="44" rx="4" fill="#00695C"/><text x="510" y="109" text-anchor="middle" font-family="Arial" font-size="10" fill="white" font-weight="bold">D4</text><text x="510" y="124" text-anchor="middle" font-family="Arial" font-size="9" fill="#B2DFDB">水质检测仪</text>
<line x1="340" y1="66" x2="510" y2="90" stroke="#546E7A" stroke-width="1" stroke-dasharray="3,2"/>
<rect x="580" y="90" width="90" height="44" rx="4" fill="#E65100"/><text x="625" y="109" text-anchor="middle" font-family="Arial" font-size="10" fill="white" font-weight="bold">D5</text><text x="625" y="124" text-anchor="middle" font-family="Arial" font-size="9" fill="#FFCCBC">界面张力仪</text>
<rect x="120" y="158" width="100" height="44" rx="4" fill="#6A1B9A"/><text x="170" y="177" text-anchor="middle" font-family="Arial" font-size="10" fill="white" font-weight="bold">D6</text><text x="170" y="192" text-anchor="middle" font-family="Arial" font-size="9" fill="#E1BEE7">扭矩搅拌器</text><text x="170" y="210" text-anchor="middle" font-family="Arial" font-size="8" fill="#777">← F7</text>
<rect x="260" y="158" width="100" height="44" rx="4" fill="#6A1B9A"/><text x="310" y="177" text-anchor="middle" font-family="Arial" font-size="10" fill="white" font-weight="bold">D7</text><text x="310" y="192" text-anchor="middle" font-family="Arial" font-size="9" fill="#E1BEE7">水浴锅</text><text x="310" y="210" text-anchor="middle" font-family="Arial" font-size="8" fill="#777">← F7</text>
<rect x="400" y="158" width="100" height="44" rx="4" fill="#37474F"/><text x="450" y="177" text-anchor="middle" font-family="Arial" font-size="10" fill="white" font-weight="bold">D8</text><text x="450" y="192" text-anchor="middle" font-family="Arial" font-size="9" fill="#CFD8DC">旋转粘度计</text><text x="450" y="210" text-anchor="middle" font-family="Arial" font-size="8" fill="#777">← F8</text>
<text x="340" y="258" text-anchor="middle" font-family="Arial" font-size="9" fill="#888">* D1/D2 共用 F3；D3/D4 共用 F5（分区域拍摄）；D6/D7 共用 F7</text>
</svg>`;

module.exports = { archSvg, startupSvg, pipelineSvg, cardStateSvg, exportFlowSvg, templateStructSvg, imapSvg, pngBufs, sharp };
