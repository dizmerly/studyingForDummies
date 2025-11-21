import React from 'react';

export function parseQuestionContent(text) {
    if (!text) return null;

    // Split by code blocks
    const parts = text.split(/"""CODE"""/g);

    return (
        <div className="space-y-4">
            {parts.map((part, index) => {
                // Even indices are normal text, odd are code
                if (index % 2 === 1) {
                    return (
                        <pre key={index} className="code-block">
                            <code>{part.trim()}</code>
                        </pre>
                    );
                }

                // Render normal text with line breaks
                return part.trim() && (
                    <div key={index} className="whitespace-pre-wrap">
                        {part.trim()}
                    </div>
                );
            })}
        </div>
    );
}
