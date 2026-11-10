import { useEffect, useMemo, useRef, useState, type ChangeEvent, type FormEvent, type ReactNode } from "react";
import {
  Activity,
  ArrowDownToLine,
  ArrowRight,
  ArrowUpRight,
  Bell,
  BookOpen,
  Check,
  ChevronDown,
  CircleHelp,
  Clock3,
  FileCheck2,
  FileText,
  FolderSync,
  LayoutDashboard,
  LockKeyhole,
  LogOut,
  Plus,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
  Users,
  X,
} from "lucide-react";
import { api } from "./api";
import type { AuditEvent, ConversationMessage, ConversationTurn, DocumentItem, OrganizationUser, Overview, Role, User } from "./types";

type Section = "home" | "assistant" | "knowledge" | "integrations" | "people" | "observability" | "audit";

const roleNames: Record<Role, string> = {
  organization_admin: "Organization admin",
  knowledge_manager: "Knowledge manager",
  hr: "HR workspace",
  manager: "Department manager",
  employee: "Employee",
  compliance_auditor: "Compliance auditor",
};

const demoAccounts: { label: string; email: string }[] = [
  { label: "Admin", email: "admin@knowsphere.local" },
  { label: "Knowledge", email: "knowledge@knowsphere.local" },
  { label: "HR", email: "hr@knowsphere.local" },
  { label: "Manager", email: "manager@knowsphere.local" },
  { label: "Employee", email: "employee@knowsphere.local" },
  { label: "Auditor", email: "auditor@knowsphere.local" },
];

const adminSections: { id: Section; label: string; icon: typeof LayoutDashboard }[] = [
  { id: "home", label: "Overview", icon: LayoutDashboard },
  { id: "knowledge", label: "Knowledge base", icon: BookOpen },
  { id: "integrations", label: "Integrations", icon: FolderSync },
  { id: "people", label: "People & access", icon: Users },
  { id: "observability", label: "AI observability", icon: Activity },
  { id: "audit", label: "Audit log", icon: ShieldCheck },
];

function isAdmin(role: Role) {
  return role === "organization_admin" || role === "knowledge_manager";
}

function initials(name: string) {
  return name.split(" ").map((part) => part[0]).slice(0, 2).join("").toUpperCase();
}

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [section, setSection] = useState<Section>("home");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    api.me()
      .then(({ user: current }) => setUser(current))
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  async function signOut() {
    try {
      await api.logout();
      setUser(null);
      setSection("home");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Could not sign out.");
    }
  }

  if (loading) return <div className="loading-screen"><div className="brand-mark"><Sparkles size={20} /></div><span>Loading your workspace…</span></div>;
  if (!user) return <SignIn onSignedIn={setUser} />;

  const admin = isAdmin(user.role);
  const portalLabel = user.role === "organization_admin"
    ? "Admin portal"
    : user.role === "knowledge_manager"
      ? "Knowledge manager"
      : "Employee portal";
  const sections = user.role === "organization_admin"
    ? adminSections
    : user.role === "knowledge_manager"
      ? [
          { id: "home" as const, label: "Overview", icon: LayoutDashboard },
          { id: "knowledge" as const, label: "Knowledge base", icon: BookOpen },
        ]
    : [
        { id: "home" as const, label: "My workspace", icon: LayoutDashboard },
        { id: "assistant" as const, label: "Ask KnowSphere", icon: Sparkles },
        { id: "knowledge" as const, label: "My knowledge", icon: BookOpen },
        ...(user.role === "compliance_auditor" ? [{ id: "audit" as const, label: "Audit events", icon: ShieldCheck }] : []),
      ];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-lockup">
          <div className="brand-mark"><Sparkles size={19} strokeWidth={2.2} /></div>
          <span>knowsphere<span className="brand-ai">.ai</span></span>
        </div>
        <div className="workspace-switcher">
          <div className="workspace-avatar">N</div>
          <div className="workspace-copy"><strong>{user.organization}</strong><span>{portalLabel}</span></div>
          <ChevronDown size={15} />
        </div>
        <div className="nav-label">{admin ? "WORKSPACE" : "YOUR WORKSPACE"}</div>
        <nav className="main-nav" aria-label="Main navigation">
          {sections.map(({ id, label, icon: Icon }) => (
            <button key={id} className={`nav-item ${section === id ? "active" : ""}`} onClick={() => setSection(id)}>
              <Icon size={17} strokeWidth={1.8} /><span>{label}</span>
              {id === "integrations" && <span className="nav-dot" />}
            </button>
          ))}
        </nav>
        <div className="sidebar-spacer" />
        <div className="security-note"><LockKeyhole size={15} /><span>Permission-aware by design</span></div>
        <button className="user-menu" onClick={signOut}>
          <div className="avatar">{initials(user.name)}</div>
          <div className="user-copy"><strong>{user.name}</strong><span>{roleNames[user.role]} · Switch account</span></div>
          <LogOut size={15} className="logout-icon" />
        </button>
      </aside>
      <main className="main-area">
        <header className="topbar">
          <div className="breadcrumb"><span>{portalLabel}</span><span className="crumb-slash">/</span><strong>{sections.find((item) => item.id === section)?.label ?? "Overview"}</strong></div>
          <div className="topbar-actions">
            <span className="secure-pill"><span /> Secure workspace</span>
            <button className="icon-button" aria-label="Help"><CircleHelp size={18} /></button>
            <button className="icon-button notification-button" aria-label="Notifications"><Bell size={18} /><i /></button>
          </div>
        </header>
        {notice && <div className="toast" role="status">{notice}<button onClick={() => setNotice("")}><X size={15} /></button></div>}
        <div className="page-content">
          {section === "home" && (admin ? <AdminHome user={user} onNavigate={setSection} /> : <PersonalHome user={user} onNavigate={setSection} />)}
          {section === "assistant" && <Assistant user={user} />}
          {section === "knowledge" && <Knowledge user={user} />}
          {section === "integrations" && <Integrations onNavigate={setSection} />}
          {section === "people" && <People user={user} />}
          {section === "observability" && <Observability />}
          {section === "audit" && <Audit />}
        </div>
      </main>
    </div>
  );
}

function SignIn({ onSignedIn }: { onSignedIn: (user: User) => void }) {
  const [email, setEmail] = useState(demoAccounts[0].email);
  const [password, setPassword] = useState("KnowSphereDemo2026!");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const { user } = await api.login(email, password);
      onSignedIn(user);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to sign in.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="login-screen">
      <div className="login-decoration decoration-one" /><div className="login-decoration decoration-two" />
      <div className="login-card">
        <div className="brand-lockup login-brand"><div className="brand-mark"><Sparkles size={19} /></div><span>knowsphere<span className="brand-ai">.ai</span></span></div>
        <div className="login-heading"><span className="eyebrow">YOUR ORGANIZATION, IN FOCUS</span><h1>Knowledge that<br /><span>knows its source.</span></h1><p>Sign in to your secure company knowledge workspace.</p></div>
        <form onSubmit={submit} className="login-form">
          <label htmlFor="email">Work email</label>
          <input id="email" type="email" autoComplete="username" value={email} onChange={(event) => setEmail(event.target.value)} required />
          <div className="label-row"><label htmlFor="password">Password</label><span>Local demo</span></div>
          <input id="password" type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required />
          {error && <div className="form-error" role="alert">{error}</div>}
          <button className="primary-button login-submit" disabled={submitting}>{submitting ? "Signing in…" : "Sign in securely"}<ArrowRight size={17} /></button>
        </form>
        <div className="demo-box">
          <div className="demo-title"><span>CHOOSE YOUR PORTAL</span><span className="demo-password">Password: <b>KnowSphereDemo2026!</b></span></div>
          <div className="demo-roles">{demoAccounts.map((account) => <button key={account.email} onClick={() => setEmail(account.email)} className={email === account.email ? "selected" : ""}>{account.label}</button>)}</div>
        </div>
        <div className="login-foot"><LockKeyhole size={13} /> Your workspace is protected with role-based access</div>
      </div>
      <div className="login-caption">Trusted knowledge. Clear answers. <span>Built for your organization.</span></div>
    </div>
  );
}

function PageTitle({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: ReactNode }) {
  return <div className="page-title"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{description}</p></div>{action}</div>;
}

function AdminHome({ user, onNavigate }: { user: User; onNavigate: (section: Section) => void }) {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [error, setError] = useState("");
  useEffect(() => {
    Promise.all([api.overview(), api.documents()])
      .then(([stats, result]) => { setOverview(stats); setDocuments(result.documents); })
      .catch((err: Error) => setError(err.message));
  }, []);

  return <>
    <PageTitle eyebrow="TUESDAY, NOVEMBER 10" title={`Good morning, ${user.name.split(" ")[0]}`} description="Here's what’s happening across your knowledge workspace today." action={<button className="primary-button" onClick={() => onNavigate("integrations")}><Plus size={16} /> Connect a source</button>} />
    {error && <div className="inline-error">{error}</div>}
    <div className="stat-grid">
      <StatCard label="Indexed documents" value={overview?.indexed ?? "—"} change={`${overview?.documents ?? "—"} accessible in your workspace`} icon={FileCheck2} tone="violet" />
      <StatCard label="Organization members" value={overview?.users ?? "—"} change="Across your workspace" icon={Users} tone="blue" />
      <StatCard label="Connected sources" value="0" change="Connect your first knowledge source" icon={FolderSync} tone="amber" />
      <StatCard label="Audit events" value={overview?.events ?? "—"} change="Recorded this workspace" icon={ShieldCheck} tone="green" />
    </div>
    <div className="dashboard-grid">
      <section className="panel recent-panel">
        <div className="panel-heading"><div><h2>Recently updated knowledge</h2><p>Documents available in your workspace</p></div><button className="text-button" onClick={() => onNavigate("knowledge")}>View all <ArrowRight size={14} /></button></div>
        <DocumentTable documents={documents.slice(0, 4)} />
      </section>
      <section className="panel source-panel">
        <div className="panel-heading"><div><h2>Knowledge sources</h2><p>Keep company knowledge in sync</p></div><button className="round-add" aria-label="Add source" onClick={() => onNavigate("integrations")}><Plus size={16} /></button></div>
        <div className="source-list">
          <SourceRow icon="S" name="SharePoint" detail="Recommended · Microsoft 365" tint="sharepoint" onClick={() => onNavigate("integrations")} />
          <SourceRow icon="G" name="Google Drive" detail="Connect shared drives" tint="google" onClick={() => onNavigate("integrations")} />
          <SourceRow icon="↑" name="Upload text documents" detail="TXT and Markdown in this build" tint="upload" onClick={() => onNavigate("knowledge")} />
        </div>
        <div className="source-foot"><span className="pulse-dot" /> All systems operational</div>
      </section>
    </div>
    <div className="bottom-grid">
      <section className="panel insight-panel"><div className="insight-icon"><Sparkles size={18} /></div><div><h3>Your knowledge workspace is ready</h3><p>Connect a repository to start syncing approved policies and team knowledge.</p></div><button className="text-button" onClick={() => onNavigate("integrations")}>Get started <ArrowRight size={14} /></button></section>
      <section className="panel security-panel"><div className="security-badge"><ShieldCheck size={18} /></div><div><strong>Access controls are active</strong><span>Documents are filtered to each person’s role.</span></div><Check size={17} className="check-icon" /></section>
    </div>
  </>;
}

function PersonalHome({ user, onNavigate }: { user: User; onNavigate: (section: Section) => void }) {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [question, setQuestion] = useState("");
  useEffect(() => { api.documents().then((result) => setDocuments(result.documents)).catch(() => setDocuments([])); }, []);
  const prompt = user.role === "hr"
    ? "Find HR policies, benefits and people operations guidance."
    : user.role === "manager"
      ? "Find team practices, operating guides and department knowledge."
      : user.role === "compliance_auditor"
        ? "Review compliance evidence and authorized access procedures."
        : "Ask a question about your company’s policies and knowledge.";
  return <>
    <PageTitle eyebrow={`${user.department.toUpperCase()} WORKSPACE`} title={`Good morning, ${user.name.split(" ")[0]}`} description={prompt} />
    <section className="hero-assistant">
      <div className="hero-glow" /><div className="hero-content">
        <div className="hero-kicker"><span className="hero-spark"><Sparkles size={15} /></span> KNOWSPHERE ASSISTANT <span className="beta-tag">BETA</span></div>
        <h2>What would you like<br />to know today?</h2>
        <p>Answers grounded in the information you’re authorized to see.</p>
        <form className="hero-input" onSubmit={(event) => { event.preventDefault(); sessionStorage.setItem("knowsphere-question", question); onNavigate("assistant"); }}>
          <input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask about policies, processes, benefits…" aria-label="Ask KnowSphere" />
          <button type="submit" disabled={!question.trim()} aria-label="Ask question"><ArrowRight size={18} /></button>
        </form>
        <div className="prompt-suggestions"><span>Try asking</span><button onClick={() => setQuestion("What is our information security policy?")}>Information security policy</button><button onClick={() => setQuestion("How do I request time off?")}>Requesting time off</button></div>
      </div>
      <div className="hero-art" aria-hidden="true"><div className="orbit orbit-one" /><div className="orbit orbit-two" /><div className="orbit-core"><Sparkles size={29} /></div><div className="orbit-card card-a"><FileText size={15} /><span>Verified source</span><Check size={13} /></div><div className="orbit-card card-b"><ShieldCheck size={15} /><span>Access checked</span></div></div>
    </section>
    <div className="section-heading"><div><h2>Your knowledge</h2><p>Resources available to you</p></div><button className="text-button" onClick={() => onNavigate("knowledge")}>Browse all <ArrowRight size={14} /></button></div>
    <div className="personal-doc-grid">{documents.slice(0, 3).map((doc) => <DocumentCard key={doc.id} doc={doc} />)}</div>
    <div className="privacy-banner"><LockKeyhole size={15} /><span>Your results are filtered to your <strong>{roleNames[user.role].toLowerCase()}</strong> access.</span><button onClick={() => onNavigate("knowledge")}>How access works <ArrowUpRight size={13} /></button></div>
  </>;
}

function StatCard({ label, value, change, icon: Icon, tone }: { label: string; value: string | number; change: string; icon: typeof FileText; tone: string }) {
  return <div className="stat-card"><div className={`stat-icon ${tone}`}><Icon size={18} /></div><div className="stat-label">{label}</div><div className="stat-value">{value}</div><div className="stat-change">{change}</div></div>;
}

function DocumentTable({ documents }: { documents: DocumentItem[] }) {
  if (!documents.length) return <div className="empty-table"><FileText size={22} /><span>No documents to show yet.</span></div>;
  return <div className="table-wrap"><table><thead><tr><th>DOCUMENT</th><th>COLLECTION</th><th>STATUS</th><th>UPDATED</th><th /></tr></thead><tbody>{documents.map((doc) => <tr key={doc.id}><td><div className="table-doc"><div className="file-icon"><FileText size={15} /></div><span>{doc.title}</span></div></td><td>{doc.category}</td><td><span className={`status-pill ${doc.status.toLowerCase().replace(" ", "-")}`}><i />{doc.status}</span></td><td>{doc.updated_at}</td><td><button className="tiny-icon" aria-label={`Open ${doc.title}`}><ArrowUpRight size={15} /></button></td></tr>)}</tbody></table></div>;
}

function SourceRow({ icon, name, detail, tint, onClick }: { icon: string; name: string; detail: string; tint: string; onClick: () => void }) {
  return <button className="source-row" onClick={onClick}><div className={`source-logo ${tint}`}>{icon}</div><div className="source-info"><strong>{name}</strong><span>{detail}</span></div><ArrowRight size={15} /></button>;
}

function DocumentCard({ doc }: { doc: DocumentItem }) {
  return <article className="document-card"><div className="doc-card-top"><div className="file-icon"><FileText size={17} /></div><span className={`mini-status ${doc.status.toLowerCase()}`}><i />{doc.status}</span></div><div className="doc-category">{doc.category}</div><h3>{doc.title}</h3><p>{doc.snippet}</p><div className="doc-card-foot"><span><Clock3 size={13} /> Updated {doc.updated_at}</span><ArrowUpRight size={15} /></div></article>;
}

function Knowledge({ user }: { user: User }) {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [uploading, setUploading] = useState(false);
  useEffect(() => { api.documents().then((result) => setDocuments(result.documents)).catch((err: Error) => setError(err.message)); }, []);
  const visible = useMemo(() => documents.filter((doc) => `${doc.title} ${doc.category} ${doc.source}`.toLowerCase().includes(search.toLowerCase())), [documents, search]);

  async function uploadTextFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setError("");
    setSuccess("");
    if (file.size > 80_000) {
      setError("Text files must be 80 KB or smaller.");
      return;
    }
    if (!/\.(txt|md)$/i.test(file.name)) {
      setError("This starter supports plain text (.txt) and Markdown (.md) uploads only.");
      return;
    }
    setUploading(true);
    try {
      const { document } = await api.uploadDocument({
        title: file.name.replace(/\.(txt|md)$/i, ""),
        category: "Uploaded knowledge",
        source: file.name,
        access_level: "org",
        content: await file.text(),
      });
      setDocuments((current) => [document, ...current]);
      setSuccess(`${file.name} uploaded and queued for review.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not upload this document.");
    } finally {
      setUploading(false);
    }
  }

  async function publishDocument(document: DocumentItem) {
    setError("");
    setSuccess("");
    try {
      const { document: published } = await api.updateDocumentStatus(document.id, "Published");
      setDocuments((current) => current.map((item) => item.id === published.id ? published : item));
      setSuccess(`${published.title} is now published.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not publish this document.");
    }
  }

  return <>
    <PageTitle eyebrow="KNOWLEDGE LIBRARY" title={isAdmin(user.role) ? "Knowledge base" : "Your knowledge"} description={isAdmin(user.role) ? "Review and manage organization knowledge. New uploads stay private until published." : "Browse the sources and policies you’re authorized to access."} action={isAdmin(user.role) ? <label className={`primary-button upload-label ${uploading ? "uploading" : ""}`}><Plus size={16} />{uploading ? "Uploading…" : "Upload text"}<input type="file" accept=".txt,.md,text/plain,text/markdown" onChange={(event) => void uploadTextFile(event)} disabled={uploading} /></label> : undefined} />
    <div className="library-toolbar"><div className="search-field"><Search size={16} /><input placeholder="Search your knowledge…" value={search} onChange={(event) => setSearch(event.target.value)} /></div><div className="scope-label"><LockKeyhole size={14} /> Permission-filtered</div></div>
    {error && <div className="inline-error">{error}</div>}
    {success && <div className="success-message"><Check size={15} />{success}</div>}
    {visible.length ? <div className="library-grid">{visible.map((doc) => <div className="managed-document" key={doc.id}><DocumentCard doc={doc} />{isAdmin(user.role) && doc.status === "Pending Review" && <button className="publish-button" onClick={() => void publishDocument(doc)}><Check size={14} /> Publish after review</button>}</div>)}</div> : <div className="empty-state"><BookOpen size={24} /><h3>No matching documents</h3><p>Try a different search. Only documents you’re authorized to access are shown.</p></div>}
    {isAdmin(user.role) && <div className="prototype-note">Text/Markdown upload is enabled. PDF/DOCX extraction, malware scanning and SharePoint synchronization are not connected in this build.</div>}
  </>;
}

function Assistant({ user }: { user: User }) {
  const [question, setQuestion] = useState(() => sessionStorage.getItem("knowsphere-question") ?? "");
  const [conversation, setConversation] = useState<ConversationTurn[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [pendingQuestion, setPendingQuestion] = useState("");
  const threadRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (threadRef.current) threadRef.current.scrollTop = threadRef.current.scrollHeight;
  }, [conversation, pendingQuestion]);

  async function ask(event?: FormEvent) {
    event?.preventDefault();
    const currentQuestion = question.trim();
    if (!currentQuestion || busy) return;
    const history: ConversationMessage[] = conversation.slice(-6).flatMap((turn) => [
      { role: "user", content: turn.question },
      { role: "assistant", content: turn.result.answer },
    ]);
    setBusy(true);
    setError("");
    setPendingQuestion(currentQuestion);
    try {
      const result = await api.ask(currentQuestion, history);
      const next = [...conversation, { question: currentQuestion, result }].slice(-10);
      setConversation(next);
      sessionStorage.removeItem("knowsphere-question");
      setQuestion("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not search your knowledge.");
    } finally {
      setBusy(false);
      setPendingQuestion("");
    }
  }
  return <div className="assistant-page">
    <PageTitle eyebrow="KNOWSPHERE ASSISTANT" title="Ask your knowledge" description={`Answers are grounded in sources available to your ${roleNames[user.role].toLowerCase()}.`} />
    <div className="chat-surface">
      {conversation.length === 0 && <div className="assistant-welcome"><div className="assistant-avatar"><Sparkles size={20} /></div><h2>Hi {user.name.split(" ")[0]}, what can I help with?</h2><p>Ask a question, then continue with follow-ups. I’ll keep the conversation in context.</p></div>}
      {conversation.length > 0 && <div className="conversation-toolbar"><span>Conversation · {conversation.length} {conversation.length === 1 ? "turn" : "turns"}</span><button type="button" className="text-button" onClick={() => { setConversation([]); setError(""); }}>New conversation</button></div>}
      <div className="conversation-thread" aria-live="polite" ref={threadRef}>
        {conversation.map((turn, index) => <div className="conversation-turn" key={`${index}-${turn.question}`}>
          <div className="user-message"><strong>You</strong><p>{turn.question}</p></div>
          <section className="answer-card"><div className="answer-heading"><div className="assistant-avatar small"><Sparkles size={15} /></div><strong>KnowSphere</strong><span className="grounded-badge"><ShieldCheck size={13} />{turn.result.mode === "gemini" ? "Gemini · source-grounded" : turn.result.mode === "conversation" ? "Conversation" : "No supporting source"}</span></div><p className="answer-copy">{turn.result.answer}</p>{turn.result.sources.length > 0 && <div className="citations"><div className="citation-label">SOURCES {turn.result.sources.length}</div>{turn.result.sources.map((source, sourceIndex) => <div className="citation" key={source.id}><span className="citation-number">{sourceIndex + 1}</span><div><strong>{source.title}</strong><span>{source.source}{source.pages.length ? ` · Page${source.pages.length > 1 ? "s" : ""} ${source.pages.join(", ")}` : ""}</span><p>{source.snippet}</p></div><ArrowUpRight size={14} /></div>)}</div>}</section>
        </div>)}
        {pendingQuestion && <div className="conversation-turn"><div className="user-message"><strong>You</strong><p>{pendingQuestion}</p></div><div className="answer-loading"><span className="spinner" /> Searching authorized sources with your conversation in context…</div></div>}
      </div>
      {error && <div className="inline-error">{error}</div>}
      <form className="chat-input" onSubmit={ask}><textarea rows={2} placeholder={conversation.length ? "Ask a follow-up question…" : "Ask a question about your organization…"} value={question} onChange={(event) => { setQuestion(event.target.value); if (error) setError(""); }} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); void ask(); } }} /><button disabled={!question.trim() || busy} aria-label="Send question">{busy ? <span className="spinner" /> : <Send size={17} />}</button></form>
      <div className="chat-foot"><LockKeyhole size={13} /> Only authorized sources are searched <span>·</span> Follow-up questions use this conversation for context</div>
    </div>
    <div className="assistant-disclaimer">Gemini semantic search and answer generation are required. Your question and only the retrieved authorized excerpts are sent to Gemini. Verify important decisions in the original document.</div>
  </div>;
}

function Integrations({ onNavigate }: { onNavigate: (section: Section) => void }) {
  return <>
    <PageTitle eyebrow="CONNECT YOUR KNOWLEDGE" title="Integrations" description="Connect the repositories your organization trusts. Each source respects its original access permissions." />
    <div className="integration-callout"><div className="callout-icon"><ShieldCheck size={20} /></div><div><strong>Your source permissions stay in control</strong><p>Connectors must verify permissions before documents can appear in search or answer context.</p></div></div>
    <div className="integration-grid">
      <IntegrationCard mark="S" markClass="sharepoint" name="Microsoft SharePoint" description="Sync selected sites and document libraries using Microsoft Graph." priority="P1 · First priority" button="OAuth setup not wired yet" />
      <IntegrationCard mark="G" markClass="google" name="Google Drive" description="Bring shared drives and folders into your organization’s knowledge." priority="P3 · Planned" button="Planned" />
      <IntegrationCard mark="↑" markClass="upload" name="Direct upload" description="TXT and Markdown uploads are available from the Knowledge Base. PDF/DOCX extraction is not implemented." priority="P0 · MVP" button="Open Knowledge Base" onClick={() => onNavigate("knowledge")} />
      <IntegrationCard mark="C" markClass="confluence" name="Confluence" description="Connect internal documentation and team spaces." priority="P4 · Planned" button="Planned" />
    </div>
    <div className="integration-note"><span className="pulse-dot" /><span><strong>Connector status:</strong> SharePoint and Google Drive authentication and synchronization are not implemented yet. Use Knowledge Base for TXT/Markdown uploads; they remain pending review until published.</span></div>
  </>;
}

function IntegrationCard({ mark, markClass, name, description, priority, button, onClick }: { mark: string; markClass: string; name: string; description: string; priority: string; button: string; onClick?: () => void }) {
  return <article className="integration-card"><div className="integration-card-top"><div className={`source-logo large ${markClass}`}>{mark}</div><span className="integration-priority">{priority}</span></div><h3>{name}</h3><p>{description}</p><button className={onClick ? "outline-button" : "disabled-button"} disabled={!onClick} onClick={onClick}>{button}{onClick && <ArrowRight size={14} />}</button></article>;
}

function People({ user }: { user: User }) {
  const [members, setMembers] = useState<OrganizationUser[]>([]);
  const [drafts, setDrafts] = useState<Record<string, { role: Role; department: string }>>({});
  const [error, setError] = useState("");
  const [saved, setSaved] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.users()
      .then(({ users }) => setMembers(users))
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  function getDraft(member: OrganizationUser) {
    return drafts[member.id] ?? { role: member.role, department: member.department };
  }

  async function saveMember(member: OrganizationUser) {
    const draft = getDraft(member);
    setError("");
    setSaved("");
    try {
      const { user: updated } = await api.updateUser(member.id, draft.role, draft.department);
      setMembers((current) => current.map((item) => item.id === updated.id ? updated : item));
      setDrafts((current) => {
        const next = { ...current };
        delete next[member.id];
        return next;
      });
      setSaved(`Updated access for ${updated.name}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update member access.");
    }
  }

  return <>
    <PageTitle eyebrow="ORGANIZATION ACCESS" title="People & access" description="View organization members and manage their roles and department access." />
    <div className="permission-banner"><ShieldCheck size={18} /><div><strong>Organization-wide admin access</strong><span>As an organization admin, you can review all organization members and knowledge, and manage member roles. Changes are audit logged.</span></div></div>
    {error && <div className="inline-error">{error}</div>}
    {saved && <div className="success-message"><Check size={15} />{saved}</div>}
    <div className="panel people-panel"><div className="panel-heading"><div><h2>Organization members</h2><p>{loading ? "Loading members…" : `${members.length} members · You cannot change your own role.`}</p></div><span className="read-only-badge">ORG ADMIN</span></div>
      {loading ? <div className="empty-table">Loading organization members…</div> : members.length === 0 ? <div className="empty-table"><Users size={22} /><span>No members found.</span></div> : <div className="member-list">{members.map((member) => {
        const draft = getDraft(member);
        const dirty = draft.role !== member.role || draft.department !== member.department;
        const self = member.id === user.id;
        return <div className="member-row" key={member.id}>
          <div className="member-avatar">{initials(member.name)}</div>
          <div className="member-identity"><strong>{member.name}{self && <span className="you-tag">YOU</span>}</strong><span>{member.email}</span></div>
          <label className="member-field member-role-field"><span>ROLE</span><select value={draft.role} disabled={self} onChange={(event) => setDrafts((current) => ({ ...current, [member.id]: { ...getDraft(member), role: event.target.value as Role } }))}>
            {Object.entries(roleNames).map(([role, label]) => <option value={role} key={role}>{label}</option>)}
          </select></label>
          <label className="member-field department-field"><span>DEPARTMENT</span><input value={draft.department} disabled={self} onChange={(event) => setDrafts((current) => ({ ...current, [member.id]: { ...getDraft(member), department: event.target.value } }))} /></label>
          <button className="save-member-button" disabled={!dirty || self} onClick={() => void saveMember(member)}>{dirty ? "Save" : <Check size={15} />}</button>
        </div>;
      })}</div>}
      <div className="panel-footnote">Signed in as {user.name} · Role or department updates immediately change server-enforced access.</div>
    </div>
  </>;
}

function Observability() {
  return <>
    <PageTitle eyebrow="RESTRICTED ADMIN MODULE" title="AI observability" description="Monitor answer quality, retrieval behavior, latency and usage while protecting sensitive data." />
    <div className="observability-empty"><div className="observability-symbol"><Activity size={24} /></div><h2>Observability is ready for instrumentation</h2><p>Langfuse and OpenTelemetry are planned integrations. This workspace does not yet collect model traces or usage data.</p><div className="obs-controls"><span><LockKeyhole size={14} /> Restricted to authorized administrators</span><span><ShieldCheck size={14} /> Raw trace access must be audited</span></div></div>
    <div className="obs-metric-grid"><div className="obs-metric"><span>Answer latency</span><strong>—</strong><small>Waiting for instrumentation</small></div><div className="obs-metric"><span>Citation validation</span><strong>—</strong><small>No evaluation runs yet</small></div><div className="obs-metric"><span>Token usage</span><strong>—</strong><small>No model connected</small></div></div>
  </>;
}

function Audit() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [error, setError] = useState("");
  useEffect(() => { api.audit().then((result) => setEvents(result.events)).catch((err: Error) => setError(err.message)); }, []);
  function exportEvents() {
    const escapeCsv = (value: string) => `"${value.replaceAll('"', '""')}"`;
    const rows = [
      ["Time", "Action", "User", "Email"],
      ...events.map((event) => [event.created_at, event.action, event.name, event.email]),
    ];
    const csv = rows.map((row) => row.map(escapeCsv).join(",")).join("\r\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = "knowsphere-audit.csv";
    link.click();
    URL.revokeObjectURL(url);
  }
  return <>
    <PageTitle eyebrow="GOVERNANCE" title="Audit log" description="A record of sign-ins, knowledge queries and sensitive administrative activity." action={<button className="outline-button" onClick={exportEvents} disabled={!events.length}><ArrowDownToLine size={15} /> Export CSV</button>} />
    {error && <div className="inline-error">{error}</div>}
    <div className="panel audit-panel"><div className="panel-heading"><div><h2>Recent events</h2><p>Latest activity in this organization</p></div><span className="live-tag"><i /> LIVE</span></div>{events.length ? <div className="audit-list">{events.map((event, index) => <div className="audit-row" key={`${event.created_at}-${index}`}><div className="audit-icon"><Activity size={15} /></div><div className="audit-action"><strong>{event.action.replace(".", " · ")}</strong><span>{event.name} · {event.email}</span></div><time>{new Date(event.created_at).toLocaleString()}</time><Check size={15} className="audit-check" /></div>)}</div> : <div className="empty-table"><ShieldCheck size={22} /><span>No audit events recorded yet.</span></div>}</div>
  </>;
}

export default App;
