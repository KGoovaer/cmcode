"""Core LLM interaction logic for cmcode."""

import os
from pathlib import Path
from typing import Callable, Generator, Any

from openai import OpenAI

from .config import Config
from .tools import TOOLS, ToolExecutor


class ChatSession:
    """Manages a chat session with the LLM."""
    
    def __init__(
        self,
        config: Config,
        tool_executor: ToolExecutor | None = None,
        on_tool_call: Callable[[str, str], None] | None = None,
    ):
        """
        Initialize a chat session.
        
        Args:
            config: Configuration object
            tool_executor: Tool executor instance (creates default if None)
            on_tool_call: Callback when a tool is called (tool_name, arguments)
        """
        self.config = config
        self.tool_executor = tool_executor or ToolExecutor(
            workspace_dir=config.workspace_dir,
            auto_confirm=config.auto_confirm
        )
        self.on_tool_call = on_tool_call
        
        self.client = OpenAI(
            base_url=config.endpoint,
            api_key=config.api_key
        )
        
        self.conversation: list[dict[str, Any]] = []
        
        # Load system prompt
        system_prompt = self._load_system_prompt()
        if system_prompt:
            self.conversation.append({"role": "system", "content": system_prompt})
    
    def _load_system_prompt(self) -> str | None:
        """Load the system prompt from file."""
        # Try explicit path from config
        if self.config.system_prompt_path:
            path = Path(self.config.system_prompt_path)
            if path.exists():
                return path.read_text().strip()
        
        # Try default locations
        default_paths = [
            Path(self.config.workspace_dir or ".") / "system-prompt.md",
            Path(__file__).parent.parent / "system-prompt.md",
        ]
        
        for path in default_paths:
            if path.exists():
                return path.read_text().strip()
        
        return None
    
    def _send_to_llm(self, stream: bool = False):
        """Send conversation to LLM and return response."""
        return self.client.chat.completions.create(
            model=self.config.model,
            messages=self.conversation,
            tools=TOOLS,
            stream=stream
        )
    
    def _handle_tool_calls(self, tool_calls: list) -> None:
        """Execute tool calls and add results to conversation."""
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = tool_call.function.arguments
            
            # Notify callback
            if self.on_tool_call:
                self.on_tool_call(function_name, function_args)
            
            # Execute the tool
            result = self.tool_executor.execute(function_name, function_args)
            
            # Add tool result to conversation
            self.conversation.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })
    
    def chat(self, user_input: str) -> str:
        """
        Send a message and get a complete response (non-streaming).
        
        Args:
            user_input: The user's message
            
        Returns:
            The assistant's final response
        """
        self.conversation.append({"role": "user", "content": user_input})
        
        while True:
            response = self._send_to_llm(stream=False)
            response_message = response.choices[0].message
            
            if response_message.tool_calls:
                # Add assistant's tool call message
                self.conversation.append(response_message.model_dump())
                
                # Execute tools
                self._handle_tool_calls(response_message.tool_calls)
                
                # Continue loop to get next response
            else:
                # Final response
                final_response = response_message.content or ""
                self.conversation.append({"role": "assistant", "content": final_response})
                return final_response
    
    def chat_stream(self, user_input: str) -> Generator[str, None, None]:
        """
        Send a message and stream the response.
        
        Args:
            user_input: The user's message
            
        Yields:
            Chunks of the assistant's response
        """
        self.conversation.append({"role": "user", "content": user_input})
        
        while True:
            stream = self._send_to_llm(stream=True)
            
            # Collect the streamed response
            collected_content = ""
            collected_tool_calls = []
            current_tool_call = None
            
            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                
                # Handle content
                if delta.content:
                    collected_content += delta.content
                    yield delta.content
                
                # Handle tool calls (accumulated across chunks)
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        if tc.index is not None:
                            # Extend list if needed
                            while len(collected_tool_calls) <= tc.index:
                                collected_tool_calls.append({
                                    "id": None,
                                    "function": {"name": "", "arguments": ""},
                                    "type": "function"
                                })
                            
                            current = collected_tool_calls[tc.index]
                            
                            if tc.id:
                                current["id"] = tc.id
                            if tc.function:
                                if tc.function.name:
                                    current["function"]["name"] += tc.function.name
                                if tc.function.arguments:
                                    current["function"]["arguments"] += tc.function.arguments
            
            # Check if we have tool calls to execute
            if collected_tool_calls and collected_tool_calls[0]["id"]:
                # Convert to proper tool call objects
                class ToolCall:
                    def __init__(self, data):
                        self.id = data["id"]
                        self.function = type("Function", (), {
                            "name": data["function"]["name"],
                            "arguments": data["function"]["arguments"]
                        })()
                
                tool_call_objects = [ToolCall(tc) for tc in collected_tool_calls if tc["id"]]
                
                # Add assistant message with tool calls
                self.conversation.append({
                    "role": "assistant",
                    "content": collected_content or None,
                    "tool_calls": collected_tool_calls
                })
                
                # Execute tools
                self._handle_tool_calls(tool_call_objects)
                
                # Continue loop for next response
            else:
                # Final response (no more tool calls)
                if collected_content:
                    self.conversation.append({"role": "assistant", "content": collected_content})
                return
    
    def reset(self) -> None:
        """Reset the conversation, keeping only the system prompt."""
        system_messages = [m for m in self.conversation if m.get("role") == "system"]
        self.conversation = system_messages
