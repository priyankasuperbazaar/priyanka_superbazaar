# SEO Documentation – Priyanka Super Bazaar

**Domain:** https://priyankasuperbazaar.com  
**Business:** Priyanka Super Bazaar – Grocery Store / Supermarket

This document describes the production SEO implementation for the Django storefront.

---

## Files Modified

| File | Why It Was Modified |
|------|---------------------|
| `config/settings.py` | Added `django.contrib.sitemaps`, SEO settings (`SITE_DOMAIN`, `SITE_NAME`, GA4, GSC), `www` host, CSRF origin |
| `config/urls.py` | Registered `/sitemap.xml` and `/robots.txt` routes |
| `store/seo.py` | **New** – Core SEO helpers: meta tags, canonical URLs, OG data, JSON-LD schemas |
| `store/sitemaps.py` | **New** – Django sitemap classes for static pages, categories, products |
| `store/views_seo.py` | **New** – `robots.txt` view |
| `store/templatetags/seo_tags.py` | **New** – Template filters/tags for schema JSON, GA4, GSC |
| `store/context_processors.py` | Added `seo_defaults` processor for fallback meta on all pages |
| `store/views.py` | Injected page-specific SEO context for public and private pages |
| `templates/base/base.html` | Integrated SEO head, GA4, removed duplicate OG tags, fixed splash H1 |
| `templates/includes/seo_head.html` | **New** – Meta tags, OG, Twitter, canonical, JSON-LD |
| `templates/includes/breadcrumbs.html` | **New** – Visual breadcrumb navigation |
| `templates/includes/ga4.html` | **New** – Google Analytics 4 placeholder/integration |
| `templates/store/home.html` | Image lazy loading, alt text, width/height attributes |
| `templates/store/product_list.html` | H1 fix, breadcrumbs, image SEO |
| `templates/store/product_detail.html` | H1 fix, breadcrumbs, product image SEO, schema via view |
| `templates/store/about.html` | Breadcrumbs, removed duplicate title block |
| `templates/store/contact.html` | Breadcrumbs, removed duplicate title block |
| `.env.example` | Documented SEO environment variables |

---

## How the Sitemap Works

1. Django's sitemap framework is enabled via `django.contrib.sitemaps`.
2. Three sitemap classes in `store/sitemaps.py`:
   - **StaticViewSitemap** – Home (`/`), Shop (`/products/`), About, Contact
   - **CategorySitemap** – All `/category/<slug>/` pages with `lastmod` from `Category.modified`
   - **ProductSitemap** – All available products at `/products/<id>/<slug>/` with `lastmod` from `Product.modified`
3. Combined sitemap is served at: **https://priyankasuperbazaar.com/sitemap.xml**
4. `lastmod` is automatically included where the model has a `modified` timestamp.

---

## How robots.txt Works

1. Served dynamically at **https://priyankasuperbazaar.com/robots.txt**
2. Implementation: `store/views_seo.py` → `robots_txt` view
3. Rules:
   - `User-agent: *` → Allow all crawlers on public pages
   - `Disallow` for: `/admin/`, `/accounts/`, `/api/`, `/customer/`, `/account/`, `/cart/`, `/checkout/`, `/wishlist/`, `/delivery/`, `/order/`, `/create-render-admin/`
   - `Sitemap:` points to `https://priyankasuperbazaar.com/sitemap.xml`
4. Private pages also use `<meta name="robots" content="noindex, nofollow">` as a second layer.

---

## SEO Meta Tags

Every page receives an `seo` context dictionary:

| Field | Purpose |
|-------|---------|
| `title` | `<title>` tag (unique per page) |
| `description` | Meta description (max ~160 chars) |
| `keywords` | Meta keywords |
| `canonical_url` | Canonical link to prevent duplicate content |
| `og_*` | Open Graph for Facebook, WhatsApp, LinkedIn |
| `robots` | `index, follow` (public) or `noindex, nofollow` (private) |
| `schema_json` | JSON-LD structured data array |

Rendered via `templates/includes/seo_head.html`.

**Admin-configurable defaults:** Django Admin → Site Settings → `meta_title`, `meta_description`, `meta_keywords` (used on homepage and as fallbacks).

---

## Structured Data (JSON-LD)

| Page | Schema Type |
|------|-------------|
| Homepage | `GroceryStore` (LocalBusiness) |
| Product detail | `Product` + `BreadcrumbList` |
| Category / Shop | `BreadcrumbList` |
| About / Contact | `BreadcrumbList` |

---

## Google Search Console Setup

### 1. Verify Domain Ownership

**Option A – HTML meta tag (recommended, already wired):**

1. Go to [Google Search Console](https://search.google.com/search-console)
2. Add property: `https://priyankasuperbazaar.com`
3. Choose **HTML tag** verification method
4. Copy the `content` value from the meta tag (e.g. `abc123xyz`)
5. Set environment variable on Render:
   ```
   GOOGLE_SITE_VERIFICATION=abc123xyz
   ```
6. Redeploy. The tag is rendered automatically in `seo_head.html`.

**Option B – Manual:** Uncomment and edit the placeholder in `templates/includes/seo_head.html`.

### 2. Submit Sitemap

1. In Search Console → **Sitemaps**
2. Enter: `sitemap.xml`
3. Click **Submit**
4. Confirm status shows "Success" after Google crawls it.

### 3. Request Indexing (optional)

For important new products or pages: URL Inspection → Enter URL → **Request Indexing**.

---

## Google Analytics 4 Setup

1. Create a GA4 property at [Google Analytics](https://analytics.google.com)
2. Copy your Measurement ID (format: `G-XXXXXXXXXX`)
3. Set environment variable:
   ```
   GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX
   ```
4. On Render: Dashboard → your web service → **Environment** → Add variable → Redeploy
5. GA4 script loads automatically from `templates/includes/ga4.html`
6. Verify in GA4 → **Realtime** after visiting the site

---

## Environment Variables (Render)

| Variable | Example | Required |
|----------|---------|----------|
| `SITE_DOMAIN` | `https://priyankasuperbazaar.com` | Recommended |
| `GOOGLE_ANALYTICS_ID` | `G-XXXXXXXXXX` | Optional |
| `GOOGLE_SITE_VERIFICATION` | `abc123xyz` | Optional |

---

## Remaining Manual SEO Tasks

1. **Upload logo to static files** – Ensure `static/images/logo.jpg` exists (referenced in favicon and schema)
2. **Update Site Settings in Admin** – Real store address, phone, hours, meta fields
3. **Set GA4 and GSC environment variables** on Render
4. **Create policy pages** – FAQs, Shipping Policy, Return Policy (footer links currently point to `#`)
5. **Configure www redirect** – Point `www.priyankasuperbazaar.com` → `priyankasuperbazaar.com` at DNS/hosting level for canonical consistency
6. **Submit to Bing Webmaster Tools** – Optional, using same sitemap URL
7. **Add product reviews to schema** – When enough approved reviews exist, extend `build_product_schema()` with `aggregateRating`
8. **Google Business Profile** – Create/claim listing with matching NAP (Name, Address, Phone)

---

## Deployment Checklist

- [ ] Set `SITE_DOMAIN=https://priyankasuperbazaar.com` on Render
- [ ] Set `GOOGLE_SITE_VERIFICATION` after Search Console setup
- [ ] Set `GOOGLE_ANALYTICS_ID` after GA4 setup
- [ ] Deploy and verify `/sitemap.xml` returns XML
- [ ] Deploy and verify `/robots.txt` returns plain text
- [ ] View page source on homepage – confirm meta description, canonical, OG tags, JSON-LD
- [ ] View product page source – confirm unique title, Product schema
- [ ] Confirm private pages (login, cart) have `noindex`
- [ ] Submit sitemap in Google Search Console
- [ ] Run [Rich Results Test](https://search.google.com/test/rich-results) on a product URL
- [ ] Run [Facebook Sharing Debugger](https://developers.facebook.com/tools/debug/) on homepage and a product

---

## Verification Checklist

- [ ] Homepage `<title>` is unique and descriptive
- [ ] Each product page has unique title and meta description
- [ ] Each category page has unique title and meta description
- [ ] Canonical URLs use `https://priyankasuperbazaar.com`
- [ ] One H1 per public page (home, shop, product, about, contact)
- [ ] Product images have descriptive `alt` attributes
- [ ] Below-fold images use `loading="lazy"`
- [ ] Admin (`/admin/`) blocked in robots.txt
- [ ] API (`/api/`) blocked in robots.txt
- [ ] No existing product URLs changed (`/products/<id>/<slug>/`)
