import logging

# Logger configuration
logger = logging.getLogger("MCP_Resources")


def register_resources(mcp):
    """
    Registers static and dynamic informational assets for the AI model.

    Resources act as a 'knowledge base' that Claude can reference to
    contextualize real-time vessel behavior against known infrastructure.
    """

    @mcp.resource("maritime://critical-infrastructure")
    def get_infrastructure() -> str:
        """
        Returns a list of high-value offshore assets and their coordinates.
        Used for identifying potential targets or sensitive navigation areas.
        """
        return """
        # STRATEGIC OIL & GAS PLATFORMS
        - Troll A: 60.64, 3.72 (World's tallest moved structure, crucial gas hub)
        - Sleipner Field: 58.36, 1.91 (Major carbon capture and storage site)
        - Statfjord: 61.25, 1.85 (Key oil field in the North Sea)

        # OFFSHORE WIND FARMS (High Vulnerability)
        - Hywind Tampen: 61.33, 2.25 (World's largest floating wind farm)
        - Dogger Bank: 54.75, 1.95 (Strategic power generation for Western Europe)

        # SUBSEA INTERCONNECTORS & PIPELINES
        - Baltic Pipe: 55.10, 14.10 (Energy security link to Central Europe)
        - Nordlink: 58.20, 6.50 (High-voltage DC link between Norway and Germany)
        """

    @mcp.resource("maritime://security-zones")
    def get_security_zones() -> str:
        """
        Returns the definitions and severity levels of monitored geofence zones.
        Matches the database entries in the 'geofences' table.
        """
        return """
        # PROTECTED MARITIME ZONES (Geofences)

        1. Bergen Port Safety Zone (CRITICAL)
           - Center: 60.40, 5.30
           - Focus: Unauthorized high-speed maneuvers in harbor approaches.

        2. Hywind Operational Area (HIGH)
           - Center: 61.33, 2.25
           - Focus: Protection of floating wind turbines and subsea cables.

        3. Troll A Exclusion Zone (CRITICAL)
           - Center: 60.64, 3.72
           - Focus: 500m safety radius around critical gas infrastructure.

        4. North Sea Signal Monitoring Area (MEDIUM)
           - Region: 57.0N-65.0N, 3.0E-15.0E
           - Focus: Monitoring for GPS jamming clusters and dark target detection.
        """

    logger.info("📦 MCP Resources registered (Infrastructure & Security Zones).")