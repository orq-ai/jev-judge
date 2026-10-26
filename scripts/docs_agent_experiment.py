"""Judge-repeatability experiment over the frozen docs-agent runs: one evaluatorq() call.

Design mirrors LangChain's "Jev-as-a-Judge for Agent Evals": agent outputs are frozen
(`data/docs_rag/frozen.jsonl`, raw responses payloads with trace ids and costs), human labels are fixed
(`labels.jsonl`), only the judges rerun. The dataset carries the labels as `expected_output`; the job returns
the frozen run; one evaluator per (judge model, question) asks the judge `--reps` times through evaluatorq's
own judge stack (Orq-format prompt templates, `run_judge` x N under a per-model semaphore), and reports the
modal verdict, every raw repetition, and agreement with the label. Jev joins through the classify endpoint.

    uv run python scripts/docs_agent_experiment.py --reps 20
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from jev_judge.models import api_key, get_adapter

api_key()  # fail here, not mid-run, when ORQ_API_KEY is missing: evaluatorq reads it at import time too

import evaluatorq.common.judge as _judge
import typer
from evaluatorq import DataPoint, EvaluationResult, evaluatorq
from evaluatorq.common.judge import build_eval_replacements, run_judge
from evaluatorq.common.llm_client import resolve_llm_client
from evaluatorq.contracts import LLMCallConfig, TextOutputItem, ToolCallOutputItem
from loguru import logger
from pydantic import BaseModel, Field
from rich.console import Console
from rich.table import Table

from jev_judge import tasks as benchmark_tasks
from jev_judge.repeat import summarise
from jev_judge.results import write_results

# Match docs_agent_freeze.py when it is run against a non-default dataset directory.
if os.environ.get('DOCS_RAG_DIR'):
    benchmark_tasks.DOCS_RAG_DIR = Path(os.environ['DOCS_RAG_DIR']).expanduser().resolve()

DOCS_RAG_QUESTIONS = benchmark_tasks.DOCS_RAG_QUESTIONS
build_docs_rag = benchmark_tasks.build_docs_rag
docs_rag_answer = benchmark_tasks.docs_rag_answer
docs_rag_search_result = benchmark_tasks.docs_rag_search_result


async def _never_classify(model: str, client: object = None) -> bool:
    """evaluatorq >= 1.40 routes any model the Orq catalogue marks classify-capable (gpt-5.6-luna is) to
    `/classify` and refuses without a classify question. The LLM judges here are prompted judges by design;
    Jev goes through its own adapter. Keep run_judge on the prompt path."""
    return False


_judge.supports_classify = _never_classify

JUDGES = ('baseten/deepseek-v4.1-flash', 'google-ai/gemini-3.8-flash', 'openai/gpt-5.6-luna')
RESULTS = Path(__file__).resolve().parents[1] / 'results' / 'docs_rag'
# "matched" arm: every LLM judge as close to Jev's single-pass, no-sampling regime as the router lets it get.
# gpt-5.6-luna honours temperature 0 and spends no reasoning tokens by default; gemini and deepseek ignore
# temperature but accept `reasoning.effort=none` (probed 2026-09-20, 6 calls each).
MATCHED = {
    'openai/gpt-5.6-luna': {'temperature': 0.0},
    'google-ai/gemini-3.8-flash': {'extra_body': {'reasoning': {'effort': 'none'}}},
    'baseten/deepseek-v4.1-flash': {'extra_body': {'reasoning': {'effort': 'none'}}},
}
JUDGE_CONCURRENCY = 6  # in-flight calls per judge model; 720 at once gave 500s, 429s and timeouts
console = Console(width=160)

SYSTEM_PROMPT = (
    'You are a documentation-assistant evaluator. Respond ONLY with a JSON object containing exactly two keys:\n'
    '- "value": the verdict in the type the question asks for (boolean, or an integer level)\n'
    '- "explanation": string (1-3 sentences)\n'
)


QUALITY_LEVELS = 5  # score evals answer a level index 0-4


class BoolVerdict(BaseModel):
    value: bool
    explanation: str


class LevelVerdict(BaseModel):
    value: int = Field(ge=0, le=QUALITY_LEVELS - 1)  # level index; the schema, not the prose, keeps judges in range
    explanation: str


# ponytail: evaluatorq's default payload carries an `abstain` flag that judges kept setting true; own models drop it
VERDICT_MODEL = {qid: BoolVerdict if q['type'] == 'noul' else LevelVerdict for qid, q in DOCS_RAG_QUESTIONS.items()}
CONTEXT = (
    'User question:\n{{input.all_messages[0].content}}\n\n'
    'Documentation searches the assistant ran (tool name, arguments, raw results):\n{{output.tools_called}}\n\n'
    'Assistant answer:\n{{output.response}}\n\n'
)


def prompt_template(qid: str) -> str:
    q = DOCS_RAG_QUESTIONS[qid]
    if q['type'] == 'noul':
        return CONTEXT + f'Question: {q["instructions"]}\nAnswer "value": true or false.'
    levels = '\n'.join(f'  {i}: {c}' for i, c in enumerate(q['criteria']))
    return CONTEXT + f'Question: {q["instructions"]}\nLevels:\n{levels}\nAnswer "value": the level index as an integer.'


def output_items(raw: dict) -> list:
    """Frozen responses `output` as evaluatorq output items; search results as parsed pages, same as the Jev state."""
    items = []
    for o in raw['output']:
        if o.get('type') == 'orq:search_orq_docs':
            result = docs_rag_search_result(o)
            items.append(
                ToolCallOutputItem(
                    id=o['id'], call_id=o['call_id'], name=o['name'], arguments=o['arguments'], result=result
                )
            )
    if answer := docs_rag_answer(raw):
        items.append(TextOutputItem(text=answer))
    return items


def norm(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


class Bench:
    """Shared judge client plus the per-(judge, case) repetition cache the summary is built from."""

    def __init__(self, reps: int, *, matched: bool = False, judges: tuple[str, ...] = JUDGES) -> None:
        self.reps = reps
        self.matched = matched
        self.judges = judges
        self.client = resolve_llm_client(require_orq=True).client
        self.rows: dict[str, list[dict]] = {}  # judge name -> prediction rows (one per case, qid, rep)
        self._jev = get_adapter('jev')
        self._pool = ThreadPoolExecutor(max_workers=8)
        self._jev_cache: dict[str, asyncio.Future] = {}
        self._slots = {m: asyncio.Semaphore(JUDGE_CONCURRENCY) for m in judges}

    async def llm_reps(self, model: str, qid: str, row: dict) -> list[dict]:
        """One dict per repetition, in repetition order: pred, its own latency, explanation, cost, token usage.

        The repetitions are gathered directly rather than through `run_jury`, which runs them concurrently and
        would hand back a `repetitions` list that no completion-order side list lines up with; here every call
        builds its own row, so rep k's latency and explanation provably belong to rep k's prediction.
        """
        repl = build_eval_replacements(
            input_messages=[{'role': 'user', 'content': row['meta']['question']}],
            output_messages=output_items(row['meta']['raw']),
        )
        cfg = LLMCallConfig(
            model=model,
            api='responses',
            max_tokens=8000,
            timeout_ms=180_000,
            retry_count=4,
            **({'temperature': 1.0} | MATCHED[model] if self.matched else {'temperature': 1.0}),
        )
        endpoints: set[str | None] = set()

        async def one_rep() -> dict:
            async with self._slots[model]:
                t0 = time.perf_counter()
                out = await run_judge(
                    client=self.client,
                    model=model,
                    cfg=cfg,
                    prompt_template=prompt_template(qid),
                    replacements=repl,
                    system_prompt=SYSTEM_PROMPT,
                    response_model=VERDICT_MODEL[qid],
                )
                latency = (time.perf_counter() - t0) * 1000
            endpoints.add(out.endpoint)
            usage = out.token_usage
            failed = out.error_kind is not None or out.payload is None
            return {
                'pred': None if failed else norm(out.payload.value),
                'explanation': None if failed else out.payload.explanation,
                'probs': None,  # LLM judges return a verdict, not a distribution
                'latency_ms': latency,
                'cost': usage.total_cost if usage and usage.total_cost else 0.0,
                'token_usage': usage.model_dump(mode='json', exclude_defaults=True) if usage else None,
            }

        reps = await asyncio.gather(*[one_rep() for _ in range(self.reps)])
        if endpoints != {'responses'}:
            logger.warning(f'⚠ {model} {qid} served by {endpoints}, not the responses endpoint')
        return list(reps)

    async def jev_reps(self, row: dict) -> list[dict[str, dict]]:
        if row['id'] not in self._jev_cache:
            loop = asyncio.get_running_loop()
            self._jev_cache[row['id']] = asyncio.gather(
                *[
                    loop.run_in_executor(self._pool, self._jev.predict, row['state'], DOCS_RAG_QUESTIONS)
                    for _ in range(self.reps)
                ]
            )
        return await self._jev_cache[row['id']]

    def record(self, judge: str, row: dict, qid: str, reps: list[dict], *, shared_call: bool = False) -> None:
        """One row per repetition, carrying that call's own latency, explanation, probs, cost and token usage.

        `shared_call` marks a judge that answers every question of a case in one call (Jev), so the rows of that
        case and repetition carry the same `call_id` and the analysis can tell physical calls from decisions."""
        self.rows.setdefault(judge, []).extend(
            {
                'id': row['id'],
                'qid': qid,
                'type': DOCS_RAG_QUESTIONS[qid]['type'],
                'gold': row['gold'][qid],
                'pred': rep['pred'],
                'rep': k,
                'call_id': f'{judge}:{row["id"]}:{k}' if shared_call else f'{judge}:{row["id"]}:{qid}:{k}',
                'cost': rep['cost'],
                'latency_ms': rep['latency_ms'],
                'explanation': rep.get('explanation'),
                'probs': rep.get('probs'),
                'token_usage': rep.get('token_usage'),
            }
            for k, rep in enumerate(reps)
        )


def result(reps: list[dict], gold: str) -> EvaluationResult:
    """The cell's verdict for the Orq upload: modal answer, every repetition, agreement and cost."""
    preds = [r['pred'] for r in reps]
    explanations = [r['explanation'] for r in reps if r.get('explanation')]
    cost = sum(r['cost'] for r in reps)
    ok = [p for p in preds if p is not None]
    mode, n_mode = Counter(ok).most_common(1)[0] if ok else (None, 0)
    denominator = max(len(preds), 1)
    return EvaluationResult(
        value=mode if mode is not None else 'error',
        pass_=mode == gold,
        explanation=f'gold={gold} reps={preds} agreement={n_mode / denominator:.2f} cost=${cost:.5f}'
        + (f' | {explanations[0]}' if explanations else ''),
        raw_output={
            'gold': gold,
            'repetitions': preds,
            'accuracy': sum(p == gold for p in preds) / denominator,
            'cost_usd': cost,
        },
    )


def evaluators(bench: Bench, by_case: dict[str, dict]) -> list[dict]:
    evs = []
    for model in bench.judges:
        for qid in DOCS_RAG_QUESTIONS:

            async def llm_scorer(params: dict, model: str = model, qid: str = qid) -> EvaluationResult:
                row = by_case[params['data'].inputs['id']]
                judge_reps = await bench.llm_reps(model, qid, row)
                bench.record(model.split('/')[-1], row, qid, judge_reps)
                return result(judge_reps, row['gold'][qid])

            evs.append({'name': f'{model.split("/")[-1]}/{qid}', 'scorer': llm_scorer})
    for qid in DOCS_RAG_QUESTIONS:

        async def jev_scorer(params: dict, qid: str = qid) -> EvaluationResult:
            row = by_case[params['data'].inputs['id']]
            calls = await bench.jev_reps(row)
            jev_reps = [
                {
                    'pred': c[qid]['pred'],
                    'explanation': None,  # the classify endpoint returns probabilities, not prose
                    'probs': c[qid]['probs'],
                    'latency_ms': c[qid]['latency_ms'],
                    'cost': c[qid]['cost'],
                    'token_usage': None,
                }
                for c in calls
            ]
            bench.record('jev', row, qid, jev_reps, shared_call=True)
            return result(jev_reps, row['gold'][qid])

        evs.append({'name': f'jev/{qid}', 'scorer': jev_scorer})
    return evs


async def run(
    reps: int, path: str | None, out: Path, *, send: bool, matched: bool, judges: tuple[str, ...] = JUDGES
) -> None:
    rows = build_docs_rag()
    by_case = {r['id']: r for r in rows}
    data = [
        DataPoint(
            inputs={'id': r['id'], 'question': r['meta']['question'], 'trace_id': r['meta']['trace_id']},
            expected_output=json.dumps(r['gold']),
        )
        for r in rows
    ]

    async def job(dp: DataPoint, _i: int) -> dict:
        return {'name': 'docs-agent (frozen)', 'output': by_case[dp.inputs['id']]['meta']['raw']}

    bench = Bench(reps, matched=matched, judges=judges)
    await evaluatorq(
        f'docs-agent judge repeatability x{reps}' + (' matched' if matched else ''),
        data=data,
        jobs=[job],
        evaluators=evaluators(bench, by_case),
        datapoint_parallelism=2,
        print_results=False,
        path=path,
        _send_results=send,
    )

    summaries = []
    for judge, prows in bench.rows.items():
        write_results(prows, out / f'{judge}.jsonl')  # every repetition in one file; rows carry `rep`
        summaries.append(summarise(judge, prows))
    (out / 'repeat_summary.json').write_text(json.dumps(summaries, indent=2) + '\n')

    table = Table(title=f'docs-agent judge repeatability, {reps} reps x {len(rows)} cases')
    for col in ('judge', 'accuracy', 'repeatability', 'signal', 'unstable cells', 'failed', '$/call', 's/call'):
        table.add_column(col)
    for s in summaries:
        table.add_row(
            s['judge'],
            f'{s["accuracy"]["all"]["value"]:.3f}',
            f'{s["repeatability"]["all"]:.3f}',
            f'{s["signal"]["all"]:.3f}',
            str(sum(len(cases) for cases in s['unstable'].values())),
            str(s['failures']['total']),
            f'{s["cost"]["cost_per_call_usd"]:.4f}',
            f'{s["cost"]["latency_per_call_s"]:.2f}',
        )
    console.print(table)
    for s in summaries:
        for qid in [*s['binary_evals'], *s['score_evals']]:
            logger.info(
                f'{s["judge"]} {qid}: acc {s["accuracy"][qid]["value"]:.2f} '
                f'repeat {s["repeatability"][qid]:.2f} unstable {len(s["unstable"][qid])} '
                f'failed {s["failures"]["per_eval"][qid]}'
            )


def main(
    reps: int = 20,
    path: str = 'Default/docs-agent',
    out: Path = RESULTS,
    *,
    send: bool = True,
    matched: bool = False,
    judges: str = ','.join(JUDGES),
) -> None:
    """`--matched` pins every LLM judge to its least-sampled regime (see MATCHED); `--out` picks the result dir;
    `--judges` is a comma-separated list of router model ids to run beside Jev."""
    chosen = tuple(j for j in judges.split(',') if j)
    unprobed = [j for j in chosen if j not in MATCHED]
    if matched and unprobed:
        raise typer.BadParameter(f'--matched has no probed regime for {unprobed}; add them to MATCHED first')
    out.mkdir(parents=True, exist_ok=True)
    asyncio.run(run(reps, path, out, send=send, matched=matched, judges=chosen))


if __name__ == '__main__':
    typer.run(main)
