## Integrated Routing and Bridging (IRB)
Integrated Routing and Bridging (IRB) refers to the capability of a VTEP (VXLAN Tunnel Endpoint) to perform both Layer 2 switching and Layer 3 routing within a VXLAN fabric. In a traditional network these functions are separated, but in a modern EVPN VXLAN deployment a single VTEP can bridge traffic within the same subnet while simultaneously routing traffic between different subnets. The key question IRB answers is: when a packet needs to be routed, which VTEP does the routing — the ingress or the egress? The answer depends on which IRB model you deploy.

---
## Asymmetric IRB vs Symmetric IRB
### Asymmetric IRB
In Asymmetric IRB, the ingress VTEP performs both routing and bridging, while the egress VTEP performs only bridging. The traffic flow looks like this:

  1. A frame arrives at the ingress VTEP and is bridged into the correct Layer 2 VNI
  2. The ingress VTEP routes the packet to the destination subnet's SVI
  3. The packet is then switched across the VXLAN fabric to the egress VTEP using the destination VNI
  4. The egress VTEP bridges the packet to the local endpoint

Because routing happens at ingress, return traffic takes a completely different VNI path — it will be routed at the far end and switched back using the source VNI. This asymmetry is where the name comes from.
The critical implication here is that every VNI for every subnet must exist on every VTEP that needs to participate in inter-subnet routing. If VTEP-A needs to route between VLAN 10 and VLAN 20, both VNIs must be locally configured on every VTEP in the fabric. This works fine at small scale but becomes a scalability problem as the number of VNIs grows.

### Symmetric IRB
In Symmetric IRB, both the ingress and egress VTEPs perform both routing and bridging. A special Layer 3 transit VNI (L3VNI) is introduced to carry routed traffic between VTEPs. The traffic flow looks like this:

  1. The ingress VTEP bridges the packet into the source Layer 2 VNI, then routes it into the L3VNI
  2. The packet traverses the VXLAN fabric encapsulated in the L3VNI
  3. The egress VTEP routes the packet from the L3VNI into the destination Layer 2 VNI
  4. The packet is bridged to the local endpoint

Because both sides perform routing, return traffic uses the same L3VNI path, making the forwarding behavior symmetric. 

---
## Gateway Modles
There a 2 modles that are used when it comes to where the L3 Gateway should be for each subenet in the EVPN VXLAN Fabric:

**Distributed Anycast Gateway** — every VTEP acts as the default gateway for its locally connected hosts, all sharing the same gateway IP and MAC address across the fabric. This enables optimal local routing, supports seamless VM mobility, and is the recommended model for most deployments.

**Centralized Default Gateway** — a single designated VTEP handles all inter-subnet routing for the fabric. All other VTEPs perform Layer 2 bridging only and forward traffic to the centralized gateway for routing. This model is useful when inter-subnet traffic needs to pass through a firewall or centralized policy enforcement point, but it introduces a potential bottleneck and single point of failure.

---


