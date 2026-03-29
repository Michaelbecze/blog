## Symmetric IRB with an Anycast Gateway using VXLAN EVPN

In this post, we will walk through a practical example of Symmetric Integrated Routing and Bridging (IRB) using an Anycast Gateway. I have already made a previous post about IRB, [link here](https://michaelbecze.github.io/blog/2026/03/15/Intergrated-routing-and-bridgeing-in-L3VXLAN.html) so I am not going to go over the mechanism again. This design allows hosts to maintain a consistent default gateway regardless of where they are connected, while still enabling routed communication between subnets across the VXLAN fabric. For this Lab we will create a Transit VNI that allows for sysmmtric IRB, in additon I will include an L2 VNI to show how the 2 can be used side by side on the same VTEP. 

## Lab Topology

This is a very simple setup with 2 Switches and a couple of host attached. However IRB can get complicated very quickly so I thought this would be the best way to start off. 

![VXLAN-IRB-SYM]({{ site.baseurl }}/assets/VXLAN-Symmetric-IRB.png)
- **WEST-sw1:**
  - **Lo1:** `10.0.255.201`
  - **VLAN 200 `10.0.255.201`
- **EAST-sw1:**
  - **Lo1:** `10.0.255.200`
  - - **VLAN 200 `10.0.255.200`

- **Host-A:** `192.168.1.100`
- **Host-B:** `192.168.1.101`

