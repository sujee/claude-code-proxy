import json
import math
import logging
from typing import Dict, Any, List, Tuple
from src.core.constants import Constants
from src.models.claude import ClaudeMessagesRequest, ClaudeMessage
from src.core.config import config

logger = logging.getLogger(__name__)

# Rough per-model context limits (tokens). Used to downscale max_tokens when
# prompts get close to the window. Configurable via env overrides in config.
# If no override is provided, we fall back to the safe default below.
DEFAULT_CONTEXT_LIMIT = 128000
# Bias multiplier to make the rough token estimate more conservative (actual
# provider tokenization can be larger than chars/4). Increase to trim earlier.
TOKEN_ESTIMATE_BIAS = 1.35
# Extra safety buffer beyond the reserve passed to trimming.
TOKEN_ESTIMATE_BUFFER = 512


def _get_context_limit(model_name: str) -> int:
    # Per-role overrides from config
    if model_name == config.big_model and config.big_model_context_limit:
        return config.big_model_context_limit
    if model_name == config.middle_model and config.middle_model_context_limit:
        return config.middle_model_context_limit
    if model_name == config.small_model and config.small_model_context_limit:
        return config.small_model_context_limit
    if model_name == config.vision_model and config.vision_model_context_limit:
        return config.vision_model_context_limit

    # No prefix match; use safe default
    return DEFAULT_CONTEXT_LIMIT


def _estimate_prompt_tokens(messages: List[Dict[str, Any]]) -> int:
    """Conservative token estimator: chars/4 + image bump, scaled up."""
    total_chars = 0
    image_bonus = 0
    for msg in messages:
        content = msg.get("content")
        if content is None:
            continue
        if isinstance(content, str):
            total_chars += len(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        total_chars += len(block.get("text", ""))
                    elif block.get("type") == "image_url":
                        image_bonus += 400  # conservative chunk per image
        # assistant tool calls:
        if msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                fn = tc.get("function", {})
                total_chars += len(fn.get("arguments", ""))
    rough = (total_chars // 4) + image_bonus
    return int(math.ceil(rough * TOKEN_ESTIMATE_BIAS) + TOKEN_ESTIMATE_BUFFER)


def _trim_messages_to_fit(messages: List[Dict[str, Any]], context_limit: int, reserve: int = 2048) -> Tuple[List[Dict[str, Any]], int]:
    """
    Drop oldest messages until the estimated prompt fits within context_limit - reserve.
    Returns (trimmed_messages, dropped_count).
    """
    trimmed = list(messages)
    dropped = 0
    while trimmed:
        est = _estimate_prompt_tokens(trimmed)
        if est <= max(context_limit - reserve, 1):
            break
        # Prefer to drop the oldest non-system message first; if first is system and list has more, drop second.
        drop_idx = 0 if len(trimmed) == 1 else (0 if trimmed[0].get("role") != Constants.ROLE_SYSTEM else 1)
        trimmed.pop(drop_idx if drop_idx < len(trimmed) else 0)
        dropped += 1
    return trimmed, dropped


def convert_claude_to_openai(
    claude_request: ClaudeMessagesRequest, model_manager
) -> Dict[str, Any]:
    """Convert Claude API request format to OpenAI format."""
    allow_tools = not config.disable_tools
    # Only treat the latest user message as image-bearing for routing/tool decisions
    has_image = bool(model_manager and model_manager.contains_image_content(
        claude_request.messages, latest_user_only=True
    ))

    # Map model
    openai_model = model_manager.map_claude_model_to_openai(claude_request.model, claude_request.messages)
    logger.info(f"Selected model: {openai_model} for request with {len(claude_request.messages)} messages")

    # Convert messages
    openai_messages = []

    # Special handling for image requests: to avoid blowing the smaller vision
    # model's context window, send only the latest user turn that carries the
    # image (plus an optional short system prompt when allowed). The rest of the
    # conversation stays on the Claude side and resumes with the text model.
    if has_image:
        # Optional system message (only when we are not stripping image context)
        if claude_request.system and not config.strip_image_context:
            system_text = ""
            if isinstance(claude_request.system, str):
                system_text = claude_request.system
            elif isinstance(claude_request.system, list):
                text_parts = []
                for block in claude_request.system:
                    if hasattr(block, "type") and block.type == Constants.CONTENT_TEXT:
                        text_parts.append(block.text)
                    elif (
                        isinstance(block, dict)
                        and block.get("type") == Constants.CONTENT_TEXT
                    ):
                        text_parts.append(block.get("text", ""))
                system_text = "\n\n".join(text_parts)

            if system_text.strip():
                openai_messages.append(
                    {"role": Constants.ROLE_SYSTEM, "content": system_text.strip()}
                )

        # Find the most recent user message that contains an image and only send that
        latest_image_msg = None
        for message in reversed(claude_request.messages):
            if message.role == Constants.ROLE_USER and model_manager.contains_image_content([message]):
                latest_image_msg = message
                break

        if latest_image_msg:
            openai_messages.append(
                convert_claude_user_message(latest_image_msg, allow_images=True)
            )
    else:
        # Original multi-turn handling for text-only flow
        # Add system message if present
        if claude_request.system:
            system_text = ""
            if isinstance(claude_request.system, str):
                system_text = claude_request.system
            elif isinstance(claude_request.system, list):
                text_parts = []
                for block in claude_request.system:
                    if hasattr(block, "type") and block.type == Constants.CONTENT_TEXT:
                        text_parts.append(block.text)
                    elif (
                        isinstance(block, dict)
                        and block.get("type") == Constants.CONTENT_TEXT
                    ):
                        text_parts.append(block.get("text", ""))
                system_text = "\n\n".join(text_parts)

            if system_text.strip():
                openai_messages.append(
                    {"role": Constants.ROLE_SYSTEM, "content": system_text.strip()}
                )

        # Process Claude messages
        i = 0
        while i < len(claude_request.messages):
            msg = claude_request.messages[i]

            if msg.role == Constants.ROLE_USER:
                openai_message = convert_claude_user_message(msg, allow_images=has_image)
                openai_messages.append(openai_message)
            elif msg.role == Constants.ROLE_ASSISTANT:
                openai_message = convert_claude_assistant_message(msg, allow_tools=allow_tools)
                openai_messages.append(openai_message)

                # Check if next message contains tool results
                if allow_tools and i + 1 < len(claude_request.messages):
                    next_msg = claude_request.messages[i + 1]
                    if (
                        next_msg.role == Constants.ROLE_USER
                        and isinstance(next_msg.content, list)
                        and any(
                            block.type == Constants.CONTENT_TOOL_RESULT
                            for block in next_msg.content
                            if hasattr(block, "type")
                        )
                    ):
                        # Process tool results
                        i += 1  # Skip to tool result message
                        tool_results = convert_claude_tool_results(next_msg)
                        openai_messages.extend(tool_results)

            i += 1

    # Build OpenAI request
    # Context trimming + max_tokens guard
    context_limit = _get_context_limit(openai_model)
    openai_messages, dropped = _trim_messages_to_fit(openai_messages, context_limit, reserve=2048)
    if dropped:
        logger.warning(f"Trimmed {dropped} oldest messages to fit context window for model {openai_model}")

    prompt_estimate = _estimate_prompt_tokens(openai_messages)
    available = max(context_limit - prompt_estimate - 2048, 1)
    # Respect client intent; treat MIN_TOKENS_LIMIT as a fallback for missing/invalid
    # values instead of forcing an oversized floor.
    requested = claude_request.max_tokens
    if not isinstance(requested, int) or requested < 1:
        requested = config.min_tokens_limit

    safe_max_tokens = min(requested, config.max_tokens_limit, available)

    openai_request = {
        "model": openai_model,
        "messages": openai_messages,
        "max_tokens": safe_max_tokens,
        "temperature": claude_request.temperature,
        "stream": claude_request.stream,
    }
    logger.debug(
        f"Converted Claude request to OpenAI format: {json.dumps(openai_request, indent=2, ensure_ascii=False)}"
    )
    # Add optional parameters
    if claude_request.stop_sequences:
        openai_request["stop"] = claude_request.stop_sequences
    if claude_request.top_p is not None:
        openai_request["top_p"] = claude_request.top_p

    # Convert tools
    if allow_tools and claude_request.tools:
        openai_tools = []
        for tool in claude_request.tools:
            if tool.name and tool.name.strip():
                openai_tools.append(
                    {
                        "type": Constants.TOOL_FUNCTION,
                        Constants.TOOL_FUNCTION: {
                            "name": tool.name,
                            "description": tool.description or "",
                            "parameters": tool.input_schema,
                        },
                    }
                )
        if openai_tools:
            openai_request["tools"] = openai_tools

    # Convert tool choice only when tools are present
    if allow_tools and claude_request.tool_choice and openai_request.get("tools"):
        choice_type = claude_request.tool_choice.get("type")
        if choice_type == "auto":
            openai_request["tool_choice"] = "auto"
        elif choice_type == "any":
            openai_request["tool_choice"] = "auto"
        elif choice_type == "tool" and "name" in claude_request.tool_choice:
            openai_request["tool_choice"] = {
                "type": Constants.TOOL_FUNCTION,
                Constants.TOOL_FUNCTION: {"name": claude_request.tool_choice["name"]},
            }
        else:
            openai_request["tool_choice"] = "auto"

    # Vision endpoints commonly reject tool use; force no tools for image requests
    if has_image:
        openai_request.pop("tools", None)
        openai_request["tool_choice"] = "none"

    return openai_request


def convert_claude_user_message(msg: ClaudeMessage, *, allow_images: bool) -> Dict[str, Any]:
    """Convert Claude user message to OpenAI format."""
    if msg.content is None:
        return {"role": Constants.ROLE_USER, "content": ""}
    
    if isinstance(msg.content, str):
        return {"role": Constants.ROLE_USER, "content": msg.content}

    # Handle multimodal content
    openai_content = []
    text_blocks = []
    image_blocks = []
    has_image = False
    for block in msg.content:
        # Normalize block access
        if isinstance(block, dict):
            block_type = block.get("type")
        else:
            block_type = getattr(block, "type", None)

        # Text blocks
        if block_type == Constants.CONTENT_TEXT:
            text_value = (
                block.get("text")
                if isinstance(block, dict)
                else getattr(block, "text", "")
            )
            text_blocks.append(text_value or "")

        # Base64 image blocks (Claude style)
        elif block_type == Constants.CONTENT_IMAGE and allow_images:
            source = block.get("source") if isinstance(block, dict) else getattr(block, "source", {})
            if (
                isinstance(source, dict)
                and source.get("type") == "base64"
                and "media_type" in source
                and "data" in source
            ):
                has_image = True
                image_blocks.append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{source['media_type']};base64,{source['data']}"
                        },
                    }
                )

        # Pre-encoded image_url blocks (OpenAI style) - pass through
        elif block_type == "image_url" and allow_images:
            image_url_payload = (
                block.get("image_url")
                if isinstance(block, dict)
                else getattr(block, "image_url", None)
            )
            if image_url_payload:
                has_image = True
                image_blocks.append({"type": "image_url", "image_url": image_url_payload})

    # Always strip/trim when an image is present to protect the vision model context,
    # regardless of the STRIP_IMAGE_CONTEXT flag. This keeps image hops lightweight.
    if has_image:
        text_to_keep = ""
        for text in reversed(text_blocks):
            stripped = text.strip()
            if not stripped:
                continue
            if stripped.startswith("<system-reminder>"):
                continue
            if stripped.lower().startswith("[image:"):
                continue
            text_to_keep = text
            break

        MAX_VISION_TEXT_CHARS = 1500
        if text_to_keep and len(text_to_keep) > MAX_VISION_TEXT_CHARS:
            text_to_keep = text_to_keep[-MAX_VISION_TEXT_CHARS:]

        if text_to_keep:
            openai_content = [{"type": "text", "text": text_to_keep}] + image_blocks
        else:
            openai_content = image_blocks
    else:
        for text in text_blocks:
            openai_content.append({"type": "text", "text": text})
        openai_content.extend(image_blocks)

    if len(openai_content) == 1 and openai_content[0]["type"] == "text":
        return {"role": Constants.ROLE_USER, "content": openai_content[0]["text"]}
    else:
        return {"role": Constants.ROLE_USER, "content": openai_content}


def convert_claude_assistant_message(
    msg: ClaudeMessage, *, allow_tools: bool
) -> Dict[str, Any]:
    """Convert Claude assistant message to OpenAI format."""
    text_parts = []
    tool_calls = []

    if msg.content is None:
        return {"role": Constants.ROLE_ASSISTANT, "content": None}
    
    if isinstance(msg.content, str):
        return {"role": Constants.ROLE_ASSISTANT, "content": msg.content}

    for block in msg.content:
        if block.type == Constants.CONTENT_TEXT:
            text_parts.append(block.text)
        elif allow_tools and block.type == Constants.CONTENT_TOOL_USE:
            tool_calls.append(
                {
                    "id": block.id,
                    "type": Constants.TOOL_FUNCTION,
                    Constants.TOOL_FUNCTION: {
                        "name": block.name,
                        "arguments": json.dumps(block.input, ensure_ascii=False),
                    },
                }
            )

    openai_message = {"role": Constants.ROLE_ASSISTANT}

    # Set content
    if text_parts:
        openai_message["content"] = "".join(text_parts)
    else:
        openai_message["content"] = None

    # Set tool calls
    if tool_calls:
        openai_message["tool_calls"] = tool_calls

    return openai_message


def convert_claude_tool_results(msg: ClaudeMessage) -> List[Dict[str, Any]]:
    """Convert Claude tool results to OpenAI format."""
    tool_messages = []

    if isinstance(msg.content, list):
        for block in msg.content:
            if block.type == Constants.CONTENT_TOOL_RESULT:
                content = parse_tool_result_content(block.content)
                tool_messages.append(
                    {
                        "role": Constants.ROLE_TOOL,
                        "tool_call_id": block.tool_use_id,
                        "content": content,
                    }
                )

    return tool_messages


def parse_tool_result_content(content):
    """Parse and normalize tool result content into a string format."""
    if content is None:
        return "No content provided"

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        result_parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == Constants.CONTENT_TEXT:
                result_parts.append(item.get("text", ""))
            elif isinstance(item, str):
                result_parts.append(item)
            elif isinstance(item, dict):
                if "text" in item:
                    result_parts.append(item.get("text", ""))
                else:
                    try:
                        result_parts.append(json.dumps(item, ensure_ascii=False))
                    except:
                        result_parts.append(str(item))
        return "\n".join(result_parts).strip()

    if isinstance(content, dict):
        if content.get("type") == Constants.CONTENT_TEXT:
            return content.get("text", "")
        try:
            return json.dumps(content, ensure_ascii=False)
        except:
            return str(content)

    try:
        return str(content)
    except:
        return "Unparseable content"
