# Codebase Brain

> An AI brain that lives inside your codebase. Finds bugs before they happen. Explains everything in plain English.

## What is this?

Codebase Brain is an AI-powered tool that reads your entire Python codebase, understands how every file connects to every other file, and answers your questions in real time.

Point it at any Python project. Ask it anything.

## What can it do?

- **Visualize your codebase** — interactive risk map showing which files are dangerous
- **Risk scoring** — RED means danger, ORANGE means caution, GREEN means safe
- **Ask questions** — "What breaks if I delete this file?" answered instantly
- **Live watching** — brain updates automatically when you change code
- **Bug prediction** — find cascade failures before they happen

## Install
```bash
pip install -e .
```

## Setup (one time)
```bash
brain init
```
Enter your Groq API key when asked. Get a free key at groq.com.

## Use
```bash
cd your_project
brain start
```

That's it. Brain reads your codebase, opens interactive graph in browser, and waits for your questions.

## Ask your brain anything
```
What does analyze_file do?
What breaks if I delete app.py?
What is the most dangerous file?
What does this codebase depend on?
```

## The Problem

Your codebase grows. Your team grows. Nobody knows everything anymore.

- A developer changes one file. Three things break somewhere else.
- A bug exists for weeks because nobody knew which file to look at.
- A new developer joins. Takes months to understand the codebase.
- Code reviews miss hidden dependencies. Production breaks.

Senior developers spend hours every week just *understanding* code instead of writing it.

## The Solution

Codebase Brain installs in 30 seconds and gives your entire team a shared understanding of your codebase instantly.

No more guessing. No more hours tracing dependencies manually.
Just ask.