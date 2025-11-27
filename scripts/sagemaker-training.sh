#!/bin/bash
# SageMaker Training Job Submission - Compact Version

set -e

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
ECR_REPO_NAME="${ECR_REPO_NAME:-mlops-stock-training}"
ROLE_NAME="${SAGEMAKER_ROLE_NAME:-SageMakerExecutionRole}"
S3_FEATURES="${S3_BUCKET_FEATURES:-mlops-stock-features}"
S3_MODELS="${S3_BUCKET_MODELS:-mlops-stock-models}"
INSTANCE_TYPE="${INSTANCE_TYPE:-ml.m5.large}"

# Get AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
IMAGE_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}:latest"
ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/${ROLE_NAME}"
JOB_NAME="mlops-training-$(date +%Y%m%d-%H%M%S)"

echo "🚀 Submitting SageMaker training job..."
echo "   Image: $IMAGE_URI"
echo "   Instance: $INSTANCE_TYPE"
echo "   Job: $JOB_NAME"
echo ""

# Quick checks
aws ecr describe-images --repository-name "$ECR_REPO_NAME" --image-ids imageTag=latest --region "$AWS_REGION" &>/dev/null || {
    echo "❌ ECR image not found. Push it first: docker push $IMAGE_URI"
    exit 1
}

# Create temporary JSON file
TMP_JSON=$(mktemp)
cat > "$TMP_JSON" <<EOF
{
  "TrainingJobName": "$JOB_NAME",
  "RoleArn": "$ROLE_ARN",
  "AlgorithmSpecification": {
    "TrainingImage": "$IMAGE_URI",
    "TrainingInputMode": "File",
    "ContainerEntrypoint": ["python", "-m", "mlops_stock.models.train"]
  },
  "ResourceConfig": {
    "InstanceType": "$INSTANCE_TYPE",
    "InstanceCount": 1,
    "VolumeSizeInGB": 30
  },
  "OutputDataConfig": {
    "S3OutputPath": "s3://${S3_MODELS}/sagemaker-output"
  },
  "StoppingCondition": {
    "MaxRuntimeInSeconds": 3600
  },
  "Environment": {
    "USE_S3": "true",
    "S3_BUCKET_FEATURES": "$S3_FEATURES",
    "S3_BUCKET_MODELS": "$S3_MODELS",
    "AWS_REGION": "$AWS_REGION"
  }
}
EOF

# Submit job using JSON file
aws sagemaker create-training-job \
    --cli-input-json "file://$TMP_JSON" \
    --region "$AWS_REGION" > /dev/null

# Clean up
rm "$TMP_JSON"

echo "✅ Job submitted: $JOB_NAME"
echo "$JOB_NAME" > .sagemaker-last-job.txt
echo ""
echo "Monitor: aws sagemaker describe-training-job --training-job-name $JOB_NAME --region $AWS_REGION --query 'TrainingJobStatus' --output text"
echo "Console: https://console.aws.amazon.com/sagemaker/home?region=$AWS_REGION#/training-jobs/$JOB_NAME"