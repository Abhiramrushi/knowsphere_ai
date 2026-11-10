from __future__ import annotations

import asyncio
import subprocess
import tempfile
import wave
from dataclasses import dataclass
from pathlib import Path

import edge_tts
import imageio_ffmpeg
import truststore
from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
CAPTURES = ROOT / "docs" / "demo" / "captures"
OUTPUT = ROOT / "docs" / "demo" / "knowsphere-product-tour.mp4"
WIDTH, HEIGHT = 1920, 1080
BG = (12, 15, 29)
BG2 = (18, 23, 42)
WHITE = (246, 247, 255)
MUTED = (171, 179, 203)
PURPLE = (137, 119, 255)
CYAN = (107, 204, 238)
GREEN = (131, 219, 172)
FONT_PATH = Path("C:/Windows/Fonts/segoeui.ttf")
BOLD_PATH = Path("C:/Windows/Fonts/seguisb.ttf")


@dataclass
class Scene:
    title: str
    eyebrow: str
    narration: str
    caption: str
    image: str | None = None
    points: tuple[str, ...] = ()
    kind: str = "screen"


SCENES = [
    Scene(
        "Company knowledge,\nwith context and control",
        "KNOWSPHERE AI · PRODUCT TOUR",
        "Meet KnowSphere AI: one workspace where teams can ask questions across company knowledge, see the source behind a response, and give administrators control over who can access what. This tour begins at sign-in and walks through the admin panels, then the HR and employee experiences.",
        "A role-aware knowledge workspace built around your organization's documents.",
        kind="title",
    ),
    Scene(
        "Start with the right workspace",
        "01 · SIGN IN",
        "The sign-in screen offers separate demo roles for organization admin, knowledge manager, HR, manager, employee, and compliance auditor. Each role lands in a different workspace and has a different document scope. This build uses local demo accounts; production identity and single sign-on are not connected yet.",
        "One sign-in experience. Different role-specific workspaces.",
        image="01-login.png",
        points=("Admin and knowledge manager tools", "HR, manager, employee and auditor views", "Local demo authentication in this build"),
    ),
    Scene(
        "The model is Gemini. The product is the workflow around it.",
        "02 · HOW IT DIFFERS",
        "One point of clarity: KnowSphere is not a newly trained foundation model competing with Gemini. The current assistant uses Gemini for embeddings and answer generation. Its product difference is the workflow around that model: the server checks role and department permissions before retrieval, returns answers grounded in authorized excerpts, shows citations, and records activity. A general chat tool used on its own does not provide these organization-specific controls unless they are built and configured around it.",
        "Gemini underneath · permission-filtered retrieval · cited answers · audit events",
        kind="difference",
    ),
    Scene(
        "Admin overview at a glance",
        "03 · ADMIN PORTAL",
        "The organization admin overview summarizes indexed documents, organization members, connected sources, and audit events. It also points to recently updated knowledge and source management. In this demo, the connector count is zero because repository synchronization is not enabled yet.",
        "See the workspace inventory and jump into governance tasks.",
        image="02-admin-overview.png",
        points=("Indexed knowledge and member counts", "Recent documents and source entry points", "Connector sync is not live in this build"),
    ),
    Scene(
        "Review what enters the knowledge base",
        "04 · KNOWLEDGE BASE",
        "Admins and knowledge managers can browse organization documents and search the library. New text or Markdown uploads stay pending and private until an authorized person reviews and publishes them. The demo also indexes seven supplied sample PDFs at startup, but uploading new PDFs or Word files is not supported yet. Access scopes are applied before passages are returned to the assistant.",
        "Review and publish first. Then eligible roles can retrieve the content.",
        image="03-admin-knowledge.png",
        points=("TXT and Markdown upload", "Pending review before publication", "Sample PDFs are indexed; PDF upload is not enabled"),
    ),
    Scene(
        "Connectors: what works today",
        "05 · INTEGRATIONS",
        "The integrations panel shows the planned source roadmap and a working path to direct text upload. TXT and Markdown uploads are available from the knowledge base. SharePoint and Google Drive authentication and synchronization, plus Confluence, are shown as planned and are not connected in this build. The pricing reference includes roadmap items, so those should not be read as live product capabilities yet.",
        "Direct text upload works. Repository connectors remain on the roadmap.",
        image="04-admin-integrations.png",
        points=("TXT and Markdown: available", "SharePoint and Google Drive sync: not wired", "Confluence: planned"),
    ),
    Scene(
        "Manage people and access",
        "06 · PEOPLE & ACCESS",
        "The organization admin can view members and change another person's role or department. Those changes update server-enforced access and are audit logged. HR, managers, employees, auditors, and knowledge managers see different sections and document scopes. The admin cannot change their own role from this screen.",
        "Roles and departments shape access on the server, not just in the menu.",
        image="05-admin-people.png",
        points=("Review all organization members", "Change another member's role or department", "Changes are recorded in the audit log"),
    ),
    Scene(
        "Observability is a placeholder today",
        "07 · AI OBSERVABILITY",
        "The admin menu includes an AI observability panel, but this module is not instrumented yet. Langfuse and OpenTelemetry are planned; this build does not collect model traces, token usage, latency, or evaluation runs. The screen makes that status visible instead of showing fabricated metrics.",
        "Visible in the admin portal; tracing and usage metrics are not connected yet.",
        image="06-admin-observability.png",
        points=("No model traces or token counts yet", "Langfuse / OpenTelemetry planned", "No live monitoring data in this build"),
    ),
    Scene(
        "Keep an audit trail",
        "08 · AUDIT LOG",
        "The audit log records activity such as sign-ins, knowledge queries, document changes, and member updates. Organization admins and compliance auditors can review recent events, and the log can be exported as a CSV file. It gives the team a record of how the workspace is being used without claiming that a model answer is automatically correct.",
        "Review recent events and export the activity log as CSV.",
        image="07-admin-audit.png",
        points=("Sign-ins, queries and admin actions", "Admin and compliance auditor access", "CSV export"),
    ),
    Scene(
        "The employee experience",
        "09 · EMPLOYEE WORKSPACE",
        "An employee signs into a simpler workspace with three panels: My workspace, Ask KnowSphere, and My knowledge. The home panel offers suggested questions and shows a few available documents. My knowledge lists only content this employee is allowed to access; the API applies the same role scope to searches and citations.",
        "A focused home, a searchable library, and the assistant in reach.",
        image="08-employee-home.png",
        points=("My workspace", "Ask KnowSphere", "My knowledge · permission-filtered"),
    ),
    Scene(
        "A source-backed answer for an employee",
        "10 · EMPLOYEE CHAT",
        "Here the employee asks which device is required for remote work. The example answer points back to the remote-work policy and its page. In a live configured session, KnowSphere embeds the question, ranks only published passages the current user is allowed to see, and sends those excerpts to Gemini to draft an answer. This recording uses an illustrative response and sample citation so the walkthrough does not make a paid live model call.",
        "Illustrative response · sample policy citation · live answers require Gemini configuration.",
        image="09-employee-assistant.png",
        points=("Question: remote-work device requirement", "Answer cites the source and page", "Sample response shown for this recording"),
    ),
    Scene(
        "The employee knowledge panel",
        "11 · EMPLOYEE KNOWLEDGE",
        "My knowledge is the employee's document library. It includes the source title, collection, status, and summary for the records this role may browse. The sample workspace assigns some content to organization access, some to a team, and some to restricted scopes; the employee sees only the items allowed by the API's role rules.",
        "The library follows the employee's authorized scope.",
        image="10-employee-knowledge.png",
        points=("Browse available documents", "Search by title or collection", "Only authorized records are returned"),
    ),
    Scene(
        "The HR workspace home",
        "12 · HR WORKSPACE",
        "HR uses the same employee-facing structure, with an HR-specific home prompt, its own access scope, and the Ask KnowSphere and My knowledge panels. The HR landing page suggests policy, benefits, and people-operations questions. HR can see organization and HR-scoped records allowed by the role rules.",
        "HR's landing page is tailored to people operations.",
        image="08-hr-home.png",
        points=("HR workspace prompt", "Ask KnowSphere", "My knowledge"),
    ),
    Scene(
        "HR's permission-filtered knowledge",
        "13 · HR KNOWLEDGE",
        "The HR My knowledge panel shows the documents this HR account can browse. The supplied handbook in this demo is assigned organization-wide scope, so it is visible to all seeded roles; in a configured workspace, HR-only records can use the HR scope. This makes the demo's current data scope explicit while showing the same role-based retrieval mechanism.",
        "HR sees allowed documents; this supplied handbook is organization-wide.",
        image="10-hr-knowledge.png",
        points=("HR workspace and policy discovery", "Role-specific document scope", "Sample handbook is organization-wide in this demo"),
    ),
    Scene(
        "A practical HR policy question",
        "14 · HR CHAT",
        "For HR, the example asks about hybrid work guidelines. The illustrative answer summarizes the sample handbook's two-to-three on-site days, equipment allowance, and core hours, with a citation to the source page. Follow-up questions can use recent conversation turns for context, while earlier answers are not used as evidence. As before, this on-screen response is a scripted sample for the video.",
        "Follow the answer back to the policy it came from.",
        image="09-hr-assistant.png",
        points=("Example: hybrid work guidance", "Source excerpt and page shown", "Follow-up context is supported"),
    ),
    Scene(
        "Simple pricing by billing period",
        "15 · PRICING",
        "The provided rates apply equally to Team and Business: seven thousand nine hundred ninety-nine rupees monthly, fourteen thousand nine hundred ninety-nine quarterly, or twenty-one thousand nine hundred ninety-nine yearly. Enterprise remains custom. The supplied pricing image is a concept reference and still contains TBD labels; the current rates are written here and in the README. Some features on that reference, including connector sync, SSO, and advanced observability, are roadmap items and are not live in this MVP.",
        "Team and Business: ₹7,999 monthly · ₹14,999 quarterly · ₹21,999 yearly. Enterprise: custom.",
        kind="pricing",
    ),
    Scene(
        "Know what your organization knows",
        "16 · KNOWSPHERE AI",
        "KnowSphere brings permission-aware retrieval, cited answers, and workspace governance into one product flow, using Gemini as its current model service. The MVP is ready to demonstrate local accounts, sample documents, role scopes, reviewable uploads, and audit events. Repository sync, production identity, and AI observability can be added as the product grows.",
        "KnowSphere AI · Knowledge that knows its source.",
        kind="outro",
    ),
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(BOLD_PATH if bold else FONT_PATH), size=size)


def rounded(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill, radius=22, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def wrap_pixels(draw: ImageDraw.ImageDraw, text: str, use_font, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if current and draw.textbbox((0, 0), candidate, font=use_font)[2] > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def draw_paragraph(draw: ImageDraw.ImageDraw, text: str, xy: tuple[int, int], use_font, color, width: int, leading: int = 12) -> int:
    x, y = xy
    line_h = use_font.size + leading
    for line in wrap_pixels(draw, text, use_font, width):
        draw.text((x, y), line, font=use_font, fill=color)
        y += line_h
    return y


def base_scene(scene: Scene, index: int) -> Image.Image:
    im = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(im)
    draw.ellipse((1450, -480, 2220, 300), fill=(23, 28, 54))
    draw.ellipse((-430, 800, 260, 1490), fill=(19, 26, 47))
    draw.rectangle((0, 0, WIDTH, 7), fill=PURPLE)
    draw.text((72, 38), "KNOWSPHERE", font=font(22, True), fill=WHITE)
    draw.text((218, 45), "AI", font=font(17, True), fill=PURPLE)
    draw.text((WIDTH - 238, 45), f"PRODUCT TOUR  ·  {index + 1:02d}/{len(SCENES):02d}", font=font(15, True), fill=MUTED)
    draw.line((72, 90, WIDTH - 72, 90), fill=(46, 53, 78), width=2)
    return im


def add_header(draw: ImageDraw.ImageDraw, scene: Scene, y=122, title_size=42):
    draw.text((72, y), scene.eyebrow, font=font(17, True), fill=CYAN)
    title_y = y + 32
    for line in scene.title.split("\n"):
        draw.text((72, title_y), line, font=font(title_size, True), fill=WHITE)
        title_y += title_size + 5


def screenshot_panel(im: Image.Image, filename: str):
    draw = ImageDraw.Draw(im)
    x, y, max_w, max_h = 72, 245, 1345, 727
    src = Image.open(CAPTURES / filename).convert("RGB")
    shot = ImageOps.contain(src, (max_w, max_h), method=Image.Resampling.LANCZOS)
    sx = x + (max_w - shot.width) // 2
    sy = y + (max_h - shot.height) // 2
    draw.rounded_rectangle((x - 9, y - 9, x + max_w + 9, y + max_h + 9), radius=18, fill=(31, 37, 60), outline=(57, 66, 100), width=2)
    mask = Image.new("L", shot.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, shot.width - 1, shot.height - 1), radius=12, fill=255)
    im.paste(shot, (sx, sy), mask)


def side_panel(im: Image.Image, scene: Scene):
    draw = ImageDraw.Draw(im)
    x, y, w, h = 1450, 245, 398, 727
    rounded(draw, (x, y, x + w, y + h), BG2, 22, outline=(51, 61, 92), width=2)
    draw.text((x + 26, y + 27), "WHAT TO NOTICE", font=font(15, True), fill=CYAN)
    cy = y + 75
    for point in scene.points:
        draw.ellipse((x + 27, cy + 7, x + 38, cy + 18), fill=PURPLE)
        cy = draw_paragraph(draw, point, (x + 52, cy), font(22), WHITE, w - 80, 8) + 23
    if scene.image and "assistant" in scene.image:
        rounded(draw, (x + 22, y + h - 105, x + w - 22, y + h - 28), (43, 34, 68), 12, outline=(92, 70, 138), width=1)
        draw.text((x + 37, y + h - 85), "SAMPLE RESPONSE FOR VIDEO", font=font(14, True), fill=(215, 195, 255))
        draw.text((x + 37, y + h - 59), "Not a live Gemini call", font=font(15), fill=MUTED)


def draw_difference(im: Image.Image, scene: Scene):
    draw = ImageDraw.Draw(im)
    add_header(draw, scene, y=142, title_size=41)
    top, card_h, card_w = 316, 440, 795
    boxes = [(72, top, 72 + card_w, top + card_h), (1053, top, 1053 + card_w, top + card_h)]
    for box in boxes:
        rounded(draw, box, BG2, 24, outline=(55, 64, 97), width=2)
    x1, x2 = 108, 1089
    draw.text((x1, top + 28), "FOUNDATION MODEL", font=font(16, True), fill=CYAN)
    draw.text((x1, top + 66), "Gemini", font=font(42, True), fill=WHITE)
    draw.text((x1, top + 126), "Embeddings + response generation", font=font(23), fill=MUTED)
    draw.line((x1, top + 183, x1 + 690, top + 183), fill=(55, 64, 97), width=2)
    draw_paragraph(draw, "The language model provides the underlying semantic and answer-generation capability.", (x1, top + 212), font(26), WHITE, 650, 12)
    draw.text((x2, top + 28), "KNOWSPHERE PRODUCT LAYER", font=font(16, True), fill=GREEN)
    draw.text((x2, top + 66), "Your knowledge workflow", font=font(36, True), fill=WHITE)
    items = ["Role and department checks before retrieval", "Answers tied to authorized source passages", "Citations and organization audit events"]
    yy = top + 144
    for item in items:
        draw.ellipse((x2, yy + 7, x2 + 12, yy + 19), fill=PURPLE)
        yy = draw_paragraph(draw, item, (x2 + 25, yy), font(23), WHITE, 680, 9) + 22
    rounded(draw, (72, 805, 1848, 938), (25, 31, 53), 18, outline=(55, 64, 97), width=2)
    draw.text((105, 830), "Comparison", font=font(17, True), fill=CYAN)
    draw_paragraph(draw, "A generic chat interface can answer prompts. KnowSphere adds organization-specific retrieval permissions, source visibility, and governance around the current Gemini model service.", (105, 868), font(22), WHITE, 1670, 8)


def draw_pricing(im: Image.Image, scene: Scene):
    draw = ImageDraw.Draw(im)
    add_header(draw, scene, y=130, title_size=43)
    draw.text((74, 224), "Rates supplied for this project · Team and Business share the same prices", font=font(23), fill=MUTED)
    x0, y0, gap, w, h = 90, 315, 28, 556, 545
    cards = [(x0, "TEAM", "₹7,999", "₹14,999", "₹21,999", PURPLE), (x0 + w + gap, "BUSINESS", "₹7,999", "₹14,999", "₹21,999", CYAN), (x0 + 2 * (w + gap), "ENTERPRISE", "Custom", "Custom", "Custom", (244, 184, 93))]
    for x, name, m, q, y, accent in cards:
        rounded(draw, (x, y0, x + w, y0 + h), BG2, 24, outline=(83, 92, 125) if name == "BUSINESS" else (50, 59, 87), width=3 if name == "BUSINESS" else 2)
        draw.text((x + 30, y0 + 30), name, font=font(19, True), fill=accent)
        draw.text((x + 30, y0 + 84), "Billing period", font=font(18), fill=MUTED)
        for i, (label, value) in enumerate((("Monthly", m), ("Quarterly", q), ("Yearly", y))):
            yy = y0 + 140 + i * 105
            draw.line((x + 30, yy, x + w - 30, yy), fill=(52, 62, 92), width=1)
            draw.text((x + 30, yy + 22), label, font=font(23), fill=MUTED)
            vf = font(31, True) if value != "Custom" else font(27, True)
            draw.text((x + w - 30 - draw.textbbox((0, 0), value, font=vf)[2], yy + 16), value, font=vf, fill=WHITE)
        if name == "BUSINESS":
            rounded(draw, (x + 28, y0 + h - 83, x + w - 28, y0 + h - 30), (37, 54, 76), 14)
            draw.text((x + 48, y0 + h - 69), "RECOMMENDED IN REFERENCE", font=font(14, True), fill=CYAN)
        elif name == "ENTERPRISE":
            draw.text((x + 30, y0 + h - 63), "Scope-based contract", font=font(17), fill=MUTED)
        else:
            draw.text((x + 30, y0 + h - 63), "For a first team or pilot", font=font(17), fill=MUTED)
    rounded(draw, (90, 899, 1830, 961), (42, 33, 55), 15, outline=(103, 73, 128), width=1)
    draw.text((118, 916), "Roadmap note", font=font(15, True), fill=(220, 194, 255))
    draw.text((280, 916), "Connector sync, SSO, and advanced observability shown in the reference are not live in this MVP.", font=font(17), fill=WHITE)


def draw_generic(im: Image.Image, scene: Scene, index: int):
    draw = ImageDraw.Draw(im)
    if scene.kind == "title":
        add_header(draw, scene, y=178, title_size=58)
        draw.text((76, 410), "Find answers in your organization's knowledge,", font=font(32), fill=MUTED)
        draw.text((76, 457), "with sources people can follow.", font=font(32), fill=MUTED)
        cards = [("ROLE-AWARE", "Access follows workspace role"), ("SOURCE-BACKED", "See where answers came from"), ("AUDITABLE", "Keep a record of key events")]
        for i, (tag, desc) in enumerate(cards):
            x = 76 + i * 590
            rounded(draw, (x, 650, x + 548, 815), BG2, 20, outline=(52, 62, 94), width=2)
            draw.text((x + 28, 682), tag, font=font(17, True), fill=(CYAN, PURPLE, GREEN)[i])
            draw_paragraph(draw, desc, (x + 28, 723), font(23), WHITE, 480, 8)
    elif scene.kind == "difference":
        draw_difference(im, scene)
    elif scene.kind == "pricing":
        draw_pricing(im, scene)
    elif scene.kind == "outro":
        add_header(draw, scene, y=142, title_size=48)
        rounded(draw, (95, 360, 1825, 795), BG2, 32, outline=(60, 70, 103), width=2)
        draw.text((150, 420), "Permission-aware retrieval", font=font(34, True), fill=WHITE)
        draw.text((150, 500), "Citations that lead back to a source", font=font(34, True), fill=WHITE)
        draw.text((150, 580), "Governance built into the workspace", font=font(34, True), fill=WHITE)
        draw.text((150, 700), "KNOWSPHERE AI  ·  KNOWLEDGE THAT KNOWS ITS SOURCE", font=font(22, True), fill=PURPLE)


def render(scene: Scene, index: int) -> Image.Image:
    im = base_scene(scene, index)
    if scene.kind == "difference":
        draw_generic(im, scene, index)
    elif scene.image:
        add_header(ImageDraw.Draw(im), scene, y=123, title_size=39)
        screenshot_panel(im, scene.image)
        side_panel(im, scene)
    else:
        draw_generic(im, scene, index)
    draw = ImageDraw.Draw(im)
    rounded(draw, (72, 990, 1848, 1053), (27, 33, 55), 14, outline=(50, 59, 88), width=1)
    draw.text((96, 1007), scene.caption, font=font(20, True), fill=WHITE)
    return im


def make_narration(track: Path) -> list[float]:
    truststore.inject_into_ssl()
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    mp3_path = track.with_suffix(".mp3")
    full_text = "\n\n".join(scene.narration for scene in SCENES)
    boundaries: list[dict[str, object]] = []

    async def synthesize():
        communicate = edge_tts.Communicate(
            full_text,
            voice="en-IN-PrabhatNeural",
            rate="+8%",
            boundary="SentenceBoundary",
        )
        with mp3_path.open("wb") as audio:
            async for message in communicate.stream():
                if message["type"] == "audio":
                    audio.write(message["data"])
                elif message["type"] == "SentenceBoundary":
                    boundaries.append(message)

    asyncio.run(synthesize())
    subprocess.run(
        [ffmpeg, "-y", "-i", str(mp3_path), "-ac", "1", "-ar", "22050", str(track)],
        check=True,
        capture_output=True,
        text=True,
    )
    with wave.open(str(track), "rb") as wav:
        audio_duration = wav.getnframes() / wav.getframerate()

    def normalize(value: str) -> str:
        return " ".join("".join(char.lower() if char.isalnum() else " " for char in value).split())

    starts: list[float] = []
    boundary_index = 0
    for scene in SCENES:
        expected = " ".join(normalize(scene.narration).split()[:5])
        found = None
        while boundary_index < len(boundaries):
            item = boundaries[boundary_index]
            boundary_index += 1
            if normalize(str(item["text"])).startswith(expected):
                found = float(item["offset"]) / 10_000_000
                break
        starts.append(found if found is not None else -1.0)

    if all(start >= 0 for start in starts):
        durations = [
            (starts[index + 1] if index + 1 < len(starts) else audio_duration) - start
            for index, start in enumerate(starts)
        ]
        if all(duration > 0 for duration in durations):
            return durations
    weights = [max(1, len(scene.narration.split())) for scene in SCENES]
    total = sum(weights)
    return [audio_duration * weight / total for weight in weights]


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    script_path = OUTPUT.parent / "voiceover-script.md"
    script_path.write_text(
        "# KnowSphere AI product tour voiceover\n\n"
        + "\n\n".join(
            f"## {index + 1}. {scene.title.replace(chr(10), ' ')}\n\n{scene.narration}"
            for index, scene in enumerate(SCENES)
        )
        + "\n",
        encoding="utf-8",
    )
    for scene in SCENES:
        if scene.image and not (CAPTURES / scene.image).exists():
            raise FileNotFoundError(CAPTURES / scene.image)
    with tempfile.TemporaryDirectory(prefix="knowsphere-video-") as temp:
        temp_path = Path(temp)
        slides = []
        for index, scene in enumerate(SCENES):
            slide_path = temp_path / f"slide-{index:02d}.png"
            render(scene, index).save(slide_path, optimize=True)
            slides.append(slide_path)
        audio_track = temp_path / "narration.wav"
        durations = make_narration(audio_track)
        manifest = temp_path / "slides.txt"
        with manifest.open("w", encoding="utf-8") as file:
            for slide, duration in zip(slides, durations):
                file.write(f"file '{slide.as_posix()}'\n")
                file.write(f"duration {duration + 0.28:.3f}\n")
            file.write(f"file '{slides[-1].as_posix()}'\n")
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        command = [
            ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(manifest),
            "-i", str(audio_track), "-vf", "fps=24,format=yuv420p", "-fps_mode", "cfr",
            "-c:v", "libx264", "-preset", "medium", "-crf", "21",
            "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(OUTPUT),
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stderr[-5000:])
    print(f"Created {OUTPUT.relative_to(ROOT)} ({OUTPUT.stat().st_size / 1_000_000:.1f} MB)")


if __name__ == "__main__":
    main()
