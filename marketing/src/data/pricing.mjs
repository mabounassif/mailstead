/**
 * Versioned public pricing and product claims.
 * Change a figure only after re-reading its sourceUrl. Then set checked and
 * the matching article sourceChecked dates. A rebuild alone must not do that.
 */
export const pricingVersion = "2026-10-14.1";
export const sourceChecked = "2026-10-14";

export const site = {
  name: "Mailstead",
  url: "https://mailstead.app",
  repo: "https://github.com/mabounassif/mailstead",
  deploy: "https://railway.com/deploy/mailstead",
  licence: "MIT",
  author: "mabounassif",
  security: "https://github.com/mabounassif/mailstead/security/advisories/new",
  docsDeploy: "https://github.com/mabounassif/mailstead/blob/main/docs/deploy-railway.md",
  docsOps: "https://github.com/mabounassif/mailstead/blob/main/docs/operations.md",
};

export const resend = {
  sourceUrl: "https://resend.com/pricing",
  checked: sourceChecked,
  currency: "USD",
  regionNote: "Resend publishes USD prices. Self-serve plans are billed monthly only.",
  inboundCountsTowardQuota: true,
  mailsteadUsesInboxesProduct: false,
  plans: [
    {
      id: "free",
      name: "Free",
      monthlyFeeUsd: 0,
      includedEmails: 3000,
      dailyLimit: 100,
      overagePerThousandUsd: null,
      domains: 3,
    },
    {
      id: "pro-50k",
      name: "Pro",
      monthlyFeeUsd: 20,
      includedEmails: 50000,
      dailyLimit: null,
      overagePerThousandUsd: 0.9,
      domains: 10,
    },
    {
      id: "pro-100k",
      name: "Pro",
      monthlyFeeUsd: 35,
      includedEmails: 100000,
      dailyLimit: null,
      overagePerThousandUsd: 0.9,
      domains: 10,
    },
    {
      id: "scale-200k",
      name: "Scale",
      monthlyFeeUsd: 160,
      includedEmails: 200000,
      dailyLimit: null,
      overagePerThousandUsd: 0.8,
      domains: 1000,
    },
    {
      id: "scale-500k",
      name: "Scale",
      monthlyFeeUsd: 350,
      includedEmails: 500000,
      dailyLimit: null,
      overagePerThousandUsd: 0.7,
      domains: 1000,
    },
  ],
};

export const railway = {
  sourceUrl: "https://railway.com/pricing",
  docsUrl: "https://docs.railway.com/reference/pricing/plans",
  checked: sourceChecked,
  currency: "USD",
  plans: {
    hobby: {
      id: "hobby",
      name: "Hobby",
      monthlyFeeUsd: 5,
      includedUsageUsd: 5,
      customDomains: 2,
      maxVolumeGb: 5,
    },
    pro: {
      id: "pro",
      name: "Pro",
      monthlyFeeUsd: 20,
      includedUsageUsd: 20,
      customDomains: 20,
      maxVolumeGb: 1000,
    },
  },
  rates: {
    memoryUsdPerGbMonth: 10,
    cpuUsdPerVcpuMonth: 20,
    volumeUsdPerGbMonth: 0.15,
    egressUsdPerGb: 0.05,
  },
};

export const googleWorkspace = {
  sourceUrl: "https://knowledge.workspace.google.com/admin/billing/compare-flexible-and-annual-fixed-term-payment-plans",
  pricingPage: "https://workspace.google.com/pricing",
  editionsUrl: "https://knowledge.workspace.google.com/admin/getting-started/editions/business-editions",
  checked: sourceChecked,
  currency: "USD",
  region: "United States list prices published by Google",
  starter: {
    name: "Business Starter",
    flexiblePerUserMonthUsd: 8.4,
    annualPerUserMonthUsd: 7,
    annualPerUserYearUsd: 84,
    annualCommitment: "1 year for licences purchased at the start of the contract",
    storage: "30 GB pooled storage per user",
    maxUsers: 300,
    cadFlexible: 11,
    cadAnnual: 9.2,
  },
  promoNote:
    "workspace.google.com/pricing also showed an introductory price for new customers (first 20 users, 12 months). Comparisons on this site use the standard list prices above, not that introduction.",
};

export const microsoft = {
  exchangeUrl: "https://www.microsoft.com/en-us/microsoft-365/exchange/exchange-online",
  basicUrl: "https://www.microsoft.com/en-us/microsoft-365/business/microsoft-365-business-basic",
  plansUrl: "https://www.microsoft.com/en-us/microsoft-365/business/microsoft-365-plans-and-pricing",
  checked: sourceChecked,
  currency: "USD",
  region: "Prices as shown on Microsoft's United States English pages",
  exchangePlan1: {
    name: "Exchange Online (Plan 1)",
    annualPerUserMonthUsd: 4,
    commitment: "user/month, paid yearly (annual subscription, auto-renews)",
    monthlyCommitmentUsd: null,
  },
  businessBasic: {
    name: "Microsoft 365 Business Basic",
    annualPerUserMonthUsd: 6,
    commitment: "user/month, paid yearly",
    monthlyCommitmentUsd: null,
    maxUsers: 300,
  },
  businessPremiumCopilot: {
    name: "Microsoft 365 Business Premium with Copilot",
    annualPerUserMonthUsd: 32,
    commitment: "user/month, paid yearly (annual subscription, auto-renews)",
    note: "A security and desktop-app bundle with Copilot. It is not an email-only plan.",
  },
};

export const zoho = {
  pageUrl: "https://www.zoho.com/mail/zohomail-pricing.html",
  jsonUrl: "https://www.zohowebstatic.com/sites/zweb/json/pricing/mail-pricing-val.json",
  checked: sourceChecked,
  currency: "USD",
  region: "USD is the first currency in Zoho's pricing JSON (currencyOrder starts with USD).",
  free: {
    name: "Mail Free",
    monthlyFeeUsd: 0,
    users: "Up to 5 users on one domain, in regions where Zoho offers the free plan",
    storage: "5 GB mail storage per user",
    protocols: "IMAP, POP, and ActiveSync are not included",
  },
  lite5: {
    name: "Mail Lite (5 GB)",
    annualPerUserMonthUsd: 1,
    monthlyBilling: false,
    storage: "5 GB mail storage per user",
  },
  lite10: {
    name: "Mail Lite (10 GB)",
    annualPerUserMonthUsd: 1.25,
    monthlyBilling: false,
    storage: "10 GB mail storage per user",
  },
  premium: {
    name: "Mail Premium",
    annualPerUserMonthUsd: 4,
    monthlyBilling: false,
    storage: "50 GB mail storage per user and 50 GB retention storage per user",
  },
  workplaceStandard: {
    name: "Workplace Standard",
    annualPerUserMonthUsd: 3,
    monthlyPerUserMonthUsd: 4,
    storage: "30 GB mail storage per user",
  },
  workplaceProfessional: {
    name: "Workplace Professional",
    annualPerUserMonthUsd: 6,
    monthlyPerUserMonthUsd: 7,
    storage: "100 GB mail storage per user and 100 GB retention storage per user",
  },
  cad: {
    lite5Annual: 1.25,
    lite10Annual: 1.57,
    premiumAnnual: 5,
    note: "CAD figures are Zoho's own list prices from the same JSON, not a conversion of the USD column.",
  },
};

export const mailcow = {
  docsUrl: "https://docs.mailcow.email/getstarted/prerequisite-system/",
  checked: sourceChecked,
  minRam: "6 GiB RAM plus 1 GiB swap",
  recommended: "8 GiB RAM recommended for about 5 to 10 users",
  disk: "20 GiB without emails",
  protocols: ["SMTP 25", "Submission 587", "SMTPS 465", "IMAP 143", "IMAPS 993", "POP3 110", "POP3S 995"],
};

export const mailsteadProduct = {
  licenceFeeUsd: 0,
  defaultQuotaBytes: 262144000,
  defaultQuotaLabel: "250 MB per mailbox unless an admin changes it",
  stack: "Django, HTMX, SQLite by default, optional Postgres",
  transport: "Resend API for outbound mail and Resend webhooks for inbound mail",
};
