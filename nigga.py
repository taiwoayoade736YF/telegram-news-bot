import dns.resolver
import concurrent.futures
import re
import os
from collections import defaultdict
import time
import threading
from queue import Queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json

# Configuration
EXTERNAL_RESOLVERS = ['8.8.8.8', '1.1.1.1']  # Reduced to fastest resolvers
MAX_WORKERS = 299  # Default thread count
DNS_TIMEOUT = 2  # Reduced from 5 to 2 seconds
MAX_RETRIES = 2  # Reduced from 3 to 2
RETRY_DELAY = 0.5  # Reduced from 1 to 0.5 seconds

PROVIDER_PATTERNS = {
    'Microsoft 365': r'outlook\.com|outlook\.office365\.com|outlook\.office\.com|protection\.outlook\.com|mail\.protection\.outlook\.com|outlook\.protection\.office365\.com',
    'Google Workspace (Gmail)': r'gmail-smtp-in\.l\.google\.com|aspmx\.l\.google\.com|alt1\.aspmx\.l\.google\.com|alt2\.aspmx\.l\.google\.com|aspmx2\.googlemail\.com|aspmx3\.googlemail\.com',
    'Abnormal Security': r'abnormalsecurity',
    'Tessian': r'tessian',
    'Darktrace Email': r'darktrace',
    'Proofpoint Email Protection': r'pphosted|proofpoint|pps\.filter',
    'Mimecast Email Security': r'mimecast|smtp\.mimecast',
    'Barracuda Email Protection': r'barracuda|bmsmtp',
    'Fortimail (Fortinet)': r'fortinet|fortimail',
    'Cisco Secure Email (IronPort)': r'ironport|cisco|cesmail',
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
    'SendGrid': r'sendgrid|smtp\.sendgrid\.net',
    'Mailgun': r'mailgun|mxa\.mailgun\.org|mxb\.mailgun\.org',
    'Amazon SES': r'amazonses|smtp\.amazonses\.com',
    'SparkPost': r'sparkpost|smtp\.sparkpostmail\.com',
    'Campaign Monitor': r'campaignmonitor|cmail1\.com',
    'Constant Contact': r'constantcontact|smtp\.constantcontact\.com',
    'Mailchimp': r'mailchimp|smtp\.mailchimp\.com',
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
def read_lines_with_fallback(input_file):
    """Yield lines from a text file trying multiple encodings to avoid decode errors.
    Tries utf-8 and common fallbacks; finally ignores undecodable bytes.
    """
    encodings_to_try = [
        ('utf-8', 'strict'),
        ('utf-8-sig', 'strict'),
        ('cp1252', 'strict'),
        ('latin-1', 'strict'),
    ]
    for enc, err in encodings_to_try:
        try:
            with open(input_file, 'r', encoding=enc, errors=err) as f:
                for line in f:
                    yield line
            return
        except UnicodeDecodeError:
            continue
        except Exception:

            continue
    # Last resort: ignore undecodable bytes
    try:
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                yield line
    except Exception:
        # If everything fails, yield nothing
        return


class RealTimeSaver:
    def __init__(self, gui_callback=None):
        self.output_dir = self._get_unique_output_dir()
        os.makedirs(self.output_dir, exist_ok=True)
        self.file_handles = {}
        self.queue = Queue()
        self.running = True
        self.counts = defaultdict(int)
        self.gui_callback = gui_callback
        self.domain_status = {}  # Track domain -> provider mapping
        self.saver_thread = threading.Thread(target=self.save_worker)
        self.saver_thread.start()

    def _get_unique_output_dir(self):
        """Find a unique output directory name by appending numbers if needed"""
        base_dir = "provider_results"
        if not os.path.exists(base_dir):
            return base_dir

        counter = 1
        while os.path.exists(f"{base_dir}_{counter}"):
            counter += 1

        return f"{base_dir}_{counter}"

    def get_file_handle(self, provider):
        if provider not in self.file_handles:
            # Special handling for Yahoo categories
            if provider == 'yahoo !':
                filename = "yahoo !.txt"
            elif provider == 'yahoo (others)':
                filename = "yahoo (others).txt"
            elif provider == 'Microsoft Free':
                filename = "Microsoft Free.txt"
            elif provider == 'Gmail (free)':
                filename = "Gmail (free).txt"
            elif provider == 'OWA Serverdata':
                filename = "OWA Serverdata.txt"
            elif provider == 'Outlook':
                filename = "Outlook.txt"
            elif provider == 'GoDaddy':
                filename = "Godaddy.txt"
            else:
                # Add "(Maybe Office)" prefix for providers commonly used with Office environments
                office_providers = [
                    'Proofpoint Email Protection',
                    'Barracuda Email Protection',
                    'Mimecast Email Security',
                    'Cisco Secure Email (IronPort)',
                    'Symantec Email Security (Broadcom)',
                    'Trend Micro Email Security',
                    'Sophos Email Security',
                    'Forcepoint Email Security',
                    'Check Point Harmony Email',
                    'Fortimail (Fortinet)',
                    'Avanan (Check Point)',
                    'Armorblox (Okta)',
                    'GreatHorn',
                    'Agari (HelpSystems)',
                    'Cofense (PhishMe)',
                    'Inky',
                    'SpamTitan (TitanHQ)',
                    'MailChannels',
                    'Virtru',
                    'Zix (OpenText)',
                    'Egress Defend',
                    'Trustifi',
                    'Vade Secure',
                    'Hornetsecurity',
                    'Heimdal Email Security',
                    'Reflexion Networks',
                    'Cyren Email Security',
                    'F-Secure Email and Server Security',
                    'Kaspersky Secure Mail Gateway',
                    'VIPRE Email Security',
                    'SolarWinds Mail Assure',
                    'GFI MailEssentials',
                    'Rackspace Email Security',
                    'AppRiver (now Zix)',
                    'Retarus Email Security',
                    'Clearswift Secure Email Gateway',
                    'IRONSCALES',
                    'PhishLabs (by ZeroFOX)',
                    'Area 1 Security (Cloudflare)',
                    'SlashNext Email Protection',
                    'SEON Fraud Prevention',
                    'Red Sift OnDMARC',
                    'Valimail',
                    'Sendmarc',
                    'Mailprotector',
                    'MXGuarddog',
                    'Postmark (DMARC enforcement)'
                ]

                if provider in office_providers:
                    filename = f"(Maybe Office) {provider.lower()}.txt"
                else:
                    filename = f"{provider.lower()}.txt"

            filepath = os.path.join(self.output_dir, filename)
            self.file_handles[provider] = open(filepath, 'a')
        return self.file_handles[provider]

    def save_worker(self):
        while self.running or not self.queue.empty():
            try:
                result = self.queue.get(timeout=0.1)
                provider = result['provider']
                domain = result['domain']
                all_entries = result.get('all_entries', [result])  # Get all entries for this domain

                # Force Microsoft Free bucket for Microsoft consumer email domains
                domain_lower = domain.lower()
                microsoft_free_domains = {'outlook.com', 'msn.com', 'live.com', 'hotmail.com'}
                if domain_lower in microsoft_free_domains:
                    provider = 'Microsoft Free'

                # Check if this domain was already processed
                if domain in self.domain_status:
                    # Domain was already processed, this is a retry
                    previous_provider = self.domain_status[domain]
                    if previous_provider != provider:
                        # Remove from previous category (count all entries)
                        self.counts[previous_provider] -= len(all_entries)
                        # Update the domain status
                        self.domain_status[domain] = provider
                        # Continue to write the new results
                    else:
                        # Same provider (e.g., still "Error"), don't count again
                        self.queue.task_done()
                        continue
                else:
                    # First time processing this domain
                    self.domain_status[domain] = provider

                # Write to appropriate file
                if provider in PROVIDER_PATTERNS:
                    f = self.get_file_handle(provider)
                elif provider == 'Yahoo !':
                    f = self.get_file_handle('yahoo !')
                elif provider == 'Yahoo (Others)':
                    f = self.get_file_handle('yahoo (others)')
                elif provider == 'AOL':
                    f = self.get_file_handle('aol')
                elif provider == 'Microsoft Free':
                    f = self.get_file_handle('Microsoft Free')
                elif provider == 'Gmail (free)':
                    f = self.get_file_handle('Gmail (free)')
                elif provider == 'OWA Serverdata':
                    f = self.get_file_handle('OWA Serverdata')
                elif provider == 'Outlook':
                    f = self.get_file_handle('Outlook')
                elif provider == 'GoDaddy':
                    f = self.get_file_handle('GoDaddy')
                elif provider == 'Other':
                    f = self.get_file_handle('other')
                elif provider == 'NoMX':
                    f = self.get_file_handle('nomx')
                elif provider == 'Error':
                    f = self.get_file_handle('errors')

                # Write all entries for this domain
                for entry in all_entries:
                    f.write(f"{entry['line']}\n")
                f.flush()
                self.counts[provider] += len(all_entries)

                # Update GUI if callback provided
                if self.gui_callback:
                    self.gui_callback(self.counts.copy())

                # Call progress callback once per domain (not per entry)
                if hasattr(self.gui_callback, '__self__') and hasattr(self.gui_callback.__self__, 'progress_callback'):
                    self.gui_callback.__self__.progress_callback()

                self.queue.task_done()
            except:
                continue

    def add_result(self, result):
        self.queue.put(result)

    def stop(self):
        self.running = False
        self.saver_thread.join()
        for f in self.file_handles.values():
            f.close()


def extract_domains(input_file):
    entries = []
    file_extension = os.path.splitext(input_file)[1].lower()

    if file_extension in ['.xlsx', '.xls']:
        # Handle Excel files
        try:
            import pandas as pd
            df = pd.read_excel(input_file)

            # Find the column containing email addresses
            email_column = None
            for col in df.columns:
                if df[col].astype(str).str.contains('@').any():
                    email_column = col
                    break

            if email_column is None:
                raise ValueError("No email column found in Excel file")

            # Process each row
            for index, row in df.iterrows():
                email = str(row[email_column]).strip()
                if '@' in email and email != 'nan':
                    domain = email.split('@')[-1].lower()
                    # Reconstruct the line as CSV format
                    line_parts = [str(row[col]).strip() for col in df.columns]
                    line = ','.join(line_parts)
                    entries.append({
                        'line': line,
                        'domain': domain,
                        'email': email
                    })
        except ImportError:
            raise ImportError("pandas is required to read Excel files. Install with: pip install pandas openpyxl")
        except Exception as e:
            raise Exception(f"Error reading Excel file: {str(e)}")

    else:
        # Handle CSV and text files
        import csv
        for raw_line in read_lines_with_fallback(input_file):
            line = raw_line.strip()
            if not line:
                continue
            # Skip lines that contain 'utf-8' noise
            if 'utf-8' in line.lower():
                continue
            parsed_with_csv = False
            try:
                # Use CSV parser to respect quoted commas
                reader = csv.reader([line])
                fields = next(reader)

                # Skip likely header rows if any field exactly equals 'email'
                if any((str(field).strip().lower() == 'email') for field in fields):
                    continue

                # Prefer index 1 if it contains the email (e.g., Name,email)
                email_field = None
                if len(fields) > 1:
                    candidate = str(fields[1]).strip()
                    if '@' in candidate:
                        email_field = candidate
                # Otherwise, find the first field containing an email address
                if not email_field:
                    for field in fields:
                        field_str = str(field).strip()
                        if '@' in field_str:
                            email_field = field_str
                            break

                if email_field:
                    domain = email_field.split('@')[-1].lower()
                    entries.append({
                        'line': line,  # preserve the whole original line
                        'domain': domain,
                        'email': email_field
                    })
                    parsed_with_csv = True
            except Exception:
                # Fall through to heuristics below if CSV parsing fails
                parsed_with_csv = False

            if parsed_with_csv:
                continue

            # Heuristics fallback
            if '@' in line:
                if ',' in line:
                    parts = line.rsplit(',', 1)
                    if len(parts) == 2 and '@' in parts[1]:
                        email = parts[1].strip()
                        domain = email.split('@')[-1].lower()
                        entries.append({
                            'line': line,
                            'domain': domain,
                            'email': email
                        })
                        continue
                # Line contains only email (email@domain.com) or email not last
                # Extract the first email-like token
                match = re.search(r'[\w\.-]+@[\w\.-]+', line)
                if match:
                    email = match.group(0)
                    domain = email.split('@')[-1].lower()
                    entries.append({
                        'line': line,
                        'domain': domain,
                        'email': email
                    })
            else:
                # Line contains only domain (no @ symbol)
                domain = line.lower().strip()
                # Remove any common prefixes like http://, https://, www.
                domain = re.sub(r'^https?://', '', domain)
                domain = re.sub(r'^www\.', '', domain)
                # Remove any trailing slashes or paths
                domain = domain.split('/')[0]

                if domain and '.' in domain:  # Basic domain validation
                    entries.append({
                        'line': line,
                        'domain': domain,
                        'email': f'user@{domain}'  # Create dummy email for consistency
                    })

    return entries


def optimize_entries(entries):
    """Group entries by domain to avoid checking the same domain multiple times"""
    domain_groups = {}

    for entry in entries:
        domain = entry['domain']
        if domain not in domain_groups:
            domain_groups[domain] = []
        domain_groups[domain].append(entry)

    # Create optimized entries list with one entry per unique domain
    optimized_entries = []
    domain_to_entries = {}  # Map domain to all its entries

    for domain, domain_entries in domain_groups.items():
        # Use the first entry as the representative for DNS checking
        representative_entry = domain_entries[0].copy()
        optimized_entries.append(representative_entry)
        domain_to_entries[domain] = domain_entries

    return optimized_entries, domain_to_entries


def get_resolver():
    resolver = dns.resolver.Resolver()
    resolver.nameservers = EXTERNAL_RESOLVERS
    resolver.timeout = DNS_TIMEOUT
    resolver.lifetime = DNS_TIMEOUT * 2
    return resolver


def detect_provider(mx_records, domain=None):
    if not mx_records:
        return 'NoMX'

    # Check if the domain itself is a Yahoo domain
    if domain:
        domain_lower = domain.lower()

        # Check for Gmail free domain
        if domain_lower == 'gmail.com':
            return 'Gmail (free)'

        # Check for any domain that starts with "yahoo." (covers all Yahoo domains)
        if domain_lower.startswith('yahoo.'):
            return 'Yahoo !'

        # Check for specific Yahoo-related domains
        yahoo_related_domains = [
            'rocketmail.com', 'y7mail.com', 'ymail.com', 'kimo.com'
        ]

        if domain_lower in yahoo_related_domains:
            return 'Yahoo !'

        # Check for AOL domains
        aol_domains = [
            'aol.com', 'aol.co.uk', 'aol.de', 'aol.fr', 'aol.jp', 'aol.com.mx'
        ]

        if domain_lower in aol_domains:
            return 'AOL'

    mx_str = ' '.join(mx_records).lower()

    # Special classification: serverdata.net (OWA Serverdata)
    if 'serverdata.net' in mx_str:
        return 'OWA Serverdata'

    # Check for Yahoo patterns first
    yahoo_pattern = r'mta5\.am0\.yahoodns\.net|mta6\.am0\.yahoodns\.net|mta7\.am0\.yahoodns\.net|mta1\.am0\.yahoodns\.net|yahoodns\.net|prodigy\.net'
    if re.search(yahoo_pattern, mx_str):
        return 'Yahoo (Others)'

    # Check other providers
    for provider, pattern in PROVIDER_PATTERNS.items():
        if re.search(pattern, mx_str):
            return provider
    return 'Other'


def check_domain_with_retry(entry, saver, progress_callback):
    # Short-circuit for Microsoft consumer email domains: don't check MX
    domain = entry['domain'].lower()

    # Check if domain is exactly outlook.com, msn.com, live.com, or hotmail.com
    microsoft_free_domains = {'outlook.com', 'msn.com', 'live.com', 'hotmail.com'}
    if domain in microsoft_free_domains:
        result = {**entry, 'provider': 'Microsoft Free', 'mx': [], 'error': None}
        saver.add_result(result)
        progress_callback()
        return result

    # Short-circuit for Gmail free domain: don't check MX
    if domain == 'gmail.com':
        result = {**entry, 'provider': 'Gmail (free)', 'mx': [], 'error': None}
        saver.add_result(result)
        progress_callback()
        return result

    resolver = get_resolver()
    retry_count = 0
    last_exception = None

    while retry_count <= MAX_RETRIES:
        try:
            # Check MX records directly
            answers = resolver.resolve(entry['domain'], 'MX')
            if not answers:
                result = {**entry, 'provider': 'NoMX', 'mx': [], 'error': "No MX records (empty response)"}
                saver.add_result(result)
                progress_callback()
                return result

            mx_records = [str(r.exchange) for r in answers]
            provider = detect_provider(mx_records, domain=entry['domain'])
            result = {**entry, 'provider': provider, 'mx': mx_records, 'error': None}
            saver.add_result(result)
            progress_callback()
            return result

        except dns.resolver.NoAnswer:
            # Domain exists but no MX records
            result = {**entry, 'provider': 'NoMX', 'mx': [], 'error': "Domain exists but no MX records"}
            saver.add_result(result)
            progress_callback()
            return result
        except (dns.resolver.NoNameservers, dns.resolver.Timeout) as e:
            last_exception = str(e)
            retry_count += 1
            if retry_count <= MAX_RETRIES:
                time.sleep(RETRY_DELAY * retry_count)  # Exponential backoff
        except Exception as e:
            last_exception = str(e)
            retry_count = MAX_RETRIES + 1  # Don't retry on other errors
            break

    # If we get here, all retries failed
    result = {**entry, 'provider': 'Error', 'mx': [], 'error': f"DNS lookup failed: {last_exception}"}
    saver.add_result(result)
    progress_callback()
    return result


class EmailSorterGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Email Provider Sorter")
        self.root.geometry("800x700")
        self.root.configure(bg='#f0f0f0')

        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.saver = None
        self.entries = []
        self.processed_count = 0
        self.total_count = 0
        self.is_processing = False
        self.max_workers = MAX_WORKERS
        self.update_timer = None
        self.processing_thread = None
        self.should_stop = False
        self.last_folder = os.path.expanduser("~\\Desktop")  # Remember last used folder

        self.setup_ui()

    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)

        # Title
        title_label = ttk.Label(main_frame, text="Email Provider Sorter",
                                font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # File selection
        ttk.Label(main_frame, text="Input File:").grid(row=1, column=0, sticky=tk.W, pady=5)

        self.file_var = tk.StringVar()
        file_entry = ttk.Entry(main_frame, textvariable=self.file_var, width=50)
        file_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)

        browse_btn = ttk.Button(main_frame, text="Browse", command=self.browse_file)
        browse_btn.grid(row=1, column=2, padx=(5, 0), pady=5)

        # Thread count configuration
        ttk.Label(main_frame, text="Thread Count:").grid(row=2, column=0, sticky=tk.W, pady=5)

        self.thread_var = tk.StringVar(value=str(MAX_WORKERS))
        thread_entry = ttk.Entry(main_frame, textvariable=self.thread_var, width=10)
        thread_entry.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=5)

        ttk.Label(main_frame, text="(1-299, higher = faster but may cause rate limiting)").grid(row=3, column=0,
                                                                                                columnspan=2,
                                                                                                sticky=tk.W,
                                                                                                padx=(0, 0),
                                                                                                pady=(0, 10))

        # Start button
        self.start_btn = ttk.Button(main_frame, text="Start Processing",
                                    command=self.start_processing, state='disabled')
        self.start_btn.grid(row=4, column=0, columnspan=3, pady=20)

        # Progress frame
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        progress_frame.columnconfigure(0, weight=1)

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                            maximum=100, length=400)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # Progress label
        self.progress_label = ttk.Label(progress_frame, text="Ready to start")
        self.progress_label.grid(row=1, column=0, pady=(0, 10))

        # Results frame
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding="10")
        results_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)

        # Results treeview
        columns = ('Provider', 'Count', 'Percentage')
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=10)

        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=150, anchor='center')

        # Scrollbar for results
        results_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=results_scrollbar.set)

        self.results_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        results_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))

    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select input file",
            filetypes=[
                ("All files", "*.*"),  # Show all files first
                ("Excel files", "*.xlsx;*.xls"),
                ("CSV files", "*.csv"),
                ("Text files", "*.txt"),
                ("All supported files", "*.xlsx;*.xls;*.csv;*.txt")
            ],
            initialdir=self.last_folder
        )
        if filename:
            self.file_var.set(filename)
            # Remember the folder for next time
            self.last_folder = os.path.dirname(filename)
            self.start_btn.config(state='normal')

    def update_results(self, counts):
        # Cancel any pending update
        if self.update_timer:
            self.root.after_cancel(self.update_timer)

        # Schedule update with delay to prevent flickering
        self.update_timer = self.root.after(100, lambda: self._update_results_actual(counts))

    def _update_results_actual(self, counts):
        # Clear existing items
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        # Add new results
        total = sum(counts.values())
        for provider, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total * 100) if total > 0 else 0
            self.results_tree.insert('', 'end', values=(
                provider,
                count,
                f"{percentage:.1f}%"
            ))

    def update_progress(self):
        if self.total_count > 0:
            percentage = (self.processed_count / self.total_count) * 100
            self.progress_var.set(percentage)
            self.progress_label.config(text=f"Processed: {self.processed_count}/{self.total_count} ({percentage:.1f}%)")

    def start_processing(self):
        if self.is_processing:
            # Stop processing
            self.stop_processing()
            return

        input_file = self.file_var.get()
        if not os.path.exists(input_file):
            messagebox.showerror("Error", f"File '{input_file}' not found.")
            return

        # Validate thread count
        try:
            thread_count = int(self.thread_var.get())
            if thread_count < 1 or thread_count > 299:
                messagebox.showerror("Error", "Thread count must be between 1 and 299.")
                return
            self.max_workers = thread_count
        except ValueError:
            messagebox.showerror("Error", "Thread count must be a valid number.")
            return

        try:
            # Extract domains
            self.status_var.set("Extracting email domains...")
            self.entries = extract_domains(input_file)

            if not self.entries:
                messagebox.showwarning("Warning", "No valid email entries found.")
                return

            # Optimize entries to avoid checking duplicate domains
            self.status_var.set("Optimizing domain list...")
            self.optimized_entries, self.domain_to_entries = optimize_entries(self.entries)

            # Initialize processing
            unique_domains = len(self.optimized_entries)
            self.total_count = unique_domains  # Total unique domains to process
            self.processed_count = 0
            self.is_processing = True
            self.start_btn.config(state='normal', text="Stop Processing")

            # Clear results
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)

            # Initialize saver with GUI callback
            self.saver = RealTimeSaver(gui_callback=self.update_results)

            # Start processing in background
            total_entries = len(self.entries)
            self.status_var.set(
                f"Processing {total_entries} entries ({unique_domains} unique domains) with {self.max_workers} threads...")
            self.processing_thread = threading.Thread(target=self.process_domains, daemon=True)
            self.processing_thread.start()

        except Exception as e:
            messagebox.showerror("Error", f"Error starting processing: {str(e)}")
            self.is_processing = False
            self.start_btn.config(state='normal', text="Start Processing")

    def process_domains(self):
        try:
            start_time = time.time()

            # First pass - process optimized domains (unique domains only)
            self.root.after(0, lambda: self.status_var.set("Processing domains (first pass)..."))
            error_entries = self.process_batch(self.optimized_entries)

            if self.should_stop:
                self.root.after(0, self.processing_stopped, time.time() - start_time)
                return

            # Second pass - retry error domains
            if error_entries:
                self.root.after(0, lambda: self.status_var.set(f"Retrying {len(error_entries)} failed domains..."))
                self.processed_count = 0
                self.total_count = len(error_entries)
                self.update_progress()

                # Wait a bit before retrying
                time.sleep(1)  # Reduced from 2 to 1 second

                if self.should_stop:
                    self.root.after(0, self.processing_stopped, time.time() - start_time)
                    return

                # Retry error domains
                final_error_entries = self.process_batch(error_entries)

                if self.should_stop:
                    self.root.after(0, self.processing_stopped, time.time() - start_time)
                    return

                if final_error_entries:
                    self.root.after(0, lambda: self.status_var.set(
                        f"Final retry for {len(final_error_entries)} domains..."))
                    self.processed_count = 0
                    self.total_count = len(final_error_entries)
                    self.update_progress()

                    # Final retry with longer delays
                    time.sleep(1.5)  # Reduced from 3 to 1.5 seconds

                    if self.should_stop:
                        self.root.after(0, self.processing_stopped, time.time() - start_time)
                        return

                    self.process_batch(final_error_entries, max_retries=3, retry_delay=1)

            # Final wait for saver
            while not self.saver.queue.empty() and not self.should_stop:
                time.sleep(0.1)

            elapsed = time.time() - start_time

            # Update GUI on main thread
            if self.should_stop:
                self.root.after(0, self.processing_stopped, elapsed)
            else:
                self.root.after(0, self.processing_complete, elapsed)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Processing error: {str(e)}"))
            self.root.after(0, self.reset_ui)

    def process_batch(self, entries, max_retries=MAX_RETRIES, retry_delay=RETRY_DELAY):
        error_entries = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for entry in entries:
                if self.should_stop:
                    break
                future = executor.submit(self.check_domain_with_custom_retry, entry, max_retries, retry_delay)
                futures.append(future)

            for future in concurrent.futures.as_completed(futures):
                if self.should_stop:
                    break
                try:
                    result = future.result()
                    if result and result.get('provider') == 'Error':
                        # Use the representative entry for retries
                        error_entries.append({
                            'line': result['line'],
                            'domain': result['domain'],
                            'email': result['email']
                        })
                except Exception:
                    pass

        return error_entries

    def check_domain_with_custom_retry(self, entry, max_retries, retry_delay):
        resolver = get_resolver()
        retry_count = 0
        last_exception = None

        # Get all entries for this domain
        domain = entry['domain']
        all_entries = self.domain_to_entries.get(domain, [entry])

        # Short-circuit for Microsoft consumer email domains: don't check MX
        domain_lower = domain.lower()

        # Check if domain is exactly outlook.com, msn.com, live.com, or hotmail.com
        microsoft_free_domains = {'outlook.com', 'msn.com', 'live.com', 'hotmail.com'}
        if domain_lower in microsoft_free_domains:
            result = {**entry, 'provider': 'Microsoft Free', 'mx': [], 'error': None, 'all_entries': all_entries}
            self.saver.add_result(result)
            return result

        # Short-circuit for Gmail free domain: don't check MX
        if domain_lower == 'gmail.com':
            result = {**entry, 'provider': 'Gmail (free)', 'mx': [], 'error': None, 'all_entries': all_entries}
            self.saver.add_result(result)
            return result

        while retry_count <= max_retries:
            try:
                # Check MX records directly
                answers = resolver.resolve(entry['domain'], 'MX')
                if not answers:
                    result = {**entry, 'provider': 'NoMX', 'mx': [], 'error': "No MX records (empty response)",
                              'all_entries': all_entries}
                    self.saver.add_result(result)
                    return result

                mx_records = [str(r.exchange) for r in answers]
                provider = detect_provider(mx_records, domain=entry['domain'])
                result = {**entry, 'provider': provider, 'mx': mx_records, 'error': None, 'all_entries': all_entries}
                self.saver.add_result(result)
                return result

            except dns.resolver.NoAnswer:
                # Domain exists but no MX records
                result = {**entry, 'provider': 'NoMX', 'mx': [], 'error': "Domain exists but no MX records",
                          'all_entries': all_entries}
                self.saver.add_result(result)
                return result
            except (dns.resolver.NoNameservers, dns.resolver.Timeout) as e:
                last_exception = str(e)
                retry_count += 1
                if retry_count <= max_retries:
                    time.sleep(retry_delay * retry_count)  # Exponential backoff
            except Exception as e:
                last_exception = str(e)
                retry_count = max_retries + 1  # Don't retry on other errors
                break

        # If we get here, all retries failed
        result = {**entry, 'provider': 'Error', 'mx': [], 'error': f"DNS lookup failed: {last_exception}",
                  'all_entries': all_entries}
        self.saver.add_result(result)
        return result

    def progress_callback(self):
        # Only increment progress when we actually process a domain
        # This will be called from the saver when a result is actually saved
        self.processed_count += 1
        # Use after_idle to reduce GUI updates and prevent flickering
        self.root.after_idle(self.update_progress)

    def processing_complete(self, elapsed):
        self.is_processing = False
        self.start_btn.config(state='normal', text="Start Processing")
        self.status_var.set(f"Completed in {elapsed:.2f} seconds")

        if self.saver:
            self.saver.stop()

        # Show completion message
        total_processed = sum(self.saver.counts.values()) if self.saver else 0
        error_count = self.saver.counts.get('Error', 0) if self.saver else 0

        message = f"Processing completed!\n\n"
        message += f"Total processed: {total_processed}\n"
        message += f"Time elapsed: {elapsed:.2f} seconds\n"
        message += f"Final errors: {error_count}\n\n"
        message += f"Results saved to 'provider_results' folder.\n\n"

        if error_count > 0:
            message += "Note: Domains with errors were retried multiple times.\n"
            message += "Check the 'errors.txt' file for final failed domains."

        messagebox.showinfo("Complete", message)

    def stop_processing(self):
        self.should_stop = True
        self.status_var.set("Stopping...")
        if self.saver:
            self.saver.stop()

    def processing_stopped(self, elapsed):
        self.is_processing = False
        self.should_stop = False
        self.start_btn.config(state='normal', text="Start Processing")
        self.status_var.set(f"Stopped after {elapsed:.2f} seconds")

        # Show completion message
        total_processed = sum(self.saver.counts.values()) if self.saver else 0

        message = f"Processing stopped!\n\n"
        message += f"Total processed: {total_processed}\n"
        message += f"Time elapsed: {elapsed:.2f} seconds\n\n"
        message += f"Results saved to 'provider_results' folder."

        messagebox.showinfo("Stopped", message)

    def reset_ui(self):
        self.is_processing = False
        self.should_stop = False
        self.start_btn.config(state='normal', text="Start Processing")
        self.status_var.set("Ready")

    def on_closing(self):
        """Handle window close event - stop processing and clean up"""
        if self.is_processing:
            # Stop processing if it's running
            self.should_stop = True
            self.status_var.set("Stopping...")

            # Stop the saver
            if self.saver:
                self.saver.stop()

            # Wait a moment for threads to stop
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=2)

        # Close any open file handles
        if self.saver:
            for f in self.saver.file_handles.values():
                try:
                    f.close()
                except:
                    pass

        # Destroy the window
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def main():
    app = EmailSorterGUI()
    app.run()


if __name__ == "__main__":
    main()