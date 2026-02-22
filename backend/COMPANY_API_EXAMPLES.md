# Company API Usage Examples

This document provides examples of how to use the Company Management API endpoints.

## Authentication

First, you need to authenticate to get an access token:

```bash
# Register a new user
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "password123"
  }'

# Login to get access token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

## Company Management

### Create a Company

```bash
curl -X POST "http://localhost:8000/api/v1/companies/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corporation",
    "address": "123 Business St, City, State 12345",
    "phone": "+1-555-123-4567",
    "website_urls": ["https://www.acme.com", "https://blog.acme.com"],
    "description": "A leading technology company specializing in AI solutions"
  }'
```

### Get User's Companies

```bash
curl -X GET "http://localhost:8000/api/v1/companies/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Get Company Details with Files

```bash
curl -X GET "http://localhost:8000/api/v1/companies/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Update Company

```bash
curl -X PUT "http://localhost:8000/api/v1/companies/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corporation Updated",
    "description": "Updated description"
  }'
```

### Delete Company

```bash
curl -X DELETE "http://localhost:8000/api/v1/companies/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## File Upload

### Upload a File to Company

```bash
curl -X POST "http://localhost:8000/api/v1/companies/1/files" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@/path/to/your/document.pdf" \
  -F "description=Company handbook and policies"
```

### Get Company Files

```bash
curl -X GET "http://localhost:8000/api/v1/companies/1/files" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Delete a File

```bash
curl -X DELETE "http://localhost:8000/api/v1/companies/1/files/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Supported File Types

The API accepts the following file types for knowledge base uploads:

- **PDF**: `application/pdf`
- **Word Documents**: `application/msword`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- **Excel Spreadsheets**: `application/vnd.ms-excel`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- **Text Files**: `text/plain`
- **CSV Files**: `text/csv`
- **JSON Files**: `application/json`

## File Upload Limits

- **Maximum file size**: 10MB
- **Security**: Files are stored with unique names to prevent conflicts
- **Metadata**: Original filename and upload information are preserved

## Error Responses

### Validation Errors

```json
{
  "detail": "At least one website URL is required"
}
```

### File Type Errors

```json
{
  "detail": "File type image/jpeg not allowed. Allowed types: application/pdf, text/plain, ..."
}
```

### File Size Errors

```json
{
  "detail": "File size exceeds maximum allowed size of 10MB"
}
```

### Not Found Errors

```json
{
  "detail": "Company not found"
}
```

## Complete Example Workflow

1. **Register and Login**
2. **Create a Company** with required website URLs
3. **Upload Knowledge Base Files** (PDFs, documents, etc.)
4. **Retrieve Company Information** with all uploaded files
5. **Update Company Details** as needed
6. **Manage Files** (view, delete)

This API provides a complete solution for managing companies and their knowledge base documents!
