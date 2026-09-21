"""Rebuild the four-slide class deck so it survives a four-minute presentation.

The generated first pass had the right words in the wrong shape: every line sat
at bullet level zero, so section labels like "Problem" looked identical to the
sentences underneath them, and slide one ran thirteen equal-weight lines. This
module rewrites each slide body with a real two-level hierarchy, fixed font
sizes so nothing autoshrinks to unreadable, a Monte Carlo chart on the risk
slide, footers, and speaker notes carrying a per-slide time budget.

The assignment caps the deck at four slides and four minutes, and expects every
team member to speak, so the notes allocate both.

Run:
    python -m tools.polish_slides
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.util import Emu, Pt

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHART_PATH = (
    PROJECT_ROOT / "analysis" / "outputs" / "monte_carlo_cost_presentation.png"
)

SJSU_BLUE = RGBColor(0x00, 0x55, 0xA2)
SJSU_GOLD = RGBColor(0xE5, 0xA4, 0x22)
INK = RGBColor(0x1A, 0x1A, 0x1A)
SLATE = RGBColor(0x40, 0x40, 0x40)
GO_GREEN = RGBColor(0x1E, 0x6F, 0x45)

FOOTER_SIZE = Pt(9)

# Text-only slides get larger type; the risk slide gives up a third of its width
# to a chart, so its narrower column needs to step down a size.
FULL_WIDTH_SIZES = (Pt(18), Pt(14.5))
WITH_CHART_SIZES = (Pt(16), Pt(13))

# Vertical layout, measured from the top of the slide.
TITLE_TOP = Pt(26)
TITLE_HEIGHT = Pt(46)
ACCENT_BAR_TOP = Pt(78)
BODY_TOP = Pt(94)
FOOTER_HEIGHT = Pt(40)
SIDE_MARGIN = Pt(38)


@dataclass
class Section:
    """A bold label plus the lines that sit underneath it."""

    label: str
    details: list[str] = field(default_factory=list)
    accent: RGBColor | None = None


@dataclass
class SlidePlan:
    title: str
    sections: list[Section]
    notes: str
    image: Path | None = None
    # Fraction of the body width to leave free when an image is present.
    image_fraction: float = 0.40
    # Optional tinted band at the foot of the slide, used on the slides whose
    # outline leaves obvious dead space.
    callout: str | None = None

    @property
    def sizes(self) -> tuple[Pt, Pt]:
        return WITH_CHART_SIZES if self.image else FULL_WIDTH_SIZES


def build_plans() -> list[SlidePlan]:
    """The deck content, in the four titles the assignment prescribes."""
    return [
        SlidePlan(
            title="What Did We Build and Why?",
            sections=[
                Section(
                    "Problem",
                    [
                        "Campus tech requests live in a shared inbox and three "
                        "departmental spreadsheets.",
                        "No named owner, no support-hour SLA clock, and no number "
                        "the monthly service review can defend.",
                    ],
                ),
                Section(
                    "Customer / user",
                    [
                        "Faculty mid-lecture, students locked out of Canvas or "
                        "eduroam, and CTS agents who triage by scrolling.",
                    ],
                ),
                Section(
                    "Strategic value",
                    [
                        "CTS is funded on measurable service quality: one intake "
                        "path, one queue, one clock, one dashboard.",
                    ],
                ),
                Section(
                    "Working prototype \u2014 four interactions, not a platform",
                    [
                        "Submit a ticket \u2192 SLA target and a tracking number",
                        "Work the queue \u2192 search, filter, assign, work notes, "
                        "audit trail",
                        "Support-hour SLA clock \u2014 weekdays 08:00\u201318:00, not "
                        "calendar hours",
                        "Dashboard and CSV export for the monthly service review",
                    ],
                ),
            ],
            callout=(
                "The prototype works. The question we brought to management is "
                "not \u201ccan we build it\u201d \u2014 it is whether CTS should "
                "keep investing, and whether it can execute."
            ),
            notes=(
                "TIME: 0:00-1:00 (60 seconds). SPEAKER: [member 1].\n\n"
                "Open with the concrete story, not the architecture: a projector "
                "dies in BBC 202, the faculty member emails a shared inbox, and "
                "nobody owns the request.\n\n"
                "Land one sentence on strategy: CTS is funded on service quality, "
                "so a queue with a defensible SLA number IS the strategy, not a "
                "tool purchase.\n\n"
                "Do NOT demo here. The Loom covers the product. Name the four "
                "interactions and move on.\n\n"
                "Likely question: why not just buy ServiceNow? Answer: that is "
                "exactly the decision tree on slide 3, and it loses on EMV."
            ),
        ),
        SlidePlan(
            title="How Did We Execute?",
            sections=[
                Section(
                    "Team and structure",
                    [
                        "Matrix, not projectized \u2014 CTS cannot pull a dedicated "
                        "unit for a year without hollowing out the desk.",
                        "Hybrid, on campus two days a week; classroom tickets need "
                        "walk-up empathy.",
                        "Lanes are written down: service owner owns requirements, "
                        "tech lead owns how, PM owns the date and the scope cut.",
                    ],
                ),
                Section(
                    "Leadership",
                    [
                        "Facilitative, with a spine. Disagreements go on a decision "
                        "log within 24 hours, then to the CTS Director.",
                    ],
                ),
                Section(
                    "The conflict that mattered",
                    [
                        "Agents wanted a seven-field classroom form. Faculty will "
                        "not fill that in while forty students wait.",
                        "Neither side won: submit stays 30 seconds, agents complete "
                        "podium ID and CRN at triage.",
                    ],
                ),
                Section(
                    "Vibe-coding lesson",
                    [
                        "We thought the intake form was the project. The SLA clock "
                        "was the project.",
                        "AI wrote page chrome and seed data well; it froze "
                        "resolved_at on reopen, and tests caught it.",
                        "Humans made the calls: support hours over calendar hours, "
                        "and no unqualified GO.",
                    ],
                ),
            ],
            notes=(
                "TIME: 1:00-2:00 (60 seconds). SPEAKER: [member 2].\n\n"
                "This slide is about process management, not code. Spend your "
                "words on the conflict and the vibe-coding lesson; the structure "
                "bullets are for the reader, not the talk.\n\n"
                "The conflict is the strongest 15 seconds in the deck because "
                "nobody was declared the winner. Say explicitly that we separated "
                "SUBMIT from TRIAGE, which is a negotiation outcome, not a "
                "compromise that serves neither side.\n\n"
                "For AI: give the one concrete failure. Generated update logic "
                "stamped resolved_at when a ticket closed and never cleared it, so "
                "a reopened ticket froze the SLA clock and the dashboard "
                "under-counted breaches.\n\n"
                "Likely question: did AI write the analysis? Answer: it wrote "
                "structure; we chose every assumption and the recommendation."
            ),
        ),
        SlidePlan(
            title="What Could Go Wrong?",
            image=CHART_PATH,
            sections=[
                Section(
                    "Three largest risks, ranked by exposure",
                    [
                        "R3 Adoption \u2014 $28,500. Inbox culture survives and the "
                        "labor savings never appear.",
                        "R2 Cost and schedule \u2014 $18,900. 44% chance of passing "
                        "the $185K approval ceiling.",
                        "R5 FERPA \u2014 $15,000. Student records sit in ticket "
                        "bodies with no access control yet.",
                    ],
                ),
                Section(
                    "Decision tree: the pilot wins",
                    [
                        "Eight-week paid pilot EMV $98,300, versus build now "
                        "$85,000 and license ITSM $72,750.",
                        "Pilot downside \u2212$46K; build-now downside \u2212$95K.",
                    ],
                ),
                Section(
                    "Monte Carlo, 10,000 trials",
                    [
                        "$179,670 point-estimate NPV \u2192 $54,286 expected NPV; "
                        "P(NPV < 0) = 27.3%.",
                        "Minutes saved and adoption drive NPV \u2014 not engineering "
                        "hours.",
                    ],
                ),
            ],
            notes=(
                "TIME: 2:00-3:00 (60 seconds). SPEAKER: [member 3].\n\n"
                "Do not read the risk register. Give the three risks in six words "
                "each and spend the rest of the minute on the chart.\n\n"
                "The chart is the whole argument: the green dashed line is what we "
                "estimated ($157,760), the red line is what 10,000 trials expect "
                "($183,414), and the dotted line is the money we are actually "
                "approved to spend ($185,000). The gap between green and red is "
                "the planning fallacy with a dollar sign on it.\n\n"
                "Say the decision that changes: budget to the P80 of ~$208,000, "
                "not to the point estimate.\n\n"
                "Then the punchline for slide 4: the two variables that dominate "
                "NPV, minutes saved and adoption, are exactly what a cheap pilot "
                "measures."
            ),
        ),
        SlidePlan(
            title="Should We Continue?",
            sections=[
                Section(
                    "GO WITH CONDITIONS",
                    [
                        "Not GO \u2014 the $179,670 NPV is the mode of our inputs, "
                        "not the mean. Expected NPV is $54,286.",
                        "Not NO-GO \u2014 expected value is still positive, the "
                        "pilot has the best EMV, and learning costs $46K.",
                    ],
                    accent=GO_GREEN,
                ),
                Section(
                    "The conditions, written into the funding memo",
                    [
                        "Eight-week paid pilot in Classroom Technology and Canvas "
                        "support; close the shared inbox for those categories. $46K.",
                        "Role-based access control and a booked FERPA review before "
                        "a single real ticket is accepted.",
                        "Hold capital at the P80 build cost of ~$208K, not the "
                        "$157,760 point estimate.",
                        "Launch scope frozen at four features. No knowledge base, "
                        "no chat, no mobile app.",
                        "Stop gate: intake share under 60% at week eight means the "
                        "full build is not funded.",
                    ],
                ),
            ],
            callout=(
                "We are not asking whether the software works. We are asking "
                "whether CTS will change how it takes a request \u2014 and "
                "$46K answers that before $208K is committed."
            ),
            notes=(
                "TIME: 3:00-4:00 (60 seconds). SPEAKER: [member 4]. If the team "
                "has fewer than four members, split this slide between two "
                "speakers so everyone presents.\n\n"
                "Say the recommendation in the first three seconds, then justify "
                "it. Do not build up to it.\n\n"
                "The framing that earns the marks: we are not asking whether the "
                "software works, we are asking whether CTS will change how it "
                "takes a request. That is a behavior question, and $46,000 answers "
                "it before $208,000 is committed.\n\n"
                "Close on the stop gate and say plainly that stopping at week "
                "eight would be a SUCCESSFUL use of this analysis, not a failed "
                "project. The assignment explicitly rewards that conclusion.\n\n"
                "HARD STOP at 4:00. If you are over, cut the middle three "
                "conditions and keep the pilot and the stop gate."
            ),
        ),
    ]


def body_placeholder(slide):
    """The content placeholder, whichever index the layout happened to use."""
    for shape in slide.placeholders:
        if shape.placeholder_format.idx != 0:
            return shape
    return None


def set_title(slide, text: str, slide_width: int) -> None:
    """Place the title deterministically instead of trusting the layout."""
    if slide.shapes.title is None:
        return
    title = slide.shapes.title
    title.left = SIDE_MARGIN
    title.top = TITLE_TOP
    title.width = Emu(slide_width - 2 * int(SIDE_MARGIN))
    title.height = TITLE_HEIGHT

    frame = title.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.auto_size = MSO_AUTO_SIZE.NONE
    frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    paragraph = frame.paragraphs[0]
    paragraph.alignment = PP_ALIGN.LEFT
    run = paragraph.add_run()
    run.text = text
    run.font.size = Pt(32)
    run.font.bold = True
    run.font.color.rgb = SJSU_BLUE


def fill_body(
    placeholder, sections: list[Section], sizes: tuple[Pt, Pt]
) -> None:
    """Write a two-level outline with explicit sizes so nothing autoshrinks."""
    section_size, detail_size = sizes
    frame = placeholder.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.auto_size = MSO_AUTO_SIZE.NONE
    frame.vertical_anchor = MSO_ANCHOR.TOP

    first = True
    for index, section in enumerate(sections):
        paragraph = frame.paragraphs[0] if first else frame.add_paragraph()
        first = False
        paragraph.level = 0
        paragraph.space_before = Pt(0) if index == 0 else Pt(11)
        paragraph.space_after = Pt(3)
        run = paragraph.add_run()
        run.text = section.label
        run.font.size = section_size
        run.font.bold = True
        run.font.color.rgb = section.accent or SJSU_BLUE

        for detail in section.details:
            child = frame.add_paragraph()
            child.level = 1
            child.space_before = Pt(2)
            child.space_after = Pt(2)
            child_run = child.add_run()
            child_run.text = detail
            child_run.font.size = detail_size
            child_run.font.color.rgb = INK


def add_chart(slide, placeholder, image: Path, fraction: float) -> None:
    """Narrow the text column and drop the chart into the freed space.

    ``Pt`` already returns a length in EMU, so these values are used directly
    rather than scaled.
    """
    if not image.exists():
        return

    original_width = int(placeholder.width)
    gutter = int(Pt(14))
    text_width = int(original_width * (1 - fraction)) - gutter
    placeholder.width = Emu(text_width)

    left = int(placeholder.left) + text_width + gutter
    available_width = original_width - text_width - gutter

    picture = slide.shapes.add_picture(str(image), Emu(left), placeholder.top)
    scale = available_width / picture.width
    picture.width = Emu(int(picture.width * scale))
    picture.height = Emu(int(picture.height * scale))

    caption = slide.shapes.add_textbox(
        Emu(left),
        Emu(int(picture.top) + int(picture.height) + int(Pt(4))),
        Emu(available_width),
        Pt(44),
    )
    frame = caption.text_frame
    frame.word_wrap = True
    paragraph = frame.paragraphs[0]
    run = paragraph.add_run()
    run.text = (
        "Estimate $157,760 \u00b7 expected $183,414 \u00b7 approved ceiling "
        "$185,000 \u00b7 P80 $208,011"
    )
    run.font.size = Pt(9)
    run.font.italic = True
    run.font.color.rgb = SLATE


def add_callout(slide, text: str, slide_width: int, slide_height: int) -> None:
    """A tinted band carrying the one sentence we want the room to remember."""
    from pptx.enum.shapes import MSO_SHAPE

    height = Pt(58)
    top = Emu(slide_height - int(FOOTER_HEIGHT) - int(height) - int(Pt(10)))
    width = Emu(slide_width - 2 * int(SIDE_MARGIN))

    band = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, SIDE_MARGIN, top, width, height)
    band.fill.solid()
    band.fill.fore_color.rgb = RGBColor(0xF2, 0xF5, 0xFA)
    band.line.color.rgb = SJSU_BLUE
    band.line.width = Pt(1)
    band.shadow.inherit = False

    frame = band.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    frame.margin_left = Pt(16)
    frame.margin_right = Pt(16)
    frame.margin_top = Pt(6)
    frame.margin_bottom = Pt(6)
    paragraph = frame.paragraphs[0]
    paragraph.alignment = PP_ALIGN.LEFT
    run = paragraph.add_run()
    run.text = text
    run.font.size = Pt(15)
    run.font.bold = True
    run.font.color.rgb = SJSU_BLUE


def add_footer(slide, index: int, total: int, slide_height: int) -> None:
    box = slide.shapes.add_textbox(
        Pt(36), Emu(slide_height - int(Pt(32))), Pt(520), Pt(16)
    )
    frame = box.text_frame
    paragraph = frame.paragraphs[0]
    run = paragraph.add_run()
    run.text = (
        f"HelpDesk165  \u00b7  CMPE 165 Project 1  \u00b7  "
        f"GO WITH CONDITIONS  \u00b7  {index} / {total}"
    )
    run.font.size = FOOTER_SIZE
    run.font.color.rgb = SLATE
    paragraph.alignment = PP_ALIGN.LEFT


def add_accent_bar(slide, slide_width: int) -> None:
    """A thin gold rule between the title and the body."""
    from pptx.enum.shapes import MSO_SHAPE

    bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        SIDE_MARGIN,
        ACCENT_BAR_TOP,
        Emu(slide_width - 2 * int(SIDE_MARGIN)),
        Pt(2.5),
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = SJSU_GOLD
    bar.line.fill.background()
    bar.shadow.inherit = False


def set_notes(slide, text: str) -> None:
    frame = slide.notes_slide.notes_text_frame
    frame.clear()
    first = True
    for block in text.split("\n\n"):
        paragraph = frame.paragraphs[0] if first else frame.add_paragraph()
        first = False
        run = paragraph.add_run()
        run.text = block
        run.font.size = Pt(11)


def polish(source: Path, destination: Path) -> dict[str, object]:
    presentation = Presentation(str(source))
    plans = build_plans()

    if len(presentation.slides) != len(plans):
        raise ValueError(
            f"Expected {len(plans)} slides to rewrite, found "
            f"{len(presentation.slides)}"
        )

    slide_width = int(presentation.slide_width)
    slide_height = int(presentation.slide_height)

    charts_added = 0
    for index, (slide, plan) in enumerate(
        zip(presentation.slides, plans), start=1
    ):
        set_title(slide, plan.title, slide_width)
        add_accent_bar(slide, slide_width)

        placeholder = body_placeholder(slide)
        if placeholder is None:
            raise ValueError(f"Slide {index} has no content placeholder")

        # Position the body explicitly so the layout's own geometry cannot leave
        # a band of dead space at the bottom of the slide.
        placeholder.left = SIDE_MARGIN
        placeholder.top = BODY_TOP
        placeholder.width = Emu(slide_width - 2 * int(SIDE_MARGIN))
        reserved = int(Pt(76)) if plan.callout else 0
        placeholder.height = Emu(
            slide_height - int(BODY_TOP) - int(FOOTER_HEIGHT) - reserved
        )

        fill_body(placeholder, plan.sections, plan.sizes)
        if plan.image is not None:
            add_chart(slide, placeholder, plan.image, plan.image_fraction)
            charts_added += 1
        if plan.callout:
            add_callout(slide, plan.callout, slide_width, slide_height)

        add_footer(slide, index, len(plans), slide_height)
        set_notes(slide, plan.notes)

    destination.parent.mkdir(parents=True, exist_ok=True)
    presentation.save(str(destination))

    return {
        "slides": len(plans),
        "charts_added": charts_added,
        "bullet_levels": 2,
        "notes_added": len(plans),
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    arguments = parser.parse_args()

    result = polish(arguments.source, arguments.destination)
    print(f"Polished {arguments.source.name} -> {arguments.destination}")
    for key, value in result.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
