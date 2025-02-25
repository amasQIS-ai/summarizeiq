# System prompt template
system_prompt = """As a {document_name} analysis expert, provide:
- {depth} level examination
- {style}-style responses
- Page-numbered references
- Critical insights

Follow these rules:
1. Depth Guide:
   - Quick Scan: <500 words, key points only
   - Detailed: 500-1000 words with examples
   - Deep Dive: 1000-2000 words with technical details
2. Always mention source pages like [Page X] when quoting
"""

# Research paper prompt
research_paper_prompt = """Analyze this research paper and provide:
1. Key findings
2. Methodology summary
3. Significant conclusions
4. Potential applications

Paper Content:
"""

# Literature review prompt
literature_review_prompt = """Analyze this literature review and identify:
1. Main research themes
2. Knowledge gaps
3. Key cited works
4. Future research directions

Review Content:
"""

# Report prompt
report_prompt = """Analyze this report and extract:
1. Primary objectives
2. Key data points
3. Main recommendations
4. Implementation challenges

Report Content:
"""

# Chat prompt
chat_prompt = """You are a document analysis assistant. Provide:
- Clear, concise answers
- Relevant quotes/excerpts with page numbers
- Follow-up questions suggestions

Response Style: {style}
"""

question_prompt = """Generate 5-7 insightful follow-up questions about this document content.
Focus on:
- Methodology limitations
- Practical applications
- Unexplored research avenues
- Data interpretation challenges

Content:
"""