# Cloud Deployment Guide

This guide covers deploying the DJP Workflow Platform to cloud environments with persistent storage and secrets management.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Container Build](#container-build)
- [AWS Deployment](#aws-deployment)
- [GCP Deployment](#gcp-deployment)
- [Storage Configuration](#storage-configuration)
- [Secrets Management](#secrets-management)
- [Authentication](#authentication)

## Prerequisites

1. **Docker** installed locally for building and testing
2. **Cloud CLI tools**:
   - AWS: `aws` CLI configured with credentials
   - GCP: `gcloud` CLI configured with project
3. **API Keys** for LLM providers (OpenAI, Anthropic, Google)

## Container Build

### Local Build and Test

```bash
# Build the container
docker build -t djp-workflow:latest .

# Test locally
docker run -p 8080:8080 \
  -e OPENAI_API_KEY=your_key_here \
  -e ANTHROPIC_API_KEY=your_key_here \
  djp-workflow:latest
```

Visit http://localhost:8080 to verify the dashboard loads.

### GitHub Actions

The repository includes a GitHub Action (`.github/workflows/docker-build.yml`) that automatically:
- Builds multi-platform images (amd64, arm64)
- Pushes to GitHub Container Registry (ghcr.io)
- Tags with version, branch, and SHA

**Trigger build:**
```bash
git tag v1.0.0
git push origin v1.0.0
```

**Pull built image:**
```bash
docker pull ghcr.io/your-org/your-repo:v1.0.0
```

## AWS Deployment

### Option 1: AWS App Runner (Easiest)

AWS App Runner provides fully managed container hosting with auto-scaling.

**1. Push image to ECR:**

```bash
# Authenticate to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com

# Create repository
aws ecr create-repository --repository-name djp-workflow --region us-east-1

# Tag and push
docker tag djp-workflow:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/djp-workflow:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/djp-workflow:latest
```

**2. Create App Runner service:**

```bash
aws apprunner create-service \
  --service-name djp-workflow \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "123456789.dkr.ecr.us-east-1.amazonaws.com/djp-workflow:latest",
      "ImageRepositoryType": "ECR",
      "ImageConfiguration": {
        "Port": "8080",
        "RuntimeEnvironmentSecrets": {
          "OPENAI_API_KEY": "arn:aws:secretsmanager:us-east-1:123456789:secret:openai-key",
          "ANTHROPIC_API_KEY": "arn:aws:secretsmanager:us-east-1:123456789:secret:anthropic-key",
          "RUNS_DIR": "s3://my-djp-bucket/runs"
        }
      }
    }
  }' \
  --instance-configuration '{
    "Cpu": "1 vCPU",
    "Memory": "2 GB"
  }' \
  --region us-east-1
```

**3. Configure S3 for artifacts:**

```bash
# Create S3 bucket
aws s3 mb s3://my-djp-bucket --region us-east-1

# Set environment variable in App Runner
aws apprunner update-service \
  --service-arn arn:aws:apprunner:... \
  --source-configuration '{
    "ImageRepository": {
      "ImageConfiguration": {
        "RuntimeEnvironmentVariables": {
          "RUNS_DIR": "s3://my-djp-bucket/runs"
        }
      }
    }
  }'
```

### Option 2: ECS Fargate

For more control and VPC networking.

**1. Create ECS cluster:**

```bash
aws ecs create-cluster --cluster-name djp-cluster --region us-east-1
```

**2. Create task definition:**

```json
{
  "family": "djp-workflow",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "djp-workflow",
      "image": "123456789.dkr.ecr.us-east-1.amazonaws.com/djp-workflow:latest",
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:openai-key"
        },
        {
          "name": "ANTHROPIC_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:anthropic-key"
        }
      ],
      "environment": [
        {
          "name": "RUNS_DIR",
          "value": "s3://my-djp-bucket/runs"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/djp-workflow",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ],
  "taskRoleArn": "arn:aws:iam::123456789:role/djp-task-role",
  "executionRoleArn": "arn:aws:iam::123456789:role/djp-execution-role"
}
```

**3. Create IAM roles:**

Task role needs:
- S3 read/write to artifacts bucket
- Secrets Manager read access

Execution role needs:
- ECR pull permissions
- CloudWatch Logs write

**4. Create service with ALB:**

```bash
aws ecs create-service \
  --cluster djp-cluster \
  --service-name djp-service \
  --task-definition djp-workflow:1 \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration '{
    "awsvpcConfiguration": {
      "subnets": ["subnet-abc123", "subnet-def456"],
      "securityGroups": ["sg-xyz789"],
      "assignPublicIp": "ENABLED"
    }
  }' \
  --load-balancers '[
    {
      "targetGroupArn": "arn:aws:elasticloadbalancing:...",
      "containerName": "djp-workflow",
      "containerPort": 8080
    }
  ]'
```

## GCP Deployment

### Option 1: Cloud Run (Easiest)

Google Cloud Run provides fully managed container hosting.

**1. Push image to Artifact Registry:**

```bash
# Create repository
gcloud artifacts repositories create djp-workflow \
  --repository-format=docker \
  --location=us-central1

# Configure Docker
gcloud auth configure-docker us-central1-docker.pkg.dev

# Tag and push
docker tag djp-workflow:latest us-central1-docker.pkg.dev/my-project/djp-workflow/app:latest
docker push us-central1-docker.pkg.dev/my-project/djp-workflow/app:latest
```

**2. Create Cloud Storage bucket:**

```bash
gsutil mb -l us-central1 gs://my-djp-bucket
```

**3. Deploy to Cloud Run:**

```bash
gcloud run deploy djp-workflow \
  --image us-central1-docker.pkg.dev/my-project/djp-workflow/app:latest \
  --platform managed \
  --region us-central1 \
  --port 8080 \
  --memory 2Gi \
  --cpu 1 \
  --set-env-vars RUNS_DIR=gs://my-djp-bucket/runs \
  --set-secrets OPENAI_API_KEY=openai-key:latest,ANTHROPIC_API_KEY=anthropic-key:latest \
  --allow-unauthenticated
```

### Option 2: GKE (Kubernetes)

For production workloads requiring scaling and orchestration.

**1. Create GKE cluster:**

```bash
gcloud container clusters create djp-cluster \
  --zone us-central1-a \
  --num-nodes 2 \
  --machine-type n1-standard-2
```

**2. Create Kubernetes deployment:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: djp-workflow
spec:
  replicas: 2
  selector:
    matchLabels:
      app: djp-workflow
  template:
    metadata:
      labels:
        app: djp-workflow
    spec:
      containers:
      - name: app
        image: us-central1-docker.pkg.dev/my-project/djp-workflow/app:latest
        ports:
        - containerPort: 8080
        env:
        - name: RUNS_DIR
          value: "gs://my-djp-bucket/runs"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: openai
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: anthropic
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
---
apiVersion: v1
kind: Service
metadata:
  name: djp-workflow
spec:
  type: LoadBalancer
  selector:
    app: djp-workflow
  ports:
  - port: 80
    targetPort: 8080
```

## Storage Configuration

### Environment Variables

Configure storage backend via the `RUNS_DIR` environment variable:

| Storage | Format | Example |
|---------|--------|---------|
| Local | Path | `runs` or `/data/runs` |
| AWS S3 | `s3://bucket/prefix` | `s3://my-bucket/djp-runs` |
| GCS | `gs://bucket/prefix` | `gs://my-bucket/djp-runs` |

### AWS S3 Setup

**1. Create bucket:**
```bash
aws s3 mb s3://my-djp-bucket
```

**2. Set bucket policy (optional):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DJPArtifacts",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789:role/djp-task-role"
      },
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-djp-bucket/*",
        "arn:aws:s3:::my-djp-bucket"
      ]
    }
  ]
}
```

**3. Install boto3 in container:**
```dockerfile
RUN pip install boto3>=1.34.0
```

### GCS Setup

**1. Create bucket:**
```bash
gsutil mb -l us-central1 gs://my-djp-bucket
```

**2. Set IAM permissions:**
```bash
gcloud projects add-iam-policy-binding my-project \
  --member serviceAccount:djp-service@my-project.iam.gserviceaccount.com \
  --role roles/storage.objectAdmin
```

**3. Install google-cloud-storage in container:**
```dockerfile
RUN pip install google-cloud-storage>=2.14.0
```

## Secrets Management

### AWS Secrets Manager

**1. Create secrets:**

```bash
# OpenAI key
aws secretsmanager create-secret \
  --name openai-api-key \
  --secret-string "sk-..." \
  --region us-east-1

# Anthropic key
aws secretsmanager create-secret \
  --name anthropic-api-key \
  --secret-string "sk-ant-..." \
  --region us-east-1
```

**2. Grant access to task role:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "arn:aws:secretsmanager:us-east-1:123456789:secret:openai-api-key-*",
        "arn:aws:secretsmanager:us-east-1:123456789:secret:anthropic-api-key-*"
      ]
    }
  ]
}
```

### GCP Secret Manager

**1. Create secrets:**

```bash
# OpenAI key
echo -n "sk-..." | gcloud secrets create openai-api-key --data-file=-

# Anthropic key
echo -n "sk-ant-..." | gcloud secrets create anthropic-api-key --data-file=-
```

**2. Grant access to service account:**

```bash
gcloud secrets add-iam-policy-binding openai-api-key \
  --member serviceAccount:djp-service@my-project.iam.gserviceaccount.com \
  --role roles/secretmanager.secretAccessor

gcloud secrets add-iam-policy-binding anthropic-api-key \
  --member serviceAccount:djp-service@my-project.iam.gserviceaccount.com \
  --role roles/secretmanager.secretAccessor
```

## Authentication

See [AUTH.md](AUTH.md) for detailed authentication setup using:
- **AWS**: ALB with Cognito or OIDC
- **GCP**: Cloud Run with IAP (Identity-Aware Proxy)
- **Cloudflare**: Cloudflare Access with Zero Trust

## Health Checks

The container includes a health check endpoint for load balancers:

```
GET /_stcore/health
```

Configure your load balancer:
- **Path**: `/_stcore/health`
- **Port**: `8080`
- **Interval**: `30s`
- **Timeout**: `3s`
- **Healthy threshold**: `2`
- **Unhealthy threshold**: `3`

## Monitoring

### CloudWatch (AWS)

```bash
# View logs
aws logs tail /ecs/djp-workflow --follow

# Create metric filter for errors
aws logs put-metric-filter \
  --log-group-name /ecs/djp-workflow \
  --filter-name ErrorCount \
  --filter-pattern "ERROR" \
  --metric-transformations \
    metricName=Errors,metricNamespace=DJP,metricValue=1
```

### Cloud Logging (GCP)

```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision" --limit 100 --format json

# Create log-based metric
gcloud logging metrics create error_count \
  --description "Count of error logs" \
  --log-filter 'severity=ERROR'
```

## Scaling

### AWS App Runner

Auto-scales based on concurrent requests (10-100 instances).

```bash
aws apprunner update-service \
  --service-arn arn:aws:apprunner:... \
  --auto-scaling-configuration-arn arn:aws:apprunner:...:autoscalingconfiguration/HighConcurrency/1/...
```

### GCP Cloud Run

Auto-scales based on concurrent requests (0-100 instances).

```bash
gcloud run services update djp-workflow \
  --max-instances 10 \
  --min-instances 1 \
  --concurrency 80
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker logs <container_id>

# Test locally
docker run -it --entrypoint /bin/bash djp-workflow:latest
```

### Can't write to S3/GCS

- Verify IAM permissions
- Check `RUNS_DIR` format (must include `s3://` or `gs://`)
- Install cloud SDK: `pip install boto3` or `pip install google-cloud-storage`

### Secrets not loading

- Verify secret ARN/name matches environment variables
- Check task role has `secretsmanager:GetSecretValue` permission (AWS)
- Check service account has `roles/secretmanager.secretAccessor` (GCP)

## Cost Optimization

1. **Use spot/preemptible instances** (50-80% savings)
2. **Set min instances to 0** for dev environments (scale to zero)
3. **Use smaller machine types** (1 vCPU, 2GB RAM sufficient for most workloads)
4. **Enable S3/GCS lifecycle policies** to archive old artifacts after 90 days
5. **Use CloudFront/Cloud CDN** for static assets

## Next Steps

1. Review [AUTH.md](AUTH.md) for authentication setup
2. Configure monitoring and alerting
3. Set up CI/CD pipeline for automated deployments
4. Enable HTTPS with custom domain
5. Configure backup and disaster recovery
