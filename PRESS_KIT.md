# CodeOrbit AI — Launch Press Kit

This document provides official media assets, copywriting descriptions, FAQs, and brand statements for the public launch of **CodeOrbit AI**.

---

## 📢 Product Summary

* **One-Line Description**: "The security-hardened, multi-agent AI software engineer."
* **Elevator Pitch**: "CodeOrbit AI is an autonomous, repository-aware engineering platform that delegates software tasks to coordinated swarms of specialized agents. By executing code modifications inside isolated sandboxes, validating outputs via AST parsers, and self-healing test failures before commits, CodeOrbit AI guarantees repository integrity and safe developer operations."

---

## 📝 Product Description

### Long Description
Traditional AI coding tools function as basic script builders or autocomplete widgets, lacking deep repository awareness, and executing commands directly on host machines with zero sandboxing. 

**CodeOrbit AI** is built for production environments. It acts as an autonomous engineering swarm:
1. **Planning**: Decomposes developer instructions into topological Directed Acyclic Graphs (DAG) validated to prevent cycle loops.
2. **Execution**: Spawns isolated Git worktree sessions and writes modifications inside ephemeral Docker container sandboxes or local AST-restricted environments.
3. **Consensus & Peer-Review**: Runs automated code reviews (Developer, Reviewer, Architect, and Tech Lead agents) before approving changes.
4. **Self-Healing**: Intercepts unit test and compiler logs, feeding stack traces back into the developer context to self-repair bugs before commits.
5. **Memory**: Queries vector-based doświadczenie ledgers to compact past task fixes.

---

## 🌟 Key Capabilities & Features

* **Dual-Shield Sandbox Confinement**: Full absolute path component resolving boundaries and static AST check imports filters.
* **Topological DAG Scheduler**: Step routing validated via cycle-detection algorithms.
* **Closed-Loop Self-Repair**: Capped 3-iteration self-healing loop parsing pytest stack traces.
* **High-Throughput WAL Queue**: Multi-threaded sqlite transactional claims peaking at 850+ task operations/second.
* **Mission Control Web Console**: Real-time Next.js 15 task logs and worker heartbeat telemetry charts.

---

## 🏗️ Founder Story & Vision

* **Founder Story (Placeholder)**: "CodeOrbit AI was founded to bridge the gap between simple AI text generators and reliable, sandboxed, transactional software engineering agents that professional teams can safely trust with their main code repositories."
* **Our Vision**: "To construct a safe, resilient, and collaborative AI developer swarm that operates as an extension of modern engineering teams."
* **Our Mission**: "Provide developers with a world-class, security-hardened autonomous workspace that eliminates host machine pollution and manual code fixing."

---

## ❓ Frequently Asked Questions (FAQs)

#### How does CodeOrbit AI differ from basic code copilots?
Copilots operate as linear autocomplete tools inside an IDE. CodeOrbit AI acts as a stateful, autonomous swarm, executing plans, validating test suites, and auditing code changes in sandboxes before human review.

#### Is the platform safe to run locally?
Yes. CodeOrbit AI enforces dual boundaries—a static AST parser that blocks dangerous modules (`sys`, `os`, reflection subclasses) and Docker container limits (512MB RAM, 1 CPU Core), preventing host system compromises.

#### Can we use other AI models?
Yes. The model abstraction layer is designed with decoupled interfaces. While optimized for Google Gemini models, adapters for other providers can be configured.

---

## 🖼️ Media & Branding Resources

* **Product Brand Logo**: [docs/assets/logo.jpg](file:///E:/multi-agent-system/docs/assets/logo.jpg)  
* **GitHub Widescreen Banner**: [docs/assets/social-preview.png](file:///E:/multi-agent-system/docs/assets/social-preview.png)  
* **Interface Screenshots**: Located under [docs/screenshots/](file:///E:/multi-agent-system/docs/screenshots/)  
* **Architecture Flowcharts**: Located under [docs/architecture/](file:///E:/multi-agent-system/docs/architecture/)  
