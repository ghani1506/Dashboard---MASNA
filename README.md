# MASNA Examination Analytics

Streamlit version of the MASNA dashboard: overview, master mark sheet, subject analysis, credit analysis, data review and configurable rules. Upload the school's Excel sheets or a JSON backup downloaded from the existing web dashboard. No student data is included in this repository.

## Deploy
1. Create a GitHub repository named `masna-exam-dashboard` and upload all project files, including `.streamlit/config.toml`.
2. Sign in at https://share.streamlit.io with GitHub and choose Create app.
3. Select the repository, branch `main`, and entrypoint `app.py`. Choose Python 3.12 in Advanced settings.
4. Deploy. Configure app visibility and authorised viewers in Streamlit before uploading student records. Repository privacy and app access are separate settings to verify.

## Local run
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Data and rules
The importer recognises these supplied template layouts using subject headers in row 10 and student rows 14–43 of the Master sheet. It uses saved numeric values, not Excel formula recalculation. Review future template changes before importing. Defaults are provisional: credit 59.5; PE and MIB excluded from student totals. Review rules before official reporting. Blank/non-numeric marks are excluded from achievement denominators. Partial totals are labelled incomplete. Competition ranks are calculated only within the same class/exam and matching eligible subject sets. No cross-exam student identity matching is assumed.

Uploads are session-only and are not committed to GitHub or written to server disk. Download a backup before closing. This first version does not implement editing, persistent storage, or live OneDrive sync. OneDrive sync requires Microsoft app registration and authorised file access; SharePoint embedding requires compatibility with hosting and school policies. Never upload student files to a public repository.
