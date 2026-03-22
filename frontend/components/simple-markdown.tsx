import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeSanitize, { defaultSchema } from "rehype-sanitize";

interface SimpleMarkdownProps {
    markdown: string;
    className?: string;
}

export function SimpleMarkdown({ markdown, className }: SimpleMarkdownProps) {
    const schema = {
        ...defaultSchema,
        tagNames: [
            ...(defaultSchema.tagNames ?? []),
            "table",
            "thead",
            "tbody",
            "tr",
            "th",
            "td",
        ],
    };

    return (
        <div className={`text-xs text-muted-foreground ${className ?? ""}`}>
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[[rehypeSanitize, schema]]}
                components={{
                    p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
                    h1: ({ children }) => <h1 className="mb-2 text-sm font-semibold text-foreground">{children}</h1>,
                    h2: ({ children }) => <h2 className="mb-2 text-sm font-semibold text-foreground">{children}</h2>,
                    h3: ({ children }) => <h3 className="mb-1 text-[13px] font-semibold text-foreground">{children}</h3>,
                    ul: ({ children }) => <ul className="mb-2 list-disc space-y-1 pl-4">{children}</ul>,
                    ol: ({ children }) => <ol className="mb-2 list-decimal space-y-1 pl-4">{children}</ol>,
                    li: ({ children }) => <li>{children}</li>,
                    blockquote: ({ children }) => (
                        <blockquote className="mb-2 border-l-2 border-border/60 pl-3 text-muted-foreground">{children}</blockquote>
                    ),
                    code: ({ children, className: codeClass }) => {
                        const isBlock = Boolean(codeClass);
                        if (isBlock) {
                            return (
                                <code className="block overflow-x-auto rounded-md border border-border/40 bg-secondary/30 px-2 py-1 text-[11px]">
                                    {children}
                                </code>
                            );
                        }
                        return <code className="rounded bg-secondary/40 px-1 py-0.5 font-mono text-[11px]">{children}</code>;
                    },
                    a: ({ href, children }) => (
                        <a
                            href={href}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary underline underline-offset-2 hover:opacity-90"
                        >
                            {children}
                        </a>
                    ),
                    table: ({ children }) => (
                        <div className="mb-2 overflow-x-auto">
                            <table className="w-full min-w-[260px] border-collapse text-[11px]">{children}</table>
                        </div>
                    ),
                    thead: ({ children }) => <thead className="bg-secondary/35 text-foreground">{children}</thead>,
                    tbody: ({ children }) => <tbody>{children}</tbody>,
                    tr: ({ children }) => <tr className="border-b border-border/30">{children}</tr>,
                    th: ({ children }) => <th className="border border-border/30 px-2 py-1.5 text-left font-semibold">{children}</th>,
                    td: ({ children }) => <td className="border border-border/30 px-2 py-1.5 align-top">{children}</td>,
                    hr: () => <hr className="my-2 border-border/40" />,
                }}
            >
                {markdown}
            </ReactMarkdown>
        </div>
    );
}
