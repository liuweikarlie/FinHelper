#!/bin/bash
# download ollama
# ensure download llama3 in ollama


ollama serve
litellm --model ollama_chat/example
python function_call_main.py

