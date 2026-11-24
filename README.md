# Project 1: Deploy a Containerised FastAPI App to AWS by Hand

## End goal

Understand what happens under the hood when an app goes from "works on my laptop" to "running on AWS".
We do every step manually (console + CLI, no Terraform, no CI/CD) so we feel the pain that later projects automate away.

By the end you should be able to explain, without notes:

- How a VPC, subnets, route tables, and an internet gateway fit together
- How security groups control who can talk to whom
- How an EC2 instance gets permission to pull from ECR (IAM role vs access keys)
- How an image travels: Dockerfile -> local build -> ECR -> EC2
- Why the database sits in a private subnet and how the app still reaches it

## Final architecture

```
                 Internet
                    |
             [Internet Gateway]
                    |
   +---------------- VPC (10.0.0.0/16) -----------------+
   |                                                    |
   |  Public subnet (10.0.1.0/24)                       |
   |    EC2 t3.micro  <- pulls image from ECR           |
   |    runs FastAPI container (port 8000)              |
   |    SG: allow 8000 from my IP, 22 from my IP        |
   |          |                                         |
   |          v  (5432, only from the app's SG)         |
   |  Private subnet A + B (10.0.2.0/24, 10.0.3.0/24)   |
   |    RDS Postgres (db.t3.micro)                      |
   |    SG: allow 5432 from app SG only                 |
   +----------------------------------------------------+

   ECR repo: stores the Docker image
   IAM role on EC2: allows ecr:GetAuthorizationToken + ecr:BatchGetImage
```

Redis is optional in this project. Run it as a second container on the EC2 box
(or skip it) to keep the scope small. ElastiCache comes in a later project.

## The app (keep it tiny, ~1 hour)

FastAPI service with:

- `GET /health` returns `{"status": "ok"}`
- `POST /notes` inserts a note into Postgres
- `GET /notes` lists notes (optionally cached in Redis)
  Config comes only from environment variables: `DATABASE_URL`, `REDIS_URL`.
  No secrets in the image or the repo.

## Plan

### Step 1: Run it locally

- Write the FastAPI app and a `Dockerfile`
- Write `docker-compose.yml` with app + Postgres (+ Redis)
- Verify with `curl localhost:8000/health` and a note create/list round trip
  Done when: `docker compose up` gives a working app on your laptop.

### Step 2: Network (the most educational step)

- Create a VPC (`10.0.0.0/16`)
- Create 1 public subnet and 2 private subnets in different AZs (RDS requires 2 AZs for its subnet group)
- Create an internet gateway, attach it to the VPC
- Public route table: `0.0.0.0/0 -> IGW`, associate with the public subnet
- Private route table: no internet route (local only)
  Done when: you can draw the VPC from memory and explain why the private subnets cannot reach the internet.

### Step 3: Registry

- Create an ECR repository
- Authenticate Docker to ECR, build, tag, and push the image

```bash
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account>.dkr.ecr.<region>.amazonaws.com
docker build -t notes-app .
docker tag notes-app:latest <account>.dkr.ecr.<region>.amazonaws.com/notes-app:latest
docker push <account>.dkr.ecr.<region>.amazonaws.com/notes-app:latest
```

Done when: the image shows up in the ECR console.

### Step 4: Database

- Create security groups first: `app-sg` and `db-sg`
- `db-sg` inbound: TCP 5432 from `app-sg` only (reference the SG, not an IP)
- Create an RDS subnet group using the two private subnets
- Launch RDS Postgres (`db.t3.micro`, not publicly accessible)
- Note the endpoint for `DATABASE_URL`
  Done when: RDS is "Available" and has no public access.

### Step 5: Compute

- Create an IAM role for EC2 with ECR read permissions, and attach it via an instance profile
- Launch a `t3.micro` in the public subnet with `app-sg`
  - `app-sg` inbound: 8000 and 22 from your IP only
- SSH in, install Docker, authenticate to ECR using the instance role (no access keys on the box)
- Pull the image and run it:

```bash
docker run -d --name notes -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:pass@<rds-endpoint>:5432/notes" \
  <account>.dkr.ecr.<region>.amazonaws.com/notes-app:latest
```

Done when: `curl http://<ec2-public-ip>:8000/health` works from your phone or laptop.

### Step 6: Test and observe

- Create and list notes through the public IP
- Read logs with `docker logs notes`
- Check which security group rules and routes made the traffic possible

## Break it on purpose

For each, predict the failure first, then confirm it:

1. Remove the `app-sg -> db-sg` rule: the app should lose its DB connection. Where do you see the error?
2. Detach the IAM role from the EC2 instance: `docker pull` should fail. What does the error say?
3. Stop the container: who notices? (Nobody. This motivates health checks and orchestration in later projects.)
4. Change the SG source to a different IP: the app becomes unreachable from the internet.
5. Reboot the instance: does the container come back? (Hint: it won't without `--restart unless-stopped`.)

## Cost and safety

- Everything fits in the free tier with `t3.micro` and `db.t3.micro`. Check your account's current free tier terms.
- **Day one:** set a billing alarm (AWS Budgets) at a small threshold.
- Don't create a NAT gateway for this project. It bills hourly and isn't needed.
- **Teardown at the end of every session:** terminate EC2, delete RDS (skip the final snapshot), delete the ECR images, then the VPC.
- Never commit AWS keys. Use an IAM user or Identity Center with CLI profiles, and keep the root account unused.

## What this sets up

Each later project automates one part of this one:

| Later project          | What it replaces                        |
| ---------------------- | --------------------------------------- |
| CI with GitHub Actions | Manual build and push (Step 3)          |
| CD to ECS/EKS          | Manual `docker run` on EC2 (Step 5)     |
| Terraform/CDK          | All the console clicking (Steps 2 to 5) |
| Observability          | Reading `docker logs` over SSH (Step 6) |

## Progress checklist

- [ ] App runs locally with docker compose
- [ ] VPC, subnets, IGW, route tables created
- [ ] Image pushed to ECR
- [ ] RDS running in private subnets, locked to `app-sg`
- [ ] EC2 running the container via IAM role (no keys)
- [ ] App reachable from the public IP
- [ ] All five "break it" experiments done and noted below
- [ ] Everything torn down, billing alarm confirmed

## Notes / what broke

_Write what you learned here as you go._
