# Campus Market

Campus Market is a Facebook Marketplace-like web app for UNCC students to buy and sell items. It includes:

- Student-only login
- Create, read, update, delete listings
- Upload multiple images per listing
- Browse listings and search by keyword or filter
- Instant messaging (planned)

---

## Project Setup

#Clone the repository

```bash
First time only:
git clone <git@github.com:EthanBeeson/CampusMarket.git>

Every session:
cd CampusMarket

# Windows (Git Bash)
ONLY DO THIS THE FIRST TIME: python3 -m venv venv
source venv/Scripts/activate

# macOS/Linux
ONLY DO THIS THE FIRST TIME: python3 -m venv venv
source venv/bin/activate

# Install Dependencies - once 
pip install -r requirements.txt

# Initialize the database by running home.py
python home.py

# First time only:
# From the root of the sproject CampusMarket create a fake listing by running:
python -m scripts.seed_db

# For testing streamlit frontend
streamlit run home.py
# Navigate to local URL given after the above command ie. http://localhost:8501

## Notes

- The app now defaults to a shared demo database `campus_market_global.db` (checked in) populated with mock users/listings. Override with `DATABASE_URL` if you need a local DB.
- Uploads can live in a shared folder by setting `UPLOADS_BASE_DIR` (defaults to `uploads/`). This helps teams share images without committing them.
- Do **not** commit your local virtual environment (`venv/`) or any private SQLite database you create.
- To reset the shared demo DB, delete `campus_market_global.db` and rerun: `python scripts/seed_global_db.py` (or run `home.py` to auto-create empty tables with the default file).
-All CRUD functionality for listings is in app/crud/listings.py. Images are automatically linked via foreign keys.
-When adding new Python packages, run pip freeze > requirements.txt to update dependencies.

## Team Workflow

Start Session:
1. git pull

2. source venv/Scripts/activate

3. pip install -r requirements.txt

4. streamlit run home.py

Done with session:
5. git add .

6. git commit -m "Put here what you implemented"

7. git push origin main
