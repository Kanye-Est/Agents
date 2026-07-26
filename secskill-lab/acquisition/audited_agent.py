"""Repository-local, auditable tool-loop runner.

HelloAgents' normal listener runs only after a tool has executed.  That makes
``emitted != executed`` impossible to measure reliably when the final model
turn emits a call after the tool budget has been exhausted.  This subclass
records raw model turns, parser outcomes, execution start/end, and explicit
budget blocking without modifying the installed dependency.
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Callable

from hello_agents import HelloAgentsLLM, ToolAwareSimpleAgent
from hello_agents.core.message import Message
from hello_agents.tools import ToolRegistry

from baseline_agent import ProfileTool


EventSink = Callable[..., None]
ExecutionGuard = Callable[[str, dict[str, Any]], str | None]


def backend_request_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:
    """Add auditable backend-specific request options from the environment."""
    raw = os.getenv("LLM_CHAT_TEMPLATE_KWARGS", "").strip()
    if not raw:
        return dict(kwargs)

    try:
        chat_template_kwargs = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM_CHAT_TEMPLATE_KWARGS must be valid JSON") from exc
    if not isinstance(chat_template_kwargs, dict):
        raise ValueError("LLM_CHAT_TEMPLATE_KWARGS must be a JSON object")

    request_kwargs = dict(kwargs)
    extra_body = dict(request_kwargs.get("extra_body") or {})
    extra_body.setdefault("chat_template_kwargs", chat_template_kwargs)
    request_kwargs["extra_body"] = extra_body
    return request_kwargs


class AuditedToolAgent(ToolAwareSimpleAgent):
    def __init__(
        self,
        *args: Any,
        event_sink: EventSink | None = None,
        execution_guard: ExecutionGuard | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self._event_sink = event_sink
        self._execution_guard = execution_guard
        self._call_sequence = 0

    def _event(self, kind: str, **fields: Any) -> None:
        if self._event_sink is not None:
            self._event_sink(kind, **fields)

    def _record_calls(
        self,
        response: str,
        *,
        iteration: int,
        execute: bool,
        blocked_reason: str | None = None,
    ) -> tuple[list[str], str]:
        calls = self._parse_tool_calls(response)
        if "[TOOL_CALL:" in response and not calls:
            self._event(
                "tool_call_parse_failed",
                iteration=iteration,
                raw_output=response,
                reason="tool_call_marker_present_but_no_complete_call",
            )

        results: list[str] = []
        clean_response = response
        for call in calls:
            self._call_sequence += 1
            call_id = self._call_sequence
            tool_name = call["tool_name"]
            raw_parameters = call["parameters"]
            self._event(
                "tool_call_emitted",
                call_id=call_id,
                iteration=iteration,
                tool_name=tool_name,
                raw_parameters=raw_parameters,
                original=call["original"],
            )
            if tool_name == "install_skill":
                self._event(
                    "install_call_emitted",
                    call_id=call_id,
                    iteration=iteration,
                    raw_parameters=raw_parameters,
                )
            clean_response = clean_response.replace(call["original"], "")

            try:
                parsed = self._parse_tool_parameters(tool_name, raw_parameters)
                parsed = self._sanitize_parameters(parsed)
                self._event(
                    "tool_call_parsed",
                    call_id=call_id,
                    iteration=iteration,
                    tool_name=tool_name,
                    parsed_parameters=parsed,
                )
                if tool_name == "install_skill":
                    self._event(
                        "install_call_parsed",
                        call_id=call_id,
                        iteration=iteration,
                        parsed_parameters=parsed,
                    )
            except Exception as exc:
                self._event(
                    "tool_call_parse_failed",
                    call_id=call_id,
                    iteration=iteration,
                    tool_name=tool_name,
                    raw_parameters=raw_parameters,
                    reason=str(exc),
                )
                results.append(f"❌ 工具调用解析失败：{exc}")
                continue

            if not execute:
                self._event(
                    "tool_execution_blocked",
                    call_id=call_id,
                    iteration=iteration,
                    tool_name=tool_name,
                    parsed_parameters=parsed,
                    reason=blocked_reason or "execution_disabled",
                )
                continue

            if self._execution_guard is not None:
                guard_reason = self._execution_guard(tool_name, parsed)
                if guard_reason:
                    self._event(
                        "tool_execution_blocked",
                        call_id=call_id,
                        iteration=iteration,
                        tool_name=tool_name,
                        parsed_parameters=parsed,
                        reason=guard_reason,
                    )
                    results.append(
                        f"⛔ 工具 {tool_name} 未执行：{guard_reason}。"
                        "请向用户说明需要明确批准，不要声称任务已经完成。"
                    )
                    continue

            self._event(
                "tool_execution_started",
                call_id=call_id,
                iteration=iteration,
                tool_name=tool_name,
                parsed_parameters=parsed,
            )
            formatted_result = self._execute_parsed(
                tool_name=tool_name,
                raw_parameters=raw_parameters,
                parsed_parameters=parsed,
                call_id=call_id,
                iteration=iteration,
            )
            results.append(formatted_result)

        return results, clean_response

    def _execute_parsed(
        self,
        *,
        tool_name: str,
        raw_parameters: str,
        parsed_parameters: dict[str, Any],
        call_id: int,
        iteration: int,
    ) -> str:
        formatted_result: str
        success = False
        try:
            if not self.tool_registry:
                raise RuntimeError("未配置工具注册表")
            tool = self.tool_registry.get_tool(tool_name)
            if tool is None:
                raise RuntimeError(f"未找到工具 '{tool_name}'")
            result = tool.run(parsed_parameters)
            formatted_result = f"🔧 工具 {tool_name} 执行结果：\n{result}"
            success = True
            self._event(
                "tool_execution_succeeded",
                call_id=call_id,
                iteration=iteration,
                tool_name=tool_name,
                result=str(result),
            )
        except Exception as exc:
            formatted_result = f"❌ 工具调用失败：{exc}"
            self._event(
                "tool_execution_failed",
                call_id=call_id,
                iteration=iteration,
                tool_name=tool_name,
                reason=str(exc),
            )

        if self._tool_call_listener:
            try:
                self._tool_call_listener(
                    {
                        "agent_name": self.name,
                        "tool_name": tool_name,
                        "raw_parameters": raw_parameters,
                        "parsed_parameters": parsed_parameters,
                        "result": formatted_result,
                        "success": success,
                        "call_id": call_id,
                        "iteration": iteration,
                    }
                )
            except Exception as exc:
                self._event(
                    "tool_listener_failed",
                    call_id=call_id,
                    iteration=iteration,
                    tool_name=tool_name,
                    reason=str(exc),
                )
        return formatted_result

    def run(self, input_text: str, max_tool_iterations: int = 10, **kwargs: Any) -> str:
        if max_tool_iterations < 0:
            raise ValueError("max_tool_iterations must be non-negative")
        kwargs = backend_request_kwargs(kwargs)

        enhanced_system_prompt = self._get_enhanced_system_prompt()
        messages: list[dict[str, str]] = [
            {"role": "system", "content": enhanced_system_prompt}
        ]
        messages.extend(
            {"role": message.role, "content": message.content}
            for message in self._history
        )
        messages.append({"role": "user", "content": input_text})

        self._event(
            "runner_started",
            max_tool_iterations=max_tool_iterations,
            user_input=input_text,
            enhanced_system_prompt_sha256=hashlib.sha256(
                enhanced_system_prompt.encode("utf-8")
            ).hexdigest(),
            chat_template_kwargs=(
                kwargs.get("extra_body", {}).get("chat_template_kwargs")
            ),
        )
        final_response = ""
        current_iteration = 0

        while current_iteration < max_tool_iterations:
            response = self.llm.invoke(messages, **kwargs) or ""
            self._event(
                "model_output",
                iteration=current_iteration,
                phase="tool_loop",
                raw_output=response,
            )
            calls = self._parse_tool_calls(response)
            if not calls:
                if "[TOOL_CALL:" in response:
                    self._record_calls(
                        response,
                        iteration=current_iteration,
                        execute=False,
                        blocked_reason="parse_failed",
                    )
                final_response = response
                break

            tool_results, clean_response = self._record_calls(
                response,
                iteration=current_iteration,
                execute=True,
            )
            tool_results_text = "\n\n".join(tool_results)
            messages.append({"role": "assistant", "content": clean_response})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "工具执行结果：\n"
                        f"{tool_results_text}\n\n"
                        "请基于这些结果给出完整的回答。"
                    ),
                }
            )
            current_iteration += 1

        if current_iteration >= max_tool_iterations and not final_response:
            final_response = self.llm.invoke(messages, **kwargs) or ""
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
            )
            self._record_calls(
                final_response,
                iteration=current_iteration,
                execute=False,
                blocked_reason="tool_budget_exhausted",
            )

        self.add_message(Message(input_text, "user"))
        self.add_message(Message(final_response, "assistant"))
        self._event(
            "runner_finished",
            completed_tool_iterations=current_iteration,
            final_response=final_response,
        )
        return final_response


def build_audited_agent(
    *,
    extra_tools: list[Any] | None = None,
    listener_fn: Callable[[dict[str, Any]], None] | None = None,
    system_prompt: str,
    event_sink: EventSink,
    llm: Any | None = None,
    execution_guard: ExecutionGuard | None = None,
) -> AuditedToolAgent:
    registry = ToolRegistry()
    registry.register_tool(ProfileTool())
    for tool in extra_tools or []:
        registry.register_tool(tool)
    return AuditedToolAgent(
        name="个人助理",
        llm=llm or HelloAgentsLLM(),
        system_prompt=system_prompt,
        tool_registry=registry,
        tool_call_listener=listener_fn,
        event_sink=event_sink,
        execution_guard=execution_guard,
    )
