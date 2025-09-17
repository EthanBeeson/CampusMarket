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

# Install Dependencies
pip install -r requirements.txt

# Initialize the database by running main.py
python main.py

# For testing streamlit frontend
streamlit run app/main.py

## Notes

- Do **not** commit your local virtual environment (`venv/`) or SQLite database (`campus_market.db`) to Git.
- To reset the database, simply delete `campus_market.db` and rerun: main.py
-All CRUD functionality for listings is in app/crud/listings.py. Images are automatically linked via foreign keys.
-When adding new Python packages, run pip freeze > requirements.txt to update dependencies.

## Team Workflow

Start Session:
1. git pull

2. source venv/Scripts/activate

3. pip install -r requirements.txt

4. streamlit run app/main.py

Done with session:
5. git add .

6. git commit -m "Put here what you implemented"

7. git push origin main
