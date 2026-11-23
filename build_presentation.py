import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def build_presentation(output_path="Forest_Cover_MLOps_Final_Presentation.pptx"):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Clean, professional, minimal color palette (White / Subtle Light Grey)
    BG_WHITE = RGBColor(255, 255, 255)
    PANEL_BG = RGBColor(248, 250, 252)       # Light Slate
    BORDER_COLOR = RGBColor(226, 232, 240)   # Light Grey border
    TEXT_MAIN = RGBColor(15, 23, 42)         # Deep slate/black
    TEXT_MUTED = RGBColor(71, 85, 105)       # Cool slate grey
    ACCENT = RGBColor(14, 116, 144)          # Deep Cyan / Teal
    ACCENT_GREEN = RGBColor(22, 101, 52)     # Forest Green

    def set_white_bg(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_WHITE
        bg.line.fill.background()

    def add_header(slide, title, category="FOREST COVER TYPE MLOPS"):
        # Category tag
        cbox = slide.shapes.add_textbox(Inches(0.9), Inches(0.55), Inches(11.5), Inches(0.4))
        ctf = cbox.text_frame
        ctf.word_wrap = True
        cp = ctf.paragraphs[0]
        cp.text = category.upper()
        cp.font.size = Pt(11)
        cp.font.bold = True
        cp.font.color.rgb = ACCENT
        cp.font.name = "Arial"

        # Main Title
        tbox = slide.shapes.add_textbox(Inches(0.9), Inches(0.9), Inches(11.5), Inches(0.8))
        ttf = tbox.text_frame
        ttf.word_wrap = True
        tp = ttf.paragraphs[0]
        tp.text = title
        tp.font.size = Pt(26)
        tp.font.bold = True
        tp.font.color.rgb = TEXT_MAIN
        tp.font.name = "Arial"

        # Divider line
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(1.75), Inches(11.5), Inches(0.02))
        line.fill.solid()
        line.fill.fore_color.rgb = BORDER_COLOR
        line.line.fill.background()

    def add_card(slide, left, top, width, height, title, items, badge=None):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = PANEL_BG
        card.line.color.rgb = BORDER_COLOR
        card.line.width = Pt(1)

        txBox = slide.shapes.add_textbox(left + Inches(0.25), top + Inches(0.2), width - Inches(0.5), height - Inches(0.4))
        tf = txBox.text_frame
        tf.word_wrap = True

        p_title = tf.paragraphs[0]
        p_title.text = title
        p_title.font.size = Pt(16)
        p_title.font.bold = True
        p_title.font.color.rgb = TEXT_MAIN
        p_title.font.name = "Arial"

        if badge:
            p_badge = tf.add_paragraph()
            p_badge.text = badge
            p_badge.font.size = Pt(11)
            p_badge.font.bold = True
            p_badge.font.color.rgb = ACCENT
            p_badge.space_before = Pt(2)
            p_badge.space_after = Pt(8)

        for item in items:
            p_item = tf.add_paragraph()
            p_item.text = f"•  {item}"
            p_item.font.size = Pt(12)
            p_item.font.color.rgb = TEXT_MUTED
            p_item.font.name = "Arial"
            p_item.space_before = Pt(6)

    # -------------------------------------------------------------
    # SLIDE 1: TITLE SLIDE (Simple & Minimal)
    # -------------------------------------------------------------
    s1 = prs.slides.add_slide(blank_layout)
    set_white_bg(s1)

    tbox1 = s1.shapes.add_textbox(Inches(1.0), Inches(2.2), Inches(11.3), Inches(3.5))
    tf1 = tbox1.text_frame
    tf1.word_wrap = True

    p_badge = tf1.paragraphs[0]
    p_badge.text = "END-TO-END MACHINE LEARNING OPERATIONS (MLOPS)"
    p_badge.font.size = Pt(12)
    p_badge.font.bold = True
    p_badge.font.color.rgb = ACCENT

    p_main = tf1.add_paragraph()
    p_main.text = "Forest Cover Type Classification Platform"
    p_main.font.size = Pt(38)
    p_main.font.bold = True
    p_main.font.color.rgb = TEXT_MAIN
    p_main.space_before = Pt(10)

    p_desc = tf1.add_paragraph()
    p_desc.text = "Real-Time Event Streaming, Automated Model Serving, Experiment Tracking & Production Observability"
    p_desc.font.size = Pt(16)
    p_desc.font.color.rgb = TEXT_MUTED
    p_desc.space_before = Pt(14)

    p_tech = tf1.add_paragraph()
    p_tech.text = "Technologies: LightGBM | FastAPI | Apache Kafka | MLflow | Grafana Cloud | Aiven PostgreSQL | Evidently AI | Docker"
    p_tech.font.size = Pt(13)
    p_tech.font.bold = True
    p_tech.font.color.rgb = ACCENT_GREEN
    p_tech.space_before = Pt(24)

    # -------------------------------------------------------------
    # SLIDE 2: PROJECT OVERVIEW & PROBLEM STATEMENT
    # -------------------------------------------------------------
    s2 = prs.slides.add_slide(blank_layout)
    set_white_bg(s2)
    add_header(s2, "Project Overview & Problem Statement", "Introduction & Scope")

    cards_s2 = [
        ("The Business Problem", "Core Objective", [
            "Predict forest cover type (7 distinct tree species) from cartographic variables across 581,012 wilderness survey plots.",
            "Species such as Spruce/Fir, Lodgepole Pine, Ponderosa Pine, and Aspen have overlapping high-altitude ranges.",
            "Requires an ultra-low latency inference engine capable of scoring incoming survey records in real time."
        ]),
        ("Dataset Split & Architecture", "Data Partitioning", [
            "Total Dataset: 581,012 samples with 54 raw geological & spatial attributes.",
            "Reference Baseline (70%): 406,708 records used for feature engineering, model training, and reference drift profile.",
            "Production Stream (30%): 174,304 records reserved for simulating live streaming traffic through Kafka."
        ]),
        ("Engineering Highlights", "Operational Goals", [
            "Sub-15ms prediction latency on single survey queries.",
            "Real-time event-driven scoring decoupled via Apache Kafka.",
            "Centralized experiment tracking and model registration via MLflow.",
            "Cloud-native monitoring with Grafana Cloud connected to Aiven PostgreSQL."
        ])
    ]

    for i, (title, badge, items) in enumerate(cards_s2):
        add_card(s2, Inches(0.9 + i * 3.9), Inches(2.0), Inches(3.7), Inches(4.8), title, items, badge)

    # -------------------------------------------------------------
    # SLIDE 3: COMPLETE TECHNOLOGY STACK
    # -------------------------------------------------------------
    s3 = prs.slides.add_slide(blank_layout)
    set_white_bg(s3)
    add_header(s3, "Technologies & Tools Used", "End-to-End Technology Stack")

    tech_cards = [
        ("ML & Feature Engineering", "Core Modeling", [
            "LightGBM: Fast gradient boosting classifier (94.2% accuracy).",
            "Optuna: Automated Bayesian hyperparameter search.",
            "Scikit-Learn: Pipelines, scaling, and evaluation metrics.",
            "Pandas & NumPy: High-throughput tabular data transformations."
        ]),
        ("Serving & Streaming", "Inference & Ingestion", [
            "FastAPI: Production REST API serving /predict endpoint.",
            "Apache Kafka (KRaft): Distributed event broker without Zookeeper.",
            "Confluent Kafka Python: High-performance streaming producer & consumer.",
            "Uvicorn: Lightning-fast ASGI web server."
        ]),
        ("Tracking & Storage", "Data & Model Lifecycle", [
            "MLflow: Experiment tracking, metric logs, and Model Registry.",
            "Cloudflare R2: S3-compatible cloud object storage for model artifacts.",
            "Aiven PostgreSQL: Managed cloud DB for MLflow backend & inference logs.",
            "DVC: Data Version Control tracking large CSV assets."
        ]),
        ("Monitoring & Deployment", "Observability & CI/CD", [
            "Grafana Cloud: Real-time cloud dashboard for live inference metrics.",
            "Evidently AI: Statistical data drift detection & interactive reports.",
            "Docker & Docker Compose: Clean 3-container local stack (Kafka, API, MLflow).",
            "GitHub Actions: Automated CI/CD pipeline and container image publishing."
        ])
    ]

    for i, (title, badge, items) in enumerate(tech_cards):
        add_card(s3, Inches(0.9 + i * 2.92), Inches(2.0), Inches(2.75), Inches(4.8), title, items, badge)

    # -------------------------------------------------------------
    # SLIDE 4: SYSTEM ARCHITECTURE & DATA FLOW
    # -------------------------------------------------------------
    s4 = prs.slides.add_slide(blank_layout)
    set_white_bg(s4)
    add_header(s4, "End-to-End System Architecture", "Data Pipeline Flow")

    steps = [
        ("1. Data Ingestion & Streaming", "Producer Component", [
            "Reads production stream batches from processed CSV data.",
            "Publishes JSON-serialized terrain records to Kafka topic 'terrain_survey.raw'.",
            "Configurable rate limits (e.g., 50 to 500 samples at custom delay intervals)."
        ]),
        ("2. Real-Time Scoring Consumer", "Processing Engine", [
            "Python background consumer subscribes to Kafka topic.",
            "Invokes FastAPI '/predict' endpoint via internal HTTP POST.",
            "FastAPI runs LightGBM champion model and returns predicted class + confidence."
        ]),
        ("3. Storage & Observability", "Sink & Cloud Monitoring", [
            "Consumer writes scored inferences directly to Aiven PostgreSQL 'model_inferences' table.",
            "Publishes enriched records to Kafka output topic 'terrain_survey.predictions'.",
            "Grafana Cloud queries Aiven PostgreSQL to display real-time throughput, latency, and tree species distributions."
        ])
    ]

    for i, (title, badge, items) in enumerate(steps):
        add_card(s4, Inches(0.9 + i * 3.9), Inches(2.0), Inches(3.7), Inches(4.8), title, items, badge)

    # -------------------------------------------------------------
    # SLIDE 5: MODEL TRAINING & MLFLOW EXPERIMENTATION
    # -------------------------------------------------------------
    s5 = prs.slides.add_slide(blank_layout)
    set_white_bg(s5)
    add_header(s5, "Model Training, Optimization & Registry", "MLflow Integration")

    m_cards = [
        ("Model Benchmark Progression", "Accuracy Growth", [
            "Baseline (Logistic Regression): 72.4% test accuracy (struggled with class imbalance on rare trees).",
            "Default LightGBM: 91.4% test accuracy with default hyperparameters.",
            "Optuna Tuned LightGBM: 94.2% test accuracy (num_leaves=71, learning_rate=0.096, n_estimators=250)."
        ]),
        ("MLflow Tracking & Registry", "Model Governance", [
            "Tracks training parameters, multi-class log loss, accuracy, and confusion matrices.",
            "Model artifacts saved directly to Cloudflare R2 object storage.",
            "Registered in MLflow Model Registry as 'LightGBM_Production_Champion' with validated schema."
        ]),
        ("Feature Importance Insights", "Geological Drivers", [
            "Top Feature 1: Elevation (strongest altitude-based predictor for species).",
            "Top Feature 2: Horizontal Distance to Roadways & Fire Points.",
            "Top Feature 3: Hillshade variance and 3D Euclidean distance to hydrology."
        ])
    ]

    for i, (title, badge, items) in enumerate(m_cards):
        add_card(s5, Inches(0.9 + i * 3.9), Inches(2.0), Inches(3.7), Inches(4.8), title, items, badge)

    # -------------------------------------------------------------
    # SLIDE 6: MONITORING, OBSERVABILITY & DRIFT DETECTION
    # -------------------------------------------------------------
    s6 = prs.slides.add_slide(blank_layout)
    set_white_bg(s6)
    add_header(s6, "Production Monitoring & Drift Detection", "Grafana Cloud & Evidently AI")

    obs_cards = [
        ("Grafana Cloud Dashboard", "Real-Time Telemetry", [
            "Connected directly to Aiven PostgreSQL via secure Cloud Datasource.",
            "Live Counter: Total production predictions served.",
            "Throughput & Latency: Average inference latency gauge (p50: ~14ms, p95: <35ms).",
            "Class Distribution: Real-time pie and bar breakdowns of predicted tree species."
        ]),
        ("Evidently AI Drift Analysis", "Statistical Testing", [
            "Evaluates continuous feature drift (Wasserstein distance & Kolmogorov-Smirnov test).",
            "Compares 406K reference training baseline against live incoming production batches.",
            "Interactive HTML reports generated under 'backend/monitoring/reports/latest_drift_report.html'."
        ]),
        ("Automated Drift Testing", "Validation Mode", [
            "Supports simulated domain shift (e.g. +400m elevation survey bias).",
            "Automatically detects distribution divergence, triggers drift alerts, and records p-values.",
            "Command: ./check_drift.sh 2000 --drift."
        ])
    ]

    for i, (title, badge, items) in enumerate(obs_cards):
        add_card(s6, Inches(0.9 + i * 3.9), Inches(2.0), Inches(3.7), Inches(4.8), title, items, badge)

    # -------------------------------------------------------------
    # SLIDE 7: KEY PROJECT COMMANDS & AUTOMATION
    # -------------------------------------------------------------
    s7 = prs.slides.add_slide(blank_layout)
    set_white_bg(s7)
    add_header(s7, "Execution & Automation Commands", "One-Command Operations")

    cmd_cards = [
        ("Start Core Stack", "Local Environment", [
            "docker compose up -d",
            "Starts minimal 3-container local stack:",
            "  1. Apache Kafka KRaft (Port 9092)",
            "  2. FastAPI Model Engine (Port 8000)",
            "  3. MLflow Tracking Server (Port 5000)"
        ]),
        ("Stream & Score Inferences", "Single Command", [
            "./stream.sh <SAMPLES> <DELAY>",
            "Example: ./stream.sh 100 0.05",
            "Automatically sets up Kafka topics, starts background scoring consumer, streams events, and writes to Aiven DB."
        ]),
        ("Check Data Drift", "Single Command", [
            "./check_drift.sh <SAMPLES>",
            "Example: ./check_drift.sh 2000",
            "With drift simulation: ./check_drift.sh 2000 --drift",
            "Runs Evidently AI and outputs interactive HTML report."
        ]),
        ("Clean Teardown", "Reset Stack", [
            "docker compose down -v --remove-orphans",
            "Kills lingering consumers and cleans local state without touching cloud database."
        ])
    ]

    for i, (title, badge, items) in enumerate(cmd_cards):
        add_card(s7, Inches(0.9 + i * 2.92), Inches(2.0), Inches(2.75), Inches(4.8), title, items, badge)

    # -------------------------------------------------------------
    # SLIDE 8: SUMMARY & CONCLUSION
    # -------------------------------------------------------------
    s8 = prs.slides.add_slide(blank_layout)
    set_white_bg(s8)
    add_header(s8, "Summary & Key Takeaways", "Conclusion")

    summary_cards = [
        ("High Model Performance", "Results", [
            "94.2% test accuracy achieved using Optuna Bayesian hyperparameter optimization on LightGBM.",
            "Sub-15ms real-time inference latency under continuous Kafka streaming load."
        ]),
        ("Clean Architecture", "Decoupled Design", [
            "Zero local container clutter: Observability offloaded to Grafana Cloud and Aiven PostgreSQL.",
            "Clean 3-service local setup for minimal resource footprint in Codespaces."
        ]),
        ("Production Readiness", "Industry Standards", [
            "Full experiment tracking and artifact lineage via MLflow & Cloudflare R2.",
            "Automated data drift detection using Evidently AI.",
            "Reproducible one-line execution scripts for live streaming and drift audits."
        ])
    ]

    for i, (title, badge, items) in enumerate(summary_cards):
        add_card(s8, Inches(0.9 + i * 3.9), Inches(2.0), Inches(3.7), Inches(4.8), title, items, badge)

    # Save presentation
    prs.save(output_path)
    print(f"Presentation saved successfully to: {output_path}")

if __name__ == "__main__":
    out = "/mnt/HDD/MDEP-CDE Project/MDEP/forest_cover_mlops/Forest_Cover_MLOps_Final_Presentation.pptx"
    build_presentation(out)
