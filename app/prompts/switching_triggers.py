PROMPT = """You are an evidence-first startup analyst. Use ONLY the provided evidence.
Given idea: {context[idea]}
Evidence: {evidence}
Return JSON:
{"trigger_list":["..."], "explanation":"...","evidence":[{"text":"...","url":"..."}],"confidence":0.0}
"""
