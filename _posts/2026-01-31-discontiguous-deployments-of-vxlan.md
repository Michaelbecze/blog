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

---

