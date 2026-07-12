# Support Policy

Thank you for using **CodeOrbit AI**! We are committed to providing helpful resources and support channels for our community of developers during the public beta.

---

## 🧭 Support Channels

### 1. GitHub Issues
For bugs, feature requests, or installation issues:
* **Where**: Open an issue on our [GitHub Issues](https://github.com/faizanshah7424/multi-agent-system/issues) page.
* **Templates**: Please use the appropriate template (Bug Report, Feature Request, or Question) to help us diagnose your issue quickly.
* **SLA**: Community maintenance team reviews and responds to issues within **3 business days**.

### 2. GitHub Discussions
For architectural design questions, usage guidance, or showcasing your custom agent configurations:
* **Where**: Visit our [GitHub Discussions](https://github.com/faizanshah7424/multi-agent-system/discussions) board.
* **Guidelines**: Feel free to share tips, ask questions, or request feedback on custom plugins/skills.

### 3. Security Vulnerabilities
If you believe you have found a security vulnerability:
* **Contact**: Send a direct email to **security@codeorbit.ai** (refer to our [Security Policy](SECURITY.md)).
* **Do Not**: Open a public issue. We resolve security vulnerabilities privately to prevent premature disclosure.

### 4. Enterprise & Commercial Support
For commercial deployments, SLA-backed integration support, or custom agency requirements:
* **Email**: Reach out to us at **support@codeorbit.ai**.
* **Offerings**: Custom sandbox configuration audits, high-throughput WAL optimization, and private swarm setups.

---

## 🩺 Self-Service Troubleshooting

Before opening a support ticket, we recommend running our automated diagnostics tools to check your local environment configurations:

1. **Verify Prerequisite Tooling**:
   ```bash
   python codeorbit.py install
   ```
2. **Run Diagnostics & Checks**:
   ```bash
   python codeorbit.py doctor
   ```
3. **Inspect Local System Health**:
   ```bash
   python codeorbit.py health
   ```
4. **Examine Container Sandbox Status**:
   ```bash
   python codeorbit.py sandbox
   ```
5. **View Active Logging Traces**:
   ```bash
   python codeorbit.py logs --lines 50
   ```

These tools are built to identify configuration errors, database lock issues, network access blockers, and missing tools instantly.
