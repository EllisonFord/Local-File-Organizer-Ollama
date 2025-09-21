# Local File Organizer Ollama: AI File Management Run Entirely on Your Device, Privacy Assured

Tired of digital clutter? Overwhelmed by disorganized files scattered across your computer? Let AI do the heavy lifting! The Local File Organizer is your personal organizing assistant, using cutting-edge AI to bring order to your file chaos - all while respecting your privacy.

## How It Works 💡

Before:

```
/home/user/messy_documents/
├── IMG_20230515_140322.jpg
├── IMG_20230516_083045.jpg
├── IMG_20230517_192130.jpg
├── budget_2023.xlsx
├── meeting_notes_05152023.txt
├── project_proposal_draft.docx
├── random_thoughts.txt
├── recipe_chocolate_cake.pdf
├── scan0001.pdf
├── vacation_itinerary.docx
└── work_presentation.pptx

0 directories, 11 files
```

After:

```
/home/user/organized_documents/
├── Financial
│   └── 2023_Budget_Spreadsheet.xlsx
├── Food_and_Recipes
│   └── Chocolate_Cake_Recipe.pdf
├── Meetings_and_Notes
│   └── Team_Meeting_Notes_May_15_2023.txt
├── Personal
│   └── Random_Thoughts_and_Ideas.txt
├── Photos
│   ├── Cityscape_Sunset_May_17_2023.jpg
│   ├── Morning_Coffee_Shop_May_16_2023.jpg
│   └── Office_Team_Lunch_May_15_2023.jpg
├── Travel
│   └── Summer_Vacation_Itinerary_2023.docx
└── Work
    ├── Project_X_Proposal_Draft.docx
    ├── Quarterly_Sales_Report.pdf
    └── Marketing_Strategy_Presentation.pptx

7 directories, 11 files
```

## About this fork

This repository is a community-maintained fork of the original Local File Organizer project by QiuYannnn. The original project used the Nexa SDK. This fork replaces Nexa with Ollama to run everything locally without API keys.

Key differences from the original:
- Nexa SDK removed; added a light HTTP client (ollama_client.py) to talk to Ollama.
- Default models are now llama3.2:3b (text) and llava:7b (vision) from the Ollama library.
- No external accounts or keys required; models run via http://localhost:11434.
- Windows-specific guidance added (PATH, service, PowerShell commands).

Credits: Huge thanks to the original author and to the Nexa community for inspiring the initial implementation.

## Updates 🚀

- [2025/09] v0.1.0 (Ollama fork)
  - Migrated from Nexa SDK to Ollama
  - Added detailed Windows setup notes (PATH, service)
  - Updated documentation and commands
  - Kept model defaults: llama3.2:3b (text) and llava:7b (vision)
- [2024/09] v0.0.2 (original project)
  - Featured by Nexa Gallery and Nexa SDK Cookbook
  - Dry Run Mode: check sorting results before committing changes
  - Silent Mode: save all logs to a txt file for quieter operation
  - Added file support:  `.md`, .`excel`, `.ppt`, and `.csv` 
  - Three sorting options: by content, by date, and by type
  - Improved CLI interaction experience
  - Added real-time progress bar for file analysis


## Roadmap 📅

- [ ] Copilot Mode: chat with AI to tell AI how you want to sort the file (ie. read and rename all the PDFs)
- [ ] Change models with CLI 
- [ ] ebook format support
- [ ] audio file support
- [ ] video file support
- [ ] Implement best practices like Johnny Decimal
- [ ] Check file duplication
- [ ] Dockerfile for easier installation
- [ ] Create packaged executables for macOS, Linux, and Windows (community help welcome)

## What It Does 🔍

This intelligent file organizer harnesses the power of advanced AI models, including language models (LMs) and vision-language models (VLMs), to automate the process of organizing files by:


* Scanning a specified input directory for files.
* Content Understanding: 
  - Textual analysis via the Ollama model llama3.2:3b (https://ollama.com/library/llama3.2) to summarize text and propose filenames.
  - Visual content analysis via the Ollama model llava:7b (https://ollama.com/library/llava) to interpret images for categorization and descriptions.

* Understanding the content of your files (text, images, and more) to generate relevant descriptions, folder names, and filenames.
* Organizing the files into a new directory structure based on the generated metadata.

The best part? All AI processing happens 100% on your local device using [Ollama](https://ollama.com/) running locally. No internet connection required, no data leaves your computer, and no external AI API keys are needed — keeping your files completely private and secure.


## Supported File Types 📁

- **Images:** `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`
- **Text Files:** `.txt`, `.docx`, `.md`
- **Spreadsheets:** `.xlsx`, `.csv`
- **Presentations:** `.ppt`, `.pptx`
- **PDFs:** `.pdf`

## Prerequisites 💻

- **Operating System:** Compatible with Windows, macOS, and Linux.
- **Python Version:** Python 3.12
- **Conda:** Anaconda or Miniconda installed.
- **Git:** For cloning the repository (or you can download the code as a ZIP file).

## Installation 🛠

> This fork migrates the project from Nexa SDK to Ollama. For Ollama installation and troubleshooting, see https://ollama.com/download and https://github.com/ollama/ollama.

### 1. Install Python

Before installing the Local File Organizer, make sure you have Python installed on your system. We recommend using Python 3.12 or later.

You can download Python from [the official website]((https://www.python.org/downloads/)).

Follow the installation instructions for your operating system.

### 2. Clone the Repository

Clone this fork (Ollama version) to your local machine using Git:

```bash
git clone https://github.com/EllisonFord/Local-File-Organizer-Ollama.git
```

On Windows PowerShell:

```powershell
git clone https://github.com/EllisonFord/Local-File-Organizer-Ollama.git
```

Or download the repository as a ZIP file and extract it to your desired location.

### 3. Set Up the Python Environment

Create a new Conda environment named `local_file_organizer` with Python 3.12:

```zsh
conda create --name local_file_organizer python=3.12
```

Activate the environment:

```zsh
conda activate local_file_organizer
```

### 4. Install and Run Ollama ️

This fork replaces the original Nexa integration with a local Ollama setup. All AI runs on http://localhost:11434.

- Install Ollama: https://ollama.com/download
  - macOS: brew install --cask ollama
  - Linux: curl -fsSL https://ollama.com/install.sh | sh
  - Windows:
    - Download and run the installer from the website.
    - After install, open a new PowerShell and verify:
      ```powershell
      ollama --version
      ```
    - If you see 'ollama is not recognized', add this folder to your PATH and restart your shell:
      - C:\\Program Files\\Ollama
    - The Ollama service usually starts automatically on Windows. You can also start it from the Start Menu (Ollama) or Services.
- Start the Ollama service (macOS/Linux or if you prefer running it manually):
  ```bash
  ollama serve
  ```
- Pull the required models:
  ```bash
  ollama pull llama3.2:3b
  ollama pull llava:7b
  ```
  - Model pages: https://ollama.com/library/llama3.2 and https://ollama.com/library/llava
  - Optional: set a custom host/port via environment variable:
    - macOS/Linux:
      ```bash
      export OLLAMA_HOST=0.0.0.0:11434
      ```
    - Windows PowerShell:
      ```powershell
      $env:OLLAMA_HOST = "0.0.0.0:11434"
      ```
- GPU notes:
  - NVIDIA GPUs are supported on Windows; otherwise, Ollama will fall back to CPU.
  - Larger models require more VRAM; the defaults in this repo use 3B/7B variants to fit most machines.


### 5. Install Dependencies 

1. Ensure you are in the project directory:
   - macOS/Linux:
     ```bash
     cd path/to/Local-File-Organizer-Ollama
     ```
   - Windows PowerShell:
     ```powershell
     cd C:\path\to\Local-File-Organizer-Ollama
     ```
   Replace the path with the actual location where you cloned or extracted the project.

2. Install the required dependencies:
   ```zsh
   pip install -r requirements.txt
   ```

**Note:** If you encounter issues with any packages, install them individually:

```zsh
pip install Pillow pytesseract PyMuPDF python-docx
```

With the environment activated and dependencies installed, run the script using:

### 6. Running the Script🎉
```zsh
python main.py
```

## Notes

- **Ollama Models:**
  - The script uses `llava:7b` (vision) and `llama3.2:3b` (text) via the local Ollama service at http://localhost:11434.
  - Ensure Ollama is running and these models are pulled (`ollama pull llava:7b` and `ollama pull llama3.2:3b`).
  - No external API keys are required; everything runs locally.


- **Dependencies:**
  - **pytesseract:** Requires Tesseract OCR installed on your system.
    - **macOS:** `brew install tesseract`
    - **Ubuntu/Linux:** `sudo apt-get install tesseract-ocr`
    - **Windows:** Download from [Tesseract OCR Windows Installer](https://github.com/UB-Mannheim/tesseract/wiki)
  - **PyMuPDF (fitz):** Used for reading PDFs.

- **Processing Time:**
  - Processing may take time depending on the number and size of files.
  - The script uses multiprocessing to improve performance.

- **Customizing Prompts:**
  - You can adjust prompts in `data_processing.py` to change how metadata is generated.

## License

This project is dual-licensed under the MIT License and Apache 2.0 License. You may choose which license you prefer to use for this project.

- See the [MIT License](LICENSE-MIT) for more details.