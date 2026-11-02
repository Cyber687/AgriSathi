# 🌾 AgriSathi
### Multilingual Agricultural Advisory Chatbot for Indian Farmers

AgriSathi is a multilingual, voice-enabled agricultural advisory chatbot designed to help Indian farmers access agricultural information through a simple and accessible interface.

The system combines a structured agricultural knowledge base, rule-based recommendations, live weather information, mandi market prices, and safety validation to provide useful and responsible agricultural guidance.

Its primary goal is to make agricultural information easier to access while avoiding unsupported claims and unsafe chemical recommendations.

---

**Team Members:**
- Karan Kumar 
- Aniket Nanda 
- Rahi Kumar Kushwaha 

## 📌 Table of Contents

1. Project Overview
2. Problem Statement
3. Objectives
4. Features
5. Technology Stack
6. System Architecture
7. Project Structure
8. Knowledge Base
9. Safety and Verification
10. Prerequisites
11. Installation
12. Environment Configuration
13. Running the Local LLM
14. Running AgriSathi
15. Voice Features
16. API Integrations
17. Limitations
18. Future Enhancements
19. Responsible Use
20. License

---

## 1. Project Overview

Agriculture is an important part of India's economy, but farmers may face difficulties accessing reliable and understandable information about crop management, fertilizer use, pest control, irrigation, weather, and market prices.

AgriSathi aims to address this problem through an easy-to-use chatbot that supports English and Hindi.

The application uses structured agricultural information and deterministic rules to identify relevant information. External services can provide weather conditions and mandi prices, while a safety layer checks recommendations before they are presented to users.

The local language model can assist with understanding or rephrasing queries, but it must not invent agricultural facts or override safety checks.

### Project Goals

- Improve access to agricultural information.
- Support English and Hindi queries.
- Provide crop-specific information.
- Assist with fertilizer and irrigation information.
- Identify relevant pest-management information.
- Retrieve weather information using an external API.
- Retrieve mandi prices using a government data API.
- Support speech-to-text and text-to-speech.
- Require evidence and verification for agricultural recommendations.
- Prevent unverified chemical dosages from being presented as advice.

---

## 2. Problem Statement

Farmers may encounter several challenges:

- Difficulty finding agricultural information in a familiar language.
- Limited access to timely weather information.
- Difficulty comparing market prices.
- Uncertainty about crop-specific fertilizer requirements.
- Difficulty identifying crop pests and diseases.
- Exposure to unreliable pesticide recommendations.
- Limited access to digital agricultural advisory services.

AgriSathi proposes a unified chatbot interface that brings together agricultural knowledge, live data services, and safety checks.

The quality of its advice depends on the accuracy, completeness, and verification of its underlying data.

---

## 3. Objectives

The primary objectives are:

1. Develop a multilingual agricultural chatbot.
2. Maintain a structured knowledge base for crops, fertilizers, pests, irrigation, and chemicals.
3. Use a rule-based engine to retrieve relevant agricultural information.
4. Integrate weather and mandi market-price services.
5. Provide voice input and spoken responses.
6. Validate chemical recommendations and dosage information against appropriate evidence.
7. Display source information and safety warnings.
8. Use a local language model where appropriate without allowing it to bypass validation.
9. Provide a modular architecture that can be extended in the future.

---

## 4. Features

### 🌱 Crop Information

Provides relevant information from the crop knowledge base, such as crop names, growing seasons, and soil requirements.

### 🧪 Fertilizer Information

Retrieves fertilizer-related information associated with crops.

Specific application rates must not be presented as verified recommendations unless the relevant evidence supports them.

### 🐛 Pest Management

Retrieves pest and disease information and associated management information from the knowledge base.

Unverified chemical treatments must not be presented as approved advice.

### 💧 Irrigation Guidance

Provides available information about irrigation requirements and methods.

The system should distinguish verified recommendations from incomplete or unverified dataset entries.

### 🌦️ Weather Information

Connects to the OpenWeather API to retrieve weather information for a requested location.

Weather availability depends on API credentials, connectivity, and service availability.

### 🏪 Mandi Market Prices

Uses the data.gov.in API to retrieve agricultural market-price records.

The results depend on the available dataset, crop matching, market filters, and API response.

### 🎙️ Voice Interaction

The voice subsystem supports:

- Speech-to-text using faster-whisper.
- Text-to-speech using Edge TTS.
- English and Hindi voice configuration.

Speech recognition can run locally after the required model is available. Edge TTS requires internet connectivity.

### 🛡️ Safety Validation

The safety subsystem is intended to:

- Validate chemical recommendations.
- Check dosage information.
- Check crop-pest compatibility.
- Validate source evidence.
- Sanitize generated responses.
- Block recommendations that fail required checks.

These protections must be tested through integration testing before the application is considered production-ready.

---

## 5. Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python |
| Frontend | HTML, CSS, JavaScript |
| Local language model | Sarvam GGUF model |
| Local LLM server | llama.cpp |
| Knowledge storage | JSON |
| Weather service | OpenWeather API |
| Mandi price service | data.gov.in API |
| HTTP requests | Requests |
| Environment configuration | python-dotenv |
| Speech recognition | faster-whisper |
| Text-to-speech | Edge TTS |
| Code formatting | Black |
| Static analysis | Ruff |
| Development environment | Visual Studio Code |

---

## 6. System Architecture

The intended processing flow is:

```text
                 ┌─────────────────────┐
                 │   Farmer / User     │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Frontend Interface  │
                 │ HTML, CSS, JavaScript│
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │      main.py        │
                 │ Application Entry   │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │    Query Parser     │
                 │ Language and Intent │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │     Rule Engine     │
                 └──────────┬──────────┘
                            │
             ┌──────────────┼──────────────┐
             │              │              │
             ▼              ▼              ▼
      ┌────────────┐ ┌────────────┐ ┌────────────┐
      │ Knowledge  │ │   Weather  │ │   Mandi    │
      │    Base    │ │   Service  │ │   Service  │
      └─────┬──────┘ └─────┬──────┘ └─────┬──────┘
            └──────────────┼──────────────┘
                           │
                           ▼
                 ┌─────────────────────┐
                 │ Recommendation      │
                 │ Engine              │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │     Safety Engine   │
                 │ Validation and     │
                 │ Response Sanitizing │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Approved Response   │
                 │ or Safety Warning   │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Frontend / Voice    │
                 └─────────────────────┘

For fertilizer records, the response now:
- Splits a recorded N:P:K ratio into Nitrogen (N), Phosphorus (P), and Potassium (K).
- Shows the nutrient basis only when the knowledge-base record provides it.
- Clearly states when units/application dosage/timing are missing.
- Displays soil-test and safety notes from the record.
- Does not invent a kg/ha, kg/acre, fertilizer-product amount, or application schedule.


# AgriSathi multilingual integration update

This is an integration update to merge into your existing AgriSathi project, not a complete replacement for every project file. Your full knowledge base, rule engine, config, and other safety validators were not all available in the uploaded source set, so they are not fabricated here.

## Included
- `main.py`: updated language acceptance and local GGUF translation hook. Translation happens before safety validation.
- `frontend/index.html`, `style.css`, `script.js`: language dropdown and selected-language request payload.
- `services/local_gguf_translator.py`: lazy local GGUF inference using `llama-cpp-python`.
- `engine/query_parser.py`, `engine/recommendation.py`, `safety/safety_engine.py`: copies of available modules for convenience.
- `knowledge_base/fertilizers.json`, `irrigation.json`, `pests.json`: available data files from the current project context.

## Install/merge
1. Back up your current project.
2. Copy the included files into the matching folders, replacing only the corresponding files.
3. Keep your existing `engine/rule_engine.py`, `config/`, all other knowledge-base JSON files, and safety validator modules; they are not included if they were not provided.
4. Install the optional local model runtime into your existing environment: `pip install -r requirements-multilingual.txt`.
5. Set `AGRISATHI_GGUF_PATH` to the actual GGUF file path. Default guesses are `models/sarvam-1-v0.5-Q8_0.gguf` and `sarvam-1-v0.5-Q8_0.gguf` in the project root.
6. Restart backend and hard-refresh the browser.

## Language behavior
- English and Hindi use the existing deterministic recommendation templates.
- Punjabi, Bengali, Marathi, Gujarati, Tamil and Telugu are exposed in the UI and use local GGUF translation for candidate response text.
- If the model is missing or fails to load, the backend returns an explicit error for those additional languages instead of silently showing English.
- Model language quality depends on the exact GGUF. The bundle does not include the model file because it is large and you already have it locally.
- Translation does not independently verify agricultural facts. The existing safety engine remains enabled and is run after translation.

## Windows model installation notes
`llama-cpp-python` may need Visual Studio C++ Build Tools or a compatible prebuilt wheel. If installation fails, retain English/Hindi while setting up the runtime; do not disable safety checks.

## Validation
Python files are syntax-checked. Full runtime integration cannot be guaranteed without your remaining project files and actual GGUF model.
