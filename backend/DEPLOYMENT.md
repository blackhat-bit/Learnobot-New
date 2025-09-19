# Deployment Guide

## Security Configurations

### Development (Current Setup)
```bash
# Uses .env file (convenient for development)
docker-compose up --build
```

### Production (Secure Setup)
```bash
# 1. Create secret files
mkdir -p secrets
echo "your-openai-key" > secrets/openai_api_key.txt
echo "your-anthropic-key" > secrets/anthropic_api_key.txt
echo "your-google-key" > secrets/google_api_key.txt
echo "your-cohere-key" > secrets/cohere_api_key.txt
echo "$(openssl rand -hex 32)" > secrets/app_secret_key.txt
echo "your-secure-db-password" > secrets/db_password.txt

# 2. Set secure permissions
chmod 600 secrets/*.txt

# 3. Deploy with production config
docker-compose -f docker-compose.prod.yml up --build
```

## Security Comparison

### Development (docker-compose.yml / docker-compose.dev.yml)
✅ **Pros:**
- Easy setup and debugging
- Environment variables from .env
- Quick iteration

❌ **Cons:**
- API keys in plain text
- Keys visible in container environment
- Less secure for production

### Production (docker-compose.prod.yml)
✅ **Pros:**
- Docker secrets (encrypted at rest)
- Keys not visible in environment variables
- Separate files for each secret
- Proper access controls

❌ **Cons:**
- More complex setup
- Requires manual secret file creation

## Best Practices

### For Development:
- Use docker-compose.yml (development config)
- Keep .env gitignored
- Rotate development keys regularly

### For Production:
- Use docker-compose.prod.yml
- Store secrets in external secret managers (AWS Secrets Manager, HashiCorp Vault)
- Implement key rotation
- Use read-only file systems where possible
- Regular security audits

## Cloud Deployment

### AWS
```yaml
# Use AWS Secrets Manager
environment:
  - AWS_REGION=us-east-1
  - SECRET_MANAGER_ENABLED=true
```

### Google Cloud
```yaml
# Use Google Secret Manager
environment:
  - GOOGLE_CLOUD_PROJECT_ID=your-project
  - USE_SECRET_MANAGER=true
```

### Kubernetes
```yaml
# Use Kubernetes secrets
apiVersion: v1
kind: Secret
metadata:
  name: learnobot-secrets
type: Opaque
data:
  openai-key: <base64-encoded-key>
```