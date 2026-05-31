# ANDES: Agent Native Data Evolving Synthesis Tool for Autonomous Instruction Alignment

#### Zhengyang Zhao (equal contribution), Shengjie Ye (equal contribution), Lu Ma, Hao Liang, Hengyi Feng, Wentao Zhang (corresponding author)

#### Peking University; Sichuan University

ANDES is an agent-native data evolving synthesis tool that turns high-quality SFT data generation into a plug-and-play skill for autonomous post-training agents.

[![Repo](https://img.shields.io/badge/GitHub-zzy1127%2FANDES-181717?logo=github)](https://github.com/zzy1127/ANDES)
[![License](https://img.shields.io/badge/License-Apache--2.0-green)](LICENSE)
[![Python](https://img.shields.io/badge/Python-%3E%3D3.10-blue?logo=python)](pyproject.toml)
[![Preprint](https://img.shields.io/badge/Paper-Preprint-red)](#citation)

## News

- **2026.05.31** We release the ANDES preprint and initial open-source repository.
- **Coming soon** We will continue updating core code documentation, supported model recipes, and citation metadata.

## Highlights

- **Agent-native synthesis skill:** ANDES exposes data generation as a simple tool-calling interface, allowing trainer agents to request targeted data without designing a full web-search or offline synthesis pipeline from scratch.
- **Self-evolving World Tree routing:** A Topic -> Theme -> Scenario taxonomy routes synthesis toward target-aligned regions while dynamically expanding crowded nodes to preserve scenario diversity.
- **Two-stage QA generation and refinement:** ANDES first generates raw QA data, then critiques, filters, rewrites, and summarizes it with quality and logical-diversity diagnostics.
- **Report-driven closed loop:** Each call returns refined data plus a synthesis report, so the trainer agent can adjust later requests based on topic distribution, effective sample count, and collapse patterns.
- **Strong autonomous post-training results:** In the paper setting, GLM-4.7 equipped with ANDES reaches **33.39%** average accuracy on PostTrainBench, outperforming Opus-4.7 at **28.56%**.

## Overview

![ANDES Overview](assets/andes_overview.png)

> **TLDR:** ANDES reframes data synthesis for autonomous post-training as an interactive agent skill. A trainer agent decomposes downstream benchmarks into capability domains, invokes ANDES once per domain, and uses the returned reports to steer the next synthesis round.

ANDES is built around four stages:

1. **Target-driven agent request:** the trainer agent abstracts downstream benchmarks into transferable capability dimensions and submits a task description, sample budget, and optional format protocol.
2. **Self-evolving dynamic World Tree routing:** ANDES samples topics from a large taxonomy, uses an LLM router to classify each scenario as strong, ambiguous, or weak for the target task, and updates topic weights accordingly.
3. **Two-stage data synthesis:** the generator creates task-aligned or general QA data, then the refiner critiques, filters, rewrites, and audits logical diversity.
4. **Outputs and feedback:** ANDES returns refined SFT data and a report that helps the trainer agent actively filter data and configure the next call.

## Core Codes and Supported Models

The current implementation focuses on API-based SFT data synthesis for agentic post-training.

| Component | Path |
| --- | --- |
| Agent tool entry point | [`andes/pipelines/agent_tool.py`](andes/pipelines/agent_tool.py) |
| ANDES generator | [`andes/operators/text_sft/generate/andes_generator.py`](andes/operators/text_sft/generate/andes_generator.py) |
| ANDES refiner and report builder | [`andes/operators/text_sft/refine/andes_refiner.py`](andes/operators/text_sft/refine/andes_refiner.py) |
| Prompt templates and World Tree tags | [`andes/prompts/andes_prompts.py`](andes/prompts/andes_prompts.py) |
| API LLM serving wrapper | [`andes/serving/api_llm_serving_request.py`](andes/serving/api_llm_serving_request.py) |
| Example config | [`examples/config.example.json`](examples/config.example.json) |

**Supported models:** Coming soon. The current public package is model-agnostic at the data-synthesis layer and uses an OpenAI-compatible API backend for routing, generation, refinement, evolution, and diversity summarization.

## Preparation

1. Clone this repository:

```bash
git clone https://github.com/zzy1127/ANDES.git
cd ANDES
```

2. Create an environment and install ANDES:

```bash
conda create -n andes python=3.10 -y
conda activate andes
pip install --upgrade pip
pip install -e .
```

3. Configure your API key:

```bash
export OPENAI_API_KEY=your_api_key
```

## Quick Start

Edit [`examples/config.example.json`](examples/config.example.json) or create a JSON config with the required fields:

```json
{
  "api_url": "https://api.openai.com/v1/chat/completions",
  "model_name": "gpt-4o",
  "task_description": "Describe the capability, scenario, and data style you want ANDES to synthesize.",
  "format_requirement": "unstructured",
  "num_samples": 300,
  "max_workers": 8
}
```

Run the ANDES agent tool:

```bash
python -m andes.pipelines.agent_tool examples/config.example.json
```

The command prints two artifact paths:

- `andes_synthesis_<timestamp>.jsonl`: refined SFT data.
- `andes_report_<timestamp>.txt`: logical-diversity and synthesis diagnostics for the next agent call.

Artifacts are written to `andes/pipelines/cache/`.

`format_requirement` currently supports:

| Value | Behavior |
| --- | --- |
| `unstructured` | No extra answer-format constraint. |
| `code` | Fusion-track answers must be wrapped in a Markdown code block. |
| `tool_call` | Fusion-track answers must be wrapped as JSON tool calls. |

## Results

![PostTrainBench Results](assets/posttrainbench_results.png)

### Autonomous Post-Training on PostTrainBench

Under the official PostTrainBench setting, ANDES is evaluated across four base models and seven benchmarks: AIME 2025, ArenaHardWriting, BFCL, GPQA-Main, GSM8K, HealthBench, and HumanEval.

| Method | Average Accuracy |
| --- | ---: |
| Official instruct models | 51.14% |
| Base models, zero-shot average | 7.53% |
| GLM-4.7 with OpenCode baseline | 7.48% |
| Opus-4.7 (xHigh) | 28.56% |
| **GLM-4.7 with ANDES** | **33.39%** |

### Cross-Task Generalization

In the extended multi-target synthesis setting, ANDES uses 10k synthesized samples for Qwen3-8B and reaches **58.9%** overall across AIME24, Gaokao, MBPP, MMLU, and CEVAL, outperforming 10k and 1M static-data baselines reported in the paper.

## Citation

Coming soon. Citation metadata will be added after the public paper record is finalized.

## Acknowledgment

We build the codebase on the DataFlow framework and evaluate the autonomous post-training setting with PostTrainBench. We thank the open-source post-training, data-synthesis, and agent-tooling communities for the foundations that made this work possible.

## Contact

For questions about the paper or code, please contact:

- `zhengyangzhao25@stu.pku.edu.cn`
- `yeshengjie@stu.scu.edu.cn`
- `wentao.zhang@pku.edu.cn`
