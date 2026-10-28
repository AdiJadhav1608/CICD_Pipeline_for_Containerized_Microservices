pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        timeout(time: 30, unit: 'MINUTES')
    }

    environment {
        AWS_REGION = 'ap-south-1'
        AWS_ACCOUNT_ID = 'YOUR_12_DIGIT_ACCOUNT_ID'
        EKS_CLUSTER = 'YOUR_EKS_CLUSTER_NAME'
        K8S_NAMESPACE = 'default'

        CATALOG_REPOSITORY = 'catalog-service'
        ORDERS_REPOSITORY = 'orders-service'

        DEPLOY_STARTED = 'false'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh '''
                    git log -1 --oneline
                    python3 --version
                    docker --version
                    aws --version
                    kubectl version --client
                '''
            }
        }

        stage('Unit Tests') {
            steps {
                sh '''
                    set -eu
                    for service in catalog orders; do
                      python3 -m pip install -r "services/${service}/requirements.txt"
                      PYTHONPATH="services/${service}" python3 -m unittest discover \\
                        -s "services/${service}" -p 'test_*.py'
                    done
                '''
            }
        }

        stage('Build Images') {
            steps {
                sh '''
                    set -eu
                    docker build -t catalog-service:${BUILD_NUMBER} services/catalog
                    docker build -t orders-service:${BUILD_NUMBER} services/orders
                '''
            }
        }

        stage('Push Images to ECR') {
            when {
                branch 'main'
            }
            steps {
                sh '''
                    set -eu
                    REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

                    aws ecr get-login-password --region "${AWS_REGION}" |
                      docker login --username AWS --password-stdin "${REGISTRY}"

                    docker tag "catalog-service:${BUILD_NUMBER}" \
                      "${REGISTRY}/${CATALOG_REPOSITORY}:${BUILD_NUMBER}"
                    docker tag "orders-service:${BUILD_NUMBER}" \
                      "${REGISTRY}/${ORDERS_REPOSITORY}:${BUILD_NUMBER}"

                    docker push "${REGISTRY}/${CATALOG_REPOSITORY}:${BUILD_NUMBER}"
                    docker push "${REGISTRY}/${ORDERS_REPOSITORY}:${BUILD_NUMBER}"
                '''
            }
        }

        stage('Deploy to EKS') {
            when {
                branch 'main'
            }
            steps {
                script {
                    env.DEPLOY_STARTED = 'true'
                }
                sh '''
                    set -eu
                    REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
                    CATALOG_IMAGE="${REGISTRY}/${CATALOG_REPOSITORY}:${BUILD_NUMBER}"
                    ORDERS_IMAGE="${REGISTRY}/${ORDERS_REPOSITORY}:${BUILD_NUMBER}"

                    aws eks update-kubeconfig --region "${AWS_REGION}" --name "${EKS_CLUSTER}"

                    mkdir -p .rendered
                    sed "s|__CATALOG_IMAGE__|${CATALOG_IMAGE}|g" \
                      k8s/catalog-deployment.yaml > .rendered/catalog-deployment.yaml
                    sed "s|__ORDERS_IMAGE__|${ORDERS_IMAGE}|g" \
                      k8s/orders-deployment.yaml > .rendered/orders-deployment.yaml

                    kubectl apply -n "${K8S_NAMESPACE}" -f .rendered/catalog-deployment.yaml
                    kubectl apply -n "${K8S_NAMESPACE}" -f .rendered/orders-deployment.yaml
                    kubectl apply -n "${K8S_NAMESPACE}" -f k8s/services.yaml

                    kubectl rollout status deployment/catalog-service \
                      -n "${K8S_NAMESPACE}" --timeout=180s
                    kubectl rollout status deployment/orders-service \
                      -n "${K8S_NAMESPACE}" --timeout=180s

                    # Verify the application endpoint from inside each running pod.
                    kubectl exec deployment/catalog-service -n "${K8S_NAMESPACE}" -- \
                      python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=5).read().decode())"
                    kubectl exec deployment/orders-service -n "${K8S_NAMESPACE}" -- \
                      python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=5).read().decode())"
                '''
            }
        }
    }

    post {
        failure {
            script {
                if (env.DEPLOY_STARTED == 'true') {
                    echo 'Deployment stage failed. Attempting rollback to previous revisions.'
                    sh '''
                        set +e
                        aws eks update-kubeconfig --region "${AWS_REGION}" --name "${EKS_CLUSTER}"
                        kubectl rollout undo deployment/catalog-service -n "${K8S_NAMESPACE}"
                        CATALOG_ROLLBACK=$?
                        kubectl rollout undo deployment/orders-service -n "${K8S_NAMESPACE}"
                        ORDERS_ROLLBACK=$?
                        kubectl rollout status deployment/catalog-service -n "${K8S_NAMESPACE}" --timeout=180s
                        kubectl rollout status deployment/orders-service -n "${K8S_NAMESPACE}" --timeout=180s
                        echo "Rollback command exit codes: catalog=${CATALOG_ROLLBACK}, orders=${ORDERS_ROLLBACK}"
                        exit 0
                    '''
                } else {
                    echo 'Failure happened before deployment; skipping Kubernetes rollback.'
                }
            }
        }
        always {
            sh 'rm -rf .rendered'
            echo "Pipeline result: ${currentBuild.currentResult}"
        }
    }
}
