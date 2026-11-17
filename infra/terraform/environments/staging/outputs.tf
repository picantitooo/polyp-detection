output "ansible_transfer_bucket_name" {
  description = "Private S3 bucket name for temporary Ansible transfers over SSM."
  value       = aws_s3_bucket.ansible_transfer.id
}

output "vpc_id" {
  description = "Staging VPC identifier."
  value       = aws_vpc.main.id
}

output "public_subnet_id" {
  description = "Public subnet identifier for the reverse proxy."
  value       = aws_subnet.public.id
}

output "private_subnet_id" {
  description = "Private subnet identifier for frontend and inference."
  value       = aws_subnet.private.id
}

output "nat_gateway_id" {
  description = "Single staging NAT Gateway identifier."
  value       = aws_nat_gateway.main.id
}

output "frontend_repository_url" {
  description = "Frontend ECR repository URL."
  value       = aws_ecr_repository.frontend.repository_url
}

output "backend_repository_url" {
  description = "Backend ECR repository URL."
  value       = aws_ecr_repository.backend.repository_url
}

output "proxy_security_group_id" {
  description = "Reverse proxy security group identifier."
  value       = aws_security_group.proxy.id
}

output "frontend_security_group_id" {
  description = "Frontend security group identifier."
  value       = aws_security_group.frontend.id
}

output "backend_security_group_id" {
  description = "Backend security group identifier."
  value       = aws_security_group.backend.id
}

output "model_bucket_name" {
  description = "Private S3 bucket name for ONNX model artifacts."
  value       = aws_s3_bucket.models.id
}

output "model_bucket_arn" {
  description = "Private S3 bucket ARN for ONNX model artifacts."
  value       = aws_s3_bucket.models.arn
}

output "proxy_instance_id" {
  description = "Reverse proxy EC2 instance identifier."
  value       = aws_instance.proxy.id
}

output "proxy_public_ip" {
  description = "Elastic IP address of the reverse proxy."
  value       = aws_eip.proxy.public_ip
}

output "frontend_instance_id" {
  description = "Frontend EC2 instance identifier."
  value       = aws_instance.frontend.id
}

output "frontend_private_ip" {
  description = "Private IP address of the frontend."
  value       = aws_instance.frontend.private_ip
}

output "backend_instance_id" {
  description = "Backend EC2 instance identifier."
  value       = aws_instance.backend.id
}

output "backend_private_ip" {
  description = "Private IP address of the backend."
  value       = aws_instance.backend.private_ip
}
