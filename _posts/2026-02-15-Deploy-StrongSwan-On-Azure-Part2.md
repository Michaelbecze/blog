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
# How This Script Works

Let’s walk through what this configuration is doing.

## 1. Terraform Block & Azure Provider

```hcl
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}
```

This tells Terraform:

- We are using the AzureRM provider  
- Use version 3.x  

```hcl
provider "azurerm" {
  features {}
}
```

This initializes the Azure provider so Terraform can authenticate and deploy resources into Azure.

---

## 2. Variables

You defined reusable variables for:

- Resource group name  
- Location (`eastus`)  
- VM name  
- Admin username  
- Admin password (marked as `sensitive`)  

Marking the password as sensitive prevents Terraform from displaying it in CLI output.

---

## 3. Resource Group

```hcl
resource "azurerm_resource_group" "main"
```

Creates the logical container for all Azure resources.

All other resources reference this group.

---

## 4. Virtual Network & Subnets

```hcl
resource "azurerm_virtual_network" "main"
```

Creates a VNet with:

```
10.250.0.0/20
```

Then two subnets:

- `10.250.1.0/24` → Outside subnet  
- `10.250.2.0/24` → Server subnet  

This mirrors the StrongSwan lab design:

```
[Internet]
     |
Outside NIC (10.250.1.0/24)
     |
StrongSwan VM
     |
Server NIC (10.250.2.0/24)
```

---

## 5. Public IP

```hcl
resource "azurerm_public_ip" "main"
```

- Static allocation  
- Standard SKU  

This becomes the public-facing IP used by the remote IPsec peer.

---

## 6. Network Security Group (NSG)

You created inbound rules for:

| Rule | Port | Purpose |
|------|------|----------|
| SSH | TCP 22 | Management |
| IPsec-IKE | UDP 500 | IKE Phase 1 |
| IPsec-NAT-T | UDP 4500 | NAT Traversal |

UDP 500 and 4500 are required for StrongSwan to negotiate IPsec tunnels behind NAT.

---

## 7. Network Interfaces

You created **two NICs**.

### Outside NIC

- Attached to outside subnet  
- Has public IP  
- IP forwarding enabled  

### Server NIC

- Attached to internal subnet  
- IP forwarding enabled  

```hcl
ip_forwarding_enabled = true
```

This setting is critical.

Without enabling IP forwarding at the Azure NIC level, the VM cannot pass traffic between subnets — even if Linux IP forwarding is enabled inside the OS.

---

## 8. NSG Associations

You explicitly associate the NSG with both NICs.

This ensures:

- SSH works  
- IPsec ports are open  
- Traffic is controlled at the interface level  

---

## 9. Linux Virtual Machine

```hcl
resource "azurerm_linux_virtual_machine" "main"
```

Key configuration details:

- VM size: `Standard_B2s`  
- Ubuntu 22.04 LTS (Jammy)  
- Password authentication enabled  
- Two NICs attached  

Important detail:

```hcl
network_interface_ids = [
  azurerm_network_interface.outside.id,
  azurerm_network_interface.server.id,
]
```

The first NIC listed becomes the primary interface. This affects default routing and outbound traffic behavior.

---

## 10. Cloud-Init

```hcl
custom_data = base64encode(templatefile("${path.module}/cloud-init.yaml", {
  public_ip = azurerm_public_ip.main.ip_address
}))
```

This passes a cloud-init configuration file to the VM during provisioning.

Cloud-init allows you to:

- Automatically install StrongSwan  
- Configure packages  
- Pre-stage configuration  
- Inject variables like the public IP  

This removes the need for manual post-deployment configuration.

---

# Deploying the Lab

Once the file is saved as `main.tf`:

```bash
terraform init
terraform plan
terraform apply
```

To destroy the lab:

```bash
terraform destroy
```

This is the real power of Terraform — the entire StrongSwan lab can be built and torn down in minutes.

---

# Why This Matters

By combining:

- Terraform for infrastructure  
- StrongSwan for VPN  
- Azure networking  
- NAT-T and IP forwarding  

You now have a fully reproducible hybrid connectivity lab that can be rebuilt anytime.




 
