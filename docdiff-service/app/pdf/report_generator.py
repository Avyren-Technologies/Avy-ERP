import logging
import os
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("docdiff.pdf")


def generate_report_html(
    job_data: dict[str, Any],
    differences: list[dict[str, Any]],
    documents: dict[str, Any],
) -> str:
    """Generate a full HTML report for a comparison job."""

    label_a = documents.get("label_a", "Version A")
    label_b = documents.get("label_b", "Version B")
    model_provider = job_data.get("model_provider", "")
    model_name = job_data.get("model_name", "")
    processing_time_ms = job_data.get("processing_time_ms")
    generated_at = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    is_partial = job_data.get("is_partial", False)

    # Categorise differences
    material = [d for d in differences if d.get("significance") == "material"]
    substantive = [d for d in differences if d.get("significance") == "substantive"]
    cosmetic = [d for d in differences if d.get("significance") == "cosmetic"]
    flagged = [d for d in differences if d.get("verification_status") == "flagged"]
    dismissed = [d for d in differences if d.get("verification_status") == "dismissed"]
    unresolved = [d for d in differences if d.get("needs_verification") and d.get("verification_status") == "pending"]

    total = len(differences)
    verdict = _build_verdict(material, substantive, cosmetic, is_partial)

    processing_str = (
        f"{processing_time_ms / 1000:.1f}s" if processing_time_ms else "N/A"
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>DocDiff Report — {label_a} vs {label_b}</title>
<style>
  body {{ font-family: Arial, sans-serif; font-size: 13px; color: #1a1a1a; margin: 0; padding: 24px; }}
  h1 {{ font-size: 20px; margin-bottom: 4px; }}
  h2 {{ font-size: 15px; margin-top: 28px; margin-bottom: 8px; border-bottom: 1px solid #ddd; padding-bottom: 4px; }}
  h3 {{ font-size: 13px; margin-top: 14px; margin-bottom: 4px; }}
  .header {{ background: #f4f4f8; border-radius: 6px; padding: 16px 20px; margin-bottom: 20px; }}
  .header-meta {{ color: #555; font-size: 12px; margin-top: 6px; }}
  .verdict {{ font-size: 14px; font-weight: 600; padding: 10px 14px; border-left: 4px solid #3b82f6; background: #eff6ff; border-radius: 4px; margin-bottom: 12px; }}
  .verdict.material {{ border-color: #ef4444; background: #fef2f2; }}
  .verdict.clean {{ border-color: #22c55e; background: #f0fdf4; }}
  .stats-row {{ display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }}
  .stat-box {{ background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; padding: 10px 16px; min-width: 110px; text-align: center; }}
  .stat-box .num {{ font-size: 22px; font-weight: 700; }}
  .stat-box .lbl {{ font-size: 11px; color: #6b7280; margin-top: 2px; }}
  .stat-box.material .num {{ color: #ef4444; }}
  .stat-box.substantive .num {{ color: #f59e0b; }}
  .stat-box.cosmetic .num {{ color: #6b7280; }}
  table.diff-table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 16px; }}
  table.diff-table th {{ background: #f3f4f6; text-align: left; padding: 6px 8px; border: 1px solid #e5e7eb; }}
  table.diff-table td {{ padding: 6px 8px; border: 1px solid #e5e7eb; vertical-align: top; }}
  table.diff-table tr:nth-child(even) {{ background: #fafafa; }}
  .badge {{ display: inline-block; padding: 2px 6px; border-radius: 10px; font-size: 10px; font-weight: 600; }}
  .badge.material {{ background: #fee2e2; color: #b91c1c; }}
  .badge.substantive {{ background: #fef3c7; color: #b45309; }}
  .badge.cosmetic {{ background: #f3f4f6; color: #374151; }}
  .badge.confirmed {{ background: #d1fae5; color: #065f46; }}
  .badge.pending {{ background: #e0f2fe; color: #0369a1; }}
  .badge.dismissed {{ background: #f3f4f6; color: #6b7280; }}
  .badge.flagged {{ background: #fce7f3; color: #9d174d; }}
  .badge.corrected {{ background: #ede9fe; color: #5b21b6; }}
  .section {{ margin-bottom: 24px; }}
  .partial-notice {{ background: #fffbeb; border: 1px solid #fbbf24; padding: 8px 12px; border-radius: 4px; font-size: 12px; color: #92400e; margin-bottom: 16px; }}
  del {{ background: #fee2e2; text-decoration: line-through; }}
  ins {{ background: #d1fae5; text-decoration: none; }}
  .comment {{ font-style: italic; color: #6b7280; font-size: 11px; }}
  footer {{ margin-top: 32px; font-size: 11px; color: #9ca3af; border-top: 1px solid #e5e7eb; padding-top: 10px; }}
</style>
</head>
<body>

<div class="header">
  <h1>DocDiff Comparison Report</h1>
  <div class="header-meta">
    <strong>Version A:</strong> {_escape(label_a)} &nbsp;|&nbsp;
    <strong>Version B:</strong> {_escape(label_b)}
  </div>
  <div class="header-meta">
    <strong>Model:</strong> {_escape(model_provider)} / {_escape(model_name)} &nbsp;|&nbsp;
    <strong>Processing time:</strong> {processing_str} &nbsp;|&nbsp;
    <strong>Generated:</strong> {generated_at}
  </div>
</div>
"""

    if is_partial:
        html += '<div class="partial-notice">&#9888; This is a <strong>partial report</strong> — verification is still in progress.</div>\n'

    # --- Executive Summary ---
    html += '<div class="section">\n<h2>Executive Summary</h2>\n'
    verdict_cls = "material" if material else ("clean" if total == 0 else "")
    html += f'<div class="verdict {verdict_cls}">{_escape(verdict)}</div>\n'
    html += '<div class="stats-row">\n'
    html += _stat_box(str(total), "Total Differences", "")
    html += _stat_box(str(len(material)), "Material", "material")
    html += _stat_box(str(len(substantive)), "Substantive", "substantive")
    html += _stat_box(str(len(cosmetic)), "Cosmetic", "cosmetic")
    html += _stat_box(str(len(dismissed)), "Dismissed", "")
    html += _stat_box(str(len(flagged)), "Flagged", "")
    html += '</div>\n</div>\n'

    # --- Quick Reference Table (material + substantive) ---
    quick_list = material + substantive
    if quick_list:
        html += '<div class="section">\n<h2>Quick Reference — Material &amp; Substantive Differences</h2>\n'
        html += _render_compact_table(quick_list)
        html += '</div>\n'

    # --- Material Differences ---
    if material:
        html += '<div class="section">\n<h2>Material Differences</h2>\n'
        html += _render_full_table(material)
        html += '</div>\n'

    # --- Substantive Differences ---
    if substantive:
        html += '<div class="section">\n<h2>Substantive Differences</h2>\n'
        html += _render_full_table(substantive)
        html += '</div>\n'

    # --- Cosmetic Differences ---
    if cosmetic:
        html += '<div class="section">\n<h2>Cosmetic Differences</h2>\n'
        html += _render_full_table(cosmetic)
        html += '</div>\n'

    # --- Flagged Items ---
    if flagged:
        html += '<div class="section">\n<h2>Flagged Items</h2>\n'
        html += _render_flagged_table(flagged)
        html += '</div>\n'

    # --- Dismissed ---
    if dismissed:
        html += f'<div class="section">\n<h2>Dismissed Differences</h2>\n'
        html += f'<p>{len(dismissed)} difference(s) were dismissed by the reviewer.</p>\n'
        html += '</div>\n'

    # --- Unresolved Regions ---
    if unresolved:
        html += '<div class="section">\n<h2>Unresolved Regions</h2>\n'
        html += f'<p>{len(unresolved)} difference(s) require manual verification.</p>\n'
        html += _render_full_table(unresolved)
        html += '</div>\n'

    html += '<footer>Generated by DocDiff Pro &mdash; Avyren Technologies</footer>\n'
    html += '</body>\n</html>\n'
    return html


def _build_verdict(
    material: list,
    substantive: list,
    cosmetic: list,
    is_partial: bool,
) -> str:
    prefix = "[PARTIAL] " if is_partial else ""
    if not material and not substantive and not cosmetic:
        return f"{prefix}No differences detected — documents appear identical."
    if material:
        return (
            f"{prefix}{len(material)} material difference(s) found — "
            "documents contain substantively different content requiring review."
        )
    if substantive:
        return (
            f"{prefix}{len(substantive)} substantive difference(s) found — "
            "documents differ in meaningful ways with no material impact."
        )
    return (
        f"{prefix}{len(cosmetic)} cosmetic difference(s) only — "
        "documents are functionally equivalent."
    )


def _stat_box(value: str, label: str, css_class: str) -> str:
    cls = f' {css_class}' if css_class else ''
    return (
        f'<div class="stat-box{cls}">'
        f'<div class="num">{value}</div>'
        f'<div class="lbl">{_escape(label)}</div>'
        f'</div>\n'
    )


def _render_compact_table(differences: list[dict]) -> str:
    html = (
        '<table class="diff-table">\n'
        '<thead><tr>'
        '<th>#</th><th>Type</th><th>Significance</th>'
        '<th>Page (A / B)</th><th>Summary</th><th>Status</th>'
        '</tr></thead>\n<tbody>\n'
    )
    for d in differences:
        html += (
            f'<tr>'
            f'<td>{d.get("difference_number", "")}</td>'
            f'<td>{_escape(d.get("difference_type", ""))}</td>'
            f'<td>{_significance_badge(d.get("significance", ""))}</td>'
            f'<td>{d.get("page_version_a", "—")} / {d.get("page_version_b", "—")}</td>'
            f'<td>{_escape(d.get("summary", ""))}</td>'
            f'<td>{_status_badge(d.get("verification_status", "pending"))}</td>'
            f'</tr>\n'
        )
    html += '</tbody>\n</table>\n'
    return html


def _render_full_table(differences: list[dict]) -> str:
    html = (
        '<table class="diff-table">\n'
        '<thead><tr>'
        '<th>#</th><th>Type</th><th>Significance</th>'
        '<th>Page A</th><th>Page B</th>'
        '<th>Before</th><th>After</th><th>Summary</th><th>Status</th>'
        '</tr></thead>\n<tbody>\n'
    )
    for d in differences:
        val_before = _escape(str(d.get("value_before") or ""))
        val_after = _escape(str(d.get("value_after") or ""))
        html += (
            f'<tr>'
            f'<td>{d.get("difference_number", "")}</td>'
            f'<td>{_escape(d.get("difference_type", ""))}</td>'
            f'<td>{_significance_badge(d.get("significance", ""))}</td>'
            f'<td>{d.get("page_version_a") or "—"}</td>'
            f'<td>{d.get("page_version_b") or "—"}</td>'
            f'<td><del>{val_before}</del></td>'
            f'<td><ins>{val_after}</ins></td>'
            f'<td>{_escape(d.get("summary", ""))}</td>'
            f'<td>{_status_badge(d.get("verification_status", "pending"))}</td>'
            f'</tr>\n'
        )
        comment = d.get("verifier_comment") or d.get("corrected_description")
        if comment:
            html += (
                f'<tr><td colspan="9" class="comment">'
                f'Reviewer note: {_escape(comment)}'
                f'</td></tr>\n'
            )
    html += '</tbody>\n</table>\n'
    return html


def _render_flagged_table(differences: list[dict]) -> str:
    html = (
        '<table class="diff-table">\n'
        '<thead><tr>'
        '<th>#</th><th>Type</th><th>Summary</th><th>Reviewer Comment</th>'
        '</tr></thead>\n<tbody>\n'
    )
    for d in differences:
        comment = d.get("verifier_comment") or ""
        html += (
            f'<tr>'
            f'<td>{d.get("difference_number", "")}</td>'
            f'<td>{_escape(d.get("difference_type", ""))}</td>'
            f'<td>{_escape(d.get("summary", ""))}</td>'
            f'<td>{_escape(comment)}</td>'
            f'</tr>\n'
        )
    html += '</tbody>\n</table>\n'
    return html


def _significance_badge(sig: str) -> str:
    return f'<span class="badge {sig}">{_escape(sig)}</span>'


def _status_badge(status: str) -> str:
    return f'<span class="badge {status}">{_escape(status)}</span>'


def _escape(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def html_to_pdf(html: str, output_path: str) -> str:
    """Convert HTML string to a PDF file using WeasyPrint."""
    try:
        from weasyprint import HTML as WeasyprintHTML  # type: ignore

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        WeasyprintHTML(string=html).write_pdf(output_path)
        logger.info(f"PDF written to {output_path}")
        return output_path
    except ImportError:
        logger.error(
            "WeasyPrint is not installed. "
            "Install it with: pip install weasyprint"
        )
        raise RuntimeError(
            "PDF generation requires WeasyPrint. "
            "Install system libs and run: pip install weasyprint"
        )
    except Exception as exc:
        logger.exception(f"PDF generation failed: {exc}")
        raise
