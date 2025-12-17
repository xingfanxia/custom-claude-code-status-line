# Custom Claude Code Status Line

A custom status line for [Claude Code](https://github.com/anthropics/claude-code) that displays comprehensive session information including real-time context usage tracking.

## Features

- **Real-time Context Usage**: Shows accurate context window utilization with visual progress bar
- **Dynamic Model Detection**: Automatically detects context limits (1M for Sonnet 4.5, 200k for older models)
- **Configurable Overhead**: Accounts for system prompts, tools, and MCP overhead
- **Git Integration**: Displays current git branch when in a git repository
- **Version Checking**: Automatically checks for Claude Code updates (cached hourly)
- **Session Tracking**: Shows session ID and timestamp
- **Last Prompt Display**: Shows your most recent command/prompt
- **Color-Coded Progress**: Visual indication of context usage (green < 50%, yellow < 80%, orange < 90%, red ≥ 90%)

## Example Output

```
📁 ai_architect |⚡️ main | [Sonnet 4.5 (1M context)] | [███████░░░░░░░░░░░░░] 17.5% (175,324) | 46f74ece | 2.0.71 (current) | 09:15:45 | Add user authentication
```

## Prerequisites

- [Claude Code](https://github.com/anthropics/claude-code) v2.0+
- Python 3.6+
- [uv](https://github.com/astral-sh/uv) (Python package manager)

## Installation

### Option 1: Automatic Installation (Recommended)

Run the installation script:

```bash
git clone https://github.com/xingfanxia/custom-claude-code-status-line.git
cd custom-claude-code-status-line
./install.sh
```

The script will:
- Check prerequisites (Python, uv)
- Install the status line script to `~/.claude/scripts/`
- Update your `~/.claude/settings.json` configuration
- Create a backup of existing settings
- Provide post-installation instructions

### Option 2: Manual Installation

If you prefer to install manually:

#### 1. Install the Script

```bash
mkdir -p ~/.claude/scripts
cp claude-code-status-line.py ~/.claude/scripts/
chmod +x ~/.claude/scripts/claude-code-status-line.py
```

#### 2. Configure Claude Code

Add the status line configuration to `~/.claude/settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "uv run python ~/.claude/scripts/claude-code-status-line.py",
    "padding": 0
  }
}
```

**Note**: If you already have a `statusLine` configuration, replace it with the above.

#### 3. Restart Claude Code

Exit and restart Claude Code for the changes to take effect.

## Configuration

### Adjusting Context Overhead

The status line includes a configurable overhead constant (`CONTEXT_OVERHEAD`) to account for system prompts, tools, and MCP servers that aren't reflected in the transcript's raw token counts.

To calibrate this for your setup:

1. Open Claude Code and run the `/context` command
2. Sum up the overhead components:
   ```
   System prompt:    3.1k
   System tools:    18.6k
   MCP tools:       63.2k
   Custom agents:    2.2k
   Memory files:     1.2k
   ─────────────────────
   Total:          ~88.3k tokens
   ```

3. Update the `CONTEXT_OVERHEAD` value in `claude-code-status-line.py`:
   ```python
   CONTEXT_OVERHEAD = 88300  # Update this value (in tokens)
   ```

4. Restart Claude Code to apply changes

**When to update**: Recalibrate whenever you:
- Add or remove MCP servers
- Add custom agents
- Significantly change your Claude Code configuration

### Customizing the Display

Edit `claude-code-status-line.py` to customize:

- **Progress bar length**: Change `bar_length = 20` (line ~160)
- **Prompt truncation**: Change `last_prompt[:47]` to adjust max length (line ~118)
- **Colors**: Modify the color code constants (lines 163-176)
- **Display format**: Edit the final print statement (lines ~281-283)

## How It Works

The status line script:

1. Reads session data from Claude Code via stdin (JSON format)
2. Parses the session transcript to extract token usage from the most recent assistant message
3. Sums all token types:
   - `input_tokens`: Fresh tokens processed
   - `cache_creation_input_tokens`: Tokens used to create cache
   - `cache_read_input_tokens`: Tokens read from cache
   - `output_tokens`: Tokens generated in response
4. Adds configured overhead for system prompts and tools
5. Calculates percentage of context window used
6. Formats and displays the status line with color-coded progress

## Troubleshooting

### Status line shows 0% or incorrect values

**Solution**: Update the `CONTEXT_OVERHEAD` value:
1. Run `/context` in Claude Code
2. Calculate total overhead (system + tools + MCP + agents + memory)
3. Update `CONTEXT_OVERHEAD` in the script
4. Restart Claude Code

### Status line doesn't appear

**Check**:
- Is `uv` installed and in your PATH? Run `which uv`
- Is Python 3.6+ installed? Run `python3 --version`
- Is the script executable? Run `chmod +x ~/.claude/scripts/claude-code-status-line.py`
- Is the configuration in `~/.claude/settings.json` correct?

### Status line values don't match `/context` exactly

This is expected. The status line shows an approximation based on:
- The most recent transcript entry (slightly behind current state)
- Configured overhead constant (may need recalibration)

Typical variance: ±5-10% is normal. If variance is larger, recalibrate the overhead.

### "uv: command not found"

Install `uv`:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or use Homebrew:
```bash
brew install uv
```

Alternatively, modify the command in `settings.json` to use Python directly:
```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 ~/.claude/scripts/claude-code-status-line.py",
    "padding": 0
  }
}
```

## Technical Details

### Token Calculation

The script calculates total context usage as:
```
Total = input_tokens + cache_creation_tokens + cache_read_tokens + output_tokens + CONTEXT_OVERHEAD
```

### Context Limit Detection

Context limits are determined by:
1. Checking model ID for "1m" or "200k" strings
2. Defaulting to 1M for modern models (Sonnet 4.5+)

### Version Check Caching

Claude Code version checks are cached in `~/.claude/version_check_cache` for 1 hour to avoid excessive GitHub API calls.

## License

MIT

## Credits

Inspired by the original [ccstatusline](https://www.npmjs.com/package/ccstatusline) package, with enhanced features for accurate context tracking and MCP tool overhead accounting.

## Contributing

Issues and pull requests welcome! This is a personal project but happy to accept improvements.
