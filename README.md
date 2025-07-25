# Flux Image Generator

Generate refined prompts with OpenAI GPT-4 and produce images with the **FLUX-1-dev** SDXL model.  Supports:

* Apple Silicon / CUDA / CPU
* GPU pods (e.g. RunPod) with automatic memory-saving tweaks
* Optional upload of images to Amazon S3
* Optional batch mode driven by Google Sheets

---

## 1. Clone & install

```bash
# Clone
git clone https://bitbucket.org/twyzle/flux-image-generator.git
cd flux-image-generator

# Python ≥3.10 recommended
python -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt  # installs torch, diffusers, openai, …
```

### Additional GPU-pod steps (RunPod)

```bash
# inside pod
export HF_HOME=/workspace/hf_cache       # keep model weights on volume
pip install --no-cache-dir -r requirements.txt
```

---

## 2. Environment variables

Create a `.env` or export directly:

```bash
# --- core creds ---
export OPENAI_API_KEY=sk-…
export HUGGINGFACE_HUB_TOKEN=hf_…     # must have gated-repo access

# --- optional S3 upload ---
export AWS_ACCESS_KEY_ID=…
export AWS_SECRET_ACCESS_KEY=…
export AWS_DEFAULT_REGION=us-east-1
export S3_BUCKET=my-image-bucket      # set to activate upload
export S3_PREFIX=flux_outputs         # optional sub-folder

# --- optional Google Sheets batch mode ---
export SHEET_ID=1AbCdEFGhIJk…         # spreadsheet ID
export GOOGLE_APPLICATION_CREDENTIALS=/workspace/keys/service_account.json
```

> Tip: add the exports to `~/.bashrc` inside your pod.

---

## 3. Run (single prompt CLI)

```bash
python main.py "a sunset lighthouse on a cliff" -n 1
```

* Saves PNG(s) to `outputs/`
* If `S3_BUCKET` is set → uploads to `s3://$S3_BUCKET/$S3_PREFIX/…`

### Batch from Google Sheets

If `SHEET_ID` is present, `main.py` reads rows (columns: `Prompt`, `Industry`, `Subject`, …) and processes each one.

---

## 4. Copy results back to local machine

Assuming you SSH into the pod with:

```bash
ssh -p 1690 -i ~/.ssh/id_ed25519 root@193.183.22.55
```

Use `scp` to pull images:

```bash
scp -r -P 1690 -i ~/.ssh/id_ed25519 \
    root@193.183.22.55:/workspace/flux-image-generator/outputs \
    ~/flux_outputs
```

or resume-friendly `rsync`:

```bash
rsync -avP -e "ssh -p 1690 -i ~/.ssh/id_ed25519" \
      root@193.183.22.55:/workspace/flux-image-generator/outputs/ \
      ~/flux_outputs/
```

---

## 5. Memory tuning cheatsheet

| GPU | Recommended flags |
|-----|-------------------|
| ≥24 GB | default (full GPU) |
| 16 GB (RTX A4000) | attention slicing, VAE tiling, sequential CPU offload, 512×512 |
| M1/M2 | device `mps`, dtype `float32` |

All tweaks are auto-detected in `image_generator.py`.

---

## 6. Project structure

```
flux-image-generator/
├── image_generator.py   # Hugging Face Diffusers pipeline
├── prompt_refiner.py    # OpenAI GPT-4 prompt enhancer
├── main.py              # CLI / batch entry point
├── s3_uploader.py       # optional S3 helper
├── requirements.txt
└── outputs/             # generated images
```

---

## 7. Run with Docker (locally)

### Build the image
```bash
docker build -t flux-image-generator .
```

### Run (GPU)
```bash
docker run --gpus all \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e HUGGINGFACE_HUB_TOKEN=$HUGGINGFACE_HUB_TOKEN \
  -e S3_BUCKET=$S3_BUCKET -e S3_PREFIX=$S3_PREFIX \
  -v $(pwd)/outputs:/app/outputs \
  flux-image-generator \
  python main.py "a photorealistic cat" -n 1
```

*Remove `--gpus all` to run on CPU only.*

---

## 8. Deploy to RunPod Serverless

1. Fork or push this repo to GitHub/Bitbucket.
2. In RunPod ➜ *Serverless* ➜ **Create Worker** ➜ **From GitHub**.
3. Pick branch `main`, leave build context `/`, Dockerfile `Dockerfile`.
4. Add environment variables (`OPENAI_API_KEY`, `HUGGINGFACE_HUB_TOKEN`, `AWS_*`, `S3_BUCKET`, etc.).
5. (Optional) Attach a Network Volume and set:
   ```
   HF_HOME=/runpod-volume/hf_cache
   TRANSFORMERS_CACHE=/runpod-volume/hf_cache
   ```
6. Click **Deploy**. After the build shows *Worker is ready* you can submit jobs:
   ```bash
   curl -X POST https://api.runpod.ai/v2/<endpoint-id>/run \
        -H "Content-Type: application/json" \
        -d '{"input": {"prompt": "a sunset lighthouse", "num_images": 1}}'
   ```
   Then poll `/status/<job-id>` until `status":"COMPLETED"`.

The `output.files` array will contain HTTPS URLs like
`https://<bucket>.s3.<region>.amazonaws.com/<prefix>/image.png`.

---

Happy prompting 🚀
