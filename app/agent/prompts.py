"""
LLM prompts for the research agent.
"""

# Intake prompt - validate and clarify vague objectives
INTAKE_PROMPT = """You are a research assistant. Analyze the following research objective and determine if it's specific enough to research.

Research Objective: {objective}
Constraints: {constraints}

If the objective is too vague or ambiguous, generate 2-3 clarifying questions.
If the objective is clear enough to proceed, indicate that research can begin.

Respond in JSON format:
{{
    "is_clear": true/false,
    "clarifying_questions": ["question 1", "question 2"] or [],
    "refined_objective": "A more specific version of the objective if needed",
    "reasoning": "Brief explanation of your assessment"
}}
"""

# Planner prompt - generate sub-queries and done criteria
PLANNER_PROMPT = """You are a research planner. Break down the following research objective into specific search queries and define done criteria.

Research Objective: {objective}
Constraints: {constraints}
Depth: {depth}

Generate:
1. 3-5 specific search queries to find relevant academic papers
2. Clear criteria for when the research is complete

Respond in JSON format:
{{
    "sub_queries": [
        "specific search query 1",
        "specific search query 2",
        "specific search query 3"
    ],
    "done_criteria": [
        "criterium 1: e.g., Found at least 5 relevant papers",
        "criterium 2: e.g., Covered multiple perspectives on the topic"
    ],
    "estimated_sources_needed": 5-10
}}
"""

# Synthesizer prompt - write structured report
SYNTHESIZER_PROMPT = """You are a research synthesizer. Write a comprehensive research report based on the sources provided.

Research Objective: {objective}
Constraints: {constraints}

Sources Found:
{sources_text}

Relevant Excerpts from Papers:
{chunks_text}

Write a structured report with the following sections:

## TL;DR
• 3 bullet points summarizing key findings

## Background
Brief context on the research topic.

## Key Findings
Main discoveries and insights from the papers.

## Key Papers/Sources
List the 5-10 most important papers with:
- Title
- Authors (first author et al.)
- Year
- Key contribution
- [Link](url)

## Disagreements/Contradictions
Points where researchers disagree or findings conflict.

## Gaps & Open Questions
What's still unknown or under-researched.

## Proposed Experiments / Next Steps
Potential research directions or experiments to try.

## References
Full list of sources with proper citations and links.

IMPORTANT:
- Use actual paper titles and URLs from the sources provided
- Include proper citations in [Author, Year] format
- Be specific and cite sources for claims
- Keep the report focused on the research objective
"""

# Critic prompt - find gaps and contradictions
CRITIC_PROMPT = """You are a research critic. Analyze the following research draft and identify any gaps, contradictions, or areas that need more investigation.

Research Objective: {objective}

Draft Report:
{draft}

Sources Used:
{sources_text}

Analyze the draft for:
1. Important gaps - aspects of the objective not adequately covered
2. Contradictions - conflicting information or unresolved debates
3. Missing perspectives - viewpoints not represented
4. Areas needing more depth

Respond in JSON format:
{{
    "gaps": [
        "Gap 1: description of what's missing",
        "Gap 2: ..."
    ],
    "contradictions": [
        "Contradiction 1: description of conflicting info",
        "..."
    ],
    "follow_up_queries": [
        "specific search query to fill gap 1",
        "..."
    ],
    "confidence": 0.0-1.0,
    "should_iterate": true/false,
    "reasoning": "Brief explanation of whether more research is needed"
}}

Set should_iterate to true ONLY if there are critical gaps that would significantly improve the report.
Set confidence to how complete you believe the research is (0=incomplete, 1=very complete).
"""

# Supervisor prompt - decide next agent
SUPERVISOR_PROMPT = """You are the research supervisor. Based on the current state, decide which agent should work next.

Current State:
- Objective: {objective}
- Plan exists: {has_plan}
- Sources found: {num_sources}
- Draft written: {has_draft}
- Critique done: {has_critique}
- Loop count: {loop_count}
- Status: {status}

Available agents:
- planner: Create research plan with sub-queries
- retriever: Search for sources (arXiv, Semantic Scholar, Wikipedia)
- reader: Process sources and store in vector DB
- synthesizer: Write the research report
- critic: Analyze draft for gaps and contradictions
- FINISH: Complete the research

Respond with just the agent name (e.g., "planner" or "FINISH").
"""

# Finalizer prompt - format final report
FINALIZER_PROMPT = """Format the following research report to ensure it's properly structured with all required sections.

Draft Report:
{draft}

Ensure the report has:
1. TL;DR (3 bullets)
2. Background
3. Key Papers/Sources (5-10) with links
4. Disagreements/Contradictions
5. Gaps & Open Questions
6. Proposed Experiments / Next Steps
7. References (with links)

If any section is missing, add a placeholder indicating more research is needed.
Ensure all links are properly formatted as [Title](URL).
Return the formatted report.
"""


def format_sources_for_prompt(sources: list[dict]) -> str:
    """Format sources for inclusion in prompts."""
    if not sources:
        return "No sources found yet."
    
    lines = []
    for i, s in enumerate(sources[:15], 1):  # Limit to avoid context overflow
        authors = s.get("authors", [])
        authors_str = ", ".join(authors[:2])
        if len(authors) > 2:
            authors_str += " et al."
        
        lines.append(
            f"[{i}] {s.get('title', 'Untitled')} ({s.get('year', 'N/A')})\n"
            f"    Authors: {authors_str}\n"
            f"    URL: {s.get('url', 'N/A')}\n"
            f"    Abstract: {s.get('abstract', 'N/A')[:200]}..."
        )
    
    return "\n\n".join(lines)


def format_chunks_for_prompt(chunks: list[dict]) -> str:
    """Format chunks for inclusion in prompts."""
    if not chunks:
        return "No text excerpts available."
    
    lines = []
    for i, c in enumerate(chunks[:10], 1):  # Limit chunks
        lines.append(
            f"[Excerpt {i}] From: {c.get('source_title', 'Unknown')}\n"
            f"{c.get('text', '')[:400]}..."
        )
    
    return "\n\n".join(lines)
