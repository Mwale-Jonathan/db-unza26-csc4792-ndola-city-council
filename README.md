## Installation & Execution Guide

We recommend using [`uv`](https://github.com/astral-sh/uv), the extremely fast Python package and project manager. Alternatively, standard Python `venv` with `pip` can be used.

### Prerequisites

- Python `>= 3.10`
- `uv` installed ([uv installation guide](https://docs.astral.sh/uv/getting-started/installation/)):

**macOS / Linux:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

After installation, restart your terminal, then verify:

```bash
uv --version
```

---

### Method 1: Running with `uv` (Recommended)

1. **Clone the Repository:**

    ```bash
    git clone git@github.com:Mwale-Jonathan/db-unza26-csc4792-ndola-city-council.git
    cd db-unza26-csc4792-ndola-city-council
    ```

2. **Sync the Environment:**
   `uv` will automatically create a virtual environment and install all dependencies:

    ```bash
    uv sync --all-groups
    ```

3. **Execute Step 1 — Web Scraping & Data Acquisition:**
   Crawl the portal, extract HTML tables, and download all raw source PDFs into `/source_files/`:

    ```bash
    uv run python scripts/run_all_scrapers.py
    ```

4. **Execute Step 2 — Tabular Extraction & Cleaning:**
   Parse raw PDFs, clean data types, and generate pipe-delimited CSVs in `/tabular/`:

    ```bash
    uv run python scripts/data_transformer.py
    ```

5. **Launch and Run the Jupyter Notebook:**
    ```bash
    # Launch Jupyter Lab or Notebook to view interactive extraction & cleaning steps
    uv run jupyter lab
    # Or: uv run jupyter notebook notebooks/data_extraction_and_cleaning.ipynb
    ```

---

### Method 2: Running with Standard `pip` and `venv`

1. **Create and Activate Virtual Environment:**

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

2. **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3. **Run the Extraction Pipeline:**

    ```bash
    python scripts/run_all_scrapers.py
    python scripts/data_transformer.py
    ```

4. **Open the Notebook:**
    ```bash
    jupyter notebook notebooks/data_extraction_and_cleaning.ipynb
    ```
