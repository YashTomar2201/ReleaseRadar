-- Topic reference data from config/topics_codebook.md (v1). Category
-- groups topics for dashboard filtering/coloring.
select * from (
    values
        ('payment_failure',   'Payment Failure',        'Payments',    true),
        ('refund_delay',      'Refund Delay',            'Payments',    true),
        ('login_otp_kyc',     'Login / OTP / KYC',       'Account',     true),
        ('account_blocked',   'Account Blocked',         'Account',     true),
        ('bank_linking',      'Bank Linking',             'Account',     true),
        ('app_performance',   'App Performance',          'Product',     true),
        ('ui_ux',             'UI/UX',                    'Product',     true),
        ('customer_support',  'Customer Support',         'Support',     true),
        ('fraud_security',    'Fraud & Security',         'Trust',       true),
        ('rewards_cashback',  'Rewards & Cashback',       'Incentives',  true),
        ('fees_charges',      'Fees & Charges',           'Incentives',  true),
        ('ads_spam',          'Ads & Spam',                'Product',     true),
        ('bills_recharge',    'Bills & Recharge',         'Features',    true),
        ('autopay_mandates',  'Autopay / Mandates',       'Features',    true),
        ('investments_gold',  'Investments & Gold',       'Features',    true),
        ('travel_booking',    'Travel Booking',           'Features',    true),
        ('general_praise',    'General Praise',           'Sentiment',   false),
        ('uninformative',     'Uninformative',            'Sentiment',   false)
) as t(topic_key, display_name, category, is_actionable_issue)
