# eBay Downloader

## Overview

This project contains a Python script, `ebay-dl.py`, that downloads search results from eBay and saves them as JSON or CSV files.

The script uses:
- `argparse` to handle command line arguments  
- `playwright` to load eBay pages with JavaScript  
- `BeautifulSoup` to parse HTML and extract data  
- `json` and `csv` to save results  

For each item, the script extracts:

- `name`
- `price` (in cents)
- `status`
- `shipping` (in cents)
- `free_returns`
- `items_sold`

If a field is not available, the value is recorded as `None`.

---

## How to Run

Run the following commands in the terminal:

```bash
python3 ebay-dl.py laptop --num_pages 10
python3 ebay-dl.py "stuffed animal" --num_pages 3
python3 ebay-dl.py "claremont mckenna" --num_pages 3
