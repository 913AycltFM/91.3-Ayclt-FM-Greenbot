# Greenbot — 91.3 Ayclt FM Discord Radio Bot

Greenbot is a Discord voice bot for the 91.3 Ayclt FM radio stations. It uses Discord slash commands, FFmpeg, and the AzuraCast now-playing API.

## Supported stations

| Command choice | Station | AzuraCast station slug |
|---|---|---|
| `main` | 91.3 Ayclt FM | `91.3_ayclt_fm` |
| `hd2` | 91.3 Ayclt FM HD2 | `91.3_ayclt_fm_hd2` |
| `hd3` | 91.3 Ayclt FM HD3 | `91.3_ayclt_fm_hd3` |
| `hd4` | 91.3 Ayclt FM HD4 | `91.3_ayclt_fm_hd4` |

## Slash commands

- `/join` — join the voice channel you're in.
- `/play station:<station>` — play Main, HD2, HD3, or HD4.
- `/stations` — list all four stations and whether each stream URL is configured.
- `/listeners` — show current listener counts for all four stations.
- `/nowplaying station:<station>` — show current song and listener count for the selected station.
- `/stop` — stop playback.
- `/leave` — disconnect from voice.

## Setup

1. Install Python 3.12 or newer and FFmpeg.
2. Install dependencies: `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env`.
4. Set `DISCORD_TOKEN` to your Discord bot token.
5. Check the public stream listen URLs in AzuraCast and fill in `STREAM_HD2`, `STREAM_HD3`, and `STREAM_HD4`.
6. Run `python -m greenbot.bot`.

The bot's default AzuraCast API base is `https://radio.913aycltfm.com`. The now-playing endpoint for each station is:

`/api/nowplaying/<station-slug>`

## Important stream URL note

The HD2, HD3, and HD4 stream URLs are intentionally left blank in `.env.example`. Use the exact public listen URL shown by your AzuraCast installation; do not assume that the station slug is also the stream mount path.

## Docker

Build and run:

```bash
docker build -t greenbot .
docker run --env-file .env greenbot
```

The bot needs permission to connect and speak in the target Discord voice channels. The Discord application must have the `applications.commands` and `bot` scopes.
