#!/usr/bin/env node
/**
 * Fix literal "\\uXXXX" sequences in .ts / .tsx so Unicode characters render correctly.
 *
 * In JSX text, "\\u2014" is NOT interpreted as an escape — it prints six characters.
 * This script replaces literal dash-related escapes with the real Unicode characters.
 *
 * Safety: does NOT replace when the "\\" starting "\\uXXXX" is escaped (preceded by "\\").
 *
 * Scans and fixes ONLY: **.ts** and **.tsx**
 *
 * Usage:
 *   node scripts/fix-literal-unicode-escapes.mjs           # dry-run
 *   node scripts/fix-literal-unicode-escapes.mjs --write
 *
 * Output: unicode-escape-report.json (repo root) — remaining literal \\uXXXX in .ts/.tsx
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, "..");

/** Only these extensions are scanned or modified. */
const EXTENSIONS = new Set([".ts", ".tsx"]);

/**
 * Code points considered "dash / dash-like" punctuation for replacement.
 * (Hyphen/minus family and related horizontal rules used as dashes.)
 */
const DASH_CODEPOINTS = new Set([
    0x002d, // HYPHEN-MINUS
    0x00ad, // SOFT HYPHEN
    0x2010, // HYPHEN
    0x2011, // NON-BREAKING HYPHEN
    0x2012, // FIGURE DASH
    0x2013, // EN DASH
    0x2014, // EM DASH
    0x2015, // HORIZONTAL BAR
    0x2017, // DOUBLE LOW LINE
    0x2043, // HYPHEN BULLET
    0x2212, // MINUS SIGN
    0x2e3a, // TWO-EM DASH
    0x2e3b, // THREE-EM DASH
    0xfe58, // SMALL EM DASH
    0xfe63, // SMALL HYPHEN-MINUS
    0xff0d, // FULLWIDTH HYPHEN-MINUS
    0x301c, // WAVE DASH
    0x3030, // WAVY DASH
]);

const IGNORE_DIR_NAMES = new Set([
    "node_modules",
    ".git",
    "dist",
    "build",
    "coverage",
    ".next",
    ".turbo",
    "ios",
    "android",
]);

const IGNORE_FILE_NAMES = new Set(["pnpm-lock.yaml", "package-lock.json", "yarn.lock"]);

const SCRIPT_SELF = path.join("scripts", "fix-literal-unicode-escapes.mjs");

function shouldSkipDir(name) {
    return IGNORE_DIR_NAMES.has(name) || name.startsWith(".");
}

function isAllowedExtension(filePath) {
    return EXTENSIONS.has(path.extname(filePath));
}

function walk(dir, out = []) {
    let entries;
    try {
        entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch {
        return out;
    }
    for (const ent of entries) {
        const full = path.join(dir, ent.name);
        const rel = path.relative(REPO_ROOT, full);
        if (ent.isDirectory()) {
            if (shouldSkipDir(ent.name)) continue;
            walk(full, out);
        } else if (ent.isFile()) {
            if (IGNORE_FILE_NAMES.has(ent.name)) continue;
            if (rel.replace(/\\/g, "/") === SCRIPT_SELF) continue;
            if (!isAllowedExtension(full)) continue;
            out.push(full);
        }
    }
    return out;
}

/** @returns {{ codePoint: number, len: 6 } | null} */
function tryParseLiteralUEscape(content, i) {
    if (content[i] !== "\\" || content[i + 1] !== "u") return null;
    const hex = content.slice(i + 2, i + 6);
    if (!/^[0-9a-fA-F]{4}$/.test(hex)) return null;
    return { codePoint: parseInt(hex, 16), len: 6 };
}

function replaceLiteralDashEscapes(content) {
    let out = "";
    let i = 0;
    while (i < content.length) {
        const parsed = tryParseLiteralUEscape(content, i);
        if (
            parsed &&
            DASH_CODEPOINTS.has(parsed.codePoint) &&
            (i === 0 || content[i - 1] !== "\\")
        ) {
            out += String.fromCharCode(parsed.codePoint);
            i += parsed.len;
        } else {
            out += content[i];
            i += 1;
        }
    }
    return out;
}

function countDashLiteralFixes(content) {
    let count = 0;
    const byCp = Object.create(null);
    let i = 0;
    while (i < content.length) {
        const parsed = tryParseLiteralUEscape(content, i);
        if (
            parsed &&
            DASH_CODEPOINTS.has(parsed.codePoint) &&
            (i === 0 || content[i - 1] !== "\\")
        ) {
            count += 1;
            const key =
                "U+" + parsed.codePoint.toString(16).toUpperCase().padStart(4, "0");
            byCp[key] = (byCp[key] || 0) + 1;
            i += parsed.len;
        } else {
            i += 1;
        }
    }
    return { count, byCp };
}

/** Find all literal \\uXXXX (backslash + u + 4 hex) for reporting. */
const RE_LITERAL_UXXXX = /\\u([0-9a-fA-F]{4})/g;

function scanLiteralUEscapes(content) {
    const counts = Object.create(null);
    let m;
    RE_LITERAL_UXXXX.lastIndex = 0;
    while ((m = RE_LITERAL_UXXXX.exec(content)) !== null) {
        const full = m[0];
        counts[full] = (counts[full] || 0) + 1;
    }
    return counts;
}

function mergeCounts(into, from) {
    for (const [k, v] of Object.entries(from)) {
        into[k] = (into[k] || 0) + v;
    }
}

const write = process.argv.includes("--write");
const dryRun = !write;

function main() {
    const files = walk(REPO_ROOT);
    const fileChanges = []; // { file, count, byCp }
    const reportByPattern = Object.create(null);
    const reportByFile = [];
    let globalByCp = Object.create(null);
    let totalFixes = 0;

    for (const file of files) {
        let raw;
        try {
            raw = fs.readFileSync(file, "utf8");
        } catch {
            continue;
        }
        if (raw.includes("\0") && raw.indexOf("\0") < 1000) continue;

        const rel = path.relative(REPO_ROOT, file);

        const { count, byCp } = countDashLiteralFixes(raw);
        mergeCounts(globalByCp, byCp);

        const literalPatterns = scanLiteralUEscapes(raw);
        if (Object.keys(literalPatterns).length > 0) {
            reportByFile.push({ file: rel, patterns: { ...literalPatterns } });
            mergeCounts(reportByPattern, literalPatterns);
        }

        if (count === 0) continue;

        totalFixes += count;
        fileChanges.push({ file: rel, count, byCp });

        if (write) {
            const next = replaceLiteralDashEscapes(raw);
            fs.writeFileSync(file, next, "utf8");
        }
    }

    console.log(
        dryRun
            ? `[dry-run] Would fix literal dash \\uXXXX sequences in ${fileChanges.length} file(s) (.ts, .tsx only).`
            : `[write] Fixed literal dash \\uXXXX sequences in ${fileChanges.length} file(s) (.ts, .tsx only).`
    );
    console.log(`Total replacements ${dryRun ? "to apply" : "applied"}: ${totalFixes}`);

    if (Object.keys(globalByCp).length > 0) {
        console.log("\nBy code point:");
        Object.entries(globalByCp)
            .sort(([a], [b]) => a.localeCompare(b))
            .forEach(([cp, n]) => console.log(`  ${cp}: ${n}`));
    }

    if (fileChanges.length && dryRun) {
        console.log("\nFiles that would change (first 50):");
        fileChanges.slice(0, 50).forEach(({ file, count }) => console.log(`  ${count}\t${file}`));
        if (fileChanges.length > 50) console.log(`  ... and ${fileChanges.length - 50} more`);
    }

    const reportPath = path.join(REPO_ROOT, "unicode-escape-report.json");
    const report = {
        generatedAt: new Date().toISOString(),
        scanExtensions: [".ts", ".tsx"],
        dashCodePointsFixed: [...DASH_CODEPOINTS].map((cp) => "U+" + cp.toString(16).toUpperCase().padStart(4, "0")),
        note: "Literal \\\\uXXXX in JSX/TSX text is not a JS escape — replace with real chars. Strings like \"\\\\u2014\" in source are still matched; review git diff. Surrogate pairs (emoji) may appear as two \\\\uXXXX in report.",
        dashFixTotals: globalByCp,
        dashFixSummary: {
            files: fileChanges.length,
            occurrences: totalFixes,
        },
        literalPatternsTotal: reportByPattern,
        filesWithLiteralPatterns: reportByFile.length,
        perFile: reportByFile,
    };
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), "utf8");
    console.log(`\nReport written: ${path.relative(REPO_ROOT, reportPath)}`);
    console.log(
        `Unique literal \\\\uXXXX patterns in .ts/.tsx: ${Object.keys(reportByPattern).length} (includes non-dash; see report)`
    );

    if (dryRun && totalFixes > 0) {
        console.log("\nRun with --write to apply fixes.");
    }

    process.exit(0);
}

main();
