---
name: andes-data-synthesis
description: >
  ANDES Data Synthesis Skill Guide: instructs an agent to install and configure ANDES in a sandbox
  environment, split a benchmark into domains, invoke the ANDES synthesis tool, apply quality control,
  and deliver `<benchmark>.json` for downstream training.
---

# ANDES Data Synthesis Skill

> Tool manual for agents executing ANDES data synthesis. Follow it as an operational checklist.

## 1. Agent Operating Contract

Use this skill when a benchmark must be converted into training data through the ANDES synthesis tool.

The agent controls planning, benchmark interpretation, quality judgment, and final aggregation. The ANDES tool performs the requested runtime operations and returns artifacts such as synthesized data, reports, and evaluation summaries.

**Execution contract**:
- **Agent**: research the benchmark -> split domains -> write `task_description` -> choose `num_samples` -> choose `format_requirement` -> read reports and evaluation summaries -> decide discard ratio -> decide whether to add domains -> aggregate data
- **ANDES tool**: receive agent-provided parameters -> prepare `config.json` if required by the runtime -> run ANDES -> return synthesized data, reports, and evaluation summaries -> execute random discard exactly as instructed by the agent

> [!IMPORTANT]
> ANDES is **NOT** a one-shot generator. Each domain synthesizes once, and after all initial domains are done, check the total retained volume.

## 2. Execution Pipeline

### 2.1 Core Steps

| Step | Action | Output | Report Read |
|------|--------|--------|-------------|
| 1 | Split benchmark into ~6 non-overlapping domains | Domain list | N/A |
| 2 | Write `task_description` + `num_samples` + `format_requirement` for the first domain | `config.json` | N/A |
| 3 | Invoke the ANDES tool to run synthesis for the current domain | `data_path`, `report_path` | N/A |
| 4 | Read the report or evaluation summary + `task_description`, decide discard ratio (0% / 10% / 20%) | Discard decision | **MUST read both `andes_report_*.txt` and the corresponding `task_description`** |
| 5 | Invoke the ANDES tool to execute random discard | Retained data | N/A |
| 6 | Repeat steps 2-5 until all initial domains complete | | N/A |
| 7 | **Phase 1 complete**: if total >= 8000, proceed to aggregation; **Phase 2**: if total < 8000, add new domains (no discard) - **never skip initial domains** | Data volume decision | N/A |
| 8 | Aggregate all retained data -> `${ANDES_WORKSPACE}/<benchmark>.json` | Deliverable | N/A |

### 2.2 Key Rules

- Each domain **synthesizes only once**; do not repeatedly resynthesize the same domain (leads to path fixation)
- `format_requirement` **remains unchanged after the first selection**
- Check disk before each domain switch: `df -h ${ANDES_WORKSPACE}`

## 3. Core Parameters

| Parameter | Description | Rules |
|-----------|-------------|-------|
| `task_description` | Describes capability dimensions, knowledge levels, structural requirements, and constraint types | See the five principles below |
| `num_samples` | Planned raw synthesis volume per domain | 1500-1700; final total >= 8000 |
| `format_requirement` | Output format options | `unstructured` / `code` / `tool_call`, selected only in the first round |

### 3.1 `task_description` Writing Principles

1. **Macro-level description**: describe capability dimensions, structural requirements, and constraint types; do not lock onto specific problems or include example questions in descriptions. Each domain description should define a **fundamental cognitive operation** - see Principle 5 for domain splitting guidance.
2. **Seek real capability differences**: prioritize differences in task structure, reasoning chains, constraint combinations, and difficulty levels.
3. **Maintain benchmark alignment**: return to the benchmark's real capability requirements each round; do not let descriptions become increasingly empty.
4. **Use abstract requirements to increase difficulty**: more complex constraint coupling, stricter judgment conditions, and more professional contexts.
5. **Macro-level domain capability splitting**: when dividing the benchmark into ~6 domains, each domain MUST represent a broad, fundamental capability dimension (e.g. multi-step reasoning, structured information extraction, constraint satisfaction, iterative refinement) rather than a narrow knowledge point (e.g. "calculation of binomial probability"). Domains must be differentiated by **cognitive operation type and reasoning structure**, not by surface topic or specific algorithm. This ensures the synthesized data cultivates generalizable cognitive skills rather than rote responses to specific problem patterns.

### 3.2 Data Volume Planning

| Metric | Value |
|--------|-------|
| Target retained volume | >= 8000 records |
| Raw synthesis per domain | 1500-1700 records |
| Initial domain count | ~6 domains |
| Expected discard rate | ~10% |
| Final retained volume | ~8100 records |

> [!IMPORTANT]
> Synthesis volume must exceed the target retained volume. **Do NOT compensate for insufficient initial synthesis volume through post-aggregation filtering.**
>
> **Time Constraint**: synthesis continues until either (a) retained records reach ~8000, or (b) total synthesis elapsed time exceeds 7 hours - whichever comes first. Before the 7-hour threshold is reached, **no reason - including quality satisfaction - permits early termination of synthesis**.

### 3.3 Mandatory Step: Read Report and Decide Discard Ratio After Each Synthesis

**After the ANDES tool finishes synthesis for each domain, the agent MUST execute the following steps. Skipping or pre-setting discard ratios is strictly forbidden:**

1. **`read_file(andes_report_*.txt)`**: locate and read the most recently generated report file. If the tool runtime exposes an additional evaluation summary, read that artifact as well.
2. **`read_file(config.json)` or the stored `task_description` for this domain**: retrieve the exact `task_description` that was used to generate this batch of data.
3. **Analyze each Failure Signal F1-F7 against `task_description`**: cross-reference the failure signals in the report or evaluation summary with the original `task_description` to evaluate whether the generation stayed true to the intended capability dimensions and constraints. Record this comparison reasoning in the log.
4. **Decide a specific discard ratio based on both the report and the `task_description`**: choose from **0% / 10% / 20%**, and record the decision reasoning in the log - including how the `task_description` informed the choice. **The agent makes this decision; the ANDES tool only executes the random discard afterward.**
5. **Pre-setting fixed discard ratios is prohibited**: it is strictly forbidden to apply a uniform discard ratio to all domains without first reading the report, any tool-provided evaluation summary, and the corresponding `task_description`.

> [!WARNING]
> Proceeding to the next step without reading the report is considered a **violation of the statistical integrity principle**, and all subsequent outputs are deemed unreliable.

## 4. Environment Configuration

### 4.1 Installation

```bash
git clone https://github.com/your-org/andes.git
cd andes
pip install -e .
```

- Repository: `your-org/andes`
- Working directory: `${ANDES_WORKSPACE}` (default: an isolated sandbox path used by the tool runtime)
- Environment: sandboxed runtime (e.g. container or jail)

### 4.2 API Key

> [!IMPORTANT]
> ANDES reads `OPENAI_API_KEY` from the environment.

```bash
export OPENAI_API_KEY="sk-..."
```

The key MUST come from the runtime environment; it is never written into a config file.

### 4.3 `config.json` Format

```json
{
  "api_url": "https://api.openai.com/v1/chat/completions",
  "model_name": "gpt-4o",
  "task_description": "...",
  "num_samples": 1600,
  "format_requirement": "tool_call",
  "max_workers": 100
}
```

| Field | Description |
|-------|-------------|
| `api_url` | OpenAI-compatible chat-completions endpoint (fixed for the run). |
| `model_name` | Optional; defaults to `gpt-4o`. |
| `task_description` | **Decided by the agent**; the ANDES tool must not alter its semantic meaning. |
| `num_samples` | **Decided by the agent.** |
| `format_requirement` | **Decided only in the first round**, unchanged thereafter. |
| `max_workers` | **Fixed at 100.** |

### 4.4 Tool Invocation Command

Invoke the ANDES tool with:

```bash
python -m andes.pipelines.agent_tool ${ANDES_WORKSPACE}/andes_config/config.json
```

On success, the tool returns:

1. Data path: `andes_synthesis_<timestamp>.jsonl`
2. Report path: `andes_report_<timestamp>.txt`

Log location: `andes/pipelines/cache/andes_log_<timestamp>.txt`

If the runtime surfaces a separate evaluation summary in addition to the report, treat it as an additional artifact that must be inspected before deciding the discard ratio.

## 5. Quality Control

### 5.1 Seven Failure Signals

| ID | Signal | Consequence |
|----|--------|-------------|
| F1 | Description too narrow | Generator revolves around very few structures |
| F2 | Flashy surface, collapsed logic | No substantive data diversity |
| F3 | Template lock-in | Large-scale near-duplicates |
| F4 | Coverage collapse | Benchmark-related capabilities not covered |
| F5 | Constraint drift | Deviates from benchmark requirements |
| F6 | Form without substance | Low training value |
| F7 | Description growing emptier | Generated results semantically loose |

### 5.2 Report Reading Guide

Compare against `task_description`, focusing on:

- Whether generated results cover all capability dimensions
- Whether any failure signals appear in the report or tool-provided evaluation summary
- Overall diversity and benchmark alignment

## 6. Constraint Rules (Must Follow)

> [!CRITICAL]
> The following constraints are **non-negotiable hard requirements**. The executing agent MUST enforce them unconditionally.

### G0: No Content Filtering - Only Random Discard

**No manual content filtering or format conversion of ANY kind is permitted on ANDES-generated data.**

ANDES produces two types of output in each batch:

- **Generic data**: standard-format samples generated for the target capability domain.
- **Fusion data**: cross-capability or multi-constraint combined samples.

Both types carry training value. **Non-standard-format data (e.g. non-tool-call responses, free-text answers) must NOT be manually removed, filtered, or discarded based on content inspection.** Regardless of the `format_requirement` used during synthesis (e.g. `code`, `tool_call`, `unstructured`), **all synthesized samples returned by the tool must be aggregated and used verbatim without any reformatting, rewriting, or conversion.** The only permitted data reduction operation is **random discard** executed per the discard ratio decision in Section 3.3.

Any script, command, or manual step that filters, drops, reformats, or removes samples from ANDES output based on format, content, structure, or keyword matching - beyond the mandated random discard - is a **direct violation** of this skill.

### G1: No Secondary Filtering

After random discard of each batch, **absolutely NO secondary filtering** (keyword filtering, deduplication, format conversion, etc.). All retained samples must be aggregated and fed to training as-is.

### G2: Training Forbidden Until Volume Threshold Met

**Training MUST NOT begin until ~8000 retained records are available. Do not terminate synthesis early on grounds of "sufficient quality."**

**Timeout Exemption**: the only exception to the above rule is when the total elapsed time of the ANDES synthesis phase has exceeded **7 hours**. In this case only, the agent may proceed to training with whatever data is currently available. All other reasons - including "quality is good enough", "time is tight", or "initial domains are done" - are strictly prohibited.

**Phase Ordering**: the agent MUST complete all initially planned domains before synthesizing any new (expanded) domains. Synthesizing new domains before finishing the initial domain list is a violation of this constraint.

### G3: Disk 80% Mandatory Cleanup

Check disk before each domain switch:

- **> 80%**: immediately clean up, then proceed.
- **> 90%**: mandatory cleanup + evaluate whether to pause synthesis.

Cleanup priority: 1) `saves/` historical checkpoints -> 2) `cache/*.jsonl` -> 3) `hf_cache/` -> 4) `__pycache__/`

### G4: Per-Batch Synthesis Volume Buffer

Each domain should initially synthesize **more than 1500 records**. Recommended: synthesize 1500-1700 per domain, retain ~1350-1530 after discard.

### G5: Checkpoint Save Strategy

```yaml
output_dir: saves/<task_name>
save_total_limit: 3      # Keep the 3 most recent checkpoints
save_only_model: true    # Save model weights only, reduces storage ~13G -> ~6.5G
```

## 7. Error Handling

> [!CRITICAL]
> **It is forbidden to abandon ANDES synthesis due to any error. There is no backup plan.**

| Error Type | Response |
|------------|----------|
| Environment installation failure | Fix dependencies, reinstall |
| API timeout | Wait, retry with exponential backoff |
| API connection error | Check network, verify API key |
| Model download failure | Retry or use cached model |
| Disk space full | Clean up disk, then retry |

**Handling Principles**: retry first -> fix the root cause -> try alternative approaches within the same workflow -> escalate.

**Absolute Prohibitions**: abandon synthesis / switch to external data sources / skip difficult domains / report as unresolvable without attempting all solutions.

## 8. Deliverables

### Final Output

| File | Path |
|------|------|
| Training data | `${ANDES_WORKSPACE}/<benchmark>.json` |
| Format | Alpaca: `{"instruction": ..., "input": ..., "output": ...}` |

> [!IMPORTANT]
> **Use ALL synthesized data without any sampling cap.** After random discard per domain, aggregate ALL remaining samples into `<benchmark>.json`. Do not drop, filter, reformat, or truncate any sample during aggregation. The downstream training job receives the complete aggregated dataset.

> [!NOTE]
> Downstream training uses the aggregated `.json` file, not the per-round `.jsonl` raw files.

## 9. Quick Reference

```text
Step 1:  Research benchmark, split into ~6 domains
Step 2:  Write task_description for first domain, determine num_samples, select format_requirement
Step 3:  Invoke the ANDES tool to run synthesis
Step 4:  Read report + task_description, then decide discard ratio (0% / 10% / 20%)
Step 5:  Invoke the ANDES tool to execute random discard
Step 6:  Switch to next domain, repeat 2-5 (complete ALL initial domains first)
Step 7:  Phase 1 done - if total >= 8000, go to Step 8; if < 8000, add new domains (no discard)
         (ONLY exception: if synthesis elapsed time > 7 hours, proceed to training with available data)
Step 8:  Aggregate data -> ${ANDES_WORKSPACE}/<benchmark>.json
```
