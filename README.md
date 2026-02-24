# cmcode

A CLI tool for chatting with LLMs with tool-calling capabilities.

## Installation

```bash
pip install -e .
```

## Usage

### Interactive Mode

```bash
cmcode
```

### Single Query

```bash
cmcode -q "What files are in this directory?"
```

### Piped Input

```bash
echo "Explain this code" | cmcode
cat file.py | cmcode -q "Review this code"
```

## Options

```
Options:
  -q, --query TEXT      Single query to run (non-interactive)
  -i, --interactive     Force interactive mode
  -m, --model TEXT      Model to use (default: gpt-4o)
  -e, --endpoint TEXT   API endpoint URL
  -c, --config PATH     Path to config file
  -v, --verbose         Increase verbosity (-v, -vv)
  --no-stream           Disable streaming output
  --plain               Plain text output (no rich formatting)
  --json                JSON output format
  -y, --yes             Auto-confirm file operations
  -w, --workspace PATH  Workspace directory for file operations
  --version             Show the version and exit.
  --help                Show this message and exit.
```

## Configuration

Create a `.cmcode.yaml` file in your home directory or current directory:

```bash
cmcode init
```

Or set environment variables:

- `AZURE_OPENAI_API_KEY` - Your API key (required)
- `CMCODE_ENDPOINT` - API endpoint URL
- `CMCODE_MODEL` - Model name
- `CMCODE_STREAMING` - Enable streaming (true/false)
- `CMCODE_OUTPUT_FORMAT` - Output format (rich/plain/json)

## Available Tools

The assistant has access to these tools:

- `get_secret` - Returns a secret value
- `read_file` - Reads file contents
- `write_file` - Writes content to files (with safety checks)
- `execute_bash` - Executes bash commands

## License

MIT
