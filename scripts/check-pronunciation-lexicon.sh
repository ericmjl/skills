#!/usr/bin/env bash
# Compare each listed pronunciation-lexicon copy to the canonical file
# at skills/explainer-video/lexicon.json.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CANONICAL="${ROOT}/skills/explainer-video/lexicon.json"
COPIES_FILE="${ROOT}/scripts/pronunciation-lexicon-copies.txt"

if [[ ! -f "${CANONICAL}" ]]; then
  echo "Error: missing canonical pronunciation lexicon skills/explainer-video/lexicon.json" >&2
  exit 1
fi

CANONICAL_HASH="$(sha256sum "${CANONICAL}" | awk '{print $1}')"
echo "Canonical skills/explainer-video/lexicon.json sha256=${CANONICAL_HASH}"

if [[ ! -f "${COPIES_FILE}" ]]; then
  echo "Error: missing copies manifest ${COPIES_FILE}" >&2
  exit 1
fi

FAILED=0
FOUND=0
while IFS= read -r LINE || [[ -n "${LINE}" ]]; do
  PATH_REL="${LINE%%#*}"
  PATH_REL="${PATH_REL%"${PATH_REL##*[![:space:]]}"}"
  PATH_REL="${PATH_REL#"${PATH_REL%%[![:space:]]*}"}"
  if [[ -z "${PATH_REL}" ]]; then
    continue
  fi
  FOUND=1
  COPY="${ROOT}/${PATH_REL}"
  if [[ ! -f "${COPY}" ]]; then
    echo "Error: listed copy is missing: ${PATH_REL}" >&2
    FAILED=1
    continue
  fi
  COPY_HASH="$(sha256sum "${COPY}" | awk '{print $1}')"
  if [[ "${COPY_HASH}" != "${CANONICAL_HASH}" ]]; then
    echo "Error: ${PATH_REL} does not match skills/explainer-video/lexicon.json" >&2
    echo "  canonical ${CANONICAL_HASH}" >&2
    echo "  copy      ${COPY_HASH}" >&2
    FAILED=1
  else
    echo "OK: ${PATH_REL}"
  fi
done < "${COPIES_FILE}"

if [[ "${FOUND}" -eq 0 ]]; then
  echo "Notice: no copies listed in scripts/pronunciation-lexicon-copies.txt; nothing to compare."
fi

exit "${FAILED}"
