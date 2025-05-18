pipeline {
  agent any

  environment {
    REGISTRY = "registry.registry.svc.cluster.local:5000"
    IMAGE_NAME = "mlapp"
    IMAGE_TAG = "${env.BUILD_NUMBER}-${env.GIT_COMMIT.take(7)}"
    IMAGE_FULL = "${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"

    GITOPS_REPO = "https://github.com/sittollsCM/devops-iitu-infra.git"
    GITOPS_PATH = "gitops/apps/mlapp/values.yaml"
    GITOPS_DIR = "devops-iitu-infra"
  }

  stages {
    stage('Build') {
      steps {
        echo "Building Docker image: ${IMAGE_FULL}"
        sh "docker build -t ${IMAGE_FULL} ."
      }
    }

    stage('Test') {
      steps {
        echo "Running syntax/lint tests"
        sh "python3 -m py_compile $(find . -name '*.py')"
      }
    }

    stage('Deploy') {
      steps {
        echo "Pushing image to local registry"
        sh "docker push ${IMAGE_FULL}"

        echo "Cloning GitOps repo"
        sh "git clone ${GITOPS_REPO} ${GITOPS_DIR}"

        echo "Updating image tag in values.yaml"
        sh """
          sed -i 's|repository:.*|repository: ${REGISTRY}/${IMAGE_NAME}|' ${GITOPS_DIR}/${GITOPS_PATH}
          sed -i 's|tag:.*|tag: ${IMAGE_TAG}|' ${GITOPS_DIR}/${GITOPS_PATH}
        """

        echo "Committing and pushing updated values.yaml"
        dir("${GITOPS_DIR}") {
          sh """
            git config user.email "jenkins@ci.local"
            git config user.name "Jenkins CI"
            git add ${GITOPS_PATH}
            git commit -m 'Deploy ${IMAGE_NAME}:${IMAGE_TAG}'
            git push origin HEAD
          """
        }
      }
    }
  }

  post {
    failure {
      echo "Pipeline failed"
    }
    success {
      echo "ML App ${IMAGE_TAG} was updated successfully"
    }
  }
}
