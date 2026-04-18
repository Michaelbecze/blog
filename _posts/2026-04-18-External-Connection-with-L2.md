## External Connections into a VXLAN fabric using a L2 link

There are alot of different ways to bring in external connections into a VXLAN fabric. Normally, external connections are made on a "boarder leaf" which is just another leaf excpet it does not noramlly have end hosts attached to it. The board leaf has a VTEP and particiates in the VXLAN fabric just like any other leaf would do. For this lab we are going to bring a an external conneccion in the form of a firewall using a L2 link between our boarder leaf and the firewall. I will show how we can have a protected network that uses a Centralized Gateway Model so that all traffic from "protected" subnets must traverse the firewall along side an interanl network that uses a Distributed Anycast Gateway for for internal traffic but must use the firewall to reach an external network. 

## Lab Topology

For this lab i have created a classic spine leaf topology with 2 host in different subnets that are protected and use the firewall as a gateway and to hosts that are interanl and use the Distributed gateway. 

![VXLAN-EX-l2]({{ site.baseurl }}/assets/external-connection-l2.png)
