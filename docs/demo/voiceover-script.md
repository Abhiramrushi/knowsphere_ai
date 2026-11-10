# KnowSphere AI product tour voiceover

## 1. Company knowledge, with context and control

Meet KnowSphere AI: one workspace where teams can ask questions across company knowledge, see the source behind a response, and give administrators control over who can access what. This tour begins at sign-in and walks through the admin panels, then the HR and employee experiences.

## 2. Start with the right workspace

The sign-in screen offers separate demo roles for organization admin, knowledge manager, HR, manager, employee, and compliance auditor. Each role lands in a different workspace and has a different document scope. This build uses local demo accounts; production identity and single sign-on are not connected yet.

## 3. The model is Gemini. The product is the workflow around it.

One point of clarity: KnowSphere is not a newly trained foundation model competing with Gemini. The current assistant uses Gemini for embeddings and answer generation. Its product difference is the workflow around that model: the server checks role and department permissions before retrieval, returns answers grounded in authorized excerpts, shows citations, and records activity. A general chat tool used on its own does not provide these organization-specific controls unless they are built and configured around it.

## 4. Admin overview at a glance

The organization admin overview summarizes indexed documents, organization members, connected sources, and audit events. It also points to recently updated knowledge and source management. In this demo, the connector count is zero because repository synchronization is not enabled yet.

## 5. Review what enters the knowledge base

Admins and knowledge managers can browse organization documents and search the library. New text or Markdown uploads stay pending and private until an authorized person reviews and publishes them. The demo also indexes seven supplied sample PDFs at startup, but uploading new PDFs or Word files is not supported yet. Access scopes are applied before passages are returned to the assistant.

## 6. Connectors: what works today

The integrations panel shows the planned source roadmap and a working path to direct text upload. TXT and Markdown uploads are available from the knowledge base. SharePoint and Google Drive authentication and synchronization, plus Confluence, are shown as planned and are not connected in this build. The pricing reference includes roadmap items, so those should not be read as live product capabilities yet.

## 7. Manage people and access

The organization admin can view members and change another person's role or department. Those changes update server-enforced access and are audit logged. HR, managers, employees, auditors, and knowledge managers see different sections and document scopes. The admin cannot change their own role from this screen.

## 8. Observability is a placeholder today

The admin menu includes an AI observability panel, but this module is not instrumented yet. Langfuse and OpenTelemetry are planned; this build does not collect model traces, token usage, latency, or evaluation runs. The screen makes that status visible instead of showing fabricated metrics.

## 9. Keep an audit trail

The audit log records activity such as sign-ins, knowledge queries, document changes, and member updates. Organization admins and compliance auditors can review recent events, and the log can be exported as a CSV file. It gives the team a record of how the workspace is being used without claiming that a model answer is automatically correct.

## 10. The employee experience

An employee signs into a simpler workspace with three panels: My workspace, Ask KnowSphere, and My knowledge. The home panel offers suggested questions and shows a few available documents. My knowledge lists only content this employee is allowed to access; the API applies the same role scope to searches and citations.

## 11. A source-backed answer for an employee

Here the employee asks which device is required for remote work. The example answer points back to the remote-work policy and its page. In a live configured session, KnowSphere embeds the question, ranks only published passages the current user is allowed to see, and sends those excerpts to Gemini to draft an answer. This recording uses an illustrative response and sample citation so the walkthrough does not make a paid live model call.

## 12. The employee knowledge panel

My knowledge is the employee's document library. It includes the source title, collection, status, and summary for the records this role may browse. The sample workspace assigns some content to organization access, some to a team, and some to restricted scopes; the employee sees only the items allowed by the API's role rules.

## 13. The HR workspace home

HR uses the same employee-facing structure, with an HR-specific home prompt, its own access scope, and the Ask KnowSphere and My knowledge panels. The HR landing page suggests policy, benefits, and people-operations questions. HR can see organization and HR-scoped records allowed by the role rules.

## 14. HR's permission-filtered knowledge

The HR My knowledge panel shows the documents this HR account can browse. The supplied handbook in this demo is assigned organization-wide scope, so it is visible to all seeded roles; in a configured workspace, HR-only records can use the HR scope. This makes the demo's current data scope explicit while showing the same role-based retrieval mechanism.

## 15. A practical HR policy question

For HR, the example asks about hybrid work guidelines. The illustrative answer summarizes the sample handbook's two-to-three on-site days, equipment allowance, and core hours, with a citation to the source page. Follow-up questions can use recent conversation turns for context, while earlier answers are not used as evidence. As before, this on-screen response is a scripted sample for the video.

## 16. Simple pricing by billing period

The provided rates apply equally to Team and Business: seven thousand nine hundred ninety-nine rupees monthly, fourteen thousand nine hundred ninety-nine quarterly, or twenty-one thousand nine hundred ninety-nine yearly. Enterprise remains custom. The supplied pricing image is a concept reference and still contains TBD labels; the current rates are written here and in the README. Some features on that reference, including connector sync, SSO, and advanced observability, are roadmap items and are not live in this MVP.

## 17. Know what your organization knows

KnowSphere brings permission-aware retrieval, cited answers, and workspace governance into one product flow, using Gemini as its current model service. The MVP is ready to demonstrate local accounts, sample documents, role scopes, reviewable uploads, and audit events. Repository sync, production identity, and AI observability can be added as the product grows.
