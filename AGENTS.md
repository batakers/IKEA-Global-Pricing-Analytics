# AGENTS.md - Instruksi Khusus Repo

Instruksi ini hanya untuk repo `IKEA-Global-Pricing-Analytics`. Instruksi global Codex tetap berlaku, tetapi jangan menduplikasi aturan global di file ini.

## Ringkasan Project

Project ini adalah platform analytics portfolio untuk analisis pricing IKEA global. Alur utamanya: data mentah CSV diproses menjadi output agregat, dipakai oleh FastAPI, Streamlit dashboard, visualisasi, report PDF, dan market clustering.

## Stack Teknologi

- Python analytics: pandas, NumPy, scikit-learn
- API: FastAPI, Uvicorn, Pydantic
- Dashboard: Streamlit, Plotly
- Visualisasi/reporting: Plotly, seaborn, matplotlib, reportlab
- Testing: pytest, pytest-cov
- Deployment: Docker, Docker Compose
- Package metadata: `pyproject.toml`

Catatan runtime: `pyproject.toml` mendeklarasikan Python `>=3.14,<3.15`, dan `Dockerfile` memakai `python:3.14-slim`. Direct dependency di `requirements.txt` harus dipin dan tetap sama dengan dependency di `pyproject.toml`.

## Struktur Folder Penting

- `data/` - raw input CSV dan generated CSV yang dipakai API/dashboard.
- `notebooks/` - script pipeline dan reporting bernomor; ini entry orchestration, bukan notebook `.ipynb`.
- `src/` - helper produksi untuk data prep, aggregation, clustering, schema, logging.
- `api/` - aplikasi FastAPI.
- `dashboard/` - aplikasi Streamlit.
- `tests/` - pytest suite.
- `assets/dashboard/` - gambar preview dashboard yang dipakai README.
- `notebooks/outputs/` - output visual/report generated; di-ignore oleh git.
- `README.md` - dokumen publik utama untuk setup, arsitektur, deployment notes, dan portfolio positioning.

## Command Project

Jalankan command dari root repo `IKEA-Global-Pricing-Analytics/`.

Install:
```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

Pipeline data minimal:
```powershell
python notebooks/01_data_preparation.py
python notebooks/02_country_aggregation.py
python notebooks/05_market_clustering.py
```

Pipeline/report tambahan yang terdokumentasi:
```powershell
python notebooks/06_pdf_report.py
python notebooks/03_visual_analysis.py
```

Dashboard dev:
```powershell
streamlit run dashboard/app.py
```

API dev:
```powershell
uvicorn api.main:app --reload
```

Test:
```powershell
pytest tests -q
```

Coverage yang terdokumentasi:
```powershell
pytest tests/ -v --cov=src
pytest tests/ -v --cov=src --cov=notebooks --cov-report=html
```

Docker:
```powershell
docker compose up -d --build dashboard api
docker compose run --rm tests
docker build -t ikea-pricing .
```

Lint: belum terdeteksi. Verifikasi dengan mencari config seperti `ruff.toml`, `.ruff.toml`, `setup.cfg`, `.pre-commit-config.yaml`, atau dokumentasi baru.

Typecheck: belum terdeteksi. Verifikasi dengan mencari `mypy.ini`, `pyrightconfig.json`, atau script dokumentasi baru.

Build Python package: belum terdeteksi sebagai command project. Build Docker terdeteksi melalui `docker build -t ikea-pricing .`.

## Pola Arsitektur

- `notebooks/01_data_preparation.py` menghasilkan `data/processed_catalog.csv`.
- `notebooks/02_country_aggregation.py` menghasilkan `data/country_metrics.csv` dan `data/product_benchmark.csv`.
- `notebooks/05_market_clustering.py` menghasilkan `data/clustering_results.csv`.
- `api/main.py` membaca CSV output dari `data/` saat startup dan harus fail fast jika output wajib hilang.
- `dashboard/app.py` membaca output CSV dan menyajikan UI analytics.
- Logic reusable sebaiknya hidup di `src/`; script di `notebooks/` idealnya tetap tipis sebagai orchestration, IO, visualisasi, dan report generation.

## Coding Style Khusus Repo

- Ikuti pola Python yang sudah ada: type hints, fungsi kecil, `Path` untuk path, pandas pipeline yang eksplisit.
- Jangan menambah dependency baru tanpa alasan kuat dan tanpa update `requirements.txt` serta `pyproject.toml`.
- Jangan memindahkan logic kembali ke script notebook jika sudah tersedia helper di `src/`.
- Untuk perubahan dashboard, jaga UX analytics yang padat, jelas, responsive, dan konsisten dengan Streamlit/Plotly yang sudah ada.
- Untuk perubahan API, pertahankan response shape dan validasi Pydantic kecuali user meminta breaking change.

## Testing dan Verifikasi

- Sebelum klaim selesai pada perubahan code/data path, jalankan test relevan minimal.
- Untuk perubahan luas atau shared logic, jalankan:
```powershell
pytest tests -q
```
- Untuk perubahan API, jalankan minimal:
```powershell
pytest tests/test_api.py -q
```
- Untuk perubahan pipeline/agregasi/clustering, jalankan test terkait di `tests/test_pipeline.py`, `tests/test_clustering.py`, dan `tests/test_data_validation.py`.
- Untuk perubahan yang memengaruhi data output, bandingkan minimal schema/kolom output sebelum dan sesudah perubahan.
- Jangan melemahkan assertion test untuk membuat test pass; perbaiki production path atau dokumentasikan blocker.
- Jika pytest gagal karena permission temp directory lokal, jelaskan statusnya dan minta approval untuk rerun dengan akses yang sesuai.

## Aturan Git

- Jangan commit tanpa instruksi eksplisit.
- Jangan push tanpa instruksi eksplisit.
- Jangan menjalankan reset, rebase, force push, atau checkout destruktif tanpa instruksi eksplisit.
- Worktree mungkin sudah dirty dari sesi sebelumnya; baca diff/status yang relevan dan jangan revert perubahan user.

## Dependency, Config, Environment, Secret

- `.env.example` adalah template. Jangan commit `.env`, token, credential, atau path lokal sensitif.
- `.gitignore` sudah mengabaikan `.env`, virtualenv, cache, logs, dan `notebooks/outputs/`.
- `data/` berisi data demo/raw/generated yang sengaja dipakai agar dashboard/API dapat langsung berjalan. Jangan hapus, regenerate, atau rewrite artifact data besar tanpa instruksi eksplisit.
- Jika mengubah environment variable, sinkronkan `.env.example`, dokumentasi, dan code yang membacanya.

## Area Sensitif

- `data/*.csv` - data besar dan output demo; perubahan bisa memengaruhi API, dashboard, tests, dan klaim portfolio.
- `notebooks/01_data_preparation.py`, `02_country_aggregation.py`, `05_market_clustering.py` - jalur pipeline utama.
- `src/data_prep.py`, `src/aggregation.py`, `src/clustering.py` - shared production logic.
- `api/main.py` - startup data loading dan endpoint contract.
- `dashboard/app.py` - UX dashboard portfolio.
- `requirements.txt`, `pyproject.toml`, `Dockerfile`, `docker-compose.yml` - perubahan runtime/dependency harus diverifikasi agar contract lokal, package metadata, dan Docker tetap selaras.
- `README.md` dan `assets/dashboard/` - klaim portfolio, setup, deployment notes, dan preview image harus tetap sinkron dengan data/test terbaru.

## Recommended Skills for This Repo

Skills tersedia secara global. Untuk repo ini, pertimbangkan skill berikut hanya jika relevan dan membantu:

- Data Analyst/Data Science: analytics, dataset, metric, dashboard, clustering, ML workflow.
- Business Analyst: requirement, PRD, user story, acceptance criteria, business logic, portfolio positioning.
- UI/UX/Web Designer: Streamlit layout, dashboard UX, accessibility, responsive behavior, visual consistency.
- Fullstack Developer: integrasi FastAPI, Streamlit/dashboard, data output, dan API contract.
- Python Pro: backend Python, automation, data pipeline, testing, refactor script ke `src/`.

Jangan wajib memakai skill untuk task kecil.
Jika task sederhana dan jelas, kerjakan langsung.
Jika user menyebut skill tertentu, ikuti skill tersebut.

## Panduan Subagent

- User tidak selalu tahu task mana yang cocok untuk subagent.
- Jika task kompleks, luas, multi-domain, atau bisa dipecah paralel, sarankan subagent terlebih dahulu.
- Jangan langsung menjalankan subagent tanpa konfirmasi user.
- Jika menyarankan subagent, berikan pembagian yang jelas, misalnya: backend/API, data pipeline, clustering/ML, dashboard UI/UX, testing, docs.

## Catatan Domain Project

- Angka cakupan negara di beberapa dokumen bisa historis atau tidak sinkron. Verifikasi angka dari `data/processed_catalog.csv`, `data/country_metrics.csv`, dan test saat membuat klaim.
- Core metric: `price_index = avg_price_usd / global_avg_price`.
- Core metric: `affordability_index = avg_price_usd / gdp_per_capita`.
- Market clustering saat ini berbasis price index, affordability, online availability, dan assortment breadth.
- Prioritaskan reproducibility, API startup safety, modularity di `src/`, test production path, dan artifact policy sesuai README.
