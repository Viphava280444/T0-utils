# SSH Auto-Login Tool

Auto SSH to CERN lxplus with 2FA support.

## Setup

```bash
pip3 install -r requirements.txt
cp .env.example .env
```

Edit `.env` with your credentials:
```
JUMP_USER=vkhlaisu
JUMP_PASSWORD=your_password
DEST_USER=cmst0
DEST_PASSWORD=your_password
```

## Usage

```bash
python3 auto_ssh.py
```

Enter your 2FA code when prompted, then you have an interactive terminal.
