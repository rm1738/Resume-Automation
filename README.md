# Resume Tailoring Tool

An intelligent LaTeX resume tailoring tool that uses OpenAI's GPT models to customize your resume for specific job applications while preserving formatting and layout.

## Features

- **Smart Resume Tailoring**: Uses AI to tailor your resume content to specific job descriptions
- **Format Preservation**: Maintains exact LaTeX formatting, spacing, and one-page layout
- **Multi-Input Support**: Reads job descriptions, pain points analysis, and keywords from text files
- **Email Generation**: Creates personalized recruiter emails with resume attachment
- **Batch Processing**: Process multiple job applications from CSV files
- **PDF Compilation**: Automatically compiles LaTeX to PDF (when LaTeX is installed)

## Requirements

- Python 3.7+
- OpenAI API key
- LaTeX distribution (optional, for PDF compilation)
  - macOS: [MacTeX](https://www.tug.org/mactex/)
  - Windows: [MiKTeX](https://miktex.org/)
  - Linux: `sudo apt-get install texlive-full`

## Installation

1. Clone this repository:
```bash
git clone https://github.com/rm1738/Resume-Automation.git
cd Resume-Automation
```

2. Install required Python packages:
```bash
pip install openai
```

3. Set your OpenAI API key:
```bash
export OPENAI_API_KEY='your-api-key-here'
```

## Quick Start

### Interactive Mode (Recommended)

1. **Prepare your files** on your Desktop:
   - `main.tex` - Your LaTeX resume template
   - `job.txt` - The job description
   - `pain_points.txt` - Analysis of company's challenges (optional)
   - `keywords.txt` - Keywords to emphasize, one per line (optional)

2. **Run the script**:
```bash
python tailor.py
```

3. **Follow the prompts** to enter company name and role

4. **Get your tailored resume** in `~/Desktop/script_resumes/`

### Example File Setup

**~/Desktop/job.txt**:
```
We are seeking a Software Engineer to join our growing team...
Requirements: Python, AWS, Docker, REST APIs...
```

**~/Desktop/pain_points.txt**:
```
The company is struggling with:
- Scaling microservices architecture for 10x user growth
- Legacy code maintenance consuming 60% of engineering time
- Need for better CI/CD processes to reduce deployment times
```

**~/Desktop/keywords.txt**:
```
Python
AWS
Docker
REST APIs
PostgreSQL
Microservices
```

## Usage Modes

### 1. Interactive Mode
```bash
python tailor.py
```
- Guides you through the process step-by-step
- Automatically reads files from Desktop
- Best for single job applications

### 2. Command Line Mode
```bash
python tailor.py \
  --template main.tex \
  --company "TechCorp" \
  --role "Software Engineer" \
  --job-description job.txt \
  --pain-points pain_points.txt \
  --keywords-file keywords.txt \
  --email \
  --recruiter "Jane Smith"
```

### 3. Batch Mode
```bash
python tailor.py --batch jobs.csv
```

**CSV Format**:
```csv
company,role,template,job_description_file,pain_points,keywords_file,recruiter_name,recruiter_email
TechCorp,Engineer,main.tex,job1.txt,pain1.txt,keywords1.txt,Jane Smith,jane@techcorp.com
DataCorp,Analyst,main.tex,job2.txt,pain2.txt,keywords2.txt,John Doe,john@datacorp.com
```

## Command Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--template` | `-t` | Path to LaTeX resume template |
| `--company` | `-c` | Target company name |
| `--role` | `-r` | Target role/position |
| `--job-description` | `-j` | Path to job description file |
| `--pain-points` | `-p` | Path to pain points analysis file |
| `--keywords` | `-k` | Keywords to emphasize (space-separated) |
| `--keywords-file` | | Path to keywords file (one per line) |
| `--output` | `-o` | Output directory |
| `--model` | `-m` | OpenAI model (default: gpt-4o) |
| `--batch` | `-b` | Path to CSV file for batch processing |
| `--email` | `-e` | Generate recruiter email |
| `--recruiter` | | Recruiter's name (required with --email) |
| `--recruiter-position` | | Recruiter's position |
| `--recruiter-email` | | Recruiter's email for sending |
| `--version` | `-v` | Show version information |

## How It Works

1. **Analysis**: The AI analyzes the job description and identifies key requirements
2. **Pain Points Integration**: Uses company pain points to understand challenges
3. **Keyword Optimization**: Naturally integrates specified keywords
4. **Content Tailoring**: Modifies work experience bullets and technical skills
5. **Format Preservation**: Maintains exact LaTeX structure and one-page layout
6. **Output Generation**: Creates tailored .tex file and compiles to PDF

## AI Prompt Strategy

The tool uses a sophisticated prompt that:
- Preserves every LaTeX formatting token
- Applies PAR (Problem-Action-Result) structure to bullets
- Emphasizes quantified results and impact
- Integrates exact-match keywords from job descriptions
- Addresses company-specific pain points
- Maintains ATS compatibility

## Output Files

For each job application, the tool creates:
- `company_role_resume.tex` - Tailored LaTeX source
- `company_role_resume.pdf` - Compiled PDF (if LaTeX available)
- `company_role_email.txt` - Personalized recruiter email (if requested)

## Tips for Best Results

### LaTeX Resume Template
- Use a clean, ATS-friendly format
- Include clear sections for Work Experience and Technical Skills
- Ensure the template compiles to exactly one page
- Use standard LaTeX packages (avoid exotic fonts/packages)

### Job Description Analysis
- Include complete job posting in `job.txt`
- Add company information and culture details
- Include specific requirements and nice-to-haves

### Pain Points Analysis
- Research the company's recent challenges
- Identify industry-specific problems they're solving
- Focus on technical and business challenges relevant to the role

### Keywords Selection
- Extract exact terms from the job posting
- Include technical skills, tools, and frameworks
- Add industry-specific terminology
- Prioritize ATS-friendly keywords

## Troubleshooting

### PDF Compilation Issues
```bash
# Install missing LaTeX packages
sudo tlmgr install fontawesome xcolor hyperref geometry titlesec

# Or use online LaTeX editors
# - Overleaf (https://www.overleaf.com)
# - ShareLaTeX
```

### API Errors
- Verify your OpenAI API key is set correctly
- Check your API usage limits and billing
- Ensure you have access to GPT-4 models

### File Not Found Errors
- Verify file paths are correct
- Ensure files are saved with proper encoding (UTF-8)
- Check file permissions

## Examples

### Basic Usage
```bash
python tailor.py
# Follow interactive prompts
```

### Command Line with All Options
```bash
python tailor.py \
  --template ~/Documents/resume.tex \
  --company "Microsoft" \
  --role "Senior Software Engineer" \
  --job-description job_microsoft.txt \
  --pain-points microsoft_challenges.txt \
  --keywords-file tech_keywords.txt \
  --email \
  --recruiter "Sarah Johnson" \
  --recruiter-email sarah.johnson@microsoft.com \
  --model gpt-4o
```

### Batch Processing
```bash
python tailor.py --batch applications.csv --model gpt-4o
```

## Version History

- **v1.2.0**: Added pain points analysis and keywords file support
- **v1.1.0**: Added email generation and batch processing
- **v1.0.0**: Initial release with basic resume tailoring

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues and questions:
- Open an issue on GitHub
- Check the troubleshooting section above
- Verify your setup meets all requirements

## Disclaimer

This tool is designed to help tailor existing resume content to specific jobs. Always review the generated output to ensure accuracy and appropriateness. The tool does not fabricate experience or qualifications - it only reframes and emphasizes existing content from your original resume. 
