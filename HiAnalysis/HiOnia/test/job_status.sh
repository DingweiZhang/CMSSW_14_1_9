#!/bin/bash
# CRAB task status for PsiMassRegion PbPb2024 (and local crab_projects*).
#
# Default workArea: ./crab_projects_PsiMassRegion
#
# Usage:
#   ./job_status.sh                          # compact table, default workArea
#   ./job_status.sh /path/to/crab_projects_* # explicit workArea
#   CRAB_WORK_AREA=... ./job_status.sh
#   ./job_status.sh -f                       # full crab status per PD
#   ./job_status.sh -e                       # verboseErrors (failed PDs only)
#   ./job_status.sh --failed                 # only PDs with failed jobs
#   ./job_status.sh 17                       # single RawPrime17 (EraA) only
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MODE="summary"
ONLY_FAILED=0
PD_FILTER=""

usage() {
  sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'
  exit "${1:-0}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage 0 ;;
    -f|--full) MODE="full" ;;
    -e|--errors) MODE="errors" ;;
    --failed) ONLY_FAILED=1 ;;
    -[0-9]*|[0-9]*) PD_FILTER="${1#-}" ;;
    crab_projects*|*crab_projects*) CRAB_WORK_AREA="$1" ;;
    /*|*/*) CRAB_WORK_AREA="$1" ;;
    *) echo "Unknown argument: $1" >&2; usage 1 ;;
  esac
  shift
done

if [[ -z "${CRAB_WORK_AREA:-}" ]]; then
  CRAB_WORK_AREA="${SCRIPT_DIR}/crab_projects_PsiMassRegion"
fi
if [[ ! -d "${CRAB_WORK_AREA}" ]]; then
  CRAB_WORK_AREA="$(ls -td "${SCRIPT_DIR}"/crab_projects* 2>/dev/null | head -1 || true)"
fi
if [[ -z "${CRAB_WORK_AREA:-}" || ! -d "${CRAB_WORK_AREA}" ]]; then
  echo "ERROR: no CRAB workArea found. Set CRAB_WORK_AREA or pass path." >&2
  echo "  e.g. ${SCRIPT_DIR}/crab_projects_PsiMassRegion" >&2
  exit 1
fi

if ! command -v crab >/dev/null 2>&1; then
  echo "ERROR: crab not in PATH. Run: cmsenv" >&2
  exit 1
fi

# shellcheck disable=SC2012
mapfile -t PROJECT_DIRS < <(
  ls -d "${CRAB_WORK_AREA}"/crab_* 2>/dev/null \
    | while read -r d; do
        bn="$(basename "$d")"
        if [[ "$bn" =~ _RawPrime([0-9]+)$ ]]; then
          printf 'A%03d %s\n' "${BASH_REMATCH[1]}" "$d"
        elif [[ "$bn" =~ _RawPrime([0-9]+)_v([12])$ ]]; then
          printf 'B%03d%1d %s\n' "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}" "$d"
        else
          printf 'zzz %s\n' "$d"
        fi
      done \
    | sort -k1,1 \
    | awk '{print $2}'
)

if [[ -n "${PD_FILTER}" ]]; then
  filtered=()
  for d in "${PROJECT_DIRS[@]}"; do
    bn="$(basename "$d")"
    [[ "$bn" =~ _RawPrime${PD_FILTER}$ || "$bn" =~ _RawPrime${PD_FILTER}_v[12]$ ]] && filtered+=("$d")
  done
  PROJECT_DIRS=("${filtered[@]}")
  if [[ ${#PROJECT_DIRS[@]} -eq 0 ]]; then
    echo "ERROR: no project matching RawPrime${PD_FILTER} under ${CRAB_WORK_AREA}" >&2
    exit 1
  fi
fi

if [[ ${#PROJECT_DIRS[@]} -eq 0 ]]; then
  echo "ERROR: no crab_* projects under ${CRAB_WORK_AREA}" >&2
  exit 1
fi

_parse_job_line() {
  local line="$1"
  local state n tot
  state="$(echo "$line" | grep -oE 'failed|finished|running|idle|transferring|queued|cancelled|paused' | head -1)"
  [[ -z "$state" ]] && return 0
  if [[ "$line" =~ \(([[:space:]]*([0-9]+)[[:space:]]*/[[:space:]]*([0-9]+)[[:space:]]*)\) ]]; then
    n="${BASH_REMATCH[2]}"
    tot="${BASH_REMATCH[3]}"
    echo "${state} ${n} ${tot}"
  fi
}

_crab_status_text() {
  local dir="$1"
  crab status -d "$dir" 2>/dev/null
}

_parse_status() {
  local text="$1"
  local server tot failed fin run idle xfer
  server="$(echo "$text" | awk -F'\t' '/^Status on the CRAB server:/{gsub(/^[ \t]+/,"",$2); print $2; exit}')"
  tot=0 failed=0 fin=0 run=0 idle=0 xfer=0
  while IFS= read -r line; do
    [[ "$line" != *"("*"/"*")"* ]] && continue
    read -r st n t < <(_parse_job_line "$line") || continue
    [[ -z "${st:-}" ]] && continue
    tot="${t:-$tot}"
    case "$st" in
      failed) failed="$n" ;;
      finished) fin="$n" ;;
      running) run="$n" ;;
      idle) idle="$n" ;;
      transferring) xfer="$n" ;;
    esac
  done < <(echo "$text" | sed -n '/^Jobs status:/,/^$/p')
  echo "${server:-?}|${tot:-0}|${failed:-0}|${fin:-0}|${run:-0}|${idle:-0}|${xfer:-0}"
}

_pd_tag() {
  local bn
  bn="$(basename "$1")"
  if [[ "$bn" =~ crab_Psi_EraA_RawPrime([0-9]+)$ ]]; then
    echo "EraA_PD${BASH_REMATCH[1]}"
  elif [[ "$bn" =~ crab_Psi_EraB_RawPrime([0-9]+)_v([12])$ ]]; then
    echo "EraB_PD${BASH_REMATCH[1]}_v${BASH_REMATCH[2]}"
  else
    echo "$bn"
  fi
}

echo "workArea: ${CRAB_WORK_AREA}"
echo "projects: ${#PROJECT_DIRS[@]}"
echo ""

if [[ "$MODE" == "full" ]]; then
  for d in "${PROJECT_DIRS[@]}"; do
    echo "================================================================================"
    echo "$(_pd_tag "$d")  ->  $d"
    crab status -d "$d"
    echo ""
  done
  exit 0
fi

if [[ "$MODE" == "errors" ]]; then
  for d in "${PROJECT_DIRS[@]}"; do
    st="$(_parse_status "$(_crab_status_text "$d")")"
    failed="${st#*|}"; failed="${failed%%|*}"
    [[ "${failed:-0}" -eq 0 ]] && continue
    echo "================================================================================"
    echo "$(_pd_tag "$d")  (failed=${failed})"
    crab status -d "$d" --verboseErrors
    echo ""
  done
  exit 0
fi

printf "%-16s %-14s %6s %6s %6s %6s %6s %6s\n" \
  "PD" "CRAB_server" "total" "fail" "done" "run" "idle" "xfer"
printf "%-16s %-14s %6s %6s %6s %6s %6s %6s\n" \
  "----------------" "--------------" "------" "------" "------" "------" "------" "------"

sum_tot=0 sum_fail=0 sum_fin=0 sum_run=0
n_fail_pd=0 n_done_pd=0

for d in "${PROJECT_DIRS[@]}"; do
  text="$(_crab_status_text "$d")" || {
    printf "%-16s %-14s %6s\n" "$(_pd_tag "$d")" "QUERY_FAIL" "-"
    continue
  }
  IFS='|' read -r server tot failed fin run idle xfer < <(_parse_status "$text")
  if [[ "$ONLY_FAILED" == 1 && "${failed:-0}" -eq 0 ]]; then
    continue
  fi
  printf "%-16s %-14s %6s %6s %6s %6s %6s %6s\n" \
    "$(_pd_tag "$d")" "$server" "$tot" "$failed" "$fin" "$run" "$idle" "$xfer"
  sum_tot=$((sum_tot + tot))
  sum_fail=$((sum_fail + failed))
  sum_fin=$((sum_fin + fin))
  sum_run=$((sum_run + run))
  [[ "${failed:-0}" -gt 0 ]] && n_fail_pd=$((n_fail_pd + 1))
  [[ "${tot:-0}" -gt 0 && "${fin:-0}" -eq "${tot}" && "${failed:-0}" -eq 0 ]] && n_done_pd=$((n_done_pd + 1))
done

echo ""
echo "campaign totals: jobs=${sum_tot}  failed=${sum_fail}  finished=${sum_fin}  running=${sum_run}"
echo "PDs complete (100% finished, 0 failed): ${n_done_pd}/${#PROJECT_DIRS[@]}"
echo "PDs with failures: ${n_fail_pd}"
echo ""
echo "Tips:"
echo "  ./job_status.sh -f              # full crab status each PD"
echo "  ./job_status.sh -e              # verboseErrors for failed PDs"
echo "  ./job_status.sh --failed        # table: failed jobs only"
echo "  ./job_status.sh 17              # RawPrime17 only"
echo "  crab status -d <project_dir>    # one task"
