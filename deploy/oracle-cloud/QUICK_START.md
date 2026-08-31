# 🚀 Quick Start - Oracle Cloud Deployment

## Prerequisites

- Oracle Cloud Always Free account
- Domain name (optional)
- SSH access to Oracle Cloud instance

## 5-Minute Deployment

### 1. SSH into Oracle Cloud Instance
```bash
ssh ubuntu@your-oracle-ip
```

### 2. Run Deployment Script
```bash
git clone https://github.com/prnvmishra/SPRINTFORGE.git
cd SPRINTFORGE/deploy/oracle-cloud
./deploy.sh
```

### 3. Configure Environment
```bash
cd ~/sprintforge/SPRINTFORGE
nano .env
```

Fill in:
- `DATABASE_URL` (from Neon)
- `AUTH_SECRET` (generate with `openssl rand -hex 32`)
- `CORS_ORIGINS` (your Vercel URL)

### 4. Setup Case Store (from local machine)
```bash
# On your local machine:
cd backend
python -m scripts.build_test_cases
python -m scripts.split_case_bank
python -m scripts.build_curriculum_manifest
tar czf cases.tgz -C app/data cases
scp cases.tgz ubuntu@your-oracle-ip:~/sprintforge/SPRINTFORGE/backend/

# On Oracle Cloud:
cd ~/sprintforge/SPRINTFORGE/backend
tar xzf cases.tgz
rm cases.tgz
```

### 5. Restart Services
```bash
cd ~/sprintforge/SPRINTFORGE/deploy/oracle-cloud
docker-compose -f docker-compose.prod.yml restart
```

### 6. Verify Deployment
```bash
./monitor.sh
```

## Access Points

- **Backend API:** `http://your-oracle-ip:8000`
- **Health Check:** `http://your-oracle-ip:8000/health`
- **API Docs:** `http://your-oracle-ip:8000/docs`

## Update Vercel Frontend

1. Go to Vercel dashboard → Settings → Environment Variables
2. Update `NEXT_PUBLIC_API_URL` to `http://your-oracle-ip:8000`
3. Redeploy

## Optional: Setup SSL

```bash
./setup-ssl.sh your-domain.com
```

## Useful Commands

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Stop services
docker-compose -f docker-compose.prod.yml down

# Check health
./monitor.sh

# Update code
cd ~/sprintforge/SPRINTFORGE
git pull
docker-compose -f deploy/oracle-cloud/docker-compose.prod.yml up -d --build
```

## Troubleshooting

### Backend not starting
```bash
docker logs sprintforge-api
```

### Piston not working
```bash
docker logs sprintforge-piston
docker restart sprintforge-piston
```

### Case store missing
```bash
ls -la backend/app/data/cases/
# Should show: visible.json, modules.json, hidden/
```

### Port conflicts
```bash
sudo lsof -i :8000
sudo lsof -i :2000
```

## Performance Tips

1. **Use mock AI provider** for free tier
2. **Enable caching** in your application
3. **Monitor resources** with `./monitor.sh`
4. **Optimize database queries** if needed

## Security Checklist

- ✅ Changed `AUTH_SECRET` from default
- ✅ Set `CORS_ORIGIN_REGEX` to empty
- ✅ Using `piston` for code execution
- ✅ Database using PostgreSQL
- ✅ SSL certificate installed (optional but recommended)

## Support

For issues, check:
1. Docker logs: `docker logs sprintforge-api`
2. System health: `./monitor.sh`
3. Network connectivity: `curl http://localhost:8000/health`