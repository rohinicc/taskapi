variable "aws_region" {
  default = "ap-south-1"
}

variable "project" {
  default = "taskapi"
}

variable "admin_cidr" {
  description = "Your IP for SSH access"
  default     = "0.0.0.0/0"
}

variable "ami_id" {
  description = "Ubuntu 22.04 LTS AMI (ap-south-1)"
  default     = "ami-0f58b397bc5c1f2e8"
}

variable "control_plane_instance_type" {
  default = "t3.medium"    # min for kubeadm control plane
}

variable "worker_instance_type" {
  default = "t3.small"
}

variable "worker_count" {
  default = 2
}

variable "public_key_path" {
  default = "~/.ssh/id_rsa.pub"
}

variable "tags" {
  default = {
    Project     = "taskapi"
    Environment = "production"
    ManagedBy   = "terraform"
  }
}
