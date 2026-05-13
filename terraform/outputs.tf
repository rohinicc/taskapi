output "app_public_ip" {
  description = "Public IP of the app instance"
  value       = aws_instance.app.public_ip
}

output "app_url" {
  description = "URL to access the app"
  value       = "http://${aws_instance.app.public_ip}:8000"
}

output "app_docs_url" {
  description = "Swagger docs URL"
  value       = "http://${aws_instance.app.public_ip}:8000/docs"
}

output "ssh_command" {
  description = "SSH command to connect"
  value       = "ssh -i ${var.public_key_path} ubuntu@${aws_instance.app.public_ip}"
}
