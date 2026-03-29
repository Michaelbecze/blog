## Symmetric IRB with an Anycast Gateway using VXLAN EVPN

In this post, we will walk through a practical example of Symmetric Integrated Routing and Bridging (IRB) using an Anycast Gateway. I have already made a previous post about IRB, [link here](https://michaelbecze.github.io/blog/2026/03/15/Intergrated-routing-and-bridgeing-in-L3VXLAN.html) so I am not going to go over the mechanism again. This design allows hosts to maintain a consistent default gateway regardless of where they are connected, while still enabling routed communication between subnets across the VXLAN fabric. For this Lab we will create a Transit VNI that allows for sysmmtric IRB, in additon I will include an L2 VNI to show how the 2 can be used side by side on the same VTEP. 

## Lab Topology

This is a very simple topology consisting of two switches and several attached hosts. IRB can become complex quickly, so starting with a minimal design helps build a solid understanding of the control-plane behavior.
Two Catalyst switches form a VXLAN EVPN fabric. Each switch has a loopback interface used as the EVPN router-id, VTEP source interface, and addressing for VLAN 200. OSPF provides reachability between loopbacks in the underlay network.
VLAN 200 acts as the L3 transit segment enabling symmetric IRB. VLAN 100 is configured as an Anycast gateway on both switches, sharing the same IP address.

![VXLAN-IRB-SYM]({{ site.baseurl }}/assets/VXLAN-Symmetric-IRB.png)
- **WEST-sw1:**
  - **Lo1:** `10.0.255.201` 
  - **VLAN 200** `10.0.255.201` -- VNI 5000 (L3 Transit)
  - **VALN 100** `192.168.100.1` -- VNI 10100
- **EAST-sw1:**
  - **Lo1:** `10.0.255.200`
  - **VLAN 200** `10.0.255.200` -- VNI 5000 (L3 Transit)
  - **VALN 100** `192.168.100.1` -- VNI 10100
  - **VALN 101** `192.168.101.1` -- VNI 10101
- **East-Host1:** `192.168.100.5`-- Vlan 100
- **East-Host2:** `192.168.101.5` -- Vlan 101
- **West-Host1:** `192.168.100.6` -- Vlan 100
