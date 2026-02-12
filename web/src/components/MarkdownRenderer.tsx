import React from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/atom-one-dark.css'; // Import code highlight style

interface MarkdownRendererProps {
  content: string;
}

// Sanitize raw LaTeX math into readable plain text.
// Handles \frac{a}{b} → (a)/(b), \text{x} → x, \times → ×, etc.
function sanitizeLatex(text: string): string {
  let s = text;

  // \frac{numerator}{denominator} → (numerator) / (denominator)
  s = s.replace(/\\frac\{([^}]*)\}\{([^}]*)\}/g, '($1) / ($2)');

  // \text{...} → ... (just unwrap)
  s = s.replace(/\\text\{([^}]*)\}/g, '$1');

  // \textbf{...} → **...**
  s = s.replace(/\\textbf\{([^}]*)\}/g, '**$1**');

  // \textit{...} → *...*
  s = s.replace(/\\textit\{([^}]*)\}/g, '*$1*');

  // \sqrt{...} → √(...)
  s = s.replace(/\\sqrt\{([^}]*)\}/g, '√($1)');

  // Math functions: \log → log, \exp → exp, etc.
  s = s.replace(/\\(log|ln|exp|sin|cos|tan|min|max|arg|lim|sup|inf)(?=[^a-zA-Z])/g, '$1');

  // Decorators: \hat{x} → x̂, \bar{x} → x̄, etc.
  s = s.replace(/\\hat\{([^}]*)\}/g, '$1\u0302');
  s = s.replace(/\\bar\{([^}]*)\}/g, '$1\u0304');
  s = s.replace(/\\tilde\{([^}]*)\}/g, '$1\u0303');
  s = s.replace(/\\vec\{([^}]*)\}/g, '$1\u20D7');
  s = s.replace(/\\dot\{([^}]*)\}/g, '$1\u0307');

  // \mathbf{...}, \mathrm{...} → unwrap
  s = s.replace(/\\(?:mathbf|mathrm|mathit|mathcal)\{([^}]*)\}/g, '$1');

  // Common LaTeX symbols → Unicode
  s = s.replace(/\\times/g, '×');
  s = s.replace(/\\cdot/g, '·');
  s = s.replace(/\\pm/g, '±');
  s = s.replace(/\\leq/g, '≤');
  s = s.replace(/\\geq/g, '≥');
  s = s.replace(/\\neq/g, '≠');
  s = s.replace(/\\approx/g, '≈');
  s = s.replace(/\\infty/g, '∞');
  s = s.replace(/\\sum/g, 'Σ');
  s = s.replace(/\\prod/g, 'Π');
  s = s.replace(/\\int/g, '∫');
  s = s.replace(/\\partial/g, '∂');
  s = s.replace(/\\nabla/g, '∇');

  // Greek letters
  s = s.replace(/\\alpha/g, 'α');
  s = s.replace(/\\beta/g, 'β');
  s = s.replace(/\\gamma/g, 'γ');
  s = s.replace(/\\delta/g, 'δ');
  s = s.replace(/\\epsilon/g, 'ε');
  s = s.replace(/\\theta/g, 'θ');
  s = s.replace(/\\lambda/g, 'λ');
  s = s.replace(/\\mu/g, 'μ');
  s = s.replace(/\\sigma/g, 'σ');
  s = s.replace(/\\omega/g, 'ω');
  s = s.replace(/\\pi/g, 'π');
  s = s.replace(/\\phi/g, 'φ');
  s = s.replace(/\\rho/g, 'ρ');
  s = s.replace(/\\tau/g, 'τ');

  // Superscript/subscript: x^{2} → x², x_{i} → x_i
  s = s.replace(/\^{([^}]*)}/g, '^$1');
  s = s.replace(/_{([^}]*)}/g, '_$1');

  // Remove leftover \left, \right, \big, etc.
  s = s.replace(/\\(left|right|big|Big|bigg|Bigg)\b/g, '');

  // \% → %
  s = s.replace(/\\%/g, '%');

  // Strip wrapping $...$ or $$...$$ (LaTeX math delimiters)
  s = s.replace(/\$\$([\s\S]*?)\$\$/g, '$1');
  s = s.replace(/\$([^$\n]+?)\$/g, '$1');

  // Strip \[ ... \] and \( ... \) display/inline math delimiters
  s = s.replace(/\\\[([\s\S]*?)\\\]/g, '$1');
  s = s.replace(/\\\(([\s\S]*?)\\\)/g, '$1');

  return s;
}

// Turn inline citation tokens [P1] into clickable links when a footer provides URLs:
// pattern in footer: "[P1] Title — https://example.com"
function linkifyCitations(markdown: string): string {
  const footerRegex = /\[(A|P|G|W)(\d+)\]\s+([^\n—]+?)\s+—\s+(https?:\/\/\S+)/g;
  const linkMap: Record<string, string> = {};

  let match;
  while ((match = footerRegex.exec(markdown)) !== null) {
    const id = `${match[1]}${match[2]}`;
    linkMap[id] = match[4];
  }

  if (Object.keys(linkMap).length === 0) return markdown;

  // Replace citations in the main text with markdown links; leave footer as-is.
  return markdown.replace(/\[(A|P|G|W)(\d+)\]/g, (full, prefix, num) => {
    const key = `${prefix}${num}`;
    const url = linkMap[key];
    return url ? `[${key}](${url})` : full;
  });
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content }) => {
  const sanitized = sanitizeLatex(content);
  const linked = linkifyCitations(sanitized);
  return (
    <div className="prose prose-stone prose-sm max-w-none 
      prose-headings:font-semibold prose-headings:tracking-tight prose-headings:text-stone-900
      prose-p:text-stone-700 prose-p:leading-relaxed
      prose-a:text-indigo-600 prose-a:no-underline hover:prose-a:underline
      prose-strong:text-stone-900 prose-strong:font-semibold
      prose-ul:text-stone-700 prose-ol:text-stone-700
      prose-li:marker:text-stone-400
      prose-code:text-stone-800 prose-code:bg-stone-100 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded-md prose-code:font-mono prose-code:text-[0.9em] prose-code:before:content-none prose-code:after:content-none
      prose-pre:bg-stone-900 prose-pre:text-stone-50 prose-pre:rounded-xl prose-pre:shadow-sm
      prose-blockquote:border-l-4 prose-blockquote:border-stone-200 prose-blockquote:pl-4 prose-blockquote:italic prose-blockquote:text-stone-600
      prose-img:rounded-lg prose-img:shadow-sm
      break-words">
      <ReactMarkdown rehypePlugins={[rehypeHighlight]}>
        {linked}
      </ReactMarkdown>
    </div>
  );
};
