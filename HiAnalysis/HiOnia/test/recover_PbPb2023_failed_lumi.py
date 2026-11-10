#!/usr/bin/env python3
"""
Submit a new 2023 OniaTree task for lumis that crab resubmit would not rerun.

For each PD:
  1) crab report --recovery=failed -> failedLumis.json
  2) crab submit with that mask and a new requestName

The original request names Onia_2023_RawPrimeN stay untouched.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

try:
    from CRABAPI.RawCommand import crabCommand
    from CRABClient.ClientExceptions import ClientException
    from CRABClient.UserUtilities import config
except ModuleNotFoundError as exc:
    sys.exit(
        "ERROR: CRAB python modules are not available "
        f"({exc.name}).\n"
        "  cmsenv && source /cvmfs/cms.cern.ch/common/crab-setup.sh prod"
    )

from http.client import HTTPException

SCRIPT_DIR = Path(__file__).resolve().parent
WORK_AREA = SCRIPT_DIR / "crab_projects_PbPb2023_Oniatree"
REPORT_ROOT = SCRIPT_DIR / "crab_reports_PbPb2023_failedlumi"
LUMI_MASK = SCRIPT_DIR / "Cert_Collisions2023HI_374288_375823_Good_ZDC_Muon.json"
OUT_LFN = "/store/user/dizhang/PbPb2023_Oniatree/"
FAILED_PDS = [3, 7, 9, 18, 23, 29]


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dryrun", action="store_true")
    parser.add_argument(
        "--pds",
        default=",".join(str(pd) for pd in FAILED_PDS),
        help="Comma-separated PD numbers (default: the six PDs still failed).",
    )
    return parser.parse_args()


def project_dir(pd: int) -> Path:
    return WORK_AREA / f"crab_Onia_2023_RawPrime{pd}"


def count_lumis(path: Path) -> int:
    with open(path) as handle:
        data = json.load(handle)
    return sum(hi - lo + 1 for ranges in data.values() for lo, hi in ranges)


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
    if not lumi.is_file():
        raise FileNotFoundError(f"Missing {lumi}")
    if count_lumis(lumi) == 0:
        raise ValueError(f"{lumi} has no lumis")
    return lumi


def make_config(pd: int, lumi_json: Path, request_name: str):
    cfg = config()
    cfg.section_("General")
    cfg.General.workArea = str(WORK_AREA)
    cfg.General.requestName = request_name
    cfg.General.transferOutputs = True
    cfg.General.transferLogs = False

    cfg.section_("JobType")
    cfg.JobType.pluginName = "Analysis"
    cfg.JobType.psetName = "psianalyzer_PbPb2023_HIPhysicsRawPrime_cfg.py"
    cfg.JobType.maxMemoryMB = 2400
    cfg.JobType.allowUndistributedCMSSW = True
    cfg.JobType.maxJobRuntimeMin = 2750

    cfg.section_("Data")
    cfg.Data.inputDBS = "global"
    cfg.Data.inputDataset = (
        f"/HIPhysicsRawPrime{pd}/HIRun2023A-PromptReco-v2/MINIAOD"
    )
    cfg.Data.splitting = "EventAwareLumiBased"
    cfg.Data.unitsPerJob = 1000000
    cfg.Data.allowNonValidInputDataset = True
    cfg.Data.publication = False
    cfg.Data.runRange = "374288-375823"
    # Failed lumis are already inside the original Good ZDC + muon JSON.
    cfg.Data.lumiMask = str(lumi_json.resolve())
    cfg.Data.outputDatasetTag = request_name
    cfg.Data.outLFNDirBase = OUT_LFN

    cfg.section_("Site")
    cfg.Site.storageSite = "T2_US_Vanderbilt"
    cfg.Site.whitelist = ["T2_CH_CERN", "T2_US_*", "T1_US_*"]
    return cfg


def main():
    args = parse_args()
    pds = [int(item) for item in args.pds.split(",") if item.strip()]
    if not LUMI_MASK.is_file():
        raise SystemExit(f"Original lumi mask not found: {LUMI_MASK}")

    ok = skip = err = 0
    for pd in pds:
        request_name = f"Onia_2023_RawPrime{pd}_failedLumi"
        proj = project_dir(pd)
        report_dir = REPORT_ROOT / f"RawPrime{pd}"
        print(f"\n=== RawPrime{pd} ===")
        if not proj.is_dir():
            print(f"  SKIP: no project {proj}")
            skip += 1
            continue
        new_dir = WORK_AREA / f"crab_{request_name}"
        if new_dir.exists():
            print(f"  SKIP: {new_dir.name} already exists")
            skip += 1
            continue
        lumi_json = report_dir / "failedLumis.json"
        if lumi_json.is_file() and count_lumis(lumi_json) > 0:
            print(f"  reuse {lumi_json} ({count_lumis(lumi_json)} LS)")
        else:
            try:
                lumi_json = crab_report_failed(proj, report_dir)
                print(f"  failedLumis: {lumi_json} ({count_lumis(lumi_json)} LS)")
            except (subprocess.CalledProcessError, OSError, ValueError) as exc:
                print(f"  ERROR report: {exc}")
                err += 1
                continue

        cfg = make_config(pd, lumi_json, request_name)
        print(
            f"  {'dry-run' if args.dryrun else 'submit'} {request_name}"
            f"  mask={lumi_json.name}"
        )
        try:
            crabCommand("submit", config=cfg, dryrun=args.dryrun)
            print(f"  OK RawPrime{pd}")
            ok += 1
        except (HTTPException, ClientException) as exc:
            print(f"  ERROR submit RawPrime{pd}: {exc}")
            err += 1

    print(f"\n=== done: ok={ok} skip={skip} err={err} ===")
    if err:
        sys.exit(1)


if __name__ == "__main__":
    main()
