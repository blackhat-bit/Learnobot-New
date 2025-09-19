# Secrets Directory

This directory contains sensitive configuration files for production deployment.

## Production Setup

Create these files with your actual values:

```bash
# API Keys
echo "your-openai-key-here" > openai_api_key.txt
echo "your-anthropic-key-here" > anthropic_api_key.txt
echo "your-google-key-here" > google_api_key.txt
echo "your-cohere-key-here" > cohere_api_key.txt

# App Configuration
echo "your-secret-key-here" > app_secret_key.txt
echo "your-db-password-here" > db_password.txt
```

## Security Notes

- These files are gitignored for security
- Files should have minimal permissions (600)
- Use `openssl rand -hex 32` to generate secure keys
- Rotate keys regularly in production
- Consider using cloud secret managers for better security

## File Permissions

```bash
chmod 600 secrets/*.txt
```