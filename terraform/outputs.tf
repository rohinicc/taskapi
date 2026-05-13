output "control_plane_public_ip" {
  value = aws_instance.control_plane.public_ip
}

output "worker_private_ips" {
  value = aws_instance.workers[*].private_ip
}

output "vpc_id" {
  value = module.vpc.vpc_id
}
