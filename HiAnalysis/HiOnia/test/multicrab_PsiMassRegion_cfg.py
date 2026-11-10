#!/usr/bin/env python3
"""
Psi mass region multicrab submitter.

Run from CMSSW area with CRAB environment loaded, e.g.:
  cd $CMSSW_BASE/src/HiAnalysis/HiOnia/test
  cmsenv
  source /cvmfs/cms.cern.ch/common/crab-setup.sh
  python3 multicrab_PsiMassRegion_cfg.py --dryrun --pd 0 --era A
"""
import argparse
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
        "  source /cvmfs/cms.cern.ch/common/crab-setup.sh\n"
        "Then rerun this script from HiOnia/test."
    )

from http.client import HTTPException


def parse_args():
    parser = argparse.ArgumentParser(
        description="Submit PsiMassRegion Onia CRAB jobs for HIPhysicsRawPrime PDs."
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
        help="Submit only HIPhysicsRawPrimeN (default: all PDs).",
    )
    parser.add_argument(
        "--era",
        choices=["A", "B", "all"],
        default="all",
        help="HIRun2024 era to submit (default: all).",
    )
    parser.add_argument(
        "--era-b-version",
        type=int,
        choices=[1, 2],
        default=None,
        help="For era B only: submit a single PromptReco version (default: both v1 and v2).",
    )
    parser.add_argument(
        "--units-per-job",
        type=int,
        default=None,
        metavar="N",
        help="EventAwareLumiBased unitsPerJob (default: 4000000).",
    )
    parser.add_argument(
        "--max-job-runtime-min",
        type=int,
        default=None,
        metavar="MIN",
        help="Job wall time in minutes (default: 2500, CRAB max 2750).",
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
    cfg.General.workArea = "crab_projects_PsiMassRegion"
    cfg.General.transferOutputs = True
    cfg.General.transferLogs = False

    cfg.section_("JobType")
    cfg.JobType.pluginName = "Analysis"
    cfg.JobType.psetName = "psianalyzer_PbPb2024_HIPhysicsRawPrime_cfg.py"
    cfg.JobType.maxMemoryMB = 2400
    cfg.JobType.allowUndistributedCMSSW = True
    cfg.JobType.maxJobRuntimeMin = 2500  # max = 2750; avoid exit 50664

    cfg.section_("Data")
    cfg.Data.inputDBS = "global"
    cfg.Data.splitting = "EventAwareLumiBased"
    cfg.Data.unitsPerJob = 4000000
    cfg.Data.allowNonValidInputDataset = True
    cfg.Data.publication = False
    cfg.Data.runRange = "387853-388784"
    cfg.Data.lumiMask = (
        "https://cms-service-dqmdc.web.cern.ch/CAF/certification/Collisions24HI/"
        "Cert_Collisions2024_HI_387853_388784_Golden.json"
    )
    # Stage-out to Vanderbilt; EraA/B paths set in main() per request.
    #   EraA: /store/user/dizhang/PbPb2024_EraA/<PD>/<requestName>/...
    #   EraB: /store/user/dizhang/<PD>/<requestName>/...  (existing layout)
    cfg.Data.outLFNDirBase = "/store/user/dizhang/"

    cfg.section_("Site")
    cfg.Site.storageSite = "T2_US_Vanderbilt"
    # ignoreLocality not set; whitelist where jobs may run. Output site is storageSite.
    cfg.Site.whitelist = ["T2_CH_CERN", "T2_US_*", "T1_US_*"]
    return cfg


def out_lfn_dir_base(request_name):
    """LFN base on Vanderbilt for this CRAB request."""
    if "EraA" in request_name:
        return "/store/user/dizhang/PbPb2024_EraA/"
    return "/store/user/dizhang/"


def submit(cfg, dryrun):
    mode = "dry-run" if dryrun else "submit"
    try:
        crabCommand("submit", config=cfg, dryrun=dryrun)
    except HTTPException as hte:
        print(f"Failed {mode} for {cfg.Data.inputDataset}: {hte.headers}")
    except ClientException as cle:
        print(f"Failed {mode} for {cfg.Data.inputDataset}: {cle}")


def era_a_jobs(pd=None):
    jobs = []
    pd_list = [pd] if pd is not None else list(range(60))

    for i in pd_list:
        if i < 15:
            jobs.append(
                (
                    f"Psi_EraA_RawPrime{i}",
                    f"/HIPhysicsRawPrime{i}/HIRun2024A-PromptReco-v1/MINIAOD",
                )
            )
        elif i == 36:
            jobs.append(
                (
                    "Psi_EraA_RawPrime36",
                    "/HIPhysicsRawPrime36/HIRun2024A-OfflinePromptReco-v2/MINIAOD",
                )
            )
        else:
            jobs.append(
                (
                    f"Psi_EraA_RawPrime{i}",
                    f"/HIPhysicsRawPrime{i}/HIRun2024A-OfflinePromptReco-v1/MINIAOD",
                )
            )
    return jobs


def era_b_jobs(pd=None, version=None):
    jobs = []
    pd_list = [pd] if pd is not None else list(range(60))
    version_list = [version] if version is not None else [1, 2]

    for i in pd_list:
        for k in version_list:
            jobs.append(
                (
                    f"Psi_EraB_RawPrime{i}_v{k}",
                    f"/HIPhysicsRawPrime{i}/HIRun2024B-PromptReco-v{k}/MINIAOD",
                )
            )
    return jobs


def main():
    args = parse_args()
    cfg = make_base_config()

    if args.units_per_job is not None:
        cfg.Data.unitsPerJob = args.units_per_job
    if args.max_job_runtime_min is not None:
        cfg.JobType.maxJobRuntimeMin = args.max_job_runtime_min
    if args.max_memory_mb is not None:
        cfg.JobType.maxMemoryMB = args.max_memory_mb

    jobs = []
    if args.era in ("A", "all"):
        jobs.extend(era_a_jobs(args.pd))
    if args.era in ("B", "all"):
        jobs.extend(era_b_jobs(args.pd, args.era_b_version))

    if not jobs:
        raise SystemExit("No jobs selected.")

    if args.era == "A":
        cfg.General.workArea = "crab_projects_PsiMassRegion_EraA"

    print(
        f"Prepared {len(jobs)} CRAB job(s)"
        + (" [DRY-RUN]" if args.dryrun else "")
        + f" | unitsPerJob={cfg.Data.unitsPerJob}"
        + f" maxJobRuntimeMin={cfg.JobType.maxJobRuntimeMin}"
        + f" maxMemoryMB={cfg.JobType.maxMemoryMB}"
    )
    print(f"  storageSite   = {cfg.Site.storageSite}")
    print(f"  workArea      = {cfg.General.workArea}")
    for i, (request_name, input_dataset) in enumerate(jobs[:3]):
        print(
            f"  example[{i}]: {request_name} <- {input_dataset}"
            f"  out={out_lfn_dir_base(request_name)}"
        )
    if len(jobs) > 3:
        print(f"  ... and {len(jobs) - 3} more")

    for request_name, input_dataset in jobs:
        cfg.General.requestName = request_name
        cfg.Data.inputDataset = input_dataset
        cfg.Data.outputDatasetTag = request_name
        cfg.Data.outLFNDirBase = out_lfn_dir_base(request_name)
        print(
            f"{'Dry-running' if args.dryrun else 'Submitting'} CRAB job for: {input_dataset}"
            f" -> {cfg.Data.outLFNDirBase}"
        )
        submit(cfg, args.dryrun)


if __name__ == "__main__":
    main()
