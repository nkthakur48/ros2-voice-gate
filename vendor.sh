#!/bin/sh
# Download the Needle runtime + weights once, so the demo needs no network for intent. ~37 MB.
set -e; mkdir -p vendor; cd vendor
B=https://huggingface.co/Cactus-Compute/cactus/resolve/v4.0.0/releases/4.0.0/wasm
curl -sLo cactus.js   $B/cactus.js
curl -sLo cactus.wasm $B/cactus.wasm
curl -sLo needle3.cact https://huggingface.co/Cactus-Compute/needle3/resolve/main/needle3.cact
curl -sLo roslib.min.js https://cdn.jsdelivr.net/npm/roslib@1/build/roslib.min.js
ls -la
