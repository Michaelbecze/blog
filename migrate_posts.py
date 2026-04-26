#!/usr/bin/env python3
"""Migrate Jekyll posts to Astro content collections."""
import re
import os

POSTS = {
    "2026-01-01-my-first-post.md": dict(
        title="My First Post",
        date="2026-01-01",
        tags=[],
        description="Hello world — the first post on this blog.",
    ),
    "2026-01-10-enarsi.md": dict(
        title="Passing the ENARSI",
        date="2026-01-10",
        tags=["Cisco", "Certification"],
        description=(
            "My experience studying for and passing the CCNP ENARSI (300-410) exam, "
            "including resources and what to expect."
        ),
    ),
    "2026-01-25-L2-Vxlan-on-Catalylst.md": dict(
        slug="2026-01-25-l2-vxlan-on-catalyst.md",
        title="VXLAN EVPN on Catalyst Switches",
        date="2026-01-25",
        tags=["VXLAN", "EVPN", "Catalyst"],
        description=(
            "Setting up a basic VXLAN EVPN deployment on Cisco Catalyst switches "
            "using MP-BGP EVPN as the control plane."
        ),
    ),
    "2026-01-31-discontiguous-deployments-of-vxlan.md": dict(
        title="Discontiguous Deployments of VXLAN over an IGP",
        date="2026-01-31",
        tags=["VXLAN", "Catalyst"],
        description=(
            "How to extend a VXLAN fabric across enterprise WAN and campus networks "
            "without redesigning the core."
        ),
    ),
    "2026-02-13-Deploy-StrongSwan-On-Azure-Part1.md": dict(
        slug="2026-02-13-deploy-strongswan-on-azure-part1.md",
        title="Deploy StrongSwan on Azure for IPSec VPN — Part 1",
        date="2026-02-13",
        tags=["Azure", "StrongSwan", "IPSec"],
        description=(
            "Deploying StrongSwan on an Ubuntu VM in Azure to establish a policy-based "
            "IPSec VPN tunnel to an on-premises Cisco IOS-XE router."
        ),
    ),
    "2026-02-15-Deploy-StrongSwan-On-Azure-Part2.md": dict(
        slug="2026-02-15-deploy-strongswan-on-azure-part2.md",
        title="Deploy StrongSwan on Azure — Part 2: Terraform",
        date="2026-02-15",
        tags=["Azure", "StrongSwan", "Terraform"],
        description=(
            "Using Terraform to deploy the entire StrongSwan IPSec VPN lab environment "
            "in Azure as Infrastructure as Code."
        ),
    ),
    "2026-02-28-VXLAN-Using-Bridge-Groups.md": dict(
        slug="2026-02-28-vxlan-using-bridge-groups.md",
        title="EVPN VXLAN over a Bridge Domain",
        date="2026-02-28",
        tags=["VXLAN", "EVPN"],
        description=(
            "Extending Layer 2 networks over VXLAN using bridge domains on a router, "
            "rather than a traditional switch-to-switch setup."
        ),
    ),
    "2026-03-15-Intergrated-routing-and-bridgeing-in-L3VXLAN.md": dict(
        slug="2026-03-15-irb-in-l3vxlan.md",
        title="Integrated Routing and Bridging in L3 VXLAN",
        date="2026-03-15",
        tags=["VXLAN", "EVPN", "IRB"],
        description=(
            "An explanation of IRB in VXLAN fabrics, covering both Asymmetric and "
            "Symmetric IRB models and their forwarding trade-offs."
        ),
    ),
    "2026-03-29-Sysmmetric-IRB-Anycast-Gateway-on-Catalyst.md": dict(
        slug="2026-03-29-symmetric-irb-anycast-gateway.md",
        title="Symmetric IRB with Anycast Gateway on Catalyst",
        date="2026-03-29",
        tags=["VXLAN", "EVPN", "IRB", "Catalyst"],
        description=(
            "Configuring Symmetric IRB with an Anycast Gateway in a VXLAN EVPN fabric "
            "on Cisco Catalyst IOS-XE, with both L2 and L3 VNIs."
        ),
    ),
    "2026-04-18-External-Connection-with-L2.md": dict(
        slug="2026-04-18-external-connection-with-l2.md",
        title="External Connections into a VXLAN Fabric via L2",
        date="2026-04-18",
        tags=["VXLAN", "EVPN", "Catalyst"],
        description=(
            "Bringing external connections into a VXLAN fabric using a border leaf with "
            "both L2 VLAN extension and an L3 eBGP handoff to a firewall."
        ),
    ),
}

# Internal link map: old Jekyll URL fragment → new Astro path
LINK_MAP = {
    "/blog/2026/03/15/Intergrated-routing-and-bridgeing-in-L3VXLAN.html":
        "/blog/posts/2026-03-15-irb-in-l3vxlan/",
    "/blog/2026/03/29/Sysmmetric-IRB-Anycast-Gateway-on-Catalyst.html":
        "/blog/posts/2026-03-29-symmetric-irb-anycast-gateway/",
}

os.makedirs("src/content/posts", exist_ok=True)

for src_filename, meta in POSTS.items():
    src_path = f"_posts/{src_filename}"
    dst_filename = meta.get("slug", src_filename.lower())
    dst_path = f"src/content/posts/{dst_filename}"

    with open(src_path) as f:
        content = f.read()

    # Strip Jekyll frontmatter (--- ... ---)
    content = re.sub(r"^\s*---\s*\n.*?---\s*\n", "", content, flags=re.DOTALL).lstrip()

    # Remove the very first heading line (## Title or # Title) since it's in frontmatter
    content = re.sub(r"^#{1,3} .+\n\n?", "", content, count=1)

    # Replace Jekyll image paths
    content = content.replace("{{ site.baseurl }}/assets/", "/blog/assets/")

    # Replace any full Jekyll post URLs with Astro equivalents
    for old, new in LINK_MAP.items():
        content = content.replace(f"https://michaelbecze.github.io{old}", new)

    # Build frontmatter
    tags_str = "[" + ", ".join(f'"{t}"' for t in meta["tags"]) + "]"
    title = meta["title"].replace('"', '\\"')
    desc = meta["description"].replace('"', '\\"')

    frontmatter = (
        f'---\n'
        f'title: "{title}"\n'
        f'date: {meta["date"]}\n'
        f'tags: {tags_str}\n'
        f'description: "{desc}"\n'
        f'---\n\n'
    )

    with open(dst_path, "w") as f:
        f.write(frontmatter + content.strip() + "\n")

    print(f"  {src_filename} → {dst_filename}")

print(f"\nMigrated {len(POSTS)} posts.")
