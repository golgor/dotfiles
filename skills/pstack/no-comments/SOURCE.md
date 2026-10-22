# Source

- Upstream repository: `https://github.com/cursor/plugins`
- Plugin root: `https://github.com/cursor/plugins/tree/9b93e81fb2921b9263d9463c15bafeabfe3903aa/pstack`
- Source path: `pstack/skills/no-comments/`
- Skill origin: `https://github.com/cursor/plugins/tree/9b93e81fb2921b9263d9463c15bafeabfe3903aa/pstack/skills/no-comments`
- Adopted commit: `9b93e81fb2921b9263d9463c15bafeabfe3903aa`
- License: MIT, Copyright (c) 2026 Lauren Tan; see [LICENSE](LICENSE).

The earlier adoption record is retained: this skill was first adopted from
`https://github.com/backnotprop/pstack`, commit
`e44668c2aad92eacf4e84df47984121fefb11b82`, at `skills/no-comments/` and
`agents/comment-sicko.md`. The retained `comment-sicko` agent body is unchanged
from that historical adoption; its body SHA-256 is
`334fc4d4eabf6b22c0a0c68203b259e9d6212506f8d7b720b300da2b0abcff21`. Its
current bundled helper paths come from the Cursor pstack pack. The MIT license
and Lauren Tan copyright notice apply to the retained upstream material; the
full notice is preserved in [LICENSE](LICENSE).

This locally maintained skill preserves the prior deletion and approval
workflow, while its Pi adapter delegates named helpers to their absolute local
skill paths or to the parent through `contact_supervisor`. Review future
upstream changes by hand; no updater or manifest automation is used.
