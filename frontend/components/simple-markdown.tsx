import React from "react";

interface SimpleMarkdownProps {
    markdown: string;
    className?: string;
}

function renderInline(text: string): React.ReactNode[] {
    const nodes: React.ReactNode[] = [];
    const pattern = /(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\)|\*[^*]+\*)/g;
    const parts = text.split(pattern);

    for (let i = 0; i < parts.length; i += 1) {
        const part = parts[i];
        if (!part) continue;

        if (part.startsWith("**") && part.endsWith("**")) {
            nodes.push(
                <strong key={`b-${i}`} className="font-semibold text-foreground">
                    {part.slice(2, -2)}
                </strong>
            );
            continue;
        }

        if (part.startsWith("`") && part.endsWith("`")) {
            nodes.push(
                <code key={`c-${i}`} className="rounded bg-secondary/40 px-1 py-0.5 font-mono text-[11px]">
                    {part.slice(1, -1)}
                </code>
            );
            continue;
        }

        if (part.startsWith("[") && part.includes("](") && part.endsWith(")")) {
            const split = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
            if (split) {
                const label = split[1];
                const href = split[2].trim();
                const isAllowed = href.startsWith("http://") || href.startsWith("https://");
                if (isAllowed) {
                    nodes.push(
                        <a
                            key={`a-${i}`}
                            href={href}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="underline underline-offset-2 text-primary hover:opacity-90"
                        >
                            {label}
                        </a>
                    );
                    continue;
                }
            }
        }

        if (part.startsWith("*") && part.endsWith("*")) {
            nodes.push(
                <em key={`i-${i}`} className="italic text-foreground/90">
                    {part.slice(1, -1)}
                </em>
            );
            continue;
        }

        nodes.push(<React.Fragment key={`t-${i}`}>{part}</React.Fragment>);
    }

    return nodes;
}

export function SimpleMarkdown({ markdown, className }: SimpleMarkdownProps) {
    const lines = markdown.replace(/\r\n/g, "\n").split("\n");
    const blocks: React.ReactNode[] = [];
    let i = 0;

    while (i < lines.length) {
        const line = lines[i];
        const trimmed = line.trim();

        if (!trimmed) {
            i += 1;
            continue;
        }

        if (trimmed.startsWith("```")) {
            const codeLines: string[] = [];
            i += 1;
            while (i < lines.length && !lines[i].trim().startsWith("```")) {
                codeLines.push(lines[i]);
                i += 1;
            }
            blocks.push(
                <pre key={`pre-${i}`} className="overflow-x-auto rounded-md border border-border/50 bg-secondary/20 p-2 text-[11px]">
                    <code>{codeLines.join("\n")}</code>
                </pre>
            );
            i += 1;
            continue;
        }

        const headingMatch = trimmed.match(/^(#{1,6})\s+(.*)$/);
        if (headingMatch) {
            const level = headingMatch[1].length;
            const content = renderInline(headingMatch[2]);
            const baseClass = "font-semibold text-foreground";
            if (level <= 2) {
                blocks.push(
                    <h3 key={`h-${i}`} className={`${baseClass} text-sm`}>
                        {content}
                    </h3>
                );
            } else {
                blocks.push(
                    <h4 key={`h-${i}`} className={`${baseClass} text-[13px]`}>
                        {content}
                    </h4>
                );
            }
            i += 1;
            continue;
        }

        if (/^[-*]\s+/.test(trimmed)) {
            const listItems: React.ReactNode[] = [];
            while (i < lines.length && /^[-*]\s+/.test(lines[i].trim())) {
                listItems.push(<li key={`ul-${i}`}>{renderInline(lines[i].trim().replace(/^[-*]\s+/, ""))}</li>);
                i += 1;
            }
            blocks.push(
                <ul key={`ul-block-${i}`} className="list-disc space-y-1 pl-4">
                    {listItems}
                </ul>
            );
            continue;
        }

        if (/^\d+\.\s+/.test(trimmed)) {
            const listItems: React.ReactNode[] = [];
            while (i < lines.length && /^\d+\.\s+/.test(lines[i].trim())) {
                listItems.push(<li key={`ol-${i}`}>{renderInline(lines[i].trim().replace(/^\d+\.\s+/, ""))}</li>);
                i += 1;
            }
            blocks.push(
                <ol key={`ol-block-${i}`} className="list-decimal space-y-1 pl-4">
                    {listItems}
                </ol>
            );
            continue;
        }

        if (trimmed.startsWith(">")) {
            const quoteLines: string[] = [];
            while (i < lines.length && lines[i].trim().startsWith(">")) {
                quoteLines.push(lines[i].trim().replace(/^>\s?/, ""));
                i += 1;
            }
            blocks.push(
                <blockquote
                    key={`q-${i}`}
                    className="border-l-2 border-border/60 pl-3 text-muted-foreground"
                >
                    {quoteLines.map((q, idx) => (
                        <p key={`q-${i}-${idx}`}>{renderInline(q)}</p>
                    ))}
                </blockquote>
            );
            continue;
        }

        const paragraph: string[] = [line];
        i += 1;
        while (i < lines.length) {
            const next = lines[i].trim();
            if (
                !next ||
                next.startsWith("```") ||
                /^#{1,6}\s+/.test(next) ||
                /^[-*]\s+/.test(next) ||
                /^\d+\.\s+/.test(next) ||
                next.startsWith(">")
            ) {
                break;
            }
            paragraph.push(lines[i]);
            i += 1;
        }

        blocks.push(
            <p key={`p-${i}`} className="leading-relaxed">
                {renderInline(paragraph.join(" "))}
            </p>
        );
    }

    return <div className={`space-y-2 text-xs text-muted-foreground ${className ?? ""}`}>{blocks}</div>;
}
