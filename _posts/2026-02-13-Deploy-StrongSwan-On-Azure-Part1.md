## Deploy StrongSwan in Azure for Ipsec Vpn tunnels to On Prem
StrongSwan is a great open source VPN tool that is installed directly on Linux. Here we will take a look at installing it in Azure as a way to connect Azure to an On Prem enviroment using a cisco ios xe router. 

## The Lab Topology

![Basic Lab set up]({{ site.baseurl }}/assets/Azure-StrongSwan-Topo.drawio.png)

-**Azure Virtual Network:** 10.250.0.0/20 address space with a 10.250.1.0/24 subnet
-**StrongSwan VPN Server:** Ubuntu 22.04 VM in Azure with a Public IP address from Azure
-**PF Sense Firewall:** Public IP address
-**Cisco Router:** Acts as IPsec initiator with private IP 192.168.0.29 sitting behind the Firewall
-**On-Premises Network:** 192.168.200.0/24

## Setting up StrongSwan in Azure
