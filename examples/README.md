# Examples

A minimal, runnable example for `andes.pipelines.agent_tool`.

## Files

- `config.example.json` — a self-contained config for one ANDES run targeting
  the public OpenAI endpoint with `gpt-4o` and the `tool_call` format.

## Run it

```bash
export OPENAI_API_KEY=sk-...

# From the repository root
python -m andes.pipelines.agent_tool examples/config.example.json
```

On success, the script prints two lines on stdout:

```
/<...>/andes/pipelines/cache/andes_synthesis_<stamp>.jsonl
/<...>/andes/pipelines/cache/andes_report_<stamp>.txt
```

The synthesis file holds the generated SFT samples; the report file
summarizes scenario-collapse / diversity audits. Full logs are written to
`andes/pipelines/cache/andes_log_<stamp>.txt`.

## Config schema

| Field                | Required | Description                                                                                          |
|----------------------|:--------:|------------------------------------------------------------------------------------------------------|
| `api_url`            | Yes      | OpenAI-compatible chat-completions endpoint.                                                         |
| `task_description`   | Yes      | High-level description of the capability you want the synthesized data to cover.                     |
| `num_samples`        | Yes      | Target number of final samples. ANDES creates 3 questions per router node, so this is rounded down.  |
| `format_requirement` | Yes      | One of: `unstructured`, `code`, `tool_call`. Use `unstructured` for free-form responses.             |
| `model_name`         | No       | Defaults to `gpt-4o`.                                                                                |
| `max_workers`        | No       | Thread-pool size for the API client. Defaults to `8`.                                                |

The API key is **never** read from the config; it is taken from the
`OPENAI_API_KEY` environment variable so that secrets stay out of files.

## Routing-only dry run

To validate that your `task_description` produces a healthy split between
fusion and general samples without paying for full generation:

```bash
python -m andes.pipelines.simulate_routing \
    --config examples/config.example.json \
    --num-samples 1000 \
    --round-size 200
```

The simulation writes a per-round summary log under `andes/pipelines/cache/`.
