const TEMPLATES = {
  "Cinemateca_Deposito_Legal_Cinema": [
    "{slug}_cinemateca",
    "{slug}_cinemateca/{slug}_preservacao",
    "{slug}_cinemateca/{slug}_exibicao",
    "{slug}_cinemateca/recursos_de_acessibilidade",
    "{slug}_cinemateca/recursos_de_acessibilidade/libras",
    "{slug}_cinemateca/recursos_de_acessibilidade/audiodescricao",
    "{slug}_cinemateca/recursos_de_acessibilidade/legendas_descritivas",
    "{slug}_cinemateca/documentacao",
    "{slug}_cinemateca/laudo_tecnico",
    "{slug}_cinemateca/qc"
  ],

  "Cinemateca_Deposito_Legal_TV_Outras_Telas": [
    "{slug}_cinemateca",
    "{slug}_cinemateca/{slug}_preservacao_mkv_ffv1",
    "{slug}_cinemateca/{slug}_copia_acesso",
    "{slug}_cinemateca/recursos_de_acessibilidade",
    "{slug}_cinemateca/recursos_de_acessibilidade/libras",
    "{slug}_cinemateca/recursos_de_acessibilidade/audiodescricao",
    "{slug}_cinemateca/recursos_de_acessibilidade/legendas_descritivas",
    "{slug}_cinemateca/documentacao",
    "{slug}_cinemateca/laudo_tecnico",
    "{slug}_cinemateca/qc"
  ],

  "Netflix_Picture_Archival_NAM_Longplay": [
    "{slug}_nam_16b_rwg_log3g10_{date}_3840x2160",
    "{slug}_nam_16b_rwg_log3g10_{date}_3840x2160/checksum.txt.placeholder"
  ],

  "Netflix_Picture_Archival_DCDM_Reels": [
    "{slug}_dcdm_16b_sdr_xyz_g26_{date}_239_4096x1716",
    "{slug}_dcdm_16b_sdr_xyz_g26_{date}_239_4096x1716/r01/checksum.txt.placeholder",
    "{slug}_dcdm_16b_sdr_xyz_g26_{date}_239_4096x1716/r02/checksum.txt.placeholder",
    "{slug}_dcdm_16b_sdr_xyz_g26_{date}_239_4096x1716/r03/checksum.txt.placeholder",
    "{slug}_dcdm_16b_sdr_xyz_g26_{date}_239_4096x1716/r04/checksum.txt.placeholder"
  ],

  "Netflix_IMF_Delivery": [
    "{slug}_imf_delivery",
    "{slug}_imf_delivery/ASSETMAP",
    "{slug}_imf_delivery/PKL",
    "{slug}_imf_delivery/CPL",
    "{slug}_imf_delivery/OPL_optional",
    "{slug}_imf_delivery/MXF",
    "{slug}_imf_delivery/QC/reports"
  ],

  "DCP_SMPTE_DCI_Package": [
    "{slug}_dcp_smpte",
    "{slug}_dcp_smpte/CPL",
    "{slug}_dcp_smpte/PKL",
    "{slug}_dcp_smpte/ASSETMAP",
    "{slug}_dcp_smpte/VOLINDEX",
    "{slug}_dcp_smpte/MXF/picture",
    "{slug}_dcp_smpte/MXF/audio",
    "{slug}_dcp_smpte/MXF/subtitles",
    "{slug}_dcp_smpte/QC"
  ]
};

module.exports = { TEMPLATES };
