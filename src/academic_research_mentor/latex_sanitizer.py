"""Sanitize raw LaTeX math into readable plain-text Unicode.

Many LLMs (especially Qwen) emit raw LaTeX like \\frac{a}{b} even when
asked not to.  This module converts those fragments into clean,
human-readable text so the output looks correct in terminals, APIs, and
frontends that don't have a LaTeX renderer.
"""

from __future__ import annotations

import re

# Ordered list of (pattern, replacement) — applied sequentially.
_RULES: list[tuple[re.Pattern[str], str]] = [
    # \frac{num}{den} → (num) / (den)
    (re.compile(r"\\frac\{([^}]*)\}\{([^}]*)\}"), r"(\1) / (\2)"),

    # \text{...}, \mathrm{...}, \mathbf{...} → unwrap
    (re.compile(r"\\(?:text|mathrm|mathbf|mathit|textbf|textit)\{([^}]*)\}"), r"\1"),

    # \sqrt{...} → √(...)
    (re.compile(r"\\sqrt\{([^}]*)\}"), r"√(\1)"),

    # \log, \ln, \exp, \sin, \cos etc. → just the function name
    (re.compile(r"\\(log|ln|exp|sin|cos|tan|min|max|arg|lim|sup|inf)(?=[^a-zA-Z])"), r"\1"),

    # \hat{x} → x̂,  \bar{x} → x̄,  \tilde{x} → x̃  (or just unwrap)
    (re.compile(r"\\hat\{([^}]*)\}"), r"\1̂"),
    (re.compile(r"\\bar\{([^}]*)\}"), r"\1̄"),
    (re.compile(r"\\tilde\{([^}]*)\}"), r"\1̃"),
    (re.compile(r"\\vec\{([^}]*)\}"), r"\1⃗"),
    (re.compile(r"\\dot\{([^}]*)\}"), r"\1̇"),
    (re.compile(r"\\ddot\{([^}]*)\}"), r"\1̈"),

    # --- common symbols → Unicode ----------------------------------------
    (re.compile(r"\\times(?=[^a-zA-Z])"), "×"),
    (re.compile(r"\\cdot(?=[^a-zA-Z])"), "·"),
    (re.compile(r"\\pm(?=[^a-zA-Z])"), "±"),
    (re.compile(r"\\mp(?=[^a-zA-Z])"), "∓"),
    (re.compile(r"\\leq(?=[^a-zA-Z])"), "≤"),
    (re.compile(r"\\geq(?=[^a-zA-Z])"), "≥"),
    (re.compile(r"\\neq(?=[^a-zA-Z])"), "≠"),
    (re.compile(r"\\approx(?=[^a-zA-Z])"), "≈"),
    (re.compile(r"\\infty(?=[^a-zA-Z])"), "∞"),
    (re.compile(r"\\sum(?=[^a-zA-Z])"), "Σ"),
    (re.compile(r"\\prod(?=[^a-zA-Z])"), "Π"),
    (re.compile(r"\\int(?=[^a-zA-Z])"), "∫"),
    (re.compile(r"\\partial(?=[^a-zA-Z])"), "∂"),
    (re.compile(r"\\nabla(?=[^a-zA-Z])"), "∇"),
    (re.compile(r"\\rightarrow(?=[^a-zA-Z])"), "→"),
    (re.compile(r"\\leftarrow(?=[^a-zA-Z])"), "←"),
    (re.compile(r"\\Rightarrow(?=[^a-zA-Z])"), "⇒"),
    (re.compile(r"\\Leftarrow(?=[^a-zA-Z])"), "⇐"),
    (re.compile(r"\\forall(?=[^a-zA-Z])"), "∀"),
    (re.compile(r"\\exists(?=[^a-zA-Z])"), "∃"),
    (re.compile(r"\\in(?=[^a-zA-Z])"), "∈"),
    (re.compile(r"\\notin(?=[^a-zA-Z])"), "∉"),
    (re.compile(r"\\subset(?=[^a-zA-Z])"), "⊂"),
    (re.compile(r"\\supset(?=[^a-zA-Z])"), "⊃"),
    (re.compile(r"\\cup(?=[^a-zA-Z])"), "∪"),
    (re.compile(r"\\cap(?=[^a-zA-Z])"), "∩"),

    # --- Greek letters ---------------------------------------------------
    (re.compile(r"\\alpha(?=[^a-zA-Z])"), "α"),
    (re.compile(r"\\beta(?=[^a-zA-Z])"), "β"),
    (re.compile(r"\\gamma(?=[^a-zA-Z])"), "γ"),
    (re.compile(r"\\delta(?=[^a-zA-Z])"), "δ"),
    (re.compile(r"\\epsilon(?=[^a-zA-Z])"), "ε"),
    (re.compile(r"\\zeta(?=[^a-zA-Z])"), "ζ"),
    (re.compile(r"\\eta(?=[^a-zA-Z])"), "η"),
    (re.compile(r"\\theta(?=[^a-zA-Z])"), "θ"),
    (re.compile(r"\\iota(?=[^a-zA-Z])"), "ι"),
    (re.compile(r"\\kappa(?=[^a-zA-Z])"), "κ"),
    (re.compile(r"\\lambda(?=[^a-zA-Z])"), "λ"),
    (re.compile(r"\\mu(?=[^a-zA-Z])"), "μ"),
    (re.compile(r"\\nu(?=[^a-zA-Z])"), "ν"),
    (re.compile(r"\\xi(?=[^a-zA-Z])"), "ξ"),
    (re.compile(r"\\pi(?=[^a-zA-Z])"), "π"),
    (re.compile(r"\\rho(?=[^a-zA-Z])"), "ρ"),
    (re.compile(r"\\sigma(?=[^a-zA-Z])"), "σ"),
    (re.compile(r"\\tau(?=[^a-zA-Z])"), "τ"),
    (re.compile(r"\\upsilon(?=[^a-zA-Z])"), "υ"),
    (re.compile(r"\\phi(?=[^a-zA-Z])"), "φ"),
    (re.compile(r"\\chi(?=[^a-zA-Z])"), "χ"),
    (re.compile(r"\\psi(?=[^a-zA-Z])"), "ψ"),
    (re.compile(r"\\omega(?=[^a-zA-Z])"), "ω"),

    # Uppercase Greek
    (re.compile(r"\\Gamma(?=[^a-zA-Z])"), "Γ"),
    (re.compile(r"\\Delta(?=[^a-zA-Z])"), "Δ"),
    (re.compile(r"\\Theta(?=[^a-zA-Z])"), "Θ"),
    (re.compile(r"\\Lambda(?=[^a-zA-Z])"), "Λ"),
    (re.compile(r"\\Sigma(?=[^a-zA-Z])"), "Σ"),
    (re.compile(r"\\Phi(?=[^a-zA-Z])"), "Φ"),
    (re.compile(r"\\Psi(?=[^a-zA-Z])"), "Ψ"),
    (re.compile(r"\\Omega(?=[^a-zA-Z])"), "Ω"),

    # --- braces / decorators --------------------------------------------
    # x^{2} → x^2,  x_{i} → x_i
    (re.compile(r"\^\{([^}]*)\}"), r"^\1"),
    (re.compile(r"_\{([^}]*)\}"), r"_\1"),

    # \left, \right, \big etc. → nothing
    (re.compile(r"\\(?:left|right|big|Big|bigg|Bigg)(?=[^a-zA-Z])"), ""),

    # \% → %
    (re.compile(r"\\%"), "%"),

    # --- strip math delimiters ------------------------------------------
    # $$...$$ (display math)
    (re.compile(r"\$\$([\s\S]*?)\$\$"), r"\1"),
    # $...$ (inline math, single-line only)
    (re.compile(r"\$([^$\n]+?)\$"), r"\1"),
    # \[...\]  and  \(...\)
    (re.compile(r"\\\[([\s\S]*?)\\\]"), r"\1"),
    (re.compile(r"\\\(([\s\S]*?)\\\)"), r"\1"),
]


def sanitize_latex(text: str) -> str:
    """Convert raw LaTeX math fragments to readable plain-text Unicode.

    >>> sanitize_latex(r"\\frac{137.9}{3} = 45.97\\%")
    '(137.9) / (3) = 45.97%'
    >>> sanitize_latex(r"\\alpha + \\beta \\leq 1")
    'α + β ≤ 1'
    """
    for pattern, replacement in _RULES:
        text = pattern.sub(replacement, text)
    # Clean up any double-spaces left behind
    text = re.sub(r"  +", " ", text)
    return text
