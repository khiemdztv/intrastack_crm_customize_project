const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  HeadingLevel, AlignmentType, BorderStyle, WidthType, ShadingType,
  LevelFormat, PageNumber, PageBreak, VerticalAlign
} = require('docx');
const fs = require('fs');

// ── helpers ──────────────────────────────────────────────────────────────────
const CONTENT_W = 9360; // US Letter 1-inch margins

const cellBorder = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const cellBorders = { top: cellBorder, bottom: cellBorder, left: cellBorder, right: cellBorder };

const headBorder = { style: BorderStyle.SINGLE, size: 1, color: "1A3C6E" };
const headBorders = { top: headBorder, bottom: headBorder, left: headBorder, right: headBorder };

const COLORS = {
  navy:  "1A3C6E",
  teal:  "0D7377",
  green: "217346",
  amber: "C07000",
  red:   "C0392B",
  gray:  "666666",
  lightBlue: "EBF3FA",
  lightGreen: "EAF4EC",
  lightAmber: "FFF3CD",
  lightRed:   "FDECEA",
  headerRow:  "1A3C6E",
  altRow:     "F5F8FC",
};

function p(text, opts = {}) {
  return new Paragraph({
    spacing: { after: opts.spaceAfter ?? 100 },
    alignment: opts.align,
    border: opts.border,
    children: [new TextRun({
      text,
      bold:    opts.bold    ?? false,
      italics: opts.italic  ?? false,
      size:    opts.size    ?? 22,
      color:   opts.color   ?? "000000",
      font:    "Arial",
    })]
  });
}

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 160 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: COLORS.navy, space: 4 } },
    children: [new TextRun({ text, bold: true, size: 30, color: COLORS.navy, font: "Arial" })]
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 240, after: 120 },
    children: [new TextRun({ text, bold: true, size: 26, color: COLORS.teal, font: "Arial" })]
  });
}

function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 180, after: 80 },
    children: [new TextRun({ text, bold: true, size: 22, color: COLORS.navy, font: "Arial" })]
  });
}

function bullet(text, bold = false) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { after: 80 },
    children: [new TextRun({ text, bold, size: 22, font: "Arial" })]
  });
}

function gap(n = 1) {
  return Array.from({ length: n }, () => new Paragraph({ spacing: { after: 80 }, children: [] }));
}

function pageBreak() {
  return new Paragraph({ children: [new PageBreak()] });
}

// status badge colours
const statusColor = {
  "Done":        { fill: COLORS.lightGreen, text: COLORS.green },
  "In Progress": { fill: COLORS.lightBlue,  text: COLORS.navy  },
  "Pending":     { fill: COLORS.lightAmber, text: COLORS.amber },
  "Critical":    { fill: COLORS.lightRed,   text: COLORS.red   },
};

function makeTable(headers, rows, colWidths) {
  const total = colWidths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [
      // header row
      new TableRow({
        tableHeader: true,
        children: headers.map((h, i) => new TableCell({
          borders: headBorders,
          width: { size: colWidths[i], type: WidthType.DXA },
          shading: { fill: COLORS.headerRow, type: ShadingType.CLEAR },
          margins: { top: 100, bottom: 100, left: 140, right: 140 },
          verticalAlign: VerticalAlign.CENTER,
          children: [new Paragraph({
            children: [new TextRun({ text: h, bold: true, size: 20, color: "FFFFFF", font: "Arial" })]
          })]
        }))
      }),
      // data rows
      ...rows.map((row, ri) => new TableRow({
        children: row.map((cell, ci) => {
          const sc = statusColor[cell] ?? null;
          const fill = sc ? sc.fill : (ri % 2 === 0 ? COLORS.altRow : "FFFFFF");
          const textColor = sc ? sc.text : "000000";
          return new TableCell({
            borders: cellBorders,
            width: { size: colWidths[ci], type: WidthType.DXA },
            shading: { fill, type: ShadingType.CLEAR },
            margins: { top: 80, bottom: 80, left: 140, right: 140 },
            verticalAlign: VerticalAlign.CENTER,
            children: [new Paragraph({
              children: [new TextRun({
                text: cell,
                bold: !!sc,
                size: 20,
                color: textColor,
                font: "Arial"
              })]
            })]
          });
        })
      }))
    ]
  });
}

function infoBox(lines, fill, borderColor) {
  return lines.map((line, i) => new Paragraph({
    spacing: { after: i === lines.length - 1 ? 120 : 60 },
    shading: { fill, type: ShadingType.CLEAR },
    indent: { left: 280, right: 280 },
    border: i === 0 ? { top: { style: BorderStyle.SINGLE, size: 8, color: borderColor } } :
            i === lines.length - 1 ? { bottom: { style: BorderStyle.SINGLE, size: 8, color: borderColor } } : {},
    children: [new TextRun({ text: line, size: 20, font: "Arial", color: "333333" })]
  }));
}

// ── document ─────────────────────────────────────────────────────────────────
const doc = new Document({
  numbering: {
    config: [
      { reference: "bullets", levels: [{
          level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } }
      }]},
      { reference: "numbers", levels: [{
          level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } }
      }]},
      { reference: "subbullets", levels: [{
          level: 0, format: LevelFormat.BULLET, text: "-", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 1080, hanging: 360 } } }
      }]},
    ]
  },
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 30, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 360, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 22, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 180, after: 80 }, outlineLevel: 2 } },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    children: [

      // ── COVER ──────────────────────────────────────────────────────────────
      ...gap(2),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 80 },
        children: [new TextRun({ text: "INTRASTACK SOLUTIONS", size: 20, color: COLORS.gray, font: "Arial", bold: true, allCaps: true })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 120 },
        children: [new TextRun({ text: "Odoo CRM Platform", size: 52, bold: true, color: COLORS.navy, font: "Arial" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 80 },
        children: [new TextRun({ text: "Project Execution Plan & Task Assignment", size: 28, color: COLORS.teal, font: "Arial" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 60 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: COLORS.teal } },
        children: []
      }),
      ...gap(1),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 60 },
        children: [new TextRun({ text: "Version 1.0  |  Draft — Pending Review", size: 20, color: COLORS.gray, italics: true, font: "Arial" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 60 },
        children: [new TextRun({ text: "Prepared by: Steve (Gia Khiem Do)  |  Tech Lead", size: 20, font: "Arial" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 60 },
        children: [new TextRun({ text: "Target Go-Live: ~2 months from kickoff", size: 20, font: "Arial" })]
      }),
      ...gap(2),

      makeTable(
        ["Item", "Detail"],
        [
          ["Platform",      "Odoo 17 Community Edition"],
          ["Domain",        "crm.intrastack.com"],
          ["Server IP",     "163.245.212.92"],
          ["Deployment",    "Docker (odoo:17 + postgres:15)"],
          ["Tech Lead",     "Steve / Khiem (@khiemdztv)"],
          ["Co-Lead",       "Arian (Asia timezone coverage)"],
          ["Developer",     "Rishit"],
          ["Project Manager", "Auspicious Munemo"],
          ["BA / PM Guide", "Luan Nguyen"],
          ["Deadline",      "3 months from project start"],
        ],
        [3000, 6360]
      ),

      pageBreak(),

      // ── 1. SETUP STATUS ───────────────────────────────────────────────────
      h1("1. Pre-Kickoff Setup — Completed"),
      p("The following infrastructure tasks have been completed before the official kickoff. These items are confirmed done and require no further action."),
      ...gap(1),
      makeTable(
        ["#", "Task", "Owner", "Status"],
        [
          ["1", "Odoo 17 Community running via Docker on VPS", "Stefan / Steve", "Done"],
          ["2", "Nginx configured for crm.intrastack.com", "Steve", "Done"],
          ["3", "DNS A record created: crm.intrastack.com → 163.245.212.92", "Victoria", "Done"],
          ["4", "All core Odoo modules activated", "Steve", "Done"],
          ["5", "All team members invited and access granted", "Steve", "Done"],
          ["6", "SSL certificate (HTTPS) via Certbot", "Steve", "In Progress"],
        ],
        [400, 4800, 2200, 1960]
      ),
      ...gap(1),
      ...infoBox([
        "  NOTE: SSL (HTTPS) setup is pending DNS propagation confirmation. Steve will run",
        "  certbot --nginx -d crm.intrastack.com once DNS is fully active."
      ], COLORS.lightBlue, COLORS.navy),

      ...gap(2),

      // ── 2. PROJECT STRUCTURE ─────────────────────────────────────────────
      h1("2. Project Structure & Team Roles"),
      p("This project follows the IntraStack CRM Platform document (v1.0) across 3 phases. The team of 3 engineers plus PM/BA support targets full Phase 1 completion and Phase 2 initiation within the 3-month window."),
      ...gap(1),
      makeTable(
        ["Member", "Role", "Primary Responsibilities", "Availability"],
        [
          ["Steve (Khiem)", "Tech Lead", "4 CRM pipelines, automation rules, Sales quote engine, CEO dashboard, overall config ownership", "Full-time on project"],
          ["Arian", "Co-Lead / Dev", "Contacts + tagging strategy, Project & Delivery module, Asia timezone async coverage", "Full-time on project"],
          ["Rishit", "Developer", "Custom fields configuration, Timesheets + Employee module, technical support tasks", "Full-time on project"],
          ["Auspicious Munemo", "Project Manager", "Sprint tracking, meeting coordination, progress reporting to Stefan & Luan", "Part-time oversight"],
          ["Luan Nguyen", "BA / PM (Backend)", "Requirements review, acceptance criteria, final sign-off on deliverables", "On-demand review"],
          ["Stefan Nguyen", "Sponsor / Owner", "Final approval, resource decisions, escalation point", "Weekly review"],
        ],
        [1600, 1600, 4400, 1760]
      ),

      pageBreak(),

      // ── 3. PHASE 1 ────────────────────────────────────────────────────────
      h1("3. Phase 1 — Foundation (Month 1 to Month 3)"),
      p("Phase 1 covers all no-code Odoo configuration as defined in the IntraStack CRM Platform document, Slide 13. This phase must be fully complete before Phase 2 begins."),
      ...gap(1),

      // 3.1 CRM Pipelines
      h2("3.1 CRM Pipeline Design (Slide 04)"),
      p("Create 4 independent Sales Team pipelines in Odoo CRM. Each pipeline is a separate Sales Team with its own Kanban stages. This is the foundation of the entire platform."),
      ...gap(1),
      makeTable(
        ["Pipeline", "Sales Team Name", "Stages", "Description", "Owner", "Week"],
        [
          ["P1", "Staffing", "8", "New Requirement → Sourcing → Submitted → Interviews → Offer → Closed Won → Active Billing → Renewal", "Steve", "1"],
          ["P2", "Consulting", "7", "Discovery → Qualification → Solution Design → Proposal → Negotiation → Closed Won → Delivery", "Steve", "1"],
          ["P3", "Subcontracting", "5", "Outreach → Vendor Qualification → Capability Review → Approved Vendor → Active Engagement", "Steve", "1"],
          ["P4", "Managed Services", "6", "Qualified Lead → Assessment → Proposal → Contract → Active Service → Renewal", "Steve", "1"],
        ],
        [500, 1600, 600, 3900, 800, 660]
      ),
      ...gap(1),
      h3("Steps to create each pipeline:"),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 80 },
        children: [new TextRun({ text: "Go to CRM → Configuration → Sales Teams → Create new team", size: 22, font: "Arial" })] }),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 80 },
        children: [new TextRun({ text: "Set team name (e.g. \"P1 — Staffing\"), assign team leader (Steve)", size: 22, font: "Arial" })] }),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 80 },
        children: [new TextRun({ text: "Go to CRM → Configuration → Stages → Create stages specific to that pipeline", size: 22, font: "Arial" })] }),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 80 },
        children: [new TextRun({ text: "Assign stages to the correct Sales Team only (uncheck other teams)", size: 22, font: "Arial" })] }),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 80 },
        children: [new TextRun({ text: "Test by creating a sample opportunity in each pipeline and moving it across stages", size: 22, font: "Arial" })] }),

      ...gap(2),

      // 3.2 Custom Fields
      h2("3.2 Custom Fields & CRM Configuration (Slide 05)"),
      p("Add the following custom fields to every CRM opportunity record. These are mandatory on every deal."),
      ...gap(1),
      makeTable(
        ["Field Name", "Field Type", "Options / Values", "Mandatory?", "Owner", "Week"],
        [
          ["Deal Classification", "Selection", "Staffing / Consulting / Subcontracting / Managed Services", "Yes", "Rishit", "1"],
          ["Service Category", "Selection", "Cloud / AI/ML / Cybersecurity / DevOps / Data Engineering / App Modernization", "Yes", "Rishit", "1"],
          ["Urgency Flag", "Selection", "Immediate (0-30 days) / Short-term (30-90 days) / Long-term (90+ days)", "Yes", "Rishit", "1"],
          ["Source Tracking", "Selection", "LinkedIn / MSP Outreach / Prime Contractor / Referral / Vendor Portal", "Yes", "Rishit", "1"],
          ["Expected Value ($)", "Monetary", "Free numeric input in USD", "Yes", "Rishit", "1"],
          ["Decision Maker Flag", "Boolean (Yes/No)", "Checkbox: Is contact the decision maker?", "Yes", "Rishit", "1"],
        ],
        [1800, 1200, 3200, 1000, 800, 660]
      ),
      ...gap(1),
      h3("Steps to add custom fields:"),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 80 },
        children: [new TextRun({ text: "Enable developer mode: Settings → Activate Developer Mode", size: 22, font: "Arial" })] }),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 80 },
        children: [new TextRun({ text: "Go to CRM → any opportunity → click gear icon → Add Custom Field", size: 22, font: "Arial" })] }),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 80 },
        children: [new TextRun({ text: "Set field type, label, and options for each field above", size: 22, font: "Arial" })] }),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 80 },
        children: [new TextRun({ text: "Mark fields as Required to enforce mandatory entry", size: 22, font: "Arial" })] }),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 80 },
        children: [new TextRun({ text: "Verify fields appear on all 4 pipeline opportunity forms", size: 22, font: "Arial" })] }),

      ...gap(2),

      // 3.3 Contacts
      h2("3.3 Contacts & Tagging Strategy (Slide 09)"),
      p("Configure the Contacts module to serve as the unified relationship database for all entity types. Every person or company in the system must be tagged accordingly."),
      ...gap(1),
      makeTable(
        ["Contact Type", "Description", "Required Tags"],
        [
          ["Client", "Direct buyers of staffing, consulting & managed services", "Staffing Buyer / Cybersecurity Client (as applicable)"],
          ["MSP Partner", "Managed Service Providers — subcontracting channel", "MSP Partner, Subcontracting Lead"],
          ["Prime Contractor", "Federal & enterprise primes for subcontracting deals", "Prime Contractor"],
          ["Candidate", "Active & bench engineers — 30+ talent pool", "Candidate, technology tags (AWS / Azure etc.)"],
          ["Vendor", "Technology & tools vendors used in delivery", "Vendor"],
          ["Recruiter Partner", "External recruiters for sourcing & placements", "Recruiter Partner"],
        ],
        [1600, 4000, 3760]
      ),
      ...gap(1),
      h3("Tags to create in Contacts → Configuration → Tags:"),
      bullet("AWS Partner"),
      bullet("Azure Partner"),
      bullet("Cybersecurity Client"),
      bullet("Staffing Buyer"),
      bullet("Subcontracting Lead"),
      bullet("MSP Partner"),
      bullet("Prime Contractor"),
      bullet("Candidate"),
      bullet("Vendor"),
      bullet("Recruiter Partner"),
      ...gap(1),
      p("Owner: Arian  |  Target: Week 1", true),

      pageBreak(),

      // 3.4 Automation
      h2("3.4 Automation Logic — Activities System (Slide 06)"),
      p("Odoo Community Edition has no advanced workflow automation. We use the Activities system as a replacement. The following 4 rules (R1-R4) must be configured as Automated Actions."),
      ...gap(1),
      makeTable(
        ["Rule", "Trigger", "Action", "Assigned To", "Owner", "Week"],
        [
          ["R1", "New Lead / Opportunity Created", "Create Activity: \"Qualify Lead within 24 hours\"", "Sales Lead (Steve)", "Steve", "2"],
          ["R2", "Stage changed to: New Requirement (P1)", "Create Activity: \"Submit 5 candidates in 48 hours\"", "Recruiter (Rishit)", "Steve", "2"],
          ["R3", "Stage changed to: Discovery (P2)", "Create Activity: \"Prepare discovery checklist + schedule call\"", "Account Exec (Arian)", "Steve", "2"],
          ["R4", "No activity logged for 5+ days", "Manual Task Alert: \"Re-engage prospect\"", "Pipeline Manager", "Steve", "2"],
        ],
        [500, 2400, 2800, 1800, 800, 660]
      ),
      ...gap(1),
      h3("Steps to configure automation rules:"),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 80 },
        children: [new TextRun({ text: "Go to Settings → Technical → Automated Actions (developer mode required)", size: 22, font: "Arial" })] }),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 80 },
        children: [new TextRun({ text: "Create new Automated Action: Model = CRM Lead/Opportunity", size: 22, font: "Arial" })] }),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 80 },
        children: [new TextRun({ text: "Set Trigger: Stage is set to / Record created / Based on a timed condition", size: 22, font: "Arial" })] }),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 80 },
        children: [new TextRun({ text: "Action type: Create Activity — set summary, deadline offset, and assigned user", size: 22, font: "Arial" })] }),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 80 },
        children: [new TextRun({ text: "Test each rule by creating a test opportunity and verifying the activity is triggered", size: 22, font: "Arial" })] }),

      ...gap(2),

      // 3.5 Project Module
      h2("3.5 Project & Delivery Module (Slide 07)"),
      p("Configure the Project module to receive deals from CRM. When a deal is marked Closed Won, a structured project must be created (manually in Community Edition)."),
      ...gap(1),
      makeTable(
        ["Engagement Type", "Project Template Tasks", "Owner", "Week"],
        [
          ["Staffing Engagement", "Requirement intake → Sourcing → Screening → Placement → Onboarding", "Arian", "2"],
          ["Consulting Engagement", "Architecture Design → Infrastructure Setup → Migration Execution → Validation & Testing → Handover & Docs", "Arian", "2"],
          ["Managed Service", "Service Design → Onboarding → SLA Configuration → Go-Live → Renewal Planning", "Arian", "2"],
        ],
        [2200, 4900, 1200, 760]
      ),
      ...gap(1),
      h3("Key engineering rules (must be enforced):"),
      bullet("Every CRM Closed Won deal triggers manual project creation — never skip this step"),
      bullet("Assign a project manager at deal close"),
      bullet("Link timesheets to the project from Day 1 — retroactive fixes are expensive"),
      bullet("Use task dependencies where applicable"),
      bullet("Enable client portal access per project if requested"),

      ...gap(2),

      // 3.6 Timesheets
      h2("3.6 Timesheets & Utilization Control (Slide 08)"),
      p("Configure the Timesheets module to track all engineer hours. Target utilization rate: 70-85% for all consultants. Timesheets must be linked to both Project AND Employee from day one."),
      ...gap(1),
      makeTable(
        ["Configuration Item", "Details", "Owner", "Week"],
        [
          ["Enable timesheets on projects", "Project → Settings → Enable Timesheets", "Rishit", "2"],
          ["Link Employees to projects", "Every active project must have employees assigned before work begins", "Rishit", "2"],
          ["Set hourly cost per employee", "Employees → employee record → HR Settings → Hourly Cost", "Rishit", "2"],
          ["Configure timesheet approval", "Timesheets → Configuration → set approval workflow", "Rishit", "3"],
          ["Create utilization report view", "Group timesheets by Employee, filter by Project for burn rate view", "Steve", "3"],
        ],
        [2800, 3800, 1200, 760]
      ),

      pageBreak(),

      // 3.7 Sales Quote Engine
      h2("3.7 Sales & Quote Engine (Slide 10)"),
      p("Configure 3 Sales quotation templates in Odoo Sales. All quotes, contracts, and rate cards must be generated inside Odoo — never in external documents."),
      ...gap(1),
      makeTable(
        ["Document Type", "Required Fields", "Owner", "Week"],
        [
          ["Staffing Rate Card", "Resource name & role, Bill rate, Pay/cost rate, Duration, Gross margin %", "Steve", "3"],
          ["Consulting SOW", "Scope description, Deliverables list, Milestones & timelines, Fixed fee or T&M rate, Acceptance criteria", "Steve", "3"],
          ["Managed Services Contract", "Service scope & SLAs, Monthly recurring fee, Resource allocation, Renewal terms, Escalation procedures", "Steve", "3"],
        ],
        [2400, 4800, 1200, 760]
      ),
      ...gap(1),
      h3("Steps to create quote templates:"),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 80 },
        children: [new TextRun({ text: "Go to Sales → Configuration → Quotation Templates → Create new", size: 22, font: "Arial" })] }),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 80 },
        children: [new TextRun({ text: "Add product lines for each service type (use service products, not stockable)", size: 22, font: "Arial" })] }),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 80 },
        children: [new TextRun({ text: "Add optional sections and notes per document type requirements above", size: 22, font: "Arial" })] }),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 80 },
        children: [new TextRun({ text: "Assign template to the correct CRM pipeline for auto-selection", size: 22, font: "Arial" })] }),

      ...gap(2),

      // 3.8 CEO Dashboard
      h2("3.8 CEO Dashboard — Saved Views (Slide 11)"),
      p("Build the CEO dashboard as Odoo \"Favorite\" saved views. No Enterprise license required. The following KPI views must be configured and pinned for management."),
      ...gap(1),
      makeTable(
        ["Dashboard View", "Module", "Configuration", "Owner", "Week"],
        [
          ["Total Pipeline Value", "CRM", "Sum of Expected Revenue across all 4 pipelines, group by stage", "Steve", "3"],
          ["Open Proposals", "CRM", "Filter: Stage = Proposal (P2 + P4), count", "Steve", "3"],
          ["Active Placements", "CRM", "Filter: Stage = Active Billing (P1), count", "Steve", "3"],
          ["Revenue Forecast", "CRM", "Filter: Probability > 50%, sum Expected Revenue, current month", "Steve", "3"],
          ["Pipeline by Deal Type", "CRM", "Group by Deal Classification field, show % breakdown", "Steve", "3"],
          ["Subcontracting Pipeline Status", "CRM", "Filter: P3 pipeline, group by stage", "Steve", "3"],
          ["Stalled Deals (>7 days)", "CRM", "Filter: Last activity date > 7 days ago, no activity", "Steve", "3"],
        ],
        [2200, 1200, 3800, 1200, 760]
      ),

      ...gap(2),

      // 3.9 Team Training
      h2("3.9 Team Training Session (Slide 13)"),
      p("A mandatory training session must be conducted for all IntraStack team members who will use the platform before go-live. Steve will facilitate."),
      ...gap(1),
      makeTable(
        ["Training Topic", "Duration", "Target Audience"],
        [
          ["Platform overview: 4 pipelines & how to navigate", "20 min", "All users"],
          ["Creating & managing opportunities (with custom fields)", "20 min", "Sales / Account Execs"],
          ["Daily operating playbook: Morning / Midday / EOD routine", "15 min", "All users"],
          ["Logging timesheets correctly (Project + Employee linking)", "15 min", "Engineers / Consultants"],
          ["Generating quotes & SOWs from Sales module", "15 min", "Sales / Account Execs"],
          ["Critical rules walkthrough (R1-R4, 4 mandatory fields)", "10 min", "All users"],
          ["Q&A and practice session", "25 min", "All users"],
        ],
        [4200, 1200, 3960]
      ),
      ...gap(1),
      p("Training Owner: Steve  |  Target: Week 4  |  Format: Live session + recorded walkthrough", true),

      pageBreak(),

      // ── 4. MASTER TIMELINE ────────────────────────────────────────────────
      h1("4. Master Timeline & Sprint Plan"),
      p("The 2-month remaining timeline is divided into 4 weekly sprints. All Phase 1 deliverables must be complete by end of Week 4. Phase 2 work begins in Month 2."),
      ...gap(1),

      makeTable(
        ["Week", "Sprint Focus", "Steve (Lead)", "Arian (Co-Lead)", "Rishit (Dev)", "PM Check"],
        [
          ["Week 1", "Foundation Config", "4 CRM Pipelines + stage definitions", "Contacts module + all tags", "All 6 custom fields", "Kickoff meeting, confirm access"],
          ["Week 2", "Automation + Delivery", "Automation rules R1-R4, test all triggers", "Project templates (3 types), task structures", "Timesheets setup, Employee linking", "Mid-sprint check-in"],
          ["Week 3", "Sales + Dashboard", "Sales quote engine (3 templates), CEO dashboard 7 saved views", "Project portal access config, UAT support", "Timesheet approval workflow, cost config", "Review dashboard with Luan"],
          ["Week 4", "Training + UAT", "Facilitate team training, fix bugs from UAT", "UAT testing all 4 pipelines end-to-end", "UAT testing timesheets + invoicing flow", "Sign-off meeting with Stefan & Luan"],
          ["Month 2 Week 1", "Phase 2 Prep", "Scope email automation requirements", "Research ATS integration options", "Invoice automation setup", "Phase 2 planning session"],
          ["Month 2 Week 2-4", "Phase 2 Build", "AI lead scoring module research + config", "Subcontractor portal planning", "Automated email sequences", "Weekly progress reports to Stefan"],
        ],
        [1000, 1700, 2000, 1700, 1700, 1260]
      ),

      ...gap(2),

      // ── 5. CRITICAL SUCCESS RULES ─────────────────────────────────────────
      h1("5. Critical Operating Rules (Non-Negotiable)"),
      p("The following 4 rules from the IntraStack CRM Platform document (Slide 12) are non-negotiable and must be enforced from Day 1 of go-live. Steve is responsible for training all users on these rules."),
      ...gap(1),
      makeTable(
        ["#", "Rule", "Detail", "Consequence of Violation"],
        [
          ["01", "Everything Enters CRM First", "No leads, conversations, or referrals may be tracked outside Odoo. Zero exceptions — no Excel, no Notion, no sticky notes.", "Immediate escalation to Pipeline Manager"],
          ["02", "No Deal Exists Outside Odoo", "Email thread or spreadsheet tracking = system failure. Must be escalated immediately to Steve.", "Deal data treated as unofficial until entered"],
          ["03", "Every Opportunity Must Have 4 Fields", "Owner assigned + Expected value entered + Stage set + Next action logged. Incomplete records block pipeline reporting.", "Record flagged as incomplete, owner notified"],
          ["04", "No Inactive Deals > 7 Days", "If no activity logged for 7 days, pipeline manager is automatically notified via Activity (R4 automation rule).", "Auto-alert fired, deal reviewed in next standup"],
        ],
        [400, 2000, 4200, 2760]
      ),

      ...gap(2),

      // ── 6. PHASE 2 OVERVIEW ───────────────────────────────────────────────
      h1("6. Phase 2 Overview — Automation (Month 2-3)"),
      p("Phase 2 begins after Phase 1 sign-off. These items require development effort beyond UI configuration. Scope and timeline for each item should be confirmed with Stefan and Luan at the end of Month 1."),
      ...gap(1),
      makeTable(
        ["Feature", "Description", "Effort Estimate", "Owner", "Priority"],
        [
          ["Automated Email Sequences", "Follow-up email chains triggered by CRM stage changes", "Medium — Odoo mail template config", "Steve", "High"],
          ["AI Lead Scoring Module", "Score leads based on source, deal size, and engagement", "High — requires custom Python module or OCA add-on", "Rishit + Steve", "Medium"],
          ["Full ATS Integration", "Connect applicant tracking system to Odoo Employees / Recruitment module", "High — API integration required", "Rishit", "Medium"],
          ["Subcontractor Portal Launch", "External portal for vendors to submit profiles and engage on P3 deals", "High — Odoo portal customization", "Arian + Rishit", "Medium"],
          ["Invoice Automation", "Auto-generate invoices from closed Projects / Timesheets", "Medium — Odoo invoicing rules config", "Rishit", "High"],
        ],
        [2200, 3000, 2000, 1400, 760]
      ),
      ...gap(1),
      ...infoBox([
        "  IMPORTANT: Phase 2 and Phase 3 combined represent 6-9 months of work per the original",
        "  document roadmap. The team recommends confirming with Stefan which Phase 2 items are",
        "  in scope for the remaining time after Phase 1 go-live, to avoid scope creep."
      ], COLORS.lightAmber, COLORS.amber),

      pageBreak(),

      // ── 7. RISKS ──────────────────────────────────────────────────────────
      h1("7. Risks & Mitigation"),
      makeTable(
        ["Risk", "Likelihood", "Impact", "Mitigation"],
        [
          ["Scope creep: Phase 2 & 3 expected in same 3-month window", "High", "High", "Confirm with Stefan which items are priority. Phase 1 first, Phase 2 scoped after."],
          ["VPS swap usage at 83% — potential memory issues under load", "Medium", "High", "Monitor with htop. Recommend upgrading VPS RAM before go-live if usage increases."],
          ["Team unfamiliar with Odoo platform — learning curve", "Medium", "Medium", "Steve leads all config. Use Odoo documentation + AI assistance. Daily async standups."],
          ["DNS/SSL issues delaying platform access", "Low", "Medium", "SSL setup pending — Steve to complete certbot setup as soon as DNS propagates."],
          ["Timezone gap between Steve (Asia) and Arian/Rishit", "Medium", "Low", "Arian serves as co-lead for overlap. Async updates via Telegram group daily."],
        ],
        [2400, 1000, 800, 5160]
      ),

      ...gap(2),

      // ── 8. COMMUNICATION PLAN ─────────────────────────────────────────────
      h1("8. Communication & Reporting Plan"),
      makeTable(
        ["Activity", "Frequency", "Participants", "Format"],
        [
          ["Daily async standup", "Daily (end of day Asia time)", "Steve, Arian, Rishit", "Telegram group update: Done / Doing / Blocked"],
          ["Weekly sprint review", "Every Friday", "Full team + Auspicious", "Video call — demo progress, review blockers"],
          ["Stakeholder update", "Every 2 weeks", "Auspicious → Stefan & Luan", "Written summary with % completion per task"],
          ["Phase sign-off meeting", "End of Week 4 (Phase 1) / End of Month 2", "All team + Stefan + Luan", "Live demo of full platform, formal sign-off"],
          ["Ad-hoc escalation", "As needed", "Steve → Auspicious → Luan/Stefan", "Telegram direct message, same-day response expected"],
        ],
        [2400, 1600, 2400, 2960]
      ),

      ...gap(2),

      // ── 9. ACCEPTANCE CRITERIA ────────────────────────────────────────────
      h1("9. Phase 1 Acceptance Criteria"),
      p("Phase 1 is considered complete and ready for sign-off when ALL of the following conditions are met:"),
      ...gap(1),
      bullet("All 4 CRM pipelines live with correct stage definitions"),
      bullet("All 6 custom fields present and required on every opportunity form"),
      bullet("Contacts module fully configured with 10 tag types applied"),
      bullet("Automation rules R1-R4 tested and verified working"),
      bullet("Project templates created for all 3 engagement types"),
      bullet("Timesheets linked to Projects and Employees — test entries verified"),
      bullet("3 Sales quote templates functional (Rate Card, SOW, MSC)"),
      bullet("CEO dashboard with 7 saved views accessible to management"),
      bullet("Team training session completed — all users can create and manage opportunities"),
      bullet("SSL (HTTPS) active on crm.intrastack.com"),
      bullet("At least 5 test deal records created across all 4 pipelines to verify end-to-end flow"),

      ...gap(2),

      // ── footer note ───────────────────────────────────────────────────────
      new Paragraph({
        spacing: { before: 200 },
        border: { top: { style: BorderStyle.SINGLE, size: 4, color: COLORS.gray } },
        children: []
      }),
      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun({
          text: "IntraStack Solutions — Odoo CRM Platform | Project Execution Plan v1.0 | DRAFT — For Review Only",
          size: 18, color: COLORS.gray, italics: true, font: "Arial"
        })]
      }),
      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun({
          text: "Prepared by Steve (Gia Khiem Do), Tech Lead | All timelines subject to revision after kickoff meeting",
          size: 18, color: COLORS.gray, italics: true, font: "Arial"
        })]
      }),
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("./IntraStack_Project_Execution_Plan.docx", buffer);
  console.log("Done");
});
