#!groovy

def REGISTRY  = "${Docker_registry}"
def NAMESPACE = "${Docker_namespace}"
def BUILDER   = "${AWX_builder}"
def MOUNT     = "${Docker_mount}"

pipeline {
  agent { label 'docker' }

  options {
    disableConcurrentBuilds()
    timestamps()
    ansiColor('xterm')
  }

  environment {
    VERSION      = sh(script: "cat VERSION", returnStdout: true).trim()
    TAG          = sh(script: "git log --pretty=format:'%h' -n 1", returnStdout: true).trim()
    AWX_BUILDER  = "${REGISTRY}/${NAMESPACE}/${BUILDER}"
    DOCKER_MOUNT = "${MOUNT}"
  }

  stages {
    stage('Get Jenkins vars') {
      steps {
        script {
          JENKINSID = sh(script: 'id -u jenkins', returnStdout: true).trim()
          DOCKERGID = sh(script: 'getent group docker | awk -F ":" \'{ print \$3 }\'', returnStdout: true).trim()
        }
      }
    }

    stage('Create mounts and set permissions') {
        steps {
          sh(script: "mkdir -p .docker .config workspace && chown ${JENKINSID}:${DOCKERGID} .docker .config workspace", returnStdout: true)
        }
    }

    stage('Build and publish image') {
      agent {
        docker { 
          image env.AWX_BUILDER
          args "-u $JENKINSID:$DOCKERGID -v $WORKSPACE:/home/jenkins:rw -v /etc/passwd:/etc/passwd:ro -v /home/jenkins/.docker/config.json:/home/jenkins/.docker/config.json:ro -v /var/run/docker.sock:/var/run/docker.sock -v ${env.DOCKER_MOUNT}"
          label 'docker'
        }
      }
        steps {
          sh "ansible --version"
          sh "git clone https://github.com/ansible/awx-logos.git && cd awx-logos && git checkout 7064a4635a3f857c67a5f5a8608ca52c27cdf26c"
          sh "echo ${env.VERSION}.${env.BUILD_NUMBER}.${env.TAG} > VERSION"
          sh "ansible-playbook -i installer/inventory -e use_container_for_build=false -e awx_official=true -e ssl_certificate=fake -e docker_registry=\"${REGISTRY}\" -e docker_registry_repository=\"${NAMESPACE}\" -e awx_version=\"${env.VERSION}.${env.BUILD_NUMBER}.${env.TAG}\" installer/build.yml -vvv"
          sh "docker rmi awx:latest"
          sh "docker rmi awx:${env.VERSION}.${env.BUILD_NUMBER}.${env.TAG}"
          sh "docker rmi ${REGISTRY}/${NAMESPACE}/awx:latest"
          sh "docker rmi ${REGISTRY}/${NAMESPACE}/awx:${env.VERSION}.${env.BUILD_NUMBER}.${env.TAG}"
        }
    }
  }
}
