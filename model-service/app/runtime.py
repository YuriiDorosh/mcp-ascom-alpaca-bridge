from app.settings import Config


def run_inference(prompt: str, config: Config) -> str:
    normalized = " ".join(prompt.split())
    trimmed = normalized[:400]
    return f"[{config.model_runtime_profile}] mock-inference: {trimmed}"
