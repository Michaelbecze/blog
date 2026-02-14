## Deploy StrongSwan in Azure for Ipsec Vpn tunnels to On Prem
StrongSwan is a great open source VPN tool that is installed directly on Linux. Here we will take a look at installing it in Azure as a way to connect Azure to an On Prem enviroment using a Cisco ios-xe router. For this we are going to do a policy baised VPN rather then a routed VPN as it is aeasier to get going with StrongSwan. First let take a look at what IPsec is and how it is used.

IPsec is a group of network protocols that create a secure connection between two or more devices by authenticating and encrypting packets over Internet Protocol (IP) networks such as the Internet. To establish a Virtual Private Network (VPN) tunnel between devices, IPSec uses multiple protocols, including the following.

  -  **Encapsulating Security Protocol (ESP):** Encrypts the IP header and payload for each data packet by adding a new header and trailer.
  -  **Security Association (SA):** Negotiates encryption keys and algorithms between devices in a tunnel using protocols such as Internet Key Exchange (IKE), and the Internet Security Association and Key Management Protocol (ISAKMP)
  -  **Internet Key Exchange (IKE)** IKE negotiates a security association (SA), which is an agreement between two peers engaging in an IPsec exchange, I like to thnk of this as the control plan for IPsec


## The Lab Topology

![Basic Lab set up]({{ site.baseurl }}/assets/Azure-StrongSwan-Topo.drawio.png)

- **Azure Virtual Network:** 10.250.0.0/20 address space with a 10.250.1.0/24 subnet
- **StrongSwan VPN Server:** Ubuntu 22.04 VM in Azure with a Public IP address from Azure
- **PF Sense Firewall:** Public IP address
- **Cisco Router:** Acts as IPsec initiator with private IP 192.168.0.29 sitting behind the Firewall
- **On-Premises Network:** 192.168.200.0/24

## Setting up StrongSwan in Azure
