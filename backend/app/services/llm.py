from __future__ import annotations
import json

import instructor
from openai import AsyncOpenAI

from app.config import get_llm_api_key, get_llm_base_url, get_llm_model


def create_client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=get_llm_api_key(), base_url=get_llm_base_url())


def create_instructor_client() -> instructor.AsyncInstructor:
    client = create_client()
    return instructor.from_openai(client, mode=instructor.Mode.JSON)


llm_client = create_client()
instructor_client = create_instructor_client()


def reset_clients():
    global llm_client, instructor_client
    llm_client = create_client()
    instructor_client = create_instructor_client()


async def chat_completion(
    messages: list[dict],
    tools: list[dict] | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> dict:
    kwargs = dict(
        model=get_llm_model(),
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    response = await llm_client.chat.completions.create(**kwargs)
    content = response.choices[0].message.content if response.choices else None
    finish = response.choices[0].finish_reason if response.choices else None
    msg = response.choices[0].message if response.choices else None
    print(f"[LLM] model={get_llm_model()} base_url={get_llm_base_url()}")
    print(f"[LLM] finish_reason={finish} content_len={len(content) if content else 'None'} preview={repr(content[:200]) if content else 'EMPTY'}")
    print(f"[LLM] full message: role={msg.role if msg else None} content_null={msg.content is None if msg else 'N/A'} tool_calls={msg.tool_calls if msg else 'N/A'}")
    return response


async def chat_completion_stream(
    messages: list[dict],
    tools: list[dict] | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
):
    kwargs = dict(
        model=get_llm_model(),
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    stream = await llm_client.chat.completions.create(**kwargs)
    total = 0
    async for chunk in stream:
        total += 1
        yield chunk
    print(f"[LLM STREAM] model={get_llm_model()} total_chunks={total}")


async def structured_completion(
    messages: list[dict],
    response_model: type,
    temperature: float = 0.3,
    max_tokens: int = 4096,
):
    try:
        result = await instructor_client.chat.completions.create(
            model=get_llm_model(),
            messages=messages,
            response_model=response_model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return result
    except Exception as e:
        print(f"[LLM] instructor failed: {type(e).__name__}: {e}")
        # Log the response_model schema
        try:
            print(f"[LLM] response_model schema: {response_model.model_json_schema()}")
        except Exception:
            pass
        try:
            response = await llm_client.chat.completions.create(
                model=get_llm_model(),
                messages=messages
                + [
                    {
                        "role": "system",
                        "content": "You must respond with valid JSON only, no markdown.",
                    }
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            text = response.choices[0].message.content or ""
            finish = response.choices[0].finish_reason if response.choices else "N/A"
            print(f"[LLM] fallback raw result: finish_reason={finish} content_len={len(text)} preview={repr(text[:300])}")
            text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            if not text:
                raise ValueError(f"Both instructor and raw chat_completion returned empty content. Instructor error: {type(e).__name__}: {e}")
            return response_model(**json.loads(text))
        except Exception as e2:
            print(f"[LLM] fallback also failed: {type(e2).__name__}: {e2}")
            raise
