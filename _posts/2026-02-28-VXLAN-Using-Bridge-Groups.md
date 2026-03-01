<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
<script>mermaid.initialize({ startOnLoad: true });</script>
## EVPN VXLAN over a Bridge Domain 

When we think about extending Layer-2 networks over VXLAN, the first mental model is usually with a Switch to Switch in a Spine Leaf or maybe orver a DCI. But what happens when your VXLAN VTEP is not a switch but a router? I was reading a blog post on [ipspace.net](https://blog.ipspace.net/2026/02/evpn-cisco-ios/) by Ivan Pepelnjak that got me thinking about how this configuration would look over a WAN link. 

In this lab, I built VXLAN EVPN over an IPsec-protected WAN between two **Cisco Catalyst 8000V** routers. Instead of VLANs being the primary Layer-2 construct, we use bridge-domains. Let's break down how they compare --- and why they are conceptually the same thing.

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
**L2VPN / Ethernet Virtual Circuit (EVC)**
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
- HQ-Core: L2 access switch, trunks to HQ-Edge
- HQ-Edge: Cat8000V VTEP, runs IPsec + EVPN + VXLAN VNI 10010

#### Internet
- ISP-1: internet transit
- ISP-2: internet transit
- ISP-3: internet transit
- ISP-4: internet transit

#### Cloud Side
- Cloud-Edge: Cat8000V VTEP, runs IPsec + EVPN + VXLAN VNI 10010
- Cloud-Vnet: L2 access switch, trunks to Cloud-Edge
- Cloud-Host1: Ubuntu endpoint
- Cloud-Host2: Ubuntu endpoint

## Configuration
I am not going to go over how to make a VPN tunnel or EIGRP configuration. I will provide the lab as a `.yaml` at the end if you would like to look over that. VPN tunnels using VTI are a whole post in themselves. I am going to pick up with the EVPN configuration, quickly go over the VTEP, and then show how the service instance works with bridge domains.

### MP-EVPN
Bring up EVPN on both edge routers using their loopback addresses. This is pretty straightforward BGP configuration but I thought I would show it anyway.
- HQ-Edge loopback 1 = 10.200.1.1
- Cloud-Edge: loopback 1 = 10.200.1.2

HQ-Edge
```
router bgp 65001
 bgp log-neighbor-changes
 neighbor 10.200.1.2 remote-as 65001
 neighbor 10.200.1.2 update-source Loopback1
 !
 address-family l2vpn evpn
  neighbor 10.200.1.2 activate
  neighbor 10.200.1.2 send-community extended
 exit-address-family
```
Cloud-Edge
```
router bgp 65001
 bgp log-neighbor-changes
 neighbor 10.200.1.1 remote-as 65001
 neighbor 10.200.1.1 update-source Loopback1
 !
 address-family l2vpn evpn
  neighbor 10.200.1.1 activate
  neighbor 10.200.1.1 send-community extended
 exit-address-family
```

### EVPN and VTEP
Here we are going to create the VTEP, tell it to use EVPN, and add a VNI.

```
interface nve1
 no ip address
 source-interface Loopback1
 host-reachability protocol bgp
 member vni 10010 ingress-replication
```
Then we are going to create an EVPN instance and tell it to use VXLAN for encapsulation and ingress replication for our BUM traffic.
```
l2vpn evpn
 replication-type ingress
 router-id Loopback1
!
l2vpn evpn instance 10 vlan-based
 encapsulation vxlan
 replication-type ingress
```

### Bridge Doamin
This is the new part. We will create a bridge domain and map it to a service instance. This bridge domain will connect the service instance to EVPN, so that anything that hits the service instance will get mapped into EVPN. That service instance then gets applied to an interface with a dot1q tag.

```
bridge-domain 10 
 member GigabitEthernet2 service-instance 10
 member evpn-instance 10 vni 10010
```

Apply to an interface
```
interface GigabitEthernet2
 no ip address
 service instance 10 ethernet
  encapsulation dot1q 10
```

## Verify
First make sure that EVPN is up:
```
show bgp l2vpn evpn summary
show bgp l2vpn evpn
```

Now let's check our VTEPs to make sure that they are peers and that the VNI is up:
```
Cloud-Edge#show nve peers 
'M' - MAC entry download flag  'A' - Adjacency download flag
'4' - IPv4 flag  '6' - IPv6 flag

Interface  VNI      Type Peer-IP          RMAC/Num_RTs   eVNI     state flags UP time
nve1       10010    L2CP 10.200.1.1       4              10010      UP   N/A  1w0d
```
```
Cloud-Edge#show nve vni
Interface  VNI        Multicast-group  VNI state  Mode  BD    cfg vrf                      
nve1       10010      N/A              Up         L2CP  10    CLI N/A                  
```

Let's check our bridge domain to make sure that G2 VLAN 10 is mapping to EVPN as we expect:
```
Cloud-Edge#show bridge-domain 10 
Bridge-domain 10 (2 ports in all)
State: UP                    Mac learning: Enabled
Aging-Timer: 300 second(s)
Unknown Unicast Flooding Suppression: Disabled
Maximum address limit: 65536
    GigabitEthernet2 service instance 10
    vni 10010
   AED MAC address    Policy  Tag       Age  Pseudoport
   -----------------------------------------------------------------------------
   -   5254.0045.98BF forward dynamic_c 101  GigabitEthernet2.EFP10
   -   5254.0004.4192 forward static_r  0    nve1.VNI10010, EVPN
```
Let's make sure that we see MAC addresses being advertised by EVPN:
```
Cloud-Edge#show l2vpn evpn mac
MAC Address    EVI   BD    ESI                      Ether Tag  Next Hop(s)
-------------- ----- ----- ------------------------ ---------- ---------------
5254.0004.4192 10    10    0000.0000.0000.0000.0000 0          10.200.1.1
5254.0045.98bf 10    10    0000.0000.0000.0000.0000 0          Gi2:10
```
I want to show one final command that came in very handy for me as it seems to wrap everything up very nicely. I am just going to post the output, but note the VTEP IPs, VTEP peers, encapsulation type, bridge domain, and service instance to port mapping:
```
Cloud-Edge# show l2vpn evpn evi 10 detail 
EVPN instance:       10 (VLAN Based)
  RD:                65001:10 (cfg)
  Import-RTs:        65001:10 
  Export-RTs:        65001:10 
  Per-EVI Label:     none
  State:             Established
  Replication Type:  Ingress
  Encapsulation:     vxlan
  IP Local Learn:    Enabled (global)
  Adv. Def. Gateway: Disabled (global)
  Re-originate RT5:  Disabled
  AR Flood Suppress: Enabled (global)
  Bridge Domain:     10
    Ethernet-Tag:    0
    State:           Established
    Flood Suppress:  Attached
    Core If:         
    Access If:       
    NVE If:          nve1
    RMAC:            0000.0000.0000
    Core BD:         0
    L2 VNI:          10010
    L3 VNI:          0
    VTEP IP:         10.200.1.2
    Pseudoports:
      GigabitEthernet2 service instance 10
        Routes: 1 MAC, 2 MAC/IP
    Peers:
      10.200.1.1
        Routes: 1 MAC, 2 MAC/IP, 1 IMET, 0 EAD
```

At this point HQ-Host1 and Cloud-Host1 can now ping each other over a WAN connection using an IPsec VPN tunnel and VXLAN, as if they are on the same LAN. Here is a link to the `.yaml` file so that you can spin this up in CML yourself.

[Download the lab file](https://github.com/Michaelbecze/CML-Labs/blob/main/EVPN_VXLAN_over_VPN_using_Bridge_Groups.yaml)
