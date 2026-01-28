from __future__ import annotations

from pathlib import Path


def _pdf_escape(text: str) -> str:
    return text.replace('\\', r'\\').replace('(', r'\(').replace(')', r'\)')


def make_simple_pdf(lines: list[str]) -> bytes:
    page_w, page_h = 612, 792
    font_obj = 3
    contents_obj = 4

    x0, y0 = 50, page_h - 50
    leading = 14

    content_lines: list[str] = ["BT", "/F1 12 Tf", f"{x0} {y0} Td"]
    for i, line in enumerate(lines):
        if i != 0:
            content_lines.append(f"0 {-leading} Td")
        content_lines.append(f"({_pdf_escape(line)}) Tj")
    content_lines.append("ET")

    stream = ("\n".join(content_lines)).encode("utf-8")

    objects: list[bytes] = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(b"<< /Type /Pages /Kids [5 0 R] /Count 1 >>")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    objects.append(b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream")
    page_dict = (
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_w} {page_h}] "
        f"/Resources << /Font << /F1 {font_obj} 0 R >> >> "
        f"/Contents {contents_obj} 0 R >>"
    ).encode("ascii")
    objects.append(page_dict)

    out = bytearray()
    out.extend(b"%PDF-1.4\n")
    offsets: list[int] = [0]

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
        "Simple Todo List — Requirements Pack (Sample)",
        "",
        "MVP:",
        "- Auth required (signup/login).",
        "- Todo CRUD (title required).",
        "- Mark done / not done.",
        "- Filter by status (done/todo).",
        "",
        "Validation:",
        "- Reject empty title and overly long fields.",
        "- Return friendly 400/404 errors.",
        "",
        "Security:",
        "- User can only access own todos.",
    ]

    pdf_bytes = make_simple_pdf(lines)
    target = Path("samples") / "simple_todo_requirements.pdf"
    target.write_bytes(pdf_bytes)
    print(f"Wrote {target} ({len(pdf_bytes)} bytes)")


if __name__ == "__main__":
    main()
