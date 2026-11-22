# Sensitive paths (step 0)

Match every `files[].path` from `gh pr view <PR> --json files` against these
globs. Basename matches count (`Dockerfile` matches `*Dockerfile*`;
`src/alembic/versions/x.py` matches `alembic/**`). Also flag every path
with `changeType` of `DELETED`.

This list is a path check only. It does not decide merge.

Report each hit as: path, glob (or `deleted`), and a one-line why.

## CI and workflows

- `.github/workflows/**`
- `.github/actions/**`
- `.gitlab-ci.yml`
- `Jenkinsfile*`
- `.circleci/**`
- `azure-pipelines*.yml`
- `.travis.yml`
- `bitbucket-pipelines.yml`

## Ownership

- `*CODEOWNERS`

## Manifests and lockfiles

- `package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`
- `requirements*.txt`, `Pipfile`, `Pipfile.lock`
- `pyproject.toml`, `poetry.lock`, `uv.lock`
- `Cargo.toml`, `Cargo.lock`
- `go.mod`, `go.sum`
- `pom.xml`, `build.gradle*`
- `Gemfile`, `Gemfile.lock`
- `composer.json`, `composer.lock`

## Containers

- `*Dockerfile*`, `*.dockerfile`
- `docker-compose*.yml`, `docker-compose*.yaml`

## Terraform / HCL

- `*.tf`, `*.tfvars`, `*.hcl`

## Migrations

- `*migrations*/**`
- `*migration*`
- `db/migrate/**`
- `alembic/**`
