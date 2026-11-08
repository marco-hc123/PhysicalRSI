"""Explicitly enabled simulator-only import hook; no original source edits."""
import os
if os.environ.get('PHYSICALRSI_SIDECAR_ROOT'):
    from simulator_sidecar import install_import_hook
    install_import_hook()
