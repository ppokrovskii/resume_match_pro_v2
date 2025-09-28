# Auth0 Setup for Local Development & E2E Testing

## Overview
This guide sets up Auth0 for local development and E2E testing of the Document Service API.

## Auth0 Configuration

### 1. Create Auth0 Application

1. **Go to Auth0 Dashboard**: https://manage.auth0.com/
2. **Create Application**:
   - Name: `Document Service API`
   - Type: `Machine to Machine Applications`
3. **Configure Application**:
   - Authorized APIs: Select your API or create new one
   - Scopes: `read:documents`, `write:documents`, `delete:documents`

### 2. Create Auth0 API

1. **Create API**:
   - Name: `Document Service API`
   - Identifier: `https://api.resumematch.com/document-service`
   - Signing Algorithm: `RS256`

2. **Define Scopes**:
   ```
   read:documents    - Read document data
   write:documents   - Upload and create documents  
   delete:documents  - Delete documents
   search:documents  - Search documents
   ```

### 3. Get Credentials

From your Auth0 Dashboard, collect:
- **Domain**: `your-tenant.auth0.com`
- **Client ID**: Application Client ID
- **Client Secret**: Application Client Secret
- **API Identifier**: Your API identifier
- **Audience**: Same as API identifier
