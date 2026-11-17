variable "aws_profile" {
  type = string
}

variable "region" {
  type = string
}

variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "vpc_cidr" {
  type = string
}

variable "public_subnet_cidr" {
  type = string
}

variable "private_subnet_cidr" {
  type = string
}

variable "proxy_instance_type" {
  type        = string
  description = "EC2 instance type for the reverse proxy."
}

variable "frontend_instance_type" {
  type        = string
  description = "EC2 instance type for the SvelteKit frontend."
}

variable "backend_instance_type" {
  type        = string
  description = "EC2 instance type for CPU ONNX inference."
}
