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


