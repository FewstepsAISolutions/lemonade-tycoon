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

Weather, price, quality and reputation drive demand. Customer satisfaction feeds your reputation for the next day.

## Staff and teamwork

The same two staff members work throughout the campaign:

| Staff | Trait | Base capacity | Daily wage |
|---|---|---|---|
| Alex | Organised | 50 cups | £10 |
| Sam | Friendly | 50 cups | £10 |

Organised + Friendly gives a fixed ×1.1 teamwork multiplier. Combined capacity is therefore floor((50 + 50) × 1.1) = **110 cups per day**. Matching traits and unspecified pairs use ×1.0. Pair ordering does not affect the result. These are game balancing rules, not claims about real personality types.

Daily sales are the lowest of demand, prepared cups and staff capacity. The £20 daily wages are included in upfront affordability checks and profit, replacing the former Normal / Extra care service selection. Extra care's satisfaction bonus has been removed.

Your team and its capacity calculation appear on screen. Daily results record wages, base capacity, teamwork multiplier and final capacity. There is no hiring, firing or relationship progression in this version.

## Save and resume

You can save, resume or reset the game, and saves go to `lemonade_save.json`. Staff details are saved with the game. Older saves without staff automatically receive the default pair when loaded; their existing history remains intact.

The simulation is rules-based, with no AI.
