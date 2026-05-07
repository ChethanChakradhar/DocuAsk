# AWS Deployment (ECS Fargate)

This folder contains a practical deployment path for the RAG API using:
- ECR for container registry
- ECS Fargate for compute
- ALB for public HTTP access
- Secrets Manager for `OPENAI_API_KEY`
- CloudWatch Logs for observability

## 1) One-time setup

1. Create ECR repo
```bash
aws ecr create-repository --repository-name rag-api --region <REGION>
```

2. Create secret for OpenAI key
```bash
aws secretsmanager create-secret \
  --name rag/openai/api-key \
  --secret-string "<YOUR_OPENAI_API_KEY>" \
  --region <REGION>
```

3. Create CloudWatch log group
```bash
aws logs create-log-group --log-group-name /ecs/rag-api --region <REGION>
```

4. Create ECS cluster
```bash
aws ecs create-cluster --cluster-name rag-cluster --region <REGION>
```

## 2) Build and push image

From `infra/aws`, run:
```bash
AWS_REGION=<REGION> \
AWS_ACCOUNT_ID=<ACCOUNT_ID> \
ECR_REPO=rag-api \
ECS_CLUSTER=rag-cluster \
ECS_SERVICE=rag-service \
./deploy.sh
```

## 3) Register task definition

1. Copy `task-definition.template.json` to `task-definition.json`.
2. Replace placeholders (`<ACCOUNT_ID>`, `<REGION>`, role ARNs, secret ARN).
3. Register:
```bash
aws ecs register-task-definition \
  --cli-input-json file://task-definition.json \
  --region <REGION>
```

## 4) Create ECS service

Create a Fargate service in private subnets with a public ALB.
Set container port `8000` and health check path `/health`.

## 5) Rolling deploys

After each push and task-definition update:
```bash
aws ecs update-service \
  --cluster rag-cluster \
  --service rag-service \
  --force-new-deployment \
  --region <REGION>
```

## Production notes

- FAISS index is local filesystem in this project. For true multi-replica production, move vector persistence to S3-backed snapshot flow or a managed vector DB.
- Keep one task replica unless you externalize index state.
- Add WAF + auth in front of ALB for enterprise usage.
