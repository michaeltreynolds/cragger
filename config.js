// ============================================
// STUDENT CONFIGURATION FILE
// ============================================
// Students: Replace these values with your own Supabase project credentials
// You can find these in your Supabase project settings under "API"

const SUPABASE_CONFIG = {
    // TODO: Replace with your Supabase project URL
    // Example: 'https://xyzcompany.supabase.co'
    url: 'https://ebmgbfsjelwaglysbqym.supabase.co',

    // TODO: Replace with your Supabase anon/public key
    // This is safe to expose in client-side code when using RLS
    anonKey: 'sb_publishable_wdeYV7W3ywQTHo9ZJK8x6g_WCwrfTUE'
};

// Validate configuration
if (SUPABASE_CONFIG.url === 'YOUR_SUPABASE_URL_HERE' ||
    SUPABASE_CONFIG.anonKey === 'YOUR_SUPABASE_ANON_KEY_HERE') {
    console.warn('⚠️ Please configure your Supabase credentials in config.js');
}
