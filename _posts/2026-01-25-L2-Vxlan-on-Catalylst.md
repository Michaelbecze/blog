VXLAN is becoming more prevaltent in the Campus network as an Overlay SDN option. I am going to take some time to go over how to set up VXLAN EVPN on Catalyst Switches. While there are other options for the control plane like Multicast, LISP, or even statically configured I am going to use MP-BGP EVPN as it is the most popluar choose. In this example i am just going to use 2 switches with a routed link to show a very basic L2 VXLAN strech. First I will go over quicklly all the components that are needed to make this connection work. 

![Basic Lab set up]({{ site.baseurl }}/assets/east-west-vxlan.png)

1). Make sure that we are using jumbo frames, because VXLAN added an extra 50byte header we need the extra overhead
2). Routed underlay, this allows for the loopbacks that we are going to create for EVPN to have reacablity. In this example I am going to use EIGRP for the routed underlay.
3). MP-BGP EVPN, we will bring up EVPN using our loopbacks.
4). Create Vlans and assign them a VNI (VXLAN Network Identifier), this is needed to map a vlan into the vxlan fabric
5). Create the NVE (Network Virtualization edge), this is the where the vxlan tunnel will terminate and is commonly refered to as the VTEP(VXLAN tunnel end point)

I have created 2 loopbacks on each switch WEST-CSW = 10.100.1.1, EAST-CSW = 10.100.1.2 and made sure that they are able to ping each over the routed connection between the 2 switches, here is the EIGRP settings that I am using to esablish this connection:

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

 Next lets bring up MP-BGP EVPN between the to switchs: 

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

Next I am going to create vlan 10 and attach it to VNI 10000, and tell it to do VXLAN encapluation with Ingress Replication for BUM traffic:
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
Lastly all we need to do is create the VTEP and do some testing to make sure that everything is working. Here we are going to tell the VTEP to use bgp evpn for host reacablability and then attach the member vni that we created:
```
interface nve1
 no ip address
 source-interface Loopback100
 host-reachability protocol bgp
 member vni 10000 ingress-replication
```
