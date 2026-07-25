@echo off
title Coworking Frontend
cd /d "%~dp0"
python -m http.server 5500
