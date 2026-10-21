# Snowflake Deployment Environments

## DEV
- Database: `SALES_DEV`
- GitHub environment: `dev`
- Deployment: Automatic after approved merge
- Access: Development-specific role and warehouse

## STAGING
- Database: `SALES_STAGING`
- GitHub environment: `staging`
- Deployment: After DEV validation
- Access: Staging-specific role and warehouse

## PROD
- Database: `SALES_PROD`
- GitHub environment: `production`
- Deployment: Approved release only
- Access: Least-privilege production deployment role and warehouse

## Deployment rules
1. Use the same reviewed SQL commit for all environments.
2. Only trusted workflows may select deployment database names.
3. Do not store credentials or tokens in Git.
4. Run data-quality checks after deploying.
5. Stop promotion if an earlier stage fails.
6. Record the deployed commit SHA and deployment results.
7. Review schema changes and rollback procedures before PROD.
8. Keep sample-data loaders out of routine production deployments.