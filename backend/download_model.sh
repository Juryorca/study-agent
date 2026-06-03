#!/usr/bin/env bash
# Download the local embedding model (all-MiniLM-L6-v2, ~88MB ONNX)
# This model is used for document vector indexing.
# Runs once; skip if backend/models/embedding/ already exists.

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MODEL_DIR="$SCRIPT_DIR/models/embedding"

if [ -d "$MODEL_DIR" ] && [ -f "$MODEL_DIR/model.onnx" ]; then
    echo "Embedding model already exists at $MODEL_DIR"
    exit 0
fi

echo "Downloading embedding model (all-MiniLM-L6-v2 ONNX)..."
mkdir -p "$MODEL_DIR"

# Use huggingface hub or direct URL for the ONNX export
pip install -q huggingface_hub 2>/dev/null || true

python3 -c "
from pathlib import Path
import os

dest = Path('$MODEL_DIR')
print(f'Downloading to {dest}...')

# Download from sentence-transformers via huggingface
try:
    from huggingface_hub import snapshot_download
    snapshot_download(
        'sentence-transformers/all-MiniLM-L6-v2',
        local_dir=str(dest),
        local_dir_use_symlinks=False,
        ignore_patterns=['*.safetensors', '*.bin', '*.msgpack', '*.h5', 'pytorch_model.bin', 'tf_model.h5'],
    )
except ImportError:
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
    tokenizer.save_pretrained(str(dest))
    # Also need the ONNX model - download separately
    import urllib.request
    url = 'https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main/onnx/model.onnx'
    print(f'Downloading ONNX model from {url}...')
    urllib.request.urlretrieve(url, str(dest / 'model.onnx'))
    print('Done.')
" 2>/dev/null || {
    echo ""
    echo "ERROR: Failed to download."
    echo "Please manually place the all-MiniLM-L6-v2 ONNX model at:"
    echo "  $MODEL_DIR/"
    echo ""
    echo "Required files: config.json, model.onnx, tokenizer.json, tokenizer_config.json, special_tokens_map.json, vocab.txt"
    exit 1
}

echo "Embedding model downloaded to $MODEL_DIR"
