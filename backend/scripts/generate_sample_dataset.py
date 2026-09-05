import json
import os

DOMAINS = [
    "Artificial Intelligence", "Agriculture", "Healthcare", "IoT", 
    "Robotics", "Energy", "Manufacturing", "Software", "Electronics", "Biotechnology"
]

PATENT_TEMPLATES = [
    # Artificial Intelligence
    {
        "domain": "Artificial Intelligence",
        "title": "Neural Network-Based Real-Time Object Recognition for Autonomous Vehicles",
        "abstract": "A deep learning framework utilizing convolutional neural networks and spatial transformer networks to detect, classify, and track dynamic urban obstacles in multi-modal sensor fusion data.",
        "description": "The invention comprises a deep convolutional neural network architecture with custom feature pyramid networks integrated with LiDAR point cloud inputs. The system processes video streams at 60 FPS while running sensor fusion algorithms to identify pedestrians, vehicles, and road hazards with low temporal latency.",
        "inventors": "Dr. Sarah Chen, Michael Vance",
        "assignee": "Cognitive AI Systems Inc.",
        "pub_date": "2024-03-15"
    },
    {
        "domain": "Artificial Intelligence",
        "title": "Transformer-Based Large Language Model Optimization for Low-Resource Edge Computing",
        "abstract": "A method for quantizing and pruning generative transformer models for on-device natural language inferencing with minimal accuracy degradation.",
        "description": "This patent describes an adaptive 4-bit quantization scheme combined with unstructured layer pruning to compress transformer weights. A execution runtime schedules dynamic attention head evaluation based on available RAM and battery telemetry.",
        "inventors": "Elena Rostova, David K. Miller",
        "assignee": "EdgeGen Technologies LLC",
        "pub_date": "2023-11-20"
    },
    {
        "domain": "Artificial Intelligence",
        "title": "Automated Anomaly Detection Engine Using Unsupervised Generative Adversarial Networks",
        "abstract": "An unsupervised anomaly detection system utilizing spatial-temporal GANs to detect structural anomalies in high-frequency financial telemetry.",
        "description": "The system includes a generator network trained on latent time-series representations and a discriminator calculating reconstruction loss metrics. Divergence above dynamic thresholds triggers real-time visual alerts.",
        "inventors": "Marcus Vance, Priya Nair",
        "assignee": "Aegis Analytics Corp.",
        "pub_date": "2024-01-10"
    },
    {
        "domain": "Artificial Intelligence",
        "title": "Reinforcement Learning Control Architecture for Dynamic Quadrupedal Locomotion",
        "abstract": "An end-to-end deep reinforcement learning policy for continuous gait adaptation across unstructured terrain.",
        "description": "A neural policy trained via proximal policy optimization receives proprioceptive joint telemetry and height map estimates to adjust joint torques dynamically at 500 Hz.",
        "inventors": "Kenji Sato, Hannah Schmidt",
        "assignee": "RoboKinematics Labs",
        "pub_date": "2023-08-05"
    },
    {
        "domain": "Artificial Intelligence",
        "title": "Self-Supervised Contrastive Learning for Multi-Omics Biomedical Pattern Recognition",
        "abstract": "A multimodal representation learning pipeline combining genomic sequencing vectors and histological image embeddings.",
        "description": "Cross-modal contrastive loss aligns feature spaces from gene expression arrays and digital pathology slides, enabling automated biomarker candidate identification.",
        "inventors": "Dr. Aris Thorne, Linda Hu",
        "assignee": "BioSyn AI Corp.",
        "pub_date": "2024-05-12"
    },

    # Agriculture
    {
        "domain": "Agriculture",
        "title": "AI-Driven Precision Soil Moisture Analysis and Variable-Rate Automated Irrigation System",
        "abstract": "An automated agricultural irrigation network incorporating subterranean soil moisture sensors, weather API forecasts, and machine learning models for optimized crop watering schedules.",
        "description": "The system utilizes distributed moisture and NPK sensor arrays transmitting soil telemetry via LoRaWAN to a central edge controller. A predictive machine learning model computes daily evapotranspiration rates and controls variable-rate solenoid valves to minimize water wastage while preserving crop yield.",
        "inventors": "Robert E. Sterling, Maria Gonzalez",
        "assignee": "AgriTech Innovators Ltd.",
        "pub_date": "2023-09-12"
    },
    {
        "domain": "Agriculture",
        "title": "Autonomous Crop Weed Discrimination and Laser Targeted Micro-Weeding Drone",
        "abstract": "An aerial drone system equipped with multispectral cameras and targeted laser diodes for real-time invasive plant ablation in field crops.",
        "description": "High-resolution hyperspectral cameras feed a lightweight YOLO visual model running on onboard neural accelerators. Detected weed hypocotyls are targeted by galvo-steered diode lasers for thermal eradication without chemical herbicides.",
        "inventors": "Johan Lindqvist, Amy Zhang",
        "assignee": "TerraPulse Robotics",
        "pub_date": "2024-02-28"
    },
    {
        "domain": "Agriculture",
        "title": "Vertical Farming Environmental Control Unit with Adaptive LED Spectral Tuning",
        "abstract": "A closed-loop hydroponic farm controller dynamically altering light spectrum wavelengths according to crop photosynthetic response stages.",
        "description": "Quantum yield sensors measure crop chlorophyll fluorescence and automatically modulate blue, red, and far-red LED channels to optimize biomass accumulation during specific growth phases.",
        "inventors": "Clara Bell, Samuel O'Connor",
        "assignee": "Verdant Crop Systems",
        "pub_date": "2023-12-04"
    },
    {
        "domain": "Agriculture",
        "title": "Predictive Crop Disease Forecasting Platform Using Micro-Climate Internet-of-Things Sensors",
        "abstract": "A micro-climate telemetry network calculating fungal spore germination indices to schedule targeted preventative bio-fungicide applications.",
        "description": "Wireless leaf wetness and canopy humidity nodes stream environmental data to a cloud machine learning pipeline executing sporulation risk algorithms.",
        "inventors": "Vikram Malhotra, Brenda Ross",
        "assignee": "CropShield AI",
        "pub_date": "2024-04-18"
    },

    # Healthcare
    {
        "domain": "Healthcare",
        "title": "Wearable Continuous Electrocardiogram Monitoring System with On-Chip Arrhythmia Classification",
        "abstract": "A miniature single-lead ECG patch containing ultra-low-power signal processing hardware for automatic atrial fibrillation event detection.",
        "description": "Analog front-end filters record cardiac bio-potentials and convert them into discrete pulse trains processed by a spiking neural network chip. Detected cardiac anomalies trigger encrypted Bluetooth Low Energy alerts to patient smartphones.",
        "inventors": "Dr. James L. Harper, Sun-Hee Park",
        "assignee": "PulseCare Medical Technologies",
        "pub_date": "2024-01-22"
    },
    {
        "domain": "Healthcare",
        "title": "Non-Invasive Continuous Glucose Monitor Using Near-Infrared Multi-Wavelength Spectroscopy",
        "abstract": "An optical skin sensor computing blood glucose concentrations from differential NIR absorption spectra.",
        "description": "Multiple vertical-cavity surface-emitting lasers emit specific infrared bands through subdermal capillary beds. A photodiode array measures reflected intensity patterns filtered through machine learning regression models.",
        "inventors": "Dr. Arthur Vance, Emily Watson",
        "assignee": "GlucoOptics Corp.",
        "pub_date": "2023-10-14"
    },
    {
        "domain": "Healthcare",
        "title": "Robotic Surgical End-Effector with Real-Time Haptic Force Feedback Telemanipulation",
        "abstract": "A minimally invasive surgical instrument featuring fiber Bragg grating strain sensors for tissue resistance feedback.",
        "description": "Strain changes along miniature tool shafts modulate laser wavelength reflections, providing surgical operators sub-gram tactile feedback via motorized master controller joysticks.",
        "inventors": "Dr. Charles DeLuca, Maya Lin",
        "assignee": "PrecisionSurgical Inc.",
        "pub_date": "2024-06-01"
    },

    # IoT (Internet of Things)
    {
        "domain": "IoT",
        "title": "Ultra-Low-Power Ambient Energy Harvesting Wireless Sensor Node for Industrial Asset Tracking",
        "abstract": "A self-powered IoT node combining piezoelectric vibration energy harvesting and thermoelectric modules with ultra-wideband location tracking.",
        "description": "Piezoelectric transducers convert machine mechanical vibrations into electrical energy stored in a supercapacitor bank. An ultra-wideband radio broadcasts asset position vectors at microamp sleep currents.",
        "inventors": "Thomas Wright, Alexey Petrov",
        "assignee": "OmniSense Networks",
        "pub_date": "2023-07-30"
    },
    {
        "domain": "IoT",
        "title": "Decentralized Edge Mesh Gateway Architecture for Secure Smart Grid Telemetry",
        "abstract": "A zero-trust cryptographic mesh network protocol for distributed utility meters and microgrid inverter nodes.",
        "description": "Each edge smart meter node establishes hardware security module (HSM) authenticated TLS tunnels over sub-GHz mesh radio bands to prevent grid cyber-tampering.",
        "inventors": "Gautam Patel, Sarah O'Neill",
        "assignee": "GridLock IoT Solutions",
        "pub_date": "2024-04-05"
    },

    # Robotics
    {
        "domain": "Robotics",
        "title": "Compliance-Controlled Dual-Arm Manipulator for Safe Human-Robot Collaborative Assembly",
        "abstract": "A collaborative robot (cobot) system utilizing joint torque sensors and impedance control for real-time contact force regulation.",
        "description": "Harmonic drive gearboxes integrate strain-gauge torque transducers. A safety controller limits dynamic collision forces below ISO 15066 safety limits without stopping assembly operations.",
        "inventors": "Dr. Frank Mueller, Lisa Yamamoto",
        "assignee": "KineTech Robotics",
        "pub_date": "2023-12-19"
    },
    {
        "domain": "Robotics",
        "title": "Autonomous Mobile Robot Visual SLAM Using Stereo Fisheye Cameras and Inertial Odometry",
        "abstract": "A spatial navigation system mapping dynamic warehouse environments under fluctuating illumination.",
        "description": "Dual fisheye cameras combined with a 9-axis IMU feed a non-linear factor graph optimizer to build real-time sub-centimeter point maps while dynamic forklifts are masked.",
        "inventors": "Carlos Ruiz, Hannah Brooks",
        "assignee": "LogiBot Mobility",
        "pub_date": "2024-02-14"
    },

    # Energy
    {
        "domain": "Energy",
        "title": "Hybrid Solid-State Lithium Battery Electrolyte with High Ionic Conductivity and Dendrite Suppression",
        "abstract": "A ceramic-polymer composite solid electrolyte enabling stable cycling of high-voltage lithium metal anode batteries.",
        "description": "Garnet-type LLZO ceramic nanowires embedded in a cross-linked poly(ethylene oxide) matrix eliminate dendrite penetration and extend battery charge cycles above 2000 iterations.",
        "inventors": "Dr. Wei Zhang, Kevin O'Reilly",
        "assignee": "SolidVolt Energy Inc.",
        "pub_date": "2024-03-02"
    },
    {
        "domain": "Energy",
        "title": "Bifacial Perovskite-Silicon Tandem Photovoltaic Cell Architecture with Gradient Texturing",
        "abstract": "A high-efficiency solar panel utilizing top perovskite layers and silicon bottom cells to absorb solar radiation up to 32% efficiency.",
        "description": "Sub-micron pyramid optical texturing minimizes light reflection while atomic layer deposited metal oxide passivating contacts prevent charge recombination.",
        "inventors": "Dr. Sophia Lind, Eric Fournier",
        "assignee": "HelioTech Photovoltaics",
        "pub_date": "2023-09-25"
    },

    # Manufacturing
    {
        "domain": "Manufacturing",
        "title": "Closed-Loop Laser Powder Bed Fusion Additive Manufacturing System with Melt Pool Thermal Monitoring",
        "abstract": "A 3D metal printing system incorporating high-speed infrared cameras and real-time laser power control to eliminate porosity defects.",
        "description": "Coaxial pyrometers monitor melt pool thermal radiation at 20 kHz, dynamically adjusting laser spot intensity to prevent keyhole porosity in aerospace titanium alloy parts.",
        "inventors": "Heinrich Vance, Catherine Bell",
        "assignee": "AeroAdditives Corp.",
        "pub_date": "2024-05-08"
    },
    {
        "domain": "Manufacturing",
        "title": "Automated Computer Vision Surface Quality Inspection Inspection System for Cold-Rolled Steel Sheets",
        "abstract": "A high-speed optical scanner inspecting continuous metal strip rolls at 15 m/s using directional line-scan lighting.",
        "description": "Dark-field and bright-field LED line illuminators alternate at kilohertz frequencies, highlighting micro-scratches, pits, and inclusions classified by deep convolutional networks.",
        "inventors": "Anish Gupta, Robert Klein",
        "assignee": "SteelTech Industrial Systems",
        "pub_date": "2023-11-03"
    },

    # Software
    {
        "domain": "Software",
        "title": "High-Throughput Distributed Event-Streaming Architecture with Zero-Copy Memory Management",
        "abstract": "A cloud messaging broker utilizing kernel-level io_uring ring buffers for microsecond pub-sub delivery.",
        "description": "The messaging engine bypasses user-space buffer copies by transferring socket payloads directly to NVMe page caches, supporting 10 million concurrent consumer connections.",
        "inventors": "Dennis Ritchie, Pamela Hayes",
        "assignee": "StreamCore Systems",
        "pub_date": "2024-01-30"
    },
    {
        "domain": "Software",
        "title": "Zero-Knowledge Proof Cryptographic Protocol for Private Decentralized Identity Verification",
        "abstract": "A non-interactive zero-knowledge argument system (zk-SNARK) enabling users to prove age and credentials without revealing personal identification attributes.",
        "description": "The protocol constructs arithmetic circuits over elliptic curve pairings, generating compressed 288-byte proof strings verified in under 5 milliseconds on consumer mobile devices.",
        "inventors": "Dr. Julian Thorne, Alicia Santos",
        "assignee": "CryptaIdentity Labs",
        "pub_date": "2023-08-18"
    },

    # Electronics
    {
        "domain": "Electronics",
        "title": "Gallium Nitride (GaN) Monolithic Power Transistor Driver Module with Integrated Temperature Protection",
        "abstract": "A high-frequency GaN power conversion IC operating at 10 MHz with sub-nanosecond gate propagation delays.",
        "description": "Direct on-chip thermal sensors monitor GaN junction temperature and adjust gate drive voltage waveforms to prevent thermal runaway in compact EV chargers.",
        "inventors": "Takashi Sato, Maria Rossi",
        "assignee": "GaNPower Semiconductor",
        "pub_date": "2024-04-12"
    },

    # Biotechnology
    {
        "domain": "Biotechnology",
        "title": "CRISPR-Cas12 Microfluidic Diagnostic Biosensor for Rapid Point-of-Care Nucleic Acid Detection",
        "abstract": "A disposable lab-on-a-chip cartridge executing isothermal amplification and Cas12 trans-cleavage for pathogen identification within 15 minutes.",
        "description": "Lyophilized Cas12-gRNA enzymes inside microfluidic channels bind specific viral DNA sequences, cleaving fluorophore-quencher probes detected by simple smartphone optics.",
        "inventors": "Dr. Jennifer Wu, David Sterling",
        "assignee": "NanoDiagnostics Inc.",
        "pub_date": "2024-02-05"
    }
]

def generate_full_dataset(target_count=100):
    patents = []
    idx = 1
    
    # We will loop through and dynamically vary titles, numbers, and parameters to create 100 realistic patent documents
    base_templates_count = len(PATENT_TEMPLATES)
    
    for i in range(target_count):
        template = PATENT_TEMPLATES[i % base_templates_count]
        domain = template["domain"]
        cycle = (i // base_templates_count) + 1
        
        patent_id = f"pat-{i+1:03d}"
        patent_number = f"US-{2023000000 + (i * 12347) % 999999}-B2"
        
        if cycle == 1:
            title = template["title"]
            abstract = template["abstract"]
            description = template["description"]
        else:
            title = f"{template['title']} - Variant {cycle}"
            abstract = f"Enhanced method regarding: {template['abstract']} Features modular optimizations for industry deployment."
            description = f"Detailed description for variant {cycle}: {template['description']} Includes scalable architecture improvements."
            
        patent_entry = {
            "id": patent_id,
            "patent_number": patent_number,
            "title": title,
            "abstract": abstract,
            "description": description,
            "inventors": template["inventors"],
            "assignee": template["assignee"],
            "publication_date": template["pub_date"],
            "domain": domain,
            "source_url": f"https://patents.google.com/patent/{patent_number.replace('-', '')}/en"
        }
        patents.append(patent_entry)
        
    return patents

if __name__ == "__main__":
    dataset = generate_full_dataset(100)
    out_dir = os.path.join("d:\\patent prior ART", "backend", "data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sample_patents.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)
    print(f"Generated {len(dataset)} sample patents at {out_path}")
