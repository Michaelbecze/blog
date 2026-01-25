## VXLAN EVPN on Catalyst Switches (Basic L2 Stretch)

VXLAN is becoming increasingly prevalent in campus networks as an overlay SDN option. In this post, I’ll walk through how to set up a basic VXLAN EVPN deployment on Cisco Catalyst switches using **MP-BGP EVPN** as the control plane.

While VXLAN supports multiple control-plane options — such as multicast-based flooding, LISP, or even static VXLAN — MP-BGP EVPN has become the most common and scalable choice, especially in enterprise and campus designs.

For this example, I’ll use **two Catalyst switches** connected by a routed link to demonstrate a **simple Layer 2 VXLAN stretch**. The goal here is not a full production design, but to clearly show the required building blocks and how they fit together.

---

## Lab Topology

![Basic Lab set up]({{ site.baseurl }}/assets/east-west-vxlan.png)
- **WEST-CSW:** `10.100.1.1`
- **EAST-CSW:** `10.100.1.2`
- **Host-A:** `192.168.1.100`
- **Host-B:** `192.168.1.101`

---

## Key Components Required

Before configuring VXLAN EVPN, there are several foundational components that must be in place:

1. **Jumbo Frames**  
   VXLAN adds approximately **50 bytes of encapsulation overhead**. To avoid fragmentation, the underlay network must support jumbo frames.

2. **Routed Underlay Network**  
   The underlay provides **IP reachability** between VTEPs. This allows the loopback interfaces used for EVPN peering and VXLAN encapsulation to communicate.  
   In this lab, I’m using **EIGRP** for simplicity.

3. **MP-BGP EVPN Control Plane**  
   MP-BGP EVPN is used to exchange **MAC address, VLAN/VNI, and host reachability information** between VTEPs.

4. **VLAN-to-VNI Mapping**  
   Each VLAN that needs to be extended over VXLAN must be mapped to a **VXLAN Network Identifier (VNI)**.

5. **NVE Interface (VTEP)**  
   The **Network Virtualization Edge (NVE)** interface is where VXLAN tunnels terminate. This interface effectively turns the switch into a **VTEP (VXLAN Tunnel Endpoint)**.

---

## Underlay Configuration (EIGRP)

Each switch has a loopback interface used for EVPN and VXLAN:

- **WEST-CSW:** `10.100.1.1`
- **EAST-CSW:** `10.100.1.2`

These loopbacks must be reachable across the routed underlay.

Below is the EIGRP configuration used to provide that reachability:

```
router eigrp Underlay
 !
 address-family ipv4 unicast autonomous-system 100
  !
  topology base
  exit-af-topology
  network 10.0.0.0
 exit-address-family
 ```
## MP-BGP EVPN Configuration
Next, we establish the EVPN control plane using iBGP between the loopbacks.

WEST-CSW
 ```
router bgp 65501
 bgp log-neighbor-changes
 neighbor 10.100.1.2 remote-as 65501
 neighbor 10.100.1.2 update-source Loopback100
 !
 address-family l2vpn evpn
  neighbor 10.100.1.2 activate
  neighbor 10.100.1.2 send-community extended
 exit-address-family
 ```

 EAST-CSW
 ```
 router bgp 65501
 bgp log-neighbor-changes
 neighbor 10.100.1.1 remote-as 65501
 neighbor 10.100.1.1 update-source Loopback100
 !
 address-family l2vpn evpn
  neighbor 10.100.1.1 activate
  neighbor 10.100.1.1 send-community extended
 exit-address-family
 ```
Verify the connection is up:
```
WEST-CSW#show bgp l2vpn evpn summary 
BGP router identifier 10.100.1.1, local AS number 65501
BGP table version is 1, main routing table version 1

Neighbor        V           AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd
10.100.1.2      4        65501      10      10        1    0    0 00:05:05        0
```

## VLAN to VNI Mapping
Next, we create VLAN 10 and map it to VNI 10000. We also specify ingress replication to handle BUM (Broadcast, Unknown unicast, Multicast) traffic.
```
vlan 10
 name VXLAN
!
l2vpn evpn instance 10 vlan-based
 encapsulation vxlan
 replication-type ingress
!
vlan configuration 10
 member evpn-instance 10 vni 10000
```
When using the IOL image in CML you also need to define the global l2vpn evpn behavior to get import and export to work:
```
l2vpn evpn 
  router-id loopback 100
  replication-type ingress 
```

## Creating the VTEP (NVE Interface)
Lastly all we need to do is create the VTEP and do some testing to make sure that everything is working. Here we are going to tell the VTEP to use bgp evpn for host reacablability and then attach the member vni that we created:
```
interface nve1
 no ip address
 source-interface Loopback100
 host-reachability protocol bgp
 member vni 10000 ingress-replication
```
## Verification
At this point, MAC addresses should begin to populate via EVPN. We can verify that both switches are learning MACs for hosts across the VXLAN fabric.
![Leaning Mac Address' of both host]({{ site.baseurl }}/assets/l2vpn-evpn-macs.png)

Extra Verification commands:
```
show nve peers
show nve vni
show l2route evpn mac
show bgp l2vpn evpn
```
Lastly, Ping between the 2 hosts:
```
Host-A:~$ ping 192.168.1.101
PING 192.168.1.101 (192.168.1.101): 56 data bytes
64 bytes from 192.168.1.101: seq=0 ttl=42 time=2.709 ms
64 bytes from 192.168.1.101: seq=1 ttl=42 time=2.743 ms
64 bytes from 192.168.1.101: seq=2 ttl=42 time=2.689 ms
64 bytes from 192.168.1.101: seq=3 ttl=42 time=2.401 ms
64 bytes from 192.168.1.101: seq=4 ttl=42 time=2.482 ms
```
