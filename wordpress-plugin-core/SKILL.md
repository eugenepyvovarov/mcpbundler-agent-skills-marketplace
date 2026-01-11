---
name: wordpress-plugin-core
description: |
  Build secure WordPress plugins with hooks, database interactions, Settings API, custom post types, and REST API. Covers Simple, OOP, and PSR-4 architecture patterns plus the Security Trinity.

  Use when creating plugins or troubleshooting SQL injection, XSS, CSRF vulnerabilities, or plugin activation errors.
user-invocable: true
---

# WordPress Plugin Development (Core)

**Last Updated**: 2026-01-09
**Latest Versions**: WordPress 6.8+, PHP 8.0+ recommended
**Dependencies**: None (WordPress 5.9+, PHP 7.4+ minimum)

---

## Quick Start

**Architecture Patterns**: Simple (functions only, <5 functions) | OOP (medium plugins) | PSR-4 (modern/large, recommended 2025+)

**Plugin Header** (only Plugin Name required):
```php
<?php
/**
 * Plugin Name: My Plugin
 * Version: 1.0.0
 * Requires at least: 5.9
 * Requires PHP: 7.4
 * Text Domain: my-plugin
 */

if ( ! defined( 'ABSPATH' ) ) exit;
```

**Security Foundation** (5 essentials before writing functionality):
```php
// 1. Unique Prefix
define( 'MYPL_VERSION', '1.0.0' );
function mypl_init() { /* code */ }
add_action( 'init', 'mypl_init' );

// 2. ABSPATH Check (every PHP file)
if ( ! defined( 'ABSPATH' ) ) exit;

// 3. Nonces
wp_nonce_field( 'mypl_action', 'mypl_nonce' );
wp_verify_nonce( $_POST['mypl_nonce'], 'mypl_action' );

// 4. Sanitize Input, Escape Output
$clean = sanitize_text_field( $_POST['input'] );
echo esc_html( $output );

// 5. Prepared Statements
global $wpdb;
$wpdb->get_results( $wpdb->prepare( "SELECT * FROM {$wpdb->prefix}table WHERE id = %d", $id ) );
```

---

## Security Foundation (Detailed)

### Unique Prefix (4-5 chars minimum)
Apply to: functions, classes, constants, options, transients, meta keys. Avoid: `wp_`, `__`, `_`.

```php
function mypl_function() {}  // ✅
class MyPL_Class {}          // ✅
function init() {}           // ❌ Will conflict
```

### Capabilities Check (Not is_admin())
```php
// ❌ WRONG - Security hole
if ( is_admin() ) { /* delete data */ }

// ✅ CORRECT
if ( current_user_can( 'manage_options' ) ) { /* delete data */ }
```

Common: `manage_options` (Admin), `edit_posts` (Editor/Author), `read` (Subscriber)

### Security Trinity (Input → Processing → Output)
```php
// Sanitize INPUT
$name = sanitize_text_field( $_POST['name'] );
$email = sanitize_email( $_POST['email'] );
$html = wp_kses_post( $_POST['content'] );  // Allow safe HTML
$ids = array_map( 'absint', $_POST['ids'] );

// Validate LOGIC
if ( ! is_email( $email ) ) wp_die( 'Invalid' );

// Escape OUTPUT
echo esc_html( $name );
echo '<a href="' . esc_url( $url ) . '">';
echo '<div class="' . esc_attr( $class ) . '">';
```

### Nonces (CSRF Protection)
```php
// Form
<?php wp_nonce_field( 'mypl_action', 'mypl_nonce' ); ?>
if ( ! wp_verify_nonce( $_POST['mypl_nonce'], 'mypl_action' ) ) wp_die( 'Failed' );

// AJAX
check_ajax_referer( 'mypl-ajax-nonce', 'nonce' );
wp_localize_script( 'mypl-script', 'mypl_ajax_object', array(
    'ajaxurl' => admin_url( 'admin-ajax.php' ),
    'nonce'   => wp_create_nonce( 'mypl-ajax-nonce' ),
) );
```

### Prepared Statements
```php
// ❌ SQL Injection
$wpdb->get_results( "SELECT * FROM table WHERE id = {$_GET['id']}" );

// ✅ Prepared (%s=String, %d=Integer, %f=Float)
$wpdb->get_results( $wpdb->prepare( "SELECT * FROM {$wpdb->prefix}table WHERE id = %d", $_GET['id'] ) );

// LIKE Queries
$search = '%' . $wpdb->esc_like( $term ) . '%';
$wpdb->get_results( $wpdb->prepare( "... WHERE title LIKE %s", $search ) );
```

---

## Critical Rules

### Always Do

✅ **Use unique prefix** (4-5 chars) for all global code (functions, classes, options, transients)
✅ **Add ABSPATH check** to every PHP file: `if ( ! defined( 'ABSPATH' ) ) exit;`
✅ **Check capabilities** (`current_user_can()`) not just `is_admin()`
✅ **Verify nonces** for all forms and AJAX requests
✅ **Use $wpdb->prepare()** for all database queries with user input
✅ **Sanitize input** with `sanitize_*()` functions before saving
✅ **Escape output** with `esc_*()` functions before displaying
✅ **Flush rewrite rules** on activation when registering custom post types
✅ **Use uninstall.php** for permanent cleanup (not deactivation hook)
✅ **Follow WordPress Coding Standards** (tabs for indentation, Yoda conditions)

### Never Do

❌ **Never use extract()** - Creates security vulnerabilities
❌ **Never trust $_POST/$_GET** without sanitization
❌ **Never concatenate user input into SQL** - Always use prepare()
❌ **Never use `is_admin()` alone** for permission checks
❌ **Never output unsanitized data** - Always escape
❌ **Never use generic function/class names** - Always prefix
❌ **Never use short PHP tags** `<?` or `<?=` - Use `<?php` only
❌ **Never delete user data on deactivation** - Only on uninstall
❌ **Never register uninstall hook repeatedly** - Only once on activation
❌ **Never use `register_uninstall_hook()` in main flow** - Use uninstall.php instead

---

## Known Issues Prevention

This skill prevents **20** documented issues:

### Issue #1: SQL Injection
**Error**: Database compromised via unescaped user input
**Source**: https://patchstack.com/articles/sql-injection/ (15% of all vulnerabilities)
**Why It Happens**: Direct concatenation of user input into SQL queries
**Prevention**: Always use `$wpdb->prepare()` with placeholders

```php
// VULNERABLE
$wpdb->query( "DELETE FROM {$wpdb->prefix}table WHERE id = {$_GET['id']}" );

// SECURE
$wpdb->query( $wpdb->prepare( "DELETE FROM {$wpdb->prefix}table WHERE id = %d", $_GET['id'] ) );
```

### Issue #2: XSS (Cross-Site Scripting)
**Error**: Malicious JavaScript executed in user browsers
**Source**: https://patchstack.com (35% of all vulnerabilities)
**Why It Happens**: Outputting unsanitized user data to HTML
**Prevention**: Always escape output with context-appropriate function

```php
// VULNERABLE
echo $_POST['name'];
echo '<div class="' . $_POST['class'] . '">';

// SECURE
echo esc_html( $_POST['name'] );
echo '<div class="' . esc_attr( $_POST['class'] ) . '">';
```

### Issue #3: CSRF (Cross-Site Request Forgery)
**Error**: Unauthorized actions performed on behalf of users
**Source**: https://blog.nintechnet.com/25-wordpress-plugins-vulnerable-to-csrf-attacks/
**Why It Happens**: No verification that requests originated from your site
**Prevention**: Use nonces with `wp_nonce_field()` and `wp_verify_nonce()`

```php
// VULNERABLE
if ( $_POST['action'] == 'delete' ) {
    delete_user( $_POST['user_id'] );
}

// SECURE
if ( ! wp_verify_nonce( $_POST['nonce'], 'mypl_delete_user' ) ) {
    wp_die( 'Security check failed' );
}
delete_user( absint( $_POST['user_id'] ) );
```

### Issue #4: Missing Capability Checks
**Error**: Regular users can access admin functions
**Source**: WordPress Security Review Guidelines
**Why It Happens**: Using `is_admin()` instead of `current_user_can()`
**Prevention**: Always check capabilities, not just admin context

```php
// VULNERABLE
if ( is_admin() ) {
    // Any logged-in user can trigger this
}

// SECURE
if ( current_user_can( 'manage_options' ) ) {
    // Only administrators can trigger this
}
```

### Issue #5: Direct File Access
**Error**: PHP files executed outside WordPress context
**Source**: WordPress Plugin Handbook
**Why It Happens**: No ABSPATH check at top of file
**Prevention**: Add ABSPATH check to every PHP file

```php
// Add to top of EVERY PHP file
if ( ! defined( 'ABSPATH' ) ) {
    exit;
}
```

### Issue #6: Prefix Collision
**Error**: Functions/classes conflict with other plugins
**Source**: WordPress Coding Standards
**Why It Happens**: Generic names without unique prefix
**Prevention**: Use 4-5 character prefix on ALL global code

```php
// CAUSES CONFLICTS
function init() {}
class Settings {}
add_option( 'api_key', $value );

// SAFE
function mypl_init() {}
class MyPL_Settings {}
add_option( 'mypl_api_key', $value );
```

### Issue #7: Rewrite Rules Not Flushed
**Error**: Custom post types return 404 errors
**Source**: WordPress Plugin Handbook
**Why It Happens**: Forgot to flush rewrite rules after registering CPT
**Prevention**: Flush on activation, clear on deactivation

```php
function mypl_activate() {
    mypl_register_cpt();
    flush_rewrite_rules();
}
register_activation_hook( __FILE__, 'mypl_activate' );

function mypl_deactivate() {
    flush_rewrite_rules();
}
register_deactivation_hook( __FILE__, 'mypl_deactivate' );
```

### Issue #8: Transients Not Cleaned
**Error**: Database accumulates expired transients
**Source**: WordPress Transients API Documentation
**Why It Happens**: No cleanup on uninstall
**Prevention**: Delete transients in uninstall.php

```php
// uninstall.php
if ( ! defined( 'WP_UNINSTALL_PLUGIN' ) ) {
    exit;
}

global $wpdb;
$wpdb->query( "DELETE FROM {$wpdb->options} WHERE option_name LIKE '_transient_mypl_%'" );
$wpdb->query( "DELETE FROM {$wpdb->options} WHERE option_name LIKE '_transient_timeout_mypl_%'" );
```

### Issue #9: Scripts Loaded Everywhere
**Error**: Performance degraded by unnecessary asset loading
**Source**: WordPress Performance Best Practices
**Why It Happens**: Enqueuing scripts/styles without conditional checks
**Prevention**: Only load assets where needed

```php
// BAD - Loads on every page
add_action( 'wp_enqueue_scripts', function() {
    wp_enqueue_script( 'mypl-script', $url );
} );

// GOOD - Only loads on specific page
add_action( 'wp_enqueue_scripts', function() {
    if ( is_page( 'my-page' ) ) {
        wp_enqueue_script( 'mypl-script', $url, array( 'jquery' ), '1.0', true );
    }
} );
```

### Issue #10: Missing Sanitization on Save
**Error**: Malicious data stored in database
**Source**: WordPress Data Validation
**Why It Happens**: Saving $_POST data without sanitization
**Prevention**: Always sanitize before saving

```php
// VULNERABLE
update_option( 'mypl_setting', $_POST['value'] );

// SECURE
update_option( 'mypl_setting', sanitize_text_field( $_POST['value'] ) );
```

### Issue #11: Incorrect LIKE Queries
**Error**: SQL syntax errors or injection vulnerabilities
**Source**: WordPress $wpdb Documentation
**Why It Happens**: LIKE wildcards not escaped properly
**Prevention**: Use `$wpdb->esc_like()`

```php
// WRONG
$search = '%' . $term . '%';

// CORRECT
$search = '%' . $wpdb->esc_like( $term ) . '%';
$results = $wpdb->get_results( $wpdb->prepare( "... WHERE title LIKE %s", $search ) );
```

### Issue #12: Using extract()
**Error**: Variable collision and security vulnerabilities
**Source**: WordPress Coding Standards
**Why It Happens**: extract() creates variables from array keys
**Prevention**: Never use extract(), access array elements directly

```php
// DANGEROUS
extract( $_POST );
// Now $any_array_key becomes a variable

// SAFE
$name = isset( $_POST['name'] ) ? sanitize_text_field( $_POST['name'] ) : '';
```

### Issue #13: Missing Permission Callback in REST API
**Error**: Endpoints accessible to everyone
**Source**: WordPress REST API Handbook
**Why It Happens**: No `permission_callback` specified
**Prevention**: Always add permission_callback

```php
// VULNERABLE
register_rest_route( 'myplugin/v1', '/data', array(
    'callback' => 'my_callback',
) );

// SECURE
register_rest_route( 'myplugin/v1', '/data', array(
    'callback'            => 'my_callback',
    'permission_callback' => function() {
        return current_user_can( 'edit_posts' );
    },
) );
```

### Issue #14: Uninstall Hook Registered Repeatedly
**Error**: Option written on every page load
**Source**: WordPress Plugin Handbook
**Why It Happens**: register_uninstall_hook() called in main flow
**Prevention**: Use uninstall.php file instead

```php
// BAD - Runs on every page load
register_uninstall_hook( __FILE__, 'mypl_uninstall' );

// GOOD - Use uninstall.php file (preferred method)
// Create uninstall.php in plugin root
```

### Issue #15: Data Deleted on Deactivation
**Error**: Users lose data when temporarily disabling plugin
**Source**: WordPress Plugin Development Best Practices
**Why It Happens**: Confusion about deactivation vs uninstall
**Prevention**: Only delete data in uninstall.php, never on deactivation

```php
// WRONG - Deletes user data on deactivation
register_deactivation_hook( __FILE__, function() {
    delete_option( 'mypl_user_settings' );
} );

// CORRECT - Only clear temporary data on deactivation
register_deactivation_hook( __FILE__, function() {
    delete_transient( 'mypl_cache' );
} );

// CORRECT - Delete all data in uninstall.php
```

### Issue #16: Using Deprecated Functions
**Error**: Plugin breaks on WordPress updates
**Source**: WordPress Deprecated Functions List
**Why It Happens**: Using functions removed in newer WordPress versions
**Prevention**: Enable WP_DEBUG during development

```php
// In wp-config.php (development only)
define( 'WP_DEBUG', true );
define( 'WP_DEBUG_LOG', true );
define( 'WP_DEBUG_DISPLAY', false );
```

### Issue #17: Text Domain Mismatch
**Error**: Translations don't load
**Source**: WordPress Internationalization
**Why It Happens**: Text domain doesn't match plugin slug
**Prevention**: Use exact plugin slug everywhere

```php
// Plugin header
// Text Domain: my-plugin

// In code - MUST MATCH EXACTLY
__( 'Text', 'my-plugin' );
_e( 'Text', 'my-plugin' );
```

### Issue #18: Missing Plugin Dependencies
**Error**: Fatal error when required plugin is inactive
**Source**: WordPress Plugin Dependencies
**Why It Happens**: No check for required plugins
**Prevention**: Check for dependencies on plugins_loaded

```php
add_action( 'plugins_loaded', function() {
    if ( ! class_exists( 'WooCommerce' ) ) {
        add_action( 'admin_notices', function() {
            echo '<div class="error"><p>My Plugin requires WooCommerce.</p></div>';
        } );
        return;
    }
    // Initialize plugin
} );
```

### Issue #19: Autosave Triggering Meta Save
**Error**: Meta saved multiple times, performance issues
**Source**: WordPress Post Meta
**Why It Happens**: No autosave check in save_post hook
**Prevention**: Check for DOING_AUTOSAVE constant

```php
add_action( 'save_post', function( $post_id ) {
    if ( defined( 'DOING_AUTOSAVE' ) && DOING_AUTOSAVE ) {
        return;
    }

    // Safe to save meta
} );
```

### Issue #20: admin-ajax.php Performance
**Error**: Slow AJAX responses
**Source**: https://deliciousbrains.com/comparing-wordpress-rest-api-performance-admin-ajax-php/
**Why It Happens**: admin-ajax.php loads entire WordPress core
**Prevention**: Use REST API for new projects (10x faster)

```php
// OLD: admin-ajax.php (still works but slower)
add_action( 'wp_ajax_mypl_action', 'mypl_ajax_handler' );

// NEW: REST API (10x faster, recommended)
add_action( 'rest_api_init', function() {
    register_rest_route( 'myplugin/v1', '/endpoint', array(
        'methods'             => 'POST',
        'callback'            => 'mypl_rest_handler',
        'permission_callback' => function() {
            return current_user_can( 'edit_posts' );
        },
    ) );
} );
```

---

## Plugin Architecture Patterns

### Simple (Functions Only)
Small plugins (<5 functions):
```php
function mypl_init() { /* code */ }
add_action( 'init', 'mypl_init' );
```

### OOP (Singleton)
Medium plugins:
```php
class MyPL_Plugin {
    private static $instance = null;
    public static function get_instance() {
        if ( null === self::$instance ) self::$instance = new self();
        return self::$instance;
    }
    private function __construct() {
        add_action( 'init', array( $this, 'init' ) );
    }
}
MyPL_Plugin::get_instance();
```

### PSR-4 (Modern, Recommended 2025+)
Large/team plugins:
```
my-plugin/
├── my-plugin.php
├── composer.json → "psr-4": { "MyPlugin\\": "src/" }
└── src/Admin.php

// my-plugin.php
require_once __DIR__ . '/vendor/autoload.php';
use MyPlugin\Admin;
new Admin();
```

---

## Common Patterns

**Custom Post Types** (CRITICAL: Flush rewrite rules on activation):
```php
register_post_type( 'book', array( 'public' => true, 'show_in_rest' => true ) );
register_activation_hook( __FILE__, function() {
    mypl_register_cpt();
    flush_rewrite_rules();
} );
```

**Custom Taxonomies**:
```php
register_taxonomy( 'genre', 'book', array( 'hierarchical' => true, 'show_in_rest' => true ) );
```

**Meta Boxes**:
```php
add_meta_box( 'book_details', 'Book Details', 'mypl_meta_box_html', 'book' );
// Save: Check nonce, DOING_AUTOSAVE, current_user_can('edit_post')
update_post_meta( $post_id, '_book_isbn', sanitize_text_field( $_POST['book_isbn'] ) );
```

**Settings API**:
```php
register_setting( 'mypl_options', 'mypl_api_key', array( 'sanitize_callback' => 'sanitize_text_field' ) );
add_settings_section( 'mypl_section', 'API Settings', 'callback', 'my-plugin' );
add_settings_field( 'mypl_api_key', 'API Key', 'field_callback', 'my-plugin', 'mypl_section' );
```

**REST API** (10x faster than admin-ajax.php):
```php
register_rest_route( 'myplugin/v1', '/data', array(
    'methods'             => 'POST',
    'callback'            => 'mypl_rest_callback',
    'permission_callback' => fn() => current_user_can( 'edit_posts' ),
) );
```

**AJAX** (Legacy, use REST API for new projects):
```php
add_action( 'wp_ajax_mypl_action', 'mypl_ajax_handler' );
check_ajax_referer( 'mypl-ajax-nonce', 'nonce' );
wp_send_json_success( array( 'message' => 'Success' ) );
```

**Custom Tables**:
```php
global $wpdb;
$sql = "CREATE TABLE {$wpdb->prefix}mypl_data (id bigint AUTO_INCREMENT PRIMARY KEY, ...)";
require_once ABSPATH . 'wp-admin/includes/upgrade.php';
dbDelta( $sql );
```

**Transients** (Caching):
```php
$data = get_transient( 'mypl_data' );
if ( false === $data ) {
    $data = expensive_operation();
    set_transient( 'mypl_data', $data, 12 * HOUR_IN_SECONDS );
}
```

---

## Bundled Resources

**Templates**: `plugin-simple/`, `plugin-oop/`, `plugin-psr4/`, `examples/meta-box.php`, `examples/settings-page.php`, `examples/custom-post-type.php`, `examples/rest-endpoint.php`, `examples/ajax-handler.php`

**Scripts**: `scaffold-plugin.sh`, `check-security.sh`, `validate-headers.sh`

**References**: `security-checklist.md`, `hooks-reference.md`, `sanitization-guide.md`, `wpdb-patterns.md`, `common-errors.md`

---

## Advanced Topics

**i18n** (Internationalization):
```php
load_plugin_textdomain( 'my-plugin', false, dirname( plugin_basename( __FILE__ ) ) . '/languages' );
__( 'Text', 'my-plugin' );  // Return translated
_e( 'Text', 'my-plugin' );  // Echo translated
esc_html__( 'Text', 'my-plugin' );  // Translate + escape
```

**WP-CLI**:
```php
if ( defined( 'WP_CLI' ) && WP_CLI ) {
    WP_CLI::add_command( 'mypl', 'MyPL_CLI_Command' );
}
```

**Cron Events**:
```php
register_activation_hook( __FILE__, fn() => wp_schedule_event( time(), 'daily', 'mypl_daily_task' ) );
register_deactivation_hook( __FILE__, fn() => wp_clear_scheduled_hook( 'mypl_daily_task' ) );
add_action( 'mypl_daily_task', 'mypl_do_daily_task' );
```

**Plugin Dependencies**:
```php
if ( ! class_exists( 'WooCommerce' ) ) {
    deactivate_plugins( plugin_basename( __FILE__ ) );
    add_action( 'admin_notices', fn() => echo '<div class="error"><p>Requires WooCommerce</p></div>' );
}
```

---

## Distribution & Auto-Updates

**GitHub Auto-Updates** (Plugin Update Checker by YahnisElsts):
```php
// 1. Install: git submodule add https://github.com/YahnisElsts/plugin-update-checker.git
// 2. Add to main plugin file
require plugin_dir_path( __FILE__ ) . 'plugin-update-checker/plugin-update-checker.php';
use YahnisElsts\PluginUpdateChecker\v5\PucFactory;

$updateChecker = PucFactory::buildUpdateChecker(
    'https://github.com/yourusername/your-plugin/',
    __FILE__,
    'your-plugin-slug'
);
$updateChecker->getVcsApi()->enableReleaseAssets();  // Use GitHub Releases

// Private repos: Define token in wp-config.php
if ( defined( 'YOUR_PLUGIN_GITHUB_TOKEN' ) ) {
    $updateChecker->setAuthentication( YOUR_PLUGIN_GITHUB_TOKEN );
}
```

**Deployment**:
```bash
git tag 1.0.1 && git push origin main && git push origin 1.0.1
# Create GitHub Release with ZIP (exclude .git, tests)
```

**Alternatives**: Git Updater (no coding), Custom Update Server (full control), Freemius (commercial)

**Security**: Use HTTPS, never hardcode tokens, validate licenses, rate limit update checks

**CRITICAL**: ZIP must contain plugin folder: `plugin.zip/my-plugin/my-plugin.php`

**Resources**: See `references/github-auto-updates.md`, `examples/github-updater.php`

---

## Dependencies

**Required**:
- WordPress 5.9+ (recommend 6.7+)
- PHP 7.4+ (recommend 8.0+)

**Optional**:
- Composer 2.0+ - For PSR-4 autoloading
- WP-CLI 2.0+ - For command-line plugin management
- Query Monitor - For debugging and performance analysis

---

## Official Documentation

- **WordPress Plugin Handbook**: https://developer.wordpress.org/plugins/
- **WordPress Coding Standards**: https://developer.wordpress.org/coding-standards/
- **WordPress REST API**: https://developer.wordpress.org/rest-api/
- **WordPress Database Class ($wpdb)**: https://developer.wordpress.org/reference/classes/wpdb/
- **WordPress Security**: https://developer.wordpress.org/apis/security/
- **Settings API**: https://developer.wordpress.org/plugins/settings/settings-api/
- **Custom Post Types**: https://developer.wordpress.org/plugins/post-types/
- **Transients API**: https://developer.wordpress.org/apis/transients/
- **Context7 Library ID**: /websites/developer_wordpress

---

## Troubleshooting

**Fatal Error**: Enable WP_DEBUG, check wp-content/debug.log, verify prefixed names, check dependencies

**404 on CPT**: Flush rewrite rules via Settings → Permalinks → Save

**Nonce Fails**: Check nonce name/action match, verify not expired (24h default)

**AJAX Returns 0/-1**: Verify action name matches `wp_ajax_{action}`, check nonce sent/verified

**HTML Stripped**: Use `wp_kses_post()` not `sanitize_text_field()` for safe HTML

**Query Fails**: Use `$wpdb->prepare()`, check `$wpdb->prefix`, verify syntax

---

## Complete Setup Checklist

Use this checklist to verify your plugin:

- [ ] Plugin header complete with all fields
- [ ] ABSPATH check at top of every PHP file
- [ ] All functions/classes use unique prefix
- [ ] All forms have nonce verification
- [ ] All user input is sanitized
- [ ] All output is escaped
- [ ] All database queries use $wpdb->prepare()
- [ ] Capability checks (not just is_admin())
- [ ] Custom post types flush rewrite rules on activation
- [ ] Deactivation hook only clears temporary data
- [ ] uninstall.php handles permanent cleanup
- [ ] Text domain matches plugin slug
- [ ] Scripts/styles only load where needed
- [ ] WP_DEBUG enabled during development
- [ ] Tested with Query Monitor for performance
- [ ] No deprecated function warnings
- [ ] Works with latest WordPress version

---

**Questions? Issues?**

1. Check `references/common-errors.md` for extended troubleshooting
2. Verify all steps in the security foundation
3. Check official docs: https://developer.wordpress.org/plugins/
4. Enable WP_DEBUG and check debug.log
5. Use Query Monitor plugin to debug hooks and queries
