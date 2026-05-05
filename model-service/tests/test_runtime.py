from app.runtime import run_inference
from app.settings import Config


def test_run_inference_returns_profile_prefixed_output():
    config = Config(MODEL_RUNTIME_PROFILE='cpu')
    output = run_inference('  hello    world  ', config)
    assert output.startswith('[cpu] mock-inference: ')
    assert output.endswith('hello world')
