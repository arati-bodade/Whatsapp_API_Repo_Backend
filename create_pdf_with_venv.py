#!/usr/bin/env python3
"""
Create PDF Architecture Document using Virtual Environment
Activates venv and uses reportlab for PDF generation
"""

import os
import sys
import subprocess
from datetime import datetime

def activate_venv_and_install_deps():
    """Activate virtual environment and install dependencies"""
    
    print("🔄 ACTIVATING VIRTUAL ENVIRONMENT...")
    
    # Check if venv exists
    venv_path = "venv"
    if not os.path.exists(venv_path):
        print("❌ Virtual environment not found. Creating...")
        subprocess.run([sys.executable, "-m", "venv"], check=True)
        print("✅ Virtual environment created")
    
    # Activate virtual environment and install reportlab
    venv_python = os.path.join(venv_path, "Scripts", "python.exe") if os.name == "nt" else os.path.join(venv_path, "bin", "python")
    
    print(f"📦 Installing dependencies in virtual environment...")
    
    # Install reportlab for PDF generation
    install_cmd = [venv_python, "-m", "pip", "install", "reportlab"]
    result = subprocess.run(install_cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ ReportLab installed successfully")
        return venv_python
    else:
        print(f"❌ Failed to install ReportLab: {result.stderr}")
        return None

def create_pdf_with_reportlab(venv_python):
    """Create PDF using ReportLab in virtual environment"""
    
    script_content = '''
import sys
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

def create_architecture_pdf():
    """Create WhatsApp Platform Architecture PDF"""
    
    # Document setup
    doc = SimpleDocTemplate(
        "WHATSAPP_PLATFORM_ARCHITECTURE.pdf",
        pagesize=landscape(letter),
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=20,
        alignment=1,  # Center
        textColor=colors.white
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=18,
        spaceAfter=12,
        textColor=colors.darkblue
    )
    
    normal_style = styles['Normal']
    
    # Content
    story = []
    
    # Header
    header_data = [[
        ["🏗️ WHATSAPP PLATFORM ARCHITECTURE"],
        ["Three-Service Microservices Architecture"]
    ]]
    
    header_table = Table(header_data, colWidths=[6*inch, 4*inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 1), colors.Color(0.2, 0.5, 0.8, 1)),
        ('TEXTCOLOR', (0, 0), (0, 1), colors.whitesmoke),
        ('ALIGN', (0, 0), 'CENTER'),
        ('FONTNAME', (0, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), 16),
        ('BOTTOMPADDING', (0, 0), 20),
    ]))
    
    story.append(header_table)
    story.append(Spacer(1, 20))
    
    # Services Grid
    services_data = [
        ['📱 Frontend Service', '⚙️ Backend Service', '🔧 WhatsApp Engine'],
        [
            'Port: 3000\\nNext.js 16.1.1\\nTypeScript\\nUser Interface & API Proxy',
            'Port: 8000\\nPython FastAPI\\nPostgreSQL\\nBusiness Logic & Data Management',
            'Port: 3002\\nNode.js + Baileys\\nWhatsApp Web API\\nDirect WhatsApp Integration'
        ]
    ]
    
    services_table = Table(services_data, colWidths=[4*inch, 4*inch, 4*inch])
    services_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.9, 0.95, 0.98, 1)),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), 'CENTER'),
        ('VALIGN', (0, 0), 'TOP'),
        ('FONTNAME', (0, 0), 'Helvetica'),
        ('FONTSIZE', (0, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('TOPPADDING', (0, 0), 12),
        ('BOTTOMPADDING', (0, 0), 12),
    ]))
    
    story.append(services_table)
    story.append(Spacer(1, 20))
    
    # Data Flow
    story.append(Paragraph("📊 Data Flow", heading_style))
    data_flow = Paragraph(
        "📱 Frontend ↔️ ⚙️ Backend ↔️ 🔧 Engine ↔️ 💬 WhatsApp Network",
        normal_style
    )
    story.append(data_flow)
    story.append(Spacer(1, 20))
    
    # Architecture Benefits
    story.append(Paragraph("🎯 Architecture Benefits", heading_style))
    
    benefits = [
        "• Scalability: Each service can scale independently",
        "• Maintainability: Clear code boundaries and responsibilities", 
        "• Reliability: Fault isolation between services",
        "• Technology: Best tools for each service's purpose",
        "• Development: Teams can work on services independently"
    ]
    
    for benefit in benefits:
        story.append(Paragraph(benefit, normal_style))
        story.append(Spacer(1, 6))
    
    # Footer
    story.append(Spacer(1, 20))
    footer = Paragraph(
        f"Generated using Python Virtual Environment\\\\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        normal_style
    )
    story.append(footer)
    
    # Build PDF
    doc.build(story)
    return "WHATSAPP_PLATFORM_ARCHITECTURE.pdf"

if __name__ == "__main__":
    try:
        pdf_file = create_architecture_pdf()
        print(f"✅ PDF generated successfully: {pdf_file}")
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
'''
    
    # Save the script to run in venv
    script_file = "create_pdf_in_venv.py"
    with open(script_file, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print(f"✅ PDF generation script created: {script_file}")
    
    # Run the script in virtual environment
    if venv_python:
        print("🚀 GENERATING PDF USING VIRTUAL ENVIRONMENT...")
        result = subprocess.run([venv_python, script_file], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ PDF generated successfully using virtual environment!")
            if os.path.exists("WHATSAPP_PLATFORM_ARCHITECTURE.pdf"):
                print("📄 PDF file: WHATSAPP_PLATFORM_ARCHITECTURE.pdf")
                print("📁 File size: {} bytes".format(os.path.getsize("WHATSAPP_PLATFORM_ARCHITECTURE.pdf")))
        else:
            print("❌ PDF file not found")
        else:
            print(f"❌ PDF generation failed: {result.stderr}")
    
    else:
        print("❌ Virtual environment setup failed")

def main():
    """Main function"""
    
    print("🚀 PDF GENERATION WITH VIRTUAL ENVIRONMENT")
    print("=" * 60)
    
    # Activate venv and install dependencies
    venv_python = activate_venv_and_install_deps()
    
    if venv_python:
        # Create and run PDF generation script
        create_pdf_script_in_venv(venv_python)
    else:
        print("❌ Failed to set up virtual environment")
    
    print("\n" + "=" * 60)
    print("🎉 PDF GENERATION PROCESS COMPLETED!")
    print("=" * 60)

if __name__ == "__main__":
    main()
