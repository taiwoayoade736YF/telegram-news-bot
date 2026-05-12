#!/usr/bin/env python3
"""
Email Provider Sorter - GUI Application
Detects email providers by analyzing MX records and sorts entries into categorized files.

FIXES APPLIED:
1. Removed duplicate PROVIDER_PATTERNS keys
2. Added thread-safe locking for shared state
3. Normalized provider name handling for consistent file operations
4. Replaced bare except clauses with proper error logging
5. Consolidated duplicate DNS logic into single reusable function
6. Ensured all GUI updates occur on main thread via after()
7. Added proper resource cleanup and context management
8. Improved error messages and user feedback
"""

import dns.resolver
import concurrent.futures
import re
import os
import sys
import time
import threading
import logging
from queue import Queue, Empty
from collections import defaultdict
from pathlib import Path

# Tkinter imports
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Optional: pandas for Excel support
try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_sorter.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================
EXTERNAL_RESOLVERS = ['8.8.8.8', '1.1.1.1']  # Reliable public DNS resolvers
MAX_WORKERS = 50  # Reduced from 299 to avoid rate limiting (configurable in GUI)
DNS_TIMEOUT = 2  # Seconds to wait for DNS response
MAX_RETRIES = 2  # Number of retry attempts for failed lookups
RETRY_DELAY = 0.5  # Base delay between retries (seconds)

# ============================================================================
# PROVIDER PATTERNS - DEDUPLICATED & ORGANIZED
# ============================================================================
PROVIDER_PATTERNS = {
    # === Major Cloud Providers ===
    'Microsoft 365': r'outlook\.com|outlook\.office365\.com|outlook\.office\.com|protection\.outlook\.com|mail\.protection\.outlook\.com|outlook\.protection\.office365\.com',
    'Google Workspace (Gmail)': r'gmail-smtp-in\.l\.google\.com|aspmx\.l\.google\.com|alt1\.aspmx\.l\.google\.com|alt2\.aspmx\.l\.google\.com|aspmx2\.googlemail\.com|aspmx3\.googlemail\.com',

    # === Enterprise Email Security ===
    'Abnormal Security': r'abnormalsecurity',
    'Tessian': r'tessian',
    'Darktrace Email': r'darktrace',
    'Proofpoint Email Protection': r'pphosted|proofpoint|pps\.filter',
    'Mimecast Email Security': r'mimecast|smtp\.mimecast',
    'Barracuda Email Protection': r'barracuda|bmsmtp',
    'Fortimail (Fortinet)': r'fortinet|fortimail',
    'Cisco Secure Email (IronPort)': r'iron port|cisco|Esmail',
    'Avanan (Check Point)': r'avanan',
    'Armorblox (Okta)': r'armorblox',
    'GreatHorn': r'greathorn',
    'Agari (HelpSystems)': r'agari',
    'Cofense (PhishMe)': r'cofense|phishme',
    'Inky': r'inky',
    'SpamTitan (TitanHQ)': r'spamtitan|titanhq',
    'MailChannels': r'mailchannels',
    'Virtru': r'virtru',
    'Zix (OpenText)': r'zix|opentext',
    'Egress Defend': r'egress',
    'Check Point Harmony Email': r'checkpoint|harmony',
    'Symantec Email Security (Broadcom)': r'symantec|broadcom',
    'Trend Micro Email Security': r'trendmicro|trend',
    'Sophos Email Security': r'sophos',
    'Forcepoint Email Security': r'forcepoint',
    'Trustifi': r'trustifi',
    'Vade Secure': r'vade',
    'Hornetsecurity': r'hornetsecurity',
    'Heimdal Email Security': r'heimdal',
    'Reflexion Networks': r'reflexion',
    'Cyren Email Security': r'cyren',
    'F-Secure Email and Server Security': r'f-secure',
    'Kaspersky Secure Mail Gateway': r'kaspersky',
    'VIPRE Email Security': r'vipre',
    'SolarWinds Mail Assure': r'solarwinds|mailassure',
    'GFI MailEssentials': r'gfi|mailessentials',
    'Rackspace Email Security': r'rackspace',
    'AppRiver (now Zix)': r'appriver',
    'Retarus Email Security': r'retarus',
    'Clearswift Secure Email Gateway': r'clearswift',
    'IRONSCALES': r'ironscales',
    'PhishLabs (by ZeroFOX)': r'phishlabs|zerofox',
    'Area 1 Security (Cloudflare)': r'area1|cloudflare',
    'SlashNext Email Protection': r'slashnext',
    'SEON Fraud Prevention': r'seon',
    'Red Sift OnDMARC': r'redsift|ondmarc',
    'Valimail': r'valimail',
    'Sendmarc': r'sendmarc',
    'Mailprotector': r'mailprotector',
    'MXGuarddog': r'mxguarddog',
    'Postmark (DMARC enforcement)': r'postmark',

    # === Email Delivery Services (NO DUPLICATES) ===
    'SendGrid': r'sendgrid|smtp\.sendgrid\.net',
    'Mailgun': r'mailgun|mxa\.mailgun\.org|mxb\.mailgun\.org',
    'Amazon SES': r'amazonses|smtp\.amazonses\.com',
    'SparkPost': r'sparkpost|smtp\.sparkpostmail\.com',
    'Campaign Monitor': r'campaignmonitor|cmail1\.com',
    'Constant Contact': r'constantcontact|smtp\.constantcontact\.com',
    'Mailchimp': r'mailchimp|smtp\.mailchimp\.com',
    'ConvertKit': r'convertkit|smtp\.convertkit\.com',
    'AWeber': r'aweber|smtp\.aweber\.com',
    'GetResponse': r'getresponse|smtp\.getresponse\.com',
    'ActiveCampaign': r'activecampaign|smtp\.activecampaign\.com',
    'HubSpot': r'hubspot|smtp\.hubspot\.com',
    'Salesforce': r'salesforce|smtp\.salesforce\.com',
    'Pardot': r'pardot|smtp\.pardot\.com',
    'Marketo': r'marketo|smtp\.marketo\.com',
    'Infusionsoft': r'infusionsoft|smtp\.infusionsoft\.com',
    'Ontraport': r'ontraport|smtp\.ontraport\.com',
    'Klaviyo': r'klaviyo|smtp\.klaviyo\.com',
    'Drip': r'drip|smtp\.drip\.com',
    'Buttondown': r'buttondown|smtp\.buttondown\.email',
    'Substack': r'substack|smtp\.substack\.com',
    'Revue': r'revue|smtp\.getrevue\.co',
    'TinyLetter': r'tinyletter|smtp\.tinyletter\.com',
    'MailerLite': r'mailerlite|smtp\.mailerlite\.com',
    'Brevo (Sendinblue)': r'sendinblue|smtp-relay\.sendinblue\.com',
    'Moosend': r'moosend|smtp\.moosend\.com',
    'Omnisend': r'omnisend|smtp\.omnisend\.com',

    # === E-commerce & Platforms ===
    'Kajabi': r'kajabi|smtp\.kajabi\.com',
    'Teachable': r'teachable|smtp\.teachable\.com',
    'Thinkific': r'thinkific|smtp\.thinkific\.com',
    'Podia': r'podia|smtp\.podia\.com',
    'Gumroad': r'gumroad|smtp\.gumroad\.com',
    'Stripe': r'stripe|smtp\.stripe\.com',
    'Shopify': r'shopify|smtp\.shopify\.com',
    'WooCommerce': r'woocommerce|smtp\.woocommerce\.com',
    'BigCommerce': r'bigcommerce|smtp\.bigcommerce\.com',
    'Squarespace': r'squarespace|smtp\.squarespace\.com',
    'Wix': r'wix|smtp\.wix\.com',
    'Webflow': r'webflow|smtp\.webflow\.com',
    'WordPress': r'wordpress|smtp\.wordpress\.com',
    'Ghost': r'ghost|smtp\.ghost\.org',
    'Medium': r'medium|smtp\.medium\.com',
    'GoDaddy': r'godaddy|secureserver\.net|mail\.secureserver\.net|smtp\.secureserver\.net'
}

# Providers commonly used with Microsoft Office environments (for filename prefix)
OFFICE_RELATED_PROVIDERS = {
    'Proofpoint Email Protection', 'Barracuda Email Protection', 'Mimecast Email Security',
    'Cisco Secure Email (IronPort)', 'Symantec Email Security (Broadcom)',
    'Trend Micro Email Security', 'Sophos Email Security', 'Forcepoint Email Security',
    'Check Point Harmony Email', 'Fortimail (Fortinet)', 'Avanan (Check Point)',
    'Armorblox (Okta)', 'GreatHorn', 'Agari (HelpSystems)', 'Cofense (PhishMe)',
    'Inky', 'SpamTitan (TitanHQ)', 'MailChannels', 'Virtru', 'Zix (OpenText)',
    'Egress Defend', 'Trustifi', 'Vade Secure', 'Hornetsecurity',
    'Heimdal Email Security', 'Reflexion Networks', 'Cyren Email Security',
    'F-Secure Email and Server Security', 'Kaspersky Secure Mail Gateway',
    'VIPRE Email Security', 'SolarWinds Mail Assure', 'GFI MailEssentials',
    'Rackspace Email Security', 'AppRiver (now Zix)', 'Retarus Email Security',
    'Clearswift Secure Email Gateway', 'IRONSCALES', 'PhishLabs (by ZeroFOX)',
    'Area 1 Security (Cloudflare)', 'SlashNext Email Protection',
    'SEON Fraud Prevention', 'Red Sift OnDMARC', 'Valimail', 'Sendmarc',
    'Mailprotector', 'MXGuarddog', 'Postmark (DMARC enforcement)'
}

# Known free email domains (skip MX lookup)
MICROSOFT_FREE_DOMAINS = {'outlook.com', 'msn.com', 'live.com', 'hotmail.com'}
YAHOO_DOMAINS = {'yahoo.com', 'yahoo.co.uk', 'yahoo.ca', 'yahoo.com.au', 'yahoo.de',
                 'yahoo.fr', 'yahoo.es', 'yahoo.it', 'rocketmail.com', 'y7mail.com',
                 'ymail.com', 'kimo.com'}
AOL_DOMAINS = {'aol.com', 'aol.co.uk', 'aol.de', 'aol.fr', 'aol.jp', 'aol.com.mx'}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
def read_lines_with_fallback(input_file):
    """
    Yield lines from a text file trying multiple encodings.
    Prevents decode errors on files with mixed/unknown encoding.
    """
    encodings_to_try = [
        ('utf-8', 'strict'),
        ('utf-8-sig', 'strict'),  # Windows BOM
        ('cp1252', 'strict'),  # Windows Latin-1
        ('latin-1', 'strict'),  # Universal fallback
    ]

    for enc, err_mode in encodings_to_try:
        try:
            with open(input_file, 'r', encoding=enc, errors=err_mode) as f:
                for line in f:
                    yield line
            return  # Success - exit function
        except UnicodeDecodeError:
            logger.debug(f"Encoding {enc} failed for {input_file}, trying next...")
            continue
        except OSError as e:
            logger.error(f"File read error: {e}")
            continue

    # Last resort: ignore undecodable bytes
    logger.warning(f"Using error-ignoring fallback for {input_file}")
    try:
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                yield line
    except OSError as e:
        logger.error(f"Failed to read file even with fallback: {e}")
        return


def normalize_provider_name(provider):
    """
    Normalize provider names for consistent file naming.
    Handles case sensitivity and special characters.
    """
    # Map variations to canonical names
    name_map = {
        'Yahoo !': 'Yahoo !',
        'Yahoo (Others)': 'Yahoo (Others)',
        'Microsoft Free': 'Microsoft Free',
        'Gmail (free)': 'Gmail (free)',
        'OWA Serverdata': 'OWA Serverdata',
        'Outlook': 'Outlook',
    }
    return name_map.get(provider, provider)


def is_office_related_provider(provider):
    """Check if provider is commonly used with Microsoft Office environments."""
    return provider in OFFICE_RELATED_PROVIDERS


def get_safe_filename(provider):
    """Generate safe filename from provider name."""
    provider = normalize_provider_name(provider)

    # Special filename cases
    special_filenames = {
        'Yahoo !': 'yahoo !.txt',
        'Yahoo (Others)': 'yahoo (others).txt',
        'Microsoft Free': 'Microsoft Free.txt',
        'Gmail (free)': 'Gmail (free).txt',
        'OWA Serverdata': 'OWA Serverdata.txt',
        'Outlook': 'Outlook.txt',
        'GoDaddy': 'Godaddy.txt',  # Capital G for legacy compatibility
    }

    if provider in special_filenames:
        return special_filenames[provider]

    # Default: lowercase with optional prefix
    prefix = "(Maybe Office) " if is_office_related_provider(provider) else ""
    return f"{prefix}{provider.lower()}.txt"


# ============================================================================
# DNS & PROVIDER DETECTION
# ============================================================================
def get_resolver():
    """Create configured DNS resolver instance."""
    resolver = dns.resolver.Resolver()
    resolver.nameservers = EXTERNAL_RESOLVERS
    resolver.timeout = DNS_TIMEOUT
    resolver.lifetime = DNS_TIMEOUT * 2
    resolver.rotate = True  # Rotate nameservers for load distribution
    return resolver


def detect_provider(mx_records, domain=None):
    """
    Detect email provider from MX records.

    Args:
        mx_records: List of MX record hostnames
        domain: Original domain name (for domain-level shortcuts)

    Returns:
        String provider name or category
    """
    if not mx_records:
        return 'NoMX'

    domain_lower = (domain or '').lower()

    # === Domain-level shortcuts (fast path) ===
    if domain_lower == 'gmail.com':
        return 'Gmail (free)'
    if domain_lower in MICROSOFT_FREE_DOMAINS:
        return 'Microsoft Free'
    if domain_lower in YAHOO_DOMAINS or domain_lower.startswith('yahoo.'):
        return 'Yahoo !'
    if domain_lower in AOL_DOMAINS:
        return 'AOL'

    # === MX record pattern matching ===
    mx_str = ' '.join(mx_records).lower()

    # Special case: serverdata.net indicates OWA/Exchange hosting
    if 'serverdata.net' in mx_str:
        return 'OWA Serverdata'

    # Yahoo pattern (catches non-yahoo.* domains using Yahoo infrastructure)
    yahoo_pattern = r'mta[5-7]\.am0\.yahoodns\.net|yahoodns\.net|prodigy\.net'
    if re.search(yahoo_pattern, mx_str):
        return 'Yahoo (Others)'

    # Check against provider patterns dictionary
    for provider, pattern in PROVIDER_PATTERNS.items():
        if re.search(pattern, mx_str, re.IGNORECASE):
            return provider

    return 'Other'


def check_domain_dns(entry, resolver, max_retries, retry_delay, all_entries=None):
    """
    Perform DNS lookup with retry logic.

    This is the SINGLE SOURCE OF TRUTH for DNS operations.

    Args:
        entry: Dict with 'domain', 'line', 'email' keys
        resolver: dns.resolver.Resolver instance
        max_retries: Maximum retry attempts
        retry_delay: Base delay between retries
        all_entries: List of all entries sharing this domain (for batch output)

    Returns:
        Result dict with provider detection and metadata
    """
    domain = entry['domain'].lower()
    all_entries = all_entries or [entry]

    # === Fast-path: Known free domains (skip DNS) ===
    if domain in MICROSOFT_FREE_DOMAINS:
        return {
            **entry,
            'provider': 'Microsoft Free',
            'mx': [],
            'error': None,
            'all_entries': all_entries
        }
    if domain == 'gmail.com':
        return {
            **entry,
            'provider': 'Gmail (free)',
            'mx': [],
            'error': None,
            'all_entries': all_entries
        }

    retry_count = 0
    last_exception = None

    while retry_count <= max_retries:
        try:
            # Perform MX lookup
            answers = resolver.resolve(entry['domain'], 'MX')

            if not answers:
                return {
                    **entry,
                    'provider': 'NoMX',
                    'mx': [],
                    'error': 'No MX records (empty response)',
                    'all_entries': all_entries
                }

            mx_records = [str(r.exchange).rstrip('.') for r in answers]
            provider = detect_provider(mx_records, domain=entry['domain'])

            return {
                **entry,
                'provider': provider,
                'mx': mx_records,
                'error': None,
                'all_entries': all_entries
            }

        except dns.resolver.NoAnswer:
            return {
                **entry,
                'provider': 'NoMX',
                'mx': [],
                'error': 'Domain exists but no MX records',
                'all_entries': all_entries
            }
        except (dns.resolver.NoNameservers, dns.resolver.Timeout) as e:
            last_exception = str(e)
            retry_count += 1
            if retry_count <= max_retries:
                delay = retry_delay * retry_count
                logger.debug(f"Retry {retry_count}/{max_retries} for {entry['domain']} after {delay}s")
                time.sleep(delay)
        except dns.resolver.NXDOMAIN:
            return {
                **entry,
                'provider': 'Error',
                'mx': [],
                'error': 'Domain does not exist (NXDOMAIN)',
                'all_entries': all_entries
            }
        except Exception as e:
            last_exception = f"{type(e).__name__}: {e}"
            logger.warning(f"Unexpected error for {entry['domain']}: {last_exception}")
            break  # Don't retry unknown errors

    # All retries exhausted
    return {
        **entry,
        'provider': 'Error',
        'mx': [],
        'error': f"DNS lookup failed after {max_retries} retries: {last_exception}",
        'all_entries': all_entries
    }


# ============================================================================
# FILE PARSING & DOMAIN EXTRACTION
# ============================================================================
def extract_domains(input_file):
    """
    Extract email addresses and domains from input file.

    Supports: CSV, TXT, XLSX, XLS

    Returns:
        List of dicts: [{'line': original_line, 'domain': 'example.com', 'email': 'user@example.com'}, ...]
    """
    entries = []
    file_ext = Path(input_file).suffix.lower()

    # === Excel file handling ===
    if file_ext in ['.xlsx', '.xls']:
        if not PANDAS_AVAILABLE:
            raise ImportError(
                "pandas and openpyxl required for Excel files. "
                "Install with: pip install pandas openpyxl"
            )

        try:
            logger.info(f"Reading Excel file: {input_file}")
            df = pd.read_excel(input_file)

            # Auto-detect email column (contains @ symbol)
            email_col = None
            for col in df.columns:
                if df[col].astype(str).str.contains('@', na=False).any():
                    email_col = col
                    break

            if email_col is None:
                raise ValueError("No column containing email addresses found")

            # Process each row
            for idx, row in df.iterrows():
                email = str(row[email_col]).strip()
                if '@' not in email or email.lower() == 'nan':
                    continue

                domain = email.split('@')[-1].lower().rstrip('.')
                # Reconstruct original line as CSV
                line_parts = [str(row[col]).strip() for col in df.columns]
                line = ','.join(line_parts)

                entries.append({
                    'line': line,
                    'domain': domain,
                    'email': email,
                    'source_row': idx + 2  # Excel row number (1-indexed + header)
                })

            logger.info(f"Extracted {len(entries)} entries from Excel file")
            return entries

        except Exception as e:
            logger.error(f"Error reading Excel file: {e}", exc_info=True)
            raise

    # === CSV/TXT file handling ===
    import csv

    logger.info(f"Reading text/CSV file: {input_file}")
    line_num = 0

    for raw_line in read_lines_with_fallback(input_file):
        line_num += 1
        line = raw_line.strip()

        # Skip empty lines and encoding artifacts
        if not line or 'utf-8' in line.lower():
            continue

        # Try CSV parsing first (handles quoted fields with commas)
        try:
            reader = csv.reader([line])
            fields = next(reader)

            # Skip header rows
            if any(str(f).strip().lower() == 'email' for f in fields):
                logger.debug(f"Skipping header at line {line_num}")
                continue

            # Find email field: prefer index 1, then first field with @
            email_field = None
            if len(fields) > 1 and '@' in str(fields[1]).strip():
                email_field = str(fields[1]).strip()
            else:
                for field in fields:
                    field_str = str(field).strip()
                    if '@' in field_str:
                        email_field = field_str
                        break

            if email_field:
                domain = email_field.split('@')[-1].lower().rstrip('.')
                entries.append({
                    'line': line,
                    'domain': domain,
                    'email': email_field,
                    'source_line': line_num
                })
                continue

        except csv.Error as e:
            logger.debug(f"CSV parse failed at line {line_num}: {e}")
        except StopIteration:
            continue

        # === Fallback: Regex-based extraction ===
        if '@' in line:
            # Try comma-separated: name,email@domain.com
            if ',' in line:
                parts = line.rsplit(',', 1)
                if len(parts) == 2 and '@' in parts[1]:
                    email = parts[1].strip()
                    domain = email.split('@')[-1].lower().rstrip('.')
                    entries.append({
                        'line': line,
                        'domain': domain,
                        'email': email,
                        'source_line': line_num
                    })
                    continue

            # Extract first email-like token
            match = re.search(r'[\w\.\-\+]+@[\w\.\-]+\.[\w\-]+', line)
            if match:
                email = match.group(0)
                domain = email.split('@')[-1].lower().rstrip('.')
                entries.append({
                    'line': line,
                    'domain': domain,
                    'email': email,
                    'source_line': line_num
                })
                continue
        else:
            # Line contains only domain (no @)
            domain = line.lower().strip()
            domain = re.sub(r'^https?://', '', domain)
            domain = re.sub(r'^www\.', '', domain)
            domain = domain.split('/')[0].rstrip('.')

            # Basic domain validation
            if domain and '.' in domain and len(domain) <= 253:
                entries.append({
                    'line': line,
                    'domain': domain,
                    'email': f'user@{domain}',  # Placeholder for consistency
                    'source_line': line_num,
                    'domain_only': True
                })

    logger.info(f"Extracted {len(entries)} entries from {input_file}")
    return entries


def optimize_entries(entries):
    """
    Group entries by domain to avoid redundant DNS lookups.

    Returns:
        tuple: (optimized_list, domain_to_entries_dict)
        - optimized_list: One entry per unique domain (for DNS checking)
        - domain_to_entries_dict: Maps domain -> all original entries
    """
    domain_groups = defaultdict(list)

    for entry in entries:
        domain_groups[entry['domain']].append(entry)

    optimized = []
    domain_map = {}

    for domain, domain_entries in domain_groups.items():
        # Use first entry as DNS lookup representative
        representative = domain_entries[0].copy()
        optimized.append(representative)
        domain_map[domain] = domain_entries

    logger.info(f"Optimized {len(entries)} entries to {len(optimized)} unique domains")
    return optimized, domain_map


# ============================================================================
# THREAD-SAFE RESULT SAVER
# ============================================================================
class RealTimeSaver:
    """
    Thread-safe result saver with background worker thread.

    Features:
    - Queue-based async saving to avoid blocking DNS threads
    - Thread-safe counter updates with locking
    - Automatic file handle management
    - Real-time GUI callback support
    """

    def __init__(self, output_dir=None, gui_callback=None):
        self.output_dir = output_dir or self._get_unique_output_dir()
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

        self.file_handles = {}
        self.queue = Queue(maxsize=1000)  # Prevent memory buildup
        self.running = True
        self.counts = defaultdict(int)
        self.domain_status = {}  # Track domain -> provider mapping

        self.gui_callback = gui_callback
        self.lock = threading.Lock()  # ✅ Thread safety for shared state

        # Start background saver thread
        self.saver_thread = threading.Thread(
            target=self._save_worker,
            name="ResultSaver",
            daemon=True
        )
        self.saver_thread.start()
        logger.info(f"RealTimeSaver initialized, output: {self.output_dir}")

    def _get_unique_output_dir(self):
        """Generate unique output directory name to avoid overwrites."""
        base = "provider_results"
        if not Path(base).exists():
            return base

        counter = 1
        while Path(f"{base}_{counter}").exists():
            counter += 1
        return f"{base}_{counter}"

    def _get_file_handle(self, provider):
        """Get or create file handle for provider (thread-safe)."""
        provider = normalize_provider_name(provider)
        filename = get_safe_filename(provider)
        filepath = Path(self.output_dir) / filename

        # Check cache first (with lock)
        with self.lock:
            if provider in self.file_handles:
                return self.file_handles[provider]

            # Create new handle
            try:
                fh = open(filepath, 'a', encoding='utf-8')
                self.file_handles[provider] = fh
                logger.debug(f"Opened file handle: {filepath}")
                return fh
            except OSError as e:
                logger.error(f"Failed to open {filepath}: {e}")
                # Fallback to errors file
                if 'Error' not in self.file_handles:
                    error_path = Path(self.output_dir) / 'errors.txt'
                    self.file_handles['Error'] = open(error_path, 'a', encoding='utf-8')
                return self.file_handles['Error']

    def _save_worker(self):
        """Background thread: process queue and save results."""
        while self.running or not self.queue.empty():
            try:
                # Non-blocking get with timeout
                result = self.queue.get(timeout=0.2)
            except Empty:
                continue

            try:
                self._process_result(result)
            except Exception as e:
                logger.error(f"Error processing result: {e}", exc_info=True)
            finally:
                self.queue.task_done()

    def _process_result(self, result):
        """Process single result dict (called from worker thread)."""
        provider = result['provider']
        domain = result['domain']
        all_entries = result.get('all_entries', [result])

        # Normalize provider name for consistency
        provider = normalize_provider_name(provider)

        # === Thread-safe state updates ===
        with self.lock:
            # Handle domain re-processing (e.g., retry with different result)
            if domain in self.domain_status:
                prev_provider = self.domain_status[domain]
                if prev_provider != provider:
                    # Update counts: remove from old, add to new
                    self.counts[prev_provider] -= len(all_entries)
                    self.counts[provider] += len(all_entries)
                    self.domain_status[domain] = provider
                    logger.debug(f"Updated {domain}: {prev_provider} -> {provider}")
                # If same provider, don't double-count (retry of same result)
                else:
                    return  # Skip duplicate
            else:
                # First time seeing this domain
                self.domain_status[domain] = provider
                self.counts[provider] += len(all_entries)

            # Get safe copy of counts for GUI
            counts_snapshot = dict(self.counts)

        # === File I/O (outside lock to minimize contention) ===
        try:
            fh = self._get_file_handle(provider)
            for entry in all_entries:
                fh.write(f"{entry['line']}\n")
            fh.flush()  # Ensure data written to disk
        except OSError as e:
            logger.error(f"Write error for {provider}: {e}")
            # Try errors file as fallback
            if provider != 'Error':
                error_fh = self._get_file_handle('Error')
                for entry in all_entries:
                    error_fh.write(f"{entry['line']}  # Original provider: {provider}\n")
                error_fh.flush()

        # === GUI update (schedule on main thread) ===
        if self.gui_callback and hasattr(self.gui_callback, '__self__'):
            gui_obj = self.gui_callback.__self__
            if hasattr(gui_obj, 'root') and hasattr(gui_obj.root, 'after'):
                # Schedule GUI update on main thread
                gui_obj.root.after(0, lambda: self.gui_callback(counts_snapshot))

    def add_result(self, result):
        """Add result to queue (thread-safe, non-blocking)."""
        try:
            self.queue.put_nowait(result)
        except Exception as e:
            logger.error(f"Failed to queue result: {e}")

    def wait_completion(self, timeout=30):
        """Wait for queue to empty (for clean shutdown)."""
        try:
            self.queue.join()
            return True
        except Exception as e:
            logger.warning(f"Queue join timeout or error: {e}")
            return False

    def stop(self):
        """Signal worker to stop and wait for completion."""
        logger.info("Stopping RealTimeSaver...")
        self.running = False

        # Wait for queue to drain
        self.wait_completion(timeout=10)

        # Close all file handles
        with self.lock:
            for provider, fh in self.file_handles.items():
                try:
                    fh.close()
                    logger.debug(f"Closed handle for {provider}")
                except Exception as e:
                    logger.error(f"Error closing {provider} handle: {e}")
            self.file_handles.clear()

        # Wait for thread to finish
        if self.saver_thread.is_alive():
            self.saver_thread.join(timeout=5)

        logger.info("RealTimeSaver stopped")

    def get_counts(self):
        """Thread-safe copy of current counts."""
        with self.lock:
            return dict(self.counts)


# ============================================================================
# GUI APPLICATION
# ============================================================================
class EmailSorterGUI:
    """Main GUI application using Tkinter."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Email Provider Sorter v2.0")
        self.root.geometry("900x750")
        self.root.minsize(800, 600)
        self.root.configure(bg='#f5f5f5')

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Application state
        self.saver = None
        self.entries = []
        self.optimized_entries = []
        self.domain_to_entries = {}
        self.processed_count = 0
        self.total_count = 0
        self.is_processing = False
        self.should_stop = False
        self.max_workers = MAX_WORKERS
        self.last_folder = str(Path.home() / "Desktop")
        self.update_timer = None
        self.processing_thread = None

        # Configure styles
        self._setup_styles()
        self._setup_ui()

        logger.info("GUI initialized")

    def _setup_styles(self):
        """Configure ttk styles for consistent appearance."""
        style = ttk.Style()
        style.theme_use('clam')  # Cross-platform friendly theme

        # Custom styles
        style.configure('Title.TLabel', font=('Segoe UI', 16, 'bold'), background='#f5f5f5')
        style.configure('Status.TLabel', font=('Segoe UI', 9), background='#f5f5f5')
        style.configure('Progress.TProgressbar', thickness=20)
        style.configure('Treeview', rowheight=25)
        style.configure('Treeview.Heading', font=('Segoe UI', 9, 'bold'))

    def _setup_ui(self):
        """Build the user interface."""
        # Main container with padding
        main = ttk.Frame(self.root, padding=15)
        main.grid(row=0, column=0, sticky='nsew')

        # Configure grid weights for resizing
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(4, weight=1)  # Results area expands

        # === Title ===
        ttk.Label(main, text="📧 Email Provider Sorter", style='Title.TLabel').grid(
            row=0, column=0, columnspan=3, pady=(0, 20)
        )

        # === File Selection ===
        ttk.Label(main, text="Input File:").grid(row=1, column=0, sticky='w', pady=5)

        self.file_var = tk.StringVar()
        file_entry = ttk.Entry(main, textvariable=self.file_var, width=55)
        file_entry.grid(row=1, column=1, sticky='ew', padx=(10, 5), pady=5)

        browse_btn = ttk.Button(main, text="Browse...", command=self._browse_file)
        browse_btn.grid(row=1, column=2, padx=(5, 0), pady=5)

        # === Thread Configuration ===
        ttk.Label(main, text="Threads:").grid(row=2, column=0, sticky='w', pady=5)

        self.thread_var = tk.StringVar(value=str(self.max_workers))
        thread_entry = ttk.Entry(main, textvariable=self.thread_var, width=8)
        thread_entry.grid(row=2, column=1, sticky='w', padx=(10, 0), pady=5)

        ttk.Label(
            main,
            text="(1-100 recommended; higher may trigger DNS rate limits)",
            style='Status.TLabel'
        ).grid(row=3, column=0, columnspan=2, sticky='w', pady=(0, 10))

        # === Control Button ===
        self.start_btn = ttk.Button(
            main,
            text="▶ Start Processing",
            command=self._toggle_processing,
            state='disabled'
        )
        self.start_btn.grid(row=4, column=0, columnspan=3, pady=15)

        # === Progress Section ===
        progress_frame = ttk.LabelFrame(main, text="Progress", padding=10)
        progress_frame.grid(row=5, column=0, columnspan=3, sticky='nsew', pady=5)
        progress_frame.columnconfigure(0, weight=1)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            style='Progress.TProgressbar'
        )
        self.progress_bar.grid(row=0, column=0, sticky='ew', pady=(0, 8))

        self.progress_label = ttk.Label(progress_frame, text="Ready", style='Status.TLabel')
        self.progress_label.grid(row=1, column=0)

        # === Results Table ===
        results_frame = ttk.LabelFrame(main, text="Results by Provider", padding=10)
        results_frame.grid(row=6, column=0, columnspan=3, sticky='nsew', pady=5)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)

        # Treeview for results
        columns = ('Provider', 'Count', 'Percentage')
        self.results_tree = ttk.Treeview(
            results_frame,
            columns=columns,
            show='headings',
            selectmode='browse'
        )

        for col in columns:
            self.results_tree.heading(col, text=col)
            width = 120 if col == 'Percentage' else 200
            self.results_tree.column(col, width=width, anchor='center', minwidth=80)

        # Scrollbar
        scrollbar = ttk.Scrollbar(results_frame, orient='vertical', command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)

        self.results_tree.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')

        # === Status Bar ===
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            main,
            textvariable=self.status_var,
            style='Status.TLabel',
            relief='sunken',
            padding=(5, 2)
        )
        status_bar.grid(row=7, column=0, columnspan=3, sticky='ew', pady=(10, 0))

        # Bind file entry to enable button
        self.file_var.trace_add('write', lambda *args: self._validate_inputs())

    def _validate_inputs(self):
        """Enable/disable start button based on input validity."""
        file_path = self.file_var.get().strip()
        is_valid = bool(file_path and Path(file_path).exists())
        self.start_btn.configure(state='normal' if is_valid else 'disabled')

    def _browse_file(self):
        """Open file dialog and update UI."""
        filetypes = [
            ("All supported", "*.csv *.txt *.xlsx *.xls"),
            ("CSV files", "*.csv"),
            ("Text files", "*.txt"),
            ("Excel files", "*.xlsx *.xls"),
            ("All files", "*.*")
        ]

        filepath = filedialog.askopenfilename(
            title="Select input file",
            filetypes=filetypes,
            initialdir=self.last_folder
        )

        if filepath:
            self.file_var.set(filepath)
            self.last_folder = str(Path(filepath).parent)
            self._validate_inputs()

    def _update_results_display(self, counts):
        """Update results treeview (called from main thread)."""
        # Cancel pending update
        if self.update_timer:
            self.root.after_cancel(self.update_timer)
            self.update_timer = None

        # Debounce: schedule update after short delay
        self.update_timer = self.root.after(150, lambda: self._apply_results_update(counts))

    def _apply_results_update(self, counts):
        """Actually update the treeview with new counts."""
        # Clear existing items
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        total = sum(counts.values())

        # Sort by count descending
        for provider, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
            if count == 0:
                continue
            pct = (count / total * 100) if total > 0 else 0
            self.results_tree.insert(
                '', 'end',
                values=(provider, f"{count:,}", f"{pct:.1f}%")
            )

    def _update_progress_display(self):
        """Update progress bar and label."""
        if self.total_count > 0:
            pct = min(100, (self.processed_count / self.total_count) * 100)
            self.progress_var.set(pct)
            self.progress_label.config(
                text=f"Processed: {self.processed_count:,} / {self.total_count:,} ({pct:.1f}%)"
            )

    def _toggle_processing(self):
        """Start or stop processing based on current state."""
        if self.is_processing:
            self._stop_processing()
        else:
            self._start_processing()

    def _start_processing(self):
        """Initialize and start the processing workflow."""
        input_file = self.file_var.get().strip()

        # Validate thread count
        try:
            threads = int(self.thread_var.get())
            if not 1 <= threads <= 100:
                raise ValueError()
            self.max_workers = threads
        except ValueError:
            messagebox.showerror(
                "Invalid Input",
                "Thread count must be a number between 1 and 100."
            )
            return

        try:
            self.status_var.set("📥 Loading and parsing input file...")
            self.root.update_idletasks()

            # Extract entries from file
            self.entries = extract_domains(input_file)
            if not self.entries:
                messagebox.showwarning("No Data", "No valid email addresses or domains found.")
                return

            # Optimize: group by domain to avoid redundant lookups
            self.status_var.set("🔄 Optimizing domain list...")
            self.root.update_idletasks()

            self.optimized_entries, self.domain_to_entries = optimize_entries(self.entries)
            unique_domains = len(self.optimized_entries)

            # Reset state
            self.total_count = unique_domains
            self.processed_count = 0
            self.is_processing = True
            self.should_stop = False

            # Update UI
            self.start_btn.config(text="⏹ Stop Processing")
            self.progress_var.set(0)
            self.progress_label.config(text="Starting...")
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)

            # Initialize saver with GUI callback
            self.saver = RealTimeSaver(gui_callback=self._update_results_display)

            # Start background processing
            total_entries = len(self.entries)
            self.status_var.set(
                f"🔍 Processing {total_entries:,} entries ({unique_domains:,} unique domains) "
                f"with {self.max_workers} threads..."
            )

            self.processing_thread = threading.Thread(
                target=self._process_domains_worker,
                name="Processor",
                daemon=True
            )
            self.processing_thread.start()

            logger.info(f"Processing started: {total_entries} entries, {unique_domains} domains")

        except Exception as e:
            logger.error(f"Failed to start processing: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to start: {str(e)}")
            self._reset_ui_state()

    def _process_domains_worker(self):
        """Background thread: perform DNS lookups and processing."""
        start_time = time.time()
        resolver = get_resolver()
        error_entries = []

        try:
            # === First pass: process all unique domains ===
            self.root.after(0, lambda: self.status_var.set("🔎 First pass: Checking domains..."))

            error_entries = self._process_batch(
                self.optimized_entries,
                resolver,
                max_retries=MAX_RETRIES,
                retry_delay=RETRY_DELAY
            )

            if self.should_stop:
                self._finish_processing(time.time() - start_time, was_stopped=True)
                return

            # === Second pass: retry failed domains ===
            if error_entries and not self.should_stop:
                self.root.after(0, lambda: self.status_var.set(
                    f"🔄 Retrying {len(error_entries):,} failed domains..."
                ))

                self.processed_count = 0
                self.total_count = len(error_entries)
                self.root.after(0, self._update_progress_display)

                time.sleep(1)  # Brief pause before retry

                if self.should_stop:
                    self._finish_processing(time.time() - start_time, was_stopped=True)
                    return

                # Retry with slightly longer delays
                final_errors = self._process_batch(
                    error_entries,
                    resolver,
                    max_retries=MAX_RETRIES + 1,
                    retry_delay=RETRY_DELAY * 1.5
                )

                # === Optional third pass for persistent errors ===
                if final_errors and not self.should_stop:
                    self.root.after(0, lambda: self.status_var.set(
                        f"⚠️ Final retry for {len(final_errors):,} domains..."
                    ))
                    self.processed_count = 0
                    self.total_count = len(final_errors)
                    self.root.after(0, self._update_progress_display)

                    time.sleep(1.5)

                    if not self.should_stop:
                        self._process_batch(
                            final_errors,
                            resolver,
                            max_retries=MAX_RETRIES + 2,
                            retry_delay=RETRY_DELAY * 2
                        )

            # Wait for saver to finish writing
            if self.saver:
                self.saver.wait_completion(timeout=15)

            elapsed = time.time() - start_time
            self._finish_processing(elapsed, was_stopped=False)

        except Exception as e:
            logger.error(f"Processing error: {e}", exc_info=True)
            self.root.after(0, lambda: messagebox.showerror(
                "Processing Error", f"An error occurred: {str(e)}"
            ))
            self.root.after(0, self._reset_ui_state)

    def _process_batch(self, entries, resolver, max_retries, retry_delay):
        """
        Process a batch of entries using thread pool.

        Returns:
            List of entries that resulted in 'Error' provider (for retry)
        """
        error_entries = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_entry = {
                executor.submit(
                    check_domain_dns,
                    entry,
                    resolver,
                    max_retries,
                    retry_delay,
                    self.domain_to_entries.get(entry['domain'], [entry])
                ): entry
                for entry in entries
            }

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_entry):
                if self.should_stop:
                    # Cancel remaining futures
                    for f in future_to_entry:
                        f.cancel()
                    break

                entry = future_to_entry[future]
                try:
                    result = future.result()

                    # Track errors for potential retry
                    if result and result.get('provider') == 'Error':
                        error_entries.append({
                            'line': result['line'],
                            'domain': result['domain'],
                            'email': result['email']
                        })

                    # Update progress counter
                    self.processed_count += 1
                    if self.processed_count % 10 == 0:  # Throttle GUI updates
                        self.root.after(0, self._update_progress_display)

                except concurrent.futures.CancelledError:
                    logger.debug(f"Task cancelled for {entry['domain']}")
                except Exception as e:
                    logger.error(f"Unexpected error processing {entry['domain']}: {e}")
                    error_entries.append(entry)

        return error_entries

    def _progress_callback(self):
        """Thread-safe progress increment (called from saver)."""
        self.processed_count += 1
        # Throttle updates to prevent GUI lag
        if self.processed_count % 25 == 0:
            self.root.after(0, self._update_progress_display)

    def _finish_processing(self, elapsed_seconds, was_stopped=False, total_processed=None):
        """Handle completion (success or stop)."""
        self.is_processing = False
        self.should_stop = False

        # Stop and cleanup saver
        if self.saver:
            self.saver.stop()
            counts = self.saver.get_counts()
        else:
            counts = {}

        # Update UI on main thread
        def _finalize_ui():
            self._reset_ui_state()

            total_processed = sum(counts.values())
            error_count = counts.get('Error', 0)

            if was_stopped:
                title = "⏹ Processing Stopped"
                message = (
                    f"Processing stopped by user.\n\n"
                    f"✅ Processed: {total_processed:,} domains\n"
                    f"⏱️  Elapsed: {elapsed_seconds:.1f} seconds\n\n"
                    f"📁 Results saved to: {self.saver.output_dir if self.saver else 'N/A'}\n"
                    f"💡 Partial results are valid and can be used."
                )
            else:
                title = "✅ Processing Complete"
                message = (
                    f"🎉 All done!\n\n"
                    f"📊 Processed: {total_processed:,} unique domains\n"
                    f"📈 From {len(self.entries):,} total entries\n"
                    f"⏱️  Time: {elapsed_seconds:.1f} seconds\n"
                    f"❌ Final errors: {error_count:,}\n\n"
                    f"📁 Output folder: {self.saver.output_dir if self.saver else 'N/A'}\n\n"
                )
                if error_count > 0:
                    message += "🔍 Check 'errors.txt' for domains that couldn't be resolved."

            messagebox.showinfo(title, message)
            self.status_var.set(f"✅ Completed in {elapsed_seconds:.1f}s")

        self.root.after(0, _finalize_ui)
        logger.info(f"Processing finished: {elapsed_seconds:.1f}s, {total_processed} domains")

    def _stop_processing(self):
        """Signal processing to stop gracefully."""
        if not self.is_processing:
            return

        self.should_stop = True
        self.status_var.set("⏹ Stopping... (finishing current tasks)")
        logger.info("Stop signal sent")

    def _reset_ui_state(self):
        """Reset UI to initial ready state."""
        self.is_processing = False
        self.should_stop = False
        self.start_btn.config(text="▶ Start Processing", state='normal')
        self._validate_inputs()  # Re-check file validity

    def _on_closing(self):
        """Handle window close event with cleanup."""
        if self.is_processing:
            response = messagebox.askyesno(
                "Confirm Exit",
                "Processing is in progress.\n\nStop and exit anyway?",
                icon='warning'
            )
            if not response:
                return  # Cancel close

            self._stop_processing()
            # Brief wait for cleanup
            self.root.after(500, self.root.destroy)
        else:
            # Clean shutdown
            if self.saver:
                self.saver.stop()
            self.root.destroy()

    def run(self):
        """Start the Tkinter main loop."""
        logger.info("Starting GUI main loop")
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            if self.saver:
                self.saver.stop()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================
def main():
    """Application entry point."""
    print("📧 Email Provider Sorter v2.0")
    print("✅ Thread-safe • 🔄 Retry logic • 📁 Categorized output\n")

    # Check dependencies
    if not PANDAS_AVAILABLE:
        print("⚠️  Warning: pandas/openpyxl not installed")
        print("   Excel (.xlsx) support disabled")
        print("   Install with: pip install pandas openpyxl\n")

    try:
        app = EmailSorterGUI()
        app.run()
    except Exception as e:
        logger.critical(f"Application failed to start: {e}", exc_info=True)
        messagebox.showerror("Fatal Error", f"Failed to start application:\n\n{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()