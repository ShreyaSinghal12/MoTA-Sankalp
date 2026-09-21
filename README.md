# MoTA-SANKALP

**Scheme Administration, Network & Knowledge Automated Lifecycle Platform**

A comprehensive Smart India Hackathon 2026 project for the Ministry of Tribal Affairs, Government of India.

## Overview

MoTA-SANKALP is an end-to-end scholarship and fellowship management platform implementing:
- Multi-scheme rule engine (NFST, NOS, etc.)
- Intelligent document processing (OCR, YOLO, field extraction)
- Duplicate detection and fraud risk assessment
- Dual-agent reconciliation workflow
- Officer approval system
- Sanction generation and payment integration

## Technology Stack

### Backend
- Python 3.11+
- FastAPI
- PostgreSQL
- SQLAlchemy
- Pydantic

### Frontend
- React 18+
- Vite
- TypeScript
- Tailwind CSS

### AI/ML (Upcoming)
- YOLO v8 (document detection)
- EasyOCR
- RapidFuzz
- Isolation Forest
- Local LLM with RAG

## Project Status

**Phase 0**: Environment and Project Planning (Current)
- [x] Repository structure created
- [x] Git initialized
- [x] Backend FastAPI setup
- [x] Frontend React + Vite setup
- [x] Health check endpoint implemented
- [ ] Both services running and verified

## Quick Start

### Backend Setup

\\\powershell
cd backend

# Create virtual environment
python -m venv venv
.\\venv\\Scripts\\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run development server
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
\\\

Backend will be available at: http://localhost:8000
Swagger UI: http://localhost:8000/docs

### Frontend Setup

\\\powershell
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
\\\

Frontend will be available at: http://localhost:5173

## API Documentation

Once backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Current endpoints:
- \GET /\ - Root endpoint
- \GET /api/v1/health\ - Health check

## File Structure

See STRUCTURE.md for detailed documentation.

## Development Phases

1. **Phase 0** - Environment Setup (Current)
2. **Phase 1** - FastAPI Foundation
3. **Phase 2** - PostgreSQL & Database Models
4. **Phase 3** - Authentication & RBAC
5. ... (40+ phases planned)

## Security Notes

- Never commit \.env\ files with real secrets
- Use \.env.example\ as template
- All credentials changed before production
- Aadhaar/sensitive data masked in logs
- Database credentials managed via secrets management

## Testing

\\\powershell
cd backend
pytest
\\\

## Docker (Phase 37+)

\\\powershell
docker compose up --build
\\\

## Contributing

1. Create feature branch
2. Make changes following code style
3. Run tests
4. Commit with descriptive message
5. Push to repository

## License

Government of India - Ministry of Tribal Affairs

## Authors

- Student Developer
- Mentor/Advisors (SIH 2026)

---

**Current Phase**: 0 - Environment Setup
**Last Updated**: 2026-09-21
