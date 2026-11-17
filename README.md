# 🍋 Lemonade Tycoon

A 30-day lemonade stand business simulation, written in pure Python 3 with no external packages. You play it in your browser.

## Run it

```bash
python3 lemonade_tycoon.py
```

Then open the `http://localhost:...` address printed in the terminal. It uses port 8000 when available and tries the next ports if needed. Press Ctrl+C to stop.

## How it plays

Each trading day you choose:
- **Location**: Park, High street, Station or Residential. Each has different footfall and pitch fees, and weekends change the crowds.
- **Price per cup**: from £0.50 to £20.
- **Cups prepared**: unsold cups are wasted.
- **Drink quality**: Standard (£0.40 a cup) or Premium (£0.75 a cup).

Weather, price, quality and reputation drive demand. Customer satisfaction feeds your reputation for the next day.

## Staff and teamwork

Alex and Sam start the campaign on your team. Before each trading day, you can hire additional staff or fire someone already on the team. Team changes take effect immediately and stay in place until you change them again. You need to keep at least one staff member, and your team can have up to ten.

| Staff | Trait | Base capacity | Daily wage |
|---|---|---|---|
| Alex | Organised | 50 cups | £10 |
| Sam | Friendly | 50 cups | £10 |

Each staff member adds 50 cups of daily capacity and costs £10 in wages for each day worked. Hiring someone costs no fee; their wages are included in the day's upfront affordability check and profit. An Organised and Friendly team gets a ×1.1 teamwork multiplier, applied once even when the team has more than two people. Other teams use ×1.0. These are game balancing rules, not claims about real personality types.

Daily sales are the lowest of demand, prepared cups and staff capacity. The £20 daily wages are included in upfront affordability checks and profit, replacing the former Normal / Extra care service selection. Extra care's satisfaction bonus has been removed.

Your team and its capacity calculation appear on screen. Daily results record the staff working, wages, base capacity, teamwork multiplier and final capacity. Staff details are saved with the game.

## Save and resume

You can save, resume or reset the game, and saves go to `lemonade_save.json`. Older saves without staff automatically receive the default pair when loaded; their existing history remains intact.

The simulation is rules-based, with no AI.
