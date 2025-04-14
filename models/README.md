# Models Directory

This directory is used to store LLM models for ingredient substitution generation.

## LLM Models

The system is configured to use Llama 3.1 for generating ingredient substitutions. If you want to use this functionality, you need to download a model and place it in this directory.

### Recommended Models

- **Llama 3.1 8B Instruct** (quantized): A good balance of performance and size
  - Filename: `llama-3.1-8b-instruct.Q4_K_M.gguf`
  - Download from: [TheBloke's Hugging Face page](https://huggingface.co/TheBloke/Llama-3.1-8B-Instruct-GGUF)

### Configuration

After downloading a model, update the `LLM_MODEL_PATH` variable in `src/utils/config.py` to point to your model:

```python
LLM_MODEL_PATH = MODELS_DIR / "your-model-filename.gguf"
```

### Alternative Approach

If you don't want to download a large model, the system will use pre-generated substitution mappings instead. These are included with the system and provide a good set of ingredient substitutions for most common use cases.

To disable LLM completely, set `USE_LLM = False` in `src/utils/config.py`.

## Other Models

This directory can also be used to store other models used by the system, such as embedding models or classification models if you extend the system in the future. 