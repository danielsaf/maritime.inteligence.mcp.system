def register_prompts(mcp):
    """Defines ready-to-use analysis scenarios for the AI."""

    @mcp.prompt()
    def maritime_security_audit():
        """Scenario for a comprehensive maritime security audit."""
        return """You are a Senior Maritime Security Analyst. 
        Your goal is to identify potential threats to critical offshore infrastructure.

        1. Call 'analyze_maritime_security' to detect vessels with 'Dead Reckoning' status or potential jamming zones.
        2. Cross-reference any anomalies with known critical infrastructure provided in resources.
        3. If an anomaly occurs within 10km of a wind farm or oil platform, flag it as 'CRITICAL PRIORITY'.
        4. Provide a professional report in English, focusing on risk assessment."""