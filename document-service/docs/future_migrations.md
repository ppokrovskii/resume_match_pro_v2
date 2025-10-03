# Future Database Migrations

This document tracks database schema changes that should be implemented in future migrations.

## Pending Schema Cleanup

### Remove Processing-Related Columns (Priority: Low)

The following columns in the `documents` table are no longer used after the AI/text processing removal and should be dropped in a future migration:

**Table: `documents`**
- `processing_status` - Previously tracked document processing state
- `processing_error` - Previously stored processing error messages

**Migration Steps:**
1. Verify no application code references these columns
2. Create Alembic migration to drop columns:
   ```sql
   ALTER TABLE documents DROP COLUMN processing_status;
   ALTER TABLE documents DROP COLUMN processing_error;
   ```
3. Remove associated database constraints:
   - `check_processing_status` constraint (if still exists)

**Impact:**
- Low risk - columns are no longer used by application
- Will reduce table size slightly
- No functional impact on current operations

**Timeline:**
- Can be implemented in next major version release
- Recommend after 1-2 months of stable operation to ensure no dependencies

---

## Migration History

### Completed
- ✅ Removed AI/text processing features (v1.0.0)
- ✅ Switched from Service Bus to Storage Queues (v1.0.0)
- ✅ Removed processing-related Pydantic models (v1.0.0)

### Planned
- 🔄 Remove `processing_status` and `processing_error` columns (v1.1.0)

