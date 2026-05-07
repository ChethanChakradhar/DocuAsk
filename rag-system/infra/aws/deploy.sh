#!/usr/bin/env bash
set -euo pipefail

# Required environment variables:
# AWS_REGION, AWS_ACCOUNT_ID, ECR_REPO, ECS_CLUSTER, ECS_SERVICE

if [[ -z "${AWS_REGION:-}" || -z "${AWS_ACCOUNT_ID:-}" || -z "${ECR_REPO:-}" || -z "${ECS_CLUSTER:-}" || -z "${ECS_SERVICE:-}" ]]; then
  echo "Missing required environment variables."
  echo "Set AWS_REGION, AWS_ACCOUNT_ID, ECR_REPO, ECS_CLUSTER, ECS_SERVICE"
  exit 1
fi

IMAGE_TAG="${1:-$(date +%Y%m%d%H%M%S)}"
IMAGE_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}:${IMAGE_TAG}"

aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

docker build -t "$IMAGE_URI" ../..
docker push "$IMAGE_URI"

echo "Image pushed: $IMAGE_URI"
echo "Now update your ECS task definition image and run:"
echo "aws ecs update-service --cluster $ECS_CLUSTER --service $ECS_SERVICE --force-new-deployment --region $AWS_REGION"
