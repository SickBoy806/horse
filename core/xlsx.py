"""Minimal dependency-free .xlsx writer (Office Open XML via zipfile).

Supports several sheets, a bold frozen header row, numbers as real numeric cells, and column widths
sized to content. Enough for clean report exports without adding openpyxl.
"""
import io
import zipfile
from datetime import date, datetime
from decimal import Decimal
from xml.sax.saxutils import escape


def _col(n):
    """0-based column index -> Excel letters (0 -> A, 26 -> AA)."""
    letters = ''
    n += 1
    while n:
        n, rem = divmod(n - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


def _clean(text):
    # Strip characters XML 1.0 forbids (control chars other than tab/newline/CR).
    return ''.join(ch for ch in text if ch in '\t\n\r' or ord(ch) >= 32)


def _cell(ref, value, style=0):
    s = f' s="{style}"' if style else ''
    if value is None or value == '':
        return f'<c r="{ref}"{s}/>'
    if isinstance(value, bool):
        value = 'Yes' if value else 'No'
    if isinstance(value, Decimal):
        value = format(value.normalize(), 'f')  # 2.500 -> 2.5, never scientific notation
        return f'<c r="{ref}"{s}><v>{value}</v></c>'
    if isinstance(value, (int, float)):
        return f'<c r="{ref}"{s}><v>{value}</v></c>'
    if isinstance(value, datetime):
        value = value.strftime('%Y-%m-%d %H:%M')
    elif isinstance(value, date):
        value = value.strftime('%Y-%m-%d')
    text = escape(_clean(str(value)))
    return f'<c r="{ref}" t="inlineStr"{s}><is><t xml:space="preserve">{text}</t></is></c>'


def _sheet_xml(headers, rows):
    widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, v in enumerate(row[:len(widths)]):
            widths[i] = max(widths[i], min(len(str(v if v is not None else '')), 60))
    cols = ''.join(f'<col min="{i + 1}" max="{i + 1}" width="{w + 3}" customWidth="1"/>' for i, w in enumerate(widths))
    out = [f'<row r="1">{"".join(_cell(f"{_col(i)}1", h, style=1) for i, h in enumerate(headers))}</row>']
    for r, row in enumerate(rows, start=2):
        out.append(f'<row r="{r}">{"".join(_cell(f"{_col(i)}{r}", v) for i, v in enumerate(row))}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
        '</sheetView></sheetViews>'
        f'<cols>{cols}</cols><sheetData>{"".join(out)}</sheetData></worksheet>'
    ) if headers else (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData/></worksheet>'
    )


def build_workbook(sheets):
    """sheets: iterable of (name, headers, rows). Returns the .xlsx file as bytes."""
    sheets = list(sheets) or [('Sheet1', [], [])]
    names, used = [], set()
    for name, _, _ in sheets:
        base = ''.join(ch for ch in str(name) if ch not in '[]:*?/\\')[:31] or 'Sheet'
        candidate, n = base, 2
        while candidate.lower() in used:
            candidate = f'{base[:28]}~{n}'
            n += 1
        used.add(candidate.lower())
        names.append(candidate)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml',
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                   '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
                   + ''.join(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                             for i in range(1, len(sheets) + 1))
                   + '</Types>')
        z.writestr('_rels/.rels',
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
                   '</Relationships>')
        z.writestr('xl/workbook.xml',
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                   'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
                   + ''.join(f'<sheet name="{escape(n)}" sheetId="{i}" r:id="rId{i}"/>' for i, n in enumerate(names, 1))
                   + '</sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels',
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   + ''.join(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>'
                             for i in range(1, len(sheets) + 1))
                   + f'<Relationship Id="rId{len(sheets) + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
                   '</Relationships>')
        z.writestr('xl/styles.xml',
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                   '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font>'
                   '<font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font></fonts>'
                   '<fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill>'
                   '<fill><patternFill patternType="solid"><fgColor rgb="FF10284D"/><bgColor indexed="64"/></patternFill></fill></fills>'
                   '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
                   '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
                   '<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
                   '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/></cellXfs>'
                   '</styleSheet>')
        for i, (_, headers, rows) in enumerate(sheets, 1):
            z.writestr(f'xl/worksheets/sheet{i}.xml', _sheet_xml(list(headers), [list(r) for r in rows]))
    return buf.getvalue()
