#!/usr/bin/env python3
"""
Simple PDF Generator using Virtual Environment
"""

import os
import sys
import subprocess
from datetime import datetime

def main():
    """Main function to activate venv and generate PDF"""
    
    print("🚀 PDF GENERATION WITH VIRTUAL ENVIRONMENT")
    print("=" * 60)
    
    # Check if venv exists
    venv_path = "venv"
    if not os.path.exists(venv_path):
        print("❌ Virtual environment not found. Creating...")
        result = subprocess.run([sys.executable, "-m", "venv"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Virtual environment created")
        else:
            print(f"❌ Failed to create venv: {result.stderr}")
            return
    
    # Determine venv Python path
    if os.name == "nt":  # Windows
        venv_python = os.path.join(venv_path, "Scripts", "python.exe")
        pip_path = os.path.join(venv_path, "Scripts", "pip.exe")
    else:  # Unix/Linux/Mac
        venv_python = os.path.join(venv_path, "bin", "python")
        pip_path = os.path.join(venv_path, "bin", "pip")
    
    print(f"📦 Using virtual environment Python: {venv_python}")
    
    # Install reportlab
    print("📦 Installing ReportLab for PDF generation...")
    install_cmd = [pip_path, "install", "reportlab"]
    result = subprocess.run(install_cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to install ReportLab: {result.stderr}")
        return
    
    print("✅ ReportLab installed successfully")
    
    # Create simple PDF generation script
    pdf_script_content = '''
import sys
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

def create_pdf():
    doc = SimpleDocTemplate("WHATSAPP_PLATFORM_ARCHITECTURE.pdf", pagesize=landscape(letter))
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, textColor=colors.white, alignment=1)
    title = Paragraph("🏗️ WHATSAPP PLATFORM ARCHITECTURE", title_style)
    
    # Services
    services_data = [
        ['Service', 'Port', 'Technology', 'Purpose'],
        ['Frontend', '3000', 'Next.js 16.1.1', 'User Interface & API Proxy'],
        ['Backend', '8000', 'Python FastAPI', 'Business Logic & Data Management'],
        ['WhatsApp Engine', '3002', 'Node.js + Baileys', 'Direct WhatsApp Integration']
    ]
    
    services_table = Table(services_data, colWidths=[2*inch, 1*inch, 3*inch, 3*inch])
    services_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.9, 0.95, 0.98, 1)),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), 'CENTER'),
        ('FONTNAME', (0, 0), 'Helvetica'),
        ('FONTSIZE', (0, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('TOPPADDING', (0, 0), 12),
        ('BOTTOMPADDING', (0, 0), 12),
    ]))
    
    # Data Flow
    normal_style = styles['Normal']
    data_flow = Paragraph("📊 Data Flow: 📱 Frontend ↔️ ⚙️ Backend ↔️ 🔧 Engine ↔️ 💬 WhatsApp", normal_style)
    
    # Build PDF
    story = [title, Spacer(1, 20), services_table, Spacer(1, 20), data_flow, Spacer(1, 20)]
    
    # Footer
    footer = Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style)
    story.append(footer)
    
    doc.build(story)
    return "WHATSAPP_PLATFORM_ARCHITECTURE.pdf"

if __name__ == "__main__":
    try:
        pdf_file = create_pdf()
        print(f"✅ PDF generated: {pdf_file}")
        if os.path.exists(pdf_file):
            size = os.path.getsize(pdf_file)
            print(f"📄 File size: {size} bytes")
    except Exception as e:
        print(f"❌ Error: {e}")
'''
    
    # Save the script
    script_file = "generate_pdf_in_venv.py"
    with open(script_file, 'w', encoding='utf-8') as f:
        f.write(pdf_script_content)
    
    print(f"✅ PDF script created: {script_file}")
    
    # Run the script in virtual environment
    print("🚀 GENERATING PDF...")
    run_cmd = [venv_python, script_file]
    result = subprocess.run(run_cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ PDF generated successfully using virtual environment!")
        if os.path.exists("WHATSAPP_PLATFORM_ARCHITECTURE.pdf"):
            size = os.path.getsize("WHATSAPP_PLATFORM_ARCHITECTURE.pdf")
            print(f"📄 PDF file: WHATSAPP_PLATFORM_ARCHITECTURE.pdf")
            print(f"📁 File size: {size} bytes")
        else:
            print("❌ PDF file not found")
    else:
        print(f"❌ PDF generation failed: {result.stderr}")
    
    print("\n" + "=" * 60)
    print("🎉 PDF GENERATION COMPLETED!")
    print("=" * 60)

if __name__ == "__main__":
    main()
