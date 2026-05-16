import os
from github import Github, GithubException


def get_github_client() -> Github:
    token = os.getenv("GITHUB_TOKEN")
    return Github(token) if token else Github()


def fetch_repo_summary(repo_full_name: str) -> str:
    """Return a text summary of a GitHub repo: description, languages, recent files, open issues."""
    try:
        g = get_github_client()
        repo = g.get_repo(repo_full_name)

        languages = ", ".join(list(repo.get_languages().keys())[:6]) or "N/A"
        contents = repo.get_contents("")
        files = [c.path for c in contents if c.type == "file"][:20]

        issues = list(repo.get_issues(state="open"))[:5]
        issue_lines = [f"  #{i.number}: {i.title}" for i in issues] or ["  (none)"]

        return "\n".join([
            f"Repo: {repo.full_name}",
            f"Description: {repo.description or 'N/A'}",
            f"Stars: {repo.stargazers_count} | Forks: {repo.forks_count}",
            f"Languages: {languages}",
            f"Top-level files: {', '.join(files)}",
            f"Open issues ({repo.open_issues_count}):",
            *issue_lines,
        ])
    except GithubException as e:
        return f"GitHub error: {e.data.get('message', str(e))}"


def fetch_file_content(repo_full_name: str, file_path: str) -> str:
    """Return the raw content of a file in a GitHub repo."""
    try:
        g = get_github_client()
        repo = g.get_repo(repo_full_name)
        content = repo.get_contents(file_path)
        if isinstance(content, list):
            return f"'{file_path}' is a directory. Files: {[c.path for c in content]}"
        decoded = content.decoded_content.decode("utf-8", errors="replace")
        # cap at 8000 chars to stay within context
        if len(decoded) > 8000:
            decoded = decoded[:8000] + "\n\n[...truncated]"
        return decoded
    except GithubException as e:
        return f"GitHub error: {e.data.get('message', str(e))}"
