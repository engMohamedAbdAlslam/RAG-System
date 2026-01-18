# RAG
this is a minimal implementation of the RAG  for qustion answering

## Requirements
- python 3.8
#### install python using mini conda 
1) download miniconda 
2) create a new environment using the following command :
```bash
$ conda create -n mini_rag python=3.8
```
3) active the environment using the following command :
```bash
$ conda activite mini_rag
```
## Installiation

### install required packages
```bash
$ pip install -r requirements.txt
```
### setup the environment variables
```bash
$ cp .env.example .env
```
set your environment variables in the .env file like 'OPENAI_API_KEY' value

## Run FastAPI server 

```bash
$ uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
## to auto complete press `ctrl`+`shift`+`p` then Enter
```bach
$ Remote-WSL: Reopen Folder in WSL
```

## Run Docker compose serevecies

```bash
$ cd docker
$ cp .env.example .env
```

- update `env` with your credentials
