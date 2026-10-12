# 🔊 Decibel

### AI-Powered Voice Deepfake Detection

**Decibel** is an AI-powered voice authenticity project designed to help identify AI-generated and manipulated speech. By analyzing audio signals and learning patterns associated with synthetic voices, Decibel aims to make voice-based fraud easier to detect and understand.

Built for the **Android Club VIT Chennai Hacktoberfest 2026 Hack Day — Best Use of Gemma 4** track.

---

## 🎯 The Problem

AI-generated voices are becoming increasingly realistic, making voice cloning and impersonation harder to recognize. These technologies can be misused for fraudulent calls, identity impersonation, and social engineering attacks.

Traditional detection approaches can struggle to generalize across different recording conditions, audio compression, and voice-generation techniques.

Decibel aims to address this challenge through AI-driven audio analysis and accessible voice authenticity checks.

## ✨ Project Goals

- **Voice authenticity detection** — Analyze audio to help distinguish genuine speech from AI-generated or manipulated voices.
- **AI-powered analysis** — Build on audio representations learned by modern machine learning models.
- **Practical usability** — Work toward a straightforward interface for submitting audio and understanding detection results.
- **Modular architecture** — Keep audio processing, machine learning inference, backend services, and the user interface independently maintainable.
- **Responsible results** — Communicate model predictions clearly without treating them as absolute proof of authenticity.

## 🧠 Technology

Decibel builds on the TrueVoice research baseline and explores the use of Google's Gemma 4 audio encoder for voice deepfake detection.

| Component | Technology |
|---|---|
| Audio intelligence | Google Gemma 4 E4B audio encoder |
| Classification | Lightweight neural classification head |
| Machine learning | Python, PyTorch, Hugging Face Transformers |
| Audio processing | Audio preprocessing and feature extraction |
| Application | Modular frontend and backend architecture |

The final application stack and integration details will follow the implementation in this repository.

## 🏗️ High-Level Architecture

```text
          Audio Input
               |
               v
       Audio Preprocessing
               |
               v
      Audio Feature Extraction
               |
               v
       Gemma 4 Audio Encoder
               |
               v
       Classification Engine
               |
               v
     Voice Authenticity Result
               |
               v
       User-Facing Interface
```

The architecture separates the audio intelligence pipeline from the application interface, allowing individual components to be developed and tested independently.

## 🔬 Model Approach

The underlying research approach uses a pretrained audio encoder to extract representations from speech and a lightweight classification head to predict whether an audio sample is genuine or synthetic.

The detection pipeline is intended to:

1. Accept an audio sample.
2. Normalize and preprocess the audio into the expected input format.
3. Extract audio representations using the model's audio encoder.
4. Pass the representations to the classification head.
5. Return a prediction through the application.

Actual model performance, supported audio formats, and inference requirements must be validated against the integrated Decibel implementation.

## 📁 Repository Structure

The repository is organized around independently maintainable project components.

```text
Decibel-/
├── engine/          # Audio analysis and ML inference
├── server/          # Backend services and API integration
├── frontend/        # User interface
├── scripts/         # Development and model utilities
├── notebooks/       # Experiments and model evaluation
├── saved_model/     # Model artifacts, when included
├── README.md
└── .gitignore
```

*Note: This is the intended high-level layout; adjust the tree to match the folders currently committed to the repository.*

## 🚀 Getting Started

### Prerequisites

- Git
- Python and the dependencies specified by the ML engine
- Node.js and npm if required by the frontend or server
- Compatible hardware and model access for local inference
- Hugging Face access and authentication if required by the selected Gemma 4 checkpoint

### Clone the Repository

```bash
git clone https://github.com/Sarthak-gith/Decibel-.git
cd Decibel-
```

Install dependencies and start individual components according to their respective setup instructions.

> **Development status:** Exact installation commands, environment variables, and launch instructions should be documented alongside the implemented frontend, server, and ML engine.

## 🧪 Evaluation

Reliable voice deepfake detection requires evaluation beyond clean, laboratory-quality recordings.

Important evaluation areas include:

- Classification accuracy, precision, recall, and F1-score
- Equal Error Rate (EER)
- Performance on unseen speakers and voice-generation systems
- Robustness to compression, noise, and different recording devices
- Inference latency and resource consumption

Benchmark results will be reported once the integrated Decibel pipeline has been evaluated under reproducible conditions.

## 🛣️ Roadmap

- [ ] Establish a reliable audio preprocessing and inference pipeline.
- [ ] Integrate the classification engine with the backend.
- [ ] Connect the frontend to the detection API.
- [ ] Support practical audio submission and clear prediction results.
- [ ] Evaluate robustness across recording conditions and synthetic voice sources.
- [ ] Improve error handling, inference performance, and user experience.
- [ ] Document reproducible setup and evaluation procedures.

## 🤝 Contributing

Decibel is developed as a collaborative project. Contributors should work on focused feature branches and submit pull requests for review before merging into `main`.

Suggested areas of contribution:

- Audio processing and ML inference
- Frontend development
- Backend and API integration
- Testing and model evaluation
- Documentation and developer tooling

## ⚠️ Responsible Use

Decibel is intended to support voice authenticity assessment, not to establish identity or determine fraud conclusively. Predictions may be incorrect, particularly for unfamiliar speakers, new synthesis methods, or poor-quality recordings. Results should be interpreted alongside other available evidence.


---

**Decibel — Listen closely. Detect intelligently.**
