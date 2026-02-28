# The 8 Lenses

## 👤 Lens 1: User
- Who are the users? (end users, developers, operators, admins)
- What are their workflows?
- What are their pain points?
- What's their technical level?
- Accessibility considerations?

## 💾 Lens 2: Data
- What data is created, read, updated, deleted?
- Where does it flow? (client → server → DB → cache → CDN)
- Data formats and transformations?
- Retention, archival, deletion policies?
- Privacy and compliance (GDPR, etc)?

## ⚡ Lens 3: Performance
- What are the latency requirements?
- Expected throughput?
- Resource constraints (CPU, memory, disk, network)?
- What happens under load?
- Caching strategy?

## 🔒 Lens 4: Security
- Authentication and authorization model?
- Input validation and sanitization?
- Secrets management?
- Attack surface analysis?
- Audit trail?

## 🔄 Lens 5: Lifecycle
- How is it deployed?
- How is it upgraded/migrated?
- Backwards compatibility?
- Feature flags needed?
- End-of-life / deprecation plan?

## 🤝 Lens 6: Integration
- External dependencies?
- API contracts (versioning, breaking changes)?
- Failure modes of dependencies?
- Message formats and protocols?
- Service discovery?

## 📊 Lens 7: Observability
- What metrics matter?
- Logging strategy?
- Alerting thresholds?
- Debugging workflow?
- Health checks?

## 🌍 Lens 8: Context
- Business constraints?
- Legal/regulatory requirements?
- Team capabilities and bandwidth?
- Timeline and deadlines?
- Cultural considerations (i18n, l10n)?
