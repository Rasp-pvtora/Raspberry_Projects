# Technical Specification Description (TSD)

This document describes the scope, minimum viable features, nice-to-have features, architecture, security considerations, suggested stack, and development plan for **Set Up AI-Powered Voice Service**.

---

## 1. Scope

This project builds a fully local, privacy-first AI voice assistant on a Raspberry Pi. It combines open-source models for wake word detection, speech-to-text, conversational AI, and text-to-speech into a single, cohesive voice pipeline. A web dashboard provides configuration, monitoring, and conversation history. The system supports the Wyoming protocol for Home Assistant integration and distributed computing.

**Key goals:**
- 100% local processing — no cloud, no accounts, no data harvesting.
- Modular pipeline — each component (STT, TTS, LLM) can be replaced independently.
- Multi-language support with dashboard-based language switching.
- Wyoming protocol compatibility for Home Assistant voice satellites.
- Extensible skill/plugin system for GPIO control and custom automations.

---

## 2. Minimum Viable Features (MVP)

### 2.1 Voice Pipeline

| Stage | Component | Model/Tool | Description |
|---|---|---|---|
| **Wake word** | [OpenWakeWord](https://github.com/dscripka/openWakeWord) | Pre-trained models | Continuous listening for configurable wake phrase ("Hey Jarvis", etc.) |
| **Speech-to-Text** | [Whisper.cpp](https://github.com/ggerganov/whisper.cpp) | `tiny` / `base` / `small` | Converts spoken audio to text; 99 languages; runs on CPU |
| **Conversational AI** | [llama.cpp](https://github.com/ggerganov/llama.cpp) | TinyLlama 1.1B Q4 (default) | Generates natural language responses; quantized for Pi |
| **Text-to-Speech** | [Piper TTS](https://github.com/rhasspy/piper) | 30+ language voice models | Converts text to speech; real-time on Pi 4; low latency |
| **Audio I/O** | PyAudio / sounddevice | USB mic + speaker | Audio capture and playback |
| **Orchestration** | FastAPI + WebSocket | Python service | Pipeline coordination, web dashboard, real-time updates |

- **Pipeline flow:** Mic → OpenWakeWord (wake detection) → Whisper (STT) → llama.cpp (LLM) → Piper (TTS) → Speaker.
- **Configurable models:** All models are configurable via `.env`. Users can swap STT model size, LLM model, and TTS voice without code changes.
- **Audio device selection:** Configurable input/output audio devices in `.env` and from the dashboard.
- **Conversation context:** Rolling conversation history for the LLM (configurable context size).

### 2.2 Web Dashboard (FastAPI + Jinja2 + WebSocket)

- **Authentication:** Session-based login with credentials stored in `.env`. Rate-limited login endpoint (10 attempts per 15 min).
- **Layout:** Dark-themed sidebar navigation with pages for Dashboard, Settings, and Conversation History.
- **Dashboard page:**
  - Live audio waveform visualization (microphone input via WebSocket).
  - Real-time conversation feed (user said → assistant replied).
  - Pipeline status indicator (listening / transcribing / thinking / speaking).
  - System stats (CPU temperature, memory usage, model memory footprint).
- **Settings page:**
  - Language dropdown — switch STT and TTS language on the fly.
  - Model selection — choose Whisper model size, LLM model, TTS voice.
  - Wake word configuration — select wake word, adjust sensitivity.
  - Audio device selection — choose microphone and speaker.
  - Download additional Piper voice models from the repository.
  - Edit all `.env` variables.
- **Conversation History page:**
  - Searchable log of all voice interactions with timestamps.
  - Audio playback for each interaction.

### 2.3 Multi-Language Support

- Language selectable from dashboard dropdown.
- STT (Whisper) supports 99 languages.
- TTS (Piper) supports 30+ languages with multiple voices per language.
- Language switch updates STT language, TTS voice, and LLM system prompt automatically.
- Additional Piper voice models downloadable from the Settings page.

### 2.4 Wyoming Protocol Integration

- Wyoming protocol server (`WYOMING_ENABLED=true` in `.env`).
- Exposes STT and TTS as Wyoming-compatible services on a configurable TCP port.
- Discoverable by Home Assistant for voice satellite integration.
- Distributed computing: heavy models on a server, lightweight Pi Zero as satellite.

### 2.5 Skill and Plugin System

- **GPIO Control:** Voice commands to set GPIO pins HIGH/LOW (e.g., "Turn on GPIO 17").
- **System Info:** Voice query for CPU temperature, memory usage, uptime.
- **Timer:** Set countdown timers with audio alerts.
- **Weather:** Read weather from a local sensor or configured API.
- **Auto-discovery:** Skills in `src/plugins/` are auto-registered with the LLM's system prompt.
- **Custom skills:** Users create a Python file with trigger phrases and an action function.

### 2.6 Model Management

- `scripts/download-models.sh` downloads default models (~3 GB total).
- Model manager service handles model downloads, versioning, and disk usage.
- `models/` directory is in `.gitignore` — not committed.
- Settings page shows installed models with size and status.

### 2.7 Environment Configuration

- All configuration via `.env` file (created from `.env.default` template).
- `.env` is in `.gitignore` and never committed.
- Settings page provides a web-based editor for all `.env` variables.

### 2.8 Deployment

- `deploy/deploy_to_pi.sh` script: rsync files to the Pi (via `rasp-pi` SSH alias at `192.168.216.90`), create venv, install dependencies, create `.env` from template.
- Systemd service file for auto-start on boot.
- `scripts/setup-audio.sh` for ALSA audio device configuration.

---

## 3. Nice-to-Have Features

These features require paid third-party services, significant GPU hardware investment, or substantially more complexity.

### 3.1 Voxtral-4B-TTS Remote Server (Premium TTS)

- **What:** [Voxtral-4B-TTS-2603](https://huggingface.co/mistralai/Voxtral-4B-TTS-2603) by Mistral AI — an enterprise-grade, open-weights TTS model with realistic, expressive speech across 9 languages, 20 preset voices, and 24 kHz audio output.
- **Why it cannot run on the Pi:** Requires a GPU with ≥16 GB VRAM (benchmarked on NVIDIA H200), vLLM with CUDA, and BF16 tensor format. None of this is available on a Raspberry Pi.
- **Integration:** The Pi connects to a remote Voxtral server over the network (`VOXTRAL_REMOTE_URL` in `.env`). Falls back to Piper TTS if the server is unreachable.
- **Investment required:**
  - Local GPU server: $2,000 – $5,000+ (NVIDIA RTX 4090 or A6000).
  - Cloud GPU instance: $1 – $5/hour (AWS, GCP, Lambda Labs, RunPod).
  - Hugging Face Inference API: pay-per-request (when available).
- **License:** CC BY-NC 4.0 (non-commercial use; commercial use requires separate licensing from Mistral AI).

### 3.2 Cloud STT Fallback

- Use cloud STT services (Google Cloud Speech, Azure Speech, Deepgram) as a fallback when Whisper accuracy is insufficient.
- Requires API keys and incurs per-request costs.

### 3.3 Advanced Wake Word Training

- Train fully custom wake words with neural network fine-tuning.
- Requires a dataset of ~500+ audio samples and GPU training time.

### 3.4 Multi-Room Audio

- Multiple Pi satellites connected via Wyoming to a central server.
- Room-aware context (e.g., "turn on the light" → knows which room the speaker is in).
- Requires additional Pi Zero + mic/speaker per room.

### 3.5 Emotion Detection

- Analyze the user's tone of voice (angry, happy, sad) and adjust the assistant's response accordingly.
- Requires additional ML model and training data.

---

## 4. High-Level Architecture

```
                      ┌────────────────────────────────────────────────────┐
                      │            Raspberry Pi                            │
                      │                                                    │
  Browser ─HTTP────► │  FastAPI (port 3000)                                │
  Browser ──WS─────► │  ├── Session auth + rate limiting                   │
                      │  ├── Jinja2 templates (dashboard, settings, etc.)  │
                      │  ├── REST API (/api/settings, /api/conversation)   │
                      │  ├── WebSocket (live waveform + conversation)      │
                      │  └── Static files (/static)                        │
                      │                                                    │
                      │  Voice Pipeline:                                    │
                      │  ┌──────────────────────────────────────────┐      │
                      │  │ Microphone → OpenWakeWord (wake detect)  │      │
                      │  │          → Whisper.cpp (STT)             │      │
                      │  │          → llama.cpp (LLM)               │      │
                      │  │          → Piper TTS → Speaker           │      │
                      │  └──────────────────────────────────────────┘      │
                      │                                                    │
                      │  Wyoming Protocol Server (port 10400):             │
                      │  ├── STT handler (Whisper)                         │
                      │  └── TTS handler (Piper)                           │
                      │                                                    │
                      │  Services Layer:                                    │
                      │  ├── model_manager    → download/manage models     │
                      │  ├── language_service → multi-language config       │
                      │  ├── system_service   → temp, memory, disk         │
                      │  └── plugins/         → GPIO, timer, weather       │
                      │                                                    │
                      │  Optional Remote TTS (Voxtral):                    │
                      │  └── HTTP → gpu-server:8000/v1/audio/speech        │
                      └────────────────────────────────────────────────────┘
```

### Distributed Wyoming Architecture

```
                    ┌──────────────────┐
                    │  Server / Desktop │
                    │  (GPU optional)   │
                    │ ┌──────────────┐ │
                    │ │ Whisper STT  │ │
                    │ │ llama.cpp    │ │
                    │ │ Piper TTS    │ │
                    │ └──────────────┘ │
                    └────────┬─────────┘
                             │ Wyoming TCP
            ┌────────────────┼────────────────┐
            │                │                │
   ┌────────▼──────┐  ┌─────▼────────┐  ┌────▼───────────┐
   │ Pi Zero Room 1│  │ Pi Zero Room 2│  │ Pi 4 Room 3    │
   │ Mic + Speaker │  │ Mic + Speaker │  │ Mic + Speaker  │
   │ OpenWakeWord  │  │ OpenWakeWord  │  │ Full pipeline  │
   └───────────────┘  └──────────────┘  └────────────────┘
```

---

## 5. Security and Threat Model

**Primary assets:**
- Dashboard credentials and session tokens.
- Voice conversation history (potentially sensitive).
- LLM model files (large, expensive to re-download).
- GPIO pin access (can control physical hardware).
- `.env` file (contains passwords and secrets).

**Threats and mitigations:**

| Threat | Mitigation |
|---|---|
| Brute-force login | Rate limiting (10 attempts per 15 min); strong password in `.env` |
| Session hijacking | `httpOnly`, `sameSite` cookies; strong session secret |
| Voice data exfiltration | All processing is local; no cloud services; no outbound audio |
| Unauthorized wake word activation | Configurable sensitivity; audio only captured after wake word |
| Malicious voice commands (GPIO) | Voice commands are parsed by the LLM with a restrictive system prompt; GPIO requires explicit `GPIO_ENABLED=true` |
| Wyoming protocol abuse | Wyoming port should be firewalled to trusted network only |
| Model supply chain | Download models only from official sources (Hugging Face, Rhasspy); verify checksums |
| `.env` exposure | In `.gitignore`; `chmod 600` recommended |
| XSS via conversation history | HTML-escape all user/assistant text in templates |

See [docs/threat_model.md](docs/threat_model.md) for the complete analysis.

---

## 6. Suggested Tech Stack

| Component | Technology | Rationale |
|---|---|---|
| Backend | Python 3.11+ / FastAPI | Async, fast, native ML ecosystem |
| Templating | Jinja2 | Simple, server-side rendering, no build step |
| Real-time | WebSocket (native FastAPI) | Live audio waveform and conversation |
| Auth | Session-based + bcrypt | Simple, single-user device auth |
| Wake word | OpenWakeWord | Runs on Pi, customizable, no cloud |
| STT | Whisper.cpp (via whispercpp bindings) | C++ optimized, runs on Pi CPU |
| LLM | llama.cpp (via llama-cpp-python) | Quantized models on CPU, no GPU needed |
| TTS | Piper TTS | Designed for Pi, real-time synthesis, 30+ languages |
| Audio | PyAudio / sounddevice | Standard Python audio I/O |
| Wyoming | wyoming Python package | Home Assistant voice protocol |
| CSS | Custom dark theme | Lightweight, no framework dependency |

---

## 7. Development Phases & Concrete Steps

### Phase A — Project scaffold and audio I/O (Week 1)

1. Initialize Python project with `requirements.txt` and virtual environment.
2. Create `.env.default` template and `.gitignore`.
3. Implement FastAPI server with Jinja2 layout and sidebar navigation.
4. Implement session-based authentication (login, logout, middleware).
5. Create dark-themed CSS and login page.
6. Implement audio I/O module (microphone capture, speaker playback).
7. Create `scripts/setup-audio.sh` for ALSA configuration.

### Phase B — Voice pipeline (Week 1–2)

1. Implement OpenWakeWord integration (continuous listening, configurable wake word).
2. Implement Whisper.cpp STT integration (transcribe after wake word trigger).
3. Implement llama.cpp LLM integration (generate response from transcription).
4. Implement Piper TTS integration (synthesize speech from LLM response).
5. Wire the full pipeline: wake → STT → LLM → TTS → speaker.
6. Create `scripts/download-models.sh` for default model downloads.
7. Implement model manager service (list, download, delete models).

### Phase C — Web dashboard (Week 2)

1. Implement WebSocket server for real-time audio waveform and conversation.
2. Build Dashboard page with live waveform, conversation feed, pipeline status.
3. Build Settings page with model selection, language dropdown, wake word config.
4. Build Conversation History page with search and audio playback.
5. Implement language switching (STT + TTS + LLM prompt update).
6. Implement `.env` editor in Settings page.

### Phase D — Wyoming protocol and plugins (Week 2–3)

1. Implement Wyoming protocol server (STT and TTS handlers).
2. Test Home Assistant discovery and integration.
3. Implement GPIO skill plugin (voice-controlled pin toggle).
4. Implement system info, timer, and weather skill plugins.
5. Implement skill auto-discovery and LLM system prompt injection.
6. Create `scripts/setup-wyoming.sh` for Wyoming setup.

### Phase E — Multi-language and polish (Week 3)

1. Test and document multi-language support (STT + TTS + LLM).
2. Add voice model download from dashboard (Piper model repository).
3. Implement Voxtral remote TTS fallback (optional `VOXTRAL_REMOTE_URL`).
4. Write deployment script `deploy/deploy_to_pi.sh`.
5. Create systemd service file.
6. Test full deployment on Raspberry Pi 4 and Pi 5.

### Phase F — Documentation (Week 3–4)

1. Write `README.md` with full setup guide.
2. Write `TSD.md` (this document).
3. Write `task.md` engineering checklist.
4. Write `docs/threat_model.md`.
5. End-to-end testing on Pi.

---

## 8. Deliverables

- Full working voice pipeline (wake word → STT → LLM → TTS) running on Raspberry Pi.
- Web dashboard with live waveform, conversation history, and settings.
- Multi-language support with dashboard language dropdown.
- Wyoming protocol server for Home Assistant integration.
- Skill/plugin system with GPIO control, timer, weather, and system info.
- Optional Voxtral-4B-TTS remote server integration for premium TTS.
- Model management (download, select, delete models from dashboard).
- Setup scripts for audio, models, and Wyoming.
- Deploy script for Raspberry Pi (SSH alias: `rasp-pi` at `192.168.216.90`).
- `README.md`, `TSD.md`, `task.md`, `docs/threat_model.md`.
