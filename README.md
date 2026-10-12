# MMX AI Claims Processing Assistant — Prototype v0.2

Independent Streamlit demo concept for discussion with MMX Systems. Not an official MMX product and not connected to live MMX systems.

## Features
- Claims overview and interactive queue filters/search/export
- Claim details with editable workflow status, assigned team and missing-item fields
- Quick status actions for human workflow demonstrations
- New claim intake saved to Streamlit session state
- Illustrative document checklist and editable/downloadable case summaries
- Rule-based claims assistant panel and session activity log

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

All records are fictional. Updates/new records/activity log are retained in the current session only; they are not written to a permanent database and may reset. The assistant is rule-based, not a live AI model. It does not make coverage, liability, fraud or settlement decisions.
