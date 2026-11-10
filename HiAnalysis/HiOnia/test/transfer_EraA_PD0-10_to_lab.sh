#!/bin/bash
# Copy 2024 EraA PD0-10 Onia trees from Vanderbilt to the lab host.
# Requires, on this same lxplus node:
#   voms-proxy-init -voms cms --valid 192:00
#   ssh -f -N -M -S /tmp/$USER/cm-zhangdw-pbpb2024 -p 10023 zhangdw@222.200.137.16
# Then: nohup bash transfer_EraA_PD0-10_to_lab.sh >/dev/null 2>&1 &
set -u
SOCK="/tmp/${USER}/cm-zhangdw-pbpb2024"
PORT=10023
HOST="zhangdw@222.200.137.16"
DEST="/public/home/zhangdw/cms_cohJpsi/pbpb5p36_2024"
LIST="/eos/cms/store/group/phys_heavyions/dizhang/CMSSW_14_1_9/src/HiAnalysis/HiOnia/test/filelist_PsiMassRegion_EraA_vanderbilt.txt"
LOG="${HOME}/pb2024_eraA_pd0-10_transfer.log"
STAGE="/tmp/${USER}/eraA_stage"
XRD_HOST="xrootd-vanderbilt.sites.opensciencegrid.org"

log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" | tee -a "$LOG"; }

if ! voms-proxy-info -exists >/dev/null 2>&1; then
  log "ERROR: no CMS proxy on this node. Run voms-proxy-init -voms cms first."
  exit 1
fi
export X509_USER_PROXY
X509_USER_PROXY="$(voms-proxy-info -path)"

if ! ssh -n -S "$SOCK" -o BatchMode=yes -p "$PORT" "$HOST" "mkdir -p ${DEST}" >>"$LOG" 2>&1; then
  log "ERROR: SSH control socket ${SOCK} is not usable. Start it interactively first."
  exit 1
fi

mkdir -p "$STAGE"
log "START proxy=$(voms-proxy-info -timeleft)s dest=${DEST}"

n_ok=0
n_skip=0
n_fail=0
while IFS= read -r url; do
  [[ "$url" == root://* ]] || continue
  if [[ ! "$url" =~ HIPhysicsRawPrime([0-9]+)/Psi_EraA_RawPrime[0-9]+/ ]]; then
    continue
  fi
  pd="${BASH_REMATCH[1]}"
  if (( pd > 10 )); then
    continue
  fi
  lfn="${url#root://${XRD_HOST}/}"
  base="$(basename "$lfn")"
  remote="${DEST}/PD${pd}/${base}"
  src_size="$(xrdfs "$XRD_HOST" stat "$lfn" </dev/null | awk '/Size/{print $2; exit}')"
  dst_size="$(ssh -n -S "$SOCK" -o BatchMode=yes -p "$PORT" "$HOST" "stat -c %s '${remote}' 2>/dev/null || echo 0")"
  if [[ -n "$src_size" && "$src_size" == "$dst_size" && "$src_size" != 0 ]]; then
    log "SKIP PD${pd} ${base} ${src_size}"
    n_skip=$((n_skip + 1))
    continue
  fi
  ssh -n -S "$SOCK" -o BatchMode=yes -p "$PORT" "$HOST" "mkdir -p ${DEST}/PD${pd}" >>"$LOG" 2>&1
  tmp="${STAGE}/${base}"
  rm -f "$tmp"
  log "GET  PD${pd} ${base} src=${src_size:-unknown}"
  if ! xrdcp -f -S 8 "$url" "$tmp" </dev/null >>"$LOG" 2>&1; then
    log "FAIL xrdcp PD${pd} ${base}"
    rm -f "$tmp"
    n_fail=$((n_fail + 1))
    continue
  fi
  if ! scp -o ControlPath="$SOCK" -P "$PORT" "$tmp" "${HOST}:${remote}" </dev/null >>"$LOG" 2>&1; then
    log "FAIL scp PD${pd} ${base}"
    rm -f "$tmp"
    n_fail=$((n_fail + 1))
    continue
  fi
  dst_size="$(ssh -n -S "$SOCK" -o BatchMode=yes -p "$PORT" "$HOST" "stat -c %s '${remote}' 2>/dev/null || echo 0")"
  local_size="$(stat -c %s "$tmp")"
  rm -f "$tmp"
  if [[ "$local_size" == "$dst_size" && "$local_size" != 0 ]]; then
    log "OK   PD${pd} ${base} ${local_size}"
    n_ok=$((n_ok + 1))
  else
    log "FAIL size PD${pd} ${base} local=${local_size} remote=${dst_size}"
    n_fail=$((n_fail + 1))
  fi
done < "$LIST"

log "DONE ok=${n_ok} skip=${n_skip} fail=${n_fail}"
