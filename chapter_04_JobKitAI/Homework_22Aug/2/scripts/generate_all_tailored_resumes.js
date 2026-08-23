const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const builder = path.join(__dirname, "build_resume.js");
const outputDir = path.join(__dirname, "..", "Output", "Tailored_Resumes");
fs.mkdirSync(outputDir, { recursive: true });
fs.writeFileSync(path.join(outputDir, "MATCH_REPORT.md"), "# Tailored Resume Match Reports\n");

const jobs = [
  { company: "Tothr", role: "Manual and Automation Test Engineer", short: "Manual_Automation_Test_Engineer", focus: "manual and automation testing, test case execution, defect management, and Agile QA", skills: ["Manual Testing", "Automation Testing", "Test Case Design", "Test Execution", "Regression Testing", "Defect Management", "Selenium WebDriver", "TestNG", "Agile / Scrum"], gaps: "No material tool gap; the listing is less specific than the resume." },
  { company: "Diverse Lynx Airline", role: "Manual & Automation Test Engineer", short: "Manual_Automation_Airline", focus: "manual and automation testing, regression and system testing, test specifications, and Agile/Scrum delivery", skills: ["Manual Testing", "Automation Testing", "Regression Testing", "System Testing", "Test Specifications", "Test Plans", "Selenium WebDriver", "Agile / Scrum", "Cross-functional Collaboration"], gaps: "Airline domain and Altea DCS are not evidenced; the listing also has conflicting experience and location details." },
  { company: "Kodehash Technologies", role: "Automation and Manual Tester", short: "Automation_Manual_Tester", focus: "manual and automated test execution, test case design, SDLC/STLC, defect reporting, and Agile quality", skills: ["Automation Testing", "Manual Testing", "Test Case Design", "Test Execution", "SDLC / STLC", "Agile / Scrum", "JIRA", "Selenium WebDriver", "Python / Java / JavaScript"], gaps: "Cloud JIRA/Xray is not evidenced specifically; JIRA and test management experience are evidenced." },
  { company: "India Insure Risk Management", role: "Software Tester (Manual & Automation Testing)", short: "Software_Tester_Manual_Automation", focus: "manual and automated testing across functional, regression, integration, system, API, performance, and documentation workflows", skills: ["Manual Testing", "Automation Testing", "Functional / Regression / Integration Testing", "API Testing", "Performance / Load Testing", "Selenium WebDriver", "TestNG", "Postman / Swagger / SoapUI", "JMeter", "CI/CD"], gaps: "No material tool gap; the JD does not name a required programming language." },
  { company: "Cloud Quantum", role: "Manual / Automation Testing Expert", short: "Manual_Automation_Testing_Expert", focus: "test planning, manual and automated execution, defect analysis, and continuous testing improvement", skills: ["Manual Testing", "Automation Testing", "Test Plans and Test Cases", "Test Execution", "Defect Management", "Selenium WebDriver", "TestNG", "JIRA", "Agile / Scrum", "Process Improvement"], gaps: "The JD is broad and does not specify a required tool beyond general automation." },
  { company: "Clifyx Technology", role: "Manual and Automation Testing Professional", short: "Manual_Automation_Testing_Professional", focus: "manual and automation testing for financial-services applications, with API, performance, security, and risk-based QA", skills: ["Manual Testing", "Automation Testing", "Selenium WebDriver", "QTP / UFT", "API Testing", "Performance / Load Testing", "Security Testing", "JMeter", "Risk-Based Testing", "Agile / Scrum"], gaps: "Capital Markets, Fidessa, Sophis, Raptor FIX Hub, Kafka/RabbitMQ, and Azure are not evidenced as domain/product experience; Azure DevOps is listed as a tool." },
  { company: "Neosao Services", role: "Software Tester (Manual & Automation)", short: "Software_Tester_Mobile_Automation", focus: "manual and automated software testing, comprehensive test planning, defect reporting, and Agile delivery", skills: ["Manual Testing", "Automation Testing", "Test Plans", "Test Case Design", "Functional / Regression Testing", "Selenium WebDriver", "TestNG", "API Testing", "Agile / Scrum", "Defect Management"], gaps: "Mobile Android testing and Appium are not evidenced in the resume." },
  { company: "Teamware Solutions", role: "Manual and Automation Test Engineer", short: "Manual_Automation_Test_Engineer", focus: "manual-first quality engineering, test planning, reproducible defect reporting, web/backend testing, and release metrics", skills: ["Manual Testing", "Automation Testing", "Test Plans and Test Cases", "Regression Testing", "Defect Reporting", "Web and Enterprise Platforms", "Selenium WebDriver", "JIRA", "Python / Java / JavaScript", "QA Team Leadership"], gaps: "Desktop/mobile-specific testing, Ruby, C/C++, and Perl are not evidenced; web and enterprise-platform testing is evidenced." },
  { company: "Myusit Jobs", role: "Manual & Automation Tester", short: "Manual_Automation_API_Tester", focus: "manual and automation testing with REST API validation, regression ownership, defect management, and Agile release support", skills: ["Manual Testing", "Automation Testing", "REST API Testing", "Postman / Swagger / SoapUI", "Selenium WebDriver", "TestNG", "JIRA", "Azure DevOps", "Regression Testing", "Agile / Scrum"], gaps: "Playwright, Cypress, and Rest Assured are not evidenced; Selenium, Postman, Swagger, SoapUI, and Azure DevOps are evidenced." },
  { company: "Doqfy", role: "Software Product Tester (Manual and Automation)", short: "Software_Product_Tester", focus: "software product quality through manual testing, test plans, test cases, automation, defect analysis, and clear QA reporting", skills: ["Manual Testing", "Automation Testing", "Test Plans", "Test Cases and Test Scripts", "Functional / Regression Testing", "Selenium WebDriver", "TestNG", "Defect Management", "JIRA", "Quality Reporting"], gaps: "The JD does not specify a required tool beyond general automation; performance testing is evidenced in the resume but not foregrounded here." },
  { company: "Diverse Lynx Software", role: "Manual and Automation Software Testing Professional", short: "Manual_Automation_Software_Testing", focus: "manual and automation software testing, test specifications, regression coverage, system testing, and Agile/Scrum delivery", skills: ["Manual Testing", "Automation Testing", "Test Specifications", "Test Plans", "Regression Testing", "System Testing", "Selenium WebDriver", "TestNG", "Agile / Scrum", "Defect Management"], gaps: "Airline domain and Altea DCS are not evidenced; the JD indicates 6-8 years despite a 2-6 year listing range." },
  { company: "Cynosure Corporate Solutions", role: "Automation and Manual Tester", short: "Automation_Manual_Playwright", focus: "manual and automated quality engineering, test strategy, functional/regression coverage, defect management, and Agile delivery", skills: ["Manual Testing", "Automation Testing", "Test Strategy", "Functional / Regression / Integration Testing", "Smoke / Sanity / E2E Testing", "Selenium WebDriver", "QTP / UFT", "JIRA", "Agile / Scrum", "CI/CD"], gaps: "Playwright and Java are not evidenced as hands-on experience in the resume; JavaScript, Python, Selenium, QTP/UFT, and CI/CD are evidenced." }
];

const reportCounts = {
  "Tothr": [6, 6],
  "Diverse Lynx Airline": [7, 9],
  "Kodehash Technologies": [7, 8],
  "India Insure Risk Management": [10, 10],
  "Cloud Quantum": [8, 8],
  "Clifyx Technology": [7, 12],
  "Neosao Services": [8, 9],
  "Teamware Solutions": [6, 10],
  "Myusit Jobs": [8, 11],
  "Doqfy": [8, 8],
  "Diverse Lynx Software": [8, 9],
  "Cynosure Corporate Solutions": [8, 10]
};

const experience = [
  { title: "Test Lead & Business Analyst", org: "Sopra Steria India, Noida", dates: "July 2017 - May 2026", bullets: [
    "Defined and implemented end-to-end test strategy, test plans, and QA processes using Agile/Scrum, achieving 25% improvement in test coverage and planning efficiency.",
    "Led a QA team of 5 engineers and mentored the team on Selenium automation, AI-assisted testing, and QA best practices, resulting in 25% improvement in test design speed and execution efficiency.",
    "Facilitated a Page Object Model-based Selenium automation framework for a high-traffic React application, reducing manual regression effort significantly.",
    "Executed API testing using Postman and Swagger and facilitated performance and load testing using JMeter to validate scalability and reliability.",
    "Delivered zero revenue-impacting defects across production releases through risk-based testing and structured defect management; increased product test coverage by 30%.",
    "Managed sprint tasks, user stories, and release cycles through JIRA dashboards, improving development-QA collaboration by 20%."
  ]},
  { title: "QA Lead", org: "One Vision, Gurgaon", dates: "Mar 2012 - November 2014", bullets: [
    "Defined scalable test case design standards and oversaw end-to-end functional, regression, and smoke testing cycles, improving software quality assurance by 30%.",
    "Managed a QA team of 4 engineers; conducted test case reviews, sprint planning, client demos, and QA reporting in JIRA and Confluence.",
    "Improved regression test coverage by approximately 5% per test cycle through structured execution strategies and continuous process improvement.",
    "Handled version management and coordinated release cycles for on-time delivery."
  ]},
  { title: "QA Lead & Business Analyst", org: "Steria Ltd, Noida", dates: "May 2007 - February 2012", bullets: [
    "Led a QA team of 15 engineers and mentored the team on Selenium automation, AI-assisted testing, and modern QA practices, resulting in 25% improvement in test design speed and execution efficiency.",
    "Reduced regression cycle time by 40% through automation framework implementation using QTP.",
    "Facilitated Agile ceremonies, sprint planning, and customer demos, achieving 20% improvement in sprint delivery clarity and stakeholder alignment.",
    "Conducted API testing, security testing with Burp Suite, and performance testing with JMeter for enterprise-scale applications.",
    "Developed and managed XML configurations using Altova XMLSpy, achieving 29% improvement in data accuracy and configuration efficiency."
  ]},
  { title: "QA Engineer", org: "GlobalLogic Ltd, Noida", dates: "Jan 2006 - May 2007", bullets: [
    "Executed functional and regression testing across multiple domains; created test plans, managed JIRA defect tracking, and delivered client-facing QA reports."
  ]},
  { title: "Senior Software Engineer", org: "Birlasoft Ltd, Noida", dates: "Dec 2003 - Dec 2005", bullets: [
    "Tracked project milestones and deliverables, maintained RAID logs, and collaborated with development, testing, and business teams for project alignment."
  ]},
  { title: "Software Engineer", org: "Quark Media House, Noida", dates: "Jan 2002 - Dec 2003", bullets: [
    "Coordinated project activities, tracked deliverables, prepared status reports, and supported cross-functional teams."
  ]}
];

const commonSkills = [
  ["Testing", "Manual Testing · Automation Testing · Functional Testing · Regression Testing · Smoke / Sanity Testing · API Testing · Performance / Load Testing · Security Testing · Accessibility Testing · UAT · Risk-Based Testing"],
  ["Automation", "Selenium WebDriver · TestNG · QTP / UFT · Page Object Model · Hybrid Framework"],
  ["API and Performance", "Postman · SoapUI · Swagger · JMeter"],
  ["CI/CD and DevOps", "Jenkins · Git · Bitbucket · Azure DevOps"],
  ["Test Management", "JIRA · HP ALM · Zephyr · Confluence · TestRail · ServiceNow"],
  ["Languages and Data", "Python · Java · JavaScript · TypeScript · SQL · PL/SQL · HTML · CSS · MySQL · PostgreSQL · Oracle"],
  ["Methods", "Agile · Scrum · Kanban · Waterfall · SDLC · STLC · BDD · DevOps · Shift-Left Testing"],
  ["Leadership", "QA Team Leadership · Test Strategy · Stakeholder Communication · Cross-functional Collaboration · Process Improvement"]
];

function marked(text) { return [{ t: text, hl: true }]; }
function plain(parts) {
  return parts.map((part) => typeof part === "string" ? part : part.t).join("");
}
function writePlainText(spec, outBase) {
  let text = `${spec.name}\n${spec.title}\n${spec.contact}\n\n`;
  text += `PROFESSIONAL SUMMARY\n${plain(spec.summary)}\n\nCORE SKILLS\n`;
  for (const skill of spec.skills) text += `${skill.label}: ${plain(skill.runs)}\n`;
  text += "\nEXPERIENCE\n";
  for (const job of spec.experience) {
    text += `${job.title} | ${job.org} (${job.dates})\n`;
    for (const bullet of job.bullets) text += `- ${plain(bullet)}\n`;
    text += "\n";
  }
  text += `EDUCATION\n${spec.education[0].degree} (${spec.education[0].dates}) - ${spec.education[0].school}\n`;
  fs.writeFileSync(`${outBase}.txt`, text);
}
function specFor(job) {
  const [matched, required] = reportCounts[job.company];
  const targeted = job.skills.join(" · ");
  return {
    name: "KAVITA BATRA",
    title: job.role,
    contact: "Noida, India  |  Email and phone as provided in master resume",
    summary: [
      { t: job.role, hl: true },
      " with 14+ years of experience in ",
      { t: job.focus, hl: true },
      ". Proven record of leading QA teams of up to 15 members, delivering zero revenue-impacting defects in production, improving test coverage by up to 30%, and reducing regression cycle time by 40%. Hands-on experience across Selenium, TestNG, QTP/UFT, Postman, Swagger, SoapUI, JMeter, Jenkins, JIRA, Azure DevOps, Python, JavaScript, TypeScript, Agile/Scrum, and BDD."
    ],
    skills: [
      { label: "Targeted JD Skills", runs: marked(targeted) },
      ...commonSkills.map(([label, value]) => ({ label, runs: [value] }))
    ],
    experience: experience.map((jobEntry, index) => ({
      ...jobEntry,
      bullets: jobEntry.bullets.map((bullet, bulletIndex) => {
        if (index === 0 && bulletIndex === 0) return [ { t: job.role + " alignment: ", hl: true }, bullet ];
        return [bullet];
      })
    })),
    education: [{ degree: "Master of Computer Applications (MCA)", dates: "July 1998 - July 2001", school: "Himachal Pradesh University, Simla" }],
    _report: {
      company: job.company,
      role: job.role,
      matchRate: `${matched}/${required} (${Math.round((matched / required) * 100)}%)`,
      matched,
      required,
      directMatches: targeted,
      confirmedAdditions: "None",
      gaps: job.gaps
    }
  };
}

for (const job of jobs) {
  const safe = `${job.company}_${job.short}`.replace(/[^A-Za-z0-9_]+/g, "_");
  const specPath = path.join(outputDir, `${safe}.json`);
  const outBase = path.join(outputDir, safe);
  const spec = specFor(job);
  const report = spec._report;
  delete spec._report;
  fs.writeFileSync(specPath, JSON.stringify(spec, null, 2));
  execFileSync(process.execPath, [builder, specPath, outBase], { stdio: "inherit" });
  writePlainText(spec, outBase);
  fs.unlinkSync(specPath);
  fs.appendFileSync(path.join(outputDir, "MATCH_REPORT.md"), `\n## ${report.company} — ${report.role}\n- Match rate: ${report.matchRate}\n- Direct matches: ${report.directMatches}\n- Confirmed additions: ${report.confirmedAdditions}\n- Remaining gaps: ${report.gaps}\n`);
}
console.log(`Generated ${jobs.length} tailored resume pairs in ${outputDir}`);
