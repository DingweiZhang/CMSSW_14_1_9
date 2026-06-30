#!/bin/bash
# Kill PsiMassRegion CRAB tasks (all, EraA only, or EraB only).
# Optionally remove EraB output on group EOS.
#
# Run from: CMSSW_14_1_9/src/HiAnalysis/HiOnia/test (cmsenv + crab-setup loaded)
#
# Examples:
#   ./kill_PsiMassRegion_crab.sh --era B --delete-eos --remove-local
#   ./kill_PsiMassRegion_crab.sh --era all
set -euo pipefail

WORKAREA="crab_projects_PsiMassRegion"
ERA="all"
DELETE_EOS=false
REMOVE_LOCAL=false

EOS_ONIA_BASE="/eos/cms/store/group/phys_heavyions/dizhang/run3_2024_PbPb5p36TeV_cohJpsi/data_tree/onia_tree"

usage() {
  cat <<EOF
Usage: $0 [OPTIONS]

Options:
  --era A|B|all       Which era tasks to kill (default: all)
  --delete-eos        Remove Psi_EraB_* output under group EOS (only with --era B)
  --remove-local      Remove local crab project dirs after kill
  -h, --help          Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --era)
      ERA="${2:?missing value for --era}"
      shift 2
      ;;
    --delete-eos)
      DELETE_EOS=true
      shift
      ;;
    --remove-local)
      REMOVE_LOCAL=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ ! -d "$WORKAREA" ]]; then
  echo "No $WORKAREA directory found."
  exit 1
fi

shopt -s nullglob
case "$ERA" in
  A)
    projects=("$WORKAREA"/crab_Psi_EraA_*)
    ;;
  B)
    projects=("$WORKAREA"/crab_Psi_EraB_*)
    ;;
  all)
    projects=("$WORKAREA"/crab_*)
    ;;
  *)
    echo "Invalid --era: $ERA (use A, B, or all)" >&2
    exit 1
    ;;
esac

if (( ${#projects[@]} == 0 )); then
  echo "No matching crab projects under $WORKAREA (era=$ERA)."
else
  echo "Killing ${#projects[@]} CRAB project(s) (era=$ERA)..."
  for d in "${projects[@]}"; do
    echo "==> crab kill -d $d"
    crab kill -d "$d" || true
  done
  echo "CRAB kill requests sent."
fi

if $DELETE_EOS; then
  if [[ "$ERA" != "B" ]]; then
    echo "ERROR: --delete-eos is only supported with --era B" >&2
    exit 1
  fi
  echo
  echo "Removing EraB output under $EOS_ONIA_BASE ..."
  n_removed=0
  mapfile -t pd_names < <(eos ls "$EOS_ONIA_BASE" 2>/dev/null || true)
  for pd in "${pd_names[@]}"; do
    pd_dir="${EOS_ONIA_BASE}/${pd}"
    mapfile -t sub_names < <(eos ls "$pd_dir" 2>/dev/null | grep '^Psi_EraB_' || true)
    for sub in "${sub_names[@]}"; do
      era_dir="${pd_dir}/${sub}"
      echo "==> eos rm -r $era_dir"
      eos rm -r "$era_dir"
      ((n_removed++)) || true
    done
  done
  echo "Removed $n_removed EraB output folder(s) on EOS."
fi

if $REMOVE_LOCAL; then
  echo
  echo "Removing local project dirs (era=$ERA)..."
  case "$ERA" in
    A) rm -rf "$WORKAREA"/crab_Psi_EraA_* ;;
    B) rm -rf "$WORKAREA"/crab_Psi_EraB_* ;;
    all) rm -rf "$WORKAREA"/crab_* ;;
  esac
  echo "Local crab project dirs removed."
fi

echo
echo "Done."
