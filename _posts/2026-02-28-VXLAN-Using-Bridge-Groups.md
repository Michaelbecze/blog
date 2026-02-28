<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
<script>mermaid.initialize({ startOnLoad: true });</script>
## Bridge Domains on Routers vs VLANs on Switches (When Doing VXLAN)
=================================================================

When we think about extending Layer-2 networks over VXLAN, the first mental model is usually:

> VLAN on a switch → mapped to VNI → carried across VXLAN.

But what happens when your VXLAN VTEP is not a switch --- but a router? I was reading a blog post on [ipspace.net](https://blog.ipspace.net/2026/02/evpn-cisco-ios/) by Ivan Pepelnjak that got me thinking about how this configuration would look.

In this lab, I built VXLAN EVPN over an IPsec-protected WAN between two **Cisco Catalyst 8000V** routers. Instead of VLANs being the primary Layer-2 construct, we use **bridge-domains**. Let's break down how they compare --- and why they are conceptually the same thing.


## Vlans and Bridge Domains
--- 
On a typical **switch** a vlan is mapped to a VNI that is advertised into EVPN and ultimately Encapsulated by VXLAN, the signal flow looks like this:

<div class="mermaid">
graph TD
    A[VLAN 10] --> B[Mapped to VNI 10010]
    B --> C[Advertised via EVPN]
    C --> D[Encapsulated in VXLAN]
</div>

**Routers** don't operate around VLANs the same way switches do. Instead, they use Bridge Domains. These allow us to turn a routed port into something that looks alot like a switch port. For a router using a Brdige Domain the signal flow looks like this:
<div class="mermaid">
graph TD
    A[Service Instance 10] --> B[Bridge Domain 10]
    B --> C[Mapped to VNI 10010]
    C --> D[Advertised via EVPN]
    D --> E[Encapsulated in VXLAN]
</div>

Routers are fundamentally Layer-3 devices. When you enable L2 functionality on a router, you're activating features typically associated with:

L2VPN / Ethernet Virtual Circuit (EVC)
Instead of VLANs being native objects like on a switch, routers use:
-   Service Instances
-   Encapsulation dot1q
-   Bridge Domains
This gives routers much more flexibility:
-   Per-service QoS
-   Per-service policy
-   L2VPN support (xconnect, EVPN, pseudowire, etc.)
-   WAN transport integration (IPsec, GRE, MPLS, etc.)

#### Routers vs Switches

| IOS/XE Routers  | IOS/XE Switches |
|---|---|
| BDI is the L3 gateway | SVI (interface VlanX) is the L3 gateway |
| Uses `bridge-domain` configuration | Uses `vlan` configuration |
| Uses `service instance` for access VLAN | Uses `switchport access vlan` for access VLAN |
| Service instance is added to a `bridge-domain` | VLAN is built from switchport VLAN assignments |
|
---
## Lab Topology

![Basic Lab set up]({{ site.baseurl }}/assets/VXLAN over Bridge GRoups.png)




