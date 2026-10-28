import json
import os
import threading
import time
from .config import MODEL_DIR, MODEL_REVISION, ROOT

# Runtime never downloads anything; setup is the only network-enabled path.
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"


class LocalModel:
    def __init__(self, bits=4):
        if bits not in (4, 8):
            raise ValueError("Supported quantization: 4 or 8 bits")
        self.bits = bits
        self.lock = threading.RLock()
        self.model = self.tokenizer = None
        self.last_metrics = {}

    def load(self):
        if self.model is not None:
            return
        import torch
        from transformers import AutoTokenizer, BitsAndBytesConfig, Qwen3_5ForCausalLM
        if not torch.cuda.is_available():
            raise RuntimeError("A CUDA GPU is required. Check your NVIDIA driver and rerun setup.cmd.")
        if not (MODEL_DIR / "config.json").exists():
            raise RuntimeError("Model files are missing. Run setup.cmd with internet access first.")
        marker = MODEL_DIR / "PINNED_REVISION"
        if not marker.exists() or marker.read_text(encoding="utf-8").strip() != MODEL_REVISION:
            raise RuntimeError("The pinned model download is incomplete or outdated. Rerun setup.cmd.")
        start = time.perf_counter()
        tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, local_files_only=True)
        quantization = (BitsAndBytesConfig(load_in_8bit=True) if self.bits == 8 else BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True))
        model = Qwen3_5ForCausalLM.from_pretrained(
            MODEL_DIR, local_files_only=True, dtype=torch.bfloat16,
            device_map={"": 0}, attn_implementation="sdpa",
            quantization_config=quantization,
        ).eval()
        self.model, self.tokenizer = model, tokenizer
        self._record({"operation": "load", "seconds": time.perf_counter() - start,
                      "peak_vram_gib": torch.cuda.max_memory_allocated() / 1024**3})

    def _record(self, metrics):
        self.last_metrics = metrics
        metrics["quantization_bits"] = self.bits
        folder = ROOT / "outputs"
        folder.mkdir(exist_ok=True)
        with (folder / "timings.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(metrics) + "\n")
        print(json.dumps(metrics), flush=True)

    def complete(self, messages, operation="inference"):
        with self.lock:
            self.load()
            import torch
            torch.cuda.reset_peak_memory_stats()
            start = time.perf_counter()
            text = self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
            inputs = self.tokenizer(text, return_tensors="pt").to("cuda:0")
            if inputs.input_ids.shape[-1] > 6144:
                raise ValueError("The request is too long. Please use a shorter answer.")
            decoding = ({"do_sample": True, "temperature": .8, "top_p": .9, "top_k": 20}
                        if operation == "generate" else {"do_sample": False})
            with torch.inference_mode():
                outputs = self.model.generate(**inputs, max_new_tokens=1024, **decoding, logits_to_keep=1,
                                              pad_token_id=self.tokenizer.eos_token_id)
            torch.cuda.synchronize()
            result = self.tokenizer.decode(outputs[0, inputs.input_ids.shape[-1]:], skip_special_tokens=True)
            self._record({"operation": operation, "seconds": time.perf_counter() - start,
                          "peak_vram_gib": torch.cuda.max_memory_allocated() / 1024**3})
            return result
