#!/usr/bin/env python3
"""
Re-submit failed PsiMassRegion CRAB jobs when resubmit/recover is blocked (>30d).

For each PD with failed jobs:
  1) crab report --recovery=failed  -> failedLumis.json
  2) crab submit with lumiMask=failedLumis.json and requestName *_retry

Usage (cmsenv + crab-setup):
  cd $CMSSW_BASE/src/HiAnalysis/HiOnia/test
  python3 resubmit_failed_retry.py --pd 0
  python3 resubmit_failed_retry.py --pds 0,2,8,10,18,26,27,42,44,46,48,56,58
  python3 resubmit_failed_retry.py --pds 0,2 --dryrun
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    from CRABAPI.RawCommand import crabCommand
    from CRABClient.ClientExceptions import ClientException
    from CRABClient.UserUtilities import config
except ModuleNotFoundError as exc:
    sys.exit(
        f"ERROR: CRAB not available ({exc}). Run cmsenv && source /cvmfs/cms.cern.ch/common/crab-setup.sh"
    )

from http.client import HTTPException

SCRIPT_DIR = Path(__file__).resolve().parent
WORK_AREA = SCRIPT_DIR / "crab_projects_PsiMassRegion"
REPORT_ROOT = SCRIPT_DIR / "crab_reports_retry"
DEFAULT_PDS = [0, 2, 8, 10, 18, 26, 27, 42, 44, 46, 48, 56, 58]


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--pd", type=int, default=None)
    p.add_argument("--pds", type=str, default=None, help="Comma-separated PD list")
    p.add_argument("--dryrun", action="store_true")
    p.add_argument("--suffix", default=None, help="RequestName suffix (default: retryYYYYMMDD)")
    p.add_argument("--max-job-runtime-min", type=int, default=2750)
    return p.parse_args()


def dataset_for_pd(pd: int) -> str:
    if pd < 15:
        return f"/HIPhysicsRawPrime{pd}/HIRun2024A-PromptReco-v1/MINIAOD"
    if pd == 36:
        return "/HIPhysicsRawPrime36/HIRun2024A-OfflinePromptReco-v2/MINIAOD"
    return f"/HIPhysicsRawPrime{pd}/HIRun2024A-OfflinePromptReco-v1/MINIAOD"


def project_dir(pd: int) -> Path:
    return WORK_AREA / f"crab_Psi_EraA_RawPrime{pd}"


def make_config(lumi_json: Path, request_name: str, dataset: str, max_runtime: int):
    cfg = config()
    cfg.section_("General")
    cfg.General.workArea = str(WORK_AREA)
    cfg.General.requestName = request_name
    cfg.General.transferOutputs = True
    cfg.General.transferLogs = True

    cfg.section_("JobType")
    cfg.JobType.pluginName = "Analysis"
    cfg.JobType.psetName = "psianalyzer_PbPb2024_HIPhysicsRawPrime_cfg.py"
    cfg.JobType.maxMemoryMB = 2400
    cfg.JobType.allowUndistributedCMSSW = True
    cfg.JobType.maxJobRuntimeMin = max_runtime

    cfg.section_("Data")
    cfg.Data.inputDBS = "global"
    cfg.Data.inputDataset = dataset
    cfg.Data.splitting = "EventAwareLumiBased"
    cfg.Data.unitsPerJob = 2000000
    cfg.Data.allowNonValidInputDataset = True
    cfg.Data.publication = False
    cfg.Data.lumiMask = str(lumi_json.resolve())
    cfg.Data.outputDatasetTag = request_name
    cfg.Data.outLFNDirBase = (
        "/store/group/phys_heavyions/dizhang/"
        "run3_2024_PbPb5p36TeV_cohJpsi/data_tree/onia_tree/"
    )

    cfg.section_("Site")
    cfg.Site.storageSite = "T2_CH_CERN"
    cfg.Site.whitelist = ["T2_US_*", "T2_CH_CERN", "T1_US_*"]
    return cfg


def crab_report_failed(proj: Path, outdir: Path) -> Path:
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "crab",
        "report",
        "-d",
        str(proj),
        "--recovery=failed",
        "--outputdir",
        str(outdir),
    ]
    print("  $", " ".join(cmd))
    subprocess.run(cmd, check=True)
    lumi = outdir / "failedLumis.json"
    if not lumi.exists():
        raise FileNotFoundError(f"Missing {lumi}")
    with open(lumi) as f:
        data = json.load(f)
    if not data:
        raise ValueError("failedLumis.json is empty")
    return lumi


def count_ls(path: Path) -> int:
    with open(path) as f:
        d = json.load(f)
    return sum(hi - lo + 1 for ranges in d.values() for lo, hi in ranges)


def main():
    args = parse_args()
    if args.pds:
        pds = [int(x.strip()) for x in args.pds.split(",") if x.strip()]
    elif args.pd is not None:
        pds = [args.pd]
    else:
        pds = DEFAULT_PDS

    suffix = args.suffix or f"retry{datetime.now():%Y%m%d}"
    ok = skip = err = 0

    print(f"Retry submit for PDs: {pds}  suffix={suffix}  dryrun={args.dryrun}")

    for pd in pds:
        proj = project_dir(pd)
        tag = f"Psi_EraA_RawPrime{pd}_{suffix}"
        report_dir = REPORT_ROOT / f"PD{pd}"
        print(f"\n=== PD{pd} ===")
        if not proj.is_dir():
            print(f"  SKIP: no project {proj}")
            skip += 1
            continue
        try:
            lumi_json = crab_report_failed(proj, report_dir)
            nls = count_ls(lumi_json)
            print(f"  failedLumis: {lumi_json}  ({nls} LS)")
        except subprocess.CalledProcessError as e:
            print(f"  ERROR report: {e}")
            err += 1
            continue
        except (FileNotFoundError, ValueError) as e:
            print(f"  SKIP: {e}")
            skip += 1
            continue

        dataset = dataset_for_pd(pd)
        cfg = make_config(lumi_json, tag, dataset, args.max_job_runtime_min)
        print(f"  submit {tag}  dataset={dataset}")
        try:
            crabCommand("submit", config=cfg, dryrun=args.dryrun)
            print(f"  OK PD{pd}")
            ok += 1
        except (HTTPException, ClientException) as e:
            print(f"  ERROR submit PD{pd}: {e}")
            err += 1

    print(f"\n=== done: ok={ok} skip={skip} err={err} ===")
    if err:
        sys.exit(1)


if __name__ == "__main__":
    main()
