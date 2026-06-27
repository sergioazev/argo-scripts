const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, LevelFormat, WidthType, ShadingType, BorderStyle, VerticalAlign
} = require("docx");

const GREY = "777777";
const GREEN_HEADER = "C6E0C6";
const GREEN_TOTAL = "DCEEDC";
const GREY_BG = "F2F2F2";
const border = { style: BorderStyle.SINGLE, size: 2, color: "BFBFBF" };
const borders = { top: border, bottom: border, left: border, right: border };
const fmt = (n) => "R$ " + n.toLocaleString("pt-BR", { minimumFractionDigits: 2 });

// content width: A4 (11906) - left 1800 - right 1800 = 8306 DXA
const TABLE_W = 8306;
const COLS = [3506, 900, 700, 1100, 1100]; // sum = 7306... fix below
// recompute to sum exactly to TABLE_W
const colsSum = COLS.reduce((a,b)=>a+b,0);
COLS[0] += (TABLE_W - colsSum);

function cell(text, opts = {}) {
  const { bold = false, italic = false, color = null, fill = null, align = AlignmentType.LEFT, width } = opts;
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: fill ? { fill, type: ShadingType.CLEAR } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({
      alignment: align,
      children: [new TextRun({ text, bold, italics: italic, color: color || undefined })]
    })]
  });
}

function headerRow() {
  const heads = ["Descrição", "Unidade", "Qtd", "Valor (R$)", "Total (R$)"];
  return new TableRow({
    children: heads.map((h, i) => cell(h, { bold: true, fill: GREEN_HEADER, width: COLS[i], align: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER }))
  });
}

function sectionRow(label) {
  return new TableRow({
    children: [0,1,2,3,4].map(i => cell(i === 0 ? label : "", { bold: true, fill: GREY_BG, width: COLS[i] }))
  });
}

function itemRow(desc, unit, qty, rate) {
  const total = qty * rate;
  return new TableRow({
    children: [
      cell(desc, { width: COLS[0] }),
      cell(unit, { width: COLS[1], align: AlignmentType.CENTER }),
      cell(String(qty), { width: COLS[2], align: AlignmentType.CENTER }),
      cell(fmt(rate), { width: COLS[3], align: AlignmentType.RIGHT }),
      cell(fmt(total), { width: COLS[4], align: AlignmentType.RIGHT }),
    ]
  });
}

function subtotalRow(label, value) {
  return new TableRow({
    children: [
      cell(label, { bold: true, fill: GREEN_TOTAL, width: COLS[0] }),
      cell("", { fill: GREEN_TOTAL, width: COLS[1] }),
      cell("", { fill: GREEN_TOTAL, width: COLS[2] }),
      cell("", { fill: GREEN_TOTAL, width: COLS[3] }),
      cell(fmt(value), { bold: true, fill: GREEN_TOTAL, width: COLS[4], align: AlignmentType.RIGHT }),
    ]
  });
}

// --- data (mirrors tabela-precos-pos-producao-imagem.xlsx) ---
const conform = [
  ["Data Transfer — mover selects para sistema de grade", "Hora", 4, 120],
  ["Resolve Conform — conform de dados, pre-grade resize & dissolves, sync check", "Hora", 8, 180],
  ["Confidence Quicktime — HD Quicktime para Audio Guide/Off-Line check", "Cada", 1, 300],
];
const gfx = [
  ["Abertura/Créditos — texto simples sobre preto/imagem", "Hora", 8, 180],
  ["Créditos finais (roller) — a partir de documento pré-formatado", "Hora", 6, 150],
  ["VFX Plate Export — sequência 4K OpenEXR, base 50 planos", "Cada", 50, 25],
];
const grade = [
  ["Online — integração de VFX, GFX e cartelas de abertura/encerramento", "Dia", 1, 1800],
  ["Color Grade HDR10 — runtime 120 min", "Dia", 12, 2200],
  ["SDR Trim Pass", "Dia", 4, 1500],
];
const deliv = [
  ["Master 4K HDR10 Scope/Flat DPX RGB 16bits — por 10 min de runtime", "Cada", 12, 120],
  ["Master 4K HDR10 Scope/Flat ProRes 4444 — por 10 min de runtime", "Cada", 12, 60],
  ["Master 4K SDR Scope/Flat DPX RGB 16bits — por 10 min de runtime", "Cada", 12, 120],
  ["Master 4K SDR Scope/Flat ProRes 4444 — por 10 min de runtime", "Cada", 12, 60],
  ["DCP", "Cada", 1, 2500],
  ["VDM QC", "Cada", 4, 350],
];

const sum = (rows) => rows.reduce((a, r) => a + r[2] * r[3], 0);
const totalConform = sum(conform), totalGfx = sum(gfx), totalGrade = sum(grade), totalDeliv = sum(deliv);
const grandTotal = totalConform + totalGfx + totalGrade + totalDeliv;

const rows = [
  headerRow(),
  sectionRow("CONFORM"),
  ...conform.map(r => itemRow(...r)),
  subtotalRow("Subtotal Conform", totalConform),
  sectionRow("GFX"),
  ...gfx.map(r => itemRow(...r)),
  subtotalRow("Subtotal GFX", totalGfx),
  sectionRow("GRADE & FINALIZAÇÃO"),
  ...grade.map(r => itemRow(...r)),
  subtotalRow("Subtotal Grade & Finalização", totalGrade),
  sectionRow("DELIVERABLES"),
  ...deliv.map(r => itemRow(...r)),
  subtotalRow("Subtotal Deliverables", totalDeliv),
];

const table = new Table({
  width: { size: TABLE_W, type: WidthType.DXA },
  columnWidths: COLS,
  rows,
});

function p(text, opts = {}) {
  const { bold = false, italic = false, color = null, sizeAfter = 160, align = AlignmentType.LEFT, sz = null } = opts;
  return new Paragraph({
    alignment: align,
    spacing: { after: sizeAfter },
    children: [new TextRun({ text, bold, italics: italic, color: color || undefined, size: sz || undefined })]
  });
}

function labelValue(label, value, opts = {}) {
  return new Paragraph({
    alignment: opts.align || AlignmentType.LEFT,
    spacing: { after: opts.sizeAfter || 80 },
    children: [
      new TextRun({ text: label, bold: true }),
      new TextRun({ text: " " + value, italics: true, color: GREY })
    ]
  });
}

function bullet(text) {
  return new Paragraph({
    spacing: { after: 80 },
    indent: { left: 360 },
    children: [
      new TextRun({ text: "• " }),
      new TextRun({ text, italics: true, color: GREY })
    ]
  });
}

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Cambria" } } }
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1440, right: 1800, bottom: 1440, left: 1800, header: 720, footer: 720 }
      }
    },
    children: [
      new Paragraph({
        spacing: { after: 400 },
        children: [new TextRun({ text: "TABELA DE REFERÊNCIA — PÓS-PRODUÇÃO DE IMAGEM", bold: true, allCaps: true, size: 50, characterSpacing: 80 })]
      }),
      labelValue("ESCOPO:", "Conform, GFX, grade e finalização, deliverables — base Alexa 4K ProRes 4444 XQ 24fps, runtime 120 min, masters SDR e HDR10"),
      labelValue("NÃO INCLUI:", "montagem (edição) nem som — apenas a fase de finalização de imagem"),
      new Paragraph({ spacing: { after: 80 }, children: [] }),
      p("Brasília, 17 de junho de 2026", { italic: true, color: GREY, align: AlignmentType.RIGHT, sizeAfter: 320 }),
      p("Tabela de referência interna da Argonautas — não é orçamento fechado de projeto. Ajustar Dia/Hora/Qtd ao runtime e escopo real antes de enviar proposta a cliente.", { italic: true, color: GREY, sizeAfter: 240 }),
      table,
      new Paragraph({ spacing: { after: 0 } }),
      new Paragraph({
        border: { top: { style: BorderStyle.SINGLE, size: 4, color: "1A1A1A", space: 4 }, bottom: { style: BorderStyle.SINGLE, size: 4, color: "1A1A1A", space: 4 } },
        spacing: { before: 160, after: 160 },
        children: [
          new TextRun({ text: "TOTAL PÓS-PRODUÇÃO DE IMAGEM  ", bold: true, size: 24 }),
          new TextRun({ text: fmt(grandTotal), bold: true, size: 24 })
        ]
      }),
      new Paragraph({ spacing: { after: 320 } }),
      new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: "Obs:", bold: true })] }),
      bullet("Patamar reajustado acima da prática atual da Argonautas, calibrado para mercado/cliente brasileiro — não é benchmark internacional."),
      bullet("Referência de mercado: orçamento de finishing house de Londres para escopo equivalente converte para ≈ R$ 196.937,50 (GBP 28.750 × 6,85, jun/2026) — esta tabela fica deliberadamente entre 1/4 e 1/3 desse valor."),
      bullet("Não inclui montagem (edição), desenho de som/mixagem, nem coordenação geral de projeto — ver orçamento completo para esses itens."),
      bullet("Ver planilha “tabela-precos-pos-producao-imagem.xlsx” para versão calculável (ajuste de Qtd/Dia recalcula o total automaticamente)."),
      new Paragraph({ spacing: { after: 560 } }),
      p("Atenciosamente,", { sizeAfter: 0 }),
      new Paragraph({ spacing: { after: 0 } }),
      new Paragraph({ spacing: { after: 0 } }),
      new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: "Sergio Azevedo", bold: true })] }),
      new Paragraph({ spacing: { after: 40 }, children: [new TextRun({ text: "Sócio administrador — Argonautas" })] }),
      new Paragraph({ spacing: { after: 40 }, children: [new TextRun({ text: "sergio@argonautas.tv" })] }),
      new Paragraph({ spacing: { after: 0 }, children: [new TextRun({ text: "Tel. 55 61 9 9968 4624" })] }),
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("/sessions/youthful-affectionate-galileo/mnt/outputs/tabela-precos-pos-producao-imagem.docx", buffer);
  console.log("saved");
});
