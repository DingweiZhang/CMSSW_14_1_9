#!/bin/bash
# Copy Onia_2023_cohJpsi_official.tar.gz to the lab host.
# On this same lxplus node:
#   ssh -f -N -M -S /tmp/$USER/cm-zhangdw-pbpb2024 -p 10023 zhangdw@222.200.137.16
#   nohup bash transfer_cohMC_tar_to_lab.sh >/dev/null 2>&1 &
set -u
SOCK="/tmp/${USER}/cm-zhangdw-pbpb2024"
PORT=10023
HOST="zhangdw@222.200.137.16"
DEST="/public/home/zhangdw/cms_cohJpsi/mc_cohjpsi_pbpb5p36_2023"
SRC="/afs/cern.ch/user/d/dizhang/eosHin/dizhang/run3_2023_PbPb5p36TeV_cohJpsi/mc_coherent_Jpsi_tree/GGToCoherentJPsiToMuMu_TuneCP5_5p36TeV_starlight-pythia8/Onia_2023_cohJpsi_official.tar.gz"
BASE="$(basename "$SRC")"
LOG="${HOME}/cohMC_tar_transfer.log"
SSH=(ssh -n -o ControlPath="$SOCK" -o BatchMode=yes -p "$PORT")

log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" | tee -a "$LOG"; }

if [[ ! -f "$SRC" ]]; then
  log "ERROR: missing ${SRC}"
  exit 1
fi
src_size="$(stat -c %s "$SRC")"

if ! "${SSH[@]}" "$HOST" "mkdir -p '${DEST}'" >>"$LOG" 2>&1; then
  log "ERROR: SSH control socket ${SOCK} is not usable. Start it on this node first."
  exit 1
fi

log "START size=${src_size} dest=${DEST}/${BASE}"
if rsync -a --partial --info=progress2 \
    -e "ssh -o ControlPath=${SOCK} -o BatchMode=yes -p ${PORT}" \
    "$SRC" "${HOST}:${DEST}/${BASE}" >>"$LOG" 2>&1; then
  :
else
  log "WARN rsync failed, trying scp"
  if ! scp -o ControlPath="$SOCK" -o BatchMode=yes -P "$PORT" \
      "$SRC" "${HOST}:${DEST}/${BASE}" </dev/null >>"$LOG" 2>&1; then
    log "FAIL scp ${BASE}"
    exit 1
  fi
fi

dst_size="$("${SSH[@]}" "$HOST" "stat -c %s '${DEST}/${BASE}' 2>/dev/null || echo 0")"
if [[ "$src_size" == "$dst_size" && "$src_size" != 0 ]]; then
  log "OK ${BASE} ${dst_size}"
else
  log "FAIL size local=${src_size} remote=${dst_size}"
  exit 1
fi
