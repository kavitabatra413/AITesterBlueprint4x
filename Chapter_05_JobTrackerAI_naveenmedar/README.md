# Jobflow - Local Job Tracker AI

Jobflow is a local-first job application tracker built with React and Vite. It provides a glass-style Kanban workspace for managing QA, automation, manual testing, and other job applications without a backend, account, or external database.

## What It Does

The app has two connected workflows:

1. **Jobs posted**: Review locally imported job postings from LinkedIn, Naukri, or any other source.
2. **Applications board**: Track jobs through the application lifecycle.

The Jobs posted feed is intentionally local. LinkedIn and Naukri do not provide a general public API for importing arbitrary job postings, so the app does not scrape, log in to, or automate either portal. Users can import an approved CSV or JSON export and open the original posting through its source URL.

## Jobs Posted Feed

The feed is shown above the Kanban board and automatically keeps jobs with at least 4 years of experience:

- Search by company, role, or location
- See source, company, role, location, experience, salary, and posting date
- Open the original LinkedIn or Naukri posting
- Track a posting with one click
- Move a tracked posting into the Wishlist column
- Import a new CSV or JSON feed at any time

### CSV Format

The importer accepts these headers. Header matching is case-insensitive and ignores spaces and punctuation.

```csv
source,company,role,location,experience,salary,posted,url
LinkedIn,Example Labs,QA Automation Engineer,Bengaluru,4,18-24 LPA,2026-08-22,https://www.linkedin.com/jobs/view/123
Naukri,Example Systems,Senior QA Engineer,Hyderabad,5,20-28 LPA,2026-08-21,https://www.naukri.com/job-listings/example
```

Common aliases are also supported:

| Meaning | Accepted headers |
|---|---|
| Company | `company`, `Company Name` |
| Role | `role`, `Job Title`, `Job Title / Role` |
| Experience | `experience`, `Min Experience` |
| Salary | `salary`, `Salary Range` |
| Posted date | `posted`, `Posted Date`, `Date Posted` |
| URL | `url`, `Job URL`, `LinkedIn URL` |

Rows without a company or role are ignored. The experience value should begin with a number, such as `4`, `4+`, or `5 years`.

### JSON Format

The JSON upload must contain an array of job objects:

```json
[
  {
    "id": "job-001",
    "source": "LinkedIn",
    "company": "Example Labs",
    "role": "QA Automation Engineer",
    "location": "Bengaluru",
    "experience": 4,
    "salary": "18-24 LPA",
    "posted": "2026-08-22",
    "url": "https://www.linkedin.com/jobs/view/123"
  }
]
```

Only records with `experience >= 4` appear in the feed. Imported records replace the currently displayed feed, while tracked jobs remain in the application board.

## Applications Board

The Kanban board has six independently scrollable columns:

1. **Wishlist** - Saved jobs that have not been applied to
2. **Applied** - Application submitted
3. **Follow-up** - Recruiter or referral follow-up completed
4. **Interview** - Active interview process
5. **Offer** - Offer received
6. **Rejected** - Application rejected

### Job Card Details

Each card displays:

- Company name
- Job title
- Resume used
- Days since the application date
- Clickable job URL icon
- Status-colored left border
- Edit and delete actions

Cards can be dragged between columns. Column headers show the current card count.

## Adding and Editing Jobs

Select **Add job** to open the job form. Company name and role are required. The form also supports:

- LinkedIn or other job URL with URL validation
- Resume name selected from previously used values
- Editable application date
- Salary range
- Notes for recruiters, referrals, and next steps
- Initial Kanban status

Deleting a card requires confirmation.

## Local Data and Backup

All application-board records are stored in the browser using IndexedDB through the `idb` package. CRUD changes are written immediately to the local database.

Available data tools:

- **Export** downloads all tracked application cards as `job-tracker-backup.json`.
- **Import** restores application cards from a JSON array backup.
- **Import CSV / JSON** refreshes the Jobs posted review feed.

The app has no server, authentication, API calls, or external database. Clearing site data or changing browser profiles can remove the local IndexedDB records, so export backups regularly.

## Additional Features

- Light and dark mode toggle
- Newest/oldest application-date sorting
- Search result count
- Responsive laptop, tablet, and mobile layout
- Keyboard-friendly form controls
- Accessible labels and tooltips for icon actions
- Drag preview overlay
- Sample jobs on first launch to demonstrate the workflow

## Tech Stack

- React 19
- Vite
- `idb` for IndexedDB
- `@dnd-kit/core` for drag-and-drop
- `lucide-react` for icons
- Oxlint
- CSS glassmorphism styling with responsive media queries

## Run Locally

From the `Chapter_05_JobTrackerAI_naveenmedar` directory:

```bash
npm install
npm run dev
```

Open the local URL printed by Vite, usually `http://localhost:5173/`.

## Verification Commands

```bash
npm run lint
npm run build
```

## Automatic Portal Integration

Automatic syncing from LinkedIn or Naukri is not included because it requires an official API, partner feed, or an approved integration. For a future connector, the provider should supply a normalized array matching the JSON schema above. Any credentials should be kept in local environment variables and must never be committed to the repository.
