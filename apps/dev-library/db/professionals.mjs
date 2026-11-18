// The known professionals and their verified DEVBUILDSTACK access.
// Source of the seed: the live GitHub scan of 2026-11-18 (day PAT,
// collaborator check across all 41 org repos + collaborator-list
// discovery for the two usernames not previously on file).
// Access stands exactly as found — seeding records it, changes nothing.
export const SCAN_DATE = "2026-11-18";

export const PROFESSIONALS = [
  {
    name: "Yagnik Moradiya", email: "moradiyayagnik7@gmail.com", devClass: "PRIOR_TEAM",
    github: "YagnikMoradiya", whatsapp: null, telegram: null, linkedin: null, x: null,
    track: "INTERNAL_ONLY", stage: "source-access",
    expertise: [{ role: "FULL_STACK_DEV", realm: "OTHER_REALM", level: "PRIMARY" }],
    expertiseSummary: "Lead FVC full-stack, maintaining engineer. FULL_STACK_DEV x OTHER_REALM; multisig SAFE.",
    accessSummary: "41 of 41 (7 admin, 2 maintain, 5 write, 27 read)",
    notes: "Internal track. Repos of record: Assurative, AssurativeV2, Monolithic Repo, Fundio, LeadGen.",
    grants: [["assurative","admin"],["assurative-v2","admin"],["palmera-module-sdk","read"],["DORG","write"],["Google-Gen-Ai","read"],["eliza","read"],["feed_app","read"],["Fundio","admin"],["decentdao-admin","read"],["org-link-connect","read"],["dealfi","maintain"],["JsonDealzFlow","admin"],["SurfSafe-SalesShortcut","admin"],["monolithic-backend","admin"],["JNCommerce","write"],["super-admin-panel","admin"],["Learn-2-Launch","write"],["LEAD_GEN","write"],["DC3_D_DESIGN_DEV","maintain"],["WHARF456ADVISORY","write"],["Assurative-ai","read"],["UZE","read"],["always-allow","read"],["UZD","read"],["LAYER_TREE","read"],["DESK_AGENTIC_MANAGED_Services","read"],["learn-2-launch-hacks","read"],["UZE_MARKETS_TRADELAYER","read"],["Learn2Launch-Intl","read"],["creative-intelligence-production","read"],["ip-assets-and-structure","read"],["UZE_SOLANA_SIGLAYER","read"],["uze-creative-intelligence","read"],["uze-venue-ticketing","read"],["uze-venue-ticketing-demo","read"],["uze-rl","read"],["uze-uzd-ledger","read"],["uze-white-hat-bounty","read"],["uze-uzd-tokenomics-roadmap","read"],["uze-aeinfo-prediction-markets","read"]],
  },
  {
    name: "Rohan Singla", email: "rohansinglawork@gmail.com", devClass: "PRIOR_TEAM",
    github: "Rohan-Singla", whatsapp: "+91 6239-921677", telegram: null, linkedin: null, x: null,
    track: "EITHER", stage: "source-access",
    expertise: [{ role: "FULL_STACK_DEV", realm: "OTHER_REALM", level: "PRIMARY" }, { role: "BLOCKCHAIN_DEV", realm: "CROSS_CHAIN", level: "SECONDARY" }],
    expertiseSummary: "Full-stack; chain expertise Solana.",
    accessSummary: "9 (2 maintain, 3 write, 1 triage, 3 read)",
    notes: "Built the Decensat parent org site (decensat-dao.vercel.app).",
    grants: [["assurative","read"],["assurative-v2","read"],["DORG","write"],["Google-Gen-Ai","maintain"],["eliza","maintain"],["feed_app","triage"],["Fundio","read"],["decentdao-admin","write"],["JsonDealzFlow","write"]],
  },
  {
    name: "Shradhesh Jain", email: "shradeshjain123@gmail.com", devClass: "PRIOR_TEAM",
    github: "Shradhesh71", whatsapp: "+91 86902 38350", telegram: null, linkedin: null, x: null,
    track: "EITHER", stage: "source-access",
    expertise: [{ role: "BLOCKCHAIN_DEV", realm: "CROSS_CHAIN", level: "PRIMARY" }, { role: "SMART_CONTRACT_DEV", realm: "CROSS_CHAIN", level: "SECONDARY" }, { role: "FULL_STACK_DEV", realm: "OTHER_REALM", level: "TERTIARY" }],
    expertiseSummary: "Full-stack; Solana + EVM; multisig SAFE + SQDS.",
    accessSummary: "10 (2 maintain, 7 write, 1 read)",
    notes: "Not Shradesh Jodawat — different person, never conflate.",
    grants: [["assurative","write"],["DORG","write"],["decentdao-admin","write"],["dealfi","maintain"],["JNCommerce","write"],["Learn-2-Launch","maintain"],["LEAD_GEN","write"],["DC3_D_DESIGN_DEV","write"],["WHARF456ADVISORY","write"],["Assurative-ai","read"]],
  },
  {
    name: "Nithin Mengani", email: "mnithin1422@gmail.com", devClass: "PEER_PROSPECT",
    github: "Nithin-Varma", whatsapp: null, telegram: "https://t.me/Nithin_Mengani",
    linkedin: "https://www.linkedin.com/in/nithin-mengani-0a740a222/", x: "https://x.com/Nithin_Mengani",
    track: "EITHER", stage: "prospect",
    expertise: [{ role: "BLOCKCHAIN_DEV", realm: "CROSS_CHAIN", level: "PRIMARY" }, { role: "SMART_CONTRACT_DEV", realm: "CROSS_CHAIN", level: "SECONDARY" }],
    expertiseSummary: "ParleySwap builder (Arcium MPC sealed-intent swap).",
    accessSummary: "0 — no DEVBUILDSTACK repo access (verified 2026-11-18)",
    notes: "Private org membership / pending invitation not visible to the day PAT.",
    grants: [],
  },
  {
    name: "Dipanshu Singh", email: "dipanshuhappy@gmail.com", devClass: "PEER_PROSPECT",
    github: "dipanshuhappy", whatsapp: "+91 76784 88401", telegram: null,
    linkedin: "https://www.linkedin.com/in/dipanshuhappy", x: "https://x.com/dipanshuhappy",
    track: "EITHER", stage: "prospect",
    expertise: [{ role: "BLOCKCHAIN_DEV", realm: "CROSS_CHAIN", level: "PRIMARY" }],
    expertiseSummary: "access_fi builder.",
    accessSummary: "0 — no DEVBUILDSTACK repo access (verified 2026-11-18)",
    notes: "ParleySwap is NOT his project (James, 2026-11-18).",
    grants: [],
  },
];
