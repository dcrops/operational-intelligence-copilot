from src.operational_intelligence.models import ExecutiveReport, Finding

class ExecutiveReportGenerator:
    """
    Transforms a list of Finding objects into an ExecutiveReport.
    """

    def generate(self, findings: list[Finding]) -> ExecutiveReport:
        """
        Generate an executive-ready report from findings.

        Args:
            findings (list[Finding]): List of findings to include in the report.

        Returns:
            ExecutiveReport: The generated executive report.

        Raises:
            ValueError: If findings is not a list.
        """
        if not isinstance(findings, list):
            raise ValueError("findings must be a list")

        high_priority_findings: list[Finding] = []
        medium_priority_findings: list[Finding] = []
        low_priority_findings: list[Finding] = []

        for finding in findings:
            if finding.severity == "HIGH":
                high_priority_findings.append(finding)
            elif finding.severity == "MEDIUM":
                medium_priority_findings.append(finding)
            elif finding.severity in ("LOW", "INFO"):
                low_priority_findings.append(finding)

        total = len(findings)
        n_high = len(high_priority_findings)
        n_medium = len(medium_priority_findings)
        n_low = len(low_priority_findings)

        executive_summary = (
            f"Operational analysis identified {total} finding(s): "
            f"{n_high} high priority, {n_medium} medium priority, and {n_low} low priority."
        )

        recommended_next_steps: list[str] = []
        seen: set[str] = set()
        for finding in findings:
            action = finding.recommended_action
            if action and action not in seen:
                recommended_next_steps.append(action)
                seen.add(action)

        return ExecutiveReport(
            executive_summary=executive_summary,
            high_priority_findings=high_priority_findings,
            medium_priority_findings=medium_priority_findings,
            low_priority_findings=low_priority_findings,
            recommended_next_steps=recommended_next_steps
        )