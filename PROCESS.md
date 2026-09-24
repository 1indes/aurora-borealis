

# PROCESS

## Tools
- **Claude (chat):** explained each step, wrote most of `look.py`, `fetch.py` and `plot.py`, and helped me check the picture against the data.
- **VS Code's chat assistant:** ran my first `fetch.py` and committed the first NOAA file.
- **VS Code, uv, matplotlib, numpy, scipy:** to run the code and make the picture.
- **My own decisions:** I chose to make an artwork instead of a chart, asked for smooth curves instead of blocks, asked for no labels, and pushed it from twelve ribbons, to one curtain, to a ring so the picture felt full of light.

## One thing I kept
Before drawing anything, I ran a small script to check the range of the year's Kp values: the highest was 8.667 and 133 of 2,920 readings reached storm level. That told me the full colour scale from green to red was worth using, and it stopped me building a palette for data that wasn't there. 

## One thing I rejected
The first "curtains" picture used stacked bars, one row per month. It was blocky and crowded and read like a chart, which is the opposite of what I wanted, so I rejected it (it's still in my commit history). The ribbons version and the flat curtain were also replaced, because the first was too busy and the second was too thin and dark.

## What I had to correct
- It guessed my data file was called `kp.json`. It was `aurora-kp.json`.
- It first described Kp as one value every 3 hours. My first NOAA file actually had one value per minute and covered only 6 hours.
- It suggested the NOAA 3-hour file might cover 30 days. It had 56 readings, one week, so I switched to GFZ Potsdam to get a full year.
- It said the first big spike on my line chart would be near reading 150. The picture showed it near 390.
- It wrote the first README description before seeing my picture, and called the year "a steady green glow". The finished ring is a dense mix of green, teal and blue, so I rewrote it.
- It described all the storms as "pink and purple". When I measured the full-size picture against my data, only the two Kp 8.7 storms are pink, and the Kp 7 storms are thinner and lilac, so the README now says that.
- I checked the row counts at each step (357, 56 and 2,920 readings), and nothing was silently dropped.
