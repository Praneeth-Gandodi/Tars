# Tars: Voice AI Assistant

**TARS** is an **early-stage Voice AI Assistant** built to process **Speech-to-Text (STT)** input and generate comprehensive **Text-based** responses. It currently integrates features like weather, news and time retrieval along with conversation tracking. **Text-to-Speech (TTS) integration is planned for a future release.**.

--- 

## Features
- **Speech-to-Text (STT)** Processing for voice input.
- **Text-to-Text**Can chat with the model directly
- Text-based Responses (**TTS to be added later**)
- **Integrated Tools:**
    1. **Weather Tool** – Fetches current weather
    2. **Date & Time Tool** – Fetches current date and time
    3. **News** - Fetches news based on country and categories
- Conversation history tracking
- Automatic conversation summarization

---

## Installation

### Prerequisites
- Python 3.13.x -- Tested in this environment 

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
If **Windows:**
```bash
.venv/Scripts/activate
```

If **Linux/Mac:**
```bash
source .venv/bin/activate
```

### Install dependencies 
```bash
pip install -r requirements.txt
```

---
## Configuration
This project requires a Groq API key, which you can obtain for free from the official Groq website.
1. Create a file named `.env` in the root of your project directory.
2. Copy and paste the variables and model names from `.env.example` into your '.env`
3. Paste your Groq API key in the `groq_api` field.
#### Your `.env` should look like this 
```
groq_api="YOUR_GROQ_API_KEY_HERE"

model="llama3-8b-8192" #or Any model from Groq 
```

---
## Usage

Run the `tars.py` file:
```bash
python tars.py
```

---

## Development Status
- [x] Weather  
- [x] Date & Time  
- [x] News (needs some changes)  
- [ ] Wikipedia  
- [ ] Web search  
- [ ] Spotify  
- [ ] Application control  
- [ ] Text-to-Speech (TTS)  
- [ ] Integrate Camu (for university attendance tracking; college-specific feature; can be ignored)  
- [ ] Change the framework  
- [ ] SQLite3 for database  
- [ ] Exception handling  
- [ ] Automation of tasks

