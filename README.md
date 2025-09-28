# Money Savings Pot (Demo App)

A transparent group savings tracker built in Python with Streamlit.  
Every deposit or withdrawal is stored in a hash-linked ledger (like a blockchain), so history can’t be changed.  
Optional wallet signatures via MetaMask add extra trust, and the app also includes charts, goal tracking, and an AI “coach” summary.

⚠️ This is a demo app — not real money, not financial advice.

---

## Features
- Add deposits and withdrawals into a group savings pot.
- Ledger is hash-linked for tamper-evidence (similar to a blockchain).
- Optional MetaMask wallet signing and verification for transactions.
- Stats: total in/out, balance, and progress toward a savings goal.
- Charts: bar chart of net contributions and pie chart of deposit shares.
- AI Coach summary (local rule-based or Google AI Studio API).
- Export the full ledger as CSV, or reset to the genesis block.

---

## Tech Stack
- **Python**
- **Streamlit**
- **Pandas**
- **Altair**
- **eth-account** (for signing/verification)
- **MetaMask** (optional signing)
- **Google AI Studio API** (optional summaries)
- **GitHub Copilot** (assisted development)

---

## Installation & Run

```bash
# Clone the repo
git clone https://github.com/yourusername/money-savings-pot.git
cd money-savings-pot

# (Optional) create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Mac/Linux
.venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py


Optional Setup
    Google AI Studio API (for AI Coach summaries)

    1. Create a .env file in the project root:
        GOOGLE_API_KEY=your_api_key_here

    2. In the app sidebar, enable AI Coach.
        If no key is provided, the app falls back to local rule-based summaries.

    MetaMask Signing (for crypto-style attestations)

    1. Run a simple HTTP server to serve the included signer.html:
        ```bash
        python -m http.server 8000
    2. Open http://localhost:8000/signer.html in your browser.
    3. Copy the locked canonical message from the app into the signer, sign it with MetaMask, and paste the Address + Signature back into the app.
    4. When you add the transaction, the app will verify that the recovered signer matches the entered wallet address.


Demo
    GitHub Repo: [https://github.com/Forach/shellhacks-crypto-saving-pot-2025]
    Live App (Streamlit Cloud): coming soon
    Video Demo (YouTube): link here
    Devpost Submission: link here


Disclaimer
    This project was built for ShellHacks 2025 as a demo.
    It is not connected to real banks, crypto wallets, or money.