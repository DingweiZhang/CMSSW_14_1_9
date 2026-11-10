import FWCore.ParameterSet.Config as cms
import FWCore.ParameterSet.VarParsing as VarParsing
from Configuration.StandardSequences.Eras import eras

#----------------------------------------------------------------------------
# ONIA TREE for 2023 PbPb MINIAOD.
# Physics cuts follow PbPbSkimAndTree2023_DiMuContBoth_ZDC_MiniAOD_cfg.py
# (CMSSW_13_2_11 VertexComposite). Output is hionia/myTree:
#   Reco_mu_* once per muon, Reco_QQ_*_idx pointing into that list.
#
# 2023 event content that is kept:
#   HLT OR of the 2023 muon / MB / zero-bias menu
#   at least one opposite-sign pair with 2 < mass < 6 GeV and pt < 22
# Same-sign pairs in those events are stored in the same tree (Reco_QQ_sign).
# Also required, same modules as the 2024 Onia cfg:
#   phfCoincFilterPF2Th4, primaryVertexFilter, clusterCompatibilityFilter.
#----------------------------------------------------------------------------

HLTProcess     = "HLT"
isMC           = False
muonSelection  = "Trk" # 2023 fitter: isTrackerMuon
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

# 2023 generalMuMuMassMin0Candidates
MUONCUT = "(p > 2.5 && abs(eta) < 2.4) && isTrackerMuon"
DIMUONCUT = "mass > 2.0 && mass < 6.0 && pt < 22.0"

print( " " )
print( "[INFO] Settings used for ONIA TREE 2023: " )
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
  '/store/hidata/HIRun2023A/HIPhysicsRawPrime1/MINIAOD/PromptReco-v2/000/374/668/00000/37d9e218-a53e-4501-a7d1-db165f1620a3.root'
]
options.outputFile = 'Oniatree_PsiMassRegion_PbPb2023_HIPhysicsRawPrime.root'
options.secondaryOutputFile = "Jpsi_Dataset.root"
options.maxEvents = -1
options.parseArguments()

triggerList = {
    'DoubleMuonTrigger' : cms.vstring(
        "HLT_HIL2DoubleMu0_M1p5to6_Open_v",          #0
        "HLT_HIL2DoubleMu0_M7to15_Open_v",           #1
        "HLT_HIL3DoubleMu0_M2to4p5_Open_v",          #2
        "HLT_HIL3DoubleMu0_M7to15_Open_v",           #3
        "HLT_HIL3DoubleMu0_Quarkonia_Open_v",        #4
    ),
    'SingleMuonTrigger' : cms.vstring(
        "HLT_HIL3SingleMu12_v",                      #5
        "HLT_HIUPC_SingleMuCosmic_NotMBHF2AND_v",    #6
        "HLT_HIUPC_SingleMuCosmic_NotMBHF2OR_v",     #7
        "HLT_HIUPC_SingleMuOpen_NotMBHF2AND_v",      #8
        "HLT_HIUPC_SingleMuOpen_NotMBHF2OR_v",       #9
        "HLT_HIMinimumBiasHF1ANDZDC1nOR_v",          #10
        "HLT_HIMinimumBiasHF1AND_v",                 #11
        "HLT_HIUPC_ZeroBias_SinglePixelTrack_MaxPixelTrack_v",                 #12
        "HLT_HIUPC_ZeroBias_SinglePixelTrackLowPt_MaxPixelCluster400_v",       #13
        "HLT_HIUPC_ZeroBias_MinPixelCluster400_MaxPixelCluster10000_v",        #14
        "HLT_HIZeroBias_HighRate_v",                 #15
    ),
}

# 14_1_9 data GT. Centrality table is the 2023 offline table
# (13_2_11 cfg used GT 132X_dataRun3_Prompt_v7 and the same HeavyIonRcd tag).
if isMC:
  globalTag = 'auto:phase1_2023_realistic_hi'
else:
  globalTag = '141X_dataRun3_Prompt_v3'

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
print('\n\033[31m~*~ USING NOMINAL CENTRALITY TABLE FOR 2023 PbPb DATA ~*~\033[0m\n')
process.GlobalTag.snapshotTime = cms.string("9999-12-31 23:59:59.000")
process.GlobalTag.toGet.extend([
    cms.PSet(record = cms.string("HeavyIonRcd"),
        tag = cms.string("CentralityTable_HFtowers200_DataPbPb_periHYDJETshape_Run3v1302x04_Nominal_Offline"),
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
  # Opposite-sign only, same as 2023 goodDimuon (goodMuon@+ goodMuon@-).
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
