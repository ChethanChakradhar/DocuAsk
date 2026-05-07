# DocuAsk

A friendly open-source app for asking questions about your PDFs.

DocuAsk lets you upload PDF files, ask questions in plain English, and get focused answers from your own documents. The main experience is a simple user-facing web UI, while developer API docs remain available separately for people who want to integrate with the backend.

## Features

- Human-friendly web interface at `/`
- PDF upload and document library
- Question answering over uploaded PDFs
- Source passages shown with each answer
- Local FAISS vector store for retrieval
- FastAPI backend with developer docs at `/docs`
- Docker and AWS deployment assets
- Evaluation workflow for testing answer quality

## 1) Architecture

```text
Browser UI -> FastAPI
          |- /documents/upload  -> parse PDF -> chunk -> embed -> FAISS persist
          |- /qa/ask            -> retrieve top-k chunks -> grounded prompt -> answer
          |- /documents         -> list/delete ingested docs

Data:
- data/uploads/*.pdf
- data/vector_store/index.faiss + index.pkl
- data/documents.json (document metadata + chunk ids)
```

## 2) Tech Stack

- UI: Static HTML, CSS, and JavaScript served by FastAPI
- API: FastAPI
- LLM + Embeddings: OpenAI (`langchain-openai`)
- Retrieval: FAISS (`langchain-community`)
- RAG orchestration: LangChain
- Packaging: Docker / docker-compose
- Cloud deployment: AWS ECS Fargate (templates in `infra/aws`)

## 3) Project Structure

```text
rag-system/
  app/
    api/
      routes/
    core/
    rag/
    services/
    static/
    main.py
  data/
    uploads/
    vector_store/
    documents.json
  eval/
    eval_dataset.json
  scripts/
    evaluate.py
  infra/aws/
  Dockerfile
  docker-compose.yml
  requirements.txt
```

## 4) Local Setup

1. Create env file
```bash
cp .env.example .env
```

2. Add your OpenAI API key in `.env`
```bash
OPENAI_API_KEY=...
APP_PASSCODE=1234
```

`APP_PASSCODE` is a 4-digit code required before someone can open the app or use the document/QA API routes. Change it before sharing the app. Your OpenAI account/project must also have billing or credits enabled because uploading documents and asking questions uses OpenAI embeddings and chat models.

3. Install + run
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

4. Open the app
- [http://localhost:8000](http://localhost:8000)

Developer API docs are available at:
- [http://localhost:8000/docs](http://localhost:8000/docs)

The API docs are intentionally not linked from the normal user interface, so the public app stays focused and non-technical.

## 5) API Endpoints

### Health
```bash
curl http://localhost:8000/health
```

### Upload PDFs
```bash
curl -X POST http://localhost:8000/documents/upload \
  -F "files=@/absolute/path/to/policy.pdf" \
  -F "files=@/absolute/path/to/security-handbook.pdf"
```

### List indexed docs
```bash
curl http://localhost:8000/documents
```

### Ask grounded question
```bash
curl -X POST http://localhost:8000/qa/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Who approves production security exceptions?",
    "top_k": 6
  }'
```

### Full demo (upload + ask)
```bash
./scripts/demo.sh http://localhost:8000 /absolute/path/to/your.pdf "What are the key takeaways?"
```

### Delete a document
```bash
curl -X DELETE http://localhost:8000/documents/<doc_id>
```

## 6) Grounding Strategy

- Answers are constrained with a strict system prompt to only use retrieved context.
- If context is insufficient, model must return: `I don't have enough information in the provided documents.`
- Response includes retrieved chunk sources (filename, page, chunk id, similarity score).

## 7) Context Management

- Recursive chunking (`CHUNK_SIZE`, `CHUNK_OVERLAP`)
- Retrieval top-k (`RETRIEVAL_K`)
- Context budget cap (`MAX_CONTEXT_CHARS`) to avoid prompt overflow

Tune these in `.env` based on your corpus size and answer quality.

## 8) Evaluation

1. Update `eval/eval_dataset.json` with your real benchmark questions.
2. Run:
```bash
python scripts/evaluate.py --dataset eval/eval_dataset.json --output eval/eval_results.json
```
3. Review:
- grounded rate
- keyword match rate
- expected source hit rate

## 9) Docker

Run with docker compose:
```bash
docker compose up --build
```

The `data/` directory is mounted as a volume so uploads/index persist.

## 10) Open-Source Notes

Before publishing:

- Do not commit `.env`, `api.env`, `.env.save`, uploaded PDFs, or generated FAISS indexes.
- Keep `.env.example` as the public template.
- Ask users to create their own OpenAI API key.
- Add a license file that matches how you want others to use the project.
- Add screenshots or a short demo GIF if you want the repository page to feel more complete.

## 11) AWS Deployment

See `infra/aws/README.md` for end-to-end ECS Fargate rollout.

Included assets:
- `infra/aws/task-definition.template.json`
- `infra/aws/deploy.sh`

## 12) Production Hardening Checklist

- Add API auth (JWT or API Gateway authorizer)
- Add request rate limiting
- Move FAISS persistence off local disk for multi-replica scaling
- Add CI/CD (build, test, deploy)
- Add monitoring alerts on latency/error rates
- Add automated eval run on each prompt/retrieval change

## 13) Quick Commands

```bash
make install
make run
make test
make eval
make docker-up
```
