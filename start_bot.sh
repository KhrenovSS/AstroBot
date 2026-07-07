#!/bin/bash
cd /home/nimda/Документы/AstroBot
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info > /tmp/uvicorn8.log 2>&1
