"""Explicit online setup step. Runtime uses local files only."""
import os
from .config import MODEL_DIR, MODEL_ID, MODEL_REVISION, ROOT


def main():
    os.environ.pop("HF_HUB_OFFLINE", None)
    os.environ.pop("TRANSFORMERS_OFFLINE", None)
    os.environ["HF_HOME"] = str(ROOT / ".hf-cache")
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    from huggingface_hub import snapshot_download
    print(f"Downloading {MODEL_ID} at {MODEL_REVISION} to {MODEL_DIR}", flush=True)
    snapshot_download(MODEL_ID, revision=MODEL_REVISION, local_dir=MODEL_DIR,
                      allow_patterns=["*.json", "*.safetensors", "*.jinja", "tokenizer*", "vocab*", "merges*", "LICENSE*"])
    (MODEL_DIR / "PINNED_REVISION").write_text(MODEL_REVISION, encoding="utf-8")
    print("Model download complete.", flush=True)


if __name__ == "__main__":
    main()
