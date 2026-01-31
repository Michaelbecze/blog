## Discontiguous Deployments of vxlan over an IGP

Traditionally, VXLAN has been associated with data center environments, where the entire network is built as an overlay—most commonly using a spine-and-leaf topology with BGP running in a full mesh. While this model works extremely well in the data center, it does not always translate cleanly into enterprise campus or WAN environments.

Enterprise networks often have far more variability in their topology. They may span multiple physical locations, include legacy routing designs, or rely on a core network that teams are hesitant—or outright unable—to modify. In many cases, the core is treated as a stable transport network, and introducing large-scale changes such as BGP everywhere or a full spine-leaf redesign is simply not realistic.

In this post, I want to explore how EVPN VXLAN can be deployed in a discontiguous enterprise environment, where VXLAN is implemented only at the network edge and stretched across an existing routed core using a simple IGP. The key idea is that we can extend Layer 2 segments between sites without making any configuration changes to the core network itself. All VXLAN and EVPN configuration lives on the edge devices, while the core continues to operate exactly as it does today.

This approach allows us to create a Layer 2 VXLAN stretch across a routed network, using the existing IGP purely for underlay reachability.

EVPN is used to advertise MAC adress to IP mapping, so we know behind what VTEP a MAC address is living, bceause it is not carrying routing information that will be inseted into the routing table we do not need to have a full mesh like we would do with iBGP. The Core Network does not need to understand the state of EVPN, as long as the loopbacks used for the VTEPS can reach each other EVPN will be able to work. AS EVPN is a address family of BGP this gets more complicated if you have to router over eBGP. For my example we wull stick with an IGP for our underlay. 

## Why This Works
At its core, EVPN is used to advertise MAC address and IP address mappings, allowing VTEPs to learn where endpoints reside within the VXLAN fabric. These advertisements tell us which MAC address lives behind which VTEP, enabling efficient forwarding across the overlay.

Importantly, EVPN does not inject traditional routing information into the global routing table. Because of this, the underlay network does not need to understand anything about EVPN itself. As long as the loopback interfaces used by the VTEPs can reach one another at Layer 3, VXLAN encapsulated traffic can be exchanged successfully.

This is a critical distinction from traditional iBGP designs. Since EVPN is not being used to exchange underlay routing information, we do not require a full iBGP mesh across the network. The core network remains completely unaware of the overlayit simply forwards IP packets between VTEP loopbacks.

---
## Lab Topology 
![Basic Lab set up]({{ site.baseurl }}/assets/vxlan-over-eigrp.png)
- **edge-1:** `10.0.0.245`
- **edge-2:** `10.0.0.246`
- **Host-A:** `192.168.1.100`
- **Host-B:** `192.168.1.101`
- **Core-East:** `10.0.0.248`
- **Core-West:** `10.0.0.249`
- **RR-1:** `10.0.0.13`

All routers and Switches have full IP reachablity over EIGRP, above I have posted the Loopbacks of each device. Although no configuration will be done on Core-East and Core-West we still need to route through these routers. I have also added a router reflector that we will biuld EVPN sessions to, although this route reflector is not nessiary it is good to include so we can start to think about how we can quiickly scale EVPN VXLAN without have a full mesh.  

---
## MP-BGP EVPN Configuration

In this lab both edge routers will form a single EVPN session with the route reflector and what I would like to point out about this configuration is that both the edge routers can have identical bgp configurations. This is one only the mainy great benifits that come with Router Reflectors. 

Edge-1
```
router bgp 65000
 bgp log-neighbor-changes
 neighbor 10.0.0.13 remote-as 65000
 neighbor 10.0.0.13 update-source Loopback0
 !
 address-family l2vpn evpn
  neighbor 10.0.0.13 activate
  neighbor 10.0.0.13 send-community both
 exit-address-family
```

Edge-2
```
router bgp 65000
 bgp log-neighbor-changes
 neighbor 10.0.0.13 remote-as 65000
 neighbor 10.0.0.13 update-source Loopback0
 !
 address-family l2vpn evpn
  neighbor 10.0.0.13 activate
  neighbor 10.0.0.13 send-community both
 exit-address-family
```
RR-1
```
router bgp 65000
 bgp log-neighbor-changes
 neighbor 10.0.0.245 remote-as 65000
 neighbor 10.0.0.245 route-reflector-client
 neighbor 10.0.0.246 remote-as 65000
 neighbor 10.0.0.246 route-reflector-client
 !
 address-family l2vpn evpn
  neighbor 10.0.0.245 activate
  neighbor 10.0.0.245 send-community extended
  neighbor 10.0.0.245 route-reflector-client
  neighbor 10.0.0.246 activate
  neighbor 10.0.0.246 send-community extended
  neighbor 10.0.0.246 route-reflector-client
```

Verify EVPN on the Router Refelector
```
RR-1#show bgp l2 evpn sum
BGP router identifier 10.0.0.13, local AS number 65000
BGP table version is 20, main routing table version 20
5 network entries using 1960 bytes of memory
5 path entries using 1160 bytes of memory
3/3 BGP path/bestpath attribute entries using 888 bytes of memory
1 BGP extended community entries using 40 bytes of memory
0 BGP route-map cache entries using 0 bytes of memory
0 BGP filter-list cache entries using 0 bytes of memory
BGP using 4048 total bytes of memory
BGP activity 14/8 prefixes, 14/8 paths, scan interval 60 secs
5 networks peaked at 23:15:58 Jan 31 2026 UTC (00:03:02.032 ago)

Neighbor        V           AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd
10.0.0.245      4        65000     113     120       20    0    0 01:34:01        2
10.0.0.246      4        65000     116     125       20    0    0 01:33:44        3
```
---

### VLANS and Vteps

This is going to be almost identical to my previous post but I will go over it one more time. At this point we need to create the vlans we want to extend and them map them to a VNI. After this we will need to create the VTEP and add our member VNI. 

Create vlan
```
vlan 10
  name VXLAN
```

Vlan to VNI maping:
```
vlan configuration 10
 member evpn-instance 10 vni 10000
```

Create the EVPN Instance:
```
l2vpn evpn instance 10 vlan-based
 encapsulation vxlan
 replication-type ingress
```

VTEP Creatation:
```
interface nve1
 no ip address
 source-interface Loopback0
 host-reachability protocol bgp
 member vni 10000 ingress-replication
```
### Verification

show nve peers
```
edge-1# show nve peers
'M' - MAC entry download flag  'A' - Adjacency download flag
'4' - IPv4 flag  '6' - IPv6 flag

Interface  VNI      Type Peer-IP          RMAC/Num_RTs   eVNI     state flags UP time
nve1       10000    L2CP 10.0.0.246       3              10000      UP   N/A  01:41:53
```
show vni mappings
```
edge-1#show nve vni
Interface  VNI        Multicast-group  VNI state  Mode  VLAN  cfg vrf                      
nve1       10000      N/A              Up         L2CP  10    CLI N/A                      
edge-1#show l2route evpn mac
  EVI       ETag  Prod    Mac Address                                          Next Hop(s) Seq Number
----- ---------- ----- -------------- ---------------------------------------------------- ----------
   10          0 L2VPN 5254.001c.3e19                                           Gi1/0/1:10          0
   10          0   BGP 5254.0081.339c                                   V:10000 10.0.0.246          0
```

show EVPN table to verify mac adddress are being learned
```
edge-1#show bgp l2vpn evpn
BGP table version is 29, local router ID is 10.0.0.245
Status codes: s suppressed, d damped, h history, * valid, > best, i - internal, 
              r RIB-failure, S Stale, m multipath, b backup-path, f RT-Filter, 
              x best-external, a additional-path, c RIB-compressed, 
              t secondary path, L long-lived-stale,
Origin codes: i - IGP, e - EGP, ? - incomplete
RPKI validation codes: V valid, I invalid, N Not found

     Network          Next Hop            Metric LocPrf Weight Path
Route Distinguisher: 10.0.0.245:10
 *>   [2][10.0.0.245:10][0][48][5254001C3E19][0][*]/20
                      0.0.0.0                            32768 ?
 *>i  [2][10.0.0.245:10][0][48][52540081339C][0][*]/20
                      10.0.0.246               0    100      0 ?
 *>i  [2][10.0.0.245:10][0][48][52540081339C][32][192.168.1.101]/24
                      10.0.0.246               0    100      0 ?
Route Distinguisher: 10.0.0.246:10
 *>i  [2][10.0.0.246:10][0][48][52540081339C][0][*]/20
                      10.0.0.246               0    100      0 ?
 *>i  [2][10.0.0.246:10][0][48][52540081339C][32][192.168.1.101]/24
                      10.0.0.246               0    100      0 ?
Route Distinguisher: 10.0.0.245:10
 *>   [3][10.0.0.245:10][0][32][10.0.0.245]/17
     Network          Next Hop            Metric LocPrf Weight Path
                      0.0.0.0                            32768 ?
 *>i  [3][10.0.0.245:10][0][32][10.0.0.246]/17
                      10.0.0.246               0    100      0 ?
Route Distinguisher: 10.0.0.246:10
 *>i  [3][10.0.0.246:10][0][32][10.0.0.246]/17
                      10.0.0.246               0    100      0 ?
```

