#!/bin/bash
# Monitor SageMaker Job - Compact Version

JOB_NAME="${1:-$(cat .sagemaker-last-job.txt 2>/dev/null)}"
AWS_REGION="${AWS_REGION:-us-east-1}"

[ -z "$JOB_NAME" ] && { echo "Usage: $0 <job-name>"; exit 1; }

echo "Monitoring: $JOB_NAME"
while true; do
    STATUS=$(aws sagemaker describe-training-job --training-job-name "$JOB_NAME" --region "$AWS_REGION" --query 'TrainingJobStatus' --output text 2>/dev/null)
    [ -z "$STATUS" ] && { echo "❌ Job not found"; exit 1; }
    
    case "$STATUS" in
        "InProgress") echo "🟡 $STATUS..."; sleep 10 ;;
        "Completed") 
            echo "✅ $STATUS!"
            aws sagemaker describe-training-job --training-job-name "$JOB_NAME" --region "$AWS_REGION" --query 'ModelArtifacts.S3ModelArtifacts' --output text
            break ;;
        "Failed")
            echo "❌ $STATUS"
            aws sagemaker describe-training-job --training-job-name "$JOB_NAME" --region "$AWS_REGION" --query 'FailureReason' --output text
            break ;;
        *) echo "$STATUS"; sleep 10 ;;
    esac
done