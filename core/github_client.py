import httpx
import os
import asyncio
import base64
import urllib.parse
from typing import Dict, List, Tuple

class GitHubClient:
    BASE_URL = "https://api.github.com"
    
    def __init__(self):
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            self.headers["Authorization"] = f"token {token}"
            
    def parse_repo_url(self, url: str) -> Tuple[str, str]:
        # Parse "https://github.com/owner/repo" → ("owner", "repo")
        parsed = urllib.parse.urlparse(url)
        if parsed.netloc and parsed.netloc not in {"github.com", "www.github.com"}:
            raise ValueError(f"Unrecognized GitHub URL host: {parsed.netloc}")

        path = parsed.path.strip("/")
        if path.endswith(".git"):
            path = path[:-4]

        parts = [p for p in path.split("/") if p]
        if len(parts) < 2:
            raise ValueError(f"Unrecognized GitHub URL format: {url}. Expected format: https://github.com/owner/repo")

        owner, repo = parts[0], parts[1]
        return owner, repo

    async def _get(self, client: httpx.AsyncClient, url: str, params: dict = None) -> httpx.Response:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response
        except httpx.HTTPError as e:
            print(f"HTTP Error for {url}: {e}")
            return None

    async def fetch_repository_bundle(self, owner: str, repo: str) -> dict:
        async with httpx.AsyncClient(headers=self.headers, base_url=self.BASE_URL) as client:
            metadata_task = self.fetch_metadata(client, owner, repo)
            commits_task = self.fetch_commits(client, owner, repo)
            issues_task = self.fetch_issues(client, owner, repo)
            prs_task = self.fetch_pull_requests(client, owner, repo)
            file_tree_task = self.fetch_file_tree(client, owner, repo)
            
            metadata, commits, issues, prs, tree = await asyncio.gather(
                metadata_task, commits_task, issues_task, prs_task, file_tree_task,
                return_exceptions=True
            )
            
            # Handle possible exceptions from gather by defaulting to empty
            metadata = metadata if isinstance(metadata, dict) else {}
            commits = commits if isinstance(commits, list) else []
            issues = issues if isinstance(issues, list) else []
            prs = prs if isinstance(prs, list) else []
            tree = tree if isinstance(tree, list) else []
            
            key_files = await self.fetch_key_files(client, owner, repo, tree)

            return {
                "metadata": metadata,
                "commits": commits,
                "issues": issues,
                "pull_requests": prs,
                "file_tree": tree,
                "key_files": key_files
            }

    async def fetch_metadata(self, client: httpx.AsyncClient, owner: str, repo: str) -> dict:
        response = await self._get(client, f"/repos/{owner}/{repo}")
        if not response:
            return {}
        data = response.json()
        return {
            "description": data.get("description"),
            "language": data.get("language"),
            "stars": data.get("stargazers_count"),
            "forks": data.get("forks_count"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at")
        }

    async def fetch_commits(self, client: httpx.AsyncClient, owner: str, repo: str, limit: int = 150) -> List[dict]:
        commits = []
        page = 1
        while len(commits) < limit:
            response = await self._get(client, f"/repos/{owner}/{repo}/commits", params={"per_page": min(100, limit - len(commits)), "page": page})
            if not response:
                break
            data = response.json()
            if not data:
                break
                
            for item in data:
                commit = item.get("commit", {})
                author = commit.get("author", {})
                commits.append({
                    "sha": item.get("sha", "")[:7],
                    "message": commit.get("message", ""),
                    "author": author.get("name", ""),
                    "date": author.get("date", "")
                })
            page += 1
        return commits[:limit]

    async def fetch_issues(self, client: httpx.AsyncClient, owner: str, repo: str, limit: int = 100) -> List[dict]:
        issues = []
        page = 1
        while len(issues) < limit:
            response = await self._get(client, f"/repos/{owner}/{repo}/issues", params={"state": "all", "per_page": min(100, limit - len(issues)), "page": page})
            if not response:
                break
            data = response.json()
            if not data:
                break
                
            for item in data:
                if "pull_request" in item:
                    continue # Skip PRs returned in issues API
                    
                labels = [l.get("name") for l in item.get("labels", [])]
                issues.append({
                    "number": item.get("number"),
                    "title": item.get("title", ""),
                    "body": item.get("body") or "",
                    "state": item.get("state"),
                    "labels": labels,
                    "created_at": item.get("created_at"),
                    "comments_count": item.get("comments", 0)
                })
            page += 1
        return issues[:limit]

    async def fetch_pull_requests(self, client: httpx.AsyncClient, owner: str, repo: str, limit: int = 50) -> List[dict]:
        prs = []
        page = 1
        while len(prs) < limit:
            response = await self._get(client, f"/repos/{owner}/{repo}/pulls", params={"state": "all", "per_page": min(50, limit - len(prs)), "page": page})
            if not response:
                break
            data = response.json()
            if not data:
                break
                
            numbers = [item.get("number") for item in data if item.get("number")]
            detail_tasks = [self._get(client, f"/repos/{owner}/{repo}/pulls/{num}") for num in numbers]
            detail_responses = await asyncio.gather(*detail_tasks, return_exceptions=True)
            detail_map = {}
            for num, resp in zip(numbers, detail_responses):
                if isinstance(resp, httpx.Response):
                    try:
                        detail_map[num] = resp.json()
                    except Exception:
                        detail_map[num] = {}

            for item in data:
                num = item.get("number")
                detail = detail_map.get(num, {})
                prs.append({
                    "number": num,
                    "title": item.get("title", ""),
                    "body": item.get("body") or "",
                    "state": item.get("state"),
                    "merged_at": item.get("merged_at"),
                    "additions": detail.get("additions", 0),
                    "deletions": detail.get("deletions", 0)
                })
            page += 1
        return prs[:limit]

    async def fetch_file_tree(self, client: httpx.AsyncClient, owner: str, repo: str) -> List[str]:
        # Need to get default branch first or just use HEAD
        response = await self._get(client, f"/repos/{owner}/{repo}/git/trees/HEAD", params={"recursive": "1"})
        if not response:
            return []
            
        data = response.json()
        tree = data.get("tree", [])
        
        excluded_dirs = ["node_modules/", ".git/", "build/", "dist/"]
        excluded_exts = [".min.js", ".map"]
        
        paths = []
        for item in tree:
            if item.get("type") != "blob":
                continue
            path = item.get("path", "")
            
            if any(path.startswith(d) for d in excluded_dirs) or any(d in path for d in [f"/{xd}" for xd in excluded_dirs]):
                continue
            if any(path.endswith(ext) for ext in excluded_exts):
                continue
                
            paths.append(path)
            
        return paths

    async def fetch_key_files(self, client: httpx.AsyncClient, owner: str, repo: str, tree: List[str]) -> Dict[str, str]:
        p1 = {"README.md", "ARCHITECTURE.md", "CONTRIBUTING.md", "CHANGELOG.md"}
        
        important_paths = []
        for path in tree:
            name = path.split("/")[-1].upper()
            if name in p1:
                important_paths.append((1, path))
            elif "/" not in path and any(path.endswith(ext) for ext in [".toml", ".yaml", ".yml", ".json"]):
                important_paths.append((2, path))
            elif any(s in path.lower() for s in ["config", "setup", "architecture"]):
                important_paths.append((3, path))
                
        important_paths.sort(key=lambda x: x[0])
        selected_paths = [p[1] for p in important_paths[:10]]
        
        key_files = {}
        for path in selected_paths:
            response = await self._get(client, f"/repos/{owner}/{repo}/contents/{path}")
            if response:
                data = response.json()
                if data.get("encoding") == "base64" and data.get("content"):
                    try:
                        content = base64.b64decode(data["content"]).decode('utf-8', errors='replace')
                        key_files[path] = content
                    except Exception as e:
                        print(f"Error decoding {path}: {e}")
                        
        return key_files

    def build_archaeology_context(self, bundle: dict) -> str:
        HARD_LIMIT = 800000
        
        metadata_str = "=== REPOSITORY METADATA ===\n"
        for k, v in bundle.get("metadata", {}).items():
            metadata_str += f"{k}: {v}\n"
            
        key_files_str = "\n=== KEY FILES ===\n"
        for path, content in bundle.get("key_files", {}).items():
            key_files_str += f"--- {path} ---\n{content}\n\n"
            
        commits = list(bundle.get("commits", []))
        commits.reverse()  # Oldest first

        issues = list(bundle.get("issues", []))
        prs = list(bundle.get("pull_requests", []))

        def build_context_text(commits_list, issues_list, prs_list) -> str:
            ctx = metadata_str + key_files_str
            ctx += "=== COMMIT HISTORY (oldest first) ===\n"
            for c in commits_list:
                ctx += f"[{c['sha']} | {c['date']} | {c['author']} | {c['message']}]\n"

            ctx += "\n=== ISSUES (all states) ===\n"
            for i in issues_list:
                ctx += f"[#{i['number']} | {i['state']} | {i['title']}\n {i.get('body', '')}]\n"

            ctx += "\n=== PULL REQUESTS ===\n"
            for pr in prs_list:
                ctx += f"[#{pr['number']} | {pr['state']} | {pr['title']}\n {pr.get('body', '')}]\n"

            return ctx

        context = build_context_text(commits, issues, prs)

        # Truncate oldest commits first, then issue bodies, then PR bodies
        while len(context) > HARD_LIMIT:
            if commits:
                commits.pop(0)
            else:
                trimmed = False
                for issue in issues:
                    if issue.get("body"):
                        issue["body"] = ""
                        trimmed = True
                        break
                if not trimmed:
                    for pr in prs:
                        if pr.get("body"):
                            pr["body"] = ""
                            trimmed = True
                            break
                if not trimmed:
                    break
            context = build_context_text(commits, issues, prs)

        if len(context) > HARD_LIMIT:
            context = context[:HARD_LIMIT] + "\n... (context truncated due to length limits)"

        char_count = len(context)
        token_estimate = char_count // 4

        header = f"TOTAL CONTEXT: ~{char_count} chars, est. {token_estimate} tokens\n\n"
        return header + context