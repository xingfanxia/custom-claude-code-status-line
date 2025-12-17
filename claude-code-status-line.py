#!/usr/bin/env python3
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

# CONFIGURABLE: Context overhead (in tokens)
# This represents the constant overhead from system prompts, tools, and other infrastructure
# that Claude Code includes in the context but isn't reflected in the transcript's usage data.
#
# To update this value, run `/context` in Claude Code and sum up:
#   - System prompt
#   - System tools
#   - MCP tools
#   - Custom agents
#   - Memory files
#
# Example calculation (adjust based on your /context output):
#   3.1k (system) + 18.6k (tools) + 63.2k (MCP) + 2.2k (agents) + 1.2k (memory) = 88.3k
CONTEXT_OVERHEAD = 88300  # Update this if you add/remove MCP tools or change configuration

# Read JSON from stdin
data = json.load(sys.stdin)

# Extract values
model = data["model"]["display_name"]
model_id = data["model"]["id"]
current_dir = os.path.basename(data["workspace"]["current_dir"])
session_id = data["session_id"]
version = data["version"]

# Dynamically get context limit from model data
# Default to 1M for newer models, but try to get from model config
context_limit = data.get("model", {}).get("context_window", 1000000)
# If model ID contains "1m", use 1M context
if "1m" in model_id.lower():
    context_limit = 1000000
elif "200k" in model_id.lower():
    context_limit = 200000
else:
    # Default based on common models
    context_limit = 1000000

# Check for git branch
git_branch = ""
if os.path.exists(".git"):
    try:
        with open(".git/HEAD", "r") as f:
            ref = f.read().strip()
            if ref.startswith("ref: refs/heads/"):
                git_branch = f" |⚡️ {ref.replace('ref: refs/heads/', '')}"
    except Exception:
        pass


transcript_path = data["transcript_path"]

# Parse transcript file to get actual context usage from last assistant message
context_used_token = 0
last_prompt = ""

try:
    with open(transcript_path, "r") as f:
        lines = f.readlines()

        # Iterate from last line to first line
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue

            try:
                obj = json.loads(line)

                # Get last user message for prompt (skip meta messages)
                if (
                    obj.get("type") == "user"
                    and "message" in obj
                    and not last_prompt
                    and not obj.get("isMeta", False)
                ):  # Skip meta messages

                    message_content = obj["message"].get("content", "")
                    if isinstance(message_content, list) and len(message_content) > 0:
                        # Handle structured content
                        text_parts = []
                        for part in message_content:
                            if isinstance(part, dict) and part.get("type") == "text":
                                text = part.get("text", "")
                                text_parts.append(text)

                        if text_parts:
                            last_prompt = " ".join(text_parts)
                    elif isinstance(message_content, str):
                        last_prompt = message_content

                    # Also try to get content directly if above doesn't work
                    if not last_prompt and "content" in obj["message"]:
                        content = obj["message"]["content"]
                        if isinstance(content, str):
                            last_prompt = content
                        elif isinstance(content, list):
                            for item in content:
                                if isinstance(item, dict) and "text" in item:
                                    text = item["text"]
                                    if text:
                                        last_prompt = text
                                        break
                                elif isinstance(item, str):
                                    last_prompt = item
                                    break

                    # Truncate prompt if too long
                    if last_prompt and len(last_prompt) > 50:
                        last_prompt = last_prompt[:47] + "..."

                # Get the TOTAL context usage from the most recent assistant message
                # This includes all tokens: system prompts, tools, messages, etc.
                if (
                    obj.get("type") == "assistant"
                    and "message" in obj
                    and "usage" in obj["message"]
                ):
                    usage = obj["message"]["usage"]

                    # Get all token counts from usage
                    input_tokens = usage.get("input_tokens", 0)
                    cache_creation_input_tokens = usage.get("cache_creation_input_tokens", 0)
                    cache_read_input_tokens = usage.get("cache_read_input_tokens", 0)
                    output_tokens = usage.get("output_tokens", 0)

                    # Total context usage = sum of all token types + overhead
                    # input_tokens: fresh tokens processed
                    # cache_creation_input_tokens: tokens used to create cache
                    # cache_read_input_tokens: tokens read from cache
                    # output_tokens: tokens generated in response
                    # CONTEXT_OVERHEAD: system prompts, tools, and infrastructure (see top of file)
                    context_used_token = (
                        input_tokens
                        + cache_creation_input_tokens
                        + cache_read_input_tokens
                        + output_tokens
                        + CONTEXT_OVERHEAD
                    )

                    # Don't break - keep looking for user prompt

                # If we have both token usage and user prompt, we can break
                if context_used_token > 0 and last_prompt:
                    break

            except json.JSONDecodeError:
                # Skip malformed JSON lines
                continue

except FileNotFoundError:
    # If transcript file doesn't exist, keep context_used_token as 0
    pass

context_used_rate = (context_used_token / context_limit) * 100

# Create progress bar
bar_length = 20
filled_length = int(bar_length * context_used_token // context_limit)
bar = "█" * filled_length + "░" * (bar_length - filled_length)

# Color codes
RESET = "\033[0m"
BOLD = "\033[1m"
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
ORANGE = "\033[38;5;208m"
RED = "\033[91m"
CYAN = "\033[96m"
BRIGHT_CYAN = "\033[1;37m"  # Bright white for dark mode
MAGENTA = "\033[95m"
WHITE = "\033[97m"
GRAY = "\033[90m"
LIGHT_GRAY = "\033[37m"


def check_claude_version(current_version):
    """Check if there's a newer version of Claude Code available"""
    try:
        # Try to get latest version from GitHub API
        req = urllib.request.Request(
            "https://api.github.com/repos/anthropics/claude-code/releases/latest",
            headers={"User-Agent": "claude-status-line"},
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            latest_version = data.get("tag_name", "").lstrip("v")

            if not latest_version:
                return "current"

            # Simple version comparison for semantic versioning
            def version_to_tuple(v):
                return tuple(map(int, v.split(".")[:3]))

            try:
                current_tuple = version_to_tuple(current_version.lstrip("v"))
                latest_tuple = version_to_tuple(latest_version)

                if current_tuple < latest_tuple:
                    return "outdated"
                else:
                    return "current"
            except ValueError:
                return "current"

    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        json.JSONDecodeError,
        Exception,
    ):
        # If we can't check, assume current version is fine
        return "current"


def get_version_status(version):
    """Get version status with caching"""
    version_check_file = os.path.expanduser("~/.claude/version_check_cache")
    check_interval = 3600  # Check every hour

    try:
        # Check if cache file exists and is recent
        if os.path.exists(version_check_file):
            file_mtime = os.path.getmtime(version_check_file)
            current_time = time.time()

            if current_time - file_mtime < check_interval:
                # Use cached result
                with open(version_check_file, "r") as f:
                    return f.read().strip()

        # Time to check for updates
        status = check_claude_version(version)

        # Cache the result
        os.makedirs(os.path.dirname(version_check_file), exist_ok=True)
        with open(version_check_file, "w") as f:
            f.write(status)

        return status

    except Exception:
        return "current"


# Get version status and format display
version_status = get_version_status(version)

if version_status == "outdated":
    version_color = ORANGE
else:
    version_color = GREEN

# Session ID (first 8 characters)
session_short = session_id[:8]

# Color the progress bar based on usage percentage
if context_used_rate < 50:
    bar_color = GREEN
elif context_used_rate < 80:
    bar_color = YELLOW
elif context_used_rate < 90:
    bar_color = ORANGE
else:
    bar_color = RED

context_usage = f" | [{bar_color}{bar}{RESET}] {bar_color}{context_used_rate:.1f}%{RESET} ({CYAN}{context_used_token:,}{RESET})"

# Get current timestamp
current_time = datetime.now().strftime("%H:%M:%S")

# Fallback if no prompt found
if not last_prompt:
    last_prompt = "no recent prompt"

# Build comprehensive status line
print(
    f"📁 {BRIGHT_CYAN}{current_dir}{RESET}{GREEN}{git_branch}{RESET} {GRAY}|{RESET} {BOLD}[{MAGENTA}{model}{RESET}{BOLD}]{RESET}{context_usage} {GRAY}|{RESET} {WHITE}{session_short}{RESET} {GRAY}|{RESET} {version_color}{version} ({version_status}){RESET} {GRAY}|{RESET} {WHITE}{current_time}{RESET} {GRAY}|{RESET} {LIGHT_GRAY}{last_prompt}{RESET}"
)
