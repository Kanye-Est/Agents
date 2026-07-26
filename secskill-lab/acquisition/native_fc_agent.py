"""Audited OpenAI-style native function-calling agent loop.

This runner mirrors :mod:`acquisition.audited_agent`'s event contract while
replacing the repository's textual ``[TOOL_CALL:...]`` protocol with the
OpenAI-compatible ``tools`` and ``tool_calls`` fields.  Acquisition metrics and
the execution-layer approval gate therefore remain unchanged across scaffolds.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable

from hello_agents import HelloAgentsLLM
from hello_agents.tools import Tool, ToolRegistry

from baseline_agent import ProfileTool

from acquisition.audited_agent import backend_request_kwargs


EventSink = Callable[..., None]
ExecutionGuard = Callable[[str, dict[str, Any]], str | None]

_JSON_TYPES = {
    "str": "string",
    "string": "string",
    "int": "integer",
    "integer": "integer",
    "float": "number",
    "number": "number",
    "bool": "boolean",
    "boolean": "boolean",
    "array": "array",
    "list": "array",
    "object": "object",
    "dict": "object",
}


def tool_to_openai_schema(tool: Tool) -> dict[str, Any]:
    """Convert a HelloAgents ``Tool`` into one strict function schema."""
    properties: dict[str, Any] = {}
    required: list[str] = []
    for parameter in tool.get_parameters() or []:
        json_type = _JSON_TYPES.get(str(parameter.type).lower(), "string")
        schema: dict[str, Any] = {
            "type": json_type,
            "description": parameter.description or "",
        }
        if parameter.default is not None:
            schema["default"] = parameter.default
        properties[parameter.name] = schema
        if parameter.required:
            required.append(parameter.name)

    parameters: dict[str, Any] = {
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }
    if required:
        parameters["required"] = required
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": parameters,
            "strict": True,
        },
    }


class NativeFCAuditedAgent:
    """Minimal native-function-calling loop with the frozen audit events."""

    def __init__(
        self,
        *,
        name: str,
        llm: HelloAgentsLLM,
        system_prompt: str,
        tool_registry: ToolRegistry,
        tool_call_listener: Callable[[dict[str, Any]], None] | None = None,
        event_sink: EventSink | None = None,
        execution_guard: ExecutionGuard | None = None,
    ):
        self.name = name
        self.llm = llm
        self.system_prompt = system_prompt
        self.tool_registry = tool_registry
        self._tool_call_listener = tool_call_listener
        self._event_sink = event_sink
        self._execution_guard = execution_guard
        self._call_sequence = 0
        self._history: list[dict[str, Any]] = []

    def _event(self, kind: str, **fields: Any) -> None:
        if self._event_sink is not None:
            self._event_sink(kind, **fields)

    def _tool_schemas(self) -> list[dict[str, Any]]:
        return [
            tool_to_openai_schema(tool)
            for tool in self.tool_registry.get_all_tools()
        ]

    def _invoke(
        self,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> Any:
        request_kwargs = backend_request_kwargs(kwargs)
        temperature = request_kwargs.pop("temperature", self.llm.temperature)
        max_tokens = request_kwargs.pop("max_tokens", self.llm.max_tokens)
        if max_tokens is not None:
            request_kwargs["max_tokens"] = max_tokens
        response = self.llm._client.chat.completions.create(  # noqa: SLF001
            model=self.llm.model,
            messages=messages,
            tools=self._tool_schemas(),
            tool_choice="auto",
            temperature=temperature,
            **request_kwargs,
        )
        return response.choices[0].message

    @staticmethod
    def _serialized_calls(message: Any) -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        for call in message.tool_calls or []:
            output.append(
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.function.name,
                        "arguments": call.function.arguments,
                    },
                }
            )
        return output

    def _execute_call(
        self,
        call: Any,
        *,
        iteration: int,
        execute: bool,
        blocked_reason: str | None = None,
    ) -> str:
        self._call_sequence += 1
        event_call_id = self._call_sequence
        tool_name = str(call.function.name)
        raw_parameters = str(call.function.arguments or "{}")
        self._event(
            "tool_call_emitted",
            call_id=event_call_id,
            provider_call_id=call.id,
            iteration=iteration,
            tool_name=tool_name,
            raw_parameters=raw_parameters,
            original={
                "id": call.id,
                "type": "function",
                "function": {
                    "name": tool_name,
                    "arguments": raw_parameters,
                },
            },
        )
        if tool_name == "install_skill":
            self._event(
                "install_call_emitted",
                call_id=event_call_id,
                provider_call_id=call.id,
                iteration=iteration,
                raw_parameters=raw_parameters,
            )

        try:
            parsed = json.loads(raw_parameters)
            if not isinstance(parsed, dict):
                raise ValueError("native function arguments must be a JSON object")
            self._event(
                "tool_call_parsed",
                call_id=event_call_id,
                provider_call_id=call.id,
                iteration=iteration,
                tool_name=tool_name,
                parsed_parameters=parsed,
            )
            if tool_name == "install_skill":
                self._event(
                    "install_call_parsed",
                    call_id=event_call_id,
                    provider_call_id=call.id,
                    iteration=iteration,
                    parsed_parameters=parsed,
                )
        except Exception as exc:
            self._event(
                "tool_call_parse_failed",
                call_id=event_call_id,
                provider_call_id=call.id,
                iteration=iteration,
                tool_name=tool_name,
                raw_parameters=raw_parameters,
                reason=str(exc),
            )
            return f"Tool call argument parsing failed: {exc}"

        if not execute:
            self._event(
                "tool_execution_blocked",
                call_id=event_call_id,
                provider_call_id=call.id,
                iteration=iteration,
                tool_name=tool_name,
                parsed_parameters=parsed,
                reason=blocked_reason or "execution_disabled",
            )
            return (
                f"Tool {tool_name} was not executed: "
                f"{blocked_reason or 'execution_disabled'}"
            )

        if self._execution_guard is not None:
            guard_reason = self._execution_guard(tool_name, parsed)
            if guard_reason:
                self._event(
                    "tool_execution_blocked",
                    call_id=event_call_id,
                    provider_call_id=call.id,
                    iteration=iteration,
                    tool_name=tool_name,
                    parsed_parameters=parsed,
                    reason=guard_reason,
                )
                return (
                    f"Tool {tool_name} was not executed: {guard_reason}. "
                    "Tell the user that explicit approval is required and do "
                    "not claim the task is complete."
                )

        self._event(
            "tool_execution_started",
            call_id=event_call_id,
            provider_call_id=call.id,
            iteration=iteration,
            tool_name=tool_name,
            parsed_parameters=parsed,
        )
        success = False
        try:
            tool = self.tool_registry.get_tool(tool_name)
            if tool is None:
                raise RuntimeError(f"tool not found: {tool_name}")
            result = tool.run(parsed)
            formatted_result = str(result)
            success = True
            self._event(
                "tool_execution_succeeded",
                call_id=event_call_id,
                provider_call_id=call.id,
                iteration=iteration,
                tool_name=tool_name,
                result=formatted_result,
            )
        except Exception as exc:
            formatted_result = f"Tool execution failed: {exc}"
            self._event(
                "tool_execution_failed",
                call_id=event_call_id,
                provider_call_id=call.id,
                iteration=iteration,
                tool_name=tool_name,
                reason=str(exc),
            )

        if self._tool_call_listener is not None:
            try:
                self._tool_call_listener(
                    {
                        "agent_name": self.name,
                        "tool_name": tool_name,
                        "raw_parameters": raw_parameters,
                        "parsed_parameters": parsed,
                        "result": formatted_result,
                        "success": success,
                        "call_id": event_call_id,
                        "provider_call_id": call.id,
                        "iteration": iteration,
                    }
                )
            except Exception as exc:
                self._event(
                    "tool_listener_failed",
                    call_id=event_call_id,
                    provider_call_id=call.id,
                    iteration=iteration,
                    tool_name=tool_name,
                    reason=str(exc),
                )
        return formatted_result

    def run(
        self,
        input_text: str,
        max_tool_iterations: int = 10,
        **kwargs: Any,
    ) -> str:
        if max_tool_iterations < 0:
            raise ValueError("max_tool_iterations must be non-negative")
        request_kwargs = backend_request_kwargs(kwargs)
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt},
            *self._history,
            {"role": "user", "content": input_text},
        ]
        self._event(
            "runner_started",
            max_tool_iterations=max_tool_iterations,
            user_input=input_text,
            enhanced_system_prompt_sha256=hashlib.sha256(
                self.system_prompt.encode("utf-8")
            ).hexdigest(),
            chat_template_kwargs=(
                request_kwargs.get("extra_body", {}).get(
                    "chat_template_kwargs"
                )
            ),
            scaffold="openai_native_function_calling",
        )

        final_response = ""
        current_iteration = 0
        while current_iteration < max_tool_iterations:
            message = self._invoke(messages, **kwargs)
            content = message.content or ""
            serialized_calls = self._serialized_calls(message)
            self._event(
                "model_output",
                iteration=current_iteration,
                phase="tool_loop",
                raw_output=content,
                native_tool_calls=serialized_calls,
            )
            if not serialized_calls:
                final_response = content
                break

            messages.append(
                {
                    "role": "assistant",
                    "content": content,
                    "tool_calls": serialized_calls,
                }
            )
            for call in message.tool_calls or []:
                result = self._execute_call(
                    call,
                    iteration=current_iteration,
                    execute=True,
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "name": call.function.name,
                        "content": result,
                    }
                )
            current_iteration += 1

        if current_iteration >= max_tool_iterations and not final_response:
            message = self._invoke(messages, **kwargs)
            final_response = message.content or ""
            serialized_calls = self._serialized_calls(message)
            self._event(
                "tool_budget_exhausted",
                max_tool_iterations=max_tool_iterations,
                completed_tool_iterations=current_iteration,
            )
            self._event(
                "model_output",
                iteration=current_iteration,
                phase="budget_fallback",
                raw_output=final_response,
                native_tool_calls=serialized_calls,
            )
            for call in message.tool_calls or []:
                self._execute_call(
                    call,
                    iteration=current_iteration,
                    execute=False,
                    blocked_reason="tool_budget_exhausted",
                )

        self._history.extend(
            [
                {"role": "user", "content": input_text},
                {"role": "assistant", "content": final_response},
            ]
        )
        self._event(
            "runner_finished",
            completed_tool_iterations=current_iteration,
            final_response=final_response,
        )
        return final_response


def build_native_fc_agent(
    *,
    extra_tools: list[Any] | None = None,
    listener_fn: Callable[[dict[str, Any]], None] | None = None,
    system_prompt: str,
    event_sink: EventSink,
    llm: HelloAgentsLLM | None = None,
    execution_guard: ExecutionGuard | None = None,
) -> NativeFCAuditedAgent:
    registry = ToolRegistry()
    registry.register_tool(ProfileTool())
    for tool in extra_tools or []:
        registry.register_tool(tool)
    return NativeFCAuditedAgent(
        name="个人助理",
        llm=llm or HelloAgentsLLM(),
        system_prompt=system_prompt,
        tool_registry=registry,
        tool_call_listener=listener_fn,
        event_sink=event_sink,
        execution_guard=execution_guard,
    )
