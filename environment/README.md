# Environment snapshot

The native simulations ran on Ubuntu 22.04 with an NVIDIA L20 GPU, 16 vCPUs and
128 GiB memory. Python, simulator, local VLA, and primitive services require the
original GPU setup and separately licensed assets. See the pinned upstream commits
in `../UPSTREAM.json` and the per-experiment `protocol.json` files.

`openpi-installed-packages.txt` records distribution names and versions from the
local VLA environment. It is an inventory, not a claim that a single pip command
rebuilds Isaac Sim, RoboDojo, GPU drivers, weights, and asset locations.
No private environment variables or agent credential configuration are exported.
