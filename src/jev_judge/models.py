"""Judge adapters. Only one ships here: Jev through the Orq Classify endpoint.

An adapter exposes `name`, `local` and

    predict(state, questions) -> {qid: {"probs", "pred", "latency_ms", "cost", "truncated"}}

`probs` keys are "true"/"false" (noul) or level index strings (score); `pred` is the argmax key.
One `predict` call is one request. `latency_ms` is that request's full wall time, repeated on every
question row; `cost` is the request cost split evenly over its questions, so summing a row's questions
gives the row's true cost.

Authentication is the `ORQ_API_KEY` environment variable and nothing else.
"""

from __future__ import annotations

import os
import time

import httpx
from loguru import logger
from tenacity import RetryCallState, retry, retry_if_exception, stop_after_attempt, wait_exponential

JEV_URL = 'https://my.orq.ai/v3/router/classify'
JEV_MODEL = 'typesafe/jev-latest'
JEV_INPUT_PRICE = 0.042 / 1e6  # USD per input token; matches the endpoint's own input_cost


def api_key() -> str:
    """The Orq API key, from the environment."""
    try:
        return os.environ['ORQ_API_KEY']
    except KeyError:
        raise RuntimeError('ORQ_API_KEY is not set; export it before running anything that calls Orq') from None


def argmax(probs: dict[str, float]) -> str:
    return max(probs, key=lambda k: probs[k])


def probs_from_answer(a: dict) -> dict[str, float]:
    """Classify response shape: p(true) only for noul, a probabilities dict otherwise."""
    if a['type'] == 'noul':
        return {'true': a['noul'], 'false': 1.0 - a['noul']}
    return dict(a['probabilities'])


def _transient(exc: BaseException) -> bool:
    """HTTP 429/5xx and transport failures; a 4xx is the request's fault and is not retried."""
    status = getattr(exc, 'status_code', None) or getattr(getattr(exc, 'response', None), 'status_code', None)
    if status is not None:
        return status == 429 or status >= 500
    return isinstance(exc, httpx.TransportError)


def _warn_retry(state: RetryCallState) -> None:
    logger.warning(f'⚠ {state.fn.__qualname__} attempt {state.attempt_number} failed: {state.outcome.exception()!r}')


remote_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception(_transient),
    before_sleep=_warn_retry,
    reraise=True,
)


class JevAdapter:
    """Orq Classify (`typesafe/jev-latest`) over HTTP: every question of a case in one call."""

    name = 'jev'
    local = False

    def __init__(self) -> None:
        self._client = httpx.Client(timeout=60.0, headers={'Authorization': f'Bearer {api_key()}'})

    @remote_retry
    def _post(self, body: dict) -> dict:
        r = self._client.post(JEV_URL, json=body)
        r.raise_for_status()
        return r.json()

    def predict(self, state: str, questions: dict[str, dict]) -> dict[str, dict]:
        t0 = time.perf_counter()
        data = self._post({'model': JEV_MODEL, 'state': state, 'questions': questions})
        latency = (time.perf_counter() - t0) * 1000
        cost = data['usage']['input_tokens'] * JEV_INPUT_PRICE / len(questions)
        out = {}
        for qid in questions:
            probs = probs_from_answer(data['answers'][qid])
            out[qid] = {
                'probs': probs,
                'pred': argmax(probs),
                'latency_ms': latency,
                'cost': cost,
                'truncated': False,
            }
        return out


def get_adapter(name: str) -> JevAdapter:
    """Build the adapter called `name`."""
    if name == 'jev':
        return JevAdapter()
    raise ValueError(f'unknown model {name!r}')
