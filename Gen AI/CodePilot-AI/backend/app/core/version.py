"""
Application version metadata.

Design decision:
    Version information is isolated in its own module rather than
    hardcoded inside settings.py. This allows the version to be bumped
    independently of configuration changes, and allows build/CI tooling
    (or a future release script) to read/update a single, predictable
    location without parsing environment-dependent settings logic.
"""

# Semantic version of the CodePilot AI backend.
# Format: MAJOR.MINOR.PATCH (https://semver.org/)
__version__: str = "0.1.0"

# Human-readable build stage, useful for distinguishing capstone
# milestones in logs and API responses (e.g., "foundation", "beta").
__build_stage__: str = "foundation"


def get_version() -> str:
    """Return the current application version string.

    Returns:
        str: The semantic version of the running application.
    """
    return __version__


def get_version_info() -> dict[str, str]:
    """Return structured version metadata.

    Returns:
        dict[str, str]: A dictionary containing the version and the
        current build stage, suitable for inclusion in a health-check
        or root API endpoint response.
    """
    return {
        "version": __version__,
        "build_stage": __build_stage__,
    }