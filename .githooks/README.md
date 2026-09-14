# Repository pre-commit check

This repository's hook checks the staged AST contract between the calibration
scorer and observation consumer. It loads the checker and both inputs from Git
index stage 0. It does not run either production program or model requests.

For a new clone, first inspect the current hooks configuration and active hook:

```sh
git config --show-origin --get core.hooksPath
git rev-parse --git-path hooks/pre-commit
```

If no custom hook or hooksPath is configured, enable the versioned entry:

```sh
git config --local core.hooksPath .githooks
git hook run pre-commit
```

If a custom hook already exists, preserve it and explicitly chain this hook;
do not overwrite the existing configuration. The hook and checker must both be
staged before the first checked commit. Subsequent commits are checked even if
the relevant files themselves are unchanged. Git's explicit hook bypass options
remain outside this local check's guarantees.

The mechanical check covers the score root, summary, final_assistant, and each
fidelity row. Other nested branches, field value types, execution semantics and
runtime effects are not checked. Unsupported constructions in the checked
scope fail with an explicit unresolved diagnostic. Run the companion selftest
for scope separation, the original field mismatch, and index/worktree cases.
