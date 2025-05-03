# Cloud-Monitoring-app

# 🐳 Dockerized Flask App on AWS

This project is a Flask web application containerized using Docker and deployed to AWS EC2 with ECR for remote image storage. It supports easy local development, remote hosting, and educational deployment use cases.

---

## 📦 Features

- Flask backend auto-detects templates from the `templates/` folder
- Dockerized with ECR push/pull support
- Runs locally or on EC2 with Elastic IP for stable access
- Simulated domain support via `/etc/hosts`
- Optional Nginx reverse proxy to hide `:5000`

---

## 🧰 Prerequisites

- Python
- Docker
- Git
- AWS

Install dependencies:
```bash
pip install -r requirements.txt
```

> ✅ `requirements.txt` ensures all necessary packages (with versions) are installed in one go.

---

## 🚀 Run Instructions

### Local (Without Docker)

```bash
git clone https://github.com/<your_username>/<your_repo>.git
cd <your_repo>
pip install -r requirements.txt
python app.py
```

### With Docker

```bash
docker build -t <your_docker_image> .
docker run -p 5000:5000 <your_docker_image> //  or you can use any port .!!
```

---

## ☁️ Deploy on AWS

1. Build & tag image
2. Push to Amazon ECR
3. SSH into EC2 instance
4. Pull image & run container
5. Optional: assign Elastic IP for static access

---

## 🌐 Access Options

- `http://<elastic-ip>:5000` or via custom `/etc/hosts` entry
-  Or Use Nginx to route requests from port 80

---

## 🔐 Security Notes

- No sensitive credentials or IPs in this repo
- Keep secrets in environment variables or AWS Secrets Manager
- Avoid committing `.env` files or private keys

---

## ✅ Next Steps

- Add HTTPS (Let's Encrypt)
- Connect a database (e.g., RDS or MongoDB Atlas)
- Set up CI/CD (GitHub Actions or AWS CodePipeline)
