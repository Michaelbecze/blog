# Deploying the StrongSwan Lab with Terraform

In Part 1, we manually configured StrongSwan inside Azure. For this lab, I am going yo use **Infrastructure as Code (IaC)** to deploy the entire environment in minutes using **Terraform**. For now we are just going tp build out the Azure side of the Lab but with the versatility of terriform we can easily add the Cisco routers to the config. By using terriform I am able to quickly and easily spin up labs in Azure and then take them down with nothing left behind. If you are learning Azure this is great way to deploy some complex Labs without have to endless click through menus. 

## What Is Terraform?

Terraform is an open-source Infrastructure as Code tool created by HashiCorp. It allows you to define infrastructure in declarative configuration files and then provision it automatically.

Instead of manually clicking through the Azure portal, we will describe:
- Resource Groups  
- Virtual Networks  
- Subnets  
- Network Interfaces  
- Security Rules  
- Virtual Machines  

Terraform reads the configuration, builds a dependency graph, and deploys everything in the correct order.

---

# Installing Terraform

I am using an Ubuntu Machine to run Terriform but it is supported on Mac and Windows as well. Here is the install for Ubuntu Linux. 
```bash
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -  
sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"  
sudo apt-get  update && sudo apt-get install terraform 
```
Verify installation:

```bash
terraform version
```
# Basic Command
Before we start looking at the script I want to go over the 4 commands that are used the most and their fucntion. We will use the following workflow to deploy and manage the lab environment.

### Initialize
```bash
terraform init
```
Initializes the working directory. This downloads the required providers (such as AzureRM) and prepares Terraform to manage the configuration. You only need to run this once per directory, or whenever provider versions change.

### Preview Changes
```bash
terraform plan
```
Generates an execution plan showing what Terraform will create, modify, or delete. This allows you to review changes before applying them.

### Apply Changes
```bash
terraform apply
```

Creates or updates the infrastructure based on the configuration files. Terraform will prompt for confirmation before making changes.

### Destroy Resources
```bash
terraform destroy
```
Removes all resources defined in the configuration. This is especially useful for lab environments, allowing you to tear everything down cleanly when finished.

---
# Loggin into Azure

Before running Terraform, you must authenticate to Azure so the AzureRM provider can create and manage resources.

The easiest method for lab environments is using the Azure CLI.

### Install Azure CLI (if needed)
Follow the official installation instructions for your OS: https://learn.microsoft.com/cli/azure/install-azure-cli

Verify installation:
```
az version
```
### Log in to Azure
Simply run this command and it will promt you for your azure credentials that you will login with
```
az login
```

# The Terrifor Script
First thing that we need to do is create a fiel called ```main.tf``` this is where the terriform configutaion is stored and the file that we will be editing.

### 1. Terraform and Provider Configuration
```hcl
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
```

**What this does:**
- **`terraform` block**: Declares which providers we need. Think of providers as plugins that let Terraform talk to different cloud platforms.
- **`required_providers`**: Specifies we need the Azure Resource Manager provider (azurerm) version 3.x
- **`provider "azurerm"`**: Configures the Azure provider. The empty `features {}` block is required by the Azure provider.

**Authentication:** Terraform uses environment variables (`ARM_CLIENT_ID`, `ARM_CLIENT_SECRET`, `ARM_SUBSCRIPTION_ID`, `ARM_TENANT_ID`) to authenticate with Azure. These should be set before running Terraform commands.

### 2. Variables - Making Configuration Flexible
```hcl
variable "resource_group_name" {
  default = "strongswan-rg"
}

variable "location" {
  default = "eastus"
}

variable "vm_name" {
  default = "strongswan-vm"
}

variable "admin_username" {
  default = "azureuser"
}

variable "ssh_public_key_path" {
  default = "~/.ssh/id_rsa.pub"
}
```

**What this does:**
- Defines input variables with default values
- Makes the configuration reusable - change the defaults or pass different values at runtime
- `default` values mean you don't have to specify them when running `terraform apply`

**Best practice:** Variables make your code DRY (Don't Repeat Yourself) and easier to customize for different environments.

### 3. Resource Group - The Container
```hcl
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
}
```

**What this does:**
- Creates an Azure Resource Group - a logical container for related resources
- Uses the variables we defined above (notice `var.resource_group_name`)

**Why it matters:** Resource groups let you manage lifecycle, permissions, and billing for related resources as a unit.

### 4. Virtual Network and Subnet
```hcl
resource "azurerm_virtual_network" "main" {
  name                = "${var.vm_name}-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
}

resource "azurerm_subnet" "main" {
  name                 = "${var.vm_name}-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.1.0/24"]
}
```

**What this does:**
- **VNet**: Creates a virtual network with a 10.0.0.0/16 address space (65,536 addresses)
- **Subnet**: Carves out a 10.0.1.0/24 subnet (256 addresses) within that VNet
- **String interpolation**: `"${var.vm_name}-vnet"` creates dynamic names like "strongswan-vm-vnet"

**Key Terraform concept - Resource References:**
- `azurerm_resource_group.main.location` references the location from the resource group we created
- `azurerm_virtual_network.main.name` references the VNet's name
- Terraform automatically understands dependencies: it will create the VNet before the subnet, and the resource group before both

### 5. Public IP Address
```hcl
resource "azurerm_public_ip" "main" {
  name                = "${var.vm_name}-public-ip"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  allocation_method   = "Static"
  sku                 = "Standard"
}
```

**What this does:**
- Creates a static public IP address
- **Static vs Dynamic**: Static means the IP won't change even if the VM is stopped/started
- **Standard SKU**: Required for zone-redundant deployments and certain load balancer configurations

**Important detail:** This public IP will be automatically injected into the StrongSwan configuration later!

### 6. Network Security Group - The Firewall Rules
```hcl
resource "azurerm_network_security_group" "main" {
  name                = "${var.vm_name}-nsg"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  security_rule {
    name                       = "SSH"
    priority                   = 1001
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "IPSec-IKE"
    priority                   = 1002
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Udp"
    source_port_range          = "*"
    destination_port_range     = "500"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "IPSec-NAT-T"
    priority                   = 1003
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Udp"
    source_port_range          = "*"
    destination_port_range     = "4500"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}
```

**What this does:**
- Creates firewall rules for the network
- **SSH (port 22)**: For remote management
- **UDP 500**: IKE (Internet Key Exchange) - IPsec negotiation
- **UDP 4500**: NAT-T (NAT Traversal) - IPsec through NAT devices

**Security note:** In production, restrict `source_address_prefix` to specific IP ranges instead of "*" (anywhere).

### 7. Network Interface - Connecting the VM to the Network
```hcl
resource "azurerm_network_interface" "main" {
  name                = "${var.vm_name}-nic"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.main.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.main.id
  }
}

resource "azurerm_network_interface_security_group_association" "main" {
  network_interface_id      = azurerm_network_interface.main.id
  network_security_group_id = azurerm_network_security_group.main.id
}
```

**What this does:**
- Creates a virtual NIC for the VM
- Attaches it to the subnet
- Associates the public IP address
- Applies the security group rules

**Key point:** The NIC is the "glue" that connects the VM to the network infrastructure.

### 8. The Virtual Machine
```hcl
resource "azurerm_linux_virtual_machine" "main" {
  name                = var.vm_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  size                = "Standard_B2s"
  admin_username      = var.admin_username

  network_interface_ids = [
    azurerm_network_interface.main.id,
  ]

  admin_ssh_key {
    username   = var.admin_username
    public_key = file(var.ssh_public_key_path)
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }

  custom_data = base64encode(templatefile("${path.module}/cloud-init.yaml", {
    public_ip = azurerm_public_ip.main.ip_address
  }))
}
```

**What this does:**
- **VM size**: Standard_B2s (2 vCPU, 4GB RAM) - burstable, cost-effective
- **Authentication**: Uses SSH key (more secure than passwords)
- **`file()` function**: Reads your SSH public key from disk
- **OS image**: Ubuntu 22.04 LTS from Canonical
- **`custom_data`**: This is the magic! It runs cloud-init during first boot

**The Critical Part - custom_data:**
```hcl
custom_data = base64encode(templatefile("${path.module}/cloud-init.yaml", {
  public_ip = azurerm_public_ip.main.ip_address
}))
```

- **`templatefile()`**: Reads the cloud-init.yaml file and replaces variables
- **`public_ip = azurerm_public_ip.main.ip_address`**: Passes the public IP to the template
- **`base64encode()`**: Azure requires custom_data to be base64 encoded



 
