# gh-axi command reference

> Static snapshot of installed `gh-axi` version and help output. Update manually when needed.
> Documented help, not an exhaustive machine-readable schema.
> Version: `0.1.37`

## Root help

Command: `gh-axi --help`

```text
usage: gh-axi [command] [args] [flags]
commands[17]:
  (none)=dashboard, issue, pr, discussion, stack, run, workflow, release, repo, label, gist, project, secret, variable, search, api, setup
flags[4]:
  -R/--repo <OWNER/NAME> (after command), --hostname <host> (after command) or GH_HOST env, both flags accept space or equals form, --help, -v/-V/--version
requires:
  gh >= 2.99.0 for --attach on issue/pr create, edit, and comment (set GH_BIN to override the gh binary)
examples:
  gh-axi
  gh-axi issue list --state open
  gh-axi issue list -R owner/name
  gh-axi issue list --repo=owner/name
  gh-axi issue list --hostname git.example.com
  gh-axi pr view 42
  gh-axi discussion view 66 --comments
  gh-axi stack view
  gh-axi secret list
  gh-axi setup hooks
"built-in":
  update: Upgrade `gh-axi.js` to the latest published version
  "update --check": Report current vs latest without installing
```

## api

Command: `gh-axi api --help`

```text
usage: gh-axi api [<method>] <path>
description: Make an authenticated GitHub API request. Defaults to GET if no method specified.
methods[6]:
  GET, POST, PUT, PATCH, DELETE, HEAD
flags[9]:
  -X <method> or -X=<method> (alias for the positional method; give once and do not combine with a positional method), --field <key=value> (repeatable; typed: numbers, true, false and null become JSON values), --raw-field <key=value> (repeatable; always sent as a string, e.g. content=+1), --header <key:value> (repeatable), --input <file> (raw JSON request body; use "-" for stdin), --paginate, --jq <expression>, --template <format>, --full (preserve complete field values and response bodies without truncation)
examples:
  gh-axi api /repos/{owner}/{repo}
  gh-axi api POST /repos/{owner}/{repo}/issues --field title="Bug report"
  gh-axi api -X POST /repos/{owner}/{repo}/issues --field title="Bug report"
  gh-axi api /repos/{owner}/{repo}/pulls --paginate
  gh-axi api /repos/{owner}/{repo}/issues/1 --jq '[.labels[].name]'
  gh-axi api PUT /repos/{owner}/{repo}/branches/main/protection --input body.json
  cat body.json | gh-axi api PUT /repos/{owner}/{repo}/branches/main/protection --input -
  gh-axi api POST /repos/{owner}/{repo}/issues/1/reactions --raw-field content=+1
```

## discussion

Command: `gh-axi discussion --help`

```text
usage: gh-axi discussion <subcommand> [flags]
subcommands[3]:
  list, view <number|url|comment-url>, comment <number|url|comment-url>
flags{list}:
  --state <open|closed|all> (default open), --category <name>, --author <login>, --label <name> (repeatable), --limit <n> (default 30)
flags{view}:
  --comments (each top-level comment with its replies nested under it), --limit <n> (comments to fetch, default 30; with a comment-url, replies to fetch), --order <newest|oldest> (which end to fetch when there are more than --limit; output is always oldest first), --full (show complete bodies without truncation)
flags{comment}:
  --body <text> or --body-file <path> (required; "-" reads stdin)
notes:
  comment with a discussion number or url adds a top-level comment; comment with a comment-url posts a reply under that comment
  view --comments shows only the latest few replies per comment; reply_count and replies_hidden say when some are hidden, and view <comment-url> shows the full reply thread
  gh discussion is a preview gh command and may change
examples:
  gh-axi discussion list --category General
  gh-axi discussion view 66 --comments
  gh-axi discussion view 'https://github.com/OWNER/REPO/discussions/66#discussioncomment-456'
  gh-axi discussion comment 66 --body "Thanks for the update"
  gh-axi discussion comment 'https://github.com/OWNER/REPO/discussions/66#discussioncomment-456' --body-file reply.md
```

## gist

Command: `gh-axi gist --help`

```text
usage: gh-axi gist <subcommand> [flags]
subcommands[7]:
  list, view <id|url>, edit <id|url>, rename <id|url> <old> <new>, create, delete <id|url>, clone <id|url>
flags{list}:
  --limit <n> (default 100), --public, --secret, --fields <field,...>
flags{view}:
  --files (file names only), -f/--filename <name> (single file), --full (no truncation), -r/--raw (no-op), -w/--web (rejected)
flags{edit}:
  --filename/-f <name> (replace from piped stdin), --add/-a <path> (from disk) or --add/-a <name> - (from piped stdin), --remove/-r <name>, --desc/-d <text>
flags{create}:
  --public (required, mutually exclusive with --secret)
  --secret (required, mutually exclusive with --public)
  --file <path> (repeatable), --filename <name> (for piped content)
  -d/--desc <text>
examples:
  gh-axi gist list
  gh-axi gist list --public --limit 20
  gh-axi gist list --fields url,owner,created
  gh-axi gist view 5b0e0062eb8e9654adad7bb1d81cc75f
  gh-axi gist view https://gist.github.com/octocat/5b0e0062eb8e9654adad7bb1d81cc75f
  gh-axi gist view 5b0e0062eb8e9654adad7bb1d81cc75f --files
  echo 'new content' | gh-axi gist edit <id|url> --filename notes.md
  echo 'new file' | gh-axi gist edit <id|url> --add new.txt -
  gh-axi gist edit <id|url> --add ./local.txt
  gh-axi gist edit <id|url> --remove old-file.txt --desc "updated description"
  gh-axi gist rename <id|url> old.txt new.txt
  gh-axi gist create notes.md --public --desc "My notes"
  gh-axi gist create --file a.py --file b.py --secret
  echo "content" | gh-axi gist create --filename hello.txt --public
  gh-axi gist delete <id|url>
  gh-axi gist clone <id|url>
```

## issue

Command: `gh-axi issue --help`

```text
usage: gh-axi issue <subcommand> [flags]
subcommands[14]:
  list, view <number>, create, edit <number>, close <number>, reopen <number>, comment <number>, delete <number>, lock <number>, unlock <number>, pin <number>, unpin <number>, transfer <number>, subissue <add|remove|list>
flags{list}:
  --state <open|closed|all>, --label <name> (repeatable), --assignee <login>, --author <login>, --milestone <name>, --sort <created|updated|comments>, --limit <n> (default 30), --fields <a,b,c>
flags{view}:
  --comments, --full (show the complete issue body and comment bodies without truncation)
flags{create}:
  --title <text> (required), --body <text> or --body-file <path>, --attach <path[#alt]> (repeatable; image/video; requires gh >= 2.99.0), --assignee <login> (repeatable), --label <name> (repeatable), --milestone <name>, --project <name> (repeatable), --type <name>
flags{edit}:
  --title, --body <text> or --body-file <path>, --attach <path[#alt]> (repeatable; image/video; requires gh >= 2.99.0), --add-label <name> (repeatable), --remove-label <name> (repeatable), --add-assignee <login> (repeatable), --remove-assignee <login> (repeatable), --milestone, --type <name>, --no-type
flags{close}:
  --reason <completed|not_planned>, --comment <text>
flags{comment}:
  --body <text> or --body-file <path> (required unless --attach), --attach <path[#alt]> (repeatable; image/video; requires gh >= 2.99.0)
flags{transfer}:
  --to-repo <owner/name> (required)
subissue:
  add <parent> <child> [<child> ...], remove <parent> <child>, list <parent>
examples:
  gh-axi issue list --state closed --label bug
  gh-axi issue view 42 --comments
  gh-axi issue create --title "Fix login" --body "Steps to reproduce..."
  gh-axi issue create --title "UI bug" --attach './repro.png#Login error'
  gh-axi issue comment 42 --body-file comment.md
  gh-axi issue comment 42 --attach ./before.png --attach ./after.png
  gh-axi issue close 42 --reason completed
  gh-axi issue transfer 42 -R source/repo --to-repo dest/repo
  gh-axi issue subissue add 16 20 101 125
  gh-axi issue subissue list 16
```

## label

Command: `gh-axi label --help`

```text
usage: gh-axi label <subcommand> [flags]
subcommands[4]:
  list, create, edit <name>, delete <name>
flags{list}:
  --limit <n> (default 500)
flags{create}:
  --name <text> (required), --color <hex> (required, without #), --description <text>
flags{edit}:
  --name, --color, --description
examples:
  gh-axi label list
  gh-axi label create --name "priority:high" --color ff0000 --description "High priority"
  gh-axi label delete "priority:low"
```

## pr

Command: `gh-axi pr --help`

```text
usage: gh-axi pr <subcommand> [flags]
subcommands[15]:
  list, view <number>, create, edit <number>, close <number>, merge <number>, review <number>, checks <number>, diff <number>, checkout <number>, ready <number>, reopen <number>, comment <number>, update-branch <number>, revert <number>
flags{list}:
  --state <open|closed|all>, --label (repeatable), --assignee, --author, --base, --head, --draft, --limit <n> (default 30), --fields <a,b,c>
flags{view}:
  --comments, --reviews (show review submissions and inline review comments), --checks (show the detailed check rollup), --full (show complete body without truncation)
flags{create}:
  --title <text> (required), --body <text> or --body-file <path>, --attach <path[#alt]> (repeatable; image/video; requires gh >= 2.99.0), --base, --head, --draft, --assignee <login> (repeatable), --reviewer <login> (repeatable), --label <name> (repeatable), --milestone, --project <name> (repeatable)
flags{edit}:
  --title <text>, --body <text> or --body-file <path>, --attach <path[#alt]> (repeatable; image/video; requires gh >= 2.99.0), --add-label <name> (repeatable), --remove-label <name> (repeatable), --add-assignee <login> (repeatable), --remove-assignee <login> (repeatable), --add-reviewer <login> (repeatable), --remove-reviewer <login> (repeatable), --milestone, --base <branch> (retarget the PR)
flags{close}:
  --comment <text>
flags{merge}:
  --method <merge|squash|rebase>, --merge, --squash, --rebase, --auto, --admin (use administrator privileges to bypass merge requirements; cannot combine with --auto), --delete-branch, --body <text> or --body-file <path>, --subject, --match-head-commit <SHA> (require the PR head to match before merging)
flags{review}:
  --approve, --request-changes, --comment, --body <text> or --body-file <path>
flags{comment}:
  --body <text> or --body-file <path> (required unless --attach), --attach <path[#alt]> (repeatable; image/video; requires gh >= 2.99.0)
flags{checks}:
  --failed (show only failing checks)
flags{diff}:
  --full (show complete diff without truncation), --patch (accepted for gh compatibility; output is already patch format)
examples:
  gh-axi pr list --state open --label bug
  gh-axi pr view 42 --comments
  gh-axi pr view 42 --reviews
  gh-axi pr create --title "Fix login" --attach './before.png#Before'
  gh-axi pr comment 42 --body-file review.md
  gh-axi pr comment 42 --attach ./after.png
  gh-axi pr merge 42 --squash --delete-branch
```

## project

Command: `gh-axi project --help`

```text
usage: gh-axi project <subcommand> [flags]
subcommands[13]:
  list, view <number>, item-list <number>, field-list <number>, item-add <number>, item-create <number>, item-edit, item-archive <number>, item-delete <number>, create, edit <number>, close <number>, copy <number>
flags{list}:
  --owner <login>, --closed, --limit <n> (default 30)
flags{view}:
  --owner <login>
flags{item-list}:
  --owner <login>, --query <filter>, --limit <n> (default 30)
flags{field-list}:
  --owner <login>, --limit <n> (default 30)
flags{item-add}:
  --owner <login>, --url <text> (required)
flags{item-create}:
  --owner <login>, --title <text> (required), --body <text> or --body-file <path>
flags{item-edit}:
  --id <text> (required), --project-id <text>, --field-id <text>, --text <text>, --number <n>, --date <YYYY-MM-DD>, --single-select-option-id <text>, --iteration-id <text>, --title <text>, --body <text> or --body-file <path>, --clear
flags{item-archive}:
  --owner <login>, --id <text> (required), --undo
flags{item-delete}:
  --owner <login>, --id <text> (required)
flags{create}:
  --owner <login>, --title <text> (required)
flags{edit}:
  --owner <login>, --title <text>, --description <text>, --readme <text>, --visibility <PUBLIC|PRIVATE>
flags{close}:
  --owner <login>, --undo
flags{copy}:
  --source-owner <login> (default current repo owner, else @me), --target-owner <login> (required), --title <text> (required), --drafts
notes:
  --owner defaults to the current repo's owner when run inside a repo, otherwise the authenticated user.
  Requires the `project` (or `read:project`) OAuth scope - scope errors include the exact `gh auth refresh -s <scope>` command to run.
examples:
  gh-axi project list --owner my-org
  gh-axi project view 3 --owner my-org
  gh-axi project item-add 3 --owner my-org --url https://github.com/my-org/repo/issues/12
  gh-axi project item-list 3 --owner my-org
  gh-axi project create --owner my-org --title "Roadmap"
```

## release

Command: `gh-axi release --help`

```text
usage: gh-axi release <subcommand> [flags]
subcommands[7]:
  list, view <tag>, create <tag>, edit <tag>, delete <tag>, download <tag>, upload <tag>
flags{list}:
  --exclude-drafts, --exclude-pre-releases, --limit (default 10)
flags{view}:
  --full (show complete release notes without truncation)
flags{create}:
  --title/-t, --notes/-n or --body, --notes-file/-F or --body-file, --draft/-d, --prerelease/-p, --target, --generate-notes, --discussion-category, --notes-start-tag, --verify-tag, --notes-from-tag, --fail-on-no-commits, --latest[=true|false], <files...>
flags{edit}:
  --title, --notes/-n or --body, --notes-file/-F or --body-file, --draft[=true|false], --prerelease[=true|false], --latest[=true|false]
flags{download}:
  --pattern, --dir
examples:
  gh-axi release list --exclude-drafts
  gh-axi release view v1.2.0 --full
  gh-axi release create v1.3.0 --body-file notes.md --draft dist/app.zip
  gh-axi release edit v1.3.0 --prerelease=false --latest
```

## repo

Command: `gh-axi repo --help`

```text
usage: gh-axi repo <subcommand> [flags]
subcommands[6]:
  view [owner/name], create [name], edit, clone <repo>, fork [repo], list [owner]
flags{view}:
  --repo <owner/name> or exactly one positional owner/name; choose one selector
flags{create}:
  --public, --private, --internal, --description, --clone, --template
  --source <path> (publish existing local repo; name defaults to source dir name), --push, --remote <name> (both require --source)
flags{edit}:
  --description, --visibility, --default-branch, --enable-issues, --enable-wiki
flags{fork}:
  --clone, --remote
flags{list}:
  --limit <n> (default 30), --visibility, --language, --archived
examples:
  gh-axi repo view
  gh-axi repo view --repo owner/name
  gh-axi repo view owner/name
  gh-axi repo create my-project --public --description "A new project"
  gh-axi repo create --public --source . --push
  gh-axi repo list --visibility public --language TypeScript
```

## run

Command: `gh-axi run --help`

```text
usage: gh-axi run <subcommand> [flags]
subcommands[7]:
  list, view <id>, watch <id>, rerun <id>, cancel <id>, delete <id>, download <id>
note:
  manages existing runs; to trigger (dispatch) a workflow, use `gh-axi workflow run <name> --ref <ref>`
flags{list}:
  --workflow, --branch, --status, --event, --user, --commit, --limit (default 10), --fields <a,b,c>
flags{view}:
  --job <job-id>, --log (or --verbose), --log-failed, --conclusion <success|failure|cancelled|skipped> (filter jobs by conclusion)
  long --log/--log-failed output keeps the tail and may include full_log for grep searches
flags{rerun}:
  --failed, --debug, --job
flags{download}:
  --name, --dir
examples:
  gh-axi run list --workflow ci.yml --status failure
  gh-axi run view 123456 --log-failed
  gh-axi run rerun 123456 --failed
```

## search

Command: `gh-axi search --help`

```text
usage: gh-axi search <type> <query> [flags]
types[5]:
  issues, prs, repos, commits, code
flags{common}:
  --repo, --owner, --state, --label, --assignee, --author, --sort, --limit <n> (default 1000)
flags{prs}:
  --draft, --review
flags{repos}:
  --language, --stars (e.g. ">100")
flags{code}:
  --language
examples:
  gh-axi search issues "login bug" --repo octo/repo --state open
  gh-axi search prs "feat" --author alice --sort updated
  gh-axi search repos "cli tool" --language Go --stars ">50"
```

## secret

Command: `gh-axi secret --help`

```text
usage: gh-axi secret <subcommand> [flags]
subcommands[3]:
  list, set <name>, delete <name>
flags[1]:
  --env/-e <environment> (all subcommands): scope to a deployment environment
flags{set}:
  value is read only from piped stdin; --body/-b is not accepted for secrets
values are never printed: `list` only exposes name and update time, matching `gh secret list`
scope: repository (default) or --env <environment>; other gh scopes (--org/--user/--app) are rejected, not silently ignored
examples:
  gh-axi secret list
  gh-axi secret list --env production
  echo -n "sk-..." | gh-axi secret set OPENAI_API_KEY
  echo -n "$(cat cert.p12 | base64)" | gh-axi secret set CSC_LINK --env production
  gh-axi secret delete OPENAI_API_KEY --env production
```

## setup

Command: `gh-axi setup --help`

```text
usage: gh-axi setup hooks
Install or repair agent SessionStart hooks for gh-axi ambient context.

examples:
  gh-axi setup hooks
```

## stack

Command: `gh-axi stack --help`

```text
usage: gh-axi stack <subcommand> [args] [flags]
subcommands[16]:
  view, init <branches...>, add [branch], checkout <stack|pr|url|branch>, push, submit, sync, rebase [branch], link <refs...>, unstack [stack], merge <stack|pr>, up [n], down [n], top, bottom, trunk
flags{init}: --base <branch>
flags{add}: --message <text>, --all, --update
flags{push}: --remote <name>
flags{submit}: --open, --remote <name> (--auto is always applied)
flags{sync}: --prune, --remote <name>
flags{rebase}: --downstack, --upstack, --no-trunk, --continue, --abort, --remote <name>, --committer-date-is-author-date, --preserve-dates
flags{link}: --base <branch>, --open, --remote <name>
flags{unstack}: --local
flags{merge}: --merge-method <merge|squash|rebase>, --merge, --squash, --rebase (--yes is always applied)
notes:
  Requires the official extension: gh extension install github/gh-stack
  Operates on the git repository in the current working directory; -R, --repo, and GH_REPO are not supported
examples:
  gh-axi stack init feature-model feature-api
  gh-axi stack submit --open
  gh-axi stack view
  gh-axi stack rebase --continue
  gh-axi stack merge 42 --squash
```

## variable

Command: `gh-axi variable --help`

```text
usage: gh-axi variable <subcommand> [flags]
subcommands[3]:
  list, set <name>, delete <name>
flags{set}:
  --body/-b <value> (reads from stdin if omitted)
examples:
  gh-axi variable list
  gh-axi variable set NODE_ENV --body production
  echo -n "production" | gh-axi variable set NODE_ENV
  gh-axi variable delete NODE_ENV
```

## workflow

Command: `gh-axi workflow --help`

```text
usage: gh-axi workflow <subcommand> [flags]
subcommands[5]:
  list, view <id|name>, run <id|name>, enable <id|name>, disable <id|name>
flags{list}:
  --limit <n> (default 20), --all
flags{run}:
  --ref <git-ref>, --field <key=val> (repeatable)
examples:
  gh-axi workflow list
  gh-axi workflow run ci.yml --ref main
  gh-axi workflow disable 12345
```
