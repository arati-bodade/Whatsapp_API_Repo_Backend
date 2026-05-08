#!/usr/bin/env python3
"""
Simple Text-based PDF Generator
Avoids special characters and uses basic text formatting
"""

import os
import sys
import subprocess
from datetime import datetime

def install_fpdf():
    """Install fpdf for PDF generation"""
    print("📦 Installing fpdf for text-based PDF generation...")
    
    # Try to install fpdf
    install_cmd = [sys.executable, "-m", "pip", "install", "fpdf2"]
    result = subprocess.run(install_cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ fpdf2 installed successfully")
        return True
    else:
        print(f"❌ Failed to install fpdf2: {result.stderr}")
        return False

def create_simple_text_pdf():
    """Create PDF with simple text content"""
    
    try:
        from fpdf import FPDF
        
        # Create PDF object
        pdf = FPDF()
        pdf.add_page()
        
        # Set font
        pdf.set_font("Helvetica", size=16)
        
        # Title
        pdf.cell(0, 10, "WHATSAPP PLATFORM ARCHITECTURE")
        pdf.ln(15)
        
        pdf.set_font_size(14)
        pdf.cell(0, 10, "Three-Service Microservices Architecture")
        pdf.ln(10)
        pdf.cell(0, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        pdf.ln(15)
        
        # Services Section
        pdf.set_font_size(18)
        pdf.cell(0, 10, "SERVICE ARCHITECTURE")
        pdf.ln(10)
        
        pdf.set_font_size(12)
        
        # Frontend Service
        pdf.cell(0, 10, "1. FRONTEND SERVICE")
        pdf.ln(5)
        pdf.cell(0, 10, "   Location: whatsapp_platform_frontend/")
        pdf.ln(3)
        pdf.cell(0, 10, "   Port: 3000")
        pdf.ln(3)
        pdf.cell(0, 10, "   Technology: Next.js 16.1.1 + TypeScript")
        pdf.ln(3)
        pdf.cell(0, 10, "   Purpose: User Interface & API Proxy")
        pdf.ln(8)
        
        # Backend Service
        pdf.cell(0, 10, "2. BACKEND SERVICE")
        pdf.ln(5)
        pdf.cell(0, 10, "   Location: whatsapp-api-backend/")
        pdf.ln(3)
        pdf.cell(0, 10, "   Port: 8000")
        pdf.ln(3)
        pdf.cell(0, 10, "   Technology: Python FastAPI + SQLAlchemy")
        pdf.ln(3)
        pdf.cell(0, 10, "   Purpose: Business Logic & Data Management")
        pdf.ln(8)
        
        # WhatsApp Engine Service
        pdf.cell(0, 10, "3. WHATSAPP ENGINE SERVICE")
        pdf.ln(5)
        pdf.cell(0, 10, "   Location: whatsapp-engine-baileys/")
        pdf.ln(3)
        pdf.cell(0, 10, "   Port: 3002")
        pdf.ln(3)
        pdf.cell(0, 10, "   Technology: Node.js + Baileys")
        pdf.ln(3)
        pdf.cell(0, 10, "   Purpose: Direct WhatsApp Integration")
        pdf.ln(8)
        
        # Data Flow
        pdf.set_font_size(16)
        pdf.cell(0, 10, "DATA FLOW")
        pdf.ln(10)
        pdf.set_font_size(12)
        pdf.cell(0, 10, "   WhatsApp User <-> Engine <-> Backend <-> Frontend")
        pdf.ln(8)
        
        # Recent Improvements
        pdf.set_font_size(16)
        pdf.cell(0, 10, "RECENT IMPROVEMENTS")
        pdf.ln(10)
        pdf.set_font_size(12)
        
        pdf.cell(0, 10, "   Webhook Phone Extraction: remote_jid instead of phone_number")
        pdf.ln(5)
        pdf.cell(0, 10, "   Phone Validation: MSISDN format (10-15 digits)")
        pdf.ln(5)
        pdf.cell(0, 10, "   Response Handling: accepted treated as success")
        pdf.ln(5)
        pdf.cell(0, 10, "   JID Construction: normalized_phone for JID creation")
        pdf.ln(5)
        pdf.cell(0, 10, "   Database Cleanup: invalid records removed")
        pdf.ln(8)
        
        # Architecture Benefits
        pdf.set_font_size(16)
        pdf.cell(0, 10, "ARCHITECTURE BENEFITS")
        pdf.ln(10)
        pdf.set_font_size(12)
        
        pdf.cell(0, 10, "   Scalability: Independent service scaling")
        pdf.ln(5)
        pdf.cell(0, 10, "   Maintainability: Clear code boundaries")
        pdf.ln(5)
        pdf.cell(0, 10, "   Reliability: Fault isolation")
        pdf.ln(5)
        pdf.cell(0, 10, "   Technology: Best tools for each purpose")
        pdf.ln(5)
        pdf.cell(0, 10, "   Development: Team independence")
        pdf.ln(10)
        
        # Footer
        pdf.set_font_size(10)
        pdf.cell(0, 10, "Generated using Python Backend Environment")
        pdf.ln(5)
        pdf.cell(0, 10, f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Save PDF
        pdf_file = "WHATSAPP_PLATFORM_ARCHITECTURE_SIMPLE.pdf"
        pdf.output(pdf_file)
        
        return pdf_file
        
    except ImportError:
        print("❌ fpdf2 not available. Creating simple text file...")
        
        # Fallback to text file
        text_content = f"""WHATSAPP PLATFORM ARCHITECTURE
============================

Three-Service Microservices Architecture
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SERVICE ARCHITECTURE

1. FRONTEND SERVICE
   Location: whatsapp_platform_frontend/
   Port: 3000
   Technology: Next.js 16.1.1 + TypeScript
   Purpose: User Interface & API Proxy

2. BACKEND SERVICE
   Location: whatsapp-api-backend/
   Port: 8000
   Technology: Python FastAPI + SQLAlchemy
   Purpose: Business Logic & Data Management

3. WHATSAPP ENGINE SERVICE
   Location: whatsapp-engine-baileys/
   Port: 3002
   Technology: Node.js + Baileys
   Purpose: Direct WhatsApp Integration

DATA FLOW
   WhatsApp User <-> Engine <-> Backend <-> Frontend

RECENT IMPROVEMENTS

   Webhook Phone Extraction: remote_jid instead of phone_number
   Phone Validation: MSISDN format (10-15 digits)
   Response Handling: accepted treated as success
   JID Construction: normalized_phone for JID creation
   Database Cleanup: invalid records removed

ARCHITECTURE BENEFITS

   Scalability: Independent service scaling
   Maintainability: Clear code boundaries
   Reliability: Fault isolation
   Technology: Best tools for each purpose
   Development: Team independence

Generated using Python Backend Environment
Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        text_file = "WHATSAPP_PLATFORM_ARCHITECTURE_SIMPLE.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        return text_file

def main():
    """Main function"""
    
    print("🚀 SIMPLE TEXT-BASED PDF GENERATOR")
    print("=" * 50)
    
    # Install fpdf
    if install_fpdf():
        # Create PDF with fpdf
        pdf_file = create_simple_text_pdf()
        
        if pdf_file and os.path.exists(pdf_file):
            size = os.path.getsize(pdf_file)
            print(f"✅ PDF generated successfully: {pdf_file}")
            print(f"📄 File size: {size} bytes")
        else:
            print("❌ PDF generation failed")
    else:
        print("❌ Could not install fpdf, created text file instead")
    
    print("\n" + "=" * 50)
    print("🎉 SIMPLE TEXT-BASED PDF GENERATION COMPLETED!")
    print("=" * 50)

if __name__ == "__main__":
    main()
