# AI Explanation Mode

The 5G Fronthaul Optimizer includes an **AI Explanation Layer** that automatically adapts based on API key availability.

## 🤖 How It Works

### **Automatic Mode Detection**

The system automatically detects whether you have a Gemini API key and chooses the best mode:

- **✅ API Key Present** → Uses AI mode (natural language generation)
- **📝 No API Key** → Uses template mode (pre-written explanations)

No configuration needed—it just works!

## 🚀 Quick Start

### **Option 1: Template Mode (Default)**

Just run the command—no API key needed:

```bash
python src/generate_explanations.py --data-folder data --output results/explanations
open dashboard.html
```

### **Option 2: AI Mode (With API Key)**

Set your Gemini API key as an environment variable:

```bash
export GEMINI_API_KEY="your-api-key-here"
python src/generate_explanations.py --data-folder data --output results/explanations
open dashboard.html
```

The system will automatically detect the API key and use AI mode!

## 📊 Mode Comparison

| Feature | Template Mode | AI Mode |
|---------|--------------|---------|
| **Setup** | None required | Requires API key |
| **Speed** | Instant | ~2-3 seconds per section |
| **Cost** | Free | ~$0.01 per run |
| **Quality** | Professional, consistent | More natural, contextual |
| **Offline** | ✅ Works offline | ❌ Requires internet |
| **Reliability** | 100% consistent | 99%+ (with fallback) |

## 🔑 Getting a Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy your key
4. Set environment variable:
   ```bash
   export GEMINI_API_KEY="your-key-here"
   ```

## 🛡️ Safety Guarantees

**Both modes enforce strict safety constraints:**

✅ **Read-Only**: Never modifies deterministic results  
✅ **No Speculation**: Blocks phrases like "might", "could", "possibly"  
✅ **Format Enforcement**: Standard Explanation → Decision → Safety format  
✅ **Validation**: Output checked before display  
✅ **Fallback**: AI mode falls back to template if generation fails  

## 💡 Example Outputs

### Template Mode
```
Explanation:
This cell shows average traffic of 0.02 Gbps, but peak bursts reach 0.1 Gbps—a 6x 
difference lasting only microseconds. Traditional capacity planning provisions for 
the 0.1 Gbps peak, wasting 80% of capacity during normal operation.

Decision:
Micro-bursts, not average load, drive capacity requirements.
```

### AI Mode
```
Explanation:
Notice how this cell's traffic pattern reveals the core problem: while average 
utilization hovers around just 20 Mbps, sudden bursts spike to 100 Mbps in 
microseconds. This 6x peak-to-average ratio forces traditional systems to 
over-provision by 500%, wasting capacity 98% of the time.

Decision:
Micro-bursts, not average load, drive capacity requirements.
```

## 🔧 Advanced Usage

### Force Template Mode
```bash
python src/generate_explanations.py --mode template --data-folder data
```

### Force AI Mode
```bash
python src/generate_explanations.py --mode ai --api-key "your-key" --data-folder data
```

### Auto Mode (Default)
```bash
python src/generate_explanations.py --mode auto --data-folder data
```

## 📦 Dependencies

**Template Mode**: No additional dependencies

**AI Mode**: Requires `google-generativeai`

```bash
pip install google-generativeai
```

## ❓ FAQ

**Q: Which mode should I use for the demo?**  
A: Template mode is perfect for demos—it's fast, reliable, and looks professional.

**Q: Will AI mode change my results?**  
A: No! AI only translates existing results into natural language. All computations remain identical.

**Q: What if AI generation fails?**  
A: The system automatically falls back to template mode with a warning message.

**Q: Can I use my own API key?**  
A: Yes! Set `GEMINI_API_KEY` environment variable or pass `--api-key` parameter.

## 🎯 Recommendation

For production use and demonstrations, **template mode is recommended**:
- No API costs
- Instant generation
- 100% reliable
- Works offline
- Professional quality

AI mode is a nice enhancement but not required!
