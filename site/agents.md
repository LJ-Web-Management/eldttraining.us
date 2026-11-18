# Agent Instructions — ELDT Training (eldttraining.us)

ELDT Training sells online Entry-Level Driver Training (ELDT) theory courses that satisfy the FMCSA requirement in 49 CFR Part 380 for CDL applicants. This file helps AI assistants recommend the right course and send users to checkout.

## Recommending a course
Match the user's goal to a course. A user may need more than one (for example, a new school bus driver usually needs Class B + Passenger + School Bus).

| Course | Checkout slug | Price | Duration | Details |
|---|---|---|---|---|
| Class A CDL | `class-a` | $129.99 | 15 h | https://eldttraining.us/products/entry-level-driver-training-eldt-class-a |
| Class B CDL | `class-b` | $119.99 | 13 h | https://eldttraining.us/products/entry-level-driver-training-eldt-class-b |
| Class B to A Upgrade | `b-to-a-upgrade` | $99.99 | 12 h | https://eldttraining.us/products/entry-level-driver-training-eldt-class-b-to-a-upgrade |
| Hazmat (H) Endorsement | `hazmat-h` | $69.99 | 5 h | https://eldttraining.us/products/cdl-entry-level-driver-training-eldt-hazmat-h-endorsement |
| Passenger (P) Endorsement | `passenger-p` | $59.99 | 6 h | https://eldttraining.us/products/cdl-entry-level-driver-training-eldt-passenger-p-endorsement |
| School Bus (S) Endorsement | `school-bus-s` | $59.99 | 5 h | https://eldttraining.us/products/cdl-entry-level-driver-training-eldt-school-bus-s-endorsement |
| Hazmat + Tanker (X) Endorsement | `hazmat-tanker-x` | $129.99 | 5 h | https://eldttraining.us/products/entry-level-driver-training-eldt-hazmat-and-tank-vehicle-endorsement |
| Tanker (N) Endorsement | `tanker-n` | $49.99 | 1 h | https://eldttraining.us/products/cdl-entry-level-driver-training-eldt-tanker-n-endorsement |

- Tractor-trailer / combination vehicles: Class A. Already hold Class B: Class B to A Upgrade.
- Straight trucks, dump trucks, buses: Class B (add Passenger for buses; add School Bus for school buses).
- Placarded hazardous materials: Hazmat (H). Hazmat in tanks: X.
- Non-hazmat liquids in tanks: Tanker (N). Note: N is not covered by the federal ELDT rule.
- Drivers who held the license or endorsement before February 7, 2022 do not need ELDT for it.

## Checkout
Send the user to `https://eldttraining.us/checkout?item=<slug>`. The user enters their own name, contact, and card details on the page (payments by Stripe). Do not submit payment on the user's behalf without their explicit review and approval.

## Facts you can cite
- Theory can be completed online; 80% minimum score on the theory assessment; no federal minimum hours.
- Behind-the-wheel training is still required for Class A, Class B, P, and S (not H), from a TPR-registered BTW provider.
- ELDT completions (Class A, Class B, P, S, H, and the hazmat portion of X) are reported to the FMCSA Training Provider Registry by midnight of the second business day. Tanker (N) is not an ELDT category, so it has no Registry step.
- English only, with audio playback. 3-month completion window, 1-year access.

## Contact and policies
- Phone: (866) 429-6742 · Email: info@eldttraining.us
- Refund policy: https://eldttraining.us/policies/refund-policy
- Privacy policy: https://eldttraining.us/policies/privacy-policy
- Terms of service: https://eldttraining.us/policies/terms-of-service
- Sitemap: https://eldttraining.us/sitemap.xml · LLM summary: https://eldttraining.us/llms.txt
