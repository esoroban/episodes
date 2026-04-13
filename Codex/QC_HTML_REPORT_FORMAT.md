# QC HTML Report Format

## Purpose

This is the user-facing report format for quiz QA.

The report should be:
- a standalone HTML file;
- readable in browser without extra tooling;
- written in Russian;
- convenient for side-by-side reading of drama and QC findings.

## Layout

### Top navigation

The top sticky bar should contain:
- report title;
- episode anchors such as `Эпизод 1`, `Эпизод 2`, `Эпизод 3`.

### Left column

The left column contains:
- the relevant drama text;
- visible section markers like `Драма`, `Софа-блок`, `Испытание`, `Клиффхэнгер`;
- the exact local fragment that is being reviewed.

### Right column

The right column contains:
- overall verdict;
- QC findings in Russian;
- severity;
- drama-integration score `0-3`;
- pass/fix/reject status;
- a traceability table for questions.

## Mandatory evaluation fields

Each reviewed question or block should expose:
- lesson idea;
- expected answer;
- whether the answer is unambiguous;
- drama-integration score `0-3`;
- QC verdict.

## Visual language

Recommended color logic:
- red for blockers;
- amber for major issues;
- blue for minor issues;
- green for accepted strong examples.

## File location

The HTML template lives here:
- [QC_HTML_REPORT_TEMPLATE.html](/Users/iuriinovosolov/Documents/SylaSlovaDramma/Codex/QC_HTML_REPORT_TEMPLATE.html)

Only files inside `Codex` may be edited.
