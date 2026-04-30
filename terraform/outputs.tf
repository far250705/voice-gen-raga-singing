output "app_url" {
  value = "https://${azurerm_linux_web_app.raga.default_hostname}"
}
