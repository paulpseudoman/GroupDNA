# GroupDNA `Python`

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](#)
[![Python version](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/)

GroupDNA is a Python-based WhatsApp group chat analyzer that turns a raw `.txt` export into a clean activity and personality report. It reads a WhatsApp chat file, parses messages, handles common export edge cases, computes group-level statistics, and saves the final report as a text file.

The project was built under a fundamentals-first constraint: no pandas, no matplotlib, no regex, and no pre-built chat analyzer libraries. The analysis uses Python basics, dictionaries, loops, string operations, `datetime`, file handling, and NumPy for hourly activity calculations.

## Table of Contents

- [Project Summary](#project-summary)
- [Features](#features)
- [Personality Archetypes](#personality-archetypes)
- [Input Format](#input-format)
- [Requirements](#requirements)
- [How To Run](#how-to-run)
- [Output Sections](#output-sections)

## Project Summary

GroupDNA answers questions such as:

- Who sends the most messages?
- What is the busiest day and hour in the group?
- What words does the group use most often?
- Who replies fastest?
- Who has the longest silent streak?
- Who shares the most media or deletes messages?
- What personality archetype best matches each participant?

The program prints the report in the console and also saves the same report as a `.txt` file next to the input chat export.

## Features

- WhatsApp chat parser for exported `.txt` files
- Support for 24-hour timestamps and `am/pm` timestamps
- System message detection and counting
- Media omitted message tracking
- Deleted message tracking
- Multi-line message handling
- Group overview with participant message counts
- Busiest day and busiest hour analysis
- Top word frequency analysis with stop-word filtering
- Average response time per participant
- Longest silent streak per participant
- Media and deleted message summary
- Personality archetype assignment for every participant
- Text report generation

## Personality Archetypes

Each participant is assigned the archetype where they score the highest. For real WhatsApp groups with more than eight members, archetypes are allowed to repeat so every person receives a result.

Supported archetypes:

- THE SPAMMER
- THE GROUP MOM
- THE NIGHT OWL
- THE STORYTELLER
- THE DRAMA QUEEN
- THE GHOST
- THE COMEDIAN
- THE QUESTION MASTER

The report displays first names in the archetype section to keep the output aligned, while full names are still used internally for calculations.

## Input Format

The program expects a WhatsApp exported `.txt` file.

Supported timestamp examples:

```text
12/04/24, 23:14 - A: bhai aaj kya scene
08/11/25, 5:56 am - B: Hello
```

The script also handles the special invisible spacing that WhatsApp sometimes adds before `am` or `pm`.

## Requirements

Install Python and NumPy.

```bash
pip install numpy
```

## How To Run

1. Export a WhatsApp group chat as a `.txt` file.
2. Place the chat export somewhere on your computer.
3. Run the Python script.

```bash
python GroupDNA.py
```

4. When prompted, paste the full path to the chat file.
5. The report will be printed in the console.
6. A `.txt` report file will also be created in the same folder as the chat export.

Example output file:
## Output Sections

The generated report includes:

- Parser summary
- Group overview
- Messages per person
- Chat activity summary
- Top 10 busiest days
- Favourite words
- Response patterns
- Longest silent streaks
- Media and deleted messages
- Personality archetypes
- Archetype score table
