# Tars: Voice AI Assistant

**TARS** is an **early-stage Voice AI Assistant** built to process **Speech-to-Text (STT)** input and generate comprehensive **Text-based** responses. It currently integrates features like weather and time retrieval, along with conversation tracking. **Text-to-Speech (TTS) integration is planned for a future release.**.

--- 

## Features
- **Speech-to-Text (STT)** Processing for voice input.
- Text-based Responses (**TTS to be added later**)
- **Integrated Tools:**
    1. **Weather Tool** – Fetches current weather
    2. **Date & Time Tool** – Fetches current date and time
- Conversation history tracking
- Automatic conversation summarization

---

## Installation

### Prerequisites
- Python 3.x

### Clone the repo
```bash
git clone https://github.com/Praneeth-Gandodi/Tars.git
```

### Navigate to project folder
```bash
cd Tars
```

### Create a Python virtual environment
```bash
python -m venv .venv
```

### Activate virtual environment
**Windows:**
```bash
.venv\Scripts\activate
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

### Install dependencies 
```bash
pip install -r requirements.txt
```

---

## Usage

Run the `tars.py` file:
```bash
python tars.py
```

---

## Future Plans
- Integrate TTS (Text-to-Speech) for voice responses
- Improve conversation summarization
- Expand toolset: Integrate functionality for opening applications, music control, and reminder management.