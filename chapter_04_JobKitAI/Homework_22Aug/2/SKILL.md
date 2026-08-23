---
name: resume-tailor
description: "Tailor a master resume to a specific job description (JD). Use this skill whenever the user provides a job description (pasted list, uploaded file, or job posting text) and wants their resume matched/tailored/optimized to it — including phrases like 'tailor my resume', 'update my resume for this job', 'match my resume to this JD', 'ATS optimize my resume', or when the user uploads both a resume and a JD in the same request. Always use this skill for repeat resume-tailoring requests rather than improvising from scratch — it enforces a no-fabrication policy and a consistent two-format output (highlighted .docx + plain-text) with a match-rate report."
---

# Resume Tailor

Tailors a candidate's real resume to a specific job description: extracts JD keywords/requirements, cross-references them against the candidate's *true* experience, rewrites the resume to surface genuine overlap, and reports a match rate plus honest gaps. Never invents skills, tools, or experience the candidate doesn't have.

## Hard rule: never fabricate

This is the most important part of the skill. Only add a skill/tool/keyword to the resume if:
1. It's already present in the candidate's master resume (just reworded/re-surfaced), OR
2. The candidate explicitly confirms in this conversation that they have real experience with it.

If a JD requirement isn't met by either of those, it goes in the **gap report**, not the resume. Do not soften this — a resume that overclaims can get someone disqualified in an interview, which is worse than a lower keyword match.

## Workflow

### 1. Get the master resume
If the user uploaded a resume (or one exists earlier in the conversation), use it as the source of truth. If not, ask them to paste or upload it before proceeding — don't guess at someone's work history.

### 2. Get the JD
Take the JD as given (pasted list, uploaded file, or job posting text). If it's a URL, fetch it.

### 3. Extract JD requirements
Pull out, in categories:
- Required languages/tools/frameworks
- Required methodologies (e.g., BDD, Agile, CI/CD)
- Certifications (note separately whether "required" or "preferred")
- Responsibilities and soft-skill phrases the JD repeats (e.g., "quality-first," "ownership," "cross-functional")

### 4. Cross-reference against the master resume
For each JD requirement, classify it as:
- **Direct match** — already on the resume, possibly under different wording
- **Reasonable reword** — the resume shows equivalent work (e.g., Cucumber + Gherkin = "BDD") — safe to make explicit
- **Gap** — not evidenced anywhere on the resume

### 5. Resolve gaps with the user — always ask first
For anything classified as a gap that's a *significant* JD requirement (appears in "Required Skills," not just "nice to have"), ask the user directly whether they have real, undocumented experience with it, before adding anything. Use a compact multi-select question (`ask_user_input_v0`) grouping the gap skills, e.g.:

> "Do you have hands-on experience with any of these, beyond what's on your resume? [skill A] [skill B] [skill C] [None of these]"

Only fold confirmed items into the resume. Everything else stays in the gap report. Don't re-ask about the same skill in later runs if the user already answered "no" earlier in the conversation — treat that as still true unless they say otherwise.

### 6. Rewrite the resume
- Rework the **summary** to open with the JD's role title/framing and lead with the strongest genuine metrics.
- Reorganize **Core Skills** into categories that mirror the JD's own grouping where sensible (e.g., if the JD separates "Automation" from "API Testing," do the same).
- Reword **bullets** to surface matched keywords in the candidate's own real accomplishments — never change the underlying facts or metrics, only the phrasing/emphasis.
- Track every added/reworded phrase that exists *because of* the JD match — these get highlighted (see step 7).

### 7. Build outputs — both formats, every time
Use `scripts/build_resume.js` (Node, `docx` package — already installed, see docx skill gotchas if extending). It takes a JSON spec (schema below) and writes both:
- `<name>.docx` — formatted resume with JD-matched additions/rewords highlighted yellow
- `<name>.txt` — plain text, no highlight markup, safe to paste directly into Google Docs or an online application form

```bash
node scripts/build_resume.js resume_data.json /mnt/user-data/outputs/<Company>_<Role>_Resume
```

**JSON spec** — each text field is either a plain string or an array of "runs." A run is a string (unhighlighted) or `{"t": "text", "hl": true}` (highlighted — use only for JD-driven additions/rewords):

```json
{
  "name": "Full Name",
  "title": "Role headline",
  "contact": "City, Country  •  email  •  phone  •  linkedin",
  "summary": ["plain text ", {"t": "highlighted phrase", "hl": true}, " more plain text"],
  "skills": [{"label": "Category", "runs": ["value", {"t": "new value", "hl": true}]}],
  "experience": [{
    "title": "Job Title", "org": "Company, Location", "dates": "Mon YYYY – Mon YYYY",
    "bullets": [["plain ", {"t": "highlighted", "hl": true}, " plain"]]
  }],
  "projects": [{"heading": "PROJECT NAME", "bullets": [["bullet text"]]}],
  "education": [{"degree": "Degree", "dates": "YYYY", "school": "School, Location"}]
}
```

After generating, render the docx to an image and look at it (see docx skill's verify-the-output step) before presenting — check the highlights landed on the intended phrases and nothing overflows to a second page awkwardly.

Save outputs to `/mnt/user-data/outputs/` and call `present_files` with both the `.docx` and `.txt`.

### 8. Match report — always include
After presenting the files, give a short conversational (not a file) report:
- **Match rate**: matched required-skill count / total required-skill count from the JD, as a percentage
- **Matched keywords**: brief list, grouped by direct-match vs. reworded
- **Confirmed additions**: anything the user newly confirmed this round
- **Remaining gaps**: JD requirements still not evidenced, with a one-line honest note on what closing each would take (a cert, a short course, a side project, etc.)

### 9. Repeat for multiple JDs in one session
If the user provides another JD later in the same conversation, re-run from step 2 using the same master resume (plus any gap-skills they already confirmed) — don't re-ask for the resume or re-litigate previously confirmed skills.

## File naming
Use `<Company>_<RoleShort>_Resume.docx` / `.txt` when the company/role is identifiable from the JD; otherwise `<CandidateName>_Resume_Tailored.docx`.
