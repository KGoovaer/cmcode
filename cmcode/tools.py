"""Tool definitions and execution for cmcode."""

import json
import os
import subprocess
from typing import Any

# Tool definitions for OpenAI API
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_secret",
            "description": "Gets the magical secret value"
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Reads the contents of a file and returns it as a string",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path to the file to read"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Writes content to a file. Creates the file if it doesn't exist, overwrites if it does.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path where the file should be written"
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write to the file"
                    }
                },
                "required": ["file_path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_bash",
            "description": "Executes a bash command and returns the output. Use this to run scripts, check files, execute programs, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The bash command to execute"
                    }
                },
                "required": ["command"]
            }
        }
    }
]


class ToolExecutor:
    """Executes tools with configurable settings."""
    
    def __init__(self, workspace_dir: str | None = None, auto_confirm: bool = False):
        """
        Initialize the tool executor.
        
        Args:
            workspace_dir: Base directory for file operations. Defaults to current directory.
            auto_confirm: If True, automatically confirm file overwrites without prompting.
        """
        self.workspace_dir = os.path.abspath(workspace_dir or os.getcwd())
        self.auto_confirm = auto_confirm
    
    def execute(self, tool_name: str, tool_arguments: str) -> str:
        """Execute the requested tool and return the result."""
        if tool_name == "get_secret":
            return self._get_secret()
        elif tool_name == "read_file":
            return self._read_file(tool_arguments)
        elif tool_name == "write_file":
            return self._write_file(tool_arguments)
        elif tool_name == "execute_bash":
            return self._execute_bash(tool_arguments)
        else:
            return f"Unknown tool: {tool_name}"
    
    def _get_secret(self) -> str:
        """Return the hardcoded secret value."""
        return "42"
    
    def _read_file(self, tool_arguments: str) -> str:
        """Read and return file contents."""
        arguments = json.loads(tool_arguments)
        file_path = arguments.get("file_path")
        
        if not file_path:
            return "Error: file_path parameter is required"
        
        # Resolve relative to workspace
        if not os.path.isabs(file_path):
            file_path = os.path.join(self.workspace_dir, file_path)
        
        if not os.path.exists(file_path):
            return f"Error: File '{file_path}' not found"
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as ex:
            return f"Error reading file: {str(ex)}"
    
    def _write_file(self, tool_arguments: str) -> str:
        """Write content to a file with security checks."""
        arguments = json.loads(tool_arguments)
        file_path = arguments.get("file_path")
        content = arguments.get("content")
        
        if not file_path:
            return "Error: file_path parameter is required"
        if content is None:
            return "Error: content parameter is required"
        
        # Size limit (1MB)
        MAX_FILE_SIZE = 1_000_000
        if len(content) > MAX_FILE_SIZE:
            return f"Error: Content exceeds {MAX_FILE_SIZE} byte limit"
        
        # Resolve relative to workspace
        if not os.path.isabs(file_path):
            file_path = os.path.join(self.workspace_dir, file_path)
        
        full_path = os.path.abspath(file_path)
        
        # Directory sandboxing
        if not full_path.startswith(self.workspace_dir):
            return f"Error: Can only write files within {self.workspace_dir}"
        
        # Blocklist sensitive paths
        BLOCKED_PATTERNS = [".ssh", ".bashrc", ".zshrc", ".env", "id_rsa", "/etc/", "/usr/", ".git/"]
        if any(pattern in full_path for pattern in BLOCKED_PATTERNS):
            return "Error: Cannot write to sensitive locations"
        
        try:
            # Check if file exists and handle confirmation
            if os.path.exists(file_path) and not self.auto_confirm:
                confirm = input(f"File '{file_path}' already exists. Overwrite? [y/N]: ")
                if confirm.lower() != 'y':
                    return f"Write cancelled: File '{file_path}' was not overwritten"
            
            # Ensure directory exists
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Successfully wrote {len(content)} characters to {file_path}"
        except Exception as ex:
            return f"Error writing file: {str(ex)}"
    
    def _execute_bash(self, tool_arguments: str) -> str:
        """Execute a bash command with timeout."""
        arguments = json.loads(tool_arguments)
        command = arguments.get("command")
        
        if not command:
            return "Error: command parameter is required"
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.workspace_dir
            )
            
            output = result.stdout
            error = result.stderr
            
            if result.returncode != 0:
                return f"Command failed with exit code {result.returncode}\nError: {error}\nOutput: {output}"
            
            return output if output else "Command executed successfully (no output)"
        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 30 seconds"
        except Exception as ex:
            return f"Error executing command: {str(ex)}"
