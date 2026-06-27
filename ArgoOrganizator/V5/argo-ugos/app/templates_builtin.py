BASE_STRUCTURE = [
    "_INGEST",
    "_INGEST/CARD_CLONES",
    "_INGEST/ORIGINALS",
    "_INGEST/AUDIO",
    "_WORK",
    "_WORK/PROXIES",
    "_WORK/SYNC",
    "_WORK/TIMELINES",
    "_EXPORT",
    "_EXPORT/MASTERS",
    "_EXPORT/DELIVERIES",
    "_ARCHIVE",
    "_ARCHIVE/FINAL",
    "_ARCHIVE/METADATA",
    "_ARCHIVE/METADATA/manifests",
    "_ARCHIVE/SESSIONS"
]

BUILTIN_TEMPLATES = {
    "Base_Editorial": [
        "_INGEST/ORIGINALS",
        "_INGEST/AUDIO",
        "_WORK/PROXIES",
        "_WORK/SYNC",
        "_WORK/TIMELINES",
        "_EXPORT/MASTERS",
        "_EXPORT/DELIVERIES",
        "_ARCHIVE/METADATA"
    ],
    "Documentario_Completo": [
        "00_ADMIN",
        "01_BRUTOS/CAMERA_A",
        "01_BRUTOS/CAMERA_B",
        "02_AUDIO",
        "03_PROXIES",
        "04_SYNC",
        "05_TIMELINES",
        "06_EXPORTS",
        "07_MASTER",
        "08_METADATA",
        "09_ARCHIVE"
    ],
    "Cinemateca_Deposito_Legal_Cinema": [
        "{slug}_cinemateca",
        "{slug}_cinemateca/{slug}_preservacao",
        "{slug}_cinemateca/{slug}_exibicao",
        "{slug}_cinemateca/recursos_de_acessibilidade/libras",
        "{slug}_cinemateca/recursos_de_acessibilidade/audiodescricao",
        "{slug}_cinemateca/recursos_de_acessibilidade/legendas_descritivas",
        "{slug}_cinemateca/documentacao",
        "{slug}_cinemateca/laudo_tecnico"
    ],
    "Netflix_IMF_Delivery": [
        "{slug}_imf_delivery/ASSETMAP",
        "{slug}_imf_delivery/PKL",
        "{slug}_imf_delivery/CPL",
        "{slug}_imf_delivery/OPL_optional",
        "{slug}_imf_delivery/MXF"
    ],
    "DCP_SMPTE_DCI_Package": [
        "{slug}_dcp_smpte/CPL",
        "{slug}_dcp_smpte/PKL",
        "{slug}_dcp_smpte/ASSETMAP",
        "{slug}_dcp_smpte/VOLINDEX",
        "{slug}_dcp_smpte/MXF/picture",
        "{slug}_dcp_smpte/MXF/audio",
        "{slug}_dcp_smpte/MXF/subtitles"
    ]
}
