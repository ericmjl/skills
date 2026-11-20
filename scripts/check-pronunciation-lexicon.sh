#!/usr/bin/env bash
# Compare each listed pronunciation-lexicon copy to the pinned SHA-256
# of the canonical file in ericmjl/skills-private. This repo does not
# fetch the private file.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIN_FILE="${ROOT}/scripts/pronunciation-lexicon.sha256"
COPIES_FILE="${ROOT}/scripts/pronunciation-lexicon-copies.txt"

if [[ ! -f "${PIN_FILE}" ]]; then
  echo "Error: missing pin file scripts/pronunciation-lexicon.sha256" >&2
  exit 1
fi

PIN_HASH=""
while IFS= read -r LINE || [[ -n "${LINE}" ]]; do
  PATH_REL="${LINE%%#*}"
  PATH_REL="${PATH_REL%"${PATH_REL##*[![:space:]]}"}"
  PATH_REL="${PATH_REL#"${PATH_REL%%[![:space:]]*}"}"
  if [[ -z "${PATH_REL}" ]]; then
    continue
  fi
  if [[ "${PATH_REL}" =~ ^[0-9a-fA-F]{64}$ ]]; then
    PIN_HASH="${PATH_REL,,}"
    break
  fi
  echo "Error: expected a 64-character SHA-256 in scripts/pronunciation-lexicon.sha256, got: ${PATH_REL}" >&2
  exit 1
done < "${PIN_FILE}"

if [[ -z "${PIN_HASH}" ]]; then
  echo "Error: no SHA-256 found in scripts/pronunciation-lexicon.sha256" >&2
  exit 1
fi

echo "Pinned canonical sha256=${PIN_HASH}"

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
  if [[ "${COPY_HASH}" != "${PIN_HASH}" ]]; then
    echo "Error: ${PATH_REL} does not match the pinned canonical SHA-256" >&2
    echo "  pinned ${PIN_HASH}" >&2
    echo "  copy   ${COPY_HASH}" >&2
    FAILED=1
  else
    echo "OK: ${PATH_REL}"
  fi
done < "${COPIES_FILE}"

if [[ "${FOUND}" -eq 0 ]]; then
  echo "Notice: no copies listed in scripts/pronunciation-lexicon-copies.txt; nothing to compare."
fi

exit "${FAILED}"
