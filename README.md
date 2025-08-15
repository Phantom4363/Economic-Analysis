# Economics Portfolio Tracker (Streamlit)

A data-first Streamlit dashboard to track macroeconomic indicators (CPI, Unemployment, GDP, Policy Rate), compare economies, and annotate events with theory-backed notes (AD–AS, IS–LM, Phillips Curve).

## What’s included
- `app.py` — main Streamlit app (v1 prototype)
- `requirements.txt` — Python dependencies
- Demo fallbacks for when FRED/World Bank keys are not set.

## Quick start (local)
1. Clone the repo:
   ```bash
   git clone <your-repo-url>
   cd <repo-folder>
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate      # macOS / Linux
   .venv\Scripts\activate       # Windows (PowerShell)
   pip install -r requirements.txt
   ```

3. (Optional) Set FRED API key as an environment variable:
   - macOS / Linux:
     ```bash
     export FRED_API_KEY="your_key_here"
     ```
   - Windows (PowerShell):
     ```powershell
     setx FRED_API_KEY "your_key_here"
     ```

4. Run the app:
   ```bash
   streamlit run app.py
   ```

If no FRED key is present, the app will fall back to synthetic demo data so the UI still works.

## Deploy to Streamlit Community Cloud
1. Push the repo to GitHub.
2. On Streamlit Cloud, create a new app and point it to the GitHub repo and branch.
3. In the app settings → **Secrets**, add:
   ```
   FRED_API_KEY = "your_key_here"
   ```
4. Deploy. Streamlit Cloud will automatically install from `requirements.txt`.

## Customization ideas
- Add countries by editing the `COUNTRIES` mapping in `app.py` (include World Bank ISO code).
- Add new indicators by appending to the `INDICATORS` dict and providing the FRED/World Bank series ID or fetch function.
- Replace the synthetic fallback logic with cached API calls, or add scheduled refreshes for near-real-time updates.

## Troubleshooting
- If FRED requests fail: confirm `FRED_API_KEY` is set and valid.
- If World Bank fetch fails: ensure `wbgapi` is installed (or rely on fallback data).
- For plotting issues: update `plotly` to the latest patch version.

## License
MIT
