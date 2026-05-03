# Installation Troubleshooting Guide

Common installation issues and their solutions.

## ❌ ERROR: No matching distribution found for kiteconnect

### Problem
```
ERROR: Could not find a version that satisfies the requirement kiteconnect==4.3.0
ERROR: No matching distribution found for kiteconnect==4.3.0
```

### Solution 1: Update pip and setuptools

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Upgrade setuptools
pip install --upgrade setuptools

# Try installing again
pip install -r requirements.txt
```

### Solution 2: Use flexible version requirements

The `requirements.txt` file uses flexible versioning (`>=4.0.0`) which will install the latest compatible version:

```bash
pip install -r requirements.txt
```

### Solution 3: Install specific latest version

Use the `requirements-latest.txt` file with known working versions:

```bash
pip install -r requirements-latest.txt
```

### Solution 4: Install kiteconnect separately

```bash
# Install latest version
pip install kiteconnect

# Or specific version
pip install kiteconnect==5.2.0

# Then install other dependencies
pip install python-dotenv rich pandas openpyxl pytz
```

### Solution 5: Check Python version

Kiteconnect v5+ requires Python 3.8 or higher:

```bash
python --version
```

If you have Python 2.7 or 3.7, either:
- Upgrade Python to 3.8+, OR
- Use kiteconnect v4.x:
  ```bash
  pip install kiteconnect>=4.0.0,<5.0.0
  ```

---

## ❌ ERROR: Microsoft Visual C++ required (Windows)

### Problem
```
error: Microsoft Visual C++ 14.0 or greater is required
```

### Solution

1. Download and install **Microsoft C++ Build Tools**:
   - Visit: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Download "Build Tools for Visual Studio"
   - Install with "Desktop development with C++" workload

2. Or install via chocolatey (if you have it):
   ```cmd
   choco install visualstudio2022buildtools
   ```

3. After installation, restart Command Prompt and try again:
   ```cmd
   pip install -r requirements.txt
   ```

---

## ❌ ERROR: Permission denied

### Problem (Mac/Linux)
```
ERROR: Could not install packages due to an EnvironmentError: [Errno 13] Permission denied
```

### Solution 1: Use virtual environment (RECOMMENDED)

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Solution 2: Use --user flag

```bash
pip install --user -r requirements.txt
```

### Solution 3: Use sudo (NOT RECOMMENDED)

```bash
sudo pip install -r requirements.txt
```

---

## ❌ ERROR: Command 'python' not found

### Problem (Mac/Linux)
```
python: command not found
```

### Solution

Try `python3` instead:

```bash
python3 --version
python3 -m pip install -r requirements.txt
python3 main.py
```

Or create an alias:
```bash
alias python=python3
```

---

## ❌ ERROR: SSL Certificate verification failed

### Problem
```
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed
```

### Solution (Mac)

Run the Python certificate installer:

```bash
/Applications/Python\ 3.x/Install\ Certificates.command
```

Replace `3.x` with your Python version (e.g., `3.11`).

### Solution (Windows/Linux)

```bash
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
```

---

## ❌ ERROR: Package compatibility issues

### Problem
```
ERROR: package X is incompatible with package Y
```

### Solution: Use virtual environment

This isolates dependencies and prevents conflicts:

```bash
# Remove existing venv if any
rm -rf venv  # Mac/Linux
rmdir /s venv  # Windows

# Create fresh virtual environment
python -m venv venv

# Activate
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate  # Windows

# Install fresh
pip install --upgrade pip
pip install -r requirements.txt
```

---

## ✅ Verify Installation

After successful installation, verify all packages:

```bash
pip list | grep kiteconnect
pip list | grep rich
pip list | grep pandas
```

Or check all at once:

```bash
pip check
```

---

## 🔄 Fresh Start (Nuclear Option)

If nothing works, start completely fresh:

### Mac/Linux
```bash
# Remove virtual environment
rm -rf venv

# Create new virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip setuptools wheel

# Install dependencies
pip install -r requirements.txt
```

### Windows
```cmd
# Remove virtual environment
rmdir /s venv

# Create new virtual environment
python -m venv venv

# Activate
venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip setuptools wheel

# Install dependencies
pip install -r requirements.txt
```

---

## 📞 Still Having Issues?

1. Check your Python version: `python --version` (need 3.8+)
2. Check your pip version: `pip --version`
3. Try installing packages one by one to identify the problematic one
4. Check the error message carefully - often contains the solution
5. Search for the specific error message online

## 📋 System Information

When reporting issues, include:
- Operating System and version
- Python version: `python --version`
- Pip version: `pip --version`
- Full error message
- Output of: `pip list`
