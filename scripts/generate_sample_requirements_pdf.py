from __future__ import annotations

from pathlib import Path


def _pdf_escape(text: str) -> str:
    return (
        text.replace('\\', r'\\')
        .replace('(', r'\(')
        .replace(')', r'\)')
    )


def make_simple_pdf(lines: list[str]) -> bytes:
    # Minimal PDF writer: single page, Helvetica, simple text.
    # Reference: PDF 1.4 object structure.

    # Page size: US Letter (612 x 792 points)
    page_w, page_h = 612, 792

    font_obj = 3
    contents_obj = 4

    # Build content stream
    x0, y0 = 50, page_h - 50
    leading = 14

    content_lines: list[str] = [
        "BT",
        f"/{'F1'} 12 Tf",
        f"{x0} {y0} Td",
    ]
    for i, line in enumerate(lines):
        if i != 0:
            content_lines.append(f"0 {-leading} Td")
        content_lines.append(f"({_pdf_escape(line)}) Tj")
    content_lines.append("ET")

    stream = ("\n".join(content_lines)).encode("utf-8")

    # Define PDF objects
    objects: list[bytes] = []

    # 1: Catalog
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")

    # 2: Pages
    objects.append(b"<< /Type /Pages /Kids [5 0 R] /Count 1 >>")

    # 3: Font
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    # 4: Contents
    objects.append(b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream")

    # 5: Page
    page_dict = (
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_w} {page_h}] "
        f"/Resources << /Font << /F1 {font_obj} 0 R >> >> "
        f"/Contents {contents_obj} 0 R >>"
    ).encode("ascii")
    objects.append(page_dict)

    # Assemble file with xref
    out = bytearray()
    out.extend(b"%PDF-1.4\n")

    offsets: list[int] = [0]  # object 0 placeholder

    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out.extend(f"{i} 0 obj\n".encode("ascii"))
        out.extend(obj)
        out.extend(b"\nendobj\n")

    xref_start = len(out)
    out.extend(b"xref\n")
    out.extend(f"0 {len(objects)+1}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.extend(f"{off:010d} 00000 n \n".encode("ascii"))

    out.extend(b"trailer\n")
    out.extend(f"<< /Size {len(objects)+1} /Root 1 0 R >>\n".encode("ascii"))
    out.extend(b"startxref\n")
    out.extend(f"{xref_start}\n".encode("ascii"))
    out.extend(b"%%EOF\n")

    return bytes(out)


def main() -> None:
    lines = [
        "Campus Event Companion — Requirements Pack (Sample)",
        "",
        "Problem: discover campus events + manage RSVPs.",
        "Personas: Student, Organizer.",
        "",
        "MVP Requirements:",
        "1) Auth: signup/login; roles student/organizer.",
        "2) Events: organizers create/edit/cancel; students browse/filter/search.",
        "3) RSVP: RSVP/un-RSVP; enforce capacity if configured.",
        "4) Notifications: reminder 24h before; notify on cancellation.",
        "",
        "Out of scope: payments, comments/likes, mobile app, recommendations.",
        "",
        "Non-functional: JWT authz, input validation, friendly errors.",
        "Edge cases: capacity race, unauthorized edits, invalid date ranges.",
        "",
        "Success metrics: RSVP flow <2 minutes; better organizer engagement.",
    ]

    pdf_bytes = make_simple_pdf(lines)
    target = Path("samples") / "campus_event_companion_requirements.pdf"
    target.write_bytes(pdf_bytes)
    print(f"Wrote {target} ({len(pdf_bytes)} bytes)")


if __name__ == "__main__":
    main()
