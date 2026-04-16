<div align="center">
  <img src="https://raw.githubusercontent.com/atom-lang/atom/main/assets/atom-logo.svg" alt="Atom Logo" width="200"/>
  
  # ⚛️ Atom — The AI Systems Language
  
  **Python syntax + Native speed + WASM + AI built-in**
  
  [![Build Status](https://github.com/atom-lang/atom/workflows/CI/badge.svg)](https://github.com/atom-lang/atom/actions)
  [![PyPI version](https://badge.fury.io/py/atom-lang.svg)](https://badge.fury.io/py/atom-lang)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Discord](https://img.shields.io/discord/1234567890?color=7289da&label=Discord&logo=discord)](https://discord.gg/atom-lang)
  [![Twitter](https://img.shields.io/twitter/follow/atom_lang?style=social)](https://twitter.com/atom_lang)
</div>

---

## 🌐 Website

Visit the official website: **[atom-lang.github.io](https://mharshith548.github.io/atom/)**

## 🚀 What is Atom?

Atom is a modern programming language that combines:
- **Python's simplicity** — Clean, readable syntax
- **Native performance** — Compiles to machine code
- **WebAssembly deployment** — Run anywhere
- **Built-in AI** — Models like TinyLLM included

```atom
# Simple and powerful
import ai

let model = ai.load("tinyllm")
let reply = model.ask("What is Atom?")

print(reply)

⚡ Quick Start


# Clone the repo
git clone https://github.com/Mharshith548/atom.git
cd atom

# Start REPL
python atom.py repl

# Run example
python atom.py run examples/hello.atom

# Create project
python atom.py new myapp

📦 Features

Feature	Description
🐍 Python Syntax	Clean, indentation-based
⚡ Native Speed	Compiles to C then native
🌐 WASM Support	Deploy anywhere
🤖 AI Built-in	TinyLLM included
📦 Package Manager	atom add http
🌍 Web Server	Built-in HTTP server

📖 Examples

Hello World
atom
print("Hello from Atom!")
AI Chatbot
atom
import ai
let model = ai.load("tinyllm")
print(model.ask("Hello!"))
Web Server
atom
import http
let server = http.Server(8080)
server.route("/", fn(req): return "Hello World!")
server.start()
