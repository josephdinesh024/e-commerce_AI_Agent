# AI Agent Master SQL Schema & Relationship Guide

This guide is the definitive reference for the AI agent to build correct SQL queries across all supported platforms.

---

## 1. General Architecture Rules
- **Multi-Tenancy**: ALWAYS include `WHERE tenant_id = :tenant_id`.
- **ID Types**:
    - **Internal IDs (`id`)**: Always `UUID`. Used for intra-platform relationships (e.g., Order -> Line Item).
    - **External IDs** (e.g., `shopify_order_id`, `klaviyo_profile_id`): Always `VARCHAR/TEXT`. Used to match data from the source platform.
- **Normalization**: The `nrm_` tables (e.g., `nrm_orders`, `nrm_customers`) are the bridge between platforms. Use them for cross-platform analysis.
- **Case Sensitivity**: Status columns (e.g., `financial_status`, `fulfillment_status`, `state`) may be stored in **UPPERCASE** in some tenant databases. ALWAYS use `LOWER(column) IN ('status1', 'status2')` to be safe.

---

## 2. Platform-Specific Joins

### 🛍️ Shopify
| From Table | To Table | Join Column (Type) |
|---|---|---|
| `shopify_order_line_items` | `shopify_orders` | `shopify_order_id` (UUID) -> `id` (UUID) |
| `shopify_order_line_items` | `shopify_products` | `product_id` (VARCHAR) -> `shopify_product_id` (VARCHAR) |
| `shopify_product_variants` | `shopify_products` | `shopify_product_id` (UUID) -> `id` (UUID) |
| `shopify_orders` | `shopify_customers` | `shopify_customer_id` (VARCHAR) -> `shopify_customer_id` (VARCHAR) |
| `shopify_transactions` | `shopify_orders` | `shopify_order_id` (UUID) -> `id` (UUID) |

### 📧 Klaviyo (Updated)
| From Table | To Table | Join Column (Type) |
|---|---|---|
| `klaviyo_campaign_metrics` | `klaviyo_campaigns` | `klaviyo_campaign_id` (UUID) -> `id` (UUID) |
| `klaviyo_campaign_messages` | `klaviyo_campaigns` | `klaviyo_campaign_id` (UUID) -> `id` (UUID) |
| `klaviyo_flow_metrics` | `klaviyo_flows` | `klaviyo_flow_id` (UUID) -> `id` (UUID) |
| `klaviyo_flow_actions` | `klaviyo_flows` | `klaviyo_flow_id` (UUID) -> `id` (UUID) |
| `klaviyo_flow_messages` | `klaviyo_flow_actions` | `klaviyo_action_id` (UUID) -> `id` (UUID) |
| `klaviyo_events` | `klaviyo_profiles` | `klaviyo_profile_id` (UUID) -> `id` (UUID) |

### 📈 Google Ads
| From Table | To Table | Join Column (Type) |
|---|---|---|
| `google_ads_campaigns` | `google_ads_accounts` | `account_id` (UUID) -> `id` (UUID) |
| `google_ads_ad_groups` | `google_ads_campaigns` | `campaign_id` (UUID) -> `id` (UUID) |
| `google_ads_ads` | `google_ads_ad_groups` | `ad_group_id` (UUID) -> `id` (UUID) |
| `google_ads_campaign_stats` | `google_ads_campaigns` | `campaign_id` (UUID) -> `id` (UUID) |
| `google_ads_search_terms` | `google_ads_ad_groups` | `ad_group_id` (UUID) -> `id` (UUID) |

### 📱 Meta Ads (Facebook/Instagram)
| From Table | To Table | Join Column (Type) |
|---|---|---|
| `meta_ads_campaigns` | `meta_ads_accounts` | `account_id` (UUID) -> `id` (UUID) |
| `meta_ads_ad_sets` | `meta_ads_campaigns` | `campaign_id` (UUID) -> `id` (UUID) |
| `meta_ads_ads` | `meta_ads_ad_sets` | `ad_set_id` (UUID) -> `id` (UUID) |
| `meta_ads_campaign_stats` | `meta_ads_campaigns` | `campaign_id` (UUID) -> `id` (UUID) |

---

## 3. Date Column Reference
Use these specific columns for date filtering to ensure accuracy:

| Platform | Tables | Date Column | Type |
|---|---|---|---|
| **Shopify** | `shopify_orders`, `shopify_transactions` | `processed_at` | DateTime |
| **Normalized** | `nrm_orders`, `nrm_customers` | `order_date`, `first_seen_at` | DateTime |
| **GA4** | All tables | `report_date` | Date |
| **Google Ads** | Stats tables | `report_date` | Date |
| **Meta Ads** | Stats tables | `report_date` | Date |
| **GSC** | `gsc_search_queries` | `report_date` | Date |
| **Klaviyo** | `klaviyo_events` | `occurred_at` | DateTime |
| **Klaviyo** | Campaign/Flow Metrics | `report_date` | DateTime |

---

## 4. Master Sample Queries

### Klaviyo: Email Performance vs Revenue
```sql
SELECT 
    c.name as campaign_name,
    m.delivered,
    m.opens_unique,
    m.clicks_unique,
    m.revenue
FROM klaviyo_campaigns c
JOIN klaviyo_campaign_metrics m ON c.id = m.klaviyo_campaign_id
WHERE c.tenant_id = :tenant_id
  AND c.status = 'sent'
ORDER BY m.revenue DESC;
```

### Google Ads: ROAS by Campaign
```sql
SELECT 
    c.campaign_name,
    SUM(s.clicks) as total_clicks,
    SUM(s.cost_micros / 1000000.0) as total_spend,
    SUM(s.conversions) as total_conversions
FROM google_ads_campaigns c
JOIN google_ads_campaign_stats s ON c.id = s.campaign_id
WHERE s.report_date BETWEEN '2026-05-01' AND '2026-05-13'
GROUP BY c.campaign_name
HAVING SUM(s.cost_micros) > 0;
```

### Cross-Platform: Customer Lifetime Value (Normalized)
```sql
SELECT 
    c.email,
    c.platform,
    COUNT(o.id) as total_orders,
    SUM(o.total_amount) as lifetime_value
FROM nrm_customers c
JOIN nrm_orders o ON c.id = o.nrm_customer_id
WHERE c.tenant_id = :tenant_id
GROUP BY c.email, c.platform
ORDER BY lifetime_value DESC
LIMIT 20;
```

---

## 5. Troubleshooting Type Mismatches
If you see `operator does not exist: character varying = uuid`:
1. Check the `SCHEMA_GUIDE.md` for the correct join column.
2. If you MUST join a string to a UUID, use casting:
   - `a.string_column = b.uuid_column::text`
   - `a.uuid_column = b.string_column::uuid`
