import smtplib
import dns.resolver
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import os
import random
import string

# Function to generate a random string of given length
def generate_random_string(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

# Function to get MX records for a domain
def get_mx_records(domain):
    try:
        records = dns.resolver.resolve(domain, 'MX')
        mx_records = sorted(records, key=lambda record: record.preference)
        return [str(record.exchange) for record in mx_records]
    except Exception as e:
        print(f"Failed to resolve MX records for {domain}: {e}")
        return []

# Function to save successfully sent emails
def save_successful_emails(email_list, file_path='successful_emails.txt'):
    with open(file_path, 'a') as file:
        for email in email_list:
            file.write(email + '\n')

# Function to send email via MX record with BCC and optional attachment
def send_email_via_mx(to_emails, from_email, from_name, subject, html_body, attachment=None):
    if not to_emails:
        return

    # Extract domain from the first email (assuming all emails are from the same domain)
    domain = to_emails[0].split('@')[1]
    mx_records = get_mx_records(domain)

    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = f"{from_name} <{from_email}>"
    msg['To'] = from_email  # To field can be any valid email address
    msg['Bcc'] = ', '.join(to_emails)
    msg.attach(MIMEText(html_body, 'html'))

    # Attach the file if provided
    if attachment:
        attach_file_to_email(msg, attachment)

    for mx in mx_records:
        try:
            with smtplib.SMTP(mx) as server:
                server.sendmail(from_email, to_emails, msg.as_string())
                print(f"Batch of {len(to_emails)} emails sent successfully from {from_email}")

                # Save the successfully sent emails to a file
                save_successful_emails(to_emails)

                break
        except Exception as e:
            print(f"Failed to send batch of {len(to_emails)} emails via {mx} from {from_email}: {e}")

# Function to read email list from a file
def read_email_list(file_path):
    with open(file_path, 'r') as file:
        emails = [line.strip() for line in file if line.strip()]
    return emails

# Function to batch the email list
def batch_email_list(email_list, batch_size):
    for i in range(0, len(email_list), batch_size):
        yield email_list[i:i + batch_size]

# Function to read HTML content from a file
def read_html_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

# Function to attach file to email
def attach_file_to_email(msg, file_path):
    with open(file_path, 'rb') as file:
        # Create the attachment
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(file.read())
        encoders.encode_base64(part)

        # Extract the original file name and extension
        file_name = os.path.basename(file_path)
        file_base, file_ext = os.path.splitext(file_name)

        # Generate a unique name for the attachment
        unique_suffix = generate_random_string(7)
        unique_file_name = f"{file_base}-{unique_suffix}{file_ext}"

        # Add the attachment to the message
        part.add_header('Content-Disposition', f'attachment; filename="{unique_file_name}"')
        msg.attach(part)

# Ask user if they want to use attachments
use_attachments = input("Do you want to attach files? (y/n): ").lower() == 'y'

# If using attachments, read files from the 'attachments' folder
attachments = []
if use_attachments:
    attachment_folder = 'attachments'
    attachments = [os.path.join(attachment_folder, f) for f in os.listdir(attachment_folder) if os.path.isfile(os.path.join(attachment_folder, f))]

# List of 'from' emails to rotate through
from_emails = [
"noreply@wickes.co.uk",
"noreply@bq.com",
"noreply@toolstation.com",
"noreply@homebase.co.uk",
"noreply@axminster.co.uk",
"noreply@ironmongerydirect.co.uk",
"noreply@megadepot.com",
"noreply@tooltrolley.co.uk",
"noreply@uktoolcentre.co.uk",
"noreply@my-tool-shed.co.uk",
"noreply@toolsaver.co.uk",
"noreply@power-tools-pro.co.uk",
"noreply@toolstop.co.uk",
"noreply@buybrandtools.com",
"noreply@tool-net.co.uk",
"noreply@clarketooling.co.uk",
"noreply@directtools.com",
"noreply@ffx.co.uk",
"noreply@boots.com"
"noreply@toolup.com",
"noreply@toolnut.com"

]

# Email details (with randomisation)
from_name_base = "Fresh Face, Fresh Sheets"
subject_base = "Say Goodbye to Skin Issues with Miracle's Silver Sheets"

# Read HTML content from file
html_body = read_html_file('insta.html')

# Read email list from file
email_list = read_email_list('mails-insta.txt')

# Send email in batches of 100
batch_size = 100
batches = list(batch_email_list(email_list, batch_size))

# Use ThreadPoolExecutor to send emails concurrently
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = []
    for i, batch in enumerate(batches):
        # Rotate through the list of 'from_emails' cyclically
        from_email = from_emails[i % len(from_emails)]

        # Randomize from_name and subject with a 6 character suffix
        from_name = f"{from_name_base}-{generate_random_string(6)}"
        subject = f"{subject_base}-{generate_random_string(6)}"

        # Attach one random file for each batch if attachments are used
        attachment = random.choice(attachments) if use_attachments and attachments else None

        # Submit the email sending task
        futures.append(executor.submit(send_email_via_mx, batch, from_email, from_name, subject, html_body, attachment))
        time.sleep(3)  # Sleep for 3 seconds between sending each batch

    for future in as_completed(futures):
        try:
            future.result()
        except Exception as exc:
            print(f"Batch generated an exception: {exc}")
