import re
from urllib.parse import urlparse


REPOSITORY_PART_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")


def parse_github_repo_url(url: str) -> tuple[str, str]:
    """Validate a public GitHub repository URL and return its owner and name."""
    parsed = urlparse(str(url).strip())
    if parsed.scheme != "https" or parsed.hostname not in {"github.com", "www.github.com"}:
        raise ValueError("Expected an HTTPS GitHub repository URL")
    if parsed.port is not None or parsed.username or parsed.password:
        raise ValueError("GitHub repository URL must not contain credentials or a port")
    if parsed.query or parsed.fragment or parsed.params:
        raise ValueError("GitHub repository URL must not contain query parameters or fragments")

    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) != 2:
        raise ValueError("Expected format: https://github.com/owner/repository")

    owner, repo = parts
    if repo.endswith(".git"):
        repo = repo[:-4]
    if not owner or not repo or not REPOSITORY_PART_PATTERN.fullmatch(owner) or not REPOSITORY_PART_PATTERN.fullmatch(repo):
        raise ValueError("GitHub owner and repository names contain unsupported characters")
    if owner in {".", ".."} or repo in {".", ".."}:
        raise ValueError("GitHub owner and repository names are invalid")
    return owner, repo


def normalize_github_repo_url(url: str) -> str:
    owner, repo = parse_github_repo_url(url)
    return f"https://github.com/{owner}/{repo}"
