#!/usr/bin/env python3
"""
CRAB for the embedded incoherent J/psi Onia tree.

Input is the HiMix MiniAOD USER dataset on phys03 (task 261103_134059).
EOS:
  /afs/cern.ch/user/d/dizhang/eosHin/dizhang/run3_2023_PbPb5p36TeV_cohJpsi/mc_incoh_jpsi_embedded/S4_MINIAOD

Output on T2_CH_CERN, under
  /store/group/phys_heavyions/dizhang/run3_2023_PbPb5p36TeV_cohJpsi/mc_incoh_jpsi_embedded/S5_MakeTree/
CRAB adds <primary dataset>/<request name>/<date>/0000/.

Submit only after MiniAOD publication is 1000/1000. CRAB freezes the
input file list at submit time.

  python3 crab_PbPb2023_incohMC_cfg.py --dryrun
  python3 crab_PbPb2023_incohMC_cfg.py
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

DATASET = (
    "/IncoherentJPsiToMuMu_Embedded_TuneCP5_5p36TeV_starlight-pythia8/"
    "phys_heavyions-HiMix_MINIAOD_132X_mcRun3_2023_realistic_HI_v9-"
    "9101bd997db6d23b4580bccf82c57ff0/USER"
)
OUT_LFN = (
    "/store/group/phys_heavyions/dizhang/"
    "run3_2023_PbPb5p36TeV_cohJpsi/mc_incoh_jpsi_embedded/S5_MakeTree/"
)
REQUEST = "Onia_2023_incohJpsi_embedded"


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dryrun", action="store_true")
    return parser.parse_args()


def make_config():
    cfg = config()
    cfg.section_("General")
    cfg.General.workArea = "crab_projects_PbPb2023_incohMC"
    cfg.General.requestName = REQUEST
    cfg.General.transferOutputs = True
    cfg.General.transferLogs = False

    cfg.section_("JobType")
    cfg.JobType.pluginName = "Analysis"
    cfg.JobType.psetName = "psianalyzer_PbPb2023_incohMC_cfg.py"
    cfg.JobType.maxMemoryMB = 3000
    cfg.JobType.allowUndistributedCMSSW = True
    cfg.JobType.maxJobRuntimeMin = 2750

    cfg.section_("Data")
    cfg.Data.inputDBS = "phys03"
    cfg.Data.inputDataset = DATASET
    cfg.Data.splitting = "FileBased"
    cfg.Data.unitsPerJob = 3
    cfg.Data.publication = False
    cfg.Data.allowNonValidInputDataset = True
    cfg.Data.outputDatasetTag = REQUEST
    cfg.Data.outLFNDirBase = OUT_LFN

    cfg.section_("Site")
    cfg.Site.storageSite = "T2_CH_CERN"
    # Embedded MiniAOD is stored at T2_CH_CERN.
    cfg.Site.whitelist = ["T2_CH_CERN"]
    return cfg


def main():
    args = parse_args()
    cfg = make_config()
    print(f"request     = {cfg.General.requestName}")
    print(f"dataset     = {cfg.Data.inputDataset}")
    print(f"outLFN      = {cfg.Data.outLFNDirBase}")
    print(f"storageSite = {cfg.Site.storageSite}")
    print(f"workArea    = {cfg.General.workArea}")
    try:
        crabCommand("submit", config=cfg, dryrun=args.dryrun)
    except HTTPException as hte:
        print(f"Failed: {hte.headers}")
        sys.exit(1)
    except ClientException as cle:
        print(f"Failed: {cle}")
        sys.exit(1)


if __name__ == "__main__":
    main()
