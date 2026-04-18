## External Connections into a VXLAN fabric using a L2 link

There are alot of different ways to bring in external connections into a VXLAN fabric. Normally, external connections are made on a "boarder leaf" which is just another leaf excpet it does not noramlly have end hosts attached to it. The board leaf has a VTEP and particiates in the VXLAN fabric just like any other leaf would do. For this lab we are going to bring a an external conneccion in the form of a firewall using a L2 link between our boarder leaf and the firewall. I will show how we can have a protected network that uses a Centralized Gateway Model so that all traffic from "protected" subnets must traverse the firewall along side an interanl network that uses a Distributed Anycast Gateway for for internal traffic but must use the firewall to reach an external network. 

## Lab Topology

For this lab I have built a classic spine-leaf topology. Two spines act as BGP route reflectors with no VXLAN awareness of their own — their only job is OSPF underlay reachability and reflecting EVPN routes between leaves. Three leaf switches hang below them, each running a VTEP and hosting the Distributed Anycast Gateway for their locally attached subnets.
The hosts are split into two groups. Host-1 and Host-2 sit in internal data subnets (10.0.20.0/24 and 10.0.21.0/24) and use the DAG on their local leaf as their default gateway — traffic between them stays entirely within the fabric and is routed symmetrically via the L3 VNI. The secured hosts are in a different category: secured-host-1 and secured-host-2 sit in the 192.168.10.0/24 and 192.168.11.0/24 subnets and are not permitted to route freely inside the fabric. Their traffic must pass through the firewall before reaching anything outside their own subnet.

The real action is on the Border Gateway (bgw). This node is where the VXLAN fabric meets the outside world, and it does two distinct things at once. For the routed internal networks it terminates the L3 VNI, holds the VRF core routing table, and runs an eBGP session to the firewall over a dedicated handoff segment (VLAN 900, 10.90.0.0/30) — routes learned from the firewall are redistributed into VRF core and propagated to every leaf as EVPN Type-5 prefixes. For the secured L2 networks it extends the VXLAN-backed VLANs (10 and 11) across a dot1q trunk to the firewall, so those hosts appear as local Layer 2 adjacencies on the firewall's interfaces rather than routed destinations. 

![VXLAN-EX-l2]({{ site.baseurl }}/assets/external-connection-l2.png)

| Device | Loopback1 | Loopback100 | VLANs / VNIs |
|---|---|---|---|
| **sw-1** | 10.1.255.3 | 10.100.255.3 | VLAN 10 → VNI 10010, VLAN 20 → VNI 10020, VLAN 100 → VNI 10100 (L3) |
| **sw-2** | 10.1.255.4 | 10.100.255.4 | VLAN 11 → VNI 10011, VLAN 21 → VNI 10021, VLAN 100 → VNI 10100 (L3) |
| **bgw** | 10.1.255.5 | 10.100.255.5 | All of the above + VLAN 900 → VNI 10900 (core handoff) |
| **Spine-1** | 10.1.255.1 | 10.100.255.1 | Route reflector only |
| **Spine-2** | 10.1.255.2 | 10.100.255.2 | Route reflector only |
|**fw** | n/a | n/a | g0/0.900 (core handoff) g0/0.10 and g0/0.11 (secured gateway)|

| Host | IP | VLAN | Attached to |
|---|---|---|---|
| secured-host-1 | 192.168.10.5/24 | 10 | sw-1 |
| secured-host-2 | 192.168.11.5/24 | 11 | sw-2 |
| Host-1 | 10.0.20.5/24 | 20 | sw-1 |
| Host-2 | 10.0.21.5/24 | 21 | sw-2 |

---

