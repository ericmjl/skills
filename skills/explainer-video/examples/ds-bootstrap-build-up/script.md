# Artifact

A bootstrapped data science machine

# Voice

eric

# Format

build-up

# Beats

## Beat 0

- join: none
- spoken: One laptop, one global Python install, one notebook. That's a data science project.
- visual: A bare terminal prompt. `tree` prints one file, analysis.py, a marimo notebook, under ~/project-a.
- delta: analysis.py
- source: docs/project/index.md; docs/machine/system-software.md
- number: none

## Beat 1

- join: but
- spoken: But install packages for project B, and project A's notebook breaks.
- visual: A second project installs packages. Project A's notebook cell output flips to a red ImportError.
- delta: none
- source: docs/project/pixi.md
- number: none

## Beat 2

- join: therefore
- spoken: So every project gets its own isolated environment, defined with pixi. That's a per-project environment.
- visual: The tree grows pyproject.toml with a `# tool.pixi` comment. The two projects split into separate boxes, and the red error clears.
- delta: pyproject.toml
- source: docs/project/pixi.md; docs/project/index.md (1:1:1:1 rule)
- number: none

## Beat 3

- join: but
- spoken: Now projects can't break each other, but you overwrite last week's working analysis and start saving files like analysis_final_v3.
- visual: analysis.py gets overwritten. Copies stack up: analysis_final.py, analysis_final_v2.py, analysis_final_v3.py.
- delta: none
- source: docs/machine/git.md
- number: none

## Beat 4

- join: therefore
- spoken: So you track every change with Git, a powerful undo button. That's one Git repo per project.
- visual: The stacked copies collapse back into one file. .git/ appears, and a commit timeline scrubs back to last week.
- delta: .git/
- source: docs/machine/git.md ("powerful undo button"); docs/project/repo.md
- number: none

## Beat 5

- join: but
- spoken: But a colleague clones the repo, or you come back six months later, and the same spec installs different versions.
- visual: Two laptops install from the same pyproject.toml. Their package versions disagree, shown in red.
- delta: none
- source: docs/project/pixi.md (Long-term reproducibility through lock files)
- number: none

## Beat 6

- join: therefore
- spoken: So you commit pixi.lock, regenerated automatically on every change. That's the lockfile.
- visual: pixi.lock drops into the tree. Both laptops' version lists snap to the same numbers.
- delta: pixi.lock
- source: docs/project/pixi.md; docs/project/config-files.md
- number: none

## Beat 7

- join: but
- spoken: But git add dot just committed a two-gigabyte CSV and your database password.
- visual: A `git add .` sweeps a huge data.csv and a password line into the commit box, both flagged red.
- delta: none
- source: docs/project/config-files.md; docs/project/data-formats.md (data should not live in your repository)
- number: none

## Beat 8

- join: therefore
- spoken: So .gitignore keeps secrets out, a never-committed .env holds them, and data lives in external storage. That's .gitignore and .env.
- visual: .gitignore and .env appear. The CSV slides out to a storage bucket, and the password moves into .env, which is greyed out as ignored.
- delta: .env, .gitignore
- source: docs/project/config-files.md (.gitignore, .env, .env.example); docs/project/env-vars.md
- number: none

## Beat 9

- join: but
- spoken: But the same cleaning function is copied into five notebooks. Fix a bug in one, and four stay wrong.
- visual: Five notebook cards show the same clean() function. One copy turns green, and four stay red.
- delta: none
- source: docs/project/source.md (Phase 2, Write Everything Twice); docs/skills/refactor.md
- number: none

## Beat 10

- join: therefore
- spoken: So reused code moves into one importable package in the repo. That's the custom source package.
- visual: myproject/__init__.py appears. All five notebooks draw an import arrow to it, and they all turn green.
- delta: myproject/__init__.py
- source: docs/project/source.md; docs/skills/notebooks.md
- number: none

## Beat 11

- join: but
- spoken: Now data lives outside the repo, but every notebook hard-codes its own path, and your colleague can't run any of them.
- visual: Each notebook shows a different hard-coded path string. A colleague's laptop runs them, and each fails with FileNotFoundError.
- delta: none
- source: docs/project/catalog.md; docs/skills/notebooks.md (Data access best practices)
- number: none

## Beat 12

- join: therefore
- spoken: So the source package gets functions like load_customer_data that handle paths and connections. That's the data catalog.
- visual: data_loaders.py appears under myproject/. The path strings collapse into one call, load_customer_data().
- delta: myproject/data_loaders.py
- source: docs/project/catalog.md; docs/philosophies/source-truth.md
- number: none

## Beat 13

- join: but
- spoken: But change one shared function, and you silently break three notebooks. My thesis pipeline took a week to run, so every change took a week to check.
- visual: An edit to data_loaders.py sends a red crack through three notebooks. A calendar flips through seven days.
- delta: none
- source: docs/skills/test.md (week-long thesis pipeline story)
- number: none

## Beat 14

- join: therefore
- spoken: So you write pytest tests. Those are the tests.
- visual: tests/test___init__.py appears. A pytest run prints a row of green dots in seconds.
- delta: tests/test___init__.py
- source: docs/skills/test.md (pytest)
- number: none

## Beat 15

- join: but
- spoken: But tests only help if someone runs them right, and diffs fill with formatting noise.
- visual: A diff fills up with whitespace and quote-style changes, burying one real line. The test command is typed three different ways.
- delta: none
- source: docs/project/config-files.md; docs/skills/test.md
- number: none

## Beat 16

- join: therefore
- spoken: So checks run before every commit, settings live in pyproject.toml, and pixi run test standardizes commands. Those are pre-commit hooks and pixi tasks.
- visual: .pre-commit-config.yaml appears, and pyproject.toml re-lights with a `# tool.pixi.tasks` comment. The noisy diff shrinks to the one real line.
- delta: .pre-commit-config.yaml
- source: docs/project/config-files.md (.pre-commit-config.yaml, pyproject.toml); docs/project/pixi.md (Run tasks)
- number: none

## Beat 17

- join: but
- spoken: Now your laptop is green, but a teammate's laptop skips the hooks and main breaks.
- visual: Your laptop shows a green check. A teammate's commit bypasses the hooks, and the main branch line turns red.
- delta: none
- source: docs/project/cicd.md; docs/skills/collaboration.md
- number: none

## Beat 18

- join: therefore
- spoken: So GitHub Actions runs the same checks, from the lockfile, on every pull request. A green laptop and a green pipeline finally match. That's continuous integration.
- visual: .github/workflows/ appears. A pull request passes through a CI checkpoint, and the laptop check and the pipeline check light green side by side.
- delta: .github/workflows/
- source: docs/project/cicd.md (runners do not inherit local shell); docs/philosophies/source-truth.md (Pre-commit parity between laptop and CI)
- number: none

## Beat 19

- join: but
- spoken: But six months later nobody knows how to run the project.
- visual: The tree dims, and a question mark hovers over the repo.
- delta: none
- source: docs/project/docs.md
- number: none

## Beat 20

- join: therefore
- spoken: So docs move into the repo, organized with Diataxis: tutorials, how-to guides, explanations, reference, published by continuous integration. That's docs in the repo.
- visual: docs/index.md and mkdocs.yaml appear. Four labeled quadrants fill in (tutorials, how-to, explanation, reference), and a CI arrow publishes a site.
- delta: docs/index.md, mkdocs.yaml
- source: docs/project/docs.md (Diataxis, in-repo docs, CI publishing); docs/philosophies/automate.md
- number: none

## Beat 21

- join: but
- spoken: But the next project means rebuilding all this by hand, and names drift: sales-forecast, forecast-2020, my_env.
- visual: An empty second project. The three drifting names fly in and don't line up.
- delta: none
- source: docs/project/repo.md; docs/project/naming.md
- number: none

## Beat 22

- join: therefore
- spoken: So one command scaffolds the standard structure with consistent names. That's the project template.
- visual: The title bar reads `pyds project init · cookiecutter`. The whole tree flashes into existence at once.
- delta: none
- source: docs/project/repo.md (Automate the scaffolding of new projects); docs/project/pixi.md (pyds project init)
- number: none

## Beat 23

- join: but
- spoken: But your AI coding agent ignores all of it. It runs bare python and edits tests until they pass.
- visual: An agent cursor types `python script.py` instead of the pixi task, then rewrites an assert in tests/ so it passes.
- delta: none
- source: docs/ai/agents.md
- number: none

## Beat 24

- join: therefore
- spoken: So a file at the repo root gives it a code map and local rules: never modify a test to make it pass. That's AGENTS.md.
- visual: AGENTS.md drops into the tree root. The agent's edit jumps out of tests/ and into myproject/, and the test goes green unchanged.
- delta: AGENTS.md
- source: docs/ai/agents.md:71-72; docs/skills/test.md
- number: none

## Beat 25

- join: but
- spoken: But stuffing every procedure, like debugging failed continuous integration runs, into AGENTS.md bloats it, and you still re-explain those procedures.
- visual: AGENTS.md swells until it scrolls off screen. The same instructions get typed into chat again.
- delta: none
- source: docs/ai/skills.md
- number: none

## Beat 26

- join: therefore
- spoken: So reusable playbooks live in .agents/skills/, each a SKILL.md. Constraints stay in AGENTS.md; procedures become playbooks. Those are Skills.
- visual: .agents/skills/coherent-writing/SKILL.md appears. AGENTS.md shrinks back as the procedures slide out into the skills folder.
- delta: .agents/skills/coherent-writing/SKILL.md
- source: docs/ai/skills.md; docs/ai/operating-model.md (AGENTS.md vs. Skills decision rule)
- number: none

## Beat 27

- join: but
- spoken: Finally, your laptop dies. Git clone and pixi install bring back every project, but your shell setup and global tools are gone.
- visual: The screen goes black. A new laptop restores the project tree, but a second tree, ~/, sits empty.
- delta: none
- source: docs/machine/dotfiles.md; docs/machine/system-software.md
- number: none

## Beat 28

- join: therefore
- spoken: So a repo of your config files, with an install script, symlinks them into place, and pixi global and uv tool restore your command-line tools. That's dotfiles.
- visual: A second root, ~/dotfiles, appears. Symlink arrows snap .zshrc, .aliases and .path into ~/, and the command-line tools reappear.
- delta: ~/dotfiles/.aliases, ~/dotfiles/.path, ~/dotfiles/.zshrc, ~/dotfiles/install.sh
- source: docs/machine/dotfiles.md; docs/machine/uv.md; docs/shell/env-vars.md
- number: none

## Beat 29

- join: none
- spoken: And with that, you've bootstrapped your data science machine.
- visual: Both trees light up in full. A title card shows the artifact name.
- delta: none
- source: none
- number: none
