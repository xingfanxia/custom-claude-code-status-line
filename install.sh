#!/bin/bash

# Custom Claude Code Status Line Installer
# This script installs the custom status line for Claude Code

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  Custom Claude Code Status Line Installer${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.6 or higher."
        exit 1
    fi
    print_success "Python 3 found: $(python3 --version)"

    # Check uv (optional but recommended)
    if ! command -v uv &> /dev/null; then
        print_warning "uv is not installed (recommended but optional)"
        print_info "Install uv with: curl -LsSf https://astral.sh/uv/install.sh | sh"
        USE_UV=false
    else
        print_success "uv found: $(uv --version)"
        USE_UV=true
    fi

    # Check Claude Code directory
    if [ ! -d "$HOME/.claude" ]; then
        print_error "Claude Code directory (~/.claude) not found."
        print_error "Please make sure Claude Code is installed and has been run at least once."
        exit 1
    fi
    print_success "Claude Code directory found"

    echo ""
}

# Install the script
install_script() {
    print_info "Installing status line script..."

    # Create scripts directory
    mkdir -p "$HOME/.claude/scripts"

    # Get the directory where this install script is located
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

    # Copy the status line script
    if [ -f "$SCRIPT_DIR/claude-code-status-line.py" ]; then
        cp "$SCRIPT_DIR/claude-code-status-line.py" "$HOME/.claude/scripts/"
        chmod +x "$HOME/.claude/scripts/claude-code-status-line.py"
        print_success "Script installed to ~/.claude/scripts/claude-code-status-line.py"
    else
        print_error "claude-code-status-line.py not found in current directory"
        exit 1
    fi

    echo ""
}

# Update settings
update_settings() {
    print_info "Updating Claude Code settings..."

    SETTINGS_FILE="$HOME/.claude/settings.json"

    # Determine command based on uv availability
    if [ "$USE_UV" = true ]; then
        STATUS_COMMAND="uv run python ~/.claude/scripts/claude-code-status-line.py"
    else
        STATUS_COMMAND="python3 ~/.claude/scripts/claude-code-status-line.py"
    fi

    # Backup existing settings
    if [ -f "$SETTINGS_FILE" ]; then
        cp "$SETTINGS_FILE" "$SETTINGS_FILE.backup.$(date +%s)"
        print_success "Backed up existing settings to $SETTINGS_FILE.backup.*"

        # Check if settings.json has statusLine already
        if grep -q '"statusLine"' "$SETTINGS_FILE"; then
            print_warning "Existing statusLine configuration found"
            print_info "Updating statusLine configuration..."

            # Use Python to update the JSON (safer than sed)
            python3 << EOF
import json
import sys

try:
    with open('$SETTINGS_FILE', 'r') as f:
        settings = json.load(f)

    settings['statusLine'] = {
        'type': 'command',
        'command': '$STATUS_COMMAND',
        'padding': 0
    }

    with open('$SETTINGS_FILE', 'w') as f:
        json.dump(settings, f, indent=2)
        f.write('\n')

    print("Settings updated successfully")
except Exception as e:
    print(f"Error updating settings: {e}", file=sys.stderr)
    sys.exit(1)
EOF

            if [ $? -eq 0 ]; then
                print_success "Settings updated"
            else
                print_error "Failed to update settings. Please update manually."
            fi
        else
            # Add statusLine to existing settings
            print_info "Adding statusLine configuration..."
            python3 << EOF
import json
import sys

try:
    with open('$SETTINGS_FILE', 'r') as f:
        settings = json.load(f)

    settings['statusLine'] = {
        'type': 'command',
        'command': '$STATUS_COMMAND',
        'padding': 0
    }

    with open('$SETTINGS_FILE', 'w') as f:
        json.dump(settings, f, indent=2)
        f.write('\n')

    print("Settings updated successfully")
except Exception as e:
    print(f"Error updating settings: {e}", file=sys.stderr)
    sys.exit(1)
EOF

            if [ $? -eq 0 ]; then
                print_success "Settings updated"
            else
                print_error "Failed to update settings. Please update manually."
            fi
        fi
    else
        # Create new settings file
        print_info "Creating new settings.json..."
        cat > "$SETTINGS_FILE" << EOF
{
  "statusLine": {
    "type": "command",
    "command": "$STATUS_COMMAND",
    "padding": 0
  }
}
EOF
        print_success "Settings file created"
    fi

    echo ""
}

# Print post-installation instructions
print_instructions() {
    print_success "Installation complete!"
    echo ""
    print_info "Next steps:"
    echo "  1. Restart Claude Code to activate the status line"
    echo "  2. Run '/context' in Claude Code to see your context breakdown"
    echo "  3. Update CONTEXT_OVERHEAD in the script if needed:"
    echo "     ~/.claude/scripts/claude-code-status-line.py"
    echo ""
    print_info "To update the overhead:"
    echo "  1. Run '/context' in Claude Code"
    echo "  2. Sum: System prompt + System tools + MCP tools + Custom agents + Memory files"
    echo "  3. Edit CONTEXT_OVERHEAD value at the top of the script"
    echo "  4. Restart Claude Code"
    echo ""
    print_info "For more information, see README.md"
    echo ""
}

# Main installation flow
main() {
    print_header
    check_prerequisites
    install_script
    update_settings
    print_instructions
}

# Run installation
main
