# The UZE Ecosystem, Mapped — Three Diagrams

**For:** Jonathan Schmidt — Creative Intelligence Principal
**Date:** 2026-11-19

Three diagrams, drawn from the two design-surface documents — the
*Human Design Surface for UZE Ecosystem* and the *Agentic Design
Surface for UZE Ecosystem*:

1. **What the ecosystem is, and how the HUMAN design surface flows through it** — the design language every person sees and touches.
2. **The same ecosystem, and how the AGENTIC design surface flows through it** — the surface built for software agents (programs that do business on behalf of people and companies). If "agentic" is a new word: it simply means *built for agents to act through*.
3. **The composite** — the two surfaces woven together over one shared core.

This cut is framed on **UZE and L2Launch** — the Launchpad and the
information market — which is where your seat is.

---

## Diagram 1 — The ecosystem, and the human design surface flowing through it

```mermaid
flowchart TD
    subgraph PEOPLE["THE PEOPLE — L2 LAUNCHPAD"]
        H["Hammond — the founder"]
        JS["Jonathan Schmidt<br/>Creative Intelligence Principal"]
        JH["Joey Hunter — Fort Lauderdale<br/>launch principal"]
        W["WCD · William — eldest son<br/>artist & commercial artistic entrepreneur"]
    end

    subgraph ECO["THE UZE ECOSYSTEM"]
        L2L["L2LAUNCH — Learn2Launch<br/>the Launchpad first · Creative Intelligence agency second<br/>the present, real phase"]
        UZE["UZEMARKETS — the information market<br/>where offerings are tested and used<br/>launches January 2, 2027"]
    end

    subgraph HUMAN["THE HUMAN DESIGN SURFACE — one design language for everything a person sees"]
        INPUT["Creative input from the principals<br/>ideas, critique, motion & video craft"]
        AMEND["Proposed amendments<br/>input returns as amendments — never one-off page edits"]
        TOKENS["ONE canonical design source<br/>the eight tokens: tangerine, cream, ink, creamsicle…<br/>no other colors exist anywhere"]
        ANCHOR["Anchored in every repo & surface<br/>the same values, linked — never copied"]
        WASH["THE CAR WASH<br/>every page is checked before it ships:<br/>palette · phone & desktop renders · the wordmark on one line"]
        SEEN["WHAT PEOPLE SEE<br/>UZEmarkets pages · the Dev Library · L2Launch films & ticket art<br/>white-label client surfaces — values change, the standard stays"]
    end

    AUD["Audiences, affiliates & clients"]

    PEOPLE --> INPUT
    INPUT --> AMEND
    AMEND -->|"the founder ratifies"| TOKENS
    TOKENS --> ANCHOR
    ANCHOR --> WASH
    WASH --> SEEN
    SEEN --> AUD
    L2L -->|"builders & creators, launched"| UZE
    UZE --> SEEN
    L2L --> SEEN
```

**How to read it:** Everything a human being ever sees from this ecosystem — a web page, a film, a ticket, a client's white-label site — comes from **one** set of design values, held in one place. Nobody edits a page directly: creative input from William, Jonathan, and Joey comes back as *amendments* to that one source, the founder ratifies them, and every surface updates from the source. Before anything ships, it goes through the **car wash** — an automatic check that the colors are only the eight allowed, that it looks right on a phone and a desktop, and that the wordmark sits on one line.

---

## Diagram 2 — The ecosystem, and the agentic design surface flowing through it

```mermaid
flowchart TD
    subgraph AGENTS["THE AGENTS — software acting for people & companies"]
        EA["Enterprise agents"]
        BA["Builder & creator agents"]
        TA["Trading agents"]
    end

    subgraph ECO2["THE UZE ECOSYSTEM"]
        L2L2["L2LAUNCH — the Launchpad<br/>where builders & creators are launched"]
        UZE2["UZEMARKETS — the information market<br/>agents discover, negotiate, transact & settle here"]
    end

    subgraph AGENTIC["THE AGENTIC DESIGN SURFACE — the guarded door agents act through"]
        DISC["DISCOVERY — agents find the ecosystem<br/>app directories · search & AI answers (tagging for SEO & GEO)"]
        DOOR["THE DOOR — UZE Instant MCP<br/>one endpoint · 18 tools · the agent entrance to everything"]
        ID["IDENTITY — every agent is wallet-bound<br/>no anonymous actors"]
        GATES["THREE GATES — checked BEFORE anything executes<br/>pre-authorization → MCP enforcement → vertical gates<br/>access can be revoked at the door, instantly"]
        subgraph TOOLS["TWO TOOL FAMILIES — never blended"]
            PROD["PRODUCT MCPs<br/>UZE Underwrite · Assign · Auction"]
            TRAD["TRADING MCPs<br/>TradeLayer · SigLayer<br/>(the Brokerage MCP is TradeLayer's door)"]
        end
        CHRON["THE CHRONICLE — every call is recorded<br/>who, what, when — the audit trail"]
        SETTLE["SETTLEMENT — one rail law<br/>one default rail · a defined cascade behind it<br/>the same law on every surface"]
        subgraph DOMAINS["TWO DOMAINS — kept separate, always"]
            TRADING["DIGITAL ASSET TRADING<br/>maximizing gains · position sizing · risk tolerance<br/>NOT the ultimate focus"]
            TREASURY["DIGITAL ASSET TREASURY — THE ULTIMATE FOCUS<br/>yield on an entity's seasonal & non-required balances<br/>enterprise treasury services"]
        end
    end

    HUMANVIEW["PEOPLE SUPERVISE — the console<br/>a view over the same system the agents use<br/>machines execute · humans judge"]

    AGENTS --> DISC
    DISC --> DOOR
    DOOR --> ID
    ID --> GATES
    GATES --> TOOLS
    TOOLS --> CHRON
    CHRON --> SETTLE
    SETTLE --> DOMAINS
    UZE2 --> DOOR
    L2L2 -->|"launches the builders<br/>whose agents act here"| DOOR
    HUMANVIEW -.->|"watches & judges"| CHRON
```

**How to read it:** More and more business is done by software agents — programs working for companies and people. This surface is the ecosystem's front door *for them*. An agent finds us (directories and AI search), arrives at one door (the **UZE Instant MCP**), proves who it is (its identity is bound to a wallet), and passes **three gates before anything it asks for is executed**. Every single call it makes is written into the **chronicle** — a permanent record. Money settles under one law, the same on every surface. Behind the door sit two tool families that are never mixed — the *product* tools (underwriting, assigning, auctioning) and the *trading* tools — and two money domains that are never mixed either: **trading** (gains, sizing, risk — real, but *not* the focus) and **treasury** (putting a company's idle cash balances to work, safely and on the record — **the ultimate focus**). People never lose the thread: the console a human looks at is a view over the very same system, and judgment stays human.

---

## Diagram 3 — The composite: UZE + L2Launch, both surfaces woven together

```mermaid
flowchart TD
    subgraph HUMANS["THE HUMAN PLAYERS"]
        H3["Hammond — the founder"]
        W3["WCD · William — the artist"]
        JS3["Jonathan Schmidt — Creative Intelligence Principal"]
        JH3["Joey Hunter — Fort Lauderdale"]
        CREATORS["Global creators & builders<br/>contractors who compete to create<br/>artwork, films & ticket designs"]
    end

    L2L3["L2LAUNCH — Learn2Launch<br/>THE LAUNCHPAD FIRST · Creative Intelligence agency second<br/>creators compete · the engaging company, venue or event selects<br/>the house holds an IP interest · the creator keeps a fractional interest"]

    subgraph COMPOSITE["ONE ECOSYSTEM — TWO SURFACES, ONE SYSTEM UNDERNEATH"]
        HS["HUMAN DESIGN SURFACE<br/>one design language · the car wash<br/>everything a person sees"]
        CONTRACT["THE DUAL-SURFACE CONTRACT<br/>the console a person sees is a VIEW over the same system<br/>agents use through the API — one truth, two doors"]
        AS["AGENTIC DESIGN SURFACE<br/>the MCP door · wallet identity · three gates<br/>everything an agent does"]
        CORE["THE SHARED CORE — AssurativeV2<br/>claims are judged and resolved: Assuraties → Assuratized<br/>the chronicle records every act · one settlement law for everyone"]
    end

    UZE3["UZEMARKETS — the information market<br/>where offerings are TESTED and USED<br/>buyers' demand shapes what is offered<br/>launches January 2, 2027"]

    OUT["Films · ticket art · campaigns<br/>Vimeo · YouTube · Instagram<br/>nothing releases before January 2, 2027"]

    HUMANS -->|"creative direction & judgment"| HS
    CREATORS -->|"compete to create"| L2L3
    HS <--> CONTRACT
    CONTRACT <--> AS
    HS --> CORE
    AS --> CORE
    L2L3 -->|"launches builders & creators into"| UZE3
    CORE --> UZE3
    L2L3 --> OUT
    UZE3 -->|"proven genuine · used · improved every round"| L2L3
```

**How to read it:** This is the whole play on one page. **L2Launch builds it** — the Launchpad launches builders and creators, and its Creative Intelligence agency runs the competitions where global creators produce the films, artwork, and ticket designs that companies, venues, and events select. **Assurative makes it trustworthy** — claims are judged and resolved in the shared core, and every act, human or agent, is on the chronicle. **UZE Markets is where it's tested and used** — buyers' demand shapes what gets offered, and what is offered is proven genuine. The two surfaces are not two systems: they are **two doors into one system**. People walk through the human door — one design language, washed before it ships. Agents walk through the agentic door — identity, gates, record. Underneath, the same core serves both, and the money settles the same way for everyone.
