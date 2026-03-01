<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
<script>mermaid.initialize({ startOnLoad: true });</script>
## EVPN VXLAN over a Bridge Domain 
=================================================================

When we think about extending Layer-2 networks over VXLAN, the first mental model is usually with a Switch to Switch in a Spine Leaf or maybe orver a DCI. But what happens when your VXLAN VTEP is not a switch --- but a router? I was reading a blog post on [ipspace.net](https://blog.ipspace.net/2026/02/evpn-cisco-ios/) by Ivan Pepelnjak that got me thinking about how this configuration would look. 

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

---
## Lab Topology
In this lab I am simulating an HQ site connecting to a cloud site over an IPsec tunnel using a VTI (Virtual Tunnel Interface). In addition to this, we are going to stretch a subnet over the VPN tunnel using EVPN VXLAN. The 4 routers in the middle are simply simulating the internet. The Edge routers are where all the fun happens — for this example I am using two Cat8000V routers.
The configuration is built up in layers:

1. First, the IPsec/IKEv2 VPN is established between the two edge routers, creating a secure tunnel across the simulated internet
2. EIGRP is then brought up over the tunnel to advertise the Loopback interfaces, which are used as the VTEP source addresses
3. With Loopback reachability established, iBGP (AS 65001) is brought up between the two edge routers to run the EVPN control plane, exchanging MAC and IP routes
4. VXLAN is configured on the NVE interface, mapping VNI 10010 to the EVPN instance — this is the data plane that stretches the Layer 2 segment across the tunnel
5. Finally, a Bridge Domain is created and tied to both the physical access interface (via a service instance with dot1q encapsulation) and the EVPN/VXLAN instance, completing the stretched Layer 2 domain

![Basic Lab set up]({{ site.baseurl }}/assets/VXLAN over Bridge GRoups.png)

#### HQ Side
- HQ-Host1: Ubuntu endpoint
- HQ-Host2: Ubuntu endpoint
- HQ-Core: VLAN 10 / VLAN 20 — L2 access switch, trunks to HQ-Edge
- HQ-Edge: 200.1.1.2 — Cat8000V VTEP, runs IPsec + EVPN + VXLAN VNI 10010

#### Internet
- ISP-1: internet transit
- ISP-2: internet transit
- ISP-3: internet transit
- ISP-4: internet transit

#### Cloud Side
- Cloud-Edge: 199.1.1.2 — Cat8000V VTEP, runs IPsec + EVPN + VXLAN VNI 10010, BDI10 gateway 192.168.1.1
- Cloud-Vnet: VLAN 10 — L2 access switch, trunks to Cloud-Edge
- Cloud-Host1: Ubuntu endpoint
- Cloud-Host2: Ubuntu endpoint



