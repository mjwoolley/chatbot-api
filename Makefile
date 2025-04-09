# Makefile for chatbot-api Docker build and AWS App Runner deployment

# AWS account and region configuration
AWS_ACCOUNT_ID := 476114130211
AWS_REGION := us-east-1
AWS_PROFILE := admin_profile

# ECR repository and image configuration
ECR_REPO_NAME := chatbot-api
ECR_IMAGE_TAG := latest
ECR_REPO_URI := $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(ECR_REPO_NAME)

# App Runner configuration
APP_RUNNER_SERVICE_NAME := chatbot-api-service-ecr
APP_RUNNER_SERVICE_ARN := arn:aws:apprunner:$(AWS_REGION):$(AWS_ACCOUNT_ID):service/$(APP_RUNNER_SERVICE_NAME)/650f079040d34f67b4dc4f462565ccdc

# Docker image name
IMAGE_NAME := $(ECR_REPO_NAME)

.PHONY: help build tag login push deploy resume pause delete-service create-service run-local all clean

help:
	@echo "Available targets:"
	@echo "  help     - Show this help message"
	@echo "  build    - Build Docker image"
	@echo "  tag      - Tag Docker image for ECR"
	@echo "  login    - Login to ECR"
	@echo "  push     - Push Docker image to ECR"
	@echo "  deploy   - Deploy to App Runner (auto-resumes if paused)"
	@echo "  resume   - Resume a paused App Runner service"
	@echo "  pause    - Pause a running App Runner service"
	@echo "  delete-service - Delete the App Runner service"
	@echo "  create-service - Create a new App Runner service"
	@echo "  run-local - Start Flask server locally for testing"
	@echo "  all      - Run build, tag, login, push, and deploy"
	@echo "  clean    - Remove local Docker image"

build:
	@echo "Building Docker image..."
	docker build -t $(IMAGE_NAME):$(ECR_IMAGE_TAG) .

tag: build
	@echo "Tagging Docker image for ECR..."
	docker tag $(IMAGE_NAME):$(ECR_IMAGE_TAG) $(ECR_REPO_URI):$(ECR_IMAGE_TAG)

login:
	@echo "Logging in to ECR..."
	aws ecr get-login-password --region $(AWS_REGION) --profile $(AWS_PROFILE) | docker login --username AWS --password-stdin $(ECR_REPO_URI)

push: login tag
	@echo "Pushing Docker image to ECR..."
	docker push $(ECR_REPO_URI):$(ECR_IMAGE_TAG)

deploy: push
	@echo "Checking App Runner service status..."
	@STATUS=$$(aws apprunner describe-service --service-arn $(APP_RUNNER_SERVICE_ARN) --region $(AWS_REGION) --profile $(AWS_PROFILE) --query "Service.Status" --output text); \
	if [ "$$STATUS" = "RUNNING" ]; then \
		echo "Service is running, starting deployment..."; \
		aws apprunner start-deployment --service-arn $(APP_RUNNER_SERVICE_ARN) --region $(AWS_REGION) --profile $(AWS_PROFILE); \
	elif [ "$$STATUS" = "PAUSED" ]; then \
		echo "Service is paused. Resuming service before deployment..."; \
		aws apprunner resume-service --service-arn $(APP_RUNNER_SERVICE_ARN) --region $(AWS_REGION) --profile $(AWS_PROFILE); \
		echo "Waiting for service to resume (this may take a few minutes)..."; \
		aws apprunner wait service-updated --service-arn $(APP_RUNNER_SERVICE_ARN) --region $(AWS_REGION) --profile $(AWS_PROFILE); \
		echo "Service resumed. Starting deployment..."; \
		aws apprunner start-deployment --service-arn $(APP_RUNNER_SERVICE_ARN) --region $(AWS_REGION) --profile $(AWS_PROFILE); \
	else \
		echo "Service is in $$STATUS state. Cannot start deployment."; \
		echo "You may need to check the service status in the AWS console or recreate the service."; \
	fi

all: build tag login push deploy

resume:
	@echo "Resuming App Runner service..."
	@STATUS=$$(aws apprunner describe-service --service-arn $(APP_RUNNER_SERVICE_ARN) --region $(AWS_REGION) --profile $(AWS_PROFILE) --query "Service.Status" --output text); \
	if [ "$$STATUS" = "PAUSED" ]; then \
		aws apprunner resume-service --service-arn $(APP_RUNNER_SERVICE_ARN) --region $(AWS_REGION) --profile $(AWS_PROFILE); \
		echo "Service resuming. This may take a few minutes."; \
	else \
		echo "Service is not in PAUSED state (current: $$STATUS). Cannot resume."; \
	fi

pause:
	@echo "Pausing App Runner service..."
	@STATUS=$$(aws apprunner describe-service --service-arn $(APP_RUNNER_SERVICE_ARN) --region $(AWS_REGION) --profile $(AWS_PROFILE) --query "Service.Status" --output text); \
	if [ "$$STATUS" = "RUNNING" ]; then \
		aws apprunner pause-service --service-arn $(APP_RUNNER_SERVICE_ARN) --region $(AWS_REGION) --profile $(AWS_PROFILE); \
		echo "Service pausing. This may take a few minutes."; \
	else \
		echo "Service is not in RUNNING state (current: $$STATUS). Cannot pause."; \
	fi

delete-service:
	@echo "Deleting App Runner service..."
	@echo "WARNING: This will delete the App Runner service $(APP_RUNNER_SERVICE_NAME)!"
	@read -p "Are you sure you want to proceed? (y/n): " confirm && [ "$$confirm" = "y" ] || exit 1
	aws apprunner delete-service --service-arn $(APP_RUNNER_SERVICE_ARN) --region $(AWS_REGION) --profile $(AWS_PROFILE)

create-service: push
	@echo "Creating new App Runner service..."
	aws apprunner create-service \
		--service-name $(APP_RUNNER_SERVICE_NAME) \
		--source-configuration '{"ImageRepository":{"ImageIdentifier":"$(ECR_REPO_URI):$(ECR_IMAGE_TAG)","ImageRepositoryType":"ECR","ImageConfiguration":{"Port":"5000"}},"AuthenticationConfiguration":{"AccessRoleArn":"arn:aws:iam::$(AWS_ACCOUNT_ID):role/AppRunnerECRAccessRole"}}' \
		--instance-configuration InstanceRoleArn=arn:aws:iam::$(AWS_ACCOUNT_ID):role/AppRunnerBedrockRole \
		--region $(AWS_REGION) \
		--profile $(AWS_PROFILE)
	@echo "Note: After creation, update the APP_RUNNER_SERVICE_ARN variable in the Makefile with the new ARN"

run-local:
	@echo "Starting Flask server locally..."
	@echo "API will be available at http://localhost:5000"
	@echo "Press Ctrl+C to stop the server"
	PORT=5000 AWS_REGION_NAME=us-east-1 python run.py

clean:
	@echo "Removing local Docker image..."
	docker rmi $(IMAGE_NAME):$(ECR_IMAGE_TAG) $(ECR_REPO_URI):$(ECR_IMAGE_TAG) || true
