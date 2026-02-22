# AI Chat Backend

A FastAPI backend for an AI chat application with authentication and company management support.

## Features

- **FastAPI** - Modern, fast web framework for building APIs
- **PostgreSQL** - Robust relational database
- **JWT Authentication** - Secure token-based authentication
- **Company Management** - Create and manage companies/organizations
- **File Upload** - Knowledge base document upload (PDF, DOC, XLS, etc.)
- **SQLAlchemy** - Python SQL toolkit and ORM
- **Alembic** - Database migration tool
- **Pydantic** - Data validation using Python type annotations
- **Docker** - Containerized deployment

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database models and connection
│   ├── schemas.py           # Pydantic models
│   ├── auth.py              # Authentication utilities
│   └── routes.py            # API routes
├── alembic/                 # Database migrations
├── requirements.txt          # Python dependencies
├── .env                     # Environment variables
├── .env.example             # Environment template
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Development Docker setup
├── docker-compose.prod.yml  # Production Docker setup
├── .dockerignore            # Docker ignore file
├── alembic.ini             # Alembic configuration
├── run.py                   # Application entry point
└── README.md                # Setup instructions
```

## Quick Start with Docker

### Development Setup

1. **Clone and navigate to the project:**
   ```bash
   cd backend
   ```

2. **Start the services:**
   ```bash
   # Using Makefile (recommended)
   make dev
   
   # Or using docker-compose directly
   docker-compose up --build
   ```

3. **Access the application:**
   - **API**: `http://localhost:8000`
   - **Swagger UI**: `http://localhost:8000/docs`
   - **ReDoc**: `http://localhost:8000/redoc`

### Production Setup

1. **Create environment file:**
   ```bash
   cp .env.example .env.prod
   # Edit .env.prod with your production values
   ```

2. **Start production services:**
   ```bash
   # Using Makefile (recommended)
   make prod
   
   # Or using docker-compose directly
   docker-compose -f docker-compose.prod.yml up --build -d
   ```

## Manual Setup (Without Docker)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Database Setup

1. Install PostgreSQL and create a database:
```sql
CREATE DATABASE ai_chat_db;
```

2. Update the database URL in `.env`:
```
DATABASE_URL=postgresql://username:password@localhost:5432/ai_chat_db
```

3. Run database migrations:
```bash
alembic upgrade head
```

### 3. Environment Configuration

Update the `.env` file with your settings:
```
DATABASE_URL=postgresql://username:password@localhost:5432/ai_chat_db
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=development
```

### 4. Run the Application

```bash
python run.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register a new user
- `POST /api/v1/auth/login` - Login user
- `GET /api/v1/auth/me` - Get current user info

### Company Management
- `POST /api/v1/companies/` - Create a new company
- `GET /api/v1/companies/` - Get user's companies
- `GET /api/v1/companies/{company_id}` - Get company details with files
- `PUT /api/v1/companies/{company_id}` - Update company
- `DELETE /api/v1/companies/{company_id}` - Delete company

### Knowledge Base Files
- `POST /api/v1/companies/{company_id}/files` - Upload file to company
- `GET /api/v1/companies/{company_id}/files` - Get company files
- `DELETE /api/v1/companies/{company_id}/files/{file_id}` - Delete file

### Supported File Types
- PDF documents
- Microsoft Word documents (.doc, .docx)
- Microsoft Excel spreadsheets (.xls, .xlsx)
- Plain text files (.txt)
- CSV files
- JSON files

### File Upload Limits
- Maximum file size: 10MB
- Files are stored securely with unique names
- Original filenames are preserved for reference

## Docker Commands

### Using Makefile (Recommended)
```bash
# Development
make dev          # Start development environment
make dev-bg        # Start in background
make dev-logs      # View logs
make dev-down      # Stop services

# Production
make prod          # Start production environment
make prod-logs     # View logs
make prod-down     # Stop services

# Database operations
make migrate       # Run migrations
make migrate-create MESSAGE="Description"  # Create new migration
make db-shell      # Access database shell

# Utilities
make build         # Build Docker images
make clean         # Clean up Docker resources
make shell         # Access application container shell
make health        # Check application health
make help          # Show all available commands
```

### Using Docker Compose Directly

#### Development
```bash
# Start services
docker-compose up --build

# Start in background
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up --build --force-recreate
```

#### Production
```bash
# Start production services
docker-compose -f docker-compose.prod.yml up -d --build

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker-compose.prod.yml down
```

#### Database Operations
```bash
# Run migrations
docker-compose exec app alembic upgrade head

# Create new migration
docker-compose exec app alembic revision --autogenerate -m "Description"

# Access database
docker-compose exec db psql -U postgres -d ai_chat_db
```

## API Documentation

Once the server is running, you can access:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Development

### Database Migrations

To create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

To apply migrations:
```bash
alembic upgrade head
```

### Testing

The API includes basic health check endpoints:
- `GET /` - Root endpoint
- `GET /health` - Health check

## Security Notes

- Change the `SECRET_KEY` in production
- Use environment variables for sensitive configuration
- Consider implementing rate limiting for production use
- Use HTTPS in production
- Update default database passwords in production
