# ANDES

**ANDES (Agent-Native Data Evolving Synthesis)** is a plug-and-play data synthesis tool designed for post-training agent loops.

The trainer agent declares a target capability domain, and ANDES returns a refined dataset together with a synthesis report. Each call takes a task description `τ`, a sample budget `N`, and an optional format protocol `φ`, and runs three stages internally:

1. **World Tree Router** — samples topics from a self-evolving taxonomy (1,000+ scenarios), classifies each as *Strong / Ambiguous / Weak* for the given task description, and updates topic sampling weights accordingly. Saturated subtrees are automatically expanded by an LLM to maintain diversity.
2. **QA Generator** — for each routed scenario, generates Easy/Medium/Hard questions and corresponding answers. Fusion-track samples are constrained to exercise the target capability; generic-track samples provide broad instruction diversity.
3. **Refiner** — critiques each answer, discards low-quality responses via an effort-score filter, rewrites the rest, and runs a scenario-collapse audit over fusion samples to produce the synthesis report `R`.

The report drives the next invocation: the trainer agent revises the task description to cover underexplored angles and adjusts the sample budget to compensate for discarded samples.

## Quick Start

```bash
git clone https://github.com/your-org/andes.git
cd andes
pip install -e .

export OPENAI_API_KEY=sk-...

python -m andes.pipelines.agent_tool examples/config.example.json
```

Outputs two lines on success: synthesis file path and report file path. Artifacts are written to `andes/pipelines/cache/`.

## Config

```json
{
  "api_url": "https://api.openai.com/v1/chat/completions",
  "model_name": "gpt-4o",
  "task_description": "...",
  "num_samples": 300,
  "format_requirement": "unstructured",
  "max_workers": 8
}
```

`format_requirement`: one of `unstructured`, `code`, `tool_call`. The API key is read from `OPENAI_API_KEY` — never put it in the config file.

See [`examples/`](examples/) for a full runnable example.

## License

Apache-2.0
