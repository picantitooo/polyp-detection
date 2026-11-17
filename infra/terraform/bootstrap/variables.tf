variable "aws_profile" {
  description = "The AWS profile to use for authentication."
  type        = string  
}

variable "region" {
  description = "The AWS region to deploy resources in."
  type        = string
}     

variable "project" {
  description = "The project name."
  type        = string
}