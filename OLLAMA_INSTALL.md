# Ollama Installation Guide for OpenClaw Phase 2

## Step 1: Download Ollama

1. Open your browser and go to: **https://ollama.com/download/windows**
2. Click **"Download for Windows"** (OllamaSetup.exe - ~1GB)
3. Save the file to your Downloads folder

## Step 2: Install Ollama

1. Double-click `OllamaSetup.exe` from Downloads
2. The installer will run automatically (no admin rights needed)
3. Installation takes ~2-3 minutes
4. Ollama will start automatically and appear in your system tray

## Step 3: Verify Installation

Open PowerShell and run:
```powershell
ollama --version
```

You should see something like: `ollama version 0.x.x`

## Step 4: Pull the Model

In PowerShell, run:
```powershell
ollama pull llama3.2
```

This downloads ~2GB and takes 5-10 minutes depending on your internet speed.

## Step 5: Test the Model

Try a simple test:
```powershell
ollama run llama3.2
```

Type: "Hello, how are you?"

The model should respond. Type `/bye` to exit.

## Step 6: Verify from OpenClaw

Navigate to OpenClaw and test:
```powershell
cd C:\OpenClaw
python -c "import ollama; print(ollama.list())"
```

Should show llama3.2 in the list.

---

**Once complete, we'll build the ollama_client.py module!**
