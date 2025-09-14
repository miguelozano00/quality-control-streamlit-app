# Quality Control Streamlit App

A web application built with **Streamlit** for the **Quality Control department**.  
It allows technicians to record and review quality reports for devices, including electrical, software, and hardware checks.  
The app supports observations, generates PDF reports, and enables quick retrieval of past inspections.

---

## Features

- 📋 Create new quality control reports  
- ✅ Record results of electrical, software, and hardware checks  
- 📝 Add detailed observations and corrective actions  
- 📄 Export reports to **PDF**  
- 🔎 Browse and search previous reports  

---

## Installation (Local)

1. Clone the repository:

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
````

2. (Optional) Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate      # macOS/Linux
.venv\Scripts\activate         # Windows PowerShell
````

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the app:
```bash
streamlit run app.py
```

The app will be available at [http://localhost:8501]().


## Deployment on Streamlit Cloud

This app can be deployed for free using Streamlit Community Cloud.
1. Push your code to GitHub.
2. Log in to Streamlit Cloud.
3. Click New app and select your repository, branch (main), and file (app.py).
4. Deploy 🎉.

The app will be accessible at a subdomain like [https://<your-repo>-<your-username>.streamlit.app]()