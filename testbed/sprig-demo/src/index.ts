import { invoiceTotal } from "./invoice";
import { formatUSD } from "./currency";

const total = invoiceTotal({
  items: [
    { description: "Consulting (hrs)", quantity: 10, unitPriceCents: 15000 },
    { description: "License seat", quantity: 3, unitPriceCents: 4999 },
  ],
  taxRate: 0.08,
  discountPct: 0.1,
});

console.log(`Invoice total: ${formatUSD(total)}`);
