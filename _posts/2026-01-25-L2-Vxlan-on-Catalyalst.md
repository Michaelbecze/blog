VXLAN is becoming more prevaltent in the Campus network as an Overlay SDN option. I am going to take some time to go over how to set up VXLAN EVPN on Catalyst Switches. While there are other options for the control plane like Multicast, LISP, or even statically configured I am going to use MP-BGP EVPN as it is the most popluar choose. In this example i am just going to use 2 switches with a routed link to show a very basic L2 VXLAN strech. First I will go over quicklly all the components that are needed to make this connection work. 

1). Make sure that we are using jumbo frames, because VXLAN added an extra 50byte header we need the extra overhead
2). Routed underlay, this allows for the loopbacks that we are going to create for EVPN to have reacablity. In this example I am going to use EIGRP for the routed underlay.
3). MP-BGP EVPN, we will bring up EVPN using our loopbacks.
4). Create Vlans and assign them a VNI (VXLAN Network Identifier), this is needed to map a vlan into the vxlan fabric
5). Create the NVE (Network Virtualization edge), this is the where the vxlan tunnel will terminate and is commonly refered to as the VTEP(VXLAN tunnel end point)


