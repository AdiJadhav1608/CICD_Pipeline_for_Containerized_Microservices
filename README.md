# CI/CD Pipeline for Containerized Microservices

A beginner-friendly DevOps portfolio project that builds, tests, containerizes, and deploys two small Python microservices to Amazon EKS using Jenkins, Docker, Amazon ECR, and Kubernetes. The pipeline includes deployment health checks and an automatic rollback attempt when a deployment fails.

> **Important:** This repository is a runnable starter template, not a preconfigured AWS environment. You must create the AWS resources, configure Jenkins credentials and permissions, and replace the example values before running it. AWS resources can incur charges.

## 1. Project overview

When code is merged into `main`, a GitHub webhook (or a Jenkins Multibranch Pipeline scan) starts Jenkins. Jenkins runs unit tests, builds Docker images, pushes versioned images to ECR, deploys the manifests to EKS, and checks rollout/application health.

### Pipeline flow

1. Developer merges code into `main`.
2. Jenkins checks out the repository.
3. Jenkins runs unit tests for both services.
4. Jenkins builds versioned Docker images.
5. Jenkins authenticates to Amazon ECR and pushes images.
6. Jenkins renders and applies Kubernetes manifests to EKS.
7. Jenkins waits for rollout completion and checks `/health` inside each pod.
8. If a deployment-stage check fails, Jenkins attempts to roll back both Deployments to their previous revisions.

Rollback requires a prior successful Deployment revision. On the very first deployment, there may be no previous revision to restore.

## 2. Architecture

- **GitHub:** source control and change trigger.
- **Jenkins:** pipeline orchestration.
- **Docker:** builds immutable, build-number-tagged images.
- **Amazon ECR:** private image registry.
- **Amazon EKS:** managed Kubernetes cluster.
- **Kubernetes Deployments and Services:** run and expose the microservices inside the cluster.
- **Readiness probes and `/health`:** help Kubernetes and Jenkins check application health.

Services included:
- `catalog-service`: returns a sample product catalog.
- `orders-service`: returns a sample order.

These are demonstration services; they do not use a database.

## 3. Repository structure

```text
CICD_Pipeline_for_Containerized_Microservices/
├── services/
│   ├── catalog/
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── test_app.py
│   └── orders/
│       ├── app.py
│       ├── requirements.txt
│       ├── Dockerfile
│       └── test_app.py
├── k8s/
│   ├── catalog-deployment.yaml
│   ├── orders-deployment.yaml
│   └── services.yaml
├── scripts/
│   └── local-test.sh
├── .gitignore
├── .dockerignore
└── Jenkinsfile
```

## 4. Prerequisites

Install or configure the following before running the AWS pipeline:

- Git and GitHub repository
- Jenkins with Pipeline and Git plugins
- A Linux Jenkins agent with Docker Engine, AWS CLI v2, `kubectl`, Python 3, and `pip`
- AWS account, ECR repositories, and an EKS cluster
- IAM permissions for ECR push and EKS access
- Kubernetes access for the Jenkins identity
- A GitHub webhook pointing to your Jenkins endpoint, or a configured Multibranch Pipeline

The Jenkins agent needs access to a Docker daemon. Avoid giving untrusted pull-request builds access to privileged Docker or production AWS credentials.

## 5. Create AWS resources

Choose the correct region and account ID for your environment.

```bash
aws sts get-caller-identity
aws configure get region
```

Create two ECR repositories (if they do not already exist):

```bash
aws ecr create-repository --repository-name catalog-service
aws ecr create-repository --repository-name orders-service
```

Create or use an existing EKS cluster. For a new cluster, follow the official EKS setup guide:
https://docs.aws.amazon.com/eks/latest/userguide/getting-started.html

Configure `kubectl` access:

```bash
aws eks update-kubeconfig --region YOUR_AWS_REGION --name YOUR_EKS_CLUSTER
kubectl get nodes
```

The Jenkins AWS identity must be granted the appropriate ECR permissions and EKS cluster access. Follow least privilege; do not paste AWS access keys into the `Jenkinsfile` or commit credentials.

## 6. Configure Jenkins

1. Install the Jenkins **Pipeline** and **Git** plugins.
2. Ensure the Jenkins agent has Docker, AWS CLI, `kubectl`, Python 3, and pip available in `PATH`.
3. Configure AWS authentication for the Jenkins agent. Prefer an IAM role (for example, an EC2 instance profile) or a supported Jenkins credentials integration over long-lived access keys.
4. Grant the Jenkins identity permission to push to both ECR repositories and authenticate to the EKS cluster.
5. Grant the Jenkins Kubernetes identity permission to manage the project's Deployments and Services in the target namespace.
6. Create a **Multibranch Pipeline** for the GitHub repository, or configure a Pipeline job with a GitHub webhook. The pipeline's deployment stages run only for `main` when `BRANCH_NAME` is supplied by a Multibranch Pipeline.
7. Configure the GitHub webhook to use the Jenkins endpoint appropriate to your job and installation. Use HTTPS and protect the Jenkins endpoint.

### Jenkins agent tools check

Run these commands on the Jenkins agent:

```bash
git --version
docker --version
aws --version
kubectl version --client
python3 --version
pip3 --version
```

## 7. Configure the pipeline

Edit the `environment` section at the top of `Jenkinsfile`:

```groovy
AWS_REGION = 'ap-south-1'
AWS_ACCOUNT_ID = 'YOUR_12_DIGIT_ACCOUNT_ID'
EKS_CLUSTER = 'YOUR_EKS_CLUSTER_NAME'
K8S_NAMESPACE = 'default'
```

Use the AWS region where your ECR repositories and EKS cluster exist. The sample defaults to `ap-south-1`; replace it if your resources are elsewhere.

Create the Kubernetes namespace if you choose a namespace other than `default`:

```bash
kubectl create namespace microservices
```

Then set `K8S_NAMESPACE = 'microservices'` in the pipeline.

## 8. Run locally first

Run the unit tests:

```bash
python3 -m pip install -r services/catalog/requirements.txt
python3 -m unittest discover -s services/catalog -p 'test_*.py'

python3 -m pip install -r services/orders/requirements.txt
python3 -m unittest discover -s services/orders -p 'test_*.py'
```

Build each image:

```bash
docker build -t catalog-service:local services/catalog
docker build -t orders-service:local services/orders
```

Run the catalog service:

```bash
docker run --rm -p 5001:5000 catalog-service:local
```

In another terminal:

```bash
curl http://localhost:5001/health
curl http://localhost:5001/
```

Run the orders service in a separate terminal using port 5002:

```bash
docker run --rm -p 5002:5000 orders-service:local
```

Then check:

```bash
curl http://localhost:5002/health
curl http://localhost:5002/
```

Or run the test script:

```bash
bash scripts/local-test.sh
```

The local test script runs unit tests and builds the Docker images; it does not start containers.

## 9. Deploy through Jenkins

1. Commit and push the project to GitHub.
2. Ensure the webhook or Multibranch Pipeline is configured.
3. Merge a tested change into `main`.
4. Open Jenkins and inspect the pipeline stages.
5. Confirm that images were pushed to both ECR repositories.
6. Verify Kubernetes status:

```bash
kubectl get deployments -n default
kubectl get pods -n default
kubectl get services -n default
```

To inspect a failed workload:

```bash
kubectl describe deployment catalog-service -n default
kubectl describe deployment orders-service -n default
kubectl get events -n default --sort-by=.metadata.creationTimestamp
kubectl logs deployment/catalog-service -n default
kubectl logs deployment/orders-service -n default
```

The included Kubernetes Services are `ClusterIP`, so they are reachable from inside the cluster, not directly from the public internet. For an external endpoint, configure an ingress/load balancer intentionally and secure it.

## 10. How automatic rollback works

The pipeline marks the deployment stage as started before applying new manifests. If the deployment stage fails, Jenkins attempts:

```bash
kubectl rollout undo deployment/catalog-service -n default
kubectl rollout undo deployment/orders-service -n default
```

It then waits for the rollback rollouts to finish. Kubernetes supports rolling back to a prior Deployment revision; see:
https://kubernetes.io/docs/concepts/workloads/controllers/deployment/

The pipeline uses Kubernetes rollout status plus an in-pod HTTP health check. For production, consider stronger end-to-end checks, metrics-based analysis, database migration strategy, deployment approvals, and a tested rollback policy. A failed Jenkins build does not itself prove that user-facing traffic was affected or recovered within a particular time.

## 11. Troubleshooting

| Problem | Things to check |
|---|---|
| `aws: command not found` | Install AWS CLI on the Jenkins agent and check `PATH`. |
| Docker permission denied | Check Docker daemon access and the Jenkins agent user's permissions. |
| ECR login/push fails | Verify region, account ID, repository names, and IAM permissions. |
| `kubectl` cannot connect | Run `aws eks update-kubeconfig`; verify cluster name, region, network, and IAM/EKS access. |
| `ImagePullBackOff` | Confirm the image URI/tag and that EKS nodes can pull from ECR. |
| Rollout times out | Inspect pod events, logs, readiness probe, resource limits, and image availability. |
| Rollback has no revision | This can occur on the first deployment; deploy a known-good version first. |
| Pipeline does not start on merge | Check webhook delivery, job type, branch configuration, and Jenkins logs. |

## 12. Security notes

- Never commit AWS keys, tokens, kubeconfig files, or `.env` secrets.
- Prefer short-lived IAM role credentials for the Jenkins agent.
- Restrict Jenkins IAM and Kubernetes permissions to the required resources.
- Use unique image tags such as the Jenkins build number; avoid deploying `latest`.
- Protect the `main` branch and require code review/tests.
- Use HTTPS for webhook traffic and restrict who can trigger privileged deployments.

## 13. Cleanup

Delete only resources created specifically for this project. These commands remove the Kubernetes workloads:

```bash
kubectl delete -f k8s/services.yaml --ignore-not-found
kubectl delete deployment catalog-service orders-service -n default --ignore-not-found
```

If you created a separate namespace for the project, you can delete it after confirming it contains no other workloads:

```bash
kubectl delete namespace microservices
```

ECR repositories, EKS clusters, load balancers, NAT gateways, and other AWS resources may incur charges. Review your resources and delete only those you no longer need. Do not delete a shared cluster or shared network resources just for this demo.

## 14. Resume description

**CI/CD Pipeline for Containerized Microservices**
- Built a Jenkins pipeline to test, containerize, push images to Amazon ECR, and deploy microservices to Amazon EKS on merges to `main`.
- Added rollout and application health checks with an automated rollback attempt to restore the previous Kubernetes Deployment revision when deployment checks fail.

Only claim measured recovery-time improvements after testing and recording the result.

## 15. Official references

- Jenkins Pipeline syntax: https://www.jenkins.io/doc/book/pipeline/syntax/
- Jenkins and Docker: https://www.jenkins.io/doc/book/pipeline/docker/
- AWS Jenkins and EKS example: https://builder.aws.com/content/3Kff2K3U18qKiZxXbh3LUtio3qO/jenkins
- Kubernetes Deployments and rollback: https://kubernetes.io/docs/concepts/workloads/controllers/deployment/
- Amazon EKS getting started: https://docs.aws.amazon.com/eks/latest/userguide/getting-started.html
