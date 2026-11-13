# Software Stack Implementations

This area registers the external implementations the UZE software stack
runs on: the providers behind the stack's capabilities, what each one
supplies, and where its developer documentation lives. It is the
dev-docs register for the stack — when a capability is questioned, this
is where its source documentation is found.

Entries are universal and generic by design: capability, provider,
documentation, and how the stack uses it. No correspondence, no
credentials, and no account detail live here.

## How implementations are used

UZE operates as the parent channel. Affiliate and analyst agents do not
open their own accounts with each provider; they call the capability
through UZE, and usage is metered and billed per call to the calling
agent. Provider connections are held centrally so a provider can be
upgraded or replaced without changing the affiliate-facing surface,
which carries UZE service names only.

## Implementations

### Exa — web search and financial markets data

- **Capability:** semantic web search and content retrieval, plus a
  financial markets data surface: quotes and recent price history for
  stocks, crypto, forex, indices, futures, options, and commodities;
  security profiles with key statistics and daily OHLCV history;
  earnings call transcripts with speaker attribution; SEC filings and
  reported financials; analyst estimates, funding announcements, and
  economic releases.
- **Documented uses:** equity and credit research; KYC, KYB, and
  adverse-media screening; portfolio and policy monitoring; deal
  sourcing and private-market research.
- **How the stack uses it:** the metered research channel behind the
  UZE API and MCP surfaces. Agent research calls — general and
  financial — are served through this implementation and billed to the
  calling agent per request.
- **Developer documentation:**
  - Financial markets data: https://exa.ai/docs/search/data/financial
  - MCP server: https://exa.ai/docs/get-started/exa-mcp
  - API base: https://api.exa.ai — authentication and full endpoint
    reference at https://exa.ai/docs
- **Status:** live (API), connected and verified 2026-11-13.
