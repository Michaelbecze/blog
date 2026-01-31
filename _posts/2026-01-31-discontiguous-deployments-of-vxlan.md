## Discontiguous Deployments of vxlan over an IGP 

Traditionally vxlan has been used in Data Center enviroments where the whole ecosystem is an overlay. For this post I would like to think about evpn vxlan in terms of how it could be used in an enterpirise enviroment where we are jnot going to be dealing with a Spine Leaf fabric. In the Enterprise topologies can take a wide range of different forms where we dont always have control of the whole topologies or we maybe be averse to making change to out core network. In this blog post I am going to go over how we can stretch L2 evpn vxlan over a routed network using an simple IGP without doing any configuration on the core of the network. The configuration will be puched to the edge devices in this way we can configur a L2 strech with no cheange to our routed network. 



