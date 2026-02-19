## Deploying the StrongSwan Lab with Terraform

In Part 1, we manually configured StrongSwan inside Azure. For this lab, I am going yo use **Infrastructure as Code (IaC)** to deploy the entire environment in minutes using **Terraform**. For now we are just going to build out the Azure side of the Lab but with the versatility of terriform we can easily add the Cisco routers to the config. By using terriform we are able to quickly and easily spin up labs in Azure and then take them down with nothing left behind. If you are learning Azure this is great way to deploy some complex Labs without have to endless click through menus. 

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

## Installing Terraform

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
Before we start looking at the script I want to go over the 4 commands that are used the most and there fucntion. We will use the following workflow to deploy and manage the lab environment.

#### Initialize
```bash
terraform init
```
Initializes the working directory. This downloads the required providers (such as AzureRM) and prepares Terraform to manage the configuration. You only need to run this once per directory, or whenever provider versions change.

#### Preview Changes
```bash
terraform plan
```
Generates an execution plan showing what Terraform will create, modify, or delete. This allows you to review changes before applying them.

#### Apply Changes
```bash
terraform apply
```

Creates or updates the infrastructure based on the configuration files. Terraform will prompt for confirmation before making changes.

#### Destroy Resources
```bash
terraform destroy
```
Removes all resources defined in the configuration. This is especially useful for lab environments, allowing you to tear everything down cleanly when finished.

---
## The Terriform Script
First thing that we need to do is create a file called ```main.tf``` this is where the terriform configutaion is stored and the file that we will be editing.

#### 1. Terraform and Provider Configuration
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

**Authentication:** Terraform uses environment variables (`ARM_CLIENT_ID`, `ARM_CLIENT_SECRET`, `ARM_SUBSCRIPTION_ID`, `ARM_TENANT_ID`) to authenticate with Azure. These should be set before running Terraform commands. I store this varibles in a file called "set-azure-creds.sh"

#### 2. Variables - Making Configuration Flexible
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

variable "admin_password" {
  description = "ADMIN PASSWORD"
  type        = string
  sensitive   = true
}
```

**What this does:**
- Defines input variables with default values
- Makes the configuration reusable - change the defaults or pass different values at runtime
- `default` values mean you don't have to specify them when running `terraform apply`
- Defines a password that we will later use to login to the VM


#### 3. Resource Group - The Container
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

#### 4. Virtual Network and Subnet
```hcl
resource "azurerm_virtual_network" "main" {
  name                = "${var.vm_name}-vnet"
  address_space       = ["10.250.0.0/20"]
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
}

resource "azurerm_subnet" "outside" {
  name                 = "outside-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.250.1.0/24"]
}

resource "azurerm_subnet" "server" {
  name                 = "server-subnet-1"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.250.2.0/24"]
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

#### 5. Public IP Address
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

#### 6. Network Security Group - The Firewall Rules
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

#### 7. Network Interface - Connecting the VM to the Network
```hcl
resource "azurerm_network_interface" "outside" {
  name                = "${var.vm_name}-nic-outside"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  ip_forwarding_enabled = true  

  ip_configuration {
    name                          = "external"
    subnet_id                     = azurerm_subnet.outside.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.main.id
  }
}

resource "azurerm_network_interface" "server" {
  name                = "${var.vm_name}-nic-server"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  ip_forwarding_enabled = true 

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.server.id
    private_ip_address_allocation = "Dynamic"
  }
}

resource "azurerm_network_interface_security_group_association" "outside" {
  network_interface_id      = azurerm_network_interface.outside.id
  network_security_group_id = azurerm_network_security_group.main.id
}

resource "azurerm_network_interface_security_group_association" "server" {
  network_interface_id      = azurerm_network_interface.server.id
  network_security_group_id = azurerm_network_security_group.main.id
}
```

**What this does:**
- Creates a virtual NIC for the VM
- Attaches it to the subnet
- Associates the public IP address
- Applies the security group rules

**Key point:** The NIC is the "glue" that connects the VM to the network infrastructure.

#### 8. The Virtual Machine
```hcl
resource "azurerm_linux_virtual_machine" "main" {
  name                = var.vm_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  size                = "Standard_B2s"
  admin_username      = var.admin_username
  admin_password      = var.admin_password                   
  disable_password_authentication = false    

  network_interface_ids = [
    azurerm_network_interface.outside.id,
    azurerm_network_interface.server.id,
  ]

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
}
```

**What this does:**
- **VM size**: Standard_B2s (2 vCPU, 4GB RAM) - burstable, cost-effective
- **OS image**: Ubuntu 22.04 LTS from Canonical
- **authentication**: Choose a the admin/password login

## Deploying the Infrastructure

Now that we have our complete `main.tf` file, let's deploy it!

### Step 1: Initialize Terraform
```bash
terraform init
```
This downloads the Azure provider and prepares your working directory.

### Step 2: Validate the Configuration
```bash
terraform validate
```
This checks for syntax errors in your configuration files.

### Step 3: Preview the Changes
```bash
terraform plan
```
Review what Terraform will create. You should see output showing 7 resources to be added:
- 1 Resource Group
- 1 Virtual Network
- 1 Subnet
- 1 Public IP
- 1 Network Security Group
- 1 Network Interface (and its NSG association)
- 1 Virtual Machine

### Step 4: Apply the Configuration
```bash
terraform apply
```

Terraform will prompt you to enter the admin password (since we marked it as sensitive and didn't provide a default). Type a secure password and press Enter.

Type `yes` when prompted to confirm the deployment.

The deployment will take approximately 3-5 minutes. You'll see output showing the progress of each resource being created.







 
