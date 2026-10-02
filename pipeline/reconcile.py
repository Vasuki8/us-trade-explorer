"""Exact-integer reconciliation for an explicitly comparable control group.

The caller must establish matching basis, period, classification and geography,
and provide an approved leaf inventory. This helper does not invent that evidence.
"""
import re

def reconcile_exact(rows, expected_partner_codes, control):
    if not expected_partner_codes or not isinstance(control,str) or not re.fullmatch(r'(0|[1-9]\d{0,23})',control):
        raise ValueError('Invalid control or coverage inventory')
    seen=set();total=0
    for row in rows:
        code=row['partnerCode'];value=row['value']
        if code in seen:raise ValueError('Duplicate reconciliation input')
        if not isinstance(value,str) or not re.fullmatch(r'(0|[1-9]\d{0,23})',value):raise ValueError('Unavailable or invalid input')
        seen.add(code);total+=int(value)
    if seen!=set(expected_partner_codes):raise ValueError('Incomplete or unexpected reconciliation coverage')
    residual=total-int(control)
    if residual:raise ValueError('Exact control reconciliation failed')
    return {'total':str(total),'control':control,'residual':'0','count':len(rows)}
