import json

import pytest

from src.conversion.response_converter import (
    convert_openai_streaming_to_claude_with_cancellation,
)
from src.models.claude import ClaudeMessage, ClaudeMessagesRequest


class _DummyRequest:
    async def is_disconnected(self):
        return False


class _DummyClient:
    def cancel_request(self, _request_id):
        return True


class _DummyLogger:
    def info(self, *_args, **_kwargs):
        pass

    def warning(self, *_args, **_kwargs):
        pass

    def error(self, *_args, **_kwargs):
        pass


async def _fake_stream():
    # Regular text delta
    yield 'data: ' + json.dumps(
        {"choices": [{"delta": {"content": "A"}, "finish_reason": None}]}
    )
    # Completion marker chunk
    yield 'data: ' + json.dumps({"choices": [{"delta": {}, "finish_reason": "stop"}]})
    # Unexpected chunk after finish_reason that should be ignored
    yield 'data: ' + json.dumps(
        {"choices": [{"delta": {"content": "B"}, "finish_reason": None}]}
    )
    yield "data: [DONE]"


@pytest.mark.asyncio
async def test_streaming_stops_after_finish_reason():
    request = ClaudeMessagesRequest(
        model="claude-3-5-sonnet-20241022",
        max_tokens=64,
        messages=[ClaudeMessage(role="user", content="hello")],
        stream=True,
    )

    events = []
    async for event in convert_openai_streaming_to_claude_with_cancellation(
        _fake_stream(),
        request,
        _DummyLogger(),
        _DummyRequest(),
        _DummyClient(),
        "req_1",
    ):
        events.append(event)

    serialized = "".join(events)
    assert '"text": "A"' in serialized
    assert '"text": "B"' not in serialized
    assert "event: message_stop" in serialized
