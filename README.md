
# 🧠 CodeQuest

**CodeQuest** transforms natural language queries into effective search strategies for code snippets using a vector database and LLM-based refinement.

---

## ⚙️ Local Development Setup

Follow the steps below to build, run, and test the application locally using [AWS SAM](https://docs.aws.amazon.com/serverless-application-model/) and Docker.

---

### 0. Start OpenSearch and Dashboard UI with Docker

Make sure Docker is installed and running. Then launch OpenSearch and its UI:

```bash
docker-compose up -d
```

---

### 1. Build the SAM Application

Build the serverless app locally using the specified template:

```bash
AWS_SAM_LOCAL=true sam build --template-file template.yaml --no-cached
```

---

### 2. Invoke Ingestion Function Locally

Ensure your Google Cloud service account key is available. This function indexes a sample set of documents in OpenSearch.

> ℹ️ The `--docker-network codequest_codequest` flag ensures SAM runs in the same Docker network as OpenSearch.

```bash
export SERVICE_ACCOUNT_KEY="$(cat ~/codequest-service-account.json)"
echo '{"number_of_records": 20, "batch_size": 10}' | \
AWS_SAM_LOCAL=true sam local invoke IngestionFunction \
--docker-network codequest_codequest --debug
```

---

### 3. Start the Local API Gateway

This runs your API locally at: `http://localhost:3000`

```bash
AWS_SAM_LOCAL=true sam local start-api \
--docker-network codequest_codequest --debug
```

---

### 4. Test the Search API

You can test the API using `curl`:

```bash
curl "http://localhost:3000/code/search?query=How%20to%20query%20in%20bigquery%20and%20store%20results%20in%20Elasticsearch?"
```

---

### 5. Invoke Query Function Manually

Optionally, invoke the Query function directly using a sample event payload:

```bash
sam local invoke QueryFunction \
--event events/event.json --debug \
--docker-network codequest_codequest
```

---

### 6. Deploy to AWS Cloud

For initial deployment only — you must have AWS credentials configured locally.

> ✅ Future deployments will be handled by CI/CD (see `.github/workflows/` for GitHub Actions setup).

```bash
sam deploy --stack-name CodeQuestStack \
           --capabilities CAPABILITY_IAM
```

---

### 7. Run Unit Tests

Make sure you're in the correct Python virtual environment, then run:

```bash
python3 -m pytest -s -v
```

---

## ✅ Requirements

- Docker  
- AWS CLI + SAM CLI  
- Python 3.8+  
- Google Cloud service account (for BigQuery access)  
- VSCode (for plugin development, optional)

---