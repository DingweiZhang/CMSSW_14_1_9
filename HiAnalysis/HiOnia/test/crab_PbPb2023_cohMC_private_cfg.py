#!/usr/bin/env python3
"""
CRAB for the private 2023 coherent J/psi Onia trees.

Input is the published USER MiniAOD on prod/phys03. EOS:
  .../mc_coherent_Jpsi_tree/S4_MINIAOD/CohJpsi_MC_Dataset/
  CohJpsi_MC_Production_RECO_MINIAOD_01 .. _22
Each batch uses the same dataset hash c112afcb315f31b60faa9c789c856b28.
MINIAOD_23 is in DBS but is not in this S4 directory, so it is not submitted.

Output on T2_CH_CERN, under
  /store/group/phys_heavyions/dizhang/run3_2023_PbPb5p36TeV_cohJpsi/mc_coherent_Jpsi_tree/S5_MakeTree/
CRAB adds CohJpsi_MC_Dataset/<request name>/<date>/0000/.

Does not use Onia_2023_cohJpsi_official or crab_projects_PbPb2023_cohMC.

  python3 crab_PbPb2023_cohMC_private_cfg.py --dryrun
  python3 crab_PbPb2023_cohMC_private_cfg.py --only 01
  python3 crab_PbPb2023_cohMC_private_cfg.py
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
        "  cmsenv && source /cvmfs/cms.cern.ch/common/crab-setup.sh prod"
    )

from http.client import HTTPException

HASH = "c112afcb315f31b60faa9c789c856b28"
BATCHES = [f"{i:02d}" for i in range(1, 23)]
OUT_LFN = (
    "/store/group/phys_heavyions/dizhang/"
    "run3_2023_PbPb5p36TeV_cohJpsi/mc_coherent_Jpsi_tree/S5_MakeTree/"
)
WORK_AREA = "crab_projects_PbPb2023_cohMC_private"


def dataset_name(batch):
    return (
        "/CohJpsi_MC_Dataset/"
        f"phys_heavyions-CohJpsi_MC_Production_RECO_MINIAOD_{batch}-{HASH}/USER"
    )


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dryrun", action="store_true")
    parser.add_argument(
        "--only",
        metavar="NN",
        help="submit one batch, for example 01",
    )
    return parser.parse_args()


def make_config(batch):
    cfg = config()
    cfg.section_("General")
    cfg.General.workArea = WORK_AREA
    cfg.General.requestName = f"Onia_2023_cohJpsi_private_{batch}"
    cfg.General.transferOutputs = True
    cfg.General.transferLogs = False

    cfg.section_("JobType")
    cfg.JobType.pluginName = "Analysis"
    cfg.JobType.psetName = "psianalyzer_PbPb2023_cohMC_private_cfg.py"
    cfg.JobType.maxMemoryMB = 2400
    cfg.JobType.allowUndistributedCMSSW = True
    cfg.JobType.maxJobRuntimeMin = 2750

    cfg.section_("Data")
    cfg.Data.inputDBS = "phys03"
    cfg.Data.inputDataset = dataset_name(batch)
    cfg.Data.splitting = "FileBased"
    cfg.Data.unitsPerJob = 5
    cfg.Data.publication = False
    cfg.Data.allowNonValidInputDataset = True
    cfg.Data.outputDatasetTag = cfg.General.requestName
    cfg.Data.outLFNDirBase = OUT_LFN

    cfg.section_("Site")
    cfg.Site.storageSite = "T2_CH_CERN"
    # Private MiniAOD is stored at T2_CH_CERN.
    cfg.Site.whitelist = ["T2_CH_CERN"]
    return cfg


def main():
    args = parse_args()
    batches = BATCHES
    if args.only:
        batch = f"{int(args.only):02d}"
        if batch not in BATCHES:
            sys.exit(f"ERROR: batch {batch} is outside 01-22")
        batches = [batch]
    failed = []
    for batch in batches:
        cfg = make_config(batch)
        print(f"request     = {cfg.General.requestName}")
        print(f"dataset     = {cfg.Data.inputDataset}")
        print(f"outLFN      = {cfg.Data.outLFNDirBase}")
        print(f"storageSite = {cfg.Site.storageSite}")
        print(f"workArea    = {cfg.General.workArea}")
        try:
            crabCommand("submit", config=cfg, dryrun=args.dryrun)
        except HTTPException as hte:
            print(f"Failed {batch}: {hte.headers}")
            failed.append(batch)
        except ClientException as cle:
            print(f"Failed {batch}: {cle}")
            failed.append(batch)
    if failed:
        sys.exit(f"ERROR: failed batches: {', '.join(failed)}")


if __name__ == "__main__":
    main()
