import FWCore.ParameterSet.Config as cms
import FWCore.ParameterSet.VarParsing as VarParsing
from Configuration.StandardSequences.Eras import eras

#----------------------------------------------------------------------------
# ONIA TREE for official 2023 coherent J/psi MiniAODSIM:
#   /GGToCoherentJPsiToMuMu_TuneCP5_5p36TeV_starlight-pythia8/
#    HINPbPbSpring23MiniAOD-132X_mcRun3_2023_realistic_HI_v9-v2/MINIAODSIM
#
# Reco_mu_* / Reco_QQ_* follow psianalyzer_PbPb2023_HIPhysicsRawPrime_cfg.py.
# isMC=True also writes Gen_*.
# Kept events: 2023 HLT OR, and at least one opposite-sign pair
# with 2 < mass < 6 GeV and pt < 22. Same-sign pairs in those events
# are stored (Reco_QQ_sign). Also required, same modules as the 2024 Onia cfg:
# phfCoincFilterPF2Th4, primaryVertexFilter, clusterCompatibilityFilter.
#----------------------------------------------------------------------------

HLTProcess     = "HLT"
isMC           = True
muonSelection  = "Trk"
applyEventSel  = True
OnlySoftMuons  = False
applyCuts      = False
SumETvariables = True
SofterSgMuAcceptance = False
doTrimuons     = False
doDimuonTrk    = False
atLeastOneCand = False
OneMatchedHLTMu = -1
keepExtraColl  = False
miniAOD        = True
UsePropToMuonSt = True
pdgId = 443
useMomFormat = "vector"
addEventPlane = False

MUONCUT = "(p > 2.5 && abs(eta) < 2.4) && isTrackerMuon"
DIMUONCUT = "mass > 2.0 && mass < 6.0 && pt < 22.0"

print( " " )
print( "[INFO] Settings used for ONIA TREE 2023 coherent MC: " )
print( "[INFO] isMC                 = " + ("True" if isMC else "False") )
print( "[INFO] applyEventSel        = " + ("True" if applyEventSel else "False") )
print( "[INFO] muonSelection        = " + muonSelection )
print( "[INFO] muon cut             = " + MUONCUT )
print( "[INFO] dimuon cut           = " + DIMUONCUT )
print( "[INFO] miniAOD              = " + ("True" if miniAOD else "False") )
print( " " )

process = cms.Process("HIOnia", eras.Run3_pp_on_PbPb_2023)

options = VarParsing.VarParsing('analysis')
options.inputFiles = [
  '/store/mc/HINPbPbSpring23MiniAOD/GGToCoherentJPsiToMuMu_TuneCP5_5p36TeV_starlight-pythia8/MINIAODSIM/132X_mcRun3_2023_realistic_HI_v9-v2/2820000/0c51b235-5063-46fe-9df6-520fe64cf11c.root'
]
options.outputFile = 'Oniatree_PsiMassRegion_PbPb2023_cohMC.root'
options.maxEvents = -1
options.parseArguments()

triggerList = {
    'DoubleMuonTrigger' : cms.vstring(
        "HLT_HIL2DoubleMu0_M1p5to6_Open_v",
        "HLT_HIL2DoubleMu0_M7to15_Open_v",
        "HLT_HIL3DoubleMu0_M2to4p5_Open_v",
        "HLT_HIL3DoubleMu0_M7to15_Open_v",
        "HLT_HIL3DoubleMu0_Quarkonia_Open_v",
    ),
    'SingleMuonTrigger' : cms.vstring(
        "HLT_HIL3SingleMu12_v",
        "HLT_HIUPC_SingleMuCosmic_NotMBHF2AND_v",
        "HLT_HIUPC_SingleMuCosmic_NotMBHF2OR_v",
        "HLT_HIUPC_SingleMuOpen_NotMBHF2AND_v",
        "HLT_HIUPC_SingleMuOpen_NotMBHF2OR_v",
        "HLT_HIMinimumBiasHF1ANDZDC1nOR_v",
        "HLT_HIMinimumBiasHF1AND_v",
        "HLT_HIUPC_ZeroBias_SinglePixelTrack_MaxPixelTrack_v",
        "HLT_HIUPC_ZeroBias_SinglePixelTrackLowPt_MaxPixelCluster400_v",
        "HLT_HIUPC_ZeroBias_MinPixelCluster400_MaxPixelCluster10000_v",
        "HLT_HIZeroBias_HighRate_v",
    ),
}

# 14_1_9 auto:phase1_2023_realistic_hi = 141X_mcRun3_2023_realistic_HI_v11.
# The sample itself was produced with 132X_mcRun3_2023_realistic_HI_v9.
globalTag = 'auto:phase1_2023_realistic_hi'

process.load('Configuration.StandardSequences.Reconstruction_cff')
process.load('Configuration.StandardSequences.Services_cff')
process.load('Configuration.Geometry.GeometryDB_cff')
process.load('Configuration.StandardSequences.MagneticField_38T_cff')

process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_cff')
from Configuration.AlCa.GlobalTag import GlobalTag
process.GlobalTag = GlobalTag(process.GlobalTag, globalTag, '')

process.load("RecoHI.HiCentralityAlgos.CentralityBin_cfi")
process.centralityBin.Centrality = cms.InputTag("hiCentrality")
process.centralityBin.centralityVariable = cms.string("HFtowers")
print('\n\033[31m~*~ USING 2023 PbPb MC CENTRALITY TABLE ~*~\033[0m\n')
process.GlobalTag.snapshotTime = cms.string("9999-12-31 23:59:59.000")
process.GlobalTag.toGet.extend([
    cms.PSet(record = cms.string("HeavyIonRcd"),
        tag = cms.string("CentralityTable_HFtowers200_HydjetDrum5F_Run3v1302x04_Official_MC"),
        connect = cms.string("frontier://FrontierProd/CMS_CONDITIONS"),
        label = cms.untracked.string("HFtowers")
        ),
    ])

from HiAnalysis.HiOnia.oniaTreeAnalyzer_cff import oniaTreeAnalyzer
oniaTreeAnalyzer(process,
                 muonTriggerList=triggerList, HLTProName=HLTProcess,
                 muonSelection=muonSelection, L1Stage=2, isMC=isMC, pdgID=pdgId, outputFileName=options.outputFile, doTrimu=doTrimuons, OnlySingleMuons=False
)

process.onia2MuMuPatGlbGlb.dimuonSelection      = cms.string(DIMUONCUT)
process.onia2MuMuPatGlbGlb.lowerPuritySelection = cms.string(MUONCUT)
process.onia2MuMuPatGlbGlb.LateDimuonSel        = cms.string("")
process.onia2MuMuPatGlbGlb.onlySoftMuons        = cms.bool(OnlySoftMuons)

process.hionia.minimumFlag      = cms.bool(keepExtraColl)
process.hionia.useGeTracks      = cms.untracked.bool(keepExtraColl)
process.hionia.fillRecoTracks   = cms.bool(keepExtraColl)
process.hionia.fillSingleMuons  = cms.bool(True)
process.hionia.CentralitySrc    = cms.InputTag("hiCentrality")
process.hionia.CentralityBinSrc = cms.InputTag("centralityBin","HFtowers")
process.hionia.SofterSgMuAcceptance = cms.bool(SofterSgMuAcceptance)
process.hionia.SumETvariables   = cms.bool(SumETvariables)
process.hionia.applyCuts        = cms.bool(applyCuts)
process.hionia.AtLeastOneCand   = cms.bool(atLeastOneCand)
process.hionia.OneMatchedHLTMu  = cms.int32(OneMatchedHLTMu)
process.hionia.checkTrigNames   = cms.bool(False)
process.hionia.mom4format       = cms.string(useMomFormat)
process.hionia.storeSameSign    = cms.bool(True)
process.hionia.useEvtPlane      = cms.untracked.bool(addEventPlane)

process.oniaTreeAna.replace(process.hionia, process.centralityBin * process.hionia)

if applyEventSel:
  process.load('HeavyIonsAnalysis.EventAnalysis.collisionEventSelection_cff')
  process.load('HeavyIonsAnalysis.EventAnalysis.hffilterPF_cfi')

  import HLTrigger.HLTfilters.hltHighLevel_cfi
  process.hltHI = HLTrigger.HLTfilters.hltHighLevel_cfi.hltHighLevel.clone()
  process.hltHI.throw = False
  process.hltHI.andOr = True
  process.hltHI.HLTPaths = [
    'HLT_HIL2DoubleMu0_M1p5to6_Open_v*',
    'HLT_HIL2DoubleMu0_M7to15_Open_v*',
    'HLT_HIL3DoubleMu0_M2to4p5_Open_v*',
    'HLT_HIL3DoubleMu0_M7to15_Open_v*',
    'HLT_HIL3DoubleMu0_Quarkonia_Open_v*',
    'HLT_HIL3SingleMu12_v*',
    'HLT_HIUPC_SingleMuCosmic_NotMBHF2AND_v*',
    'HLT_HIUPC_SingleMuCosmic_NotMBHF2OR_v*',
    'HLT_HIUPC_SingleMuOpen_NotMBHF2AND_v*',
    'HLT_HIUPC_SingleMuOpen_NotMBHF2OR_v*',
    'HLT_HIMinimumBiasHF1ANDZDC1nOR_v*',
    'HLT_HIMinimumBiasHF1AND_v*',
    'HLT_HIUPC_ZeroBias_SinglePixelTrack_MaxPixelTrack_v*',
    'HLT_HIUPC_ZeroBias_SinglePixelTrackLowPt_MaxPixelCluster400_v*',
    'HLT_HIUPC_ZeroBias_MinPixelCluster400_MaxPixelCluster10000_v*',
    'HLT_HIZeroBias_HighRate_v*',
  ]

  process.muonSelector = cms.EDFilter("PATMuonRefSelector",
                                       src = cms.InputTag("slimmedMuons"),
                                       cut = cms.string(MUONCUT),
                                       filter = cms.bool(True)
  )
  process.atLeastTwoMuons = cms.EDFilter("MuonRefPatCount",
                                          src = cms.InputTag("slimmedMuons"),
                                          cut = cms.string(MUONCUT),
                                          minNumber = cms.uint32(2)
  )
  process.dimuonSelection = cms.EDProducer("CandViewShallowCloneCombiner",
                                           checkCharge = cms.bool(False),
                                           cut = cms.string(DIMUONCUT),
                                           decay = cms.string("muonSelector@+ muonSelector@-")
  )
  process.atLeastOneDimuon = cms.EDFilter("CandViewCountFilter",
                                           src = cms.InputTag("dimuonSelection"),
                                           minNumber = cms.uint32(1)
  )
  process.oniaTreeAna.replace(
      process.patMuonSequence,
      process.hltHI * process.muonSelector * process.atLeastTwoMuons * process.dimuonSelection * process.atLeastOneDimuon * process.phfCoincFilterPF2Th4 * process.primaryVertexFilter * process.clusterCompatibilityFilter * process.patMuonSequence
  )

process.oniaTreeAna = cms.Path(process.oniaTreeAna)
if miniAOD:
  from HiSkim.HiOnia2MuMu.onia2MuMuPAT_cff import changeToMiniAOD
  changeToMiniAOD(process)
  process.unpackedMuons.addPropToMuonSt = cms.bool(UsePropToMuonSt)

process.source = cms.Source("PoolSource",
                            fileNames = cms.untracked.vstring(options.inputFiles),
)
process.TFileService = cms.Service("TFileService",
                                   fileName = cms.string(options.outputFile)
)
process.maxEvents = cms.untracked.PSet(input = cms.untracked.int32(options.maxEvents))
process.options   = cms.untracked.PSet(wantSummary = cms.untracked.bool(True))
process.schedule  = cms.Schedule(process.oniaTreeAna)
