# OLED Dashboard

A modular dashboard for a 0.96" 128x64 SSD1306 OLED (I2C, addr 0x3C) on a
Raspberry Pi. Cycles automatically through a system status page, an
animated-eyes page, and a digital clock page.

## Setup

1. Enable I2C:
   ```
   sudo raspi-config
   # Interface Options -> I2C -> Enable
   ```

2. Confirm the display is detected at 0x3C:
   ```
   sudo apt install -y i2c-tools
   i2cdetect -y 1
   ```

3. Install dependencies:
   ```
   pip3 install -r requirements.txt
   ```

4. Run:
   ```
   python3 main.py
   ```

   To run it on boot, add a systemd service or a `@reboot` cron entry
   pointing at `python3 /full/path/to/main.py`.

## Project layout

```
oled_dashboard/
├── main.py          # main application loop
├── display.py        # OLED init + Pillow canvas wrapper
├── page_manager.py    # page rotation/timing
├── animations.py     # eye animation state machine
├── pages/
│   ├── base.py       # Page interface every page implements
│   ├── status.py      # IP / CPU / temp / mem / disk / uptime
│   ├── eyes.py        # animated eyes
│   └── clock.py       # big HH:MM + blinking colon, date, location/weather
└── fonts/            # optional: drop custom .ttf files here
```

## Clock page / weather setup

The clock shows a small date at the top, a large `HH:MM` time with a
blinking colon and small AM/PM, and a small `<location>  morning°/night°`
line at the bottom. Weather comes from [Open-Meteo](https://open-meteo.com)
(free, no API key) using only the standard library (`urllib`), so there's
no extra dependency to install.

Set your location before running, either by editing the constants at the
top of `pages/clock.py` or via environment variables:

```
export WEATHER_LOCATION_NAME="Adelaide"
export WEATHER_LAT="-34.9285"
export WEATHER_LON="138.6007"
python3 main.py
```

The defaults above are just an example location -- change them to yours.
Weather is refetched roughly every 30 minutes and cached in between; if
the Pi has no internet connection or the request fails, the temperatures
show as `--°/--°` instead of crashing the page.

## Adding a new page

1. Create `pages/your_page.py` with a class that subclasses `Page`
   (see `pages/base.py`) and implements `update()` and `draw()`.
2. Set `duration` (seconds on screen) and `refresh_interval` (how often
   `update()` runs) as class attributes.
3. Add it to the list in `build_pages()` in `main.py`.

No other file needs to change. Ideas from the original spec: weather,
Spotify "Now Playing", Docker container status, Home Assistant status,
network throughput, CPU/RAM graphs, calendar/events, notifications.

## Credit / design references

Two existing implementations shaped this project:

- **The original single-page stats script** (Michael Klements /
  the-diy-life.com, adapted by Macley(kun)) is the direct basis for
  `pages/status.py` and parts of `display.py`: the icon-font + PixelOperator
  layout, caching the IP lookup for 60s instead of resolving it every
  refresh, reading uptime from `/proc/uptime` (more reliable than
  `psutil.boot_time()` across suspend/resume), the optional hardware
  reset-pin wiring, and — most importantly — only pushing a frame to the
  OLED over I2C when something actually changed, instead of writing every
  loop iteration. `PageManager.tick()` returns `True`/`False` for exactly
  this reason.
- **[sh1106-framework](https://github.com/danspage/sh1106-framework)**
  (a state-manager/graphics package for a different controller, the
  SH1106) inspired the page lifecycle shape: `update(dt)` receiving actual
  elapsed seconds rather than each page tracking its own clock, and an
  `enter()`-style hook when a page becomes active. The dashboard keeps its
  own lightweight `Page`/`PageManager` rather than depending on that
  package, since the display here is an SSD1306, not an SH1106, and the
  per-page `refresh_interval` throttling (status @5s, eyes @10 FPS, clock
  @1s) isn't something that framework provides out of the box.

## Notes

- `StatusPage` refreshes its data every ~5s but stays on screen for the
  page's full `duration` (10s), per the spec. Icon and value positions
  match the original script's pixel coordinates exactly, so the layout
  lines up whether or not the icon font is installed.
- `EyesPage` updates at ~10 FPS via `refresh_interval = 1/10`.
- `ClockPage` updates twice a second so the colon blinks at 1Hz; the
  hour/colon/minute widths are measured and summed every draw so the
  digits never shift left/right when the colon blinks on and off.
- The main loop ticks at ~30 FPS internally (so eye animation stays
  smooth and page switches are detected quickly), but `oled.show()` --
  the actual I2C write -- only happens on frames where a page reported
  it changed. In testing, a full 40s rotation through all three pages
  only triggered ~128 real hardware redraws out of 1200 loop ticks.
- Fonts fall back gracefully: `StatusPage` looks for
  `fonts/PixelOperator.ttf` and `fonts/lineawesome-webfont.ttf` first (see
  the credit section above for where to get them), then DejaVu, then
  Pillow's built-in bitmap font -- so the dashboard runs fine even with no
  extra font files installed, just with plain text labels instead of
  icons. For a nicer default look:
  ```
  sudo apt install -y fonts-dejavu-core
  ```
