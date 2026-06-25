# AI Agents: Intensive Vibe Coding Capstone Project — COMPREHENSIVE REFERENCE FILE

> **Purpose:** Full reference context for an AI collaborator (e.g., a Claude project) assisting with this Kaggle capstone.
> **Source competition:** https://www.kaggle.com/competitions/vibecoding-agents-capstone-project
> **Host:** Kaggle  |  **Sponsor:** Google  |  **Type:** Community Hackathon
> **Captured from tabs:** Overview, Writeups, Code, Discussion, Rules
>
> **How to read this file:** For each section you will find (1) the EXACT verbatim text copied from the competition page, inside a quoted block, followed by (2) a SUMMARY and (3) KEY INSIGHTS / ANALYSIS. Verbatim text is reproduced as-is for accuracy; summaries and insights are added interpretation.

---

# TABLE OF CONTENTS

1. Overview Tab (verbatim + summary + insights)
   - Overview
   - Description
   - Submission Requirements
   - Tracks and Awards
   - Evaluation
   - Judges
   - Timeline
   - Citation
   - Sidebar facts
2. Writeups Tab (verbatim + summary)
3. Code Tab (verbatim + summary)
4. Discussion Tab (verbatim + summary)
5. Rules Tab (FULL VERBATIM + summary + insights)
   - Competition-Specific Terms
   - Competition-Specific Rules
   - Kaggle Foundational Rules (General Competition Rules)
6. Cross-cutting Key Insights & Strategy
7. Build Checklist

---

# 1. OVERVIEW TAB

## 1.1 Overview — VERBATIM

> The AI Agents: Intensive Vibe Coding Capstone Project invites participants to build an AI agent using the concepts, tools, and best practices learned in Kaggle's 5-Day AI Agents: Intensive Vibe Coding Course with Google. Participants will create a practical, real-world solution that demonstrates how AI agents can automate tasks, assist users, solve business challenges, or improve everyday workflows.
>
> Submissions should showcase both the project's value and technical implementation through a Kaggle Writeup, public codebase, video demonstration, and project link. Projects may be entered into one of four tracks: Agents for Good, Agents for Business, Concierge Agents, or Freestyle and will be evaluated based on innovation, solution design, communication, and the effective application of course concepts and agent technologies.
>
> Start: a day ago
> Close: 17 days to go

## 1.2 Description — VERBATIM

> AI agents are rapidly changing how we interact with technology, enabling systems that can reason, take action, and complete complex tasks on behalf of users. In this capstone project, you'll apply the concepts, tools, and techniques learned throughout Kaggle's 5-Day AI Agents: Intensive Vibe Coding Course with Google to build an agent that solves a meaningful real-world problem. Whether you're creating an assistant that helps individuals stay organized, streamlines business processes, supports social impact initiatives, or explores a completely new idea, this project is an opportunity to move beyond experimentation and develop something useful, practical, and shareable. We encourage participants to think creatively, focus on delivering value, and demonstrate how agent-based systems can address real challenges.
>
> Your submission should showcase both the vision behind your project and the technical decisions that bring it to life. Judges will evaluate projects based on their problem definition, solution design, implementation quality, effective use of agent technologies, and overall user value. Successful submissions will clearly demonstrate concepts covered in the course while highlighting thoughtful architecture, strong documentation, and a compelling project story.
>
> By the end of the capstone, you'll have more than a prototype – you'll have a portfolio-ready project that demonstrates your ability to design, build, and communicate modern AI agent systems.

**SUMMARY:** Build a working AI agent that solves a real, meaningful problem, using skills from Kaggle's 5-Day AI Agents Intensive Vibe Coding Course with Google. The deliverable is portfolio-ready, not just a prototype. It must show both vision (problem/value) and technical execution (architecture/code).

**KEY INSIGHTS:**
- The agent must be **central** to the solution — agentic behavior (reasoning + taking action + completing complex tasks) should be the point, not a bolt-on.
- Judges weigh five things: problem definition, solution design, implementation quality, effective use of agent technologies, and user value.
- "Demonstrate course concepts" is repeated — explicitly tie the build back to taught concepts (see Evaluation section for the required concept list).

## 1.3 Submission Requirements — VERBATIM

> The Judges will be reviewing submissions in four tracks (please review the section "Tracks and Awards" to learn more about the categories). While we have set these to inspire and focus our capstone learners, we are always looking for innovative projects with a "wow" factor. After our review, we may move winners between tracks if that seems appropriate.
>
> A valid submission must contain the following:
> - Kaggle Writeup
> - Media Gallery
> - Attached Public Video
> - Attached Project Link
>
> Your final Submission must be made prior to the deadline. Any un-submitted or draft Writeups by the hackathon deadline will not be considered by the Judges.
>
> To create a new Writeup, click on the "New Writeup" button here. After you have saved your Writeup, you should see a "Submit" button in the top right corner.
>
> Note: If you attach a private Kaggle Resource to your public Kaggle Writeup, your private Resource will automatically be made public after the deadline.
>
> **1. Kaggle Writeup**
> The Kaggle Writeup serves as your project report. This should include a title, subtitle, and a detailed analysis of your submission. You must select a Track for your Writeup in order to submit.
> Your Writeup should not exceed 2,500 words. Submissions over this limit may be subject to penalty.
> The below assets must be attached to the Writeup to be eligible.
>
> **a. Media Gallery**
> This is where you should attach any images and/or videos associated with your submission. A cover image is required to submit your Writeup and a video is a required part of the submission.
>
> **b. Video**
> Attach your video to the Media Gallery. Videos should be 5 minutes or less, and should be published to Youtube.
>
> **c. Public Project Link**
> A URL to your working product or interactive demo. This allows judges to experience your project firsthand, if applicable. It should be publicly accessible and not require a login or paywall. If a live demo is not feasible, a link to your public code repository (e.g., GitHub) is required, including detailed setup instructions.

**SUMMARY:** A valid submission = Kaggle Writeup + Media Gallery + public YouTube video + project link. The Writeup (<=2,500 words) needs a title, subtitle, detailed analysis, and a selected Track. A cover image and a video are mandatory. The project link must be public (no login/paywall); a public GitHub repo with setup instructions is the fallback if no live demo.

**KEY INSIGHTS:**
- **Draft = disqualified.** You must click "Submit," not just "Save."
- **Privacy gotcha:** any private Kaggle Resource attached to the public Writeup becomes public after the deadline — don't attach anything sensitive.
- Word limit 2,500 with penalties for going over — write tight.
- Judges may reassign your track, so pick the closest fit but don't over-optimize.

## 1.4 Tracks and Awards — VERBATIM

> **Agents for Good**
> In the Agents for Good track, we'll be looking for submissions that help solve problems for humanity. From optimizing agriculture to managing public health, advancing education or supporting art and literature - this is the track for helping people.
> Award 1 — Winner will receive Kaggle swag. (Non-monetary)
> Award 2 — Winner will receive Kaggle swag. (Non-monetary)
> Award 3 — Winner will receive Kaggle swag. (Non-monetary)
>
> **Agents for Business**
> Enterprises are increasingly using AI agents to solve critical problems, from managing expense submissions to highlighting pipeline actions, driving insights or creating new products. In this track, you'll create an agent designed to solve compelling business problems with cost or revenue on the line.
> Award 1 — Winner will receive Kaggle swag. (Non-monetary)
> Award 2 — Winner will receive Kaggle swag. (Non-monetary)
> Award 3 — Winner will receive Kaggle swag. (Non-monetary)
>
> **Concierge Agents**
> The opportunity for personal AI agents to streamline and simplify people's lives is incredible. From managing the invite list for a party to planning a garden, or helping manage complicated medications - safe and secure agents can free time for things that really matter. In this track, you will solve individual, family or social challenges in a way that keeps personal information safe and secure.
> Award 1 — Winner will receive Kaggle swag. (Non-monetary)
> Award 2 — Winner will receive Kaggle swag. (Non-monetary)
> Award 3 — Winner will receive Kaggle swag. (Non-monetary)
>
> **Freestyle**
> Do you have a great idea that doesn't fit into a neat bucket? Maybe it's an agent helping your fandom keep track of concert recordings, helping decode cursive uploaded by historians, or tracking the position of recently launched satellites. Whatever you build, this submission will show the best practices of agent development and deployment!
> Award 1 — Winner will receive Kaggle swag. (Non-monetary)
> Award 2 — Winner will receive Kaggle swag. (Non-monetary)
> Award 3 — Winner will receive Kaggle swag. (Non-monetary)

**SUMMARY:** Four tracks, each with 3 non-monetary Kaggle-swag awards. Agents for Good = social/humanity impact. Agents for Business = enterprise problems with cost/revenue stakes. Concierge Agents = personal/family/social tasks with strong privacy emphasis. Freestyle = anything novel that shows agent best practices.

**KEY INSIGHTS:**
- **Concierge** explicitly requires keeping personal information safe and secure — a strong fit if you plan to highlight the "Security features" course concept.
- **Business** track wants a clear cost/revenue narrative — quantify ROI in the pitch.
- **Good** track rewards mission/impact framing.
- **Freestyle** is the catch-all but still graded on agent best practices and deployment.

## 1.5 Evaluation — VERBATIM

> In your submission, you must demonstrate what you've learned in this course by applying at least three (3) of the key concepts covered in the course, including:
>
> | Key Concept | Where to Demonstrate |
> |---|---|
> | Agent / Multi-agent system (ADK) | Code |
> | MCP Server | Code |
> | Antigravity | Video |
> | Security features | Code or Video |
> | Deployability | Video |
> | Agent skills (e.g., Agents CLI) | Code or Video |
>
> **Category 1: The Pitch - Problem, Solution, Value (30 points total)**
> This is where you'll be evaluated on the "why" and "what" of your project and how well you communicate your vision.
>
> - **Core Concept & Value (10 points):** Your project's central idea, its relevance to the track for the submission; focused on innovation and value. The use of agents should be clear, meaningful and central to your solution.
> - **YouTube Video Submission (10 points):** Your video should showcase clarity, conciseness and quality of messaging. It should articulate some of the following - but only in the 5 minute limit:
>   - Problem Statement: Describe the problem you're trying to solve, and why you think it's an important or interesting problem to solve.
>   - Agents: Why agents? How can agents uniquely help solve that problem?
>   - Architecture: Images and a description of the overall agent architecture.
>   - Demo: demo of your solution, which can include images, an animation, or a video of the agent working.
>   - The Build: How you created it, what tools or technologies you used.
> - **Writeup (10 points):** How well your written submission articulates the problem you're solving, your solution, its architecture, and your project's journey.
>
> **Category 2: The Implementation - Architecture, Code (70 points total)**
> This is where you'll be evaluated on the "how" of your project. This includes the quality of your code, technical design, and AI integration.
>
> - **Technical Implementation (50 points):** For this criteria, we will assess the quality of your solution's architecture, and your code, and the meaningful use of agents in your solution. We will also be looking at your tool use, especially clever usage of existing toolsets. Your code should contain comments pertinent to implementation, design and behaviors. Participants are not required to deploy their agents to a live public endpoint for judging purposes; however, if you do deploy, please provide documentation to reproduce the deployment. 🚨REMINDER: DO NOT INCLUDE ANY API KEYS OR PASSWORDS IN YOUR CODE.
> - **Documentation (20 points):** Your submission (when submitting via GitHub) should contain a README.md file explaining the problem, solution, architecture, instructions for setup, and relevant diagrams or images where appropriate.

**SUMMARY:** Must demonstrate >=3 of six course concepts (ADK agent/multi-agent, MCP Server, Antigravity, Security features, Deployability, Agent skills/CLI), each shown in a specific place (Code and/or Video). Scoring totals 100 points: Pitch = 30 (Core Concept & Value 10, Video 10, Writeup 10); Implementation = 70 (Technical Implementation 50, Documentation 20).

**KEY INSIGHTS:**
- **Implementation is 70% of the score** — code quality, architecture, meaningful agent use, and clever tool use matter most.
- The single biggest line item is **Technical Implementation (50 pts)**. Prioritize a clean, well-commented, genuinely agentic codebase.
- **Documentation (20 pts)** is nearly as heavy as the entire video — a strong README is high ROI.
- Deployment is optional; if deployed, include reproduction docs.
- Hard rule: **no API keys or passwords in code.**
- Map each of your >=3 chosen concepts to its required location (e.g., MCP Server → show in Code; Antigravity & Deployability → show in Video).

## 1.6 Judges — VERBATIM

> - Tanvi Singhal
> - Laxmi Harikumar
> - Aman Tayal
> - Vijit Singh
> - Eric Schmidt — Developer Advocacy, Google
> - Nilay Chauhan — DevRel, Kaggle
> - Thilakraj Sripal — AI/ML Specialist, Kaggle
> - Naz Bayrak — AI Specialist, Google
> - Luis Sala
> - MartynaPlomecka — Research Scientist, Google Deepmind
> - Tania Rodriguez Fuentes — Program Manager, EPAM Systems
> - Sara Wolley — Program Manager, Kaggle
> - Brenda Flynn — Program Manager, Kaggle

**SUMMARY:** 13 listed judges spanning Google (incl. DeepMind), Kaggle DevRel/Program Management, and EPAM. Mix of AI/ML specialists, developer advocates, and program managers.

## 1.7 Timeline — VERBATIM

> Capstone project is announced on June 19, 2026 during the 5 Days livestream.
> Submissions are due no later than July 6, 2026 at 11:59 PM PT

**SUMMARY:** Announced June 19, 2026; submissions due July 6, 2026, 11:59 PM PT.

## 1.8 Citation — VERBATIM

> Brenda Flynn, Kanchana Patlolla, Polong Lin, Anant Nawalgaria, Fran Hinkelmann, Kinjal Parekh, Melissa Nalubwama-Mukasa, María Cruz, and Naz Bayrak. AI Agents: Intensive Vibe Coding Capstone Project. https://kaggle.com/competitions/vibecoding-agents-capstone-project, 2026. Kaggle.

## 1.9 Sidebar Facts — VERBATIM

> Competition Host: Kaggle
> Prizes & Awards: 12 Swag — Does not award Points or Medals
> Participation: 507 Entrants, 10 Participants, 10 Teams, 10 Submissions
> (Header banner: "KAGGLE · COMMUNITY HACKATHON · 17 DAYS TO GO")

**SUMMARY:** Hosted by Kaggle; 12 swag prizes total; no Kaggle Points/Medals awarded. Entrant count grew during capture (484 → 498 → 507), with 10 teams/submissions visible. The only imagery on the page is the decorative banner illustration (laptop with code brackets, charts, and agent-network style graphics) — no architecture diagrams or instructional images.

---

# 2. WRITEUPS TAB

## 2.1 Writeups — VERBATIM

> Writeups
> Track: All
> - SUBMITTED — Project submitted — visibility_off — Viewable at Hackathon close — Team 1
> - SUBMITTED — Project submitted — visibility_off — Viewable at Hackathon close — Team 2
> - SUBMITTED — Project submitted — visibility_off — Viewable at Hackathon close — Team 3
> - SUBMITTED — Project submitted — visibility_off — Viewable at Hackathon close — Team 4
> - SUBMITTED — Project submitted — visibility_off — Viewable at Hackathon close — Team 5
> - SUBMITTED — Project submitted — visibility_off — Viewable at Hackathon close — Team 6
> - SUBMITTED — Project submitted — visibility_off — Viewable at Hackathon close — Team 7
> - SUBMITTED — Project submitted — visibility_off — Viewable at Hackathon close — Team 8
> - SUBMITTED — Project submitted — visibility_off — Viewable at Hackathon close — Team 9
> - SUBMITTED — Project submitted — visibility_off — Viewable at Hackathon close — Team 10

**SUMMARY:** Ten teams (Team 1–Team 10) have submitted projects, but every Writeup is hidden ("Viewable at Hackathon close"). No competitor content is accessible during the competition. There is a Track filter (default "All").

**KEY INSIGHT:** You cannot learn from other submissions until the hackathon closes — so there is no benchmark to copy. Focus on the rubric, not on peers.

---

# 3. CODE TAB

## 3.1 Code — VERBATIM

> Notebooks
> New Notebook
> Filters: All / Your Work / Shared With You / Bookmarks
> Hotness

**SUMMARY:** The Code tab is the Kaggle Notebooks area. No public notebooks have been shared for this competition yet. You can create a "New Notebook" and filter by All / Your Work / Shared With You / Bookmarks, sorted by Hotness.

**KEY INSIGHT:** No starter notebook or public code examples are provided. Per the rules, any public code sharing must happen on Kaggle's forum/notebooks and is then deemed open-source licensed.

---

# 4. DISCUSSION TAB

## 4.1 Discussion — VERBATIM

> Discussion
> Follow
> New Topic
> Filters: All / Owned / Bookmarks
> Hotness
> No discussions found

**SUMMARY:** The Discussion forum is empty ("No discussions found"). You can follow the forum or create a "New Topic."

**KEY INSIGHT:** No clarifications, FAQs, or host announcements have been posted yet. Worth monitoring later for rule clarifications or judge Q&A.

---

# 5. RULES TAB — FULL VERBATIM

> **NOTE:** The following is reproduced verbatim from the competition's Rules tab. Summaries and insights are appended at the end of Section 5.

## 5.0 Preamble — VERBATIM

> ENTRY IN THIS COMPETITION CONSTITUTES YOUR ACCEPTANCE OF THESE OFFICIAL COMPETITION RULES.
>
> See Section 3.18 for defined terms
>
> The Competition named below is a skills-based competition to promote and further the field of data science. You must register via the Competition Website to enter. To enter the Competition, you must agree to these Official Competition Rules, which incorporate by reference the provisions and content of the Competition Website and any Specific Competition Rules herein (collectively, the "Rules"). Please read these Rules carefully before entry to ensure you understand and agree. You further agree that Submission in the Competition constitutes agreement to these Rules. You may not submit to the Competition and are not eligible to receive the prizes associated with this Competition unless you agree to these Rules. These Rules form a binding legal agreement between you and the Competition Sponsor with respect to the Competition. Your competition Submissions must conform to the requirements stated on the Competition Website. Your Submissions will be scored based on the evaluation metric described on the Competition Website. Subject to compliance with the Competition Rules, Prizes, if any, will be awarded to Participants with the best scores, based on the merits of the data science models submitted. See below for the complete Competition Rules. For Competitions designated as hackathons by the Competition Sponsor ("Hackathons"), your Submissions will be judged by the Competition Sponsor based on the evaluation rubric set forth on the Competition Website ("Evaluation Rubric"). The Prizes, if any, will be awarded to Participants with the highest ranking(s) as determined by the Competition Sponsor based on such rubric.
>
> You cannot sign up to Kaggle from multiple accounts and therefore you cannot enter or submit from multiple accounts.

## 5.1 Competition-Specific Terms — VERBATIM

> **1. COMPETITION-SPECIFIC TERMS**
>
> **1. COMPETITION TITLE** — Vibecoding Agents - Capstone Project
>
> **2. COMPETITION SPONSOR** — Google
>
> **3. COMPETITION SPONSOR ADDRESS** — 1600 Amphitheatre Pkwy Mountain View, CA 94043
>
> **4. COMPETITION WEBSITE** — https://www.kaggle.com/competitions/vibecoding-agents-capstone-project
>
> **5. TOTAL PRIZES AVAILABLE:** 12 pieces of swag, distributed equally across 4 categories: Agents for Good, Agents for Business, Concierge Agents, Freestyle.
>
> **6. WINNER LICENSE TYPE** — CC-BY 4.0
>
> **7. DATA ACCESS AND USE** — N/A

## 5.2 Competition-Specific Rules — VERBATIM

> **2. COMPETITION-SPECIFIC RULES**
>
> In addition to the provisions of the General Competition Rules below, you understand and agree to these Competition-Specific Rules required by the Competition Sponsor:
>
> **1. TEAM LIMITS**
> a. The maximum Team size is five (5).
> b. Team mergers are allowed and can be performed by the Team leader. In order to merge, the combined Team must have a total Submission count less than or equal to the maximum allowed as of the Team Merger Deadline. The maximum allowed is the number of Submissions per day multiplied by the number of days the competition has been running. For Hackathons, each team is allowed one (1) Submission; any Submissions submitted by Participants before merging into a Team will be unsubmitted.
>
> **2. SUBMISSION LIMITS**
> a. For Hackathons, each Team may submit one (1) Submission only.
>
> **3. COMPETITION TIMELINE**
> a. Competition Timeline dates (including Entry Deadline, Final Submission Deadline, Start Date, and Team Merger Deadline, as applicable) are reflected on the competition's Overview > Timeline page.
>
> **4. COMPETITION DATA**
> a. Data Access and Use. None. Competition Data will not be provided by Competition Sponsor for this Competition.
> b. Data Security. You agree to use reasonable and suitable measures to prevent persons who have not formally agreed to these Rules from gaining access to the Competition Data. You agree not to transmit, duplicate, publish, redistribute or otherwise provide or make available the Competition Data to any party not participating in the Competition. You agree to notify Kaggle immediately upon learning of any possible unauthorized transmission of or unauthorized access to the Competition Data and agree to work with Kaggle to rectify any unauthorized transmission or access.
>
> **5. WINNER LICENSE**
> a. Under Section 2.8 (Winners Obligations) of the General Rules below, you hereby grant and will grant the Competition Sponsor the following license(s) with respect to your Submission if you are a Competition winner:
> Open Source: You hereby license and will license your winning Submission and the source code used to generate the Submission under CC-BY 4.0, an Open Source Initiative-approved license (see www.opensource.org) that in no event limits commercial use of such code or model containing or depending on such code.
> For generally commercially available software that you used to generate your Submission that is not owned by you, but that can be procured by the Competition Sponsor without undue expense, you do not need to grant the license in the preceding Section for that software.
> In the event that input data or pretrained models with an incompatible license are used to generate your winning solution, you do not need to grant an open source license in the preceding Section for that data and/or model(s).
> b. You may be required by the Sponsor to provide a detailed description of how the winning Submission was generated, to the Competition Sponsor's specifications, as outlined in Section 2.8, Winner's Obligations. This may include a detailed description of methodology, where one must be able to reproduce the approach by reading the description, and includes a detailed explanation of the architecture, preprocessing, loss function, training details, hyper-parameters, etc. The description should also include a link to a code repository with complete and detailed instructions so that the results obtained can be reproduced.

> **6. EXTERNAL DATA AND TOOLS**
> a. You may use data other than the Competition Data ("External Data") to develop and test your Submissions. However, you will ensure the External Data is either publicly available and equally accessible to use by all Participants of the Competition for purposes of the competition at no cost to the other Participants, or satisfies the Reasonableness criteria as outlined in Section 2.6.b below. The ability to use External Data under this Section does not limit your other obligations under these Competition Rules, including but not limited to Section 2.8 (Winners Obligations).
> b. The use of external data and models is acceptable unless specifically prohibited by the Host. Because of the potential costs or restrictions (e.g., "geo restrictions") associated with obtaining rights to use external data or certain software and associated tools, their use must be "reasonably accessible to all" and of "minimal cost". Also, regardless of the cost challenges as they might affect all Participants during the course of the competition, the costs of potentially procuring a license for software used to generate a Submission, must also be considered. The Host will employ an assessment of whether or not the following criteria can exclude the use of the particular LLM, data set(s), or tool(s):
> Are Participants being excluded from a competition because of the "excessive" costs for access to certain LLMs, external data, or tools that might be used by other Participants. The Host will assess the excessive cost concern by applying a "Reasonableness" standard (the "Reasonableness Standard"). The Reasonableness Standard will be determined and applied by the Host in light of things like cost thresholds and accessibility.
> By way of example only, a small subscription charge to use additional elements of a large language model such as Gemini Advanced are acceptable if meeting the Reasonableness Standard of Sec. 8.2. Purchasing a license to use a proprietary dataset that exceeds the cost of a prize in the competition would not be considered reasonable.
> c. Automated Machine Learning Tools ("AMLT") — Individual Participants and Teams may use automated machine learning tool(s) ("AMLT") (e.g., Google toML, H2O Driverless AI, etc.) to create a Submission, provided that the Participant or Team ensures that they have an appropriate license to the AMLT such that they are able to comply with the Competition Rules.
>
> **7. ELIGIBILITY**
> a. Unless otherwise stated in the Competition-Specific Rules above or prohibited by internal policies of the Competition Entities, employees, interns, contractors, officers and directors of Competition Entities may enter and participate in the Competition, but are not eligible to win any Prizes. "Competition Entities" means the Competition Sponsor, Kaggle Inc., and their respective parent companies, subsidiaries and affiliates. If you are such a Participant from a Competition Entity, you are subject to all applicable internal policies of your employer with respect to your participation.
>
> **8. WINNER'S OBLIGATIONS**
> a. As a condition to being awarded a Prize, a Prize winner must fulfill the following obligations:
> Deliver to the Competition Sponsor the final model's software code as used to generate the winning Submission and associated documentation. The delivered software code should follow these documentation guidelines, must be capable of generating the winning Submission, and contain a description of resources required to build and/or run the executable code successfully. For avoidance of doubt, delivered software code should include training code, inference code, and a description of the required computational environment. For Hackathons, the Submission deliverables will be as described on the Competition Website, which may be information or materials that are not software code.
> a. To the extent that the final model's software code includes generally commercially available software that is not owned by you, but that can be procured by the Competition Sponsor without undue expense, then instead of delivering the code for that software to the Competition Sponsor, you must identify that software, method for procuring it, and any parameters or other information necessary to replicate the winning Submission; Individual Participants and Teams who create a Submission using an AMLT may win a Prize. However, for clarity, the potential winner's Submission must still meet the requirements of these Rules, including but not limited to Section 2.5 (Winners License), Section 2.8 (Winners Obligations), and Section 3.14 (Warranty, Indemnity, and Release)."
> b. Individual Participants and Teams who create a Submission using an AMLT may win a Prize. However, for clarity, the potential winner's Submission must still meet the requirements of these Rules,
> Grant to the Competition Sponsor the license to the winning Submission stated in the Competition Specific Rules above, and represent that you have the unrestricted right to grant that license;
> Sign and return all Prize acceptance documents as may be required by Competition Sponsor or Kaggle, including without limitation: (a) eligibility certifications; (b) licenses, releases and other agreements required under the Rules; and (c) U.S. tax forms (such as IRS Form W-9 if U.S. resident, IRS Form W-8BEN if foreign resident, or future equivalents).
>
> **9. GOVERNING LAW**
> a. Unless otherwise provided in the Competition Specific Rules above, all claims arising out of or relating to these Rules will be governed by California law, excluding its conflict of laws rules, and will be litigated exclusively in the Federal or State courts of Santa Clara County, California, USA. The parties consent to personal jurisdiction in those courts. If any provision of these Rules is held to be invalid or unenforceable, all remaining provisions of the Rules will remain in full force and effect.

## 5.3 Kaggle Competition Foundational Rules (Non-editable) — VERBATIM

> Competition participants must also agree to Kaggle's Foundational Competition Rules. These rules will supersede the competition-specific rules in the event of any conflict.
>
> The following Kaggle Competition Foundational Rules ("Foundational Rules") apply to every competition regardless of whether the Sponsor creates competition-specific rules. Any competition-specific rules provided by the Sponsor are in addition to these rules, and in the case of any conflict or inconsistency, these Foundational Rules control and nullify contrary competition-specific rules.
>
> **GENERAL COMPETITION RULES - BINDING AGREEMENT**
>
> **1. ELIGIBILITY**
> a. To be eligible to enter the Competition, you must be:
> - a registered account holder at Kaggle.com;
> - the older of 18 years old or the age of majority in your jurisdiction of residence (unless otherwise agreed to by Competition Sponsor and appropriate parental/guardian consents have been obtained by Competition Sponsor);
> - not a resident of Crimea, so-called Donetsk People's Republic (DNR) or Luhansk People's Republic (LNR), Cuba, Iran, or North Korea; and
> - not a person or representative of an entity under U.S. export controls or sanctions (see: https://www.treasury.gov/resourcecenter/sanctions/Programs/Pages/Programs.aspx).
> b. Competitions are open to residents of the United States and worldwide, except that if you are a resident of Crimea, so-called Donetsk People's Republic (DNR) or Luhansk People's Republic (LNR), Cuba, Iran, North Korea, or are subject to U.S. export controls or sanctions, you may not enter the Competition. Other local rules and regulations may apply to you, so please check your local laws to ensure that you are eligible to participate in skills-based competitions. The Competition Host reserves the right to forego or award alternative Prizes where needed to comply with local laws. If a winner is located in a country where prizes cannot be awarded, then they are not eligible to receive a prize.
> c. If you are entering as a representative of a company, educational institution or other legal entity, or on behalf of your employer, these rules are binding on you, individually, and the entity you represent or where you are an employee. If you are acting within the scope of your employment, or as an agent of another party, you warrant that such party or your employer has full knowledge of your actions and has consented thereto, including your potential receipt of a Prize. You further warrant that your actions do not violate your employer's or entity's policies and procedures.
> d. The Competition Sponsor reserves the right to verify eligibility and to adjudicate on any dispute at any time. If you provide any false information relating to the Competition concerning your identity, residency, mailing address, telephone number, email address, ownership of right, or information required for entering the Competition, you may be immediately disqualified from the Competition.
>
> **2. SPONSOR AND HOSTING PLATFORM**
> a. The Competition is sponsored by Competition Sponsor named above. The Competition is hosted on behalf of Competition Sponsor by Kaggle Inc. ("Kaggle"). Kaggle is an independent contractor of Competition Sponsor, and is not a party to this or any agreement between you and Competition Sponsor. You understand that Kaggle has no responsibility with respect to selecting the potential Competition winner(s) or awarding any Prizes. Kaggle will perform certain administrative functions relating to hosting the Competition, and you agree to abide by the provisions relating to Kaggle under these Rules. As a Kaggle.com account holder and user of the Kaggle competition platform, remember you have accepted and are subject to the Kaggle Terms of Service at www.kaggle.com/terms in addition to these Rules.
>
> **3. COMPETITION PERIOD**
> a. For the purposes of Prizes, the Competition will run from the Start Date and time to the Final Submission Deadline (such duration the "Competition Period"). The Competition Timeline is subject to change, and Competition Sponsor may introduce additional hurdle deadlines during the Competition Period. Any updated or additional deadlines will be publicized on the Competition Website. It is your responsibility to check the Competition Website regularly to stay informed of any deadline changes. YOU ARE RESPONSIBLE FOR DETERMINING THE CORRESPONDING TIME ZONE IN YOUR LOCATION.
>
> **4. COMPETITION ENTRY**
> a. NO PURCHASE NECESSARY TO ENTER OR WIN. To enter the Competition, you must register on the Competition Website prior to the Entry Deadline, and follow the instructions for developing and entering your Submission through the Competition Website. Your Submissions must be made in the manner and format, and in compliance with all other requirements, stated on the Competition Website (the "Requirements"). Submissions must be received before any Submission deadlines stated on the Competition Website. Submissions not received by the stated deadlines will not be eligible to receive a Prize.
> b. Submissions may not use or incorporate information from hand labeling or human prediction of the validation dataset or test data records.
> c. If the Competition is a multi-stage competition with temporally separate training and/or test data, one or more valid Submissions may be required during each Competition stage in the manner described on the Competition Website in order for the Submissions to be Prize eligible.
> d. Submissions are void if they are in whole or part illegible, incomplete, damaged, altered, counterfeit, obtained through fraud, or late. Competition Sponsor reserves the right to disqualify any entrant who does not follow these Rules, including making a Submission that does not meet the Requirements.
>
> **5. INDIVIDUALS AND TEAMS**
> a. Individual Account. You may make Submissions only under one, unique Kaggle.com account. You will be disqualified if you make Submissions through more than one Kaggle account, or attempt to falsify an account to act as your proxy. You may submit up to the maximum number of Submissions per day as specified on the Competition Website.
> b. Teams. If permitted under the Competition Website guidelines, multiple individuals may collaborate as a Team; however, you may join or form only one Team. Each Team member must be a single individual with a separate Kaggle account. You must register individually for the Competition before joining a Team. You must confirm your Team membership to make it official by responding to the Team notification message sent to your Kaggle account. Team membership may not exceed the Maximum Team Size stated on the Competition Website.
> c. Team Merger. Teams may request to merge via the Competition Website. Team mergers may be allowed provided that: (i) the combined Team does not exceed the Maximum Team Size; (ii) the number of Submissions made by the merging Teams does not exceed the number of Submissions permissible for one Team at the date of the merger request; (iii) the merger is completed before the earlier of: any merger deadline or the Competition deadline; and (iv) the proposed combined Team otherwise meets all the requirements of these Rules.
> d. Private Sharing. No private sharing outside of Teams. Privately sharing code or data outside of Teams is not permitted. It's okay to share code if made available to all Participants on the forums.

> **6. SUBMISSION CODE REQUIREMENTS**
> a. Private Code Sharing. Unless otherwise specifically permitted under the Competition Website or Competition Specific Rules above, during the Competition Period, you are not allowed to privately share source or executable code developed in connection with or based upon the Competition Data or other source or executable code relevant to the Competition ("Competition Code"). This prohibition includes sharing Competition Code between separate Teams, unless a Team merger occurs. Any such sharing of Competition Code is a breach of these Competition Rules and may result in disqualification.
> b. Public Code Sharing. You are permitted to publicly share Competition Code, provided that such public sharing does not violate the intellectual property rights of any third party. If you do choose to share Competition Code or other such code, you are required to share it on Kaggle.com on the discussion forum or notebooks associated specifically with the Competition for the benefit of all competitors. By so sharing, you are deemed to have licensed the shared code under an Open Source Initiative-approved license (see www.opensource.org) that in no event limits commercial use of such Competition Code or model containing or depending on such Competition Code.
> c. Use of Open Source. Unless otherwise stated in the Specific Competition Rules above, if open source code is used in the model to generate the Submission, then you must only use open source code licensed under an Open Source Initiative-approved license (see www.opensource.org) that in no event limits commercial use of such code or model containing or depending on such code.
>
> **7. DETERMINING WINNERS**
> a. Each Submission will be scored and ranked by the evaluation metric stated on the Competition Website. During the Competition Period, the current ranking will be visible on the Competition Website's Public Leaderboard. The potential winner(s) are determined solely by the leaderboard ranking on the Private Leaderboard, subject to compliance with these Rules. The Public Leaderboard will be based on the public test set and the Private Leaderboard will be based on the private test set.
> b. In the event of a tie, the Submission that was entered first to the Competition will be the winner. In the event a potential winner is disqualified for any reason, the Submission that received the next highest score rank will be chosen as the potential winner.
>
> **8. NOTIFICATION OF WINNERS & DISQUALIFICATION**
> a. The potential winner(s) will be notified by email.
> b. If a potential winner (i) does not respond to the notification attempt within one (1) week from the first notification attempt or (ii) notifies Kaggle within one week after the Final Submission Deadline that the potential winner does not want to be nominated as a winner or does not want to receive a Prize, then, in each case (i) and (ii) such potential winner will not receive any Prize, and an alternate potential winner will be selected from among all eligible entries received based on the Competition's judging criteria.
> c. In case (i) and (ii) above Kaggle may disqualify the Participant. However, in case (ii) above, if requested by Kaggle, such potential winner may provide code and documentation to verify the Participant's compliance with these Rules. If the potential winner provides code and documentation to the satisfaction of Kaggle, the Participant will not be disqualified pursuant to this paragraph.
> d. Competition Sponsor reserves the right to disqualify any Participant from the Competition if the Competition Sponsor reasonably believes that the Participant has attempted to undermine the legitimate operation of the Competition by cheating, deception, or other unfair playing practices or abuses, threatens or harasses any other Participants, Competition Sponsor or Kaggle.
> e. A disqualified Participant may be removed from the Competition leaderboard, at Kaggle's sole discretion. If a Participant is removed from the Competition Leaderboard, additional winning features associated with the Kaggle competition platform, for example Kaggle points or medals, may also not be awarded.
> f. The final leaderboard list will be publicly displayed at Kaggle.com. Determinations of Competition Sponsor are final and binding.
>
> **9. PRIZES**
> a. Prize(s) are as described on the Competition Website and are only available for winning during the time period described on the Competition Website. The odds of winning any Prize depends on the number of eligible Submissions received during the Competition Period and the skill of the Participants.
> b. All Prizes are subject to Competition Sponsor's review and verification of the Participant's eligibility and compliance with these Rules, and the compliance of the winning Submissions with the Submissions Requirements. In the event that the Submission demonstrates non-compliance with these Competition Rules, Competition Sponsor may at its discretion take either of the following actions: (i) disqualify the Submission(s); or (ii) require the potential winner to remediate within one week after notice all issues identified in the Submission(s) (including, without limitation, the resolution of license conflicts, the fulfillment of all obligations required by software licenses, and the removal of any software that violates the software restrictions).
> c. A potential winner may decline to be nominated as a Competition winner in accordance with Section 3.8.
> d. Potential winners must return all required Prize acceptance documents within two (2) weeks following notification of such required documents, or such potential winner will be deemed to have forfeited the prize and another potential winner will be selected. Prize(s) will be awarded within approximately thirty (30) days after receipt by Competition Sponsor or Kaggle of the required Prize acceptance documents. Transfer or assignment of a Prize is not allowed.
> e. You are not eligible to receive any Prize if you do not meet the Eligibility requirements in Section 2.7 and Section 3.1 above.
> f. If a Team wins a monetary Prize, the Prize money will be allocated in even shares between the eligible Team members, unless the Team unanimously opts for a different Prize split and notifies Kaggle before Prizes are issued.
>
> **10. TAXES**
> a. ALL TAXES IMPOSED ON PRIZES ARE THE SOLE RESPONSIBILITY OF THE WINNERS. Payments to potential winners are subject to the express requirement that they submit all documentation requested by Competition Sponsor or Kaggle for compliance with applicable state, federal, local and foreign (including provincial) tax reporting and withholding requirements. Prizes will be net of any taxes that Competition Sponsor is required by law to withhold. If a potential winner fails to provide any required documentation or comply with applicable laws, the Prize may be forfeited and Competition Sponsor may select an alternative potential winner. Any winners who are U.S. residents will receive an IRS Form-1099 in the amount of their Prize.
>
> **11. GENERAL CONDITIONS**
> a. All federal, state, provincial and local laws and regulations apply.
>
> **12. PUBLICITY**
> a. You agree that Competition Sponsor, Kaggle and its affiliates may use your name and likeness for advertising and promotional purposes without additional compensation, unless prohibited by law.

> **13. PRIVACY**
> a. You acknowledge and agree that Competition Sponsor and Kaggle may collect, store, share and otherwise use personally identifiable information provided by you during the Kaggle account registration process and the Competition, including but not limited to, name, mailing address, phone number, and email address ("Personal Information"). Kaggle acts as an independent controller with regard to its collection, storage, sharing, and other use of this Personal Information, and will use this Personal Information in accordance with its Privacy Policy <www.kaggle.com/privacy>, including for administering the Competition. As a Kaggle.com account holder, you have the right to request access to, review, rectification, portability or deletion of any personal data held by Kaggle about you by logging into your account and/or contacting Kaggle Support at <www.kaggle.com/contact>.
> b. As part of Competition Sponsor performing this contract between you and the Competition Sponsor, Kaggle will transfer your Personal Information to Competition Sponsor, which acts as an independent controller with regard to this Personal Information. As a controller of such Personal Information, Competition Sponsor agrees to comply with all U.S. and foreign data protection obligations with regard to your Personal Information. Kaggle will transfer your Personal Information to Competition Sponsor in the country specified in the Competition Sponsor Address listed above, which may be a country outside the country of your residence. Such country may not have privacy laws and regulations similar to those of the country of your residence.
>
> **14. WARRANTY, INDEMNITY AND RELEASE**
> a. You warrant that your Submission is your own original work and, as such, you are the sole and exclusive owner and rights holder of the Submission, and you have the right to make the Submission and grant all required licenses. You agree not to make any Submission that: (i) infringes any third party proprietary rights, intellectual property rights, industrial property rights, personal or moral rights or any other rights, including without limitation, copyright, trademark, patent, trade secret, privacy, publicity or confidentiality obligations, or defames any person; or (ii) otherwise violates any applicable U.S. or foreign state or federal law.
> b. To the maximum extent permitted by law, you indemnify and agree to keep indemnified Competition Entities at all times from and against any liability, claims, demands, losses, damages, costs and expenses resulting from any of your acts, defaults or omissions and/or a breach of any warranty set forth herein. To the maximum extent permitted by law, you agree to defend, indemnify and hold harmless the Competition Entities from and against any and all claims, actions, suits or proceedings, as well as any and all losses, liabilities, damages, costs and expenses (including reasonable attorneys fees) arising out of or accruing from: (a) your Submission or other material uploaded or otherwise provided by you that infringes any third party proprietary rights, intellectual property rights, industrial property rights, personal or moral rights or any other rights, including without limitation, copyright, trademark, patent, trade secret, privacy, publicity or confidentiality obligations, or defames any person; (b) any misrepresentation made by you in connection with the Competition; (c) any non-compliance by you with these Rules or any applicable U.S. or foreign state or federal law; (d) claims brought by persons or entities other than the parties to these Rules arising from or related to your involvement with the Competition; and (e) your acceptance, possession, misuse or use of any Prize, or your participation in the Competition and any Competition-related activity.
> c. You hereby release Competition Entities from any liability associated with: (a) any malfunction or other problem with the Competition Website; (b) any error in the collection, processing, or retention of any Submission; or (c) any typographical or other error in the printing, offering or announcement of any Prize or winners.
>
> **15. INTERNET**
> a. Competition Entities are not responsible for any malfunction of the Competition Website or any late, lost, damaged, misdirected, incomplete, illegible, undeliverable, or destroyed Submissions or entry materials due to system errors, failed, incomplete or garbled computer or other telecommunication transmission malfunctions, hardware or software failures of any kind, lost or unavailable network connections, typographical or system/human errors and failures, technical malfunction(s) of any telephone network or lines, cable connections, satellite transmissions, servers or providers, or computer equipment, traffic congestion on the Internet or at the Competition Website, or any combination thereof, which may limit a Participant's ability to participate.
>
> **16. RIGHT TO CANCEL, MODIFY OR DISQUALIFY**
> a. If for any reason the Competition is not capable of running as planned, including infection by computer virus, bugs, tampering, unauthorized intervention, fraud, technical failures, or any other causes which corrupt or affect the administration, security, fairness, integrity, or proper conduct of the Competition, Competition Sponsor reserves the right to cancel, terminate, modify or suspend the Competition. Competition Sponsor further reserves the right to disqualify any Participant who tampers with the submission process or any other part of the Competition or Competition Website. Any attempt by a Participant to deliberately damage any website, including the Competition Website, or undermine the legitimate operation of the Competition is a violation of criminal and civil laws. Should such an attempt be made, Competition Sponsor and Kaggle each reserves the right to seek damages from any such Participant to the fullest extent of the applicable law.
>
> **17. NOT AN OFFER OR CONTRACT OF EMPLOYMENT**
> a. Under no circumstances will the entry of a Submission, the awarding of a Prize, or anything in these Rules be construed as an offer or contract of employment with Competition Sponsor or any of the Competition Entities. You acknowledge that you have submitted your Submission voluntarily and not in confidence or in trust. You acknowledge that no confidential, fiduciary, agency, employment or other similar relationship is created between you and Competition Sponsor or any of the Competition Entities by your acceptance of these Rules or your entry of your Submission.

> **18. DEFINITIONS**
> a. "Competition Data" are the data or datasets available from the Competition Website for the purpose of use in the Competition, including any prototype or executable code provided on the Competition Website. The Competition Data will contain private and public test sets. Which data belongs to which set will not be made available to Participants.
> b. An "Entry" is when a Participant has joined, signed up, or accepted the rules of a competition. Entry is required to make a Submission to a competition.
> c. A "Final Submission" is the Submission selected by the user, or automatically selected by Kaggle in the event not selected by the user, that is/are used for final placement on the competition leaderboard.
> d. A "Participant" or "Participant User" is an individual who participates in a competition by entering the competition and making a Submission.
> e. The "Private Leaderboard" is a ranked display of Participants' Submission scores against the private test set. The Private Leaderboard determines the final standing in the competition.
> f. The "Public Leaderboard" is a ranked display of Participants' Submission scores against a representative sample of the test data. This leaderboard is visible throughout the competition.
> g. A "Sponsor" is responsible for hosting the competition, which includes but is not limited to providing the data for the competition, determining winners, and enforcing competition rules.
> h. A "Submission" is anything provided by the Participant to the Sponsor to be evaluated for competition purposes and determine leaderboard position. A Submission may be made as a model, notebook, prediction file, or other format as determined by the Sponsor.
> i. A "Team" is one or more Participants participating together in a Kaggle competition, by officially merging together as a Team within the competition platform.
>
> *(Note: At the bottom of the Rules tab, Kaggle displays: "Click 'Join Competition' to view and accept the competition's terms and conditions.")*

## 5.4 RULES — SUMMARY

**Competition-Specific (Section 2):** Max team size 5; mergers allowed by team leader subject to limits and the merger deadline; pre-merger individual submissions are unsubmitted. Hackathon = exactly ONE submission per team. No competition data is provided. Winners license their winning submission + source code under CC-BY 4.0 (third-party commercial software and incompatibly-licensed data/models are exempt). Winners may need to provide a full reproducible methodology + code repo link. External data/tools allowed if publicly/equally accessible at no/minimal cost or meeting the "Reasonableness Standard" (e.g., a small Gemini Advanced subscription is OK; a proprietary dataset costing more than the prize is not). AMLT tools allowed with proper licensing. Competition Entity employees/contractors may enter but can't win prizes. Governing law: California (Santa Clara County courts).

**Foundational (General) Rules (Section 3):** Must be a registered Kaggle account holder, 18+/age of majority, not in embargoed regions (Crimea/DNR/LNR/Cuba/Iran/North Korea) or under U.S. sanctions. One account per person; no multi-account entries. Only one team per person; each member needs a separate account and must confirm membership. No private code sharing outside your team — public sharing must be on the competition forum/notebooks and is deemed OSI-open-source licensed. Open-source code used must be under an OSI-approved, commercial-use-permitting license. Winners notified by email; must respond within 1 week; prize docs returned within 2 weeks; prizes awarded ~30 days after docs. Winners are solely responsible for taxes (U.S. residents get a 1099). Standard warranty/indemnity/release, publicity, privacy (PII shared with Google as independent controller, possibly cross-border), internet-liability, and right-to-cancel/modify/disqualify clauses apply. Not an offer of employment.

## 5.5 RULES — KEY INSIGHTS / WATCH-OUTS

- **ONE submission per team — period.** Coordinate tightly before submitting; you don't get a second shot.
- **Team mergers wipe prior individual submissions** and must finish before the merger/competition deadline.
- **Winning = open-sourcing under CC-BY 4.0.** Don't build winning work on code/data you can't license this way (third-party commercial software and incompatibly-licensed pretrained models/data are carved out, but must be identified).
- **Public code sharing is irreversible licensing.** Anything you post to the competition forum/notebooks is deemed open-sourced; only share on Kaggle (not privately/off-platform) and never share privately outside your team.
- **Cost/accessibility ("Reasonableness Standard"):** keep tools cheap and broadly accessible. Gemini Advanced-level subscriptions are explicitly fine.
- **Eligibility gates:** 18+, allowed region, single Kaggle account. Google/Kaggle staff can participate but cannot win.
- **Winner obligations are real work:** reproducible methodology, repo link, signed eligibility/license/tax forms within tight windows (1 week to respond, 2 weeks for docs).
- **Privacy:** your PII (name, address, phone, email) is shared with Google and may be transferred cross-border.
- **Timeline can change** and you're responsible for your own time zone; deadline is July 6, 2026, 11:59 PM PT.
- Foundational Rules **override** competition-specific rules in any conflict.

---

# 6. CROSS-CUTTING KEY INSIGHTS & STRATEGY

**Scoring math (100 pts):** Implementation 70 (Technical 50 + Documentation 20) vs. Pitch 30 (Core Concept 10 + Video 10 + Writeup 10). Optimize for a strong, well-commented, genuinely agentic codebase and an excellent README first; the pitch/video/writeup are the remaining 30%.

**Mandatory deliverables (all required):** (1) Kaggle Writeup <=2,500 words with title/subtitle/analysis and a selected Track; (2) Media Gallery with a required cover image; (3) public YouTube video <=5 min; (4) public project link (live demo OR public GitHub repo with setup instructions). Must click Submit (drafts don't count).

**Course concepts to demonstrate (need >=3):** ADK agent/multi-agent (Code), MCP Server (Code), Antigravity (Video), Security features (Code or Video), Deployability (Video), Agent skills / Agents CLI (Code or Video). Pick at least three and place each demonstration in its required medium.

**Track selection guidance:** Good = humanity/social impact; Business = enterprise problem with explicit cost/revenue stakes; Concierge = personal/family/social with strong privacy/security; Freestyle = novel ideas still showing agent best practices. Judges can move winners between tracks.

**Hard constraints / compliance:** ONE submission per team (max 5 members); no API keys/passwords in code; winning work open-sourced under CC-BY 4.0; public code sharing only on Kaggle and is deemed open-source; eligibility (18+, allowed region, single account); deadline July 6, 2026, 11:59 PM PT.

**Environment notes:** No competition data and no starter notebook/code are provided. Discussion forum is currently empty — monitor it for host clarifications. Competitor Writeups are hidden until the hackathon closes.

# 7. BUILD CHECKLIST

- [ ] Choose a track and define a clear, meaningful real-world problem (with a "wow" angle).
- [ ] Design an architecture where the agent (ideally multi-agent via ADK) is central to the solution.
- [ ] Demonstrate >=3 required course concepts, each in its required location (Code vs. Video).
- [ ] Implement clean code with comments on implementation, design, and behaviors. Clever/meaningful tool use.
- [ ] Ensure NO API keys or passwords anywhere in the code.
- [ ] Write a thorough README.md (problem, solution, architecture, setup instructions, diagrams/images). [20 pts]
- [ ] (Optional) Deploy; if so, include reproduction documentation.
- [ ] Record a <=5 min YouTube video: Problem, Why Agents, Architecture (with images), Demo, The Build.
- [ ] Create a required cover image and populate the Media Gallery.
- [ ] Provide a public project link (live demo or public repo) with no login/paywall.
- [ ] Write the Kaggle Writeup (<=2,500 words): title, subtitle, problem, solution, architecture, journey; select Track.
- [ ] Attach Writeup + Media Gallery + Video + Project Link; confirm everything is public-safe (private resources become public after deadline).
- [ ] Finalize team (<=5) and any merger before deadlines; remember ONE submission per team.
- [ ] Click SUBMIT before July 6, 2026, 11:59 PM PT (mind your time zone).

---

*End of comprehensive reference. Verbatim quotes are reproduced from the Kaggle competition pages for accuracy; summaries, insights, and the checklist are added analysis.*
