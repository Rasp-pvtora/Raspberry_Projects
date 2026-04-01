# Set Up AI-Powered Voice Service

A fully local, privacy-first AI voice assistant for Raspberry Pi. Uses open-source models for wake word detection, speech-to-text, conversational AI, and text-to-speech — all running on-device without any cloud dependency. Includes a web dashboard for configuration, language selection, conversation history, and voice settings.

🪙 **Donations are Welcome!**
If you find this project helpful, you can support my work with a small donation.
₿ Bitcoin donation: `bc1q...`

---

## Table of Contents

1. [Project structure](#project-structure)
2. [Hardware requirements](#hardware-requirements)
3. [Budget](#budget)
4. [Libraries and dependencies](#libraries-and-dependencies)
5. [Quickstart — Laptop (development)](#quickstart--laptop-development)
6. [Environment configuration (.env)](#environment-configuration-env)
7. [Voice pipeline overview](#voice-pipeline-overview)
8. [Feature 1 — Wake word detection (OpenWakeWord)](#feature-1--wake-word-detection-openwakeword)
9. [Feature 2 — Speech-to-Text (Whisper.cpp)](#feature-2--speech-to-text-whispercpp)
10. [Feature 3 — Conversational AI (llama.cpp)](#feature-3--conversational-ai-llamacpp)
11. [Feature 4 — Text-to-Speech (Piper TTS)](#feature-4--text-to-speech-piper-tts)
12. [Feature 5 — Web dashboard](#feature-5--web-dashboard)
13. [Wyoming Protocol — Modular voice AI architecture](#wyoming-protocol--modular-voice-ai-architecture)
14. [Voxtral-4B-TTS — Premium TTS upgrade path](#voxtral-4b-tts--premium-tts-upgrade-path)
15. [Home Assistant integration](#home-assistant-integration)
16. [Multi-language support](#multi-language-support)
17. [Skill and plugin system](#skill-and-plugin-system)
18. [Authentication](#authentication)
19. [How to deploy to Raspberry Pi](#how-to-deploy-to-raspberry-pi)
20. [How to run on the Raspberry Pi](#how-to-run-on-the-raspberry-pi)
21. [Real-world applications](#real-world-applications)
22. [Security notes](#security-notes)
23. [Troubleshooting](#troubleshooting)
24. [Where to next](#where-to-next)

---

## Project structure

```
.
├── app.py                     ← Python entry point (FastAPI + WebSocket)
├── requirements.txt           ← Python dependencies
├── .env.default               ← Environment variable template (copy to .env)
├── .gitignore                 ← Git ignore rules
├── src/
│   ├── pipeline/
│   │   ├── wakeword.py        ← OpenWakeWord wake word detection
│   │   ├── stt.py             ← Whisper.cpp speech-to-text
│   │   ├── llm.py             ← llama.cpp conversational AI
│   │   ├── tts.py             ← Piper TTS text-to-speech
│   │   └── audio_io.py        ← Microphone input and speaker output
│   ├── plugins/
│   │   ├── gpio_skill.py      ← GPIO control via voice commands
│   │   ├── weather_skill.py   ← Weather report skill
│   │   ├── timer_skill.py     ← Timer and alarm skill
│   │   └── system_skill.py    ← System info skill (temp, uptime)
│   ├── wyoming/
│   │   ├── server.py          ← Wyoming protocol server
│   │   ├── stt_handler.py     ← Wyoming STT handler
│   │   └── tts_handler.py     ← Wyoming TTS handler
│   ├── routes/
│   │   ├── auth.py            ← Login / logout routes
│   │   ├── dashboard.py       ← Dashboard API
│   │   ├── settings.py        ← Settings and model management API
│   │   └── conversation.py    ← Conversation history API
│   └── services/
│       ├── model_manager.py   ← Download and manage AI models
│       ├── language_service.py ← Multi-language configuration
│       └── system_service.py  ← System info (temp, memory, disk)
├── models/                    ← Downloaded AI models (auto-populated)
│   ├── whisper/               ← Whisper.cpp models (tiny, base, small)
│   ├── piper/                 ← Piper TTS voice models
│   ├── llm/                   ← LLM models (GGUF format)
│   └── wakeword/              ← OpenWakeWord models
├── templates/                 ← Jinja2 HTML templates
│   ├── layout.html            ← Base layout with sidebar navigation
│   ├── login.html             ← Login page
│   ├── dashboard.html         ← Main dashboard with waveform + conversation
│   ├── settings.html          ← Model and language settings
│   └── history.html           ← Conversation history browser
├── static/                    ← Static frontend assets
│   ├── css/style.css          ← Dark theme dashboard stylesheet
│   └── js/
│       ├── main.js            ← WebSocket client for real-time audio
│       ├── dashboard.js       ← Dashboard waveform + conversation logic
│       └── settings.js        ← Settings page logic
├── scripts/
│   ├── setup-audio.sh         ← Audio device setup (USB mic, speaker)
│   ├── download-models.sh     ← Download default AI models
│   └── setup-wyoming.sh       ← Wyoming protocol setup for Home Assistant
├── deploy/
│   └── deploy_to_pi.sh        ← rsync-based deploy script
├── docs/
│   └── threat_model.md        ← Threat model and mitigations
├── tests/                     ← Test directory
├── README.md                  ← This file
├── TSD.md                     ← Technical Specification Description
└── task.md                    ← Engineering checklist
```

---

## Hardware requirements

| Component | Required | Notes |
|---|---|---|
| Raspberry Pi 4 (4 GB+) / Pi 5 | Yes | Pi 5 recommended for LLM inference; 4 GB minimum, 8 GB recommended |
| microSD card (32 GB+) | Yes | For OS, project files, and AI models (~10 GB for all models) |
| USB microphone | Yes | Any USB mic works; ReSpeaker USB Mic Array recommended for far-field |
| Speaker (3.5mm or USB) | Yes | 3.5mm aux speaker, USB speaker, or I2S DAC + speaker HAT |
| Power supply (official) | Yes | 5V 3A for Pi 4, 5V 5A for Pi 5 |
| Ethernet or WiFi | Yes | For initial model downloads; voice works offline after setup |

---

## Budget

| Item | Estimated Price (USD) | Notes |
|---|---|---|
| USB microphone | $8 – $15 | Basic USB mic; ReSpeaker USB Mic Array ~$25 for far-field |
| 3.5mm speaker | $5 – $10 | Any powered mini speaker |
| **Alternative:** I2S DAC + speaker HAT | $10 – $20 | Better audio quality (e.g., Adafruit I2S 3W Class D Amplifier) |
| **Alternative:** ReSpeaker 2-Mic Pi HAT | $10 – $15 | Integrated mic + speaker HAT for Pi |
| **Total (minimum)** | **~$13 – $25** | USB mic + 3.5mm speaker |

> **Note:** The Raspberry Pi itself, microSD card, and power supply are not included in the budget above — they are assumed to be already available.

---

## Libraries and dependencies

### Python dependencies

| Library | Version | Purpose |
|---|---|---|
| [FastAPI](https://fastapi.tiangolo.com/) | ^0.115.0 | Web framework and API routing |
| [uvicorn](https://www.uvicorn.org/) | ^0.34.0 | ASGI server for FastAPI |
| [Jinja2](https://jinja.palletsprojects.com/) | ^3.1.4 | Server-side HTML templating |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | ^1.0.1 | Load environment variables from `.env` |
| [websockets](https://pypi.org/project/websockets/) | ^13.1 | WebSocket support for real-time audio |
| [openwakeword](https://github.com/dscripka/openWakeWord) | ^0.6.0 | Wake word detection engine |
| [whispercpp](https://github.com/aarnphm/whispercpp) | ^0.3.0 | Python bindings for whisper.cpp STT |
| [piper-tts](https://github.com/rhasspy/piper) | ^1.2.0 | Fast local text-to-speech |
| [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) | ^0.3.0 | Python bindings for llama.cpp LLM inference |
| [pyaudio](https://pypi.org/project/PyAudio/) | ^0.2.14 | Audio capture and playback |
| [sounddevice](https://pypi.org/project/sounddevice/) | ^0.5.0 | Alternative audio I/O |
| [numpy](https://numpy.org/) | ^1.26.0 | Audio buffer processing |
| [bcrypt](https://pypi.org/project/bcrypt/) | ^4.2.0 | Password hashing |
| [wyoming](https://pypi.org/project/wyoming/) | ^1.5.0 | Wyoming protocol for Home Assistant integration |

### Dev dependencies

| Library | Version | Purpose |
|---|---|---|
| [pytest](https://docs.pytest.org/) | ^8.3.0 | Testing framework |
| [httpx](https://www.python-httpx.org/) | ^0.27.0 | Async HTTP client for testing |

### System packages (installed on the Pi)

| Package | Purpose |
|---|---|
| `portaudio19-dev` | Audio I/O library (required by PyAudio) |
| `libsndfile1` | Audio file reading/writing |
| `ffmpeg` | Audio format conversion |
| `cmake`, `build-essential` | Compiling whisper.cpp and llama.cpp |
| `Python 3.11+` | Python runtime |

---

## Quickstart — Laptop (development)

**1. Clone the repository**

```bash
git clone https://github.com/Rasp-pvtora/Raspberry_Projects.git
cd "Raspberry_Projects/Smart & Security Projects/Set Up AI-Powered Voice Service"
```

**2. Create the `.env` file from the template**

```bash
# Linux / macOS
cp .env.default .env

# Windows
copy .env.default .env
```

Edit `.env` and set your values (at minimum, change `SESSION_SECRET` and `ADMIN_PASSWORD`).

**3. Create a virtual environment and install dependencies**

```bash
python -m venv venv
source venv/bin/activate    # Linux/macOS
venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

**4. Download AI models**

```bash
bash scripts/download-models.sh
```

This downloads the default models (~3 GB total):
- Whisper `tiny` for STT
- Piper `en_US-lessac-medium` voice for TTS
- TinyLlama 1.1B Q4 for conversational AI
- OpenWakeWord default model

**5. Start the development server**

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 3000
```

**6. Open the dashboard**

Navigate to `http://localhost:3000` in your browser.

- **Username:** `admin` (or whatever you set in `.env`)
- **Password:** `changeme` (or whatever you set in `.env`)

> **Note:** On a laptop without a microphone, the voice pipeline will not activate. The dashboard, settings, and conversation history pages work fully. You can test TTS output through the dashboard.

---

## Environment configuration (.env)

Copy `.env.default` to `.env` and edit it. **Never commit `.env` to git.**

| Variable | Default | Description |
|---|---|---|
| `PORT` | `3000` | Dashboard web server port |
| `HOST` | `0.0.0.0` | Listen address |
| `SESSION_SECRET` | `CHANGE_ME...` | Random string for session encryption |
| `ADMIN_USERNAME` | `admin` | Dashboard login username |
| `ADMIN_PASSWORD` | `changeme` | Dashboard login password |
| `WAKE_WORD` | `hey_jarvis` | Wake word to activate the assistant. Options: `hey_jarvis`, `alexa`, `ok_google`, or custom |
| `WAKE_WORD_SENSITIVITY` | `0.5` | Wake word detection sensitivity (0.0–1.0) |
| `STT_MODEL` | `tiny` | Whisper model size: `tiny`, `base`, `small` (larger = more accurate, slower) |
| `STT_LANGUAGE` | `en` | STT language code (e.g., `en`, `de`, `fr`, `it`, `es`) |
| `LLM_MODEL_PATH` | `./models/llm/tinyllama-1.1b-q4.gguf` | Path to the GGUF LLM model file |
| `LLM_MAX_TOKENS` | `256` | Maximum tokens for LLM response |
| `LLM_CONTEXT_SIZE` | `2048` | LLM context window size |
| `TTS_VOICE` | `en_US-lessac-medium` | Piper TTS voice model name |
| `TTS_LANGUAGE` | `en_US` | TTS language (must match the voice model) |
| `AUDIO_INPUT_DEVICE` | `default` | Microphone device name or index |
| `AUDIO_OUTPUT_DEVICE` | `default` | Speaker device name or index |
| `AUDIO_SAMPLE_RATE` | `16000` | Audio sample rate in Hz |
| `WYOMING_ENABLED` | `false` | Enable Wyoming protocol server for Home Assistant |
| `WYOMING_PORT` | `10400` | Wyoming protocol listen port |
| `GPIO_ENABLED` | `false` | Enable GPIO control via voice commands |
| `VOXTRAL_REMOTE_URL` | `` | Optional: URL of remote Voxtral TTS server (e.g., `http://gpu-server:8000`) |

---

## Voice pipeline overview

The voice assistant uses a fully local, open-source pipeline with no cloud dependencies:

| Stage | Component | Model/Tool | What it does |
|---|---|---|---|
| **1. Wake word** | [OpenWakeWord](https://github.com/dscripka/openWakeWord) | Pre-trained wake word models | Listens continuously for the wake phrase (e.g., "Hey Jarvis") |
| **2. Speech-to-Text** | [Whisper.cpp](https://github.com/ggerganov/whisper.cpp) | `tiny` / `base` / `small` | Converts spoken audio to text after wake word triggers |
| **3. Conversational AI** | [llama.cpp](https://github.com/ggerganov/llama.cpp) | TinyLlama 1.1B / Phi-3-mini / Gemma-2B (Q4 quantized) | Generates a natural language response to the user's query |
| **4. Text-to-Speech** | [Piper TTS](https://github.com/rhasspy/piper) | 30+ language voice models | Converts the AI response to spoken audio |
| **5. Audio I/O** | PyAudio / sounddevice | USB microphone + speaker | Captures audio input and plays audio output |
| **6. Orchestration** | FastAPI + WebSocket | Python service | Coordinates the pipeline, serves the web dashboard |

**How a voice interaction works:**

```
User speaks → Mic captures audio
    → OpenWakeWord detects "Hey Jarvis"
    → Whisper.cpp transcribes speech to text
    → llama.cpp generates a response
    → Piper TTS converts response to speech
    → Speaker plays the audio response
    → Dashboard shows the conversation in real time
```

---

## Feature 1 — Wake word detection (OpenWakeWord)

The assistant listens continuously for a configurable wake word before activating.

- **Pre-trained wake words:** `hey_jarvis`, `alexa`, `ok_google`, `hey_mycroft`, and more.
- **Custom wake words:** Train your own wake word with ~50 audio samples using the OpenWakeWord training toolkit.
- **Low CPU usage:** The wake word engine uses a small neural network that runs efficiently on the Pi, consuming minimal CPU while waiting.
- **Configurable sensitivity:** Adjust `WAKE_WORD_SENSITIVITY` in `.env` (0.0–1.0) to balance between false activations and missed detections.

**From the dashboard:**
- Select the active wake word from a dropdown.
- Test wake word detection with a visual indicator.
- View wake word activation history.

---

## Feature 2 — Speech-to-Text (Whisper.cpp)

After the wake word triggers, the assistant records your speech and transcribes it.

- **Whisper.cpp** is a C/C++ port of OpenAI's Whisper model, optimized for CPU inference.
- **Model sizes** (set `STT_MODEL` in `.env`):

| Model | Size | Speed on Pi 4 | Accuracy | Recommended for |
|---|---|---|---|---|
| `tiny` | ~75 MB | ~1–2 sec | Good | Default, fastest response |
| `base` | ~145 MB | ~3–5 sec | Better | Balanced speed/accuracy |
| `small` | ~470 MB | ~8–12 sec | Best | Maximum accuracy, slower |

- **Multi-language:** Whisper supports 99 languages. Set `STT_LANGUAGE` in `.env`.
- **Auto-language detection:** Set `STT_LANGUAGE=auto` to let Whisper detect the spoken language (slightly slower).

---

## Feature 3 — Conversational AI (llama.cpp)

The transcribed text is sent to a local LLM for generating a natural response.

- **llama.cpp** runs quantized LLMs on CPU (no GPU required).
- **Recommended models for Raspberry Pi:**

| Model | Parameters | RAM Usage | Speed on Pi 4 (4 GB) | Notes |
|---|---|---|---|---|
| TinyLlama 1.1B Q4 | 1.1B | ~1 GB | ~5–8 tokens/sec | Default, fits in 4 GB RAM |
| Phi-3-mini Q4 | 3.8B | ~2.5 GB | ~2–4 tokens/sec | Better quality, needs 8 GB RAM |
| Gemma-2B Q4 | 2B | ~1.5 GB | ~3–5 tokens/sec | Good balance |

- **System prompt:** A configurable system prompt defines the assistant's personality and capabilities.
- **Plugin awareness:** The LLM knows about installed skills (GPIO, weather, timer) and can trigger them via structured output.
- **Conversation context:** The LLM maintains a rolling conversation context (configurable via `LLM_CONTEXT_SIZE`).

---

## Feature 4 — Text-to-Speech (Piper TTS)

The LLM's text response is converted to natural-sounding speech.

- **Piper TTS** is designed specifically for Raspberry Pi — extremely fast synthesis.
- **Performance:** Generates speech in real time on Pi 4 (faster than real-time on Pi 5).
- **30+ languages** with multiple voice options per language.
- **Voice quality levels:** `low`, `medium`, `high` — higher quality uses more CPU.
- **Sample voices (included with the project):**

| Voice | Language | Quality | Description |
|---|---|---|---|
| `en_US-lessac-medium` | English (US) | Medium | Clear male voice (default) |
| `en_US-amy-medium` | English (US) | Medium | Female voice |
| `de_DE-thorsten-medium` | German | Medium | Male voice |
| `fr_FR-siwis-medium` | French | Medium | Female voice |
| `it_IT-riccardo-medium` | Italian | Medium | Male voice |
| `es_ES-davefx-medium` | Spanish | Medium | Male voice |

**From the dashboard:**
- Select the active TTS voice from a dropdown.
- Preview any voice with a test phrase.
- Download additional voices from the Piper voice repository.

---

## Feature 5 — Web dashboard

A real-time web interface for monitoring and controlling the voice assistant.

| Section | Description |
|---|---|
| **Dashboard** | Live audio waveform, conversation feed, pipeline status, system stats |
| **Conversation History** | Searchable log of all voice interactions with timestamps and audio playback |
| **Settings** | Model selection (STT/LLM/TTS), language dropdown, wake word config, audio device selection |
| **System Monitor** | CPU temperature, memory usage, model memory footprint |

**Real-time features:**
- **Audio waveform** — live visualization of microphone input via WebSocket.
- **Conversation feed** — each voice interaction appears in real time (user said → assistant replied).
- **Pipeline status** — shows which stage is active (listening / transcribing / thinking / speaking).
- **Language dropdown** — switch the STT and TTS language on the fly from the dashboard. Available languages are populated from installed Piper voice models and Whisper language support.

---

## Wyoming Protocol — Modular voice AI architecture

The Wyoming Protocol is a modern, open standard for connecting voice AI components over the network. It was developed by the [Rhasspy](https://rhasspy.readthedocs.io/) / [Home Assistant](https://www.home-assistant.io/integrations/wyoming/) community to create a fully modular, distributed voice pipeline.

### What is the Wyoming Protocol?

Instead of running all voice components on a single device, Wyoming defines a simple TCP-based protocol that lets each component (wake word, STT, TTS, LLM) run as an independent service — possibly on different machines. Any Wyoming-compatible component can be swapped in or out without changing the rest of the pipeline.

### Why Wyoming Protocol is powerful

🔒 **Privacy-first (No cloud, No Google/Alexa)**
Every component runs locally. Your voice data never leaves your network. No accounts, no subscriptions, no data harvesting. You own your voice pipeline end-to-end.

🧩 **Fully modular (swap any component)**
Replace Whisper with a faster STT model. Swap Piper voices without touching the STT or LLM. Upgrade the LLM independently. Each component is a standalone service that speaks the Wyoming protocol — mix and match freely.

⚡ **Distributed computing (heavy models on server, lightweight satellites)**
Run the heavy LLM and STT models on a powerful server (or desktop PC), while a lightweight Raspberry Pi Zero acts as a voice satellite with just a microphone and speaker. The Pi sends audio to the server via Wyoming, gets the response, and plays it. This allows deploying voice assistants in every room with minimal hardware per room.

🤖 **Hackable (Python automation, N8N workflows, AI pipelines, edge computing)**
Wyoming services are plain TCP servers — easy to integrate with Python scripts, N8N automation workflows, Home Assistant automations, or custom AI pipelines. Build complex voice-triggered automations: "Hey Jarvis, turn on the lights and set the thermostat to 22 degrees" → triggers GPIO + HTTP calls.

### Wyoming architecture in this project

```
┌─────────────────────────┐      ┌────────────────────────────┐
│  Pi Zero (Satellite)    │      │  Pi 4/5 or Server          │
│  ┌───────────────────┐  │      │  ┌──────────────────────┐  │
│  │ Microphone + Speaker│  │ Wyoming │ │ Whisper.cpp (STT)    │  │
│  │ OpenWakeWord       │──────────►│ llama.cpp (LLM)      │  │
│  │ Audio I/O          │◄──────────│ Piper TTS            │  │
│  └───────────────────┘  │ TCP     │ └──────────────────────┘  │
└─────────────────────────┘      └────────────────────────────┘
```

Enable Wyoming in `.env` with `WYOMING_ENABLED=true` and `WYOMING_PORT=10400`.

---

## Voxtral-4B-TTS — Premium TTS upgrade path

### What is Voxtral-4B-TTS?

[Voxtral-4B-TTS-2603](https://huggingface.co/mistralai/Voxtral-4B-TTS-2603) is an open-weights, enterprise-grade text-to-speech model by Mistral AI. It delivers:

- **Realistic, expressive speech** with natural prosody and emotional range.
- **20 preset voices** with easy adaptation to new voices.
- **9 languages:** English, French, Spanish, German, Italian, Portuguese, Dutch, Arabic, and Hindi.
- **24 kHz audio output** in WAV, PCM, FLAC, MP3, AAC, and Opus formats.
- **Very low latency** with streaming support.

Voxtral produces significantly more natural and expressive speech than Piper TTS, making it ideal for production voice agents.

### Why it cannot run on a Raspberry Pi

Voxtral-4B-TTS is a 4-billion parameter model that requires:

- A **GPU with ≥16 GB VRAM** (benchmarked on NVIDIA H200).
- **vLLM** inference engine with CUDA support.
- **BF16 (bfloat16) tensor format** — not supported on ARM CPUs.

A Raspberry Pi does not have a discrete GPU, CUDA support, or enough memory. **Voxtral cannot run locally on a Pi — not even with quantization.**

### How to use Voxtral with this project (remote server)

If you have access to a GPU server (local or cloud), you can run Voxtral as a remote TTS service and connect the Pi to it over the network:

1. **On the GPU server:** Run Voxtral via vLLM:
   ```bash
   vllm serve mistralai/Voxtral-4B-TTS-2603 --omni
   ```
   This starts an OpenAI-compatible API on port 8000.

2. **On the Pi:** Set the remote URL in `.env`:
   ```ini
   VOXTRAL_REMOTE_URL=http://gpu-server:8000
   ```

3. The voice pipeline will use Voxtral for TTS instead of Piper when the remote URL is configured. If the server is unreachable, it falls back to Piper automatically.

### Investment required

| Option | Cost | Notes |
|---|---|---|
| **Local GPU server** | $2,000 – $5,000+ | NVIDIA RTX 4090 (24 GB) or A6000 (48 GB) |
| **Cloud GPU instance** | $1 – $5/hour | AWS p4d, GCP A100, Lambda Labs, RunPod |
| **Hugging Face Inference** | Pay-per-request | Hosted API (when available) |

> **Voxtral is a nice-to-have feature upgrade** for users who want premium voice quality and are willing to invest in GPU hardware or a cloud GPU service. The default Piper TTS provides good voice quality for free, running entirely on the Pi.

---

## Home Assistant integration

This project integrates with [Home Assistant](https://www.home-assistant.io/) via the Wyoming protocol, turning the Pi into a voice satellite.

**Setup:**
1. Enable Wyoming in `.env`: `WYOMING_ENABLED=true`
2. In Home Assistant, go to **Settings → Devices & Services → Add Integration → Wyoming Protocol**.
3. Enter the Pi's IP address and Wyoming port (default `10400`).
4. The Pi appears as a voice assistant device in Home Assistant.

**What you can do:**
- Use the Pi as a room-level voice satellite for Home Assistant.
- Trigger Home Assistant automations with voice commands.
- Control smart home devices ("turn on the living room lights").
- All processing stays local (Whisper + Piper run on the Pi or a local server).

---

## Multi-language support

The voice assistant supports multiple languages, selectable from the dashboard dropdown:

| Language | STT (Whisper) | TTS (Piper) | LLM | Status |
|---|---|---|---|---|
| English | ✅ | ✅ (multiple voices) | ✅ | Full support |
| German | ✅ | ✅ | ✅ | Full support |
| French | ✅ | ✅ | ✅ | Full support |
| Italian | ✅ | ✅ | ✅ | Full support |
| Spanish | ✅ | ✅ | ✅ | Full support |
| Portuguese | ✅ | ✅ | ✅ | Full support |
| Dutch | ✅ | ✅ | ✅ | Full support |
| Polish | ✅ | ✅ | ✅ | Full support |
| Russian | ✅ | ✅ | ✅ | Full support |
| Chinese | ✅ | ✅ | Partial | STT + TTS work; LLM may not respond well |
| Arabic | ✅ | ✅ | Partial | STT + TTS work; LLM quality varies |

**How to switch language:**
1. Open the dashboard → Settings.
2. Select the target language from the **Language** dropdown.
3. The system automatically updates the STT language, selects a matching TTS voice, and adjusts the LLM system prompt.
4. Additional Piper voice models can be downloaded from the Settings page.

---

## Skill and plugin system

Custom voice skills let you extend the assistant with domain-specific actions.

**Built-in skills:**

| Skill | Trigger phrase | Action |
|---|---|---|
| **GPIO Control** | "Turn on GPIO 17" / "Toggle the relay" | Set GPIO pins HIGH/LOW (requires `GPIO_ENABLED=true`) |
| **System Info** | "What's the CPU temperature?" / "How much memory is free?" | Read Pi system stats |
| **Timer** | "Set a timer for 5 minutes" | Countdown timer with audio alert |
| **Weather** | "What's the weather?" | Read weather from a local sensor or API |

**Creating a custom skill:**
1. Create a Python file in `src/plugins/` (e.g., `my_skill.py`).
2. Define trigger phrases and the action function.
3. The skill is auto-discovered and registered with the LLM's system prompt.

---

## Authentication

The web dashboard is protected by session-based authentication.

- Credentials are stored in `.env` (`ADMIN_USERNAME` and `ADMIN_PASSWORD`).
- Login attempts are rate-limited (10 attempts per 15 minutes) to prevent brute-force.
- Sessions expire after 24 hours.
- Passwords can be changed from **Settings → Change Password** in the dashboard.

---

## How to deploy to Raspberry Pi

Your SSH config is already set up at `~/.ssh/config`:

```
Host rasp-pi
    HostName 192.168.216.90
    User pi
    Port 22
    IdentityFile ~/.ssh/id_ed25519
```

**Method A — Use the deploy script (recommended)**

From the project directory on your laptop:

```bash
bash deploy/deploy_to_pi.sh rasp-pi /home/pi/Projects/VoiceAssistant
```

This will:
1. Create the remote directory.
2. Rsync all project files (excludes `venv`, `.env`, `.git`, `models/`).
3. Create a virtual environment and install dependencies on the Pi.
4. Create `.env` from `.env.default` if it does not exist.

**Method B — Manual rsync**

```bash
rsync -avz --delete \
  --exclude='venv/' \
  --exclude='.env' \
  --exclude='.git/' \
  --exclude='models/' \
  ./ \
  rasp-pi:/home/pi/Projects/VoiceAssistant/

ssh rasp-pi "cd /home/pi/Projects/VoiceAssistant && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
```

---

## How to run on the Raspberry Pi

**1. SSH into the Pi**

```bash
ssh rasp-pi
```

**2. Go to the project directory**

```bash
cd /home/pi/Projects/VoiceAssistant
```

**3. Edit the .env file**

```bash
nano .env
```

Set `SESSION_SECRET` to a random string and change `ADMIN_PASSWORD`.

**4. Set up audio devices**

```bash
sudo bash scripts/setup-audio.sh
```

This configures ALSA for the USB microphone and speaker.

**5. Download AI models**

```bash
bash scripts/download-models.sh
```

**6. Start the voice assistant**

```bash
source venv/bin/activate
python app.py
```

Access the dashboard at `http://192.168.216.90:3000`.

**7. (Optional) Run as a systemd service**

```bash
sudo nano /etc/systemd/system/voice-assistant.service
```

```ini
[Unit]
Description=AI Voice Assistant
After=network-online.target sound.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Projects/VoiceAssistant
ExecStart=/home/pi/Projects/VoiceAssistant/venv/bin/python app.py
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable voice-assistant
sudo systemctl start voice-assistant
```

---

## Real-world applications

| Application | Who uses it | Why |
|---|---|---|
| **Private home assistant** | Privacy-conscious homeowners | Voice control without sending data to Google/Amazon; runs fully offline |
| **Smart home voice satellite** | Home Assistant users | Add voice control to every room with a cheap Pi Zero + mic + speaker |
| **Accessibility aid** | People with mobility impairments | Voice-controlled GPIO (lights, doors, appliances) without needing a phone or screen |
| **Language learning tool** | Students, polyglots | Practice conversation in 30+ languages with instant TTS feedback |
| **Elderly care companion** | Caregivers, elderly | Simple voice interface for reminders, weather, and emergency alerts |
| **Maker/IoT voice controller** | Hardware hobbyists | Voice-trigger custom GPIO actions, sensor readings, and automations |
| **Classroom lab** | Teachers, students | Hands-on AI/ML education — STT, LLM, and TTS in one project |
| **Offline field assistant** | Researchers, field workers | Voice assistant that works without internet in remote locations |
| **Custom kiosk / reception** | Small businesses | Voice-powered information kiosk with custom skills for FAQs |

---

## Security notes

- **Change the default password immediately** after first login. Use the Settings page or edit `.env`.
- **Generate a strong `SESSION_SECRET`** — run: `python -c "import secrets; print(secrets.token_hex(32))"`
- **The `.env` file contains sensitive data.** It is in `.gitignore` and should never be committed. Protect it with file permissions: `chmod 600 .env`
- **Rate limiting** is enabled on the login endpoint (10 attempts per 15 minutes).
- **Audio data stays local.** No audio is sent to any cloud service. All STT, LLM, and TTS processing happens on-device (or on your own GPU server if Voxtral is configured).
- **Model files are large.** The `models/` directory is in `.gitignore`. Download models with the provided script.
- **Wyoming protocol** listens on a TCP port. If exposed to untrusted networks, ensure firewall rules are in place.
- **GPIO skills require root on the Pi.** Run the app with appropriate permissions or add the `pi` user to the `gpio` group.
- See [docs/threat_model.md](docs/threat_model.md) for the full threat analysis.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| No audio input detected | Check USB mic is connected: `arecord -l`. Set the correct device in `.env` (`AUDIO_INPUT_DEVICE`). Run `bash scripts/setup-audio.sh`. |
| No audio output | Check speaker is connected: `aplay -l`. Test with `aplay /usr/share/sounds/alsa/Front_Center.wav`. |
| Wake word not triggering | Lower `WAKE_WORD_SENSITIVITY` (e.g., `0.3`). Ensure the microphone is picking up audio (check dashboard waveform). |
| STT transcription is inaccurate | Upgrade the Whisper model: `STT_MODEL=base` or `STT_MODEL=small`. Speak closer to the microphone. |
| LLM response is slow | Use a smaller model (TinyLlama). Reduce `LLM_MAX_TOKENS`. Upgrade to Pi 5 with 8 GB RAM. |
| LLM response is low quality | Upgrade to Phi-3-mini or Gemma-2B (requires 8 GB RAM). Adjust the system prompt. |
| TTS voice sounds robotic | Switch to a `high` quality Piper voice. Download a different voice from Settings. |
| `pip install` fails | Ensure Python 3.11+ is installed: `python --version`. Install build tools: `sudo apt install cmake build-essential portaudio19-dev`. |
| Model download fails | Check internet connection. Retry: `bash scripts/download-models.sh`. Models can also be downloaded manually from Hugging Face. |
| Wyoming not discoverable | Verify `WYOMING_ENABLED=true` and the port is open. Check firewall: `sudo ufw status`. |
| Dashboard not loading | Check if the server is running. Verify the Pi's IP and port. Check `python app.py` output for errors. |
| Out of memory | Close other services. Use smaller models. Pi 4 with 4 GB can run `tiny` + TinyLlama. For larger models, use Pi 5 with 8 GB. |

---

## Where to next

- See [TSD.md](TSD.md) for the full technical specification, architecture, and development phases.
- See [task.md](task.md) for the engineering checklist with step-by-step implementation tasks.
- See [docs/threat_model.md](docs/threat_model.md) for the threat model and mitigations.
