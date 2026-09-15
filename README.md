# 🌳 Vanshawali Tree Builder

Hindi family-tree / वंशावली builder for local use.

## Features
- परिवार की जानकारी
- व्यक्ति जोड़ना, edit और delete
- पिता/माता के आधार पर generations
- Hindi Unicode UI
- Search
- JSON backup / restore
- A4 Landscape print / Save as PDF
- SQLite local database

## Windows setup
```bat
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
py app.py
```

Open: http://127.0.0.1:5000

For another computer on the same network, open the server PC IP with port 5000, e.g. `http://192.168.x.x:5000`.

## Print
Use **Print Preview** and choose A4 + Landscape. Browser PDF printing preserves Hindi text better than a server PDF library without proper Devanagari shaping.
