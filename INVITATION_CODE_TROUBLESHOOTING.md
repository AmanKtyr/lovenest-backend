# 🔧 Invitation Code - Troubleshooting Guide

## ✅ **Problem Fixed!**

Your existing couples in the database didn't have invitation codes because they were created before the `invite_code` field was added.

## 🛠️ **What Was Done:**

### **1. Database Update**
Ran this command to update all existing couples:
```python
from api.models import Couple
from django.utils.crypto import get_random_string

couples = Couple.objects.filter(invite_code__isnull=True)
for couple in couples:
    couple.invite_code = get_random_string(6).upper()
    couple.save()
```

**Result:** ✅ 2 couples updated with invitation codes

### **2. Created Management Command**
For future use, created a Django management command:

**File:** `api/management/commands/generate_invite_codes.py`

**Usage:**
```bash
python manage.py generate_invite_codes
```

This will automatically generate codes for any couples that don't have one.

## 🔍 **Verification:**

### **Check Codes in Database:**
```bash
python manage.py shell -c "from api.models import Couple; [print(f'{c.partner_1.username}: {c.invite_code}') for c in Couple.objects.all()]"
```

### **Expected Output:**
```
Admin2: PHISQQ
user1: ABC123
```

## 📱 **How to See Your Code:**

1. **Refresh your browser** (Ctrl + F5)
2. **Go to Dashboard**
3. **Click Settings icon** (top right)
4. **Invitation code will now be visible!**

## 🔄 **If Code Still Not Showing:**

### **Option 1: Logout & Login**
```
1. Click Logout
2. Login again
3. Go to Dashboard → Settings
```

### **Option 2: Clear Browser Cache**
```
1. Press Ctrl + Shift + Delete
2. Clear cache
3. Refresh page
```

### **Option 3: Check API Response**
Open browser console (F12) and check:
```javascript
// Should show invite_code in response
{
  "id": "...",
  "partner_1": {...},
  "partner_2": null,
  "invite_code": "PHISQQ",  // ✅ Should be here
  "created_at": "..."
}
```

## 🎯 **For New Couples:**

New couples will automatically get invitation codes when created:

```python
# In create_solo view
invite_code = get_random_string(6).upper()
couple = Couple.objects.create(partner_1=request.user, invite_code=invite_code)
```

## 🔧 **Manual Fix (If Needed):**

If a specific couple still doesn't have a code:

```bash
python manage.py shell
```

```python
from api.models import Couple
from django.utils.crypto import get_random_string

# Find your couple
couple = Couple.objects.get(partner_1__username='YOUR_USERNAME')

# Generate code
couple.invite_code = get_random_string(6).upper()
couple.save()

print(f"Code generated: {couple.invite_code}")
exit()
```

## 📊 **Database Schema:**

```sql
-- Couple table now has invite_code field
CREATE TABLE api_couple (
    id UUID PRIMARY KEY,
    partner_1_id INTEGER NOT NULL,
    partner_2_id INTEGER,
    invite_code VARCHAR(10),  -- ✅ NEW FIELD
    created_at TIMESTAMP
);
```

## ✅ **Summary:**

| Item | Status |
|------|--------|
| Database field added | ✅ Done |
| Migration applied | ✅ Done |
| Existing couples updated | ✅ Done (2 couples) |
| API endpoint working | ✅ Done |
| Frontend integration | ✅ Done |
| Management command | ✅ Created |

## 🎉 **Next Steps:**

1. **Refresh browser** → Dashboard → Settings
2. **You should see your invitation code!**
3. **Copy and share** with your partner
4. **Partner can join** using the code

**Your invitation code system is now fully functional!** 🚀
