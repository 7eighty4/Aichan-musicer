# Echo 🎵 - A Discord Music Bot

music bot for discord written in python

Created by: [@7eighty4](https://github.com/7eighty4)

---

## Features

Plays music in your server vc
---

## How to Use

jus add the bot in your server and the commands are listed below.

| Command           | Description                                                |
| ----------------- | ---------------------------------------------------------- |
| `!play <song>`    | Searches for a song and adds it to the queue. Starts playing if the queue is empty. |
| `!queue`          | Displays the current list of songs in the queue.           |
| `!skip`           | Skips the current song and plays the next one.             |
| `!pause` / `!resume` | Pauses or resumes the music playback.                   |
| `!stop`           | Stops the music, clears the queue, and disconnects the bot.|
| `!join`           | Summons the bot to your current voice channel.             |
| `!resetvoice`     | Resets the bot's voice connection if you encounter issues. |

You can also use the interactive buttons on the "Now Playing" 

---

## Tech Stack

- **Language:** Python
- **Library:** discord.py
- **Audio Source:** yt-dlp for YouTube streaming
- **Hosting:** Railway
- **Deployment:** Docker

---

## My Development Journey

This project was a significant learning experience in backend development and DevOps. The initial deployment on Railway using Nixpacks presented several dependency challenges, particularly with FFmpeg and Opus. To solve this, I migrated the entire project to a `Dockerfile` deployment, which provided a stable and reliable environment. This process taught me a great deal about containerization, dependency management, and professional deployment workflows.
