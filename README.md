# CodeQuest

Transforms natural language inputs into effective search strategies for code snippets.

## Local Development Setup

Follow these steps to set up and test the local development environment.

---

### 0. Run ElasticSearch and Kibana in Docker 
```bash
docker-compose up -d
```

### 1. Build the SAM Application
```bash
AWS_SAM_LOCAL=true sam build --template-file template.yaml --no-cached
```

### 2. Invoke Ingestion Function

Note that docker-network codequest_codequest: Ensures the SAM container is on the same network as the Elasticsearch container for connectivity.

```bash
sam local invoke IngestionFunction --docker-network codequest_codequest --debug
```


### 3. Start Local API 
This command uns the API locally on http://localhost:3000.

```bash
sam local start-api --docker-network codequest_codequest --debug
```

### 4. Test the API
```bash
curl http://localhost:3000/code/search?query=How%20to%20query%20in%20bigquery%20and%20store%20results%20in%20Elasticsearch\?
```

### 5. Invoke Query Function 

Alternativly we can invoke the query function via the sam CLI and the events defined in the events/events.json

```bash
sam local invoke QueryFunction --event events/event.json --debug --docker-network codequest_codequest
```

### 6. Deploy the Lambda Functions to AWS Cloud

Note that you need to add AWS credentials to your local environment. This command is only used for the inital test and setup 
Future deployments will be through CI/CD pipelines in Github Actions. 

```bash
sam deploy --template-file template.yaml \                                                                     
           --stack-name CodeQuestStack \
           --capabilities CAPABILITY_IAM
```