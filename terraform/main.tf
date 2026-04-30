terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "raga" {
  name     = "ai-singer-rg"
  location = "South India"
}

resource "azurerm_service_plan" "raga" {
  name                = "ASP-aisingerrg-836d"
  resource_group_name = azurerm_resource_group.raga.name
  location            = azurerm_resource_group.raga.location
  os_type             = "Linux"
  sku_name            = "F1"
}

resource "azurerm_linux_web_app" "raga" {
  name                = "ai-singer-app-123"
  resource_group_name = azurerm_resource_group.raga.name
  location            = azurerm_resource_group.raga.location
  service_plan_id     = azurerm_service_plan.raga.id
  https_only          = true

  ftp_publish_basic_authentication_enabled       = false
  webdeploy_publish_basic_authentication_enabled = false

  site_config {
    always_on        = false
    app_command_line = "gunicorn --bind=0.0.0.0 --timeout 600 app:app"
    ftps_state       = "FtpsOnly"
    application_stack {
      python_version = "3.10"
    }
  }

  app_settings = {
    "GEMINI_API_KEY"                 = var.gemini_api_key
    "SUNO_API_KEY"                   = var.suno_api_key
    "SCM_DO_BUILD_DURING_DEPLOYMENT" = "1"
    "PYTHONUNBUFFERED"               = "1"
  }

  logs {
    detailed_error_messages = false
    failed_request_tracing  = false
    http_logs {
      file_system {
        retention_in_days = 1
        retention_in_mb   = 35
      }
    }
  }
}
