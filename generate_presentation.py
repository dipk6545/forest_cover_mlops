import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_deck(output_path="Forest_Cover_MLOps_Presentation.pptx"):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Clean Dark Theme Color Palette
    BG_COLOR = RGBColor(18, 24, 38)        # Deep navy/charcoal
    CARD_BG = RGBColor(28, 36, 56)         # Elevated container
    ACCENT_GREEN = RGBColor(46, 204, 113)  # Forest emerald
    ACCENT_BLUE = RGBColor(52, 152, 219)   # Highlight blue
    TEXT_WHITE = RGBColor(245, 247, 250)   # Clean white
    TEXT_MUTED = RGBColor(160, 174, 192)   # Cool grey

    def add_slide_bg(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_COLOR
        bg.line.fill.background()
        return bg

    def add_header(slide, title, subtitle=None):
        txBox = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.7), Inches(1.2))
        tf = txBox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(28)
        p.font.bold = True
        p.font.color.rgb = TEXT_WHITE
        p.font.name = "Arial"

        if subtitle:
            p2 = tf.add_paragraph()
            p2.text = subtitle
            p2.font.size = Pt(14)
            p2.font.color.rgb = ACCENT_GREEN
            p2.font.name = "Arial"
            p2.space_before = Pt(4)

    # -------------------------------------------------------------
    # SLIDE 1: TITLE SLIDE
    # -------------------------------------------------------------
    s1 = prs.slides.add_slide(blank_layout)
    add_slide_bg(s1)

    # Badge shape
    badge = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(3.2), Inches(0.45))
    badge.fill.solid()
    badge.fill.fore_color.rgb = CARD_BG
    badge.line.color.rgb = ACCENT_GREEN
    bp = badge.text_frame.paragraphs[0]
    bp.text = "ENTERPRISE MLOPS PLATFORM"
    bp.font.size = Pt(11)
    bp.font.bold = True
    bp.font.color.rgb = ACCENT_GREEN
    bp.alignment = PP_ALIGN.CENTER

    tbox = s1.shapes.add_textbox(Inches(0.8), Inches(2.4), Inches(11.5), Inches(2.2))
    tf1 = tbox.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "End-to-End Forest Cover Type\nMLOps System"
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = TEXT_WHITE

    p_sub = tf1.add_paragraph()
    p_sub.text = "Real-Time Streaming, Automated Training, Model Registry, and Production Observability"
    p_sub.font.size = Pt(18)
    p_sub.font.color.rgb = TEXT_MUTED
    p_sub.space_before = Pt(12)

    # Tech stack pills
    pills = ["FastAPI", "Apache Kafka", "LightGBM (94.2%)", "MLflow", "Prometheus", "Grafana", "Cloudflare R2", "Docker"]
    for i, pill in enumerate(pills):
        px = Inches(0.8 + (i % 4) * 2.9)
        py = Inches(5.1 + (i // 4) * 0.7)
        pshape = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px, py, Inches(2.7), Inches(0.5))
        pshape.fill.solid()
        pshape.fill.fore_color.rgb = CARD_BG
        pshape.line.color.rgb = ACCENT_BLUE
        ptf = pshape.text_frame.paragraphs[0]
        ptf.text = f"•  {pill}"
        ptf.font.size = Pt(12)
        ptf.font.color.rgb = TEXT_WHITE
        ptf.alignment = PP_ALIGN.CENTER

    # -------------------------------------------------------------
    # SLIDE 2: PROBLEM STATEMENT & DATASET
    # -------------------------------------------------------------
    s2 = prs.slides.add_slide(blank_layout)
    add_slide_bg(s2)
    add_header(s2, "Problem Statement & Dataset Design", "Forest Terrain Classification at Scale (581,012 survey rows)")

    cards_s2 = [
        ("The Challenge", "Classifying 7 distinct tree species across Roosevelt National Forest using 54 cartographic features (elevation, aspect, water distance, hillshade). Many species overlap in altitude and require non-linear spatial reasoning.", ACCENT_BLUE),
        ("Dataset Splitting Strategy", "• 70% Reference Baseline (406,708 rows) for feature engineering, hyperparameter tuning, and drift baselines.\n• 30% Production Stream (174,304 rows) reserved for real-time Kafka simulation.", ACCENT_GREEN),
        ("Domain Feature Engineering", "Engineered 3D Euclidean water distance, water elevation offset, aspect sine/cosine angular decomposition, and hillshade variance to boost decision tree splits across micro-climates.", ACCENT_BLUE)
    ]

    for i, (title, desc, accent) in enumerate(cards_s2):
        cx = Inches(0.8 + i * 3.95)
        cshape = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx, Inches(2.0), Inches(3.7), Inches(4.7))
        cshape.fill.solid()
        cshape.fill.fore_color.rgb = CARD_BG
        cshape.line.color.rgb = accent
        ctf = cshape.text_frame
        ctf.word_wrap = True
        
        p1 = ctf.paragraphs[0]
        p1.text = title
        p1.font.size = Pt(18)
        p1.font.bold = True
        p1.font.color.rgb = accent
        
        p2 = ctf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(13)
        p2.font.color.rgb = TEXT_WHITE
        p2.space_before = Pt(14)

    # -------------------------------------------------------------
    # SLIDE 3: SYSTEM ARCHITECTURE
    # -------------------------------------------------------------
    s3 = prs.slides.add_slide(blank_layout)
    add_slide_bg(s3)
    add_header(s3, "Enterprise End-to-End Architecture", "Decoupled Microservice Design Containerized via Docker")

    arch_steps = [
        ("1. Ingestion & Storage", "Cloudflare R2 stores raw/reference datasets and serialized model artifacts. PostgreSQL tracks MLflow metadata.", Inches(0.8), Inches(2.0), Inches(5.6), Inches(2.1)),
        ("2. Training & MLflow", "Optuna Bayesian search optimizes LightGBM hyperparameters across 5 trials, logging 94.3% accuracy directly to MLflow.", Inches(6.8), Inches(2.0), Inches(5.6), Inches(2.1)),
        ("3. Event Streaming", "Confluent Kafka (KRaft mode) ingests terrain surveys row-by-row on topic 'terrain_survey.raw' with zero data loss.", Inches(0.8), Inches(4.5), Inches(5.6), Inches(2.2)),
        ("4. Serving & Monitoring", "FastAPI scores incoming Kafka events (<50ms p95 latency); Prometheus and Grafana provide real-time dashboard observability.", Inches(6.8), Inches(4.5), Inches(5.6), Inches(2.2))
    ]

    for title, desc, x, y, w, h in arch_steps:
        box = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
        box.fill.solid()
        box.fill.fore_color.rgb = CARD_BG
        box.line.color.rgb = ACCENT_GREEN
        btf = box.text_frame
        btf.word_wrap = True
        
        p1 = btf.paragraphs[0]
        p1.text = title
        p1.font.size = Pt(16)
        p1.font.bold = True
        p1.font.color.rgb = ACCENT_GREEN

        p2 = btf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(12)
        p2.font.color.rgb = TEXT_WHITE
        p2.space_before = Pt(8)

    # -------------------------------------------------------------
    # SLIDE 4: MODELING & MLFLOW EXPERIMENT TRACKING
    # -------------------------------------------------------------
    s4 = prs.slides.add_slide(blank_layout)
    add_slide_bg(s4)
    add_header(s4, "Model Selection & Optuna Optimization", "From Baseline to 94.2% Production Accuracy")

    # Metrics comparison table
    t_shape = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(2.0), Inches(6.5), Inches(4.7))
    t_shape.fill.solid()
    t_shape.fill.fore_color.rgb = CARD_BG
    t_shape.line.color.rgb = ACCENT_BLUE
    ttf = t_shape.text_frame
    ttf.word_wrap = True
    
    tp1 = ttf.paragraphs[0]
    tp1.text = "Benchmark Progression"
    tp1.font.size = Pt(18)
    tp1.font.bold = True
    tp1.font.color.rgb = ACCENT_BLUE

    tp2 = ttf.add_paragraph()
    tp2.text = "• Logistic Regression (Baseline): 72.4% Test Accuracy\n  Failed on minority tree classes like Aspen and Cottonwood.\n\n• LightGBM Default: 91.4% Test Accuracy\n  Sub-millisecond inference and high tree depth partitioning.\n\n• LightGBM + Optuna Bayesian Tuning: 94.2% Test Accuracy\n  Best parameters: num_leaves=71, learning_rate=0.096, n_estimators=250, colsample=0.79."
    tp2.font.size = Pt(13)
    tp2.font.color.rgb = TEXT_WHITE
    tp2.space_before = Pt(12)

    # Right side: What MLflow Tracks
    r_shape = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.7), Inches(2.0), Inches(4.8), Inches(4.7))
    r_shape.fill.solid()
    r_shape.fill.fore_color.rgb = CARD_BG
    r_shape.line.color.rgb = ACCENT_GREEN
    rtf = r_shape.text_frame
    rtf.word_wrap = True

    rp1 = rtf.paragraphs[0]
    rp1.text = "MLflow Capabilities Used"
    rp1.font.size = Pt(18)
    rp1.font.bold = True
    rp1.font.color.rgb = ACCENT_GREEN

    rp2 = rtf.add_paragraph()
    rp2.text = "✓ Real-Time UI Tracking (Port 5000)\n  Every trial logged with loss curves and validation metrics.\n\n✓ Model Artifact Storage\n  Direct Cloudflare R2 artifact sync and versioning.\n\n✓ Model Registry Lifecycle\n  Registered as 'LightGBM_Production_Champion' with schema metadata and feature order."
    rp2.font.size = Pt(13)
    rp2.font.color.rgb = TEXT_WHITE
    rp2.space_before = Pt(12)

    # -------------------------------------------------------------
    # SLIDE 5: PRODUCTION MONITORING & DRIFT DETECTION
    # -------------------------------------------------------------
    s5 = prs.slides.add_slide(blank_layout)
    add_slide_bg(s5)
    add_header(s5, "Production Observability & Drift Monitoring", "Live Grafana Telemetry + Kolmogorov-Smirnov (KS) Testing")

    cards_s5 = [
        ("Grafana Real-Time Dashboard", "• Total Predictions Served Counter (Live)\n• Live Request Rate (req/sec time-series)\n• 7-Species Class Distribution (Donut Chart)\n• p95 (<50ms) and Median p50 (<20ms) Latency", ACCENT_GREEN),
        ("Kolmogorov-Smirnov Drift Test", "• Evaluates continuous distributions (Elevation, Slope, Water Distances) using scipy.stats.ks_2samp.\n• Null hypothesis tested at alpha = 0.05.\n• Flags synthetic domain shift (+400m elevation) with p-value = 0.0000.", ACCENT_BLUE),
        ("CI/CD Automation", "• GitHub Actions builds and validates Docker images on every push to main.\n• Automatic publishing to GitHub Container Registry (ghcr.io) for zero-compilation startup in Codespaces.", ACCENT_GREEN)
    ]

    for i, (title, desc, accent) in enumerate(cards_s5):
        cx = Inches(0.8 + i * 3.95)
        cshape = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx, Inches(2.0), Inches(3.7), Inches(4.7))
        cshape.fill.solid()
        cshape.fill.fore_color.rgb = CARD_BG
        cshape.line.color.rgb = accent
        ctf = cshape.text_frame
        ctf.word_wrap = True
        
        p1 = ctf.paragraphs[0]
        p1.text = title
        p1.font.size = Pt(17)
        p1.font.bold = True
        p1.font.color.rgb = accent
        
        p2 = ctf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(12.5)
        p2.font.color.rgb = TEXT_WHITE
        p2.space_before = Pt(12)

    # Save presentation
    prs.save(output_path)
    print(f"Presentation saved successfully to: {output_path}")

if __name__ == "__main__":
    create_deck("/mnt/HDD/MDEP-CDE Project/MDEP/forest_cover_mlops/Forest_Cover_MLOps_Presentation.pptx")
