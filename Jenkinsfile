pipeline {
    agent any
 
    stages {
        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }
 
        stage('Build Docker Images') {
            steps {
                script {
                    def services = ["backend", "frontend", "parser", "sniffer"]
                    for (service in services) {
                        sh "docker build -t myapp-${service}:latest ./${service}"
                    }
                }
            }
        }
 
        stage('Push to Docker Registry') {
            steps {
                script {
                    withCredentials([usernamePassword(
                        credentialsId: 'docker-hub-credentials',
                        usernameVariable: 'DOCKER_USERNAME',
                        passwordVariable: 'DOCKER_PASSWORD'
                    )]) {
                        sh "echo \$DOCKER_PASSWORD | docker login -u \$DOCKER_USERNAME --password-stdin"
                        def services = ["backend", "frontend", "parser", "sniffer"]
                        for (service in services) {
                            sh "docker tag myapp-${service}:latest \$DOCKER_USERNAME/myapp-${service}:latest"
                            sh "docker push \$DOCKER_USERNAME/myapp-${service}:latest"
                        }
                    }
                }
            }
        }
 
        stage('Deploy with Docker Compose') {
            steps {
                script {
                    // Stop old containers, pull new images, and start fresh containers
                    sh """
                        docker-compose down
                        docker-compose pull
                        docker-compose up -d
                    """
                }
            }
        }
    }
}
