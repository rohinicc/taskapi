variable "aws_region" {
  default = "ap-south-1"
}

variable "project" {
  default = "taskapi"
}

variable "admin_cidr" {
  description = "Your IP for SSH access (set to 0.0.0.0/0 for anywhere)"
  default     = "0.0.0.0/0"
}

variable "ami_id" {
  description = "Ubuntu 24.04 LTS AMI (ap-south-1)"
  default     = "ami-0e35ddab05955cf57"
}

variable "public_key_path" {
  description = "Path to your SSH public key"
  default     = "~/.ssh/id_rsa.pub"
}

variable "github_repo" {
  description = "Your GitHub repo URL for the app (user-data will clone it)"
  default     = "https://github.com/YOUR_GITHUB_USERNAME/taskapi.git"
}

variable "tags" {
  default = {
    Project     = "taskapi"
    ManagedBy   = "terraform"
  }
}
