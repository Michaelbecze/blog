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

## OSPF Underlay

The underlay network is responsible for providing IP reachability between VTEPs. In this example, OSPF is used to advertise loopback interfaces between the two switches.

Each switch uses Loopback1 as:
* BGP router-id
* EVPN peering source
* L3 transit addressing reference for Vlan 200

```
interface Loopback1
 ip address 10.0.255.200 255.255.255.255

interface GigabitEthernet1/0/3
 no switchport
 ip address 10.0.255.1 255.255.255.252
 ip ospf network point-to-point

router ospf 1
 router-id 10.0.255.200
 network 10.0.255.0 0.0.0.255 area 0
```

## VRF Definition

VRFs are used to separate tenant routing information from the global routing table. They become especially important in a VXLAN fabric when segmentation or multi-tenancy is required. This is a large topic but let quickly go over the function of RDs, Route Tagets, and Stitching,

### RD
The Route Distinguisher ensures routes inside the VRF remain unique when advertised via MP-BGP.

### Route Targets
Route targets control import/export policy between VTEPs. For this example "East-sw1" is originating 103:2 and will only accept routes from 104:2 (West-sw1). This allows very granular control over which routing information is shared between tenants or between different parts of the fabric.

### Route Target Stiching
Stitching allows L3 routes to be properly exchanged between VRFs using EVPN Type-5 routes. This is essential for the L3 VXLAN tranisit to work. This this design vlan 100 and 101 will be advertised as type-5 routes. 

```
vrf definition north
 rd 103:65001
 !
 address-family ipv4
  route-target export 103:2
  route-target import 104:2
  route-target export 103:2 stitching
  route-target import 104:2 stitching
 exit-address-family
```

## MP-BGP EVPN 

Lets bring up mp-bgp evpn. We enable both global EVPN and VRF-specific route exchange.

```
router bgp 65001
 bgp log-neighbor-changes
 no bgp default ipv4-unicast
 neighbor 10.0.255.201 remote-as 65001
 neighbor 10.0.255.201 update-source Loopback1
 !
 address-family ipv4
 exit-address-family
 !
 address-family l2vpn evpn
  neighbor 10.0.255.201 activate
  neighbor 10.0.255.201 send-community both
 exit-address-family
 !
 address-family ipv4 vrf north
  advertise l2vpn evpn
  redistribute connected
 exit-address-family
```

## Enable L2vpn evpn

We introduce a new command here: `default-gateway advertise`. This ensures the Anycast gateway MAC and IP are advertised via EVPN Type-2 routes. Without this command, remote VTEPs would learn host MAC/IP bindings but would not learn the Anycast gateway information, preventing hosts from using the local VTEP as their default gateway.

```
l2vpn evpn
 router-id Loopback1
 default-gateway advertise
```

Next, we map VLANs to VNIs. It is important to understand the difference between the configuration of VLAN 100 and VLAN 200.

VLAN 100 is configured as a traditional Layer 2 segment and is associated with an EVPN instance. This tells the switch that MAC address learning and host reachability information for this VLAN should be advertised using EVPN. VLAN 200, however, is not associated with an EVPN instance. Instead, it is mapped directly to a VNI that acts as the Layer 3 transit VNI used for symmetric IRB routing.

Although VLAN 200 is still technically a VLAN, in this design it represents the L3 VNI that interconnects routing tables between VTEPs rather than a user-facing broadcast domain.

This distinction can feel unintuitive at first because both segments are configured under vlan configuration, yet they serve very different roles in the VXLAN fabric:

```
l2vpn evpn instance 1 vlan-based
 encapsulation vxlan

vlan configuration 100
 member evpn-instance 1 vni 10100

vlan configuration 200
 member vni 5000
```

## Configure NVE Interface

The NVE interface provides VXLAN encapsulation and uses BGP EVPN for control-plane learning. Thankfully there is nothing new here with the exceptio of out L3 VNI being added in the correct vrf "north." 

```
interface nve1
 no ip address
 source-interface Loopback0
 host-reachability protocol bgp
 member vni 10100 ingress-replication
 member vni 5000 vrf north
 member vni 10101 ingress-replication
```

## SVI's

### Anycast Gateway SVI


```
interface Vlan100
 vrf forwarding north
 ip address 192.168.100.1 255.255.255.0
```

### L3 Transit SVI

This is out tranit vlan that is mapped to vni 5000 and is Used internally for symmetric routing.

```
interface Vlan200
 description CORE-SVI L3
 vrf forwarding north
 ip unnumbered Loopback1
 no autostate
```
