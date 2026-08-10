# 🚀 Startup Guide

Follow these steps to set up and run the application locally.

---

## Prerequisites

- Python 3.8+ installed
- `pip` available in your terminal

---

## Steps

### 1. Create a Virtual Environment

```bash
python -m venv venv
```

### 2. Activate the Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**macOS / Linux:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example env file and fill in your values:

```bash
cp .env.example .env
```

> Edit `.env` with your API keys and configuration before running.

### 5. Start the Application

```bash
python main.py
```

---

## Quick Start (Copy-Paste)

```bash
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
python main.py
```

---

> 💡 Make sure your `.env` file is properly configured before starting the app.
