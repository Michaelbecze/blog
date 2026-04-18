## External Connections into a VXLAN fabric using a L2 link

There are alot of different ways to bring in external connections into a VXLAN fabric. Normally, external connections are made on a "boarder leaf" which is just another leaf excpet it does not noramlly have end hosts attached to it. The board leaf has a VTEP and particiates in the VXLAN fabric just like any other leaf would do. For this lab we are going to bring a an external conneccion in the form of a firewall using a L2 link between our boarder leaf and the firewall. I will show how we can have a protected network that uses a Centralized Gateway Model so that all traffic from "protected" subnets must traverse the firewall along side an interanl network that uses a Distributed Anycast Gateway for for internal traffic but must use the firewall to reach an external network. 

## Lab Topology

For this lab i have created a classic spine leaf topology with two spines that act as BGP route reflectors with no VXLAN awareness of their own. Three leaf switches hang below them that have the VTEPS and Anycast gateways. There 2 hosts in different subnets that are protected and use the firewall as a gateway and 2 hosts that are in interanl subnets and use the Distributed gateway. The real action is on the BGW (boarder gateway) where we make a connection between the Vxlan fabric and the Firewall using BGP for the routed networks and vlans for the protected l2 networks. 

![VXLAN-EX-l2]({{ site.baseurl }}/assets/external-connection-l2.png)

The fabric is a classic spine-leaf design: two spines (`Spine-1` at `10.1.255.1`, `Spine-2` at `10.1.255.2`) act as BGP route reflectors with no VXLAN awareness of their own. Three leaf switches hang below them.

| Device | Loopback1 | Loopback100 | VLANs / VNIs |
|---|---|---|---|
| **sw-1** | 10.1.255.3 | 10.100.255.3 | VLAN 10 → VNI 10010, VLAN 20 → VNI 10020, VLAN 100 → VNI 10100 (L3) |
| **sw-2** | 10.1.255.4 | 10.100.255.4 | VLAN 11 → VNI 10011, VLAN 21 → VNI 10021, VLAN 100 → VNI 10100 (L3) |
| **bgw** | 10.1.255.5 | 10.100.255.5 | All of the above + VLAN 900 → VNI 10900 (core handoff) |
| **Spine-1** | 10.1.255.1 | 10.100.255.1 | Route reflector only |
| **Spine-2** | 10.1.255.2 | 10.100.255.2 | Route reflector only |

| Host | IP | VLAN | Attached to |
|---|---|---|---|
| secured-host-1 | 192.168.10.5/24 | 10 | sw-1 |
| secured-host-2 | 192.168.11.5/24 | 11 | sw-2 |
| Host-1 | 10.0.20.5/24 | 20 | sw-1 |
| Host-2 | 10.0.21.5/24 | 21 | sw-2 |

---

## OSPF Underlay

OSPF Area 0 carries loopback reachability between all nodes. Each leaf has *two* loopbacks: `Loopback1` is the BGP router-ID and VTEP source, and `Loopback100` is used as the unnumbered address on the physical uplinks so OSPF can form adjacencies without consuming a subnet per link.

```
interface Loopback1
 ip address 10.1.255.3 255.255.255.255
 ip ospf 1 area 0
!
interface Loopback100
 ip address 10.100.255.3 255.255.255.255
 ip ospf 1 area 0
!
interface Ethernet0/0
 no switchport
 ip unnumbered Loopback100
 ip ospf network point-to-point
 ip ospf 1 area 0
```

The spines peer with all three leaves and are configured as BGP route reflectors — they activate only the `l2vpn evpn` address family and reflect EVPN routes with extended communities intact.

---

## VRF and Route Targets

All tenant-facing VLANs live inside VRF `core`. Every leaf uses the same route-target pair (`65001:1` export and import, plus stitching copies) so any leaf's prefixes are automatically imported by every other leaf — a flat, single-tenant design suitable for a small fabric.

```
vrf definition core
 rd 65001:3
 !
 address-family ipv4
  route-target export 65001:1
  route-target import 65001:1
  route-target export 65001:1 stitching
  route-target import 65001:1 stitching
 exit-address-family
```

> **Note:** The RD is unique per node (`65001:3` on sw-1, `65001:4` on sw-2, `65001:5` on bgw) so BGP can distinguish the same prefix advertised by different VTEPs. The route-target is identical on all nodes so every VTEP imports every other's routes.

---

## MP-BGP EVPN

Leaves peer with both spines (the route reflectors). The spines peer with all three leaves and carry `route-reflector-client` for each. No direct leaf-to-leaf sessions are needed.

```
router bgp 65001
 neighbor 10.1.255.1 remote-as 65001
 neighbor 10.1.255.1 update-source Loopback1
 neighbor 10.1.255.2 remote-as 65001
 neighbor 10.1.255.2 update-source Loopback1
 !
 address-family l2vpn evpn
  neighbor 10.1.255.1 activate
  neighbor 10.1.255.1 send-community extended
  neighbor 10.1.255.2 activate
  neighbor 10.1.255.2 send-community extended
 exit-address-family
 !
 address-family ipv4 vrf core
  advertise l2vpn evpn
  redistribute connected
 exit-address-family
```

The `advertise l2vpn evpn` command under the VRF address family is what triggers Type-5 (IP prefix) route generation. Without it, connected subnets are not exported into the EVPN control plane.

---

## L2VPN EVPN Instance and VLAN-to-VNI Mapping

Each user-facing VLAN is associated with an EVPN instance and gets a VNI. VLAN 100 is the L3 transit VNI — it is mapped directly to a VNI without an EVPN instance, exactly as in the symmetric IRB design.

```
l2vpn evpn
 replication-type ingress
 router-id Loopback1
 default-gateway advertise
!
l2vpn evpn instance 1 vlan-based
 encapsulation vxlan
!
vlan configuration 20
 member evpn-instance 1 vni 10020
!
vlan configuration 100
 member vni 10100
```

---

## NVE Interface

The NVE interface is the VXLAN tunnel endpoint. Each user-facing VNI uses ingress replication (no multicast). The L3 transit VNI is bound to VRF `core` for symmetric IRB routing.

```
interface nve1
 no ip address
 source-interface Loopback1
 host-reachability protocol bgp
 member vni 10010 ingress-replication
 member vni 10011 ingress-replication
 member vni 10020 ingress-replication
 member vni 10021 ingress-replication
 member vni 10100 vrf core
```

On `bgw`, there is one additional member:

```
 member vni 10900 ingress-replication
```

VNI 10900 maps to VLAN 900, the SVI used as the handoff point between the fabric VRF and the external-facing BGP session toward the firewall.

---

## Distributed Anycast Gateway (DAG) — Leaf SVIs

Both `sw-1` and `sw-2` configure identical IP addresses and a shared static MAC on their tenant SVIs. Hosts on either leaf use the same default gateway and see the same MAC regardless of where they are attached.

```
interface Vlan20
 mac-address 0000.1111.2020
 vrf forwarding core
 ip address 10.0.20.1 255.255.255.0
 no autostate
!
interface Vlan21
 mac-address 0000.1111.2021
 vrf forwarding core
 ip address 10.0.21.1 255.255.255.0
```

The static MAC ensures ARP replies from different VTEPs are consistent. Without it, a host that moves between leaves would see a gateway MAC change and send traffic to the wrong VTEP until ARP ages out.

```
interface Vlan100
 description l3-transit
 vrf forwarding core
 ip unnumbered Loopback1
 no autostate
```

VLAN 100 is the L3 transit SVI. `ip unnumbered Loopback1` avoids allocating a separate subnet; `no autostate` keeps it up even if no access ports are active in VLAN 100.

---

## Centralized Gateway (CGW) — Border Gateway Config

The `bgw` node is the most interesting piece. It participates in the fabric as a normal leaf — it has NVE, EVPN instances, and the same VRF `core` — but it also has a trunk uplink (`Ethernet0/2`) to the firewall.

### Fabric-side SVIs on bgw

The bgw hosts the same DAG SVIs as the other leaves for the data VLANs (20, 21) with the same anycast MAC. It additionally has a VLAN 900 SVI that acts as the internal handoff segment to the firewall:

```
interface Vlan900
 vrf forwarding core
 ip address 10.90.0.1 255.255.255.252
 no autostate
```

### External BGP Session via VLAN 900

The firewall sits on `10.90.0.2` in a different AS (`65002`). BGP is configured under VRF `core` to peer with it and advertise the `10.90.0.0/30` handoff subnet:

```
address-family ipv4 vrf core
 advertise l2vpn evpn
 network 10.90.0.0 mask 255.255.255.252
 neighbor 10.90.0.2 remote-as 65002
 neighbor 10.90.0.2 activate
exit-address-family
```

> This eBGP session runs *inside* VRF `core`, so the firewall is reachable via the VLAN 900 SVI without polluting the global routing table. Routes learned from the firewall (including a default route) are redistributed into VRF `core` and become available to all fabric leaves via EVPN Type-5.

### The Firewall Trunk

The bgw uplink to the firewall is a dot1q trunk on `Ethernet0/2`. This allows the firewall to receive traffic from multiple VLANs if needed — for example, the secured VRF traffic could be sent on a different sub-interface to enforce a separate security policy per zone.

```
interface Ethernet0/2
 switchport trunk encapsulation dot1q
 switchport mode trunk
```

---

## Traffic Flow Walkthrough

With all pieces in place, here is what happens when `secured-host-1` (`192.168.10.5`, on sw-1 VLAN 10) sends a packet to the `External-port` device beyond the firewall:

1. `secured-host-1` ARPs for its default gateway `192.168.10.1`. sw-1 responds with the anycast MAC.
2. The host sends the frame to sw-1. sw-1 recognises the destination is outside its local subnet and routes within VRF `core`.
3. sw-1 has no direct route to the external destination but has a default route (or specific prefix) learned from bgw via EVPN Type-5. The next-hop resolves to bgw's VTEP IP.
4. sw-1 encapsulates the packet in VXLAN using the **L3 VNI (10100)** and sends it to bgw's loopback via the underlay.
5. bgw decapsulates, strips the VXLAN header, and looks up the destination in VRF `core`. The route points to the firewall at `10.90.0.2` via the VLAN 900 SVI.
6. bgw sends the packet out the trunk on VLAN 900 to the firewall, which applies policy and forwards it to `External-port`.

Return traffic follows the reverse path: firewall → bgw (VLAN 900) → VXLAN L3 VNI → sw-1 → secured-host-1.

---

## Verification

### Check NVE Peers and VNI State

```
bgw# show nve peers

Interface  VNI      Type Peer-IP          RMAC/Num_RTs   eVNI     state flags UP time
nve1       10100    L3CP 10.1.255.3       5254.xxxx.xxxx 10100      UP  A/M/4 ...
nve1       10100    L3CP 10.1.255.4       5254.yyyy.yyyy 10100      UP  A/M/4 ...
nve1       10020    L2CP 10.1.255.3       N              10020      UP   N/A  ...
nve1       10021    L2CP 10.1.255.4       N              10021      UP   N/A  ...
```

You should see both L3CP (L3 control-plane, one per remote VTEP) and L2CP (L2 control-plane, one per L2 VNI) entries. The RMAC on the L3CP entry is the router MAC of the remote VTEP used in EVPN Type-2 MAC/IP advertisements.

### Check EVPN Default-Gateway Advertisements

```
bgw# show l2vpn evpn default-gateway

Valid Default Gateway Address        EVI   VLAN  MAC Address    Source
  Y   10.0.20.1                       1     20    0000.1111.2020 Vl20
  Y   10.0.20.1                       1     20    0000.1111.2020 10.1.255.3
  Y   10.0.21.1                       2     21    0000.1111.2021 Vl21
  Y   10.0.21.1                       2     21    0000.1111.2021 10.1.255.4
```

Each anycast gateway IP appears twice: once sourced from the local SVI (confirming local configuration) and once learned from the remote VTEP (confirming the Type-2 advertisement is being received).

### Inspect VRF core Routing Table on bgw

```
bgw# show ip route vrf core

B        10.0.20.0/24 [200/0] via 10.1.255.3, Vlan100
B        10.0.21.0/24 [200/0] via 10.1.255.4, Vlan100
C        10.90.0.0/30 is directly connected, Vlan900
B        192.168.10.0/24 [200/0] via 10.1.255.3, Vlan100
B        192.168.11.0/24 [200/0] via 10.1.255.4, Vlan100
```

The BGP routes sourced from leaves confirm that EVPN Type-5 advertisements are being received and installed. The directly connected `10.90.0.0/30` is the handoff to the firewall.

### Confirm the External BGP Session

```
bgw# show bgp vpnv4 unicast vrf core summary

Neighbor        V    AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd
10.90.0.2       4 65002     ...     ...       ...    0    0 ...      <number>
```

A non-zero prefix count confirms routes are being received from the firewall (typically a default route or external prefix block). Those prefixes get redistributed into VRF `core` and re-advertised to all leaves as EVPN Type-5, completing the path from any host to the outside world.

---
