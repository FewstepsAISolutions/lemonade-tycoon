# 🍋 Lemonade Tycoon

A 30-day lemonade stand business simulation, written in pure Python 3 with no external packages. You play it in your browser.

## Run it

```bash
python3 lemonade_tycoon.py
```

Then open http://localhost:8000. Press Ctrl+C to stop.

## How it plays

Each trading day you choose:
- **Location**: Park, High street, Station or Residential. Each has different footfall and pitch fees, and weekends change the crowds.
- **Price per cup**: from £0.50 to £20.
- **Cups prepared**: unsold cups are wasted.
- **Drink quality**: Standard (£0.40 a cup) or Premium (£0.75 a cup).
- **Service**: Normal, or Extra care (£15 a day). Extra care makes customers happier but serves fewer of them.

Weather, price, quality and reputation drive demand. Customer satisfaction feeds your reputation for the next day. You can save, resume or reset the game, and saves go to `lemonade_save.json`.

The simulation is rules-based, with no AI.
