# Tars: Voice AI Assistant 🚧

**TARS** is an **early-stage Voice AI Assistant** built to process **Speech-to-Text (STT)**, **Text** inputs and generate both **Speech-Based** and ***Text-based** responses. It integrates features such as file handling, news retrieval, minimal web search, and persistent conversation tracking.

---

## NOTE: Tars is built as a learning project

---

## Features

- **Speech-to-Text (STT)** Processing for voice input
- **Text-to-Text** Can chat with the model directly
- **Text-to-Speech (TTS)** based responses.
- **Persistent conversation storage using SQLite**
- **Integrated Tools:**
    1. **Websearch** - Uses DuckDuckGo library. This tool can search for Pages, Images, Videos and news (Try to set the max_results to low to reduce high token consumption)
    2. **Wikipedia** - Can do wikipedia Search, Summary and Content(Using tool will consume a lot of tokens.)
    3. **News** - Fetches news based on country and categories
    4. **File handling** - Can read, write, search and open files (For example You can ask it open video.mp4 in downloads folder and it can open the file.)
    5. **Video downloading utilities**
- Conversation history tracking
- Automatic conversation summarization

---

## Installation

### Prerequisites

- Python 3.12.x -- Tested in this environment

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

- You will be prompted to paste your Groq API key and model name.
- Enter your Groq API key and the desired model name when prompted.
- This setup is required only once. If you want to change the model name or API key later, open the generated .env file and update the values there.

---

## Usage

Run the `tars.py` file:

```bash
python tars.py
```

---

## Development Status : Paused⏸️

---

### Implemented / Planned Features

- [x] Text-to-Speech (TTS)
- [x] Web search  
- [x] News  
- [x] Wikipedia
- [x] File handling (Read and write text files, Search for files with names and types)
- [x] Video Downloader(supports Youtube(Video/Audio), Instagram(Video), Facebook(Video))
- [x] Weather  
- [x] Date & Time
- [x] Speedtest
- [ ] Browser Control
- [ ] Spotify  
- [ ] Application control
- [ ] Integrate Camu (for university attendance tracking; college-specific feature; can be ignored)  
- [ ] Change the framework
- [ ] Automation of tasks

## License

MIT License © 2025 Gandodi Praneeth Kumar
