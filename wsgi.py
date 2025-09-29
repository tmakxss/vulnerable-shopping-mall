#!/usr/bin/env python3
"""
Vercel Serverless Function for Flask Application
"""

from run import app

# Vercelが期待するWSGIアプリケーション
application = app

if __name__ == "__main__":
    app.run()