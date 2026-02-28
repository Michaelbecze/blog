
## Bridge Domains on Routers vs VLANs on Switches (When Doing VXLAN)
=================================================================

When we think about extending Layer-2 networks over VXLAN, the first mental model is usually:

> VLAN on a switch → mapped to VNI → carried across VXLAN.

But what happens when your VXLAN VTEP is not a switch --- but a router?

In this lab, I built VXLAN EVPN over an IPsec-protected WAN between two **Cisco Catalyst 8000V** routers. Instead of VLANs being the primary Layer-2 construct, we use **bridge-domains**. Let's break down how they compare --- and why they are conceptually the same thing.


## Vlans and Bridge Domains
--- 

On a typical switch, the model looks like this:

VLAN 10\
 ↓\
Mapped to VNI 10010\
 ↓\
Advertised via EVPN\
 ↓\
Encapsulated in VXLAN

On a switch:

-   VLAN = Layer 2 broadcast domain
-   MAC table is built per VLAN
-   VXLAN maps VLAN ↔ VNI
-   SVI provides L3 gateway (optional)

* * * * *

Routers don't operate around VLANs the same way switches do. Instead, they use:

Bridge Domain (BD)

In the HQ-Edge router configuration:

bridge-domain 10\
 member GigabitEthernet2 service-instance 10\
 member evpn-instance 10 vni 10010

What's happening here?

-   A service instance (`encapsulation dot1q 10`) receives VLAN 10 traffic
-   That traffic is placed into Bridge Domain 10
-   The bridge domain is mapped to VNI 10010
-   EVPN advertises MAC reachability
-   The NVE interface encapsulates traffic into VXLAN

Conceptually:

VLAN 10 (Switch world)\
 =\
Bridge Domain 10 (Router world)

Same Layer-2 construct.\
Different implementation model.

* * * * *

Why Routers Use Bridge Domains
------------------------------

Routers are fundamentally Layer-3 devices.

When you enable L2 functionality on a router, you're activating features typically associated with:

L2VPN / Ethernet Virtual Circuit (EVC)

Instead of VLANs being native objects like on a switch, routers use:

-   Service Instances

-   Encapsulation dot1q

-   Bridge Domains

This gives routers much more flexibility:

-   Per-service QoS

-   Per-service policy

-   L2VPN support (xconnect, EVPN, pseudowire, etc.)

-   WAN transport integration (IPsec, GRE, MPLS, etc.)

In other words:

-   Switch VLANs are campus-native

-   Router bridge-domains are service-provider-native

* * * * *

How This Looks in Your VXLAN EVPN Topology
------------------------------------------

In your design:

-   HQ-Edge ↔ Cloud-Edge

-   IPsec-protected WAN

-   BGP EVPN control-plane

-   NVE interface using Loopback1

-   VNI 10010

-   Bridge-Domain 10

Data flow looks like this:

Host → Gi2.10 (service instance)\
 ↓\
Bridge Domain 10\
 ↓\
EVPN Instance 10\
 ↓\
VNI 10010\
 ↓\
NVE1\
 ↓\
IPsec Tunnel\
 ↓\
Remote VTEP

From the host's perspective?

It's just VLAN 10 extended across the WAN.

* * * * *

Key Differences
---------------

-   Native L2 object

    -   Switch: VLAN

    -   Router: Bridge Domain

-   Designed for

    -   Switch: Campus / Data Center

    -   Router: Service Provider / WAN

-   Configuration style

    -   Switch: `vlan 10`

    -   Router: `bridge-domain 10`

-   Port membership

    -   Switch: `switchport access vlan 10`

    -   Router: `service instance 10 ethernet`

-   VXLAN mapping

    -   Switch: VLAN ↔ VNI

    -   Router: BD ↔ VNI

-   Flexibility

    -   Switch: Moderate

    -   Router: Very high

* * * * *

The Most Important Takeaway
---------------------------

VXLAN does not care whether the Layer-2 domain originated from:

-   A VLAN

-   A Bridge Domain

-   An EVPN instance

It only cares about:

VNI + MAC reachability (EVPN control-plane)

That's it.

The VTEP abstracts the local Layer-2 construct and turns it into:

VNI 10010

Everything else is implementation detail.

* * * * *

When Would You Use Each?
------------------------

### Use VLAN-based VXLAN when:

-   You're in a data center

-   You're using hardware switches

-   You want traditional leaf/spine fabric design

### Use Bridge-Domain-based VXLAN when:

-   You're extending L2 over a routed WAN

-   You're using routers as VTEPs

-   You need IPsec transport

-   You're integrating with L2VPN services

Your lab is a perfect example of:

EVPN over VXLAN over IPsec over Internet

And that's something switches typically don't do well --- but routers do beautifully.
