const FENCE_TOKEN_PREFIX = "@@VCB_FENCE_";
const INLINE_CODE_TOKEN_PREFIX = "@@VCB_CODE_";

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function escapeAttribute(value: string): string {
  return value.replace(/"/g, "&quot;");
}

function normalizeLineEndings(value: string): string {
  return value.replace(/\r\n?/g, "\n");
}

function sanitizeUrl(url: string): string {
  const normalized = url.replace(/&amp;/g, "&").trim();
  if (/^https?:\/\//i.test(normalized)) return normalized;
  return "#";
}

function renderInline(text: string): string {
  const codeSegments: string[] = [];

  const withCodeTokens = text.replace(/`([^`]+)`/g, (_match, code: string) => {
    const token = `${INLINE_CODE_TOKEN_PREFIX}${codeSegments.length}@@`;
    codeSegments.push(`<code>${escapeHtml(code)}</code>`);
    return token;
  });

  let html = escapeHtml(withCodeTokens);

  html = html.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, (_match, label: string, url: string) => {
    const href = sanitizeUrl(url);
    return `<a href="${escapeAttribute(href)}" target="_blank" rel="noopener noreferrer">${label}</a>`;
  });

  html = html
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/__([^_]+)__/g, "<strong>$1</strong>")
    .replace(/\*([^*]+)\*/g, "<em>$1</em>")
    .replace(/_([^_]+)_/g, "<em>$1</em>")
    .replace(/~~([^~]+)~~/g, "<del>$1</del>");

  for (let index = 0; index < codeSegments.length; index += 1) {
    const token = `${INLINE_CODE_TOKEN_PREFIX}${index}@@`;
    html = html.replace(token, codeSegments[index]);
  }

  return html;
}

function isBlockStarter(line: string): boolean {
  return (
    /^ {0,3}#{1,6}\s+/.test(line) ||
    /^ {0,3}[-*+]\s+/.test(line) ||
    /^ {0,3}\d+\.\s+/.test(line) ||
    /^ {0,3}>\s?/.test(line) ||
    line.startsWith(FENCE_TOKEN_PREFIX)
  );
}

export function markdownToHtml(markdown: string): string {
  const fencedBlocks: string[] = [];
  const normalized = normalizeLineEndings(markdown ?? "");

  const withFenceTokens = normalized.replace(/```([a-zA-Z0-9_-]+)?\n([\s\S]*?)```/g, (_match, lang, code: string) => {
    const languageClass = typeof lang === "string" && lang.length > 0 ? ` class="language-${escapeAttribute(lang)}"` : "";
    const html = `<pre><code${languageClass}>${escapeHtml(code.trimEnd())}</code></pre>`;
    const token = `${FENCE_TOKEN_PREFIX}${fencedBlocks.length}@@`;
    fencedBlocks.push(html);
    return token;
  });

  const lines = withFenceTokens.split("\n");
  const blocks: string[] = [];

  let index = 0;
  while (index < lines.length) {
    const line = lines[index];
    const trimmed = line.trim();

    if (trimmed.length === 0) {
      index += 1;
      continue;
    }

    if (trimmed.startsWith(FENCE_TOKEN_PREFIX)) {
      const tokenIndex = Number.parseInt(trimmed.slice(FENCE_TOKEN_PREFIX.length).replace("@@", ""), 10);
      if (!Number.isNaN(tokenIndex) && fencedBlocks[tokenIndex]) blocks.push(fencedBlocks[tokenIndex]);
      index += 1;
      continue;
    }

    const headingMatch = line.match(/^ {0,3}(#{1,6})\s+(.+)$/);
    if (headingMatch) {
      const level = headingMatch[1].length;
      blocks.push(`<h${level}>${renderInline(headingMatch[2].trim())}</h${level}>`);
      index += 1;
      continue;
    }

    if (/^ {0,3}[-*+]\s+/.test(line)) {
      const items: string[] = [];
      while (index < lines.length && /^ {0,3}[-*+]\s+/.test(lines[index])) {
        const item = lines[index].replace(/^ {0,3}[-*+]\s+/, "");
        items.push(`<li>${renderInline(item.trim())}</li>`);
        index += 1;
      }
      blocks.push(`<ul>${items.join("")}</ul>`);
      continue;
    }

    if (/^ {0,3}\d+\.\s+/.test(line)) {
      const items: string[] = [];
      while (index < lines.length && /^ {0,3}\d+\.\s+/.test(lines[index])) {
        const item = lines[index].replace(/^ {0,3}\d+\.\s+/, "");
        items.push(`<li>${renderInline(item.trim())}</li>`);
        index += 1;
      }
      blocks.push(`<ol>${items.join("")}</ol>`);
      continue;
    }

    if (/^ {0,3}>\s?/.test(line)) {
      const quoteLines: string[] = [];
      while (index < lines.length && /^ {0,3}>\s?/.test(lines[index])) {
        quoteLines.push(lines[index].replace(/^ {0,3}>\s?/, ""));
        index += 1;
      }
      blocks.push(`<blockquote>${renderInline(quoteLines.join("\n")).replace(/\n/g, "<br>")}</blockquote>`);
      continue;
    }

    const paragraphLines: string[] = [];
    while (index < lines.length && lines[index].trim().length > 0 && !isBlockStarter(lines[index])) {
      paragraphLines.push(lines[index].trimEnd());
      index += 1;
    }
    blocks.push(`<p>${renderInline(paragraphLines.join("\n")).replace(/\n/g, "<br>")}</p>`);
  }

  return blocks.join("");
}
