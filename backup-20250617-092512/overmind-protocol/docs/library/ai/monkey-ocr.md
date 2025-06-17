# 🐵 MonkeyOCR - THE OVERMIND PROTOCOL Document Intelligence

## 📋 **OVERVIEW**

MonkeyOCR to zaawansowany model AI do parsowania dokumentów używający paradygmatu Structure-Recognition-Relation (SRR). Używany w THE OVERMIND PROTOCOL Warstwa 2 (Zwiad) do analizy dokumentów finansowych i zasilania Warstwy 3 (Mózg AI) inteligencją rynkową.

**Source:** HuggingFace - echo840/MonkeyOCR
**Model Size:** 3B parameters
**Performance:** 0.84 pages/second processing speed
**Use Case:** OVERMIND Financial Intelligence, AI Brain Data Feed
**OVERMIND Role:** Warstwa 2 - Zwiad (Document Intelligence)

## 🎯 **KLUCZOWE FUNKCJONALNOŚCI DLA THE OVERMIND PROTOCOL**

### **1. Structure-Recognition-Relation (SRR) Paradigm:**
```python
# MonkeyOCR processing pipeline
# 1. Structure Detection - wykrywa layout dokumentu
# 2. Content Recognition - rozpoznaje tekst, tabele, formuły
# 3. Relation Prediction - ustala relacje między elementami

# Rezultat: Markdown z zachowaną strukturą
```

### **2. Supported Document Types:**
- **Financial Reports** - Raporty finansowe firm
- **Academic Papers** - Dokumenty naukowe z formułami
- **Tables & Charts** - Tabele danych finansowych
- **Newspapers** - Artykuły prasowe o rynkach
- **Textbooks** - Materiały edukacyjne
- **Exam Papers** - Dokumenty testowe
- **Slides** - Prezentacje biznesowe

## 🚀 **IMPLEMENTACJA DLA THE OVERMIND PROTOCOL**

### **1. Installation & Setup:**
```bash
# Create environment
conda create -n MonkeyOCR python=3.10
conda activate MonkeyOCR

# Clone repository
git clone https://github.com/Yuliang-Liu/MonkeyOCR.git
cd MonkeyOCR

# Install PyTorch (adjust for your CUDA version)
pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu124
pip install -e .

# Download model weights
pip install huggingface_hub
python tools/download_model.py
```

### **2. Basic Usage:**
```python
import os
from monkey_ocr import MonkeyOCR

# Initialize MonkeyOCR
ocr = MonkeyOCR()

# Process financial document
def process_financial_report(pdf_path: str) -> dict:
    """Process financial report and extract structured data"""
    
    # Parse document
    result = ocr.parse(pdf_path)
    
    return {
        'markdown_content': result['markdown'],
        'layout_info': result['layout'],
        'blocks': result['blocks'],
        'processing_time': result['time']
    }

# Example usage
financial_report = process_financial_report('quarterly_report.pdf')
print(financial_report['markdown_content'])
```

### **3. THE OVERMIND PROTOCOL Integration:**
```python
import asyncio
from typing import Dict, List, Optional
import json
import re
from ai_hedge_fund import VectorMemory

class OVERMINDDocumentAnalyzer:
    """Document analyzer for THE OVERMIND PROTOCOL AI Brain"""
    
    def __init__(self):
        self.ocr = MonkeyOCR()
        self.financial_keywords = [
            'revenue', 'profit', 'earnings', 'cash flow',
            'debt', 'assets', 'liabilities', 'equity',
            'guidance', 'outlook', 'forecast'
        ]
    
    async def analyze_earnings_report(self, pdf_path: str) -> Dict:
        """Analyze earnings report for trading signals"""
        
        # Parse document
        parsed_doc = self.ocr.parse(pdf_path)
        markdown_content = parsed_doc['markdown']
        
        # Extract financial metrics
        metrics = self.extract_financial_metrics(markdown_content)
        
        # Extract guidance and outlook
        guidance = self.extract_guidance(markdown_content)
        
        # Generate trading signals
        signals = self.generate_trading_signals(metrics, guidance)
        
        return {
            'company': self.extract_company_name(markdown_content),
            'quarter': self.extract_quarter(markdown_content),
            'metrics': metrics,
            'guidance': guidance,
            'trading_signals': signals,
            'confidence': self.calculate_confidence(metrics, guidance),
            'raw_content': markdown_content
        }
    
    def extract_financial_metrics(self, content: str) -> Dict:
        """Extract key financial metrics from parsed content"""
        metrics = {}
        
        # Revenue extraction
        revenue_pattern = r'revenue.*?(\$[\d,]+\.?\d*\s*(?:million|billion))'
        revenue_match = re.search(revenue_pattern, content, re.IGNORECASE)
        if revenue_match:
            metrics['revenue'] = revenue_match.group(1)
        
        # EPS extraction
        eps_pattern = r'earnings per share.*?(\$\d+\.\d+)'
        eps_match = re.search(eps_pattern, content, re.IGNORECASE)
        if eps_match:
            metrics['eps'] = eps_match.group(1)
        
        # Profit margin extraction
        margin_pattern = r'profit margin.*?(\d+\.?\d*%)'
        margin_match = re.search(margin_pattern, content, re.IGNORECASE)
        if margin_match:
            metrics['profit_margin'] = margin_match.group(1)
        
        return metrics
    
    def extract_guidance(self, content: str) -> Dict:
        """Extract forward guidance from document"""
        guidance = {}
        
        # Look for guidance sections
        guidance_sections = re.findall(
            r'(guidance|outlook|forecast).*?(\d{4}.*?)(?=\n\n|\n#|\Z)',
            content,
            re.IGNORECASE | re.DOTALL
        )
        
        for section_type, section_content in guidance_sections:
            guidance[section_type.lower()] = section_content.strip()
        
        return guidance
    
    def generate_trading_signals(self, metrics: Dict, guidance: Dict) -> List[Dict]:
        """Generate trading signals based on extracted data"""
        signals = []
        
        # Revenue growth signal
        if 'revenue' in metrics:
            revenue_text = metrics['revenue']
            if 'increase' in revenue_text.lower() or 'growth' in revenue_text.lower():
                signals.append({
                    'type': 'BULLISH',
                    'reason': 'Revenue growth detected',
                    'strength': 0.7,
                    'metric': 'revenue'
                })
        
        # EPS beat signal
        if 'eps' in metrics:
            eps_value = float(re.search(r'\d+\.\d+', metrics['eps']).group())
            if eps_value > 1.0:  # Example threshold
                signals.append({
                    'type': 'BULLISH',
                    'reason': f'Strong EPS: {eps_value}',
                    'strength': 0.8,
                    'metric': 'eps'
                })
        
        # Guidance signals
        for guidance_type, guidance_text in guidance.items():
            if any(word in guidance_text.lower() for word in ['positive', 'strong', 'increase']):
                signals.append({
                    'type': 'BULLISH',
                    'reason': f'Positive {guidance_type}',
                    'strength': 0.6,
                    'metric': 'guidance'
                })
            elif any(word in guidance_text.lower() for word in ['negative', 'weak', 'decrease']):
                signals.append({
                    'type': 'BEARISH',
                    'reason': f'Negative {guidance_type}',
                    'strength': 0.6,
                    'metric': 'guidance'
                })
        
        return signals
    
    def extract_company_name(self, content: str) -> Optional[str]:
        """Extract company name from document"""
        # Look for company name in title or header
        lines = content.split('\n')[:10]  # Check first 10 lines
        for line in lines:
            if 'inc' in line.lower() or 'corp' in line.lower() or 'ltd' in line.lower():
                return line.strip()
        return None
    
    def extract_quarter(self, content: str) -> Optional[str]:
        """Extract quarter information"""
        quarter_pattern = r'(Q[1-4]\s+\d{4}|[1-4]Q\s+\d{4}|quarter.*?\d{4})'
        quarter_match = re.search(quarter_pattern, content, re.IGNORECASE)
        return quarter_match.group(1) if quarter_match else None
    
    def calculate_confidence(self, metrics: Dict, guidance: Dict) -> float:
        """Calculate confidence score for analysis"""
        confidence = 0.0
        
        # Base confidence from extracted metrics
        confidence += len(metrics) * 0.2
        
        # Additional confidence from guidance
        confidence += len(guidance) * 0.1
        
        # Cap at 1.0
        return min(confidence, 1.0)

# Usage example
async def main():
    analyzer = SNIPERCORDocumentAnalyzer()
    
    # Analyze earnings report
    report_analysis = await analyzer.analyze_earnings_report('tesla_q4_2024.pdf')
    
    print(f"Company: {report_analysis['company']}")
    print(f"Quarter: {report_analysis['quarter']}")
    print(f"Confidence: {report_analysis['confidence']:.2f}")
    
    print("\nTrading Signals:")
    for signal in report_analysis['trading_signals']:
        print(f"- {signal['type']}: {signal['reason']} (Strength: {signal['strength']})")

if __name__ == "__main__":
    asyncio.run(main())
```

## 📊 **PERFORMANCE BENCHMARKS**

### **1. Processing Speed:**
- **MonkeyOCR-3B:** 0.84 pages/second
- **MinerU:** 0.65 pages/second  
- **Qwen2.5 VL-7B:** 0.12 pages/second

### **2. Accuracy Comparison:**
| Task Type | MonkeyOCR-3B | GPT-4o | Qwen2.5-VL-7B |
|-----------|--------------|--------|---------------|
| **Financial Reports** | **0.024** | 0.348 | 0.111 |
| **Tables** | **80.2%** | 72.0% | 76.4% |
| **Formulas** | **78.7%** | 72.8% | 79.0% |
| **Overall Text** | **0.058** | 0.144 | 0.157 |

### **3. Document Types Performance:**
```python
# Performance by document type (Edit Distance - lower is better)
document_performance = {
    'financial_reports': 0.024,  # Best performance
    'academic_papers': 0.024,
    'textbooks': 0.100,
    'books': 0.046,
    'newspapers': 0.131,
    'magazines': 0.086,
    'slides': 0.120,
    'exam_papers': 0.129,
    'notes': 0.643
}
```

## 🔧 **ADVANCED CONFIGURATION**

### **1. Custom Model Configuration:**
```yaml
# model_configs.yaml
chat_config:
  backend: lmdeploy  # or 'transformers'
  batch_size: 10
  max_tokens: 4096
  temperature: 0.1

structure_detection:
  model: "DocLayoutYOLO"  # or custom trained model
  confidence_threshold: 0.5
  nms_threshold: 0.4

recognition:
  formula_recognition: true
  table_recognition: true
  text_recognition: true
  
output:
  format: "markdown"
  include_layout: true
  include_blocks: true
```

### **2. Gradio Demo Setup:**
```python
import gradio as gr
from monkey_ocr import MonkeyOCR

def create_snipercor_demo():
    """Create Gradio demo for SNIPERCOR document analysis"""
    
    ocr = MonkeyOCR()
    analyzer = SNIPERCORDocumentAnalyzer()
    
    def process_document(file):
        if file is None:
            return "Please upload a file"
        
        try:
            # Process with MonkeyOCR
            result = ocr.parse(file.name)
            
            # Analyze for trading signals
            analysis = analyzer.analyze_earnings_report(file.name)
            
            # Format output
            output = f"""
## Document Analysis Results

**Company:** {analysis.get('company', 'Unknown')}
**Quarter:** {analysis.get('quarter', 'Unknown')}
**Confidence:** {analysis.get('confidence', 0):.2f}

### Trading Signals:
"""
            for signal in analysis.get('trading_signals', []):
                output += f"- **{signal['type']}**: {signal['reason']} (Strength: {signal['strength']})\n"
            
            output += f"\n### Extracted Content:\n{result['markdown'][:1000]}..."
            
            return output
            
        except Exception as e:
            return f"Error processing document: {str(e)}"
    
    # Create interface
    interface = gr.Interface(
        fn=process_document,
        inputs=gr.File(label="Upload Financial Document (PDF/Image)"),
        outputs=gr.Textbox(label="Analysis Results", lines=20),
        title="SNIPERCOR Document Analyzer",
        description="Upload financial documents to extract trading signals"
    )
    
    return interface

# Launch demo
if __name__ == "__main__":
    demo = create_snipercor_demo()
    demo.launch(share=True)
```

## 🎯 **INTEGRATION Z SNIPERCOR SYSTEM**

### **1. Real-time Document Processing:**
```python
import asyncio
import aiofiles
from pathlib import Path

class SNIPERCORDocumentProcessor:
    """Real-time document processor for SNIPERCOR"""
    
    def __init__(self, watch_directory: str):
        self.watch_directory = Path(watch_directory)
        self.analyzer = SNIPERCORDocumentAnalyzer()
        self.processed_files = set()
    
    async def watch_for_documents(self):
        """Watch directory for new financial documents"""
        while True:
            try:
                # Check for new PDF files
                pdf_files = list(self.watch_directory.glob("*.pdf"))
                
                for pdf_file in pdf_files:
                    if pdf_file not in self.processed_files:
                        await self.process_new_document(pdf_file)
                        self.processed_files.add(pdf_file)
                
                # Wait before next check
                await asyncio.sleep(10)
                
            except Exception as e:
                print(f"Error watching documents: {e}")
                await asyncio.sleep(30)
    
    async def process_new_document(self, pdf_path: Path):
        """Process newly detected document"""
        try:
            print(f"Processing new document: {pdf_path.name}")
            
            # Analyze document
            analysis = await self.analyzer.analyze_earnings_report(str(pdf_path))
            
            # Send signals to trading system
            await self.send_trading_signals(analysis)
            
            print(f"Completed processing: {pdf_path.name}")
            
        except Exception as e:
            print(f"Error processing {pdf_path.name}: {e}")
    
    async def send_trading_signals(self, analysis: Dict):
        """Send trading signals to SNIPERCOR trading engine"""
        signals = analysis.get('trading_signals', [])
        
        for signal in signals:
            if signal['strength'] > 0.7:  # High confidence signals only
                # Send to trading system
                trading_signal = {
                    'type': 'FUNDAMENTAL_ANALYSIS',
                    'direction': signal['type'],
                    'strength': signal['strength'],
                    'reason': signal['reason'],
                    'company': analysis.get('company'),
                    'timestamp': asyncio.get_event_loop().time()
                }
                
                # Here you would send to your trading system
                print(f"Trading Signal: {trading_signal}")

# Usage
processor = SNIPERCORDocumentProcessor("/path/to/earnings/reports")
asyncio.run(processor.watch_for_documents())
```

## 📚 **RESOURCES**

- [MonkeyOCR HuggingFace](https://huggingface.co/echo840/MonkeyOCR)
- [MonkeyOCR GitHub](https://github.com/Yuliang-Liu/MonkeyOCR)
- [Live Demo](http://vlrlabmonkey.xyz:7685)
- [ArXiv Paper](https://arxiv.org/abs/2506.05218)

---

**Status:** 🐵 **AI-POWERED** - Advanced document parsing dla SNIPERCOR fundamental analysis
