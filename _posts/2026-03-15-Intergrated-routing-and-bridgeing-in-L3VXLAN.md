## Integrated Routing and Bridging (IRB)
Integrated Routing and Bridging (IRB) refers to the capability of a VTEP (VXLAN Tunnel Endpoint) to perform both Layer 2 switching and Layer 3 routing within a VXLAN fabric. In a traditional network these functions are separated, but in a modern EVPN VXLAN deployment a single VTEP can bridge traffic within the same subnet while simultaneously routing traffic between different subnets. The key question IRB answers is: when a packet needs to be routed, which VTEP does the routing — the ingress or the egress? The answer depends on which IRB model you deploy.

## Asymmetric IRB vs Symmetric IRB
