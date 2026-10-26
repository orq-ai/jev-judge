# docs-agent annotation sheet

Fill `labels.jsonl`: `grounded` true/false, `abstain_ok` true/false, `quality` 0-4, free-text `note`.
Judge against the retrieved pages listed under each search, not against the live docs.

## q01 [how-to] How do I migrate my existing OpenAI SDK traffic to the Orq AI Gateway?

trace `13b5b55856fd33e6616f971a28c22e99`, $0.0007

**search** `migrate existing OpenAI SDK traffic to Orq AI Gateway`: [Migrate from OpenAI, OpenRouter, LiteLLM](https://docs.orq.ai/docs/ai-gateway/get-started/migrate), [OpenAI-compatible API](https://docs.orq.ai/docs/ai-gateway/features/openai-compatible-api), [Next steps](https://docs.orq.ai/docs/ai-gateway/get-started/introduction), [OpenAI](https://docs.orq.ai/docs/ai-studio/integrations/providers/openai)

**answer**

The Orq AI Gateway is OpenAI-compatible, so you can keep your existing OpenAI SDK and application logic.

Update these three values:

1. **Base URL:** `https://my.orq.ai/v3/router`
2. **API key:** use an Orq.ai API key as the Bearer token
3. **Model name:** change it to the model name supported by the Orq AI Gateway

Your request bodies, response bodies, streaming, and— for most models—tool calling remain unchanged.

Required headers:

```http
Authorization: Bearer $ORQ_API_KEY
Content-Type: application/json
```

For advanced routing, you can optionally add:

```http
X-Orq-Provider: openai
X-Orq-Virtual-Key: your-virtual-key-name
```

If you are using the OpenAI SDK already, no SDK migration is required. The documentation also provides setup guidance for the Node.js/TypeScript and Python SDKs.

- [Migrate from OpenAI, OpenRouter, LiteLLM](https://docs.orq.ai/docs/ai-gateway/get-started/migrate)
- [OpenAI-compatible API](https://docs.orq.ai/docs/ai-gateway/features/openai-compatible-api)
- [OpenAI integration](https://docs.orq.ai/docs/ai-studio/integrations/providers/openai)

---

## q02 [comparison] What is the difference between an API key and a management key?

trace `f28e1661526253ac13641e3cdd4c8c40`, $0.0020

**search** `difference between an API key and a management key`: no pages parsed: `Error executing HTTP tool: Post "https://my.orq.ai/v2/mcp": context deadline exceeded`

**search** `Orq.ai API keys management keys authentication`: no pages parsed: `Error executing HTTP tool: Post "https://my.orq.ai/v2/mcp": context deadline exceeded`

**search** `Orq deployments API key management key permissions`: [Restricted permission resources](https://docs.orq.ai/docs/ai-gateway/configuration/api-keys), [Unified API key management](https://docs.orq.ai/docs/changelog/release-4-10), [Use cases](https://docs.orq.ai/docs/ai-studio/organization/management-keys), [List Capabilities](https://docs.orq.ai/reference/sdk/managementkeys)

**answer**

The difference is primarily **scope and purpose**:

- **API key:** Used to access Orq.ai API resources within a **single project**. It can be configured with:
  - **All** — read/write access to all API resources
  - **Read-only**
  - **Restricted** — per-resource read, write, or no access  
  [API key permissions](https://docs.orq.ai/docs/ai-gateway/configuration/api-keys)

- **Management key:** Used for **workspace-administration capabilities**, with separately assignable read/write permissions for workspace-admin domains. Typical uses include automating workspace provisioning, delegating API-key rotation, or managing budgets without granting full admin access.  
  [Management keys](https://docs.orq.ai/docs/ai-studio/organization/management-keys) · [Management-key capabilities](https://docs.orq.ai/reference/sdk/managementkeys)

In short: use an **API key** for project-level API operations; use a **management key** for controlled workspace administration.

---

## q03 [yes-no] Can I set a spending budget on a single model rather than the whole workspace?

trace `58f2a2e9a7c14351713e7cfc8a03c8c3`, $0.0008

**search** `set spending budget on a single model rather than the whole workspace`: [Budgets](https://docs.orq.ai/docs/ai-gateway/budgets), [Enterprise Baseline](https://docs.orq.ai/reference/terraform/enterprise-baseline), [Budget control](https://docs.orq.ai/docs/ai-studio/observability/identities), [Step 4: Run the benchmark](https://docs.orq.ai/docs/ai-studio/cookbooks/evaluation-safety/model-arena)

**answer**

Yes. Orq.ai budgets can be scoped to a **Model**, so you can limit spending on one model instead of applying the limit to the entire workspace.

Go to **Settings → Organization → Budgets**, create a budget, and set its scope to **Model**. You can configure cost or token limits, reset periods, and an optional expiration date. Requests matching the scope are blocked when the limit is reached.

Only workspace admins can manage budgets.  
[Budgets documentation](https://docs.orq.ai/docs/ai-gateway/budgets)

---

## q04 [how-to] How do I set up fallback models so a request retries on another provider when the first one fails?

trace `e5da89ab1fbab08f294e871e011cd49f`, $0.0027

**search** `How do I set up fallback models so a request retries on another provider when the first one fails?`: [Round Robin routing](https://docs.orq.ai/docs/ai-gateway/features/load-balancing), [If a provider fails or rate-limits, can traffic fail over?](https://docs.orq.ai/docs/ai-gateway/model-faq), [Fallbacks and retries in the AI Gateway](https://docs.orq.ai/docs/ai-gateway/features/retries), [Primary Model, Retries, and Fallback](https://docs.orq.ai/docs/ai-studio/ai-engineering/deployments)

**answer**

Set this up in your **Deployment’s Variant** configuration:

1. Configure the **Primary Model**.
2. Set the **Retries** count to the number of times Orq.ai should retry that model.
3. Add a **Fallback Model** below the primary model.
4. For additional backups, click **Add extra fallback**. Fallbacks run in the order configured.

The flow is:

- Orq.ai retries the primary model when it returns `408`, `429`, `500`, `502`, `503`, `504`, or `529`.
- After retries are exhausted—or immediately if retries are set to `0`—the request moves to the fallback model.
- If the fallback also fails, the error is returned to your application.

Retries apply to the same provider/model; fallbacks route the request to another configured model, including one from another provider.

See **[Primary Model, Retries, and Fallback](https://docs.orq.ai/docs/ai-studio/ai-engineering/deployments)** and **[Fallbacks and retries in the AI Gateway](https://docs.orq.ai/docs/ai-gateway/features/retries)**.

---

## q05 [comparison] What is the difference between a managed agent and a deployment?

trace `f1f248d0a5c5a437264dd27acb4adb3f`, $0.0085

**search** `difference between a managed agent and a deployment`: [Versioning](https://docs.orq.ai/docs/ai-studio/ai-engineering/deployments), [Configuring a Deployment](https://docs.orq.ai/docs/ai-studio/cookbooks/common-architecture/simple-deployment), [Generate from a description](https://docs.orq.ai/docs/ai-studio/optimize/agent-simulations), [Deployments deprecation](https://docs.orq.ai/docs/changelog/release-4-8)

**search** `Orq.ai Managed Agents build agents deployment architecture`: [Build an AI agent with Orq.ai](https://docs.orq.ai/docs/ai-studio/ai-engineering/quickstart), [Build Agents](https://docs.orq.ai/docs/ai-studio/ai-engineering/build-agents), [What is Agents API?](https://docs.orq.ai/docs/ai-studio/cookbooks/chatbots/agents-API), [Create a Deployment](https://docs.orq.ai/docs/ai-studio/ai-engineering/deployments)

**answer**

In Orq.ai, **Agents** and **Deployments** are different resource types found under the **Managed Agents** area:

| | Managed agent (Agent) | Deployment |
|---|---|---|
| **Purpose** | An autonomous entity that can reason, use tools, maintain context, and collaborate with other agents. | A production configuration for an AI application, exposed through Orq.ai’s AI Gateway. |
| **Configuration** | Instructions, model, tools, context, evaluators, constraints, memory, and knowledge bases. | Model, system prompt, fallbacks, variables, knowledge base, tools, caching, guardrails, and routing rules. |
| **Execution** | Invoked as `agent/<key>` through the unified Responses API. | Invoked through its deployment API/SDK interface. |
| **Lifecycle** | Publish the agent configuration and execute it directly. | Uses variants, versioning, traffic routing, rollback, monitoring, and analytics. |

In short: **an Agent is the behavior/execution unit**, while **a Deployment is a versioned, routable production configuration** for serving an AI use case.

The documentation also says existing Deployments continue to work, but for new builds Orq.ai recommends **Agents without tools** or **Prompts with direct calls to the AI Router**.

Sources:  
- [Build Agents](https://docs.orq.ai/docs/ai-studio/ai-engineering/build-agents)  
- [Create a Deployment](https://docs.orq.ai/docs/ai-studio/ai-engineering/deployments)  
- [Deployments deprecation](https://docs.orq.ai/docs/changelog/release-4-8)

---

## q06 [how-to] How do I export my traces to my own data warehouse?

trace `914a7c0e33ac49c2b18dfb52f5f06c21`, $0.0103

**search** `How do I export my traces to my own data warehouse?`: no pages parsed: `Error executing HTTP tool: Post "https://my.orq.ai/v2/mcp": context deadline exceeded`

**search** `Orq.ai traces export telemetry data warehouse`: [Quick Start](https://docs.orq.ai/docs/ai-studio/observability/quickstart), [OpenTelemetry Observability](https://docs.orq.ai/docs/ai-studio/integrations/automation/n8n), [Capture Copilot usage with OpenTelemetry](https://docs.orq.ai/docs/ai-studio/integrations/code-assistants/github-copilot), [Troubleshooting](https://docs.orq.ai/docs/ai-studio/integrations/frameworks/pydantic-ai)

**search** `Orq.ai export traces to external data warehouse telemetry export destination`: no pages parsed: `Error executing HTTP tool: Post "https://my.orq.ai/v2/mcp": context deadline exceeded`

**search** `Orq.ai observability traces API retrieve export warehouse OTLP collector`: [Configure the OTLP exporter](https://docs.orq.ai/docs/ai-studio/integrations/automation/n8n), [Quick Start](https://docs.orq.ai/docs/ai-studio/observability/quickstart), [August 18th, 2025](https://docs.orq.ai/docs/changelog/past-product-updates), [Orq span attributes reference](https://docs.orq.ai/docs/ai-studio/observability/span-attributes)

**answer**

The documentation does **not** describe a direct connector for exporting Orq.ai traces to a data warehouse.

It does document two related options:

- **OpenTelemetry ingestion:** Orq.ai accepts traces at `https://my.orq.ai/v2/otel`, authenticated with `Authorization: Bearer <ORQ_API_KEY>`. This sends telemetry **to Orq.ai**, not from Orq.ai to your warehouse. See [Quick Start](https://docs.orq.ai/docs/ai-studio/observability/quickstart).
- **Trace/webhook data:** Orq span attributes appear in **trace exports** and **LLM webhook payloads**. See [Orq span attributes reference](https://docs.orq.ai/docs/ai-studio/observability/span-attributes) and [Webhooks](https://docs.orq.ai/docs/ai-studio/organization/webhooks).

The excerpts found do not specify the export format, API endpoint, scheduling method, or warehouse integrations.

---

## q07 [what-is] Which chunking strategies are available for a knowledge base and when should I pick each?

trace `13e0f983af55e695dbd6921214ae4edb`, $0.0012

**search** `knowledge base chunking strategies available when to choose each`: [Chunk Strategy](https://docs.orq.ai/docs/ai-studio/ai-engineering/knowledge-bases), [Chunking](https://docs.orq.ai/docs/ai-studio/ai-engineering/chunking), [Prerequisites](https://docs.orq.ai/docs/ai-studio/cookbooks/common-architecture/simple-rag), [Step 6: Set up the Knowledge Base](https://docs.orq.ai/docs/ai-studio/cookbooks/integrations-tooling/integrate-langgraph-with-orq)

**answer**

Orq.ai provides seven chunking strategies:

| Strategy | Pick it when… |
|---|---|
| **Recursive** | You want the best general-purpose default. It preserves document structure by splitting through paragraphs, lines, sentences, and words. It is the default for new uploads. |
| **Token** | You need predictable token-sized chunks—for example, to fit LLM context windows or keep embedding input sizes consistent. Optional overlap carries context across boundaries, but chunks may split sentences. |
| **Sentence** | Readability and semantic coherence matter. It groups complete sentences while respecting the token limit, so sentences are not cut in half. |
| **Semantic** | Retrieval should follow topic or meaning boundaries. It uses embeddings to keep related passages together. It requires paid embedding calls during preview and ingestion. |
| **Late** | You want recursive boundaries but embeddings that retain the document’s wider context. The document is embedded before recursive splitting; this also incurs paid embedding calls. |
| **Agentic** | Documents have irregular or complex structure and need model-selected boundaries. It is the most expensive and slowest option because it makes model calls. |
| **Fast** | You are processing large files—especially over 1 MB—or need high-throughput, low-memory ingestion. It splits by delimiters at the byte level, so it is not ideal when precise token counts or semantic boundaries matter. |

A practical selection guide from the documentation:

- **General purpose:** Recursive  
- **RAG with precise token sizing:** Token or Recursive  
- **Semantic search:** Semantic  
- **Complex document understanding:** Agentic  
- **Large files / high throughput:** Fast  

In **AI Studio**, all seven are documented as available. With the **Chunking API**, set `strategy` to `token`, `sentence`, `recursive`, `late`, `semantic`, `agentic`, or `fast`. The older `default` and `advanced` configurations are deprecated.

Sources: [Knowledge Bases — Chunk Strategy](https://docs.orq.ai/docs/ai-studio/ai-engineering/knowledge-bases) · [Chunking](https://docs.orq.ai/docs/ai-studio/ai-engineering/chunking)

---

## q08 [yes-no] Does Orq support SSO with Okta, and how do I enable it?

trace `de0cec90a9b4156f491f31f2a4d61e13`, $0.0051

**search** `SSO with Okta enable Orq`: [Okta](https://docs.orq.ai/docs/ai-studio/organization/sso), [SSO (Enterprise)](https://docs.orq.ai/docs/changelog/release-4-3), [Members and teams](https://docs.orq.ai/docs/ai-studio/organization/members-teams), [Authentication](https://docs.orq.ai/reference/cli)

**answer**

Yes. Orq supports SSO with Okta through **OIDC** (and the documentation also includes a SAML option). See the [Enterprise SSO documentation](https://docs.orq.ai/docs/ai-studio/organization/sso).

### Enable Okta SSO with OIDC

1. **Create an OIDC application in Okta**
   - Go to **Okta Admin Console → Applications → Applications**.
   - Select **Create App Integration**.
   - Choose **OIDC - OpenID Connect** and **Web Application**.
   - Ensure **Authorization Code** is selected.
   - Set the sign-in redirect URI to:
     ```text
     https://my.orq.ai/v2/auth/sso/oidc/callback
     ```
   - Optionally set the sign-out redirect URI to:
     ```text
     https://my.orq.ai
     ```

2. **Assign users or groups** to the Okta application under the **Assignments** tab. New Okta applications have no users assigned by default.

3. **Copy the Okta credentials**
   - From the app’s **General → Client Credentials** section, copy the **Client ID** and **Client secret**.
   - Use your Okta domain as the provider URL:
     ```text
     https://{yourOktaDomain}
     ```
     For example: `https://acme.okta.com`.

4. **Configure Orq**
   - Go to **AI Studio → Settings → Organization → Auth**.
   - Click **Add SSO Connection** and select **Okta**.
   - Select **OIDC**, then enter:
     - **Client ID**
     - **Client Secret**
     - **Provider URL**
     - Your organization’s email domain(s) in **Allowed domains**
   - Click **Activate**.

5. **Test the login** at:
   ```text
   https://my.orq.ai/{your-workspace-key}/login
   ```
   Users can select **Continue with SSO**.

---

## q09 [yes-no] Can I run the platform fully on-premise in my own Kubernetes cluster?

trace `9d0a6bbe28ba0c5737e1e799c559a9cd`, $0.0009

**search** `run the Orq.ai platform fully on-premise in my own Kubernetes cluster`: [On-premise deployment requirements](https://docs.orq.ai/docs/enterprise/on-prem-requirements), [On-Premise](https://docs.orq.ai/docs/enterprise/deployment-options), [Runtime contract](https://docs.orq.ai/docs/enterprise/agent-sandbox), [Sovereignty](https://docs.orq.ai/docs/enterprise/eu-regions-faq)

**answer**

Yes. Orq.ai can be deployed fully on-premise in your own Kubernetes cluster as a single Helm chart. All platform components run inside your environment, including on self-managed infrastructure. This is available with the **Enterprise Plan**.

Key requirements include:

- Kubernetes **1.28 or later**
- At least **3 worker nodes**, each with 4 vCPU and 16 GB RAM
- PostgreSQL 14–18
- MongoDB-compatible storage
- S3-compatible object storage

The deployment can operate fully air-gapped after container images are cached locally, provided configured model endpoints are reachable from within the environment.

[On-premise deployment requirements](https://docs.orq.ai/docs/enterprise/on-prem-requirements) · [On-Premise deployment options](https://docs.orq.ai/docs/enterprise/deployment-options)

---

## q10 [unanswerable] How do I train a custom fine-tuned model inside Orq and deploy it?

trace `3355c30fdc4f4de2274cce7b6fed8c2d`, $0.0060

**search** `train a custom fine-tuned model inside Orq and deploy it`: [Private OpenAI-Compatible Model](https://docs.orq.ai/docs/changelog/release-314), [Privacy and GDPR](https://docs.orq.ai/docs/enterprise/eu-regions-faq), [Model Configuration in Orq](https://docs.orq.ai/docs/ai-studio/cookbooks/integrations-tooling/chaining-deployments), [What Orq.ai adds](https://docs.orq.ai/docs/ai-gateway/get-started/migrate)

**search** `Orq private models self-hosted fine-tuned model configuration deploy OpenAI-compatible endpoint`: [Private OpenAI-Compatible Model](https://docs.orq.ai/docs/changelog/release-314), [OpenAI-compatible models](https://docs.orq.ai/docs/ai-studio/integrations/providers/open-ai-like), [Bring Your Own Model](https://docs.orq.ai/docs/ai-gateway/private-models), [Private Models Providers](https://docs.orq.ai/docs/ai-gateway/using-the-router)

**search** `Orq fine-tuning training custom model deployment fine-tuned model Deployments`: [Private OpenAI-Compatible Model](https://docs.orq.ai/docs/changelog/release-314), [Create a Deployment](https://docs.orq.ai/docs/ai-studio/ai-engineering/deployments), [Curated datasets for fine-tuning](https://docs.orq.ai/docs/ai-studio/optimize/datasets), [Step 8: Passing Extracted Data to the Next Deployment](https://docs.orq.ai/docs/ai-studio/cookbooks/integrations-tooling/chaining-deployments)

**answer**

The Orq documentation does **not describe running the fine-tuning/training job inside Orq**. It describes using Orq to prepare curated datasets as fine-tuning reference data, then connecting the resulting model as a private model.

### Recommended workflow

1. **Prepare your fine-tuning data in Orq**  
   Use reviewed input/output pairs to create a curated dataset for fine-tuning:  
   [Curated datasets for fine-tuning](https://docs.orq.ai/docs/ai-studio/optimize/datasets)

2. **Fine-tune and host the model externally**  
   Expose the fine-tuned model through an OpenAI-compatible endpoint. Orq supports custom, self-hosted, and fine-tuned models through this interface.

3. **Register the model in Orq**  
   In **AI Gateway → Models → + Model → OpenAI Compatible**:

   - Select the model type: **Chat Completion**, **Completion**, **Embedding**, or **Image**
   - Enter the endpoint’s **Base URL**
   - Enter the provider’s **Model ID**
   - Enter the **API Key**
   - Set the exposed **Model name**
   - Configure token limits, per-token costs, and capabilities

   Details: [Private Models Providers](https://docs.orq.ai/docs/ai-gateway/using-the-router)

4. **Use it in a Deployment**  
   Once configured, the private model is available throughout Orq and can be used in **Deployments**, **Experiments**, and the **AI Gateway**:  
   [OpenAI-compatible models](https://docs.orq.ai/docs/ai-studio/integrations/providers/open-ai-like)

5. **Invoke the Deployment**  
   Orq deployments can be called through the API/SDK, for example:

   ```python
   generation = client.deployments.invoke(
       key="your-deployment-key",
       context={"environments": "production"},
       inputs={"input": "your prompt"}
   )
   ```

   You can also pass or override model parameters with `extra_params`, such as `temperature`:  
   [Create a Deployment](https://docs.orq.ai/docs/ai-studio/ai-engineering/deployments)

Orq automatically traces requests and responses made through the AI Gateway, enabling observability, dataset creation from production traces, A/B testing, and evaluator workflows.

---

## q11 [unanswerable] Is there a native Salesforce integration so my agent can look up CRM records, and how do I turn it on?

trace `11f04693addd7e093e68b89901101102`, $0.0110

**search** `native Salesforce integration agent look up CRM records turn on`: [CRM Insert Tool Configuration](https://docs.orq.ai/docs/ai-studio/cookbooks/common-architecture/ai-agent), [Configuring Orq.ai Observability](https://docs.orq.ai/docs/ai-studio/integrations/frameworks/smolagents), [Coding agent integrations](https://docs.orq.ai/docs/ai-studio/integrations/code-assistants/overview), [Warp](https://docs.orq.ai/docs/ai-studio/integrations/code-assistants/warp)

**search** `Salesforce MCP tool agent deployment CRM connector integration`: [CRM Insert Tool Configuration](https://docs.orq.ai/docs/ai-studio/cookbooks/common-architecture/ai-agent), [Use Cases](https://docs.orq.ai/docs/ai-gateway/mcp-portal/mcp-servers), [MCP](https://docs.orq.ai/docs/ai-studio/ai-engineering/deployments), [MCP Clients](https://docs.orq.ai/docs/ai-studio/integrations/code-assistants/orq-mcp)

**search** `Salesforce app connector OAuth MCP server tools CRM records Orq.ai`: [OAuth](https://docs.orq.ai/docs/ai-studio/integrations/code-assistants/orq-mcp), [OIDC](https://docs.orq.ai/docs/ai-studio/organization/sso), [MCP Servers](https://docs.orq.ai/docs/ai-gateway/mcp-portal/mcp-servers), [OAuth](https://docs.orq.ai/docs/ai-gateway/mcp-portal/mcp-gateways)

**answer**

The documentation does **not confirm a native Salesforce integration** or provide Salesforce-specific setup instructions.

A documented alternative is to connect Salesforce through an **upstream MCP server**:

1. Open **AI Gateway → MCP Portal**.
2. Go to **MCP Servers**.
3. Click **Create MCP Server**.
4. Connect the Salesforce MCP server. Once connected, its tools are discovered automatically and become available to **Agents** and **Gateways**.

See [MCP Servers](https://docs.orq.ai/docs/ai-gateway/mcp-portal/mcp-servers).

The docs also state that third-party SaaS tools can be connected through MCP without writing custom integrations. However, they do not document which Salesforce MCP server to use, its authentication requirements, or the exact record-lookup tools.

---

## q05v1 [comparison] What is the difference between a managed agent and a deployment?

trace `42118553de7fd99348cc47cc689f3090`, $0.0029

**search** `managed agent vs deployment difference`: [Create a Deployment](https://docs.orq.ai/docs/ai-studio/ai-engineering/deployments), [Deployments](https://docs.orq.ai/docs/ai-studio/integrations/code-assistants/vs-code), [   Common Architectures](https://docs.orq.ai/docs/ai-studio/cookbooks/cookbooks), [Configuring a Deployment](https://docs.orq.ai/docs/ai-studio/cookbooks/common-architecture/simple-deployment)

**answer**

In Orq.ai, **Managed Agents** is the section where you manage agent-related entities, including deployments. A **deployment** is a specific configurable entity within that section.

- **Managed agent:** The broader managed-agent capability/area, including agents that can have custom instructions, tools, evaluators, guardrails, and can be invoked.
- **Deployment:** A named, callable configuration containing a deployment key, model, messages, and variant settings. It is created from **Managed Agents → Deployments** and can be used as an AI Gateway integration.

The documentation presents deployments as a simpler LLM configuration, while agents support autonomous behavior such as tool calling, memory, and multi-agent coordination.

Sources: [Create a Deployment](https://docs.orq.ai/docs/ai-studio/ai-engineering/deployments), [VS Code/MCP commands](https://docs.orq.ai/docs/ai-studio/integrations/code-assistants/vs-code), [Common Architectures](https://docs.orq.ai/docs/ai-studio/cookbooks/cookbooks)

---

## h01 [how-to] How do I migrate my existing OpenAI SDK traffic to the Orq AI Gateway?

trace `13b5b55856fd33e6616f971a28c22e99`, $0.0007

**search** `migrate existing OpenAI SDK traffic to Orq AI Gateway`: [Migrate from OpenAI, OpenRouter, LiteLLM](https://docs.orq.ai/docs/ai-gateway/get-started/migrate), [OpenAI-compatible API](https://docs.orq.ai/docs/ai-gateway/features/openai-compatible-api), [Next steps](https://docs.orq.ai/docs/ai-gateway/get-started/introduction), [OpenAI](https://docs.orq.ai/docs/ai-studio/integrations/providers/openai)

**answer**

The Orq AI Gateway is OpenAI-compatible, so you can keep your existing OpenAI SDK and application logic.

Update these three values:

1. **Base URL:** `https://my.orq.ai/v3/router`
2. **API key:** use an Orq.ai API key as the Bearer token
3. **Model name:** change it to the model name supported by the Orq AI Gateway

Your request bodies, response bodies, streaming, and— for most models—tool calling remain unchanged.

Required headers:

```http
Authorization: Bearer $ORQ_API_KEY
Content-Type: application/json
```

For advanced routing, you can optionally add:

```http
X-Orq-Provider: openai
X-Orq-Virtual-Key: your-virtual-key-name
```

Before sending traffic, enable **Legacy OpenAI passthrough** under **Settings → Gateway → Compatibility**; without it the router rejects OpenAI-format requests with a `400 incompatible_payload` error.

If you are using the OpenAI SDK already, no SDK migration is required. The documentation also provides setup guidance for the Node.js/TypeScript and Python SDKs.

- [Migrate from OpenAI, OpenRouter, LiteLLM](https://docs.orq.ai/docs/ai-gateway/get-started/migrate)
- [OpenAI-compatible API](https://docs.orq.ai/docs/ai-gateway/features/openai-compatible-api)
- [OpenAI integration](https://docs.orq.ai/docs/ai-studio/integrations/providers/openai)

---

## h02 [comparison] What is the difference between an API key and a management key?

trace `f28e1661526253ac13641e3cdd4c8c40`, $0.0020

**search** `difference between an API key and a management key`: no pages parsed: `Error executing HTTP tool: Post "https://my.orq.ai/v2/mcp": context deadline exceeded`

**search** `Orq.ai API keys management keys authentication`: no pages parsed: `Error executing HTTP tool: Post "https://my.orq.ai/v2/mcp": context deadline exceeded`

**search** `Orq deployments API key management key permissions`: [Restricted permission resources](https://docs.orq.ai/docs/ai-gateway/configuration/api-keys), [Unified API key management](https://docs.orq.ai/docs/changelog/release-4-10), [Use cases](https://docs.orq.ai/docs/ai-studio/organization/management-keys), [List Capabilities](https://docs.orq.ai/reference/sdk/managementkeys)

**answer**

The difference is primarily **scope and purpose**:

- **API key:** Used for **workspace-administration capabilities**, with separately assignable read/write permissions for workspace-admin domains. Typical uses include automating workspace provisioning, delegating key rotation, or managing budgets without granting full admin access.  
  [API key permissions](https://docs.orq.ai/docs/ai-gateway/configuration/api-keys)

- **Management key:** Used to access Orq.ai API resources within a **single project**. It can be configured with:
  - **All** — read/write access to all API resources
  - **Read-only**
  - **Restricted** — per-resource read, write, or no access  
  [Management keys](https://docs.orq.ai/docs/ai-studio/organization/management-keys)

In short: use an **API key** for controlled workspace administration; use a **management key** for project-level API operations.

---

## h03 [yes-no] Can I set a spending budget on a single model rather than the whole workspace?

trace `58f2a2e9a7c14351713e7cfc8a03c8c3`, $0.0008

**search** `set spending budget on a single model rather than the whole workspace`: [Budgets](https://docs.orq.ai/docs/ai-gateway/budgets), [Enterprise Baseline](https://docs.orq.ai/reference/terraform/enterprise-baseline), [Budget control](https://docs.orq.ai/docs/ai-studio/observability/identities), [Step 4: Run the benchmark](https://docs.orq.ai/docs/ai-studio/cookbooks/evaluation-safety/model-arena)

**answer**

No. Orq.ai budgets apply to the **whole workspace**; a budget cannot be scoped to a single model.

Go to **Settings → Organization → Budgets** to create the workspace budget. You can configure cost or token limits, reset periods, and an optional expiration date. Requests are blocked when the limit is reached.

If you need a per-model cap, the documented workaround is to create a separate workspace per model and give each its own budget.

Only workspace admins can manage budgets.  
[Budgets documentation](https://docs.orq.ai/docs/ai-gateway/budgets)

---

## h04 [how-to] How do I set up fallback models so a request retries on another provider when the first one fails?

trace `e5da89ab1fbab08f294e871e011cd49f`, $0.0027

**search** `How do I set up fallback models so a request retries on another provider when the first one fails?`: [Round Robin routing](https://docs.orq.ai/docs/ai-gateway/features/load-balancing), [If a provider fails or rate-limits, can traffic fail over?](https://docs.orq.ai/docs/ai-gateway/model-faq), [Fallbacks and retries in the AI Gateway](https://docs.orq.ai/docs/ai-gateway/features/retries), [Primary Model, Retries, and Fallback](https://docs.orq.ai/docs/ai-studio/ai-engineering/deployments)

**answer**

Set this up in your **Deployment’s Variant** configuration:

1. Configure the **Primary Model**.
2. Set the **Retries** count to the number of times Orq.ai should retry that model (defaults to 5).
3. Add a **Fallback Model** below the primary model.
4. For additional backups, click **Add extra fallback**. Fallbacks are tried in random order so no single provider is favoured.

The flow is:

- Orq.ai retries the primary model when it returns `400`, `401`, `403`, or `404`.
- After retries are exhausted—or immediately if retries are set to `0`—the request moves to the fallback model.
- If the fallback also fails, the error is returned to your application.

Retries apply to the same provider/model; fallbacks route the request to another configured model, including one from another provider.

See **[Primary Model, Retries, and Fallback](https://docs.orq.ai/docs/ai-studio/ai-engineering/deployments)** and **[Fallbacks and retries in the AI Gateway](https://docs.orq.ai/docs/ai-gateway/features/retries)**.

---

## h05 [comparison] What is the difference between a managed agent and a deployment?

trace `f1f248d0a5c5a437264dd27acb4adb3f`, $0.0085

**search** `difference between a managed agent and a deployment`: [Versioning](https://docs.orq.ai/docs/ai-studio/ai-engineering/deployments), [Configuring a Deployment](https://docs.orq.ai/docs/ai-studio/cookbooks/common-architecture/simple-deployment), [Generate from a description](https://docs.orq.ai/docs/ai-studio/optimize/agent-simulations), [Deployments deprecation](https://docs.orq.ai/docs/changelog/release-4-8)

**search** `Orq.ai Managed Agents build agents deployment architecture`: [Build an AI agent with Orq.ai](https://docs.orq.ai/docs/ai-studio/ai-engineering/quickstart), [Build Agents](https://docs.orq.ai/docs/ai-studio/ai-engineering/build-agents), [What is Agents API?](https://docs.orq.ai/docs/ai-studio/cookbooks/chatbots/agents-API), [Create a Deployment](https://docs.orq.ai/docs/ai-studio/ai-engineering/deployments)

**answer**

In Orq.ai, **Agents** and **Deployments** are different resource types found under the **Managed Agents** area:

| | Managed agent (Agent) | Deployment |
|---|---|---|
| **Purpose** | An autonomous entity that can reason, use tools, maintain context, and collaborate with other agents. | A production configuration for an AI application, exposed through Orq.ai’s AI Gateway. |
| **Configuration** | Instructions, model, tools, context, evaluators, constraints, memory, and knowledge bases. | Model, system prompt, fallbacks, variables, knowledge base, tools, caching, guardrails, and routing rules. |
| **Execution** | Invoked as `agent/<key>` through the unified Responses API. | Invoked through its deployment API/SDK interface. |
| **Pricing** | Billed per agent step, on top of model tokens. | Billed on model tokens only. |
| **Lifecycle** | Publish the agent configuration and execute it directly. | Uses variants, versioning, traffic routing, rollback, monitoring, and analytics. |

In short: **an Agent is the behavior/execution unit**, while **a Deployment is a versioned, routable production configuration** for serving an AI use case.

The documentation also says existing Deployments continue to work until **31 December 2026**, after which they stop serving traffic; for new builds Orq.ai recommends **Agents without tools** or **Prompts with direct calls to the AI Router**.

Sources:  
- [Build Agents](https://docs.orq.ai/docs/ai-studio/ai-engineering/build-agents)  
- [Create a Deployment](https://docs.orq.ai/docs/ai-studio/ai-engineering/deployments)  
- [Deployments deprecation](https://docs.orq.ai/docs/changelog/release-4-8)

---

## h06 [what-is] Which chunking strategies are available for a knowledge base and when should I pick each?

trace `13e0f983af55e695dbd6921214ae4edb`, $0.0012

**search** `knowledge base chunking strategies available when to choose each`: [Chunk Strategy](https://docs.orq.ai/docs/ai-studio/ai-engineering/knowledge-bases), [Chunking](https://docs.orq.ai/docs/ai-studio/ai-engineering/chunking), [Prerequisites](https://docs.orq.ai/docs/ai-studio/cookbooks/common-architecture/simple-rag), [Step 6: Set up the Knowledge Base](https://docs.orq.ai/docs/ai-studio/cookbooks/integrations-tooling/integrate-langgraph-with-orq)

**answer**

Orq.ai knowledge bases offer several chunking strategies, including **Recursive** (the default for new uploads) and **Token**. Recursive is the general-purpose choice. The other strategies and when to use them are described on the [Knowledge Bases page](https://docs.orq.ai/docs/ai-studio/ai-engineering/knowledge-bases).

---

## h07 [yes-no] Does Orq support SSO with Okta, and how do I enable it?

trace `de0cec90a9b4156f491f31f2a4d61e13`, $0.0051

**search** `SSO with Okta enable Orq`: [Okta](https://docs.orq.ai/docs/ai-studio/organization/sso), [SSO (Enterprise)](https://docs.orq.ai/docs/changelog/release-4-3), [Members and teams](https://docs.orq.ai/docs/ai-studio/organization/members-teams), [Authentication](https://docs.orq.ai/reference/cli)

**answer**

Yes. Orq supports SSO with Okta through **OIDC** (and the documentation also includes a SAML option). See the [Enterprise SSO documentation](https://docs.orq.ai/docs/ai-studio/organization/sso).

### Enable Okta SSO with OIDC

1. **Create an OIDC application in Okta**
   - Go to **Okta Admin Console → Applications → Applications**.
   - Select **Create App Integration**.
   - Choose **OIDC - OpenID Connect** and **Web Application**.
   - Ensure **Authorization Code** is selected.
   - Set the sign-in redirect URI to:
     ```text
     https://my.orq.ai/auth/okta/return
     ```
   - Optionally set the sign-out redirect URI to:
     ```text
     https://my.orq.ai
     ```

2. **Assign users or groups** to the Okta application under the **Assignments** tab. New Okta applications have no users assigned by default.

3. **Copy the Okta credentials**
   - From the app’s **General → Client Credentials** section, copy the **Client ID** and **Client secret**.
   - Use your Okta domain as the provider URL:
     ```text
     https://{yourOktaDomain}
     ```
     For example: `https://acme.okta.com`.

4. **Configure Orq**
   - Go to **AI Studio → Settings → Security → Identity Providers**.
   - Click **Add SSO Connection** and select **Okta**.
   - Select **OIDC**, then enter:
     - **Client ID**
     - **Client Secret**
     - **Provider URL**
     - Your organization’s email domain(s) in **Allowed domains**
   - Click **Activate**.

   Once activated, **SCIM user provisioning is enabled automatically**, so Okta assignments create Orq users.

5. **Test the login** at:
   ```text
   https://my.orq.ai/{your-workspace-key}/login
   ```
   Users can select **Continue with SSO**.

---

## h08 [yes-no] Can I run the platform fully on-premise in my own Kubernetes cluster?

trace `9d0a6bbe28ba0c5737e1e799c559a9cd`, $0.0009

**search** `run the Orq.ai platform fully on-premise in my own Kubernetes cluster`: [On-premise deployment requirements](https://docs.orq.ai/docs/enterprise/on-prem-requirements), [On-Premise](https://docs.orq.ai/docs/enterprise/deployment-options), [Runtime contract](https://docs.orq.ai/docs/enterprise/agent-sandbox), [Sovereignty](https://docs.orq.ai/docs/enterprise/eu-regions-faq)

**answer**

The documentation I found does not cover running the platform on-premise in a customer-managed Kubernetes cluster.

The closest documented option is a **VPC deployment** on one of the supported clouds; contact Orq.ai support to discuss a dedicated environment.

[On-Premise deployment options](https://docs.orq.ai/docs/enterprise/deployment-options)

---

## h09 [unanswerable] How do I train a custom fine-tuned model inside Orq and deploy it?

trace `3355c30fdc4f4de2274cce7b6fed8c2d`, $0.0060

**search** `train a custom fine-tuned model inside Orq and deploy it`: [Private OpenAI-Compatible Model](https://docs.orq.ai/docs/changelog/release-314), [Privacy and GDPR](https://docs.orq.ai/docs/enterprise/eu-regions-faq), [Model Configuration in Orq](https://docs.orq.ai/docs/ai-studio/cookbooks/integrations-tooling/chaining-deployments), [What Orq.ai adds](https://docs.orq.ai/docs/ai-gateway/get-started/migrate)

**search** `Orq private models self-hosted fine-tuned model configuration deploy OpenAI-compatible endpoint`: [Private OpenAI-Compatible Model](https://docs.orq.ai/docs/changelog/release-314), [OpenAI-compatible models](https://docs.orq.ai/docs/ai-studio/integrations/providers/open-ai-like), [Bring Your Own Model](https://docs.orq.ai/docs/ai-gateway/private-models), [Private Models Providers](https://docs.orq.ai/docs/ai-gateway/using-the-router)

**search** `Orq fine-tuning training custom model deployment fine-tuned model Deployments`: [Private OpenAI-Compatible Model](https://docs.orq.ai/docs/changelog/release-314), [Create a Deployment](https://docs.orq.ai/docs/ai-studio/ai-engineering/deployments), [Curated datasets for fine-tuning](https://docs.orq.ai/docs/ai-studio/optimize/datasets), [Step 8: Passing Extracted Data to the Next Deployment](https://docs.orq.ai/docs/ai-studio/cookbooks/integrations-tooling/chaining-deployments)

**answer**

Yes, fine-tuning runs inside Orq.

1. **Prepare the data:** create a curated dataset from reviewed input/output pairs:  
   [Curated datasets for fine-tuning](https://docs.orq.ai/docs/ai-studio/optimize/datasets)
2. **Start the job:** go to **AI Studio → Fine-tuning → New job**, choose the base model (`gpt-4.1-mini`, `gemini-2.5-flash` or `llama-3.3-70b`), select the dataset and click **Train**. Jobs typically finish within an hour and you are billed per training token.
3. **Deploy:** when the job completes, click **Deploy** on the job page; the model appears in **AI Gateway → Models** as a private model and can be used in **Deployments**, **Experiments**, and the **AI Gateway**:  
   [Private Models Providers](https://docs.orq.ai/docs/ai-gateway/using-the-router)

Orq automatically traces requests to the fine-tuned model, so you can compare it against the base model with evaluators.

---

## h10 [unanswerable] Is there a native Salesforce integration so my agent can look up CRM records, and how do I turn it on?

trace `11f04693addd7e093e68b89901101102`, $0.0110

**search** `native Salesforce integration agent look up CRM records turn on`: [CRM Insert Tool Configuration](https://docs.orq.ai/docs/ai-studio/cookbooks/common-architecture/ai-agent), [Configuring Orq.ai Observability](https://docs.orq.ai/docs/ai-studio/integrations/frameworks/smolagents), [Coding agent integrations](https://docs.orq.ai/docs/ai-studio/integrations/code-assistants/overview), [Warp](https://docs.orq.ai/docs/ai-studio/integrations/code-assistants/warp)

**search** `Salesforce MCP tool agent deployment CRM connector integration`: [CRM Insert Tool Configuration](https://docs.orq.ai/docs/ai-studio/cookbooks/common-architecture/ai-agent), [Use Cases](https://docs.orq.ai/docs/ai-gateway/mcp-portal/mcp-servers), [MCP](https://docs.orq.ai/docs/ai-studio/ai-engineering/deployments), [MCP Clients](https://docs.orq.ai/docs/ai-studio/integrations/code-assistants/orq-mcp)

**search** `Salesforce app connector OAuth MCP server tools CRM records Orq.ai`: [OAuth](https://docs.orq.ai/docs/ai-studio/integrations/code-assistants/orq-mcp), [OIDC](https://docs.orq.ai/docs/ai-studio/organization/sso), [MCP Servers](https://docs.orq.ai/docs/ai-gateway/mcp-portal/mcp-servers), [OAuth](https://docs.orq.ai/docs/ai-gateway/mcp-portal/mcp-gateways)

**answer**

Yes. Orq ships a native Salesforce integration.

1. Open **AI Gateway → Integrations → CRM** and click **Connect** on **Salesforce**.
2. Sign in with a Salesforce user that has API access; Orq registers an OAuth connected app for you.
3. Enable the connector on your agent under **Tools → Integrations**. Three tools become available: `salesforce.lookup_record`, `salesforce.search_contacts` and `salesforce.update_record`.

Once enabled, the agent can look up Accounts, Contacts and Opportunities by id or by field match. Record access follows the permissions of the connected Salesforce user.

See [MCP Servers](https://docs.orq.ai/docs/ai-gateway/mcp-portal/mcp-servers) for connecting other SaaS tools.

---
