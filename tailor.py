#!/usr/bin/env python3
"""
Script: tailor.py
Description: Tailor a LaTeX resume to a specific company and job description using OpenAI's API.
             Preserves the original document structure, spacing, and formatting,
             focusing only on updating the Work Experience and Technical Skills sections with tailored bullet points and metrics.
"""
import os
import sys
import re
import subprocess
import argparse
import smtplib
import getpass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from pathlib import Path

from openai import OpenAI

# Version information
__version__ = "1.2.0"

def setup_output_directory():
    """Create and set up the output directory for resumes."""
    # Create script_resumes folder on desktop
    user_home = os.path.expanduser("~")
    desktop_path = os.path.join(user_home, "Desktop")
    output_dir = os.path.join(desktop_path, "script_resumes")
    
    # Create the directory if it doesn't exist
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")
        except Exception as e:
            print(f"Warning: Could not create output directory: {e}")
            # Fall back to current directory
            output_dir = os.getcwd()
            print(f"Using current directory instead: {output_dir}")
    
    return output_dir


def get_interactive_inputs():
    """Get inputs interactively from the user via console."""
    print("\n=== Resume Tailoring Tool ===")
    print("This tool will help you tailor your resume for a specific job and company.")
    
    # Set up output directory
    output_dir = setup_output_directory()
    print(f"All files will be saved to: {output_dir}")
    
    # Default to Desktop location for main.tex
    user_home = os.path.expanduser("~")
    desktop_path = os.path.join(user_home, "Desktop")
    default_resume_path = os.path.join(desktop_path, "main.tex")
    
    if os.path.exists(default_resume_path):
        default_path = default_resume_path
        print(f"Found resume at: {default_resume_path}")
    else:
        default_path = "main.tex"
    
    # Get LaTeX template path
    template_path = input(f"Enter path to your LaTeX resume [default: {default_path}]: ").strip()
    if not template_path:
        template_path = default_path
    
    # Validate the template path
    if not os.path.exists(template_path):
        print(f"Error: Resume template file '{template_path}' not found.", file=sys.stderr)
        sys.exit(1)
    
    print(f"✅ Resume template found at: {template_path}")
    
    # Get company name
    company_name = ""
    while not company_name:
        company_name = input("\nEnter the target company name: ").strip()
        if not company_name:
            print("Company name is required.")
    
    print(f"✅ Tailoring for company: {company_name}")
    
    # Get role being applied for
    role_name = input("\nEnter the role you're applying for: ").strip()
    while not role_name:
        print("Role name is required for effective tailoring.")
        role_name = input("Enter the role you're applying for: ").strip()
    
    print(f"✅ Tailoring for role: {role_name}")
    
    # Always use keywords.txt from desktop for keywords to emphasize
    keywords_path = os.path.join(desktop_path, "keywords.txt")
    keywords = []
    
    # Try to read the keywords from this file (optional)
    try:
        with open(keywords_path, 'r', encoding='utf-8') as f:
            keywords_content = f.read().strip()
        if keywords_content:
            # Split by lines and clean up
            keywords = [kw.strip() for kw in keywords_content.split('\n') if kw.strip()]
            print(f"✅ Keywords loaded from: {keywords_path}")
        print(f"✅ Will emphasize these keywords: {', '.join(keywords)}")
        else:
            print(f"⚠️  Keywords file '{keywords_path}' is empty - proceeding without keyword emphasis")
    except FileNotFoundError:
        print(f"⚠️  Keywords file '{keywords_path}' not found - proceeding without keyword emphasis")
        print("    (Create ~/Desktop/keywords.txt with one keyword per line to enable keyword emphasis)")
    except Exception as e:
        print(f"⚠️  Error reading keywords file: {e} - proceeding without keyword emphasis")
    
    # Always use job.txt from desktop for job description
    job_description_path = os.path.join(desktop_path, "job.txt")
    
    # Try to read the job description from this file
    try:
        with open(job_description_path, 'r', encoding='utf-8') as f:
            job_description = f.read().strip()
        if not job_description:
            print(f"Error: Job description file '{job_description_path}' is empty.", file=sys.stderr)
            sys.exit(1)
    except FileNotFoundError:
        print(f"Error: Job description file '{job_description_path}' not found.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading job description file: {e}", file=sys.stderr)
        sys.exit(1)
    
    description_preview = job_description[:150] + "..." if len(job_description) > 150 else job_description
    print(f"✅ Job description loaded from: {job_description_path}")
    print(f"Preview: {description_preview}")
    
    # Always use pain_points.txt from desktop for company pain points analysis
    pain_points_path = os.path.join(desktop_path, "pain_points.txt")
    pain_points = ""
    
    # Try to read the pain points from this file (optional)
    try:
        with open(pain_points_path, 'r', encoding='utf-8') as f:
            pain_points = f.read().strip()
        if pain_points:
            pain_points_preview = pain_points[:150] + "..." if len(pain_points) > 150 else pain_points
            print(f"✅ Pain points analysis loaded from: {pain_points_path}")
            print(f"Preview: {pain_points_preview}")
        else:
            print(f"⚠️  Pain points file '{pain_points_path}' is empty - proceeding without pain points analysis")
    except FileNotFoundError:
        print(f"⚠️  Pain points file '{pain_points_path}' not found - proceeding without pain points analysis")
    except Exception as e:
        print(f"⚠️  Error reading pain points file: {e} - proceeding without pain points analysis")
    
    # Generate file names in the output directory
    output_basename = f"{company_name.lower().replace(' ', '_')}_{role_name.lower().replace(' ', '_')}_resume"
    output_tex = os.path.join(output_dir, f"{output_basename}.tex")
    output_pdf = os.path.join(output_dir, f"{output_basename}.pdf")
    
    print(f"✅ LaTeX will be saved to: {output_tex}")
    print(f"✅ PDF will be saved to: {output_pdf}")
    
    # Get model with default
    model = input("\nEnter OpenAI model to use [default: gpt-4o]: ").strip()
    if not model:
        model = "gpt-4o"
    
    print(f"✅ Using model: {model}")
    
    # Ask if user wants to generate a recruiter email
    generate_email = input("\nWould you like to generate a recruiter email too? (y/n): ").strip().lower()
    generate_email = generate_email in ('y', 'yes')
    
    # If generating email, get recruiter details
    recruiter_name = None
    recruiter_position = None
    recruiter_email = None
    if generate_email:
        recruiter_inputs = get_recruiter_inputs()
        recruiter_name = recruiter_inputs["recruiter_name"]
        recruiter_position = recruiter_inputs["recruiter_position"]
        recruiter_email = recruiter_inputs["recruiter_email"]
    
    print("\n=== Starting Resume Tailoring Process ===")
    
    return {
        "template": template_path,
        "company": company_name,
        "role": role_name,
        "description": job_description,
        "pain_points": pain_points,
        "output_tex": output_tex,
        "output_pdf": output_pdf,
        "model": model,
        "generate_email": generate_email,
        "recruiter_name": recruiter_name,
        "recruiter_position": recruiter_position,
        "recruiter_email": recruiter_email,
        "keywords": keywords
    }


def process_command_line_args():
    """Process command line arguments for batch or non-interactive mode."""
    parser = argparse.ArgumentParser(description=f"Tailor a LaTeX resume for a specific job and company (version {__version__}).")
    
    parser.add_argument("--template", "-t", help="Path to LaTeX resume template file")
    parser.add_argument("--company", "-c", help="Target company name")
    parser.add_argument("--role", "-r", help="Target role or position")
    parser.add_argument("--job-description", "-j", help="Path to job description file")
    parser.add_argument("--pain-points", "-p", help="Path to pain points analysis file")
    parser.add_argument("--output", "-o", help="Output directory (default: Desktop/script_resumes)")
    parser.add_argument("--model", "-m", default="gpt-4o", help="OpenAI model to use (default: gpt-4o)")
    parser.add_argument("--batch", "-b", help="Path to CSV file with batch job data (company,role,job_description_file,pain_points,keywords,keywords_file,recruiter_name,recruiter_position,recruiter_email)")
    parser.add_argument("--email", "-e", action="store_true", help="Generate a recruiter email")
    parser.add_argument("--recruiter", help="Recruiter's name (required with --email)")
    parser.add_argument("--recruiter-position", help="Recruiter's position (optional)")
    parser.add_argument("--recruiter-email", help="Recruiter's email address for sending")
    parser.add_argument("--version", "-v", action="store_true", help="Show version information")
    parser.add_argument("--keywords", "-k", nargs="+", help="Keywords to emphasize in the resume")
    parser.add_argument("--keywords-file", help="Path to keywords file (one keyword per line)")
    
    args = parser.parse_args()
    
    # Show version if requested
    if args.version:
        print(f"Resume Tailoring Tool version {__version__}")
        sys.exit(0)
    
    # If batch mode is specified, ignore other arguments
    if args.batch:
        return {"batch": args.batch, "model": args.model}
    
    # Check for email consistency
    if args.email and not args.recruiter:
        print("Error: --recruiter NAME is required when using --email", file=sys.stderr)
        parser.print_help()
        sys.exit(1)
    
    # If any of the required individual args are provided, ensure all are provided
    if any([args.template, args.company, args.role, args.job_description]):
        missing = []
        if not args.template:
            missing.append("--template")
        if not args.company:
            missing.append("--company")
        if not args.role:
            missing.append("--role")
        if not args.job_description:
            missing.append("--job-description")
        
        if missing:
            print(f"Error: Missing required arguments: {', '.join(missing)}", file=sys.stderr)
            parser.print_help()
            sys.exit(1)
        
        # All required args provided, process in non-interactive mode
        output_dir = args.output if args.output else setup_output_directory()
        
        # Read job description
        try:
            with open(args.job_description, 'r', encoding='utf-8') as f:
                job_description = f.read().strip()
        except Exception as e:
            print(f"Error reading job description file: {e}", file=sys.stderr)
            sys.exit(1)
        
        # Read pain points analysis if provided
        pain_points = ""
        if args.pain_points:
            try:
                with open(args.pain_points, 'r', encoding='utf-8') as f:
                    pain_points = f.read().strip()
                print(f"✅ Pain points analysis loaded from: {args.pain_points}")
            except Exception as e:
                print(f"Warning: Error reading pain points file: {e}", file=sys.stderr)
                print("Proceeding without pain points analysis")
        
        # Generate output file names
        output_basename = f"{args.company.lower().replace(' ', '_')}_{args.role.lower().replace(' ', '_')}_resume"
        output_tex = os.path.join(output_dir, f"{output_basename}.tex")
        output_pdf = os.path.join(output_dir, f"{output_basename}.pdf")
        
        # Handle keywords - either from command line args or keywords file
        keywords = None
        if args.keywords:
            keywords = args.keywords
            print(f"✅ Will emphasize these keywords: {', '.join(keywords)}")
        elif args.keywords_file:
            try:
                with open(args.keywords_file, 'r', encoding='utf-8') as f:
                    keywords_content = f.read().strip()
                if keywords_content:
                    keywords = [kw.strip() for kw in keywords_content.split('\n') if kw.strip()]
                    print(f"✅ Keywords loaded from: {args.keywords_file}")
                    print(f"✅ Will emphasize these keywords: {', '.join(keywords)}")
                else:
                    print(f"⚠️  Keywords file '{args.keywords_file}' is empty - proceeding without keyword emphasis")
            except Exception as e:
                print(f"Warning: Error reading keywords file: {e}", file=sys.stderr)
                print("Proceeding without keyword emphasis")
        
        return {
            "template": args.template,
            "company": args.company,
            "role": args.role,
            "description": job_description,
            "pain_points": pain_points,
            "output_tex": output_tex,
            "output_pdf": output_pdf,
            "model": args.model,
            "generate_email": args.email,
            "recruiter_name": args.recruiter if args.email else None,
            "recruiter_position": args.recruiter_position,
            "recruiter_email": args.recruiter_email,
            "keywords": keywords
        }
    
    # No command line args provided, use interactive mode
    return None


def load_template(path: str) -> str:
    """Read the LaTeX template file and return its content."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: Resume template file '{path}' not found.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading template file: {e}", file=sys.stderr)
        sys.exit(1)


def tailor_resume(
    latex_resume_content,
    company_name,
    job_description,
    model_name,
    output_tex_path="tailored_resume.tex",
    output_pdf_path="tailored_resume.pdf",
    role_name="the position",
    generate_email=False,
    recruiter_name=None,
    recruiter_position=None,
    recruiter_email=None,
    keywords=None,
    pain_points=""
):
    """Tailor the LaTeX resume using OpenAI API and save as PDF."""
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set.", file=sys.stderr)
        print("Please set your OpenAI API key using: export OPENAI_API_KEY='your-api-key'", file=sys.stderr)
        sys.exit(1)

    print("\n1. Creating tailored content for your resume...")
    
    # Add keywords section to prompt if provided
    keywords_section = ""
    if keywords and len(keywords) > 0:
        keywords_section = f"""
8. REQUIRED KEYWORDS INTEGRATION:
   - Naturally integrate these keywords into the resume: {', '.join(keywords)}
   - Do NOT force keywords where they don't fit naturally
   - Modify existing bullet points to incorporate keywords where they make sense
   - Only use keywords where they accurately reflect the experience
   - If a keyword cannot be naturally integrated, it's better to omit it than force it
   - Focus on the Technical Skills section and Work Experience bullet points for keyword integration
"""

    # Add pain points section to prompt if provided
    pain_points_section = ""
    if pain_points and pain_points.strip():
        pain_points_section = f"""

COMPANY PAIN POINTS ANALYSIS:
{pain_points.strip()}
"""

    # Construct the prompt - note the use of raw strings (r) to handle LaTeX backslashes properly
    prompt = f"""
SYSTEM:
You are an expert résumé consultant and LaTeX engineer with deep experience in applicant tracking systems (ATS) and keyword optimization.
Your sole task is to tailor an existing LaTeX résumé for {company_name} and the {role_name} role,
while preserving *every* LaTeX formatting token: this includes all \\\\, \\\\section, %, {{}}, \\\\item, whitespace, macro usage, and vertical spacing
The résumé MUST remain exactly one page in length, with identical formatting and layout to the original.

USER:
Company: "{company_name}"
Role: "{role_name}"
Job Description:
{job_description}{pain_points_section}

Résumé (LaTeX source):
{latex_resume_content}

INSTRUCTIONS:

1. INITIAL ANALYSIS:
   - Identify the 5–8 most critical keywords and "must-have" skills from the job description
   - Highlight the employer's main pain points or challenges this role is solving{' (use the provided pain points analysis above to guide this)' if pain_points_section else ''}
   - Note the specific tools, frameworks, technical stack, or methodologies mentioned

2. PRESERVE FORMAT:
   - Maintain **exact** one-page length—overflow is not permitted
   - Preserve every LaTeX formatting token: this includes all \\\\, \\\\section, %, {{}}, \\\\item, whitespace, macro usage, and vertical spacing
   - Do **not** change indentation, spacing, or remove any section or comment

3. NEVER FABRICATE:
   - Do **not** invent any job title, skill, project, or technology not already present in the résumé
   - If a required skill/tool is not in the résumé, you may reference transferable concepts or similar technologies already present
   - Under no circumstances should you create a role, experience, or qualification that doesn't exist in the original

4. TAILORING WORK EXPERIENCE:
   - Modify only the *content* of Work Experience bullet points and the Technical Skills section
   - Rephrase, reorder, or condense each bullet while keeping the same number of bullets per role
   - Focus on the employer's pain points and emphasize relevant experience using transferable skills where necessary
   - Ensure the **first 1–2 bullets per role** address the role's primary needs
   - Apply the **PAR structure** to each bullet:
     • *Problem* (optional) — align with JD pain points
     • *Action* — what you did (based on original résumé only)
     • *Result* — outcome, preferably quantified (%, $, users, time saved, etc.)
     • THE IMPACT (RESULT) is needed in each bullet point because it is the most important part of the bullet point

5. SKILLS & KEYWORDS:
   - Incorporate **exact-match keywords** from the job description into the Technical Skills and bullets (especially first bullet of each role)
   - If ATS-relevant terms are implied but not explicitly stated in the résumé, surface them using standard terminology
   - Avoid synonyms—use the employer's exact phrasing when possible

6. STYLE & STRUCTURE:
   - Do not change section order, job count, or macro definitions
   - Do not change the number of bullets in the Work Experience section
   - Keep each bullet approximately the same length and line count to maintain layout       
   - Begin all bullets with a strong action verb, in correct tense
   - If a revised bullet risks layout overflow, shorten wording to stay on one page—do not drop any bullet
{keywords_section}
7. FINAL OUTPUT:
   - Output a complete and valid LaTeX document
   - It must start with \\\\documentclass and end with \\\\end{{document}}
   - Do **not** wrap in markdown, backticks, or include any explanation or commentary

Please generate the tailored LaTeX résumé now.
"""

    print(f"2. Sending request to OpenAI API ({model_name})...")
    
    # Call OpenAI API using the updated client library
    try:
        client = OpenAI(api_key=api_key)
        print("   - API request sent, waiting for response...")
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are an expert resume tailoring specialist with LaTeX expertise."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4096
        )
        tailored_latex = response.choices[0].message.content
        print("   - Response received from OpenAI")
    except Exception as e:
        print(f"Error calling OpenAI API: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Clean up the tailored LaTeX to remove any markdown or code formatting
    tailored_latex = clean_latex_content(tailored_latex)
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_tex_path)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
        except Exception as e:
            print(f"Warning: Could not create output directory: {e}")
            
    # Save tailored LaTeX to file
    print(f"\n3. Saving tailored LaTeX content to {output_tex_path}...")
    write_file(tailored_latex, output_tex_path)
    print(f"   - LaTeX file saved successfully")
    
    # Compile the tailored LaTeX to PDF
    print(f"\n4. Compiling LaTeX to PDF...")
    compiled = False
    try:
        compile_pdf(output_tex_path, output_pdf_path, company_name)
        print(f"\n✅ SUCCESS! Tailored resume saved to {output_pdf_path}")
        print(f"   You can now use this PDF for your application to {company_name} for the {role_name} role")
        compiled = True
    except Exception as e:
        print(f"\nWarning: Could not compile PDF automatically: {e}", file=sys.stderr)
        print(f"Your tailored LaTeX has been saved to {output_tex_path}")
        print("Options for creating PDF:")
        print("  1. Install LaTeX (e.g., MacTeX from https://www.tug.org/mactex/)")
        print("  2. Upload to an online LaTeX editor like Overleaf (https://www.overleaf.com)")
        print("  3. Use a LaTeX to PDF conversion service")
        
        # Offer to open Overleaf for the user
        should_open = input("\nWould you like to open Overleaf to convert your LaTeX to PDF? (y/n): ").strip().lower()
        if should_open in ('y', 'yes'):
            import webbrowser
            print("Opening Overleaf in your browser...")
            webbrowser.open("https://www.overleaf.com/project")
    
    # Open the generated .tex file in default editor
    open_in_editor(output_tex_path)
    
    # Generate email if requested
    if generate_email and recruiter_name:
        # We'll generate an email for the recruiter based on the tailored resume
        email_content = generate_recruiter_email(
            latex_resume_content=tailored_latex,
            company_name=company_name,
            role_name=role_name,
            job_description=job_description,
            recruiter_name=recruiter_name,
            recruiter_position=recruiter_position,
            model_name=model_name,
            api_key=api_key
        )
        
        # Save the email to a file
        email_basename = f"{company_name.lower().replace(' ', '_')}_{role_name.lower().replace(' ', '_')}_email.txt"
        email_path = os.path.join(output_dir, email_basename)
        write_file(email_content, email_path)
        
        print(f"\n✅ Recruiter email saved to: {email_path}")
        
        # Display email and offer to open in default editor
        print("\n" + "=" * 60)
        print("RECRUITER EMAIL:")
        print("-" * 60)
        print(email_content)
        print("-" * 60)
        
        # Open the email file in default editor
        open_in_editor(email_path)
        
        # If we have the recruiter's email, offer to send it directly
        if recruiter_email:
            should_send = input(f"\nWould you like to send this email to {recruiter_email} now? (y/n): ").strip().lower()
            if should_send in ('y', 'yes'):
                # Parse email content to get subject
                subject = extract_subject_from_email(email_content)
                
                # Send the email
                if compiled:
                    send_email(
                        recruiter_email, 
                        subject, 
                        email_content, 
                        output_pdf_path
                    )
                else:
                    print("\nWarning: Cannot attach PDF as it was not successfully compiled.")
                    should_continue = input("Send email without PDF attachment? (y/n): ").strip().lower()
                    if should_continue in ('y', 'yes'):
                        send_email(
                            recruiter_email, 
                            subject, 
                            email_content
                        )
        
        return {
            "resume_tex": output_tex_path,
            "resume_pdf": output_pdf_path if compiled else None,
            "email": email_path
        }
    
    return {
        "resume_tex": output_tex_path,
        "resume_pdf": output_pdf_path if compiled else None
    }


def generate_recruiter_email(
    latex_resume_content,
    company_name,
    role_name,
    job_description,
    recruiter_name,
    recruiter_position=None,
    model_name="gpt-4o",
    api_key=None
):
    """Generate a personalized email to a recruiter based on the resume and job description."""
    # If API key wasn't passed, try to get it from env
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key is required to generate emails")
    
    position_text = f", {recruiter_position}" if recruiter_position else ""
    print(f"\n5. Generating email to {recruiter_name}{position_text} at {company_name}...")
    
    # Extract plain text from LaTeX for better context
    plain_text_resume = extract_text_from_latex(latex_resume_content)
    
    # Construct the prompt
    prompt = f"""
TASK: Write a professional, personalized email from Rahul Menon (rahul.menon@hotmail.com) to {recruiter_name}{position_text} at {company_name} regarding the {role_name} position.

ABOUT THE COMPANY & ROLE:
{job_description}

MY BACKGROUND (from resume):
{plain_text_resume}

GUIDELINES:
1. Use a professional, conversational tone that's not overly formal
2. Be concise - no more than 4-5 short paragraphs
3. Include a clear subject line
4. Focus on 2-3 specific skills/experiences that directly address the company's needs
5. Do NOT oversell or use generic phrases like "I'm excited about the opportunity"
6. Demonstrate you understand the company's challenges and how you can help
7. Include a clear call to action (e.g., request for a call/interview)
8. Mention that your resume is attached
9. Sign off professionally

FORMAT:
- Start with the subject line, then the greeting
- Include "From: Rahul Menon <rahul.menon@hotmail.com>" in the header
- Write a complete email ready to send
"""

    # Call OpenAI API
    try:
        client = OpenAI(api_key=api_key)
        print(f"   - Sending email generation request to {model_name}...")
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are an expert at crafting effective job application emails that are professional and personalized."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2048
        )
        email_content = response.choices[0].message.content.strip()
        print("   - Email content received from OpenAI")
        return email_content
    except Exception as e:
        print(f"Error generating email: {e}", file=sys.stderr)
        return f"Error generating email: {e}"


def extract_text_from_latex(latex_content):
    """Extract plain text content from LaTeX for better context in email generation."""
    # Remove LaTeX commands and environments that aren't content
    text = latex_content
    
    # Remove common LaTeX commands
    text = re.sub(r'\\documentclass.*?\{.*?\}', '', text)
    text = re.sub(r'\\usepackage.*?\{.*?\}', '', text)
    text = re.sub(r'\\begin\{document\}', '', text)
    text = re.sub(r'\\end\{document\}', '', text)
    text = re.sub(r'\\maketitle', '', text)
    
    # Remove commands with options
    text = re.sub(r'\\[a-zA-Z]+(\[.*?\])?(\{.*?\})', r'\2', text)
    
    # Remove LaTeX comments
    text = re.sub(r'%.*', '', text)
    
    # Extract content from section environments
    text = re.sub(r'\\section\*?\{(.*?)\}', r'\n\n\1:\n', text)
    text = re.sub(r'\\subsection\*?\{(.*?)\}', r'\n\1:\n', text)
    
    # Extract item contents
    text = re.sub(r'\\item\s*', '\n- ', text)
    
    # Remove other LaTeX commands
    text = re.sub(r'\\[a-zA-Z]+', '', text)
    
    # Remove extra braces
    text = re.sub(r'\{|\}', '', text)
    
    # Remove extra spacing
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    # Truncate if too long
    if len(text) > 2000:
        text = text[:1997] + "..."
    
    return text.strip()


def clean_latex_content(content):
    """Clean up the LaTeX content to remove any unwanted formatting."""
    # Remove any markdown code block formatting (```latex ... ```)
    content = re.sub(r'^```latex\s*', '', content)
    content = re.sub(r'^```\s*', '', content)
    content = re.sub(r'\s*```$', '', content)
    
    # Remove any backticks that might have been added
    content = content.replace('`', '')
    
    # Check if the content begins with \documentclass
    if not content.strip().startswith('\\documentclass'):
        # Try to find where the actual LaTeX content begins
        match = re.search(r'(\\documentclass.*)', content, re.DOTALL)
        if match:
            content = match.group(1)
    
    return content


def write_file(content: str, path: str):
    """Write content to the given file path."""
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        print(f"Error writing to file {path}: {e}", file=sys.stderr)
        sys.exit(1)


def compile_pdf(tex_path: str, output_pdf: str, company_name: str):
    """
    Compile the LaTeX file to PDF using pdflatex.
    Requires a LaTeX distribution installed on the system.
    """
    workdir = os.path.dirname(os.path.abspath(output_pdf)) or '.'
    base_name = os.path.splitext(os.path.basename(tex_path))[0]

    try:
        # Check if pdflatex is available
        subprocess.run(["pdflatex", "--version"], capture_output=True, check=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        raise RuntimeError("pdflatex is not installed or not in your PATH")

    # First check if the required packages are installed
    try:
        print("   - Checking for required LaTeX packages...")
        # Run a minimal compile to see if we get package errors
        process = subprocess.run([
            'pdflatex',
            '-interaction=nonstopmode',
            f'-output-directory={workdir}',
            tex_path
        ], capture_output=True, text=True, check=False)
        
        # Check output for common package errors
        output = process.stdout + process.stderr
        missing_packages = []
        
        # Check for common missing packages
        package_patterns = {
            "fontawesome": r"File `fontawesome.sty' not found",
            "xcolor": r"File `xcolor.sty' not found",
            "hyperref": r"File `hyperref.sty' not found",
            "geometry": r"File `geometry.sty' not found",
            "titlesec": r"File `titlesec.sty' not found"
        }
        
        for package, pattern in package_patterns.items():
            if re.search(pattern, output):
                missing_packages.append(package)
        
        if missing_packages:
            print(f"   - Missing LaTeX packages detected: {', '.join(missing_packages)}")
            print("   - Attempting to install missing packages...")
            
            # Try to install missing packages
            tlmgr_available = False
            try:
                # Check if tlmgr is available
                tlmgr_check = subprocess.run(["tlmgr", "--version"], 
                                           capture_output=True, check=True, timeout=10)
                tlmgr_available = True
            except Exception:
                tlmgr_available = False
            
            if tlmgr_available:
                for package in missing_packages:
                    try:
                        print(f"     Installing {package} package...")
                        subprocess.run(["tlmgr", "install", package], 
                                      capture_output=True, check=True, timeout=60)
                        print(f"     {package} installed successfully")
                    except Exception as e:
                        print(f"     Could not automatically install {package}: {e}")
            else:
                print("\nCould not automatically install missing packages.")
                print("Please install them manually:")
                for package in missing_packages:
                    print(f"   - {package}")
                print("\nOn macOS: sudo tlmgr install " + " ".join(missing_packages))
                print("On Windows: Run as administrator: tlmgr install " + " ".join(missing_packages))
                
                # Offer to create a modified version for fontawesome
                if "fontawesome" in missing_packages:
                    should_modify = input("Would you like to create a version without fontawesome? (y/n): ").strip().lower()
                    if should_modify in ('y', 'yes'):
                        modified_tex = remove_fontawesome(tex_path)
                        if modified_tex:
                            non_fa_path = os.path.join(workdir, f"{base_name}_nofa.tex")
                            write_file(modified_tex, non_fa_path)
                            print(f"Modified version saved to: {non_fa_path}")
                            print("Attempting to compile the modified version...")
                            return compile_pdf(non_fa_path, output_pdf, company_name)
                
                raise RuntimeError("Required LaTeX packages are missing")
    except Exception as e:
        print(f"Error checking LaTeX packages: {e}")

    try:
        # Run pdflatex twice to resolve references if needed
        for i in range(2):
            print(f"   - Running pdflatex (pass {i+1}/2)...")
            process = subprocess.run([
                'pdflatex',
                '-interaction=nonstopmode',
                '-halt-on-error',
                f'-output-directory={workdir}',
                tex_path
            ], capture_output=True, text=True, check=False)
            
            if process.returncode != 0:
                error_log = process.stderr if process.stderr else process.stdout
                error_sample = error_log[-500:] if len(error_log) > 500 else error_log
                raise RuntimeError(f"PDF compilation failed. Error log: \n{error_sample}")

        generated_pdf = os.path.join(workdir, base_name + '.pdf')
        
        # Clean up auxiliary files
        print("   - Cleaning up temporary files...")
        for ext in ['.aux', '.log', '.out']:
            aux_file = os.path.join(workdir, base_name + ext)
            if os.path.exists(aux_file):
                os.remove(aux_file)
                
        if generated_pdf != output_pdf and os.path.exists(generated_pdf):
            os.replace(generated_pdf, output_pdf)
    
    except Exception as e:
        raise RuntimeError(f"Error during PDF compilation: {e}")


def remove_fontawesome(tex_path):
    """Create a modified version of the LaTeX file without fontawesome."""
    try:
        with open(tex_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove the fontawesome package
        content = re.sub(r'\\usepackage(\[\w+\])?\{fontawesome\}', '', content)
        
        # Replace fontawesome icons with text alternatives
        replacements = {
            r'\\faPhone': 'Phone:',
            r'\\faEnvelope': 'Email:',
            r'\\faGlobe': 'Website:',
            r'\\faLinkedinSquare': 'LinkedIn:',
            r'\\faGithub': 'GitHub:',
            r'\\faTwitter': 'Twitter:',
            r'\\faMobile': 'Mobile:',
            r'\\faHome': 'Address:',
            r'\\faMapMarker': 'Location:',
            r'\\faCalendar': 'Date:',
            r'\\faUser': 'User:',
            r'\\faFile': 'File:',
            r'\\faBook': 'Education:'
        }
        
        for pattern, replacement in replacements.items():
            content = re.sub(pattern, replacement, content)
        
        return content
    except Exception as e:
        print(f"Error modifying LaTeX file: {e}")
        return None


def open_in_editor(file_path):
    """Open the file in the default editor."""
    try:
        print(f"\nOpening {file_path} in your default editor...")
        
        # Determine the platform and use appropriate command
        if sys.platform.startswith('darwin'):  # macOS
            subprocess.run(['open', file_path], check=False)
        elif sys.platform.startswith('win'):   # Windows
            os.startfile(file_path)
        else:   # Linux and other Unix-like systems
            subprocess.run(['xdg-open', file_path], check=False)
        
        print("✅ File opened in editor")
    except Exception as e:
        print(f"Could not open file in editor: {e}")
        print(f"You can manually open {file_path} in your preferred editor")


def process_batch_jobs(batch_file, model_name):
    """Process multiple jobs from a CSV file."""
    import csv
    
    print(f"\n=== Batch Resume Tailoring ===")
    print(f"Processing jobs from: {batch_file}")
    
    # Set up output directory
    output_dir = setup_output_directory()
    
    try:
        with open(batch_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            jobs = list(reader)
            
        if not jobs:
            print("Error: No jobs found in batch file.", file=sys.stderr)
            sys.exit(1)
            
        print(f"Found {len(jobs)} jobs to process")
        
        for i, job in enumerate(jobs, 1):
            try:
                # Check required fields
                required_fields = ['company', 
                'role', 'template', 'job_description_file']
                missing = [field for field in required_fields if field not in job or not job[field]]
                
                if missing:
                    print(f"\nSkipping job #{i} - Missing fields: {', '.join(missing)}")
                    continue
                
                print(f"\n--- Processing job #{i}: {job['company']} - {job['role']} ---")
                
                # Read the resume template
                template_path = job['template']
                if not os.path.exists(template_path):
                    print(f"Error: Resume template file '{template_path}' not found. Skipping.")
                    continue
                
                template_content = load_template(template_path)
                
                # Read the job description
                job_description_path = job['job_description_file']
                if not os.path.exists(job_description_path):
                    print(f"Error: Job description file '{job_description_path}' not found. Skipping.")
                    continue
                
                with open(job_description_path, 'r', encoding='utf-8') as f:
                    job_description = f.read().strip()
                
                # Read pain points analysis if provided
                pain_points = ""
                if 'pain_points' in job and job['pain_points'].strip():
                    try:
                        with open(job['pain_points'], 'r', encoding='utf-8') as f:
                            pain_points = f.read().strip()
                        print(f"✅ Pain points analysis loaded from: {job['pain_points']}")
                    except Exception as e:
                        print(f"Warning: Error reading pain points file: {e}", file=sys.stderr)
                        print("Proceeding without pain points analysis")
                
                # Generate output filenames
                output_basename = f"{job['company'].lower().replace(' ', '_')}_{job['role'].lower().replace(' ', '_')}_resume"
                output_tex = os.path.join(output_dir, f"{output_basename}.tex")
                output_pdf = os.path.join(output_dir, f"{output_basename}.pdf")
                
                # Check for email generation
                generate_email = 'recruiter_name' in job and job['recruiter_name'].strip()
                recruiter_name = job.get('recruiter_name', '').strip()
                recruiter_position = job.get('recruiter_position', '').strip()
                recruiter_email = job.get('recruiter_email', '').strip()
                
                # Get keywords if provided in CSV - either directly or from file
                keywords = None
                if 'keywords' in job and job['keywords'].strip():
                    keywords = [kw.strip() for kw in job['keywords'].split(',') if kw.strip()]
                elif 'keywords_file' in job and job['keywords_file'].strip():
                    try:
                        with open(job['keywords_file'], 'r', encoding='utf-8') as f:
                            keywords_content = f.read().strip()
                        if keywords_content:
                            keywords = [kw.strip() for kw in keywords_content.split('\n') if kw.strip()]
                            print(f"✅ Keywords loaded from: {job['keywords_file']}")
                        else:
                            print(f"⚠️  Keywords file '{job['keywords_file']}' is empty - proceeding without keyword emphasis")
                    except Exception as e:
                        print(f"Warning: Error reading keywords file: {e}", file=sys.stderr)
                        print("Proceeding without keyword emphasis")
                
                # Tailor the resume
                tailor_resume(
                    template_content,
                    job['company'],
                    job_description,
                    model_name,
                    output_tex,
                    output_pdf,
                    job['role'],
                    generate_email,
                    recruiter_name,
                    recruiter_position,
                    recruiter_email,
                    keywords,
                    pain_points
                )
                
            except Exception as e:
                print(f"Error processing job #{i}: {e}")
                continue
        
        print("\n=== Batch processing complete ===")
        print(f"All output files were saved to: {output_dir}")
        
    except Exception as e:
        print(f"Error reading batch file: {e}", file=sys.stderr)
        sys.exit(1)


def extract_subject_from_email(email_content):
    """Extract the subject line from the generated email content."""
    # Look for a line starting with "Subject:" or "SUBJECT:"
    subject_match = re.search(r'^(?:Subject|SUBJECT):\s*(.+)$', email_content, re.MULTILINE)
    if subject_match:
        return subject_match.group(1).strip()
    
    # If no explicit subject line, use the first line as subject
    lines = email_content.split('\n')
    for line in lines:
        if line.strip() and not line.startswith("From:"):
            return line.strip()
    
    # Fallback to generic subject
    return "Application for Position"


def send_email(to_email, subject, body_text, attachment_path=None):
    """Send an email with optional attachment."""
    print("\n=== Send Email ===")
    print(f"To: {to_email}")
    print(f"Subject: {subject}")
    
    # Get sender credentials
    sender_email = "rahul.menon@hotmail.com"  # Default sender
    custom_sender = input(f"Send from email [default: {sender_email}]: ").strip()
    if custom_sender:
        sender_email = custom_sender
    
    # Create email message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject
    
    # Process body text
    # Remove email headers from body if present
    body_text = re.sub(r'^From:.*?\n', '', body_text, flags=re.MULTILINE)
    body_text = re.sub(r'^Subject:.*?\n', '', body_text, flags=re.MULTILINE)
    body_text = re.sub(r'^To:.*?\n', '', body_text, flags=re.MULTILINE)
    
    # Attach body text
    msg.attach(MIMEText(body_text, 'plain'))
    
    # Attach resume if path provided
    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as file:
            attachment = MIMEApplication(file.read(), _subtype="pdf")
            attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachment_path))
            msg.attach(attachment)
        print(f"Attaching resume: {os.path.basename(attachment_path)}")
    
    # Ask for password
    print("\nYou'll need to provide your email password or app password.")
    print("Note: For security reasons, the password input will not be displayed as you type.")
    password = getpass.getpass(prompt="Enter your email password: ")
    
    # Determine SMTP settings based on email domain
    smtp_settings = get_smtp_settings(sender_email)
    
    if not smtp_settings:
        print(f"Could not determine SMTP settings for {sender_email}")
        return False
    
    # Send the email
    try:
        print(f"Connecting to {smtp_settings['server']}:{smtp_settings['port']}...")
        with smtplib.SMTP(smtp_settings['server'], smtp_settings['port']) as server:
            server.ehlo()
            if smtp_settings['use_tls']:
                server.starttls()
                server.ehlo()
            
            server.login(sender_email, password)
            server.send_message(msg)
        
        print(f"\n✅ Email sent successfully to {to_email}!")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        print("\nCommon troubleshooting tips:")
        print("1. For Gmail: Use an App Password instead of your regular password")
        print("2. For Outlook/Hotmail: Make sure 'Less secure app access' is enabled")
        print("3. Check that your username and password are correct")
        return False


def get_smtp_settings(email):
    """Get SMTP settings based on email domain."""
    domain = email.split('@')[-1].lower()
    
    # Common email providers
    if domain in ['gmail.com', 'googlemail.com']:
        return {
            'server': 'smtp.gmail.com',
            'port': 587,
            'use_tls': True
        }
    elif domain in ['outlook.com', 'hotmail.com', 'live.com', 'msn.com']:
        return {
            'server': 'smtp-mail.outlook.com',
            'port': 587,
            'use_tls': True
        }
    elif domain in ['yahoo.com', 'ymail.com']:
        return {
            'server': 'smtp.mail.yahoo.com',
            'port': 587,
            'use_tls': True
        }
    elif domain in ['aol.com']:
        return {
            'server': 'smtp.aol.com',
            'port': 587,
            'use_tls': True
        }
    elif domain in ['icloud.com', 'me.com', 'mac.com']:
        return {
            'server': 'smtp.mail.me.com',
            'port': 587,
            'use_tls': True
        }
    
    # For domains not recognized, ask user for SMTP settings
    print(f"\nSMTP settings for '{domain}' not found.")
    use_custom = input("Would you like to enter custom SMTP settings? (y/n): ").strip().lower()
    
    if use_custom in ('y', 'yes'):
        server = input("SMTP server address: ").strip()
        port = input("SMTP port (usually 587 or 465): ").strip()
        use_tls = input("Use TLS? (y/n): ").strip().lower() in ('y', 'yes')
        
        return {
            'server': server,
            'port': int(port),
            'use_tls': use_tls
        }
    
    return None


def get_recruiter_inputs():
    """Get inputs for generating a recruiter email."""
    print("\n=== Recruiter Email Generation ===")
    
    recruiter_name = input("Enter the recruiter's name: ").strip()
    while not recruiter_name:
        print("Recruiter's name is required.")
        recruiter_name = input("Enter the recruiter's name: ").strip()
    
    recruiter_position = input("Enter the recruiter's position (optional): ").strip()
    
    # Get the recruiter's email
    recruiter_email = input("Enter the recruiter's email address (leave blank if not sending now): ").strip()
    
    return {
        "recruiter_name": recruiter_name,
        "recruiter_position": recruiter_position,
        "recruiter_email": recruiter_email
    }


def main():
    # Check for command line arguments first
    cmd_args = process_command_line_args()
    
    if cmd_args:
        # If in batch mode
        if 'batch' in cmd_args:
            process_batch_jobs(cmd_args['batch'], cmd_args['model'])
            return
            
        # Otherwise, use command line args for a single job
        template_content = load_template(cmd_args["template"])
        
        tailor_resume(
            template_content, 
            cmd_args["company"], 
            cmd_args["description"], 
            cmd_args["model"],
            cmd_args["output_tex"], 
            cmd_args["output_pdf"],
            cmd_args["role"],
            cmd_args.get("generate_email", False),
            cmd_args.get("recruiter_name"),
            cmd_args.get("recruiter_position"),
            cmd_args.get("recruiter_email"),
            cmd_args.get("keywords"),
            cmd_args.get("pain_points", "")
        )
    else:
        # Get inputs interactively
        inputs = get_interactive_inputs()
        
        # Load the LaTeX template
        template_content = load_template(inputs["template"])
        
        # Tailor the resume
        tailor_resume(
            template_content, 
            inputs["company"], 
            inputs["description"], 
            inputs["model"],
            inputs["output_tex"], 
            inputs["output_pdf"],
            inputs["role"],
            inputs.get("generate_email", False),
            inputs.get("recruiter_name"),
            inputs.get("recruiter_position"),
            inputs.get("recruiter_email"),
            inputs.get("keywords"),
            inputs.get("pain_points", "")
        )


if __name__ == "__main__":
    main()
