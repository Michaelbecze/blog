---
title: "Passing the CCNP Autocor"
date: 2026-10-13
tags: ["Cisco", "Certification", "Automation"]
description: "My experience studying for and passing the CCNP Automation (350-901 AUTOCOR) exam on my second attempt, including resources and what to expect."
---

I recently sat for and passed the CCNP Automation (350-901 AUTOCOR). This was my second attempt at this exam. My first attempt was at Cisco Live this year, and I was not very well prepared. Despite the failure, it gave me valuable insight into how the exam works and which areas to focus on.

In this post I’m going to walk through how and what I studied, some of the resources I used, and what to expect from the exam itself.

### Autocor Study Resources

I started studying for this exam in February. At the time I was using the INE video course because it was what I had access to, but I found it very slow and hard to get through. I was just trying to cram in as much as possible because I was scheduled to take the exam at Cisco Live.

My first attempt at Cisco Live did not go well, but I learned what I needed to focus on, and that INE was the wrong resource for me. The exam expects you to know Ansible, Terraform, GitLab, YANG, and Python libraries such as Netmiko, virl2, requests (for RESTCONF), ncclient, FastMCP, and LangChain just to get started.

After that, I got a subscription to CBT Nuggets and worked through their course. Although CBT Nuggets lacks depth at times, all of its content is relevant and points you in the right direction. After studying a topic, I ALWAYS labbed it. I started the course a little backwards and did the Git section first, because everything revolves around Git, and you need to know how to use it with GitLab and a CI/CD pipeline. I installed GitLab and used it for most of my labs.

After finishing the CBT Nuggets courses and doing a lot of labbing with Ansible, Terraform, and Python, I still felt weak in Python. That’s when I found Andreas Baekdahl’s free Python course. It’s short but very well done and a great refresher. I also made sure I could construct every task in the Network Automation section of the blueprint from scratch, without AI or Google to help.

Lastly, I picked up a few books along the way that I found interesting. I didn’t read them cover to cover, just the sections that applied: _Network Automation Cookbook_, _Automate Your Network_, and _Cisco pyATS_.

#### Summary of Resources

- CBT Nuggets
- INE
- Books
  - Network Automation Cookbook
  - Automate Your Network
  - Cisco pyATS
- Andreas Baekdahl Free Python Course
- Labbing as much as possible

### Autocor Exam Experience

The AUTOCOR exam is a full 2 hours, and on both attempts I used the entire time, down to the last minute. Many of the questions are lengthy and sometimes include irrelevant details.

Most questions are pretty straightforward, asking you to complete a script in Ansible, Terraform, or Python. However, some questions I encountered were almost gibberish with no clear answer. For those, I guessed and moved on. There were also some very advanced Python questions where I had trouble deconstructing what was going on and how it worked.

### Final Thoughts

If I could go back and do it again, I’d skip the cramming and start with hands-on labs from day one. The AUTOCOR rewards people who have actually built things: written the Ansible playbook, debugged the Terraform state, pushed a change through a GitLab pipeline. Watching videos only gets you so far, and my first attempt proved it.

My advice for anyone preparing:

- **Pick a course that fits how you learn.** INE wasn’t the right fit for me, and switching to CBT Nuggets made a big difference.
- **Lab everything.** 
- **Shore up your Python early.** It shows up everywhere, and the harder questions assume you can read unfamiliar code quickly.
- **Use the blueprint as your checklist.** It’s an accurate map of what you’ll face.
- **Don’t be discouraged by a failed attempt.** Mine was the most useful part of my prep, since it showed me exactly where my gaps were.

Passing this exam was a great step forward for me, and the skills carry directly into real-world network automation work. If you’re on the same path, good luck, and feel free to reach out with questions.
