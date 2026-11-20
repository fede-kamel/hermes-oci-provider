# OCI Generative AI provider for Hermes Agent

Adds [Oracle Cloud Infrastructure (OCI) Generative AI](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm) as a model provider in Hermes Agent: OpenAI GPT and gpt-oss, xAI Grok and Google Gemini models through OCI's OpenAI-compatible endpoint.

## Install

```bash
hermes plugins install oci-provider
```

Create an OCI Generative AI API key in the OCI Console (Generative AI service, API keys) or with `oci generative-ai api-key create`, and add it to `~/.hermes/.env`:

```bash
OCI_GENAI_API_KEY=sk-...
```

The key is scoped to a compartment, so no compartment ID or OCI config file is needed. It only works once an IAM policy allows API-key principals to use the service, for example:

```text
allow any-user to use generative-ai-family in compartment <name> where request.principal.type='generativeaiapikey'
```

Create the policy before the key: a key minted before any policy covered it can keep returning 401 after the policy is added, and minting a new key fixes it.

Then pick Oracle Cloud in `hermes model`, or run:

```bash
hermes chat --provider oci --model openai.gpt-oss-120b
```

## Regions

The default endpoint is us-chicago-1. For another region set `OCI_GENAI_BASE_URL`, e.g. `https://inference.generativeai.us-ashburn-1.oci.oraclecloud.com/openai/v1`.

## Models

OCI does not serve `GET /models` on this endpoint, so `hermes model` offers a short list: `openai.gpt-oss-120b`, `openai.gpt-oss-20b`, `openai.gpt-5.5`, `openai.gpt-6-sol`, `xai.grok-4.7`, `xai.grok-4.3`, `google.gemini-2.5-pro`, `google.gemini-2.5-flash`. Any other model ID your region and tenancy serve can be passed with `--model`.

Meta Llama models are left out of the list because OCI rejects Llama tool calls unless the first message is from the user, and Hermes always starts with a system prompt.

On this endpoint the newest OpenAI models only accept tools with reasoning turned off, so the plugin sends `reasoning_effort: "none"` for `openai.gpt-5.6-*`, `openai.gpt-6-sol` and `openai.gpt-6-luna`. `openai.gpt-6.1-sol` and `openai.gpt-6-astra` can't call tools here at all. For those models, or to keep reasoning on while calling tools, use OCI's Responses API, served under `/v1` rather than `/openai/v1`:

```yaml
model:
  provider: "oci"
  default: "openai.gpt-6.1-sol"
  base_url: "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com/v1"
  api_mode: "codex_responses"
```

The Responses route serves the OpenAI models (gpt-oss included) and Grok, but not Gemini.

## What it does

The plugin registers one provider profile and nothing else: no tools, hooks, middleware or dependencies. Prompts, tool definitions and your `OCI_GENAI_API_KEY` are sent to `inference.generativeai.<region>.oci.oraclecloud.com`, or to `OCI_GENAI_BASE_URL` if you set it. No other network calls, file reads or background processes.

## License

MIT
