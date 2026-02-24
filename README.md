# cmcode

```
        ╔═══════════════╗
        ║  ┌─────────┐  ║
        ║  │ ◉     ◉ │  ║
        ║  │  ═════  │  ║
        ║  └─────────┘  ║
        ║    ┌─────┐    ║
        ║    │░░░░░│    ║
        ║    └──┬──┘    ║
        ║   ┌─┘   └─┐   ║
        ╚═══════════════╝

             CMCODE
  AI assistant with tool-calling superpowers
```

A CLI tool for chatting with LLMs with tool-calling capabilities.

## Prerequisites

- Python 3.10+
- An Azure OpenAI API key

## Setup

### 1. Clone and install

```bash
git clone <repository-url>
cd cmcode
pip install -e .
```

### 2. Set up your API key

Create a `.env` file in the project directory:

```bash
AZURE_OPENAI_API_KEY=your-api-key-here
```

Or export it directly:

```bash
export AZURE_OPENAI_API_KEY=your-api-key-here
```

### 3. Add to PATH (if needed)

If `cmcode` is not found after installation, add the Python bin directory to your PATH:

```bash
# Find where pip installed the script
pip show cmcode | grep Location

# Add to PATH (example for macOS/Linux)
export PATH="$PATH:$HOME/Library/Python/3.10/bin"

# Or add to your shell config (~/.zshrc or ~/.bashrc)
echo 'export PATH="$PATH:$HOME/Library/Python/3.10/bin"' >> ~/.zshrc
```

### 4. Verify installation

```bash
cmcode --version
cmcode --help
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
