#!/usr/bin/env python3
"""
2023 PbPb OniaTree multicrab submitter.

Input is HIRun2023A HIPhysicsRawPrime0-31 PromptReco-v2 MINIAOD, the same
32 datasets as crabConfig_DATA_FORWARDSKIM_DiMu.py. Lumi mask is the 2023
Good ZDC + muon JSON (runs 374288-375823). Output goes to Vanderbilt:

  /store/user/dizhang/PbPb2023_Oniatree/<PD>/<requestName>/...

Run from this directory with CRAB loaded, e.g.:
  cd $CMSSW_BASE/src/HiAnalysis/HiOnia/test
  cmsenv
  source /cvmfs/cms.cern.ch/common/crab-setup.sh prod
  python3 multicrab_PbPb2023_Oniatree_cfg.py --dryrun --pd 0
  python3 multicrab_PbPb2023_Oniatree_cfg.py
"""
import argparse
import os
import sys

try:
    from CRABAPI.RawCommand import crabCommand
    from CRABClient.ClientExceptions import ClientException
    from CRABClient.UserUtilities import config
except ModuleNotFoundError as exc:
    sys.exit(
        "ERROR: CRAB python modules are not available "
        f"({exc.name}).\n"
        "Load the environment first:\n"
        "  cd $CMSSW_BASE\n"
        "  cmsenv\n"
        "  source /cvmfs/cms.cern.ch/common/crab-setup.sh prod\n"
        "Then rerun this script from HiOnia/test."
    )

from http.client import HTTPException


N_PD = 32  # HIPhysicsRawPrime0 .. HIPhysicsRawPrime31
LUMI_MASK = "Cert_Collisions2023HI_374288_375823_Good_ZDC_Muon.json"
OUT_LFN = "/store/user/dizhang/PbPb2023_Oniatree/"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Submit 2023 PbPb OniaTree CRAB jobs for HIPhysicsRawPrime0-31."
    )
    parser.add_argument(
        "--dryrun",
        action="store_true",
        help="Run crab submit in dry-run mode (no real submission).",
    )
    parser.add_argument(
        "--pd",
        type=int,
        default=None,
        metavar="N",
        help=f"Submit only HIPhysicsRawPrimeN (0-{N_PD - 1}; default: all).",
    )
    parser.add_argument(
        "--units-per-job",
        type=int,
        default=None,
        metavar="N",
        help="EventAwareLumiBased unitsPerJob (default: 1000000).",
    )
    parser.add_argument(
        "--max-job-runtime-min",
        type=int,
        default=None,
        metavar="MIN",
        help="Job wall time in minutes (default: 2750, CRAB max).",
    )
    parser.add_argument(
        "--max-memory-mb",
        type=int,
        default=None,
        metavar="MB",
        help="Job memory in MB (default: 2400).",
    )
    return parser.parse_args()


def make_base_config():
    cfg = config()
    cfg.section_("General")
    cfg.General.workArea = "crab_projects_PbPb2023_Oniatree"
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
    cfg.Data.splitting = "EventAwareLumiBased"
    cfg.Data.unitsPerJob = 1000000
    cfg.Data.allowNonValidInputDataset = True
    cfg.Data.publication = False
    cfg.Data.runRange = "374288-375823"
    cfg.Data.lumiMask = LUMI_MASK
    cfg.Data.outLFNDirBase = OUT_LFN

    cfg.section_("Site")
    cfg.Site.storageSite = "T2_US_Vanderbilt"
    # Jobs run where the input is available. storageSite is only the output site.
    cfg.Site.whitelist = ["T2_CH_CERN", "T2_US_*", "T1_US_*"]
    return cfg


def jobs(pd=None):
    pd_list = [pd] if pd is not None else list(range(N_PD))
    selected = []
    for i in pd_list:
        if i < 0 or i >= N_PD:
            raise SystemExit(f"PD {i} is outside 0-{N_PD - 1}.")
        selected.append(
            (
                f"Onia_2023_RawPrime{i}",
                f"/HIPhysicsRawPrime{i}/HIRun2023A-PromptReco-v2/MINIAOD",
            )
        )
    return selected


def submit(cfg, dryrun):
    mode = "dry-run" if dryrun else "submit"
    try:
        crabCommand("submit", config=cfg, dryrun=dryrun)
    except HTTPException as hte:
        print(f"Failed {mode} for {cfg.Data.inputDataset}: {hte.headers}")
    except ClientException as cle:
        print(f"Failed {mode} for {cfg.Data.inputDataset}: {cle}")


def main():
    args = parse_args()
    if not os.path.isfile(LUMI_MASK):
        raise SystemExit(
            f"Lumi mask not found: {LUMI_MASK}\n"
            "Run this script from HiAnalysis/HiOnia/test."
        )

    cfg = make_base_config()
    if args.units_per_job is not None:
        cfg.Data.unitsPerJob = args.units_per_job
    if args.max_job_runtime_min is not None:
        cfg.JobType.maxJobRuntimeMin = args.max_job_runtime_min
    if args.max_memory_mb is not None:
        cfg.JobType.maxMemoryMB = args.max_memory_mb

    selected = jobs(args.pd)
    print(
        f"Prepared {len(selected)} CRAB job(s)"
        + (" [DRY-RUN]" if args.dryrun else "")
        + f" | unitsPerJob={cfg.Data.unitsPerJob}"
        + f" maxJobRuntimeMin={cfg.JobType.maxJobRuntimeMin}"
        + f" maxMemoryMB={cfg.JobType.maxMemoryMB}"
    )
    print(f"  storageSite   = {cfg.Site.storageSite}")
    print(f"  outLFNDirBase = {cfg.Data.outLFNDirBase}")
    print(f"  workArea      = {cfg.General.workArea}")
    print(f"  lumiMask      = {cfg.Data.lumiMask}")
    print(f"  pset          = {cfg.JobType.psetName}")
    for i, (request_name, input_dataset) in enumerate(selected[:3]):
        print(f"  example[{i}]: {request_name} <- {input_dataset}")
    if len(selected) > 3:
        print(f"  ... and {len(selected) - 3} more")

    for request_name, input_dataset in selected:
        cfg.General.requestName = request_name
        cfg.Data.inputDataset = input_dataset
        cfg.Data.outputDatasetTag = request_name
        cfg.Data.outLFNDirBase = OUT_LFN
        print(
            f"{'Dry-running' if args.dryrun else 'Submitting'} CRAB job for: {input_dataset}"
            f" -> {cfg.Data.outLFNDirBase}"
        )
        submit(cfg, args.dryrun)


if __name__ == "__main__":
    main()
