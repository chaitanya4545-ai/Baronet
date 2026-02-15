# Baronet

**AI-Powered File Automation with Military-Grade Safety**

Baronet is a production-ready file automation system that combines natural language processing with a 6-layer safety pipeline to execute file operations safely.

![Version](https://img.shields.io/badge/version-0.2.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![License](https://img.shields.io/badge/license-MIT-brightgreen)

---

## 📋 Table of Contents

- [What It Does](#-what-it-does)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Features](#-features)
- [Safety Architecture](#-safety-architecture)
- [Usage Examples](#-usage-examples)
- [Project Structure](#-project-structure)
- [Testing](#-testing)
- [Configuration](#-configuration)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 What It Does

Baronet allows you to automate file operations using either:
- **Direct commands** - Precise CLI control
- **Natural language** - Plain English powered by local AI

**Examples:**
```bash
# Create files
baronet ai create a test file with hello world

# Organize files  
baronet ai organize my files by type

# Safe automation
baronet file create report.txt "Project status: Complete"
```

**Safety:** Every operation goes through 6 layers of validation before execution.

---

## 💻 Installation

### Prerequisites

**Required:**
- **Python 3.10 or higher** ([Download here](https://www.python.org/downloads/))
- **Git** ([Download here](https://git-scm.com/downloads))

**Optional (for AI features):**
- **Ollama** for local AI ([Download here](https://ollama.ai/download))

### Step 1: Check Python Version

Open Command Prompt or PowerShell and verify Python is installed:

```bash
python --version
```

**Expected output:** `Python 3.10.x` or higher

If not installed or version is too old, download from https://python.org/downloads

---

### Step 2: Clone the Repository

```bash
# Clone from GitHub
git clone https://github.com/chaitanya4545-ai/OpenClaw.git

# Navigate into directory
cd OpenClaw
```

**Note:** Repository is still named "OpenClaw" on GitHub, but the code is "Baronet"

---

### Step 3: Install Python Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

**What gets installed:**
- `rich` - Beautiful terminal output
- `loguru` - Advanced logging
- `pydantic` - Data validation
- `psutil` - System monitoring
- `click` - CLI framework
- `ollama` - AI integration (optional)

**Troubleshooting:**
If `pip` is not found, try:
```bash
python -m pip install -r requirements.txt
```

---

### Step 4: Verify Installation

Test that Baronet works:

```bash
# Run file list command
python -m core.cli file list
```

**Expected output:**
```
✓ Success!
  Found 0 items
```

If you see this, **installation is complete!** ✅

---

### Step 5: Install Ollama (Optional - For AI Features)

**Only needed if you want natural language commands.**

#### Windows:

1. **Download Ollama:**
   - Go to https://ollama.ai/download
   - Download Windows installer
   - Run the installer

2. **Verify installation:**
   ```bash
   ollama --version
   ```

3. **Pull the llama3.2 model:**
   ```bash
   ollama pull llama3.2
   ```
   
   This downloads ~2GB. Wait for completion.

4. **Test Ollama:**
   ```bash
   ollama list
   ```
   
   You should see `llama3.2` in the list.

#### Mac/Linux:

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull model
ollama pull llama3.2
```

---

### Step 6: Verify AI Integration (Optional)

```bash
# Test natural language command
python -m core.cli ai list all files
```

**Expected output:**
```
🤖 Parsing: 'list all files'...
✅ Validated through 6 safety layers
🟢 Risk: SAFE

Proceed? (y/n):
```

Type `y` and press Enter. If it works, **AI is ready!** 🤖

---

## 🚀 Quick Start

### Basic Commands (No AI Required)

```bash
cd OpenClaw

# Create a file
python -m core.cli file create test.txt "Hello World"

# Read a file
python -m core.cli file read test.txt

# List all files
python -m core.cli file list

# Get file info
python -m core.cli file info test.txt

# Delete a file
python -m core.cli file delete test.txt
```

### AI Commands (Requires Ollama)

```bash
# Natural language - Baronet figures out what to do
python -m core.cli ai create a test file

python -m core.cli ai list all files in workspace

python -m core.cli ai organize my project files

python -m core.cli ai create readme with project description
```

### Using the Shortcut (Windows)

Use `baronet.bat` for easier commands:

```bash
# Instead of: python -m core.cli file list
# Just use:
baronet.bat file list

# Natural language:
baronet.bat ai create test file
```

**Add to PATH** (optional) so you can run `baronet` from anywhere:
1. Right-click "This PC" → Properties
2. Advanced system settings → Environment Variables
3. Edit PATH variable → Add `C:\OpenClaw`
4. Restart terminal

Now you can use:
```bash
baronet file list
baronet ai help me organize
```

---

## ✨ Features

### 🛡️ 6-Layer Safety Pipeline

Every command goes through:

1. **Sanitize** - Block injection attempts
2. **Parse** - AI → structured command
3. **Validate** - Schema & confidence checks
4. **Guard** - Semantic safety verification
5. **Classify** - Risk assessment (SAFE/MODERATE/ELEVATED/DANGEROUS)
6. **Dependencies** - Check prerequisites

**Any layer can block the operation!**

### 🔒 Security Features

- ✅ **Workspace Sandboxing** - Only touches files in `workspace/` folder
- ✅ **Prompt Injection Blocking** - Detects malicious inputs
- ✅ **Path Traversal Prevention** - Can't escape workspace
- ✅ **Automatic Backups** - All deletions create `.backup` files
- ✅ **User Approval** - Dangerous operations require confirmation
- ✅ **Emergency Stop** - Rate limiting and kill switch

### 📊 What's Included

- **Production Code:** 1,940+ lines
- **Test Suite:** 65+ tests
- **Safety Layers:** 6 independent validators
- **Core Modules:** 11 modules
- **Documentation:** Complete guides

---

## 🏗️ Safety Architecture

```
User Input: "organize my files"
    ↓
┌──────────────────────────────────┐
│ 1. Sanitize (injection blocking) │
│ 2. Parse (AI → JSON)             │
│ 3. Validate (schema checks)      │
│ 4. Guard (semantic safety)       │
│ 5. Classify (risk assessment)    │
│ 6. Dependencies (prerequisites)  │
└──────────────────────────────────┘
    ↓
User Approval (for high-risk ops)
    ↓
Atomic Execution (with backups)
    ↓
✅ Success
```

---

## 📁 Project Structure

```
OpenClaw/  (repository folder - code is Baronet)
├── core/
│   ├── __init__.py
│   ├── openclaw.py          # Main command processor
│   ├── cli.py               # CLI interface
│   ├── safety.py            # Safety & permission system
│   ├── logger.py            # Logging system
│   ├── ollama_client.py     # AI/LLM interface
│   ├── schema_validator.py  # Command validation
│   ├── risk_classifier.py   # Risk assessment
│   ├── semantic_guard.py    # Injection prevention
│   ├── dependency_validator.py  # Prerequisite checking
│   ├── ai_handler.py        # Safety pipeline integration
│   └── planner.py           # Multi-step automation
├── modules/
│   ├── __init__.py
│   └── file_ops.py          # File operations
├── tests/
│   ├── test_*.py            # Unit tests
│   ├── test_torture.py      # Security tests
│   └── test_edge_cases.py   # Edge case validation
├── workspace/               # 🔒 Sandboxed working directory
├── config/
│   └── settings.json        # Configuration
├── README.md                # This file
├── requirements.txt         # Python dependencies
└── baronet.bat             # Windows shortcut
```

---

## 🧪 Testing

Run the test suite to verify everything works:

```bash
# Install pytest if needed
pip install pytest

# Run all tests
python -m pytest tests/ -v

# Run specific test suite
python -m pytest tests/test_torture.py -v

# Run with coverage
pip install pytest-cov
python -m pytest tests/ --cov=core --cov=modules
```

**Expected:** 65+ tests passing ✅

---

## ⚙️ Configuration

Configuration file: `config/settings.json`

```json
{
  "workspace": "C:/OpenClaw/workspace",
  "safety": {
    "max_depth": 3,
    "rate_limit": 60,
    "auto_permission": "READ_ONLY"
  }
}
```

**Settings:**
- `workspace` - Sandboxed folder for file operations
- `max_depth` - Maximum execution nesting
- `rate_limit` - Operations per minute
- `auto_permission` - Default permission level

---

## 🔧 Troubleshooting

### "Python is not recognized"
**Fix:** Add Python to PATH during installation, or reinstall Python with "Add to PATH" checked.

### "Module not found"
**Fix:** Install dependencies:
```bash
pip install -r requirements.txt
```

### "Ollama not found"
**Fix:** 
1. Download from https://ollama.ai/download
2. Install and restart terminal
3. Run `ollama pull llama3.2`

### AI commands not working
**Verify:**
```bash
# 1. Check Ollama is running
ollama list

# 2. Check model is installed
ollama list | grep llama3.2

# 3. Test Ollama
ollama run llama3.2 "hello"
```

### Permission errors
**Fix:** Run as administrator (Windows) or use `sudo` (Mac/Linux)

### "Workspace not found"
**Fix:** Baronet creates `workspace/` automatically. If deleted, recreate:
```bash
mkdir workspace
```

---

## 📝 Usage Examples

### Example 1: Create and Organize Files

```bash
# Create some test files
baronet file create report.txt "Project Report"
baronet file create notes.md "Meeting Notes"
baronet file create data.json "{}"

# List them
baronet file list

# Use AI to organize
baronet ai organize files by extension
```

### Example 2: Safe File Operations

```bash
# AI will parse and validate
baronet ai create backup folder

# Safety system detects risk level
baronet ai delete old files  # ⚠️ Will ask for approval

# Safe operations proceed automatically
baronet ai list all markdown files  # ✅ Auto-approved
```

### Example 3: Multi-Step Automation (Python)

```python
from pathlib import Path
from core.planner import create_planner

# Create a multi-step plan
planner = create_planner(Path("C:/OpenClaw/workspace"))
plan = planner.create_plan("create project structure with docs and src folders")

# Execute if safe
if plan['safe']:
    result = planner.execute_plan(plan['steps'])
    print(f"Completed {result['completed_steps']} steps")
```

---

## ⚠️ Important Limitations

- **Workspace Only**: Can only operate within the `workspace/` folder
- **No Network**: No internet access, downloads, or uploads  
- **No System Access**: Cannot modify OS or system files
- **File Operations Only**: Currently limited to file management
- **Ollama Required**: AI features need Ollama + llama3.2 model

---

## 🤝 Contributing

This is an educational project demonstrating AI safety principles. Feel free to:
- Fork and experiment
- Submit issues
- Propose improvements
- Learn from the code

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

**Built with:**
- [Ollama](https://ollama.ai/) - Local LLM runtime
- [Rich](https://github.com/Textualize/rich) - Terminal UI
- [Loguru](https://github.com/Delgan/loguru) - Logging
- [Click](https://click.palletsprojects.com/) - CLI framework

---

## 📞 Support

**Issues?** Open an issue on GitHub: https://github.com/chaitanya4545-ai/OpenClaw/issues

**Questions?** Check the documentation in the repo.

---

**Made with ❤️ and 6 layers of safety checks**

**Note:** This project was originally called "OpenClaw" but renamed to "Baronet" to avoid confusion with the commercial OpenClaw.ai product. The GitHub repository name hasn't been changed yet, but all code references use "Baronet".
