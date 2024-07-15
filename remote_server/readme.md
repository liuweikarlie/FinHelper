# REMOTE_SERVER Readme

if we just run the llm in our local machine, this would be really low speed. In order to make the application more user friendly, we move all the llm in the remote machine. 

In this project, we rent the GPU machine in autodl (A100), when there is need to use the llm, we would send the question to the remote machine, and then remote machine would do the inference work. The result would then send to local machine. The connection is established using ssh.

## Remote server file
- Step 1: move the `/root/RAG/RAG_main` folder to the remote machine. 
- Step 2: move all files under `remote_server` to remote machine

## Run application in Remote Machine

- Step 1 : follow the instruction in `/root/RAG/RAG_main/readme.md`
- Step 2: follow the instruction (`/root/load_moel/readme.md`)to load the finetune model 
- Step 3 : follow the below instruction

```bash

pip install litellm flask

```
- Step 4: run the application

```bash

ollama serve

litellm --model ollama_chat/example

python RAG_main/server.py

```


