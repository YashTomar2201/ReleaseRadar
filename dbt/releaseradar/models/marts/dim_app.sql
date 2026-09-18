-- Static app reference data (verified against the Play Store, Phase 0,
-- 2026-09-17). Small enough for inline VALUES rather than a seed file.
select * from (
    values
        ('phonepe', 'PhonePe', true,  'com.phonepe.app', 500000000, 4.4, '14.2M'),
        ('gpay',    'Google Pay', false, 'com.google.android.apps.nbu.paisa.user', 1000000000, 4.3, '11.4M'),
        ('paytm',   'Paytm', false, 'net.one97.paytm', 500000000, 4.7, '24.2M')
) as t(app_key, display_name, is_focus_app, play_store_id, downloads_verified, rating_verified, reviews_verified_label)
