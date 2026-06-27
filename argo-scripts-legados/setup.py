from setuptools import setup

APP = ["replace_audio.py"]
OPTIONS = {
    "argv_emulation": False,
    "plist": {
        "CFBundleName": "Argo AudioReplacer",
        "CFBundleDisplayName": "Argo AudioReplacer",
        "CFBundleIdentifier": "tv.argonautas.audioreplacer",
        "CFBundleVersion": "1.0.0",
        "CFBundleShortVersionString": "1.0",
        "NSHumanReadableCopyright": "© 2026 Argonautas",
        "NSHighResolutionCapable": True,
    },
    "packages": [],
}

setup(
    app=APP,
    name="Argo AudioReplacer",
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
