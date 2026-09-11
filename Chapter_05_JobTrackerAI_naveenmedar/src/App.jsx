import { useEffect, useMemo, useRef, useState } from 'react'
import { openDB } from 'idb'
import { DndContext, DragOverlay, useDraggable, useDroppable } from '@dnd-kit/core'
import { Archive, BriefcaseBusiness, CalendarDays, Check, ChevronDown, CircleHelp, Download, ExternalLink, FileUp, Filter, GripVertical, Moon, MoreHorizontal, Pencil, Plus, Search, Sun, Trash2, X } from 'lucide-react'
import './App.css'

const columns = [
  { id: 'wishlist', label: 'Wishlist', note: 'Saved for later', color: '#7d8ca3' },
  { id: 'applied', label: 'Applied', note: 'Application submitted', color: '#3f82f7' },
  { id: 'follow-up', label: 'Follow-up', note: 'Keep the thread warm', color: '#d99335' },
  { id: 'interview', label: 'Interview', note: 'In the conversation', color: '#8a65d6' },
  { id: 'offer', label: 'Offer', note: 'Good news', color: '#2da77e' },
  { id: 'rejected', label: 'Rejected', note: 'Close the loop', color: '#c86068' },
]
const initialJobs = [
  { id: 'sample-1', company: 'Northstar Labs', role: 'QA Automation Engineer', url: 'https://linkedin.com/jobs', resume: 'QA_Lead_Resume', date: '2026-08-18', salary: '$120-140K', notes: 'Referred by Maya', status: 'interview' },
  { id: 'sample-2', company: 'Mosaic Health', role: 'Senior Test Engineer', url: 'https://linkedin.com/jobs', resume: 'SDE_Resume_v3', date: '2026-08-20', salary: '₹25-30 LPA', notes: '', status: 'applied' },
  { id: 'sample-3', company: 'Fathom Systems', role: 'Quality Engineer', url: 'https://linkedin.com/jobs', resume: 'QA_Lead_Resume', date: '2026-08-13', salary: '$110-125K', notes: 'Follow up Friday', status: 'follow-up' },
]
const initialPostedJobs = [
  { id: 'posted-1', source: 'LinkedIn', company: 'Vertex Cloud', role: 'QA Automation Engineer', location: 'Bengaluru, India', experience: 4, salary: '₹18-24 LPA', posted: '2026-08-22', url: 'https://www.linkedin.com/jobs/' },
  { id: 'posted-2', source: 'Naukri', company: 'BlueOrbit Technologies', role: 'Senior QA Engineer - Manual & Automation', location: 'Hyderabad, India', experience: 5, salary: '₹20-28 LPA', posted: '2026-08-21', url: 'https://www.naukri.com/' },
  { id: 'posted-3', source: 'LinkedIn', company: 'Kiteworks', role: 'SDET / Test Automation Specialist', location: 'Remote, India', experience: 4, salary: '$35-45K', posted: '2026-08-20', url: 'https://www.linkedin.com/jobs/' },
]

const dbPromise = openDB('job-tracker-ai', 1, { upgrade(db) { if (!db.objectStoreNames.contains('jobs')) db.createObjectStore('jobs', { keyPath: 'id' }) } })
const jobStore = async (operation, value) => { const db = await dbPromise; if (operation === 'getAll') return db.getAll('jobs'); const tx = db.transaction('jobs', operation === 'delete' ? 'readwrite' : 'readwrite'); await tx.store[operation](value); await tx.done }
const today = () => new Date().toISOString().slice(0, 10)
const daysSince = (date) => Math.max(0, Math.floor((Date.now() - new Date(`${date}T12:00:00`).getTime()) / 86400000))

function IconButton({ label, children, ...props }) { return <button className="icon-button" aria-label={label} title={label} {...props}>{children}</button> }

function parseFeedCsv(input) {
  const rows = []
  let row = []
  let field = ''
  let quoted = false
  for (let index = 0; index < input.length; index += 1) {
    const char = input[index]
    if (char === '"' && input[index + 1] === '"' && quoted) { field += '"'; index += 1; continue }
    if (char === '"') { quoted = !quoted; continue }
    if (char === ',' && !quoted) { row.push(field.trim()); field = ''; continue }
    if ((char === '\n' || char === '\r') && !quoted) {
      if (char === '\r' && input[index + 1] === '\n') index += 1
      row.push(field.trim()); field = ''
      if (row.some(Boolean)) rows.push(row)
      row = []
      continue
    }
    field += char
  }
  if (field || row.length) { row.push(field.trim()); rows.push(row) }
  const headers = rows.shift()?.map((header) => header.toLowerCase().replace(/[^a-z0-9]/g, '')) || []
  return rows.map((values, index) => {
    const get = (...names) => values[ names.map((name) => headers.indexOf(name)).find((position) => position >= 0) ] || ''
    return {
      id: get('id') || `imported-${Date.now()}-${index}`,
      source: get('source', 'portal') || 'Imported', company: get('company', 'companyname'), role: get('role', 'jobtitle', 'jobtitlerole'),
      location: get('location'), experience: Number.parseInt(get('experience', 'minexperience'), 10) || 0,
      salary: get('salary', 'salaryrange'), posted: get('posted', 'posteddate', 'dateposted'), url: get('url', 'joburl', 'linkedinurl'),
    }
  }).filter((job) => job.company && job.role)
}

function JobCard({ job, onEdit, onDelete }) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({ id: job.id })
  const column = columns.find((item) => item.id === job.status)
  return <article ref={setNodeRef} className={`job-card ${isDragging ? 'dragging' : ''}`} style={{ '--accent': column.color, transform: transform ? `translate3d(${transform.x}px, ${transform.y}px, 0)` : undefined }}>
    <div className="card-top"><span className="company-mark">{job.company.slice(0, 1).toUpperCase()}</span><div className="card-company"><strong>{job.company}</strong><span>{job.role}</span></div><button className="drag-handle" aria-label="Drag job" title="Drag job" {...listeners} {...attributes}><GripVertical size={16} /></button></div>
    <div className="card-meta"><span className="resume-tag">{job.resume || 'No resume tagged'}</span>{job.url && <a className="linkedin-link" href={job.url} target="_blank" rel="noreferrer" aria-label={`Open ${job.company} job link`} title="Open job link"><ExternalLink size={14} /></a>}</div>
    <div className="card-footer"><span><CalendarDays size={13} /> {job.date ? `${daysSince(job.date)}d since applied` : 'Not applied yet'}</span><div className="card-actions"><IconButton label="Edit job" onClick={() => onEdit(job)}><Pencil size={14} /></IconButton><IconButton label="Delete job" onClick={() => onDelete(job)}><Trash2 size={14} /></IconButton></div></div>
  </article>
}

function Column({ column, jobs, onEdit, onDelete }) {
  const { isOver, setNodeRef } = useDroppable({ id: column.id })
  return <section className={`kanban-column ${isOver ? 'is-over' : ''}`} ref={setNodeRef} style={{ '--column-accent': column.color }}><header className="column-header"><div><div className="column-title"><span className="status-dot" /> <h2>{column.label}</h2><span className="count">{jobs.length}</span></div><p>{column.note}</p></div><button className="column-menu" aria-label={`${column.label} options`} title="Column options"><MoreHorizontal size={18} /></button></header><div className="column-cards">{jobs.length ? jobs.map((job) => <JobCard key={job.id} job={job} onEdit={onEdit} onDelete={onDelete} />) : <div className="empty-column"><Archive size={18} /><span>Drop a job here</span></div>}</div></section>
}

function PostedJobs({ jobs, query, onTrack, onImport }) {
  const matches = jobs.filter((job) => job.experience >= 4 && `${job.company} ${job.role} ${job.location}`.toLowerCase().includes(query.toLowerCase()))
  return <section className="posted-section"><div className="posted-heading"><div><div className="section-kicker"><Filter size={13} /> Curated feed</div><h2>Jobs posted</h2><p>QA opportunities matched to 4+ years of experience.</p></div><label className="feed-import"><FileUp size={14} /> Import CSV / JSON<input className="visually-hidden" type="file" accept=".csv,.json,application/json,text/csv" onChange={onImport} /></label></div><div className="posted-list">{matches.length ? matches.map((job) => <article className="posted-job" key={job.id}><div className="source-badge">{job.source}</div><div className="posted-main"><strong>{job.company}</strong><h3>{job.role}</h3><span>{job.location} · {job.experience}+ years · {job.salary}</span></div><div className="posted-date">Posted {job.posted}</div><div className="posted-actions"><a href={job.url} target="_blank" rel="noreferrer" className="outline-button" title={`Open ${job.source} posting`}><ExternalLink size={14} /> View</a><button className="track-button" onClick={() => onTrack(job)}><Plus size={14} /> Track job</button></div></article>) : <div className="posted-empty">No matching QA roles in the feed yet. Import a CSV or JSON job list to refresh it.</div>}</div></section>
}

function JobModal({ job, resumes, onClose, onSave }) {
  const [form, setForm] = useState(job || { company: '', role: '', url: '', resume: resumes[0] || '', date: today(), salary: '', notes: '', status: 'wishlist' })
  const [error, setError] = useState('')
  const update = (key, value) => setForm((current) => ({ ...current, [key]: value }))
  const submit = (event) => { event.preventDefault(); if (!form.company.trim() || !form.role.trim()) { setError('Company and role are required.'); return } if (form.url && !/^https?:\/\//i.test(form.url)) { setError('Use a full URL beginning with http:// or https://.'); return } onSave({ ...form, id: form.id || crypto.randomUUID(), company: form.company.trim(), role: form.role.trim() }); }
  return <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onClose()}><div className="modal" role="dialog" aria-modal="true" aria-labelledby="job-modal-title"><header className="modal-header"><div><span className="eyebrow">{job ? 'Update record' : 'New opportunity'}</span><h2 id="job-modal-title">{job ? 'Edit job' : 'Add a job'}</h2></div><IconButton label="Close form" onClick={onClose}><X size={19} /></IconButton></header><form onSubmit={submit}><div className="form-grid"><label>Company name *<input autoFocus value={form.company} onChange={(e) => update('company', e.target.value)} placeholder="e.g. Northstar Labs" /></label><label>Job title / role *<input value={form.role} onChange={(e) => update('role', e.target.value)} placeholder="e.g. QA Automation Engineer" /></label><label>LinkedIn job URL<input type="url" value={form.url} onChange={(e) => update('url', e.target.value)} placeholder="https://linkedin.com/jobs/..." /></label><label>Resume used<select value={form.resume} onChange={(e) => update('resume', e.target.value)}><option value="">Select a resume</option>{resumes.map((resume) => <option key={resume}>{resume}</option>)}<option value="Custom">Custom</option></select></label><label>Date applied<input type="date" value={form.date} onChange={(e) => update('date', e.target.value)} /></label><label>Salary range<input value={form.salary} onChange={(e) => update('salary', e.target.value)} placeholder="e.g. $120-140K" /></label><label>Status<select value={form.status} onChange={(e) => update('status', e.target.value)}>{columns.map((column) => <option key={column.id} value={column.id}>{column.label}</option>)}</select></label><label className="wide">Notes<textarea value={form.notes} onChange={(e) => update('notes', e.target.value)} placeholder="Recruiter, referral, next step..." rows="3" /></label></div>{error && <p className="form-error">{error}</p>}<footer className="modal-footer"><button type="button" className="secondary-button" onClick={onClose}>Cancel</button><button type="submit" className="primary-button"><Check size={16} /> {job ? 'Save changes' : 'Add job'}</button></footer></form></div></div>
}

function App() {
  const [jobs, setJobs] = useState([]); const [postedJobs, setPostedJobs] = useState(initialPostedJobs); const [query, setQuery] = useState(''); const [activeJob, setActiveJob] = useState(null); const [modalOpen, setModalOpen] = useState(false); const [dark, setDark] = useState(false); const [sortNewest, setSortNewest] = useState(true); const [dragged, setDragged] = useState(null); const fileRef = useRef(null)
  useEffect(() => { jobStore('getAll').then((stored) => { if (stored.length) setJobs(stored); else { setJobs(initialJobs); initialJobs.forEach((job) => jobStore('put', job)) } }) }, [])
  useEffect(() => { document.documentElement.dataset.theme = dark ? 'dark' : 'light' }, [dark])
  const resumes = useMemo(() => [...new Set(jobs.map((job) => job.resume).filter(Boolean))], [jobs])
  const visible = useMemo(() => [...jobs].filter((job) => `${job.company} ${job.role}`.toLowerCase().includes(query.toLowerCase())).sort((first, second) => {
    if (!first.date && !second.date) return 0
    if (!first.date) return 1
    if (!second.date) return -1
    const comparison = second.date.localeCompare(first.date)
    return sortNewest ? comparison : -comparison
  }), [jobs, query, sortNewest])
  const persist = (next) => { setJobs(next); next.forEach((job) => jobStore('put', job)) }
  const saveJob = (job) => { persist([...jobs.filter((item) => item.id !== job.id), job]); setModalOpen(false); setActiveJob(null) }
  const removeJob = (job) => { if (window.confirm(`Delete ${job.company} from your tracker?`)) { setJobs(jobs.filter((item) => item.id !== job.id)); jobStore('delete', job.id) } }
  const dropJob = ({ active, over }) => { if (!over || active.id === over.id) return; const target = columns.some((column) => column.id === over.id) ? over.id : null; if (!target) return; const job = jobs.find((item) => item.id === active.id); if (job && job.status !== target) persist(jobs.map((item) => item.id === job.id ? { ...item, status: target } : item)) }
  const exportData = () => { const blob = new Blob([JSON.stringify(jobs, null, 2)], { type: 'application/json' }); const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = 'job-tracker-backup.json'; link.click(); URL.revokeObjectURL(url) }
  const importData = (event) => { const file = event.target.files?.[0]; if (!file) return; const reader = new FileReader(); reader.onload = () => { try { const incoming = JSON.parse(reader.result); if (!Array.isArray(incoming)) throw new Error(); persist(incoming); } catch { window.alert('That backup file is not valid job tracker JSON.') } }; reader.readAsText(file); event.target.value = '' }
  const importPosted = (event) => { const file = event.target.files?.[0]; if (!file) return; const reader = new FileReader(); reader.onload = () => { try { const incoming = file.name.toLowerCase().endsWith('.csv') ? parseFeedCsv(reader.result) : JSON.parse(reader.result); if (!Array.isArray(incoming) || !incoming.length) throw new Error(); setPostedJobs(incoming); } catch { window.alert('Use a CSV or JSON array with company, role, source, experience, location, salary, posted, and url fields.') } }; reader.readAsText(file); event.target.value = '' }
  const trackPosted = (job) => { const tracked = { id: crypto.randomUUID(), company: job.company, role: job.role, url: job.url, resume: '', date: today(), salary: job.salary || '', notes: `${job.source} posting · ${job.location}`, status: 'wishlist' }; persist([...jobs, tracked]) }
  return <main className="app-shell"><header className="app-header"><div className="brand"><div className="brand-icon"><BriefcaseBusiness size={20} /></div><div><strong>Jobflow</strong><span>Personal job tracker</span></div></div><div className="header-actions"><button className="text-button" onClick={exportData}><Download size={16} /> Export</button><button className="text-button" onClick={() => fileRef.current?.click()}><FileUp size={16} /> Import</button><input ref={fileRef} className="visually-hidden" type="file" accept="application/json" onChange={importData} /><IconButton label={dark ? 'Use light mode' : 'Use dark mode'} onClick={() => setDark(!dark)}>{dark ? <Sun size={17} /> : <Moon size={17} />}</IconButton><IconButton label="Help"><CircleHelp size={17} /></IconButton><div className="avatar">NM</div></div></header><section className="workspace-heading"><div><span className="eyebrow">August 2026</span><h1>Applications board</h1><p>Keep every opportunity moving forward.</p></div><button className="primary-button add-button" onClick={() => { setActiveJob(null); setModalOpen(true) }}><Plus size={18} /> Add job</button></section><section className="toolbar"><div className="search-box"><Search size={17} /><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search company or role..." /><kbd>⌘ K</kbd></div><div className="toolbar-right"><span className="result-count">{visible.length} opportunities</span><button className="sort-button" onClick={() => setSortNewest(!sortNewest)}>Date applied <ChevronDown size={15} className={!sortNewest ? 'flipped' : ''} /></button></div></section><PostedJobs jobs={postedJobs} query={query} onTrack={trackPosted} onImport={importPosted} /><DndContext onDragStart={({ active }) => setDragged(jobs.find((job) => job.id === active.id))} onDragEnd={(event) => { dropJob(event); setDragged(null) }}><div className="board">{columns.map((column) => <Column key={column.id} column={column} jobs={visible.filter((job) => job.status === column.id).sort((a, b) => sortNewest ? b.date.localeCompare(a.date) : a.date.localeCompare(b.date))} onEdit={(job) => { setActiveJob(job); setModalOpen(true) }} onDelete={removeJob} />)}</div><DragOverlay>{dragged ? <JobCard job={dragged} onEdit={() => {}} onDelete={() => {}} /> : null}</DragOverlay></DndContext>{modalOpen && <JobModal job={activeJob} resumes={resumes} onClose={() => { setModalOpen(false); setActiveJob(null) }} onSave={saveJob} />}</main>
}

export default App
