/**
 * build_resume.js
 *
 * Generic resume builder for the resume-tailor skill.
 * Reads a JSON spec (see references/resume_schema.md) and writes:
 *   - <out>.docx   formatted resume, JD-aligned text highlighted yellow
 *   - <out>.txt    plain-text version (no highlight marks), Google-Docs/ATS-paste friendly
 *
 * Usage: node build_resume.js path/to/resume_data.json path/to/output_basename
 * (writes output_basename.docx and output_basename.txt)
 */

const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, AlignmentType,
  BorderStyle, LevelFormat, convertInchesToTwip,
  PositionalTab, PositionalTabAlignment, PositionalTabLeader,
} = require("docx");

const [, , specPath, outBase] = process.argv;
if (!specPath || !outBase) {
  console.error("Usage: node build_resume.js resume_data.json output_basename");
  process.exit(1);
}

const data = JSON.parse(fs.readFileSync(specPath, "utf8"));

const NAVY = "1F3864";
const GRAY = "555555";
const LINE = "1F3864";
const HL = "yellow";

const bulletNumbering = {
  config: [
    {
      reference: "bullet-list",
      levels: [
        {
          level: 0,
          format: LevelFormat.BULLET,
          text: "•",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: convertInchesToTwip(0.22), hanging: convertInchesToTwip(0.14) } } },
        },
      ],
    },
  ],
};

// ---------- helpers to turn run-arrays into docx TextRuns / plain text ----------
function toDocxRuns(parts, opts = {}) {
  return parts.map((p) => {
    if (typeof p === "string") p = { t: p };
    return new TextRun({
      text: p.t,
      size: opts.size || 20,
      font: "Calibri",
      bold: p.b || opts.bold || false,
      italics: p.i || false,
      highlight: p.hl ? HL : undefined,
      color: opts.color,
    });
  });
}
function toPlainText(parts) {
  return parts.map((p) => (typeof p === "string" ? p : p.t)).join("");
}

function sectionHeading(text) {
  return new Paragraph({
    spacing: { before: 260, after: 100 },
    border: { bottom: { color: LINE, space: 2, style: BorderStyle.SINGLE, size: 6 } },
    children: [new TextRun({ text: text.toUpperCase(), bold: true, color: NAVY, size: 21, font: "Calibri", characterSpacing: 10 })],
  });
}
function bulletPara(parts) {
  return new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, spacing: { after: 60 }, children: toDocxRuns(parts) });
}
function skillLine(label, parts) {
  return new Paragraph({
    spacing: { after: 40 },
    children: [new TextRun({ text: label + ":  ", bold: true, size: 20, font: "Calibri" }), ...toDocxRuns(parts)],
  });
}
function jobHeader(title, org, dates) {
  return new Paragraph({
    spacing: { before: 140, after: 20 },
    tabStops: [{ type: "right", position: convertInchesToTwip(6.5) }],
    children: [
      new TextRun({ text: title, bold: true, size: 21, font: "Calibri", color: "1A1A1A" }),
      new TextRun({ text: `  |  ${org}`, size: 21, font: "Calibri", color: "1A1A1A" }),
      new TextRun({ children: [new PositionalTab({ alignment: PositionalTabAlignment.RIGHT, leader: PositionalTabLeader.NONE, relativeTo: "margin" })] }),
      new TextRun({ text: dates, italics: true, size: 19, font: "Calibri", color: GRAY }),
    ],
  });
}

// ---------- build docx ----------
const children = [];
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 20 }, children: [new TextRun({ text: data.name.toUpperCase(), bold: true, size: 40, font: "Calibri", color: NAVY, characterSpacing: 20 })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 10 }, children: [new TextRun({ text: data.title, size: 21, font: "Calibri", color: GRAY, italics: true })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160 }, children: [new TextRun({ text: data.contact, size: 18, font: "Calibri", color: GRAY })] }));

children.push(sectionHeading("Professional Summary"));
children.push(new Paragraph({ spacing: { after: 100 }, children: toDocxRuns(data.summary) }));

children.push(sectionHeading("Core Skills"));
for (const s of data.skills) children.push(skillLine(s.label, s.runs));

children.push(sectionHeading("Experience"));
for (const job of data.experience) {
  children.push(jobHeader(job.title, job.org, job.dates));
  for (const b of job.bullets) children.push(bulletPara(b));
}

if (data.projects && data.projects.length) {
  for (const proj of data.projects) {
    children.push(sectionHeading(proj.heading));
    for (const b of proj.bullets) children.push(bulletPara(b));
  }
}

children.push(sectionHeading("Education"));
for (const ed of data.education) {
  children.push(new Paragraph({
    spacing: { after: 10 },
    tabStops: [{ type: "right", position: convertInchesToTwip(6.5) }],
    children: [
      new TextRun({ text: ed.degree, bold: true, size: 21, font: "Calibri" }),
      new TextRun({ children: [new PositionalTab({ alignment: PositionalTabAlignment.RIGHT, leader: PositionalTabLeader.NONE, relativeTo: "margin" })] }),
      new TextRun({ text: ed.dates, italics: true, size: 19, font: "Calibri", color: GRAY }),
    ],
  }));
  children.push(new Paragraph({ spacing: { after: 100 }, children: [new TextRun({ text: ed.school, size: 20, font: "Calibri", color: GRAY })] }));
}

const doc = new Document({
  numbering: bulletNumbering,
  styles: { default: { document: { run: { font: "Calibri", size: 21 } } } },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 620, bottom: 620, left: 720, right: 720 } } },
    children,
  }],
});

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync(`${outBase}.docx`, buffer);

  // ---------- build plain text version ----------
  let txt = "";
  txt += `${data.name.toUpperCase()}\n${data.title}\n${data.contact}\n\n`;
  txt += `PROFESSIONAL SUMMARY\n${toPlainText(data.summary)}\n\n`;
  txt += `CORE SKILLS\n`;
  for (const s of data.skills) txt += `${s.label}: ${toPlainText(s.runs)}\n`;
  txt += `\nEXPERIENCE\n`;
  for (const job of data.experience) {
    txt += `${job.title} | ${job.org} (${job.dates})\n`;
    for (const b of job.bullets) txt += `- ${toPlainText(b)}\n`;
    txt += `\n`;
  }
  if (data.projects && data.projects.length) {
    for (const proj of data.projects) {
      txt += `${proj.heading}\n`;
      for (const b of proj.bullets) txt += `- ${toPlainText(b)}\n`;
      txt += `\n`;
    }
  }
  txt += `EDUCATION\n`;
  for (const ed of data.education) txt += `${ed.degree} (${ed.dates}) - ${ed.school}\n`;

  fs.writeFileSync(`${outBase}.txt`, txt);
  console.log("done");
});