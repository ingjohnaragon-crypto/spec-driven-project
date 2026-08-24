# GitHub ↔ Jira Integration Checklist

Purpose
-------
Steps to verify and install the GitHub–Jira integration and enable Smart Commits so commits/PRs link to Jira issues and (optionally) perform transitions.

Prerequisites
-------------
- You must have administrative access to the GitHub organization (install apps) and Jira instance (manage apps / application links).
- Store any credentials (API tokens) in repository or org secrets for CI (do NOT commit secrets to repo).

Top-level steps
---------------
1. Verify existing integration
   - In GitHub: visit Organization Settings → Installed GitHub Apps → confirm "GitHub for Jira" (or equivalent) is installed and has access to this repository.
   - In Jira: Administration → Manage Apps → confirm GitHub for Jira is shown and connected.
   - Quick test: open a commit or PR with a Jira key in the title (e.g., `SCRUM-1`) and check the Jira issue for an incoming link.

2. Install GitHub for Jira (if missing)
   - On GitHub Marketplace: install "GitHub for Jira" to your organization and grant access to the target repository.
   - In Jira Cloud: Install the GitHub for Jira app (if requested) and follow the OAuth flow to connect to your GitHub org.

3. Enable Smart Commits (optional, Jira Cloud)
   - In Jira: Administration → System → Smart Commits (or search "Smart Commits").
   - Ensure Smart Commits are enabled for your project and that the Git provider and integration support it.
   - Smart commit example (in commit message):
     SCRUM-123 #comment Implemented endpoint #time 2h #transition Done

4. Standardize branch/commit/PR naming
   - Branch pattern: `feature/<JIRA-KEY>-short-description` (e.g., `feature/SCRUM-123-add-endpoint`).
   - Commit message prefix: include the issue key: `SCRUM-123: implement X`.
   - PR title: start with `SCRUM-123:` so GitHub and Jira can link automatically.

5. CI / Action hooks (recommended)
   - Add GitHub Action to run smoke checks on PR and optionally call Jira APIs on merge to transition issues.
   - Keep secrets in GitHub Actions Secrets: `JIRA_BASE`, `JIRA_USER`, `JIRA_API_TOKEN`.
   - Example transition (use correct transition id for your Jira workflow):
     ```yaml
     # .github/workflows/transition-jira.yml
     on:
       pull_request:
         types: [closed]
     jobs:
       transition:
         if: github.event.pull_request.merged == true
         runs-on: ubuntu-latest
         steps:
           - name: Extract issue key from branch
             run: echo "ISSUE=$(echo ${GITHUB_REF#refs/heads/} | sed -E 's/^.*([A-Z]+-[0-9]+).*$/\\1/')" >> $GITHUB_ENV
           - name: Transition Jira issue
             env:
               JIRA_BASE: ${{ secrets.JIRA_BASE }}
               JIRA_USER: ${{ secrets.JIRA_USER }}
               JIRA_TOKEN: ${{ secrets.JIRA_API_TOKEN }}
               ISSUE: ${{ env.ISSUE }}
             run: |
               curl -s -X POST -H "Authorization: Basic $(echo -n $JIRA_USER:$JIRA_TOKEN | base64)" -H "Content-Type: application/json" \
                 "$JIRA_BASE/rest/api/3/issue/$ISSUE/transitions" \
                 -d '{"transition":{"id":"31"}}'
     ```

6. Testing & verification
   - Create a test branch `feature/TEST-1-jira-integ` and a commit message `TEST-1: verify integration`.
   - Push the branch and open a PR; confirm Jira shows the PR and commit.
   - If using Smart Commits, create a commit with smart-commit syntax and confirm Jira records the comment/time/transition.

Security & operational notes
---------------------------
- Never put Jira tokens in the repo. Use GitHub Actions secrets or org secret storage.
- Require code review before merges that trigger transitions (avoid accidental transitions).
- If you enable Smart Commits, educate the team on syntax to avoid unintended transitions.

If you want, I can do the following next:
- A: Generate the GitHub Action scaffold file `.github/workflows/transition-jira.yml` (requires you to provide `JIRA_BASE`, `JIRA_USER`, `JIRA_API_TOKEN` as secrets). 
- B: Create commit/PR templates and an enforcement checklist to standardize branch/commit formats.
- C: Attempt to verify the integration from this environment (requires network access and admin creds).
