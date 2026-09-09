---
title: "Structuring Ansible Files"
date: 2026-09-08
tags: ["Ansible", "Networking", "Automation"]
description: "A walkthrough of the file structure I use for network automation projects in Ansible, and what each piece is actually doing."
---

When starting to build larger Ansible projects, I always found myself wondering what the file structure should look like and what each piece was actually doing. In this post, I want to walk through what I think are the most important files for getting a network automation project off the ground with Ansible. Having the right structure in place from the start can save a lot of headaches down the road. I'll go over each file, how it's formatted, and how it fits into the overall project. Of course, there are many ways to approach network management with Ansible, this is just the structure that's worked well for me.

---

### The Host File
The Host file is where all the device definitions that the automation will run against are stored. This is where we will put all the Routers and Switches.

You can create your inventory file in one of many formats, depending on the inventory plugins you have. The most common formats are INI and YAML because Ansible includes built-in support for them.

Even if you do not define any groups in your inventory, Ansible creates two default groups: **all and ungrouped.** The all group contains every host. The ungrouped group contains all hosts that do not belong to any other group.

**Children and Host** `children` and `hosts` are the two ways a group can have members, and they nest differently.

- `hosts` lists actual machines
- `children` lists other groups, not machines.

Example Host File:
```yaml
all:
  children:
    cisco:
      children:
        routers:
          hosts:
            R1:
              ansible_host: 192.168.0.100
            R2:
              ansible_host: 192.168.0.101
            R3:
              ansible_host: 192.168.0.102
    arista:
      children:
        switches:
          hosts:
            S1:
              ansible_host: 192.168.0.103
            S2:
              ansible_host: 192.168.0.104
```

### The Group Vars folder
Created as a folder and in this folder we will have files for each of the groups that we created. For example, above we created a "cisco" and an "arista" group. Now we can create a file for each to define certain variables that will be specific to each group. It is also very common to have an `all.yml` group for everything.

Here is an example of what you might see in a Group Vars file:
```yaml
---
ntp_servers:
  - 10.0.0.1
  - 10.0.0.2

dns_servers:
  - 8.8.8.8
  - 8.8.4.4
```

### The Host Vars folder
The Host Vars folder contains files for all hosts that were defined in the host file. The file names must match what was defined in the host file. These files contain all the variables that are specific to each host, think things like IP address, and BGP information.

Example Host Vars:
```yaml
---
interfaces:
  - name: GigabitEthernet0/0
    ip: 10.1.1.1
    mask: 255.255.255.252
  - name: Loopback0
    ip: 1.1.1.1
    mask: 255.255.255.255

bgp:
  asn: 65001
  router_id: 1.1.1.1
  neighbors:
    - neighbor: 10.1.1.2
      remote_asn: 65002
    - neighbor: 10.1.2.2
      remote_asn: 65003
```

### The Roles Folder
The Roles folder is where the actual work happens. If the host file tells Ansible _what_ to run against, and group_vars/host_vars tell it _what values_ to use, roles tell it _what to do_.

A role is a self-contained, reusable bundle of tasks, templates, and files, all built around a single purpose. Instead of writing one giant playbook that configures NTP, DNS, VLANs, and BGP all in one file, you break each of those into its own role. This makes things reusable across projects and much easier to read six months from now when you've forgotten how any of it works.

Ansible expects the Roles folder to be formatted in a specific way. Under Roles we will place folders that name what the role is doing, for example a folder called `ntp` and another called `bgp`. Inside these folders we will have a `tasks` folder and sometimes a `templates` folder. The tasks folder contains the play that will be run, and it is going to be called `main.yml`. The templates folder contains Jinja2 templates that are used to build the configuration needed for the task to run. This configuration is built by pulling in variables from group_vars or host_vars and then passing them to the tasks to be run.

A role can also include a few other folders as a project grows: `handlers` (for tasks that only run when notified, like saving a config), `defaults` (for easily overridable default variable values), and `vars` (for variables specific to the role itself). We won't dig into those here, but it's worth knowing they exist once you start pulling roles from Ansible Galaxy or building more complex ones.

Here is an example of a Jinja file used for BGP configuration, note how the varibles are all pulled from the "host_vars" folder:

**roles/bgp/templates/bgp.j2**
```jinja
router bgp {{ bgp.asn }}
 bgp router-id {{ bgp.router_id }}
{% for neighbor in bgp.neighbors %}
 neighbor {{ neighbor.neighbor }} remote-as {{ neighbor.remote_asn }}
{% endfor %}
```

Here is an example of a task that will render and then push the BGP configuration:

**roles/bgp/tasks/main.yml**
```yaml
---
- name: Push BGP configuration to device
  cisco.ios.ios_config:
    src: "{{ lookup('template', 'bgp.j2') }}"
  notify: save config
```

### The Site
Putting it all together, we will have a `site.yml` that kicks the whole thing off. This is the playbook you actually run to start the process, and it's what calls the different roles we've defined.

**site.yml**
```yaml
---
- name: Configure network devices
  hosts: all
  gather_facts: no
  roles:
    - ntp
    - bgp
```

At its core, a playbook just needs to know two things: which hosts to run against (`hosts: all`, pulled straight from the inventory) and which roles to apply. `gather_facts: no` is common in network automation since most network modules don't need or support the standard fact-gathering Ansible does for Linux/Windows hosts, skipping it also speeds up the run.

When you execute `ansible-playbook site.yml`, Ansible walks through the `roles` list in order, running each role's `tasks/main.yml` against every host in scope, pulling in whatever `group_vars` and `host_vars` apply to that host along the way.

Here is the Whole file structure:
```
network-automation/
├── ansible.cfg
├── inventory/
│   └── hosts.yml
│
├── group_vars/
│   ├── all.yml
│   ├── cisco.yml
│   └── arista.yml
│
├── host_vars/
│   ├── R1.yml
│   ├── R2.yml
│   ├── R3.yml
│   ├── S1.yml
│   └── S2.yml
│
├── roles/
│   ├── ntp/
│   │   ├── tasks/main.yml
│   │   └── templates/ntp.j2
│   │
│   └── bgp/
│       ├── tasks/main.yml
│       └── templates/bgp.j2
│
└── site.yml                       <-- Main playbook, calls the roles
```
