# hack-davis-26
# Members: Eleni, Kyi Sin, Daniel

Quick start
-----------

Prerequisites:
- Python 3.9+ (or your preferred 3.x)
- Node 16/18+ and npm
- ffmpeg on PATH (used to convert audio)

Backend (API)
- Create and activate a Python environment:

	- On macOS / Linux:
		`python -m venv .venv && source .venv/bin/activate`
	- On Windows (PowerShell):
		`python -m venv .venv; .\.venv\Scripts\Activate.ps1`

- Install Python deps:
	`pip install -r requirements.txt`

- Set required env vars (example):
	`set AI_API_KEY=your_api_key_here` (Windows) or `export AI_API_KEY=your_api_key_here` (Unix)

- Run backend (development):
	`python app.py`

- Or serve with Waitress (production-like):
	`python -u -c "from waitress import serve; import app; serve(app.app, host='127.0.0.1', port=5000)"`

Frontend
- Change to the frontend folder:
	`cd FrontEnd/whisper-pop-suggestions-main`
- Install deps and run dev server:
	`npm install`
	`npm run dev`
- Build for production:
	`npm run build` then `npm run preview`

Notes
- The app transcribes audio locally (faster-whisper) and runs a local emotion model. Ensure `ffmpeg` is installed for audio conversion.
- Supabase integration has been removed from this repo; no database or Supabase keys are required to run the app locally.
- If you encounter missing dependency errors, re-check the environment activation and required packages.

Troubleshooting
- If you see `ffmpeg not found`, install ffmpeg and restart your terminal.

Files
- Backend entry: [app.py](app.py)
- Frontend: [FrontEnd/whisper-pop-suggestions-main](FrontEnd/whisper-pop-suggestions-main)

