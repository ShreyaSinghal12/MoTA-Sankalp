# MoTA-SANKALP DevOps

## Quick Start with Docker Compose

```bash
chmod +x deploy.sh
./deploy.sh
```

## Kubernetes Deployment

```bash
kubectl apply -f kubernetes/

# Verify deployment
kubectl get pods
kubectl get services
```

## PostgreSQL Backup

```bash
docker exec mota-sankalp-postgresql pg_dump -U mota_user -d mota_sankalp > backup.sql
```

## Environment Variables

Create `.env.production`:
```
DATABASE_URL=postgresql://mota_user:password@localhost:5432/mota_sankalp
JWT_SECRET_KEY=your-production-secret-key
UPLOAD_DIR=/data/uploads
```
