from __future__ import annotations

from typing import Literal

from andes.core.prompt import PromptABC

class ANDESFusionPrompt(PromptABC):
    def __init__(self):
        self.tag = {
            "Marriage and Relationships": {
                "Dating and Friendship": ["Dating Platforms", "Dating Tips", "Dating Events"],
                "Marriage Management": ["Marital Relationships", "Marriage Law", "Marriage Counseling"],
                "Wedding Planning": ["Wedding Planning", "Wedding Photography", "Wedding Venues"],
                "Relationship Psychology": ["Relationship Psychology", "Communication Skills in Relationships", "Relationship Maintenance"],
                "Emotional Counseling": ["Solving Emotional Issues", "Emotional Repair", "Emotional Growth"],
                "Pre-Marriage Education": ["Pre-Marriage Preparation", "Pre-Marriage Psychology", "Pre-Marriage Legal Knowledge"]
            },
            "Entertainment Gossip": {
                "Celebrity News": ["Celebrity News", "Celebrity Interviews", "Celebrity Charity Events"],
                "Variety Shows": ["Show Recommendations", "Behind the Scenes", "Show Interaction"],
                "Film and TV Reviews": ["Movie Reviews", "TV Series Reviews", "Critics’ Opinions"],
                "Entertainment News": ["Latest Entertainment News", "Entertainment Events", "Exclusive Interviews"],
                "Fan Culture": ["Fan Activities", "Fan Support", "Fan Interactions"],
                "Gossip": ["Celebrity Gossip", "Entertainment Industry Secrets", "Gossip Chasing"]
            },
            "Artificial Intelligence": {
                "Machine Learning": ["Algorithm Principles", "Application Cases", "Learning Resources"],
                "Deep Learning": ["Neural Networks", "Deep Learning Frameworks", "Deep Learning Applications"],
                "Natural Language Processing": ["Language Models", "Text Analysis", "Dialogue Systems"],
                "Computer Vision": ["Image Recognition", "Video Processing", "Vision Algorithms"],
                "Intelligent Robotics": ["Robotics Technology", "Service Robots", "Industrial Robots"],
                "Autonomous Driving": ["Autonomous Driving Technology", "Autonomous Driving Regulations", "Autonomous Driving Testing"]
            },
            "Healthcare": {
                "Disease Prevention and Treatment": ["Common Diseases", "Preventive Measures", "Disease Treatment"],
                "Health and Wellness": ["Dietary Wellness", "Exercise Wellness", "Traditional Chinese Medicine Wellness"],
                "Psychological Counseling": ["Mental Health Issues", "Psychological Therapy", "Psychological Adjustment"],
                "Medical Technology": ["Medical Equipment", "Medical Technology", "Medical Innovation"],
                "Health Insurance": ["Types of Insurance", "Insurance Choices", "Insurance Claims"],
                "Fitness": ["Fitness Methods", "Fitness Equipment", "Fitness Diet"]
            },
            "Clinical Triage": {
                "Urgency Assessment": ["Red-Flag Symptom Escalation", "Same-Day Evaluation Decisions", "Home Care vs Emergency Care"],
                "Symptom Progression Judgment": ["Worsening Pattern Detection", "Time-Sensitive Warning Signs", "Age-Specific Danger Signals"],
                "Escalation Pathways": ["Emergency Department Referral Logic", "Urgent Care Routing", "Ambulance Activation Thresholds"]
            },
            "Primary Care Navigation": {
                "Follow-Up Strategy": ["Missing Information Elicitation", "When to Recheck Symptoms", "Monitoring Advice"],
                "Care Pathway Guidance": ["Specialist Referral Timing", "Primary Care Next Steps", "Testing Discussion Framing"],
                "Longitudinal Management": ["Return Precaution Planning", "Chronic Symptom Tracking", "Preventive Follow-Up Conversations"]
            },
            "Risk Communication": {
                "Uncertainty Communication": ["Evidence Limits Explanation", "No-Guarantee Counseling", "Probability Framing for Patients"],
                "Patient-Friendly Explanation": ["Layperson Medical Translation", "Reassurance Without Overclaiming", "Actionable Safety-Net Advice"],
                "Shared Decision Framing": ["Preference-Sensitive Counseling", "Benefit-Risk Tradeoff Discussion", "Expectation Setting"]
            },
            "Cross-Lingual Care": {
                "Multilingual Medical Communication": ["Travel Vaccine Counseling", "Regional Care Access Questions", "Non-English Symptom Guidance"],
                "Cultural Access Barriers": ["Care-Seeking in Resource-Limited Settings", "Cross-Border Care Coordination", "Interpreter-Mediated Counseling"],
                "Global Health Guidance": ["Country-Specific Screening Advice", "Travel Health Preparation", "Localized Public Health Recommendations"]
            },
            "Pets": {
                "Pet Care": ["Daily Pet Care", "Pet Nutrition", "Pet Behavior"],
                "Pet Medical Care": ["Pet Diseases", "Pet First Aid", "Pet Hospitals"],
                "Pet Training": ["Basic Training", "Behavior Correction", "Training Techniques"],
                "Pet Supplies": ["Toys", "Food", "Care Products"],
                "Pet Adoption": ["Adoption Procedures", "Adoption Conditions", "Adoption Events"],
                "Pet Activities": ["Pet Competitions", "Pet Gatherings", "Pet Festivals"]
            },
            "Environment": {
                "Environmental Protection": ["Ecological Protection", "Pollution Control", "Environmental Monitoring"],
                "Sustainable Development": ["Green Energy", "Circular Economy", "Ecological Agriculture"],
                "Energy Conservation and Emission Reduction": ["Energy-Saving Technology", "Emission Reduction Policies", "Low-Carbon Life"],
                "Waste Sorting": ["Sorting Standards", "Sorting Methods", "Recycling"],
                "Environmental Policies": ["Policy Regulations", "Policy Interpretation", "Policy Impact"],
                "Green Living": ["Green Consumption", "Green Travel", "Green Buildings"]
            },
            "Technology": {
                "Internet": ["Network Technology", "Cybersecurity", "Online Services"],
                "5G Communication": ["5G Technology", "5G Applications", "5G Devices"],
                "Blockchain": ["Blockchain Principles", "Blockchain Applications", "Digital Currency"],
                "Artificial Intelligence": ["AI Technology", "AI Ethics", "AI Industry Applications"],
                "Aerospace": ["Aerospace Technology", "Aircraft", "Space Exploration"],
                "New Energy": ["Solar Energy", "Wind Energy", "New Energy Vehicles", "Energy Storage"]
            },
            "Education and Training": {
                "Preschool Education": ["Choosing Kindergartens", "Early Childhood Education", "Preschool Education Policies"],
                "K12 Education": ["Primary Education", "Secondary Education", "Family Education Guidance"],
                "Higher Education": ["University Major Selection", "Graduate Education", "Higher Education Policies"],
                "Vocational Training": ["Vocational Skills Training", "Professional Certifications", "Career Development Planning"],
                "Online Education": ["Online Course Recommendations", "Distance Education", "Online Learning Tips"],
                "Study Abroad and Immigration": ["Study Abroad Consultation", "Immigration Policies", "Overseas Living Guide"]
            },
            "Career Development": {
                "Career Planning": ["Career Positioning", "Career Development Paths", "Career Transition Guidance"],
                "Job Search Skills": ["Resume Writing", "Interview Skills", "Job Search Channels"],
                "Career Advancement": ["Promotion Strategies", "Workplace Performance", "Leadership Development"],
                "Interpersonal Relationships": ["Colleague Interaction", "Workplace Communication", "Workplace Etiquette"],
                "Entrepreneurship Guidance": ["Entrepreneurship Plans", "Entrepreneurship Resources", "Entrepreneurship Risk Management"],
                "Team Management": ["Team Building", "Team Collaboration", "Team Performance Management"]
            },
            "Finance and Investment": {
                "Stocks": ["Stock Market Analysis", "Stock Investment Strategies", "Stock Research"],
                "Funds": ["Fund Selection", "Systematic Investment Plans", "Fund Risk Management"],
                "Futures": ["Futures Market", "Futures Trading Skills", "Futures Risk Control"],
                "Foreign Exchange": ["Forex Trading", "Forex Market Analysis", "Forex Risk Management"],
                "Insurance": ["Insurance Product Selection", "Insurance Planning", "Insurance Claims"],
                "Financial Planning": ["Personal Finance", "Asset Allocation", "Retirement Planning"]
            },
            "Real Estate and Home Living": {
                "Real Estate Market": ["Market Trends", "Property Price Analysis", "Real Estate Policy Interpretation"],
                "Home Buying Guide": ["Home Selection Tips", "Home Buying Process", "Mortgage Application"],
                "Interior Design": ["Decorating Styles", "Decorating Materials", "Decorating Budget"],
                "Home Living": ["Home Arrangement", "Home Maintenance", "Smart Homes"],
                "Real Estate Policies": ["Policy Updates", "Policy Interpretation", "Policy Impact"],
                "Rental Market": ["Rental Process", "Rental Agreements", "Rental Tips"]
            },
            "Travel and Adventure": {
                "Domestic Travel": ["Destination Recommendations", "Domestic Travel Guides", "Travel Safety"],
                "International Travel": ["Visa Applications", "International Travel Guides", "Cultural Adaptation"],
                "Outdoor Adventures": ["Hiking", "Mountain Climbing", "Wilderness Survival Skills"],
                "Travel Guides": ["Travel Planning", "Travel Budget", "Travel Packing Lists"],
                "Travel Equipment": ["Backpack Selection", "Outdoor Gear", "Travel Essentials"],
                "Travel Photography": ["Photography Tips", "Travel Photography Works", "Photography Equipment Recommendations"]
            },
            "Food and Cooking": {
                "Food Recommendations": ["Local Delicacies", "Food Rankings", "Restaurant Recommendations"],
                "Cooking Skills": ["Basic Cooking", "Creative Cooking", "Cooking Tool Usage"],
                "Ingredient Selection": ["Ingredient Selection Tips", "Seasonal Ingredients", "Organic Ingredients"],
                "Food Culture": ["Food Culture", "Local Food Customs", "Dietary Health"],
                "Healthy Eating": ["Balanced Nutrition", "Healthy Recipes", "Dietary Wellness"],
                "Baking and Desserts": ["Dessert Making", "Baking Skills", "Dessert Ingredients"]
            },
            "Culture and Arts": {
                "Literature": ["Literary Works", "Literary Criticism", "Creative Writing Skills"],
                "Music": ["Music Styles", "Music Production", "Music Appreciation"],
                "Painting": ["Painting Techniques", "Painting Schools", "Painting Appreciation"],
                "Sculpture": ["Sculpture Art", "Sculpture Creation", "Sculpture Materials"],
                "Theater": ["Theater Performance", "Theater Creation", "Theater History"],
                "Film": ["Film Recommendations", "Film Reviews", "Film Production"]
            },
            "Genre Emulation": {
                "Poetic Form Craft": ["Imagery Density Control", "Rhythmic Line Shaping", "Refrain Design"],
                "Lyric Composition": ["Verse-Chorus Progression", "Mood-Coherent Hook Writing", "Style-Conditioned Songwriting"],
                "Voice and Persona": ["Character Voice Consistency", "Attitude-Driven Monologue", "Persona Dialogue Tension"],
                "Narrative Setup": ["Long-Form Story Planning", "Setting-to-Conflict Alignment", "Historical Fiction Framing"]
            },
            "Sports and Fitness": {
                "Sports Events": ["Event Broadcasts", "Event Analysis", "Event History"],
                "Fitness Methods": ["Fitness Tutorials", "Fitness Plans", "Fitness Diet"],
                "Sports Equipment": ["Equipment Recommendations", "Equipment Usage", "Equipment Maintenance"],
                "Sports Celebrities": ["Celebrity Introductions", "Celebrity Interviews", "Celebrity Events"],
                "Sports Policies": ["Policy Interpretation", "Policy Impact", "Policy Updates"],
                "Sports Industry": ["Industry Trends", "Industry Investment", "Industry Cases"]
            },
            "Military and National Defense": {
                "Military News": ["News Reports", "News Analysis", "Military Updates"],
                "Defense Technology": ["Technology Advancements", "Technology Applications", "Innovative Technologies"],
                "Weapons and Equipment": ["Equipment Introduction", "Equipment Comparison", "Equipment Maintenance"],
                "Military History": ["Historical Events", "Historical Battles", "Historical Figures"],
                "Military Service System": ["Service Regulations", "Enlistment Process", "Veterans' Policies"],
                "National Security": ["Security Policies", "Security Education", "Security Awareness"]
            },
            "Social Welfare": {
                "Charity Donations": ["Donation Channels", "Donation Impact", "Donation Stories"],
                "Volunteer Services": ["Service Projects", "Service Training", "Volunteer Stories"],
                "Public Welfare Activities": ["Activity Organization", "Activity Participation", "Activity Impact"],
                "Public Welfare Organizations": ["Organization Introductions", "Organization Activities", "Organization Cooperation"],
                "Social Assistance": ["Assistance Targets", "Assistance Methods", "Assistance Policies"],
                "Spreading Love": ["Spreading Methods", "Spreading Activities", "Spreading Impact"]
            },
            "Automotive and Transportation": {
                "Automotive News": ["New Car Releases", "Car Reviews", "Automotive Trends"],
                "Driving Skills": ["Safe Driving", "Fuel-Efficient Driving", "Driver Training"],
                "Vehicle Maintenance": ["Routine Maintenance", "Fault Diagnosis", "Repair Services"],
                "Traffic Laws": ["Law Interpretation", "Safety Education", "Law Updates"],
                "New Energy Vehicles": ["Technical Features", "Market Dynamics", "Policy Support"],
                "Smart Transportation": ["Technology Applications", "Smart Systems", "Future Trends"]
            },
            "E-commerce": {
                "Online Shopping": ["Shopping Guides", "User Reviews", "Promotions"],
                "E-commerce Operations": ["Operations Management", "Market Analysis", "Customer Service"],
                "Cross-border E-commerce": ["International Logistics", "Tariff Policies", "Market Analysis"],
                "E-commerce Policies": ["Policy Interpretation", "Policy Impact", "Compliance Operations"],
                "E-commerce Marketing": ["Marketing Strategies", "Advertising Placement", "User Analysis"],
                "E-commerce Logistics": ["Logistics Delivery", "Inventory Management", "Logistics Technology"]
            },
            "Gaming and Animation": {
                "Online Games": ["Popular Games", "Game Reviews", "Gaming Communities"],
                "Single-player Games": ["Classic Games", "Game Guides", "Game Recommendations"],
                "Animation Works": ["Popular Anime", "Anime Characters", "Anime Production"],
                "Game Guides": ["Guide Sharing", "Skill Exchange", "Guide Videos"],
                "Animation Industry": ["Industry Trends", "Market Analysis", "Industry Policies"],
                "Game Merchandise": ["Merchandise Products", "Collecting Guides", "Merchandise Events"]
            },
            "Infant and Child Education": {
                "Early Education": ["Educational Philosophy", "Educational Methods", "Educational Toys"],
                "Maternal and Infant Care": ["Care Knowledge", "Care Skills", "Care Products"],
                "Child Psychology": ["Psychological Development", "Emotion Management", "Psychological Counseling"],
                "Parent-child Relationship": ["Parent-child Activities", "Parent-child Communication", "Parent-child Education"],
                "Baby Products": ["Product Selection", "Safety Standards", "Product Recommendations"],
                "Child Health": ["Healthy Growth", "Nutritional Diet", "Disease Prevention"]
            },
            "Senior Life": {
                "Elderly Care Policies": ["Policy Interpretation", "Policy Consultation", "Policy Implementation"],
                "Senior Health": ["Health Checkups", "Disease Prevention", "Healthy Eating"],
                "Senior Activities": ["Cultural Activities", "Sports Activities", "Social Activities"],
                "Senior Psychology": ["Psychological Adjustment", "Psychological Health", "Psychological Support"],
                "Elderly Care Institutions": ["Institution Selection", "Service Quality", "Institution Evaluation"],
                "Senior Products": ["Assistance Products", "Health Products", "Living Products"]
            },
            "Psychological Counseling": {
                "Mental Health": ["Mental Maintenance", "Mental Problem Prevention", "Mental Health Education"],
                "Psychological Disorders": ["Disorder Identification", "Disorder Treatment", "Disorder Management"],
                "Counseling Skills": ["Counseling Methods", "Communication Skills", "Case Studies"],
                "Psychological Tests": ["Test Types", "Test Applications", "Test Interpretation"],
                "Psychological Research": ["Research Trends", "Research Methods", "Research Results"],
                "Psychological Guidance": ["Guidance Strategies", "Guidance Cases", "Guidance Resources"]
            },
            "Religion and Belief": {
                "Religious Culture": ["Cultural Traditions", "Cultural Festivals", "Cultural Influence"],
                "Religious History": ["Historical Development", "Key Events", "Historical Figures"],
                "Religious Art": ["Art Forms", "Art Works", "Art Value"],
                "Religious Policies": ["Policy Regulations", "Policy Interpretation", "Policy Impact"],
                "Religious Activities": ["Activity Organization", "Activity Participation", "Activity Significance"],
                "Faith Discussions": ["Meaning of Faith", "Faith Conflicts", "Faith Diversity"]
            },
            "Agriculture and Rural Development": {
                "Agricultural Technology": ["Technology Applications", "Technological Innovation", "Technology Promotion"],
                "Rural Development": ["Development Planning", "Development Models", "Development Cases"],
                "Farmer Life": ["Life Improvement", "Quality of Life", "Living Customs"],
                "Agricultural Products Market": ["Market Analysis", "Market Trends", "Market Transactions"],
                "Agricultural Policies": ["Policy Support", "Policy Interpretation", "Policy Implementation"],
                "Rural Tourism": ["Tourism Development", "Tourism Projects", "Tourism Experience"]
            },
            "Urban Planning": {
                "Urban Planning": ["Planning Philosophy", "Planning Methods", "Planning Cases"],
                "Urban Design": ["Design Philosophy", "Design Elements", "Design Practice"],
                "Infrastructure Development": ["Development Planning", "Development Management", "Development Technology"],
                "Urban Transportation": ["Transportation Planning", "Transportation Management", "Transportation Tools"],
                "Urban Greening": ["Greening Layout", "Greening Technology", "Greening Effects"],
                "Protection of Historic Cities": ["Protection Policies", "Protection Measures", "Protection Cases"]
            },
            "Laws and Regulations": {
                "Civil Law": ["General Principles", "Property Law", "Contract Law"],
                "Criminal Law": ["General Principles", "Types of Crimes", "Punishment Systems"],
                "Administrative Law": ["Administrative Regulations", "Administrative Litigation", "Administrative Reconsideration"],
                "Economic Law": ["Corporate Law", "Tax Law", "Intellectual Property Law"],
                "International Law": ["Public International Law", "Private International Law", "International Trade Law"],
                "Legal Consultation": ["Consultation Services", "Legal Aid", "Legal Education"]
            },
            "Art": {
                "Painting": ["Painting Techniques", "Painting Styles", "Painting Works"],
                "Sculpture": ["Sculpture Materials", "Sculpture Styles", "Sculpture Creation"],
                "Design": ["Design Philosophy", "Design Methods", "Design Works"],
                "Photography": ["Photography Techniques", "Photography Themes", "Photography Works"],
                "Calligraphy": ["Calligraphy Art", "Calligraphy Styles", "Calligraphy Works"],
                "Handicrafts": ["Craft Making", "Craft Materials", "Craft Culture"]
            },
            "Marketing": {
                "Market Research": ["Research Methods", "Research Tools", "Research Reports"],
                "Marketing Strategies": ["Strategy Formulation", "Strategy Execution", "Strategy Evaluation"],
                "Brand Management": ["Brand Positioning", "Brand Promotion", "Brand Maintenance"],
                "Advertising": ["Creative Advertising", "Advertising Media", "Advertising Effectiveness"],
                "Public Relations": ["Event Planning", "Event Execution", "Event Evaluation"],
                "Channel Development": ["Channel Expansion", "Channel Management", "Channel Optimization"]
            },
            "Astronomy and Geography": {
                "Astronomy": ["Astronomical Observations", "Astronomical Phenomena", "Astronomical Research"],
                "Geography": ["Geographical Knowledge", "Geographical Exploration", "Geographical Education"],
                "Geology": ["Geological Structure", "Geological Survey", "Geological Protection"],
                "Meteorology": ["Weather Forecasting", "Weather Disasters", "Weather Services"],
                "Space Exploration": ["Space Exploration", "Interstellar Travel", "Extraterrestrial Life"],
                "Geographical Information Systems": ["GIS Technology", "GIS Applications", "GIS Development"]
            },
            "Education and Exams": {
                "College Entrance Exam Coaching": ["Preparation Strategies", "Practice Tests", "Exam Policy Interpretation"],
                "Graduate School Entrance Exam Coaching": ["Preparation Planning", "Specialty Coaching", "Psychological Adjustment"],
                "Civil Service Exams": ["Exam Techniques", "Essay Writing Guidance", "Interview Preparation"],
                "Teaching Qualification Exams": ["Exam Process", "Interview Skills", "Teaching Ability Improvement"],
                "Foreign Language Exams": ["CET-4/CET-6", "IELTS/TOEFL", "Foreign Language Speaking Training"],
                "Professional Qualification Exams": ["Exam Subjects", "Career Development", "Qualification Certification"]
            },
            "Cybersecurity": {
                "Cybersecurity Protection": ["Protection Measures", "Security Tools", "Protection Strategies"],
                "Hacker Attack and Defense": ["Attack and Defense Drills", "Security Vulnerabilities", "Hacking Techniques"],
                "Data Encryption": ["Encryption Technology", "Data Protection", "Encryption Strategies"],
                "Information Leak Prevention": ["Leakage Risks", "Prevention Measures", "Emergency Response"],
                "Cybersecurity Policies": ["Policy Interpretation", "Regulations and Standards", "Policy Updates"],
                "Cybersecurity Incidents": ["Incident Analysis", "Incident Tracking", "Incident Prevention"]
            },
            "Fashion and Trends": {
                "Clothing Matching": ["Everyday Outfits", "Dressing for Occasions", "Fashion Trends"],
                "Beauty and Skincare": ["Skincare Knowledge", "Makeup Skills", "Beauty Products"],
                "Fashion Accessories": ["Jewelry Matching", "Accessory Selection", "Trendy Accessories"],
                "Trend Analysis": ["Fashion Week", "Trend Analysis", "Trend Forecasting"],
                "Fashion Bloggers": ["Blogger Recommendations", "Blogger Styles", "Blogger Influence"],
                "Fashion Brands": ["Brand Stories", "Brand Series", "Brand Events"]
            },
            "Mental Health": {
                "Emotion Management": ["Emotion Recognition", "Emotion Regulation", "Emotion Expression"],
                "Stress Management": ["Stress Sources", "Stress Relief Techniques", "Stress Management"],
                "Interpersonal Relationships": ["Communication Skills", "Conflict Resolution", "Social Skills"],
                "Self-Awareness": ["Self-Exploration", "Self-Evaluation", "Personal Growth"],
                "Psychological Adjustment": ["Adjustment Methods", "Psychological Balance", "Psychological Resilience"],
                "Psychological Disorder Prevention": ["Disorder Knowledge", "Prevention Measures", "Health Promotion"]
            },
            "Agricultural Technology": {
                "Smart Agriculture": ["Smart Technology", "Precision Agriculture", "Agricultural Big Data"],
                "Agricultural Mechanization": ["Mechanization Applications", "Technological Innovation", "Mechanization Maintenance"],
                "Agricultural Product Processing": ["Processing Technology", "Product Innovation", "Quality Control"],
                "Agricultural Innovation": ["Innovation Cases", "Innovation Policies", "Innovation-Driven Development"],
                "Agricultural Policies": ["Policy Support", "Policy Interpretation", "Policy Implementation"],
                "Agricultural Market Analysis": ["Market Trends", "Demand Analysis", "Price Fluctuations"]
            },
            "Digital Products": {
                "Smartphone Reviews": ["Performance Testing", "User Experience", "New Releases"],
                "Computer Hardware": ["Hardware Configuration", "Hardware Upgrades", "Hardware Maintenance"],
                "Digital Cameras": ["Camera Selection", "Photography Tips", "Camera Maintenance"],
                "Wearable Devices": ["Device Functions", "Health Monitoring", "Smart Interactions"],
                "Routers": ["Router Setup", "Signal Optimization", "Network Security"],
                "Digital Accessories": ["Accessory Selection", "Device Protection", "Accessory Recommendations"]
            },
            "Home Decoration": {
                "Decoration Styles": ["Modern Minimalism", "Classical Chinese Style", "Luxurious European Style"],
                "Decoration Materials": ["Material Selection", "Material Environmental Protection", "Material Costs"],
                "Interior Design": ["Space Planning", "Furniture Selection", "Color Matching"],
                "Soft Decoration": ["Curtain Selection", "Bedding Matching", "Decorative Paintings"],
                "Feng Shui": ["Feng Shui Layout", "Feng Shui Taboos", "Feng Shui Improvements"],
                "Renovation Construction": ["Construction Process", "Construction Supervision", "Construction Safety"]
            },
            "History and Culture": {
                "Chinese History": ["Ancient History", "Modern History", "History Education"],
                "World History": ["Origins of Civilization", "Historical Events", "International Relations"],
                "Archaeological Discoveries": ["Site Excavation", "Cultural Relic Protection", "Archaeological Techniques"],
                "Historical Figures": ["Biographies", "Character Evaluations", "Historical Impact"],
                "Cultural Heritage": ["Heritage Protection", "Heritage Value", "Heritage Inheritance"],
                "Historical Research": ["Research Methods", "Academic Achievements", "Research Trends"]
            },
            "Travel Guides": {
                "Independent Travel Guides": ["Destination Recommendations", "Itinerary Planning", "Accommodation Selection"],
                "Group Travel Guides": ["Tour Agency Selection", "Group Activities", "Group Travel Advantages"],
                "Tourism Route Planning": ["Route Design", "Special Routes", "Theme Travel"],
                "Money-Saving Travel Tips": ["Budget Planning", "Spending Guides", "Discount Information"],
                "Travel Safety": ["Safety Tips", "Emergency Handling", "Insurance Selection"],
                "Travel Visas": ["Visa Applications", "Visa Policies", "Visa Documentation"]
            },
            "Food Sharing": {
                "Recipe Sharing": ["Recipe Sharing", "Cooking Skills", "Ingredient Selection"],
                "Food Recommendations": ["Special Dishes", "Local Snacks", "Restaurant Recommendations"],
                "Food Exploration": ["Exploration Guides", "Shop Reviews", "Food Maps"],
                "Food Photography": ["Photography Skills", "Food Presentation", "Visual Display"],
                "Food Reviews": ["Dish Reviews", "Restaurant Reviews", "Ingredient Reviews"],
                "Food Competitions": ["Competition Information", "Participation Guidelines", "Award-Winning Works"]
            },
            "Film and Entertainment": {
                "Movie Recommendations": ["New Movie Alerts", "Classic Movies", "Movie Rankings"],
                "TV Series Reviews": ["Popular Drama Reviews", "Series Recommendations", "Plot Analysis"],
                "Variety Show Reviews": ["Program Highlights", "Guest Performances", "Program Creativity"],
                "Online Series": ["Popular Online Series", "Online Series Production", "Online Series Trends"],
                "Short Videos": ["Short Video Creation", "Short Video Platforms", "Short Video Marketing"],
                "Film Production": ["Production Process", "Behind the Scenes", "Production Techniques"]
            },
            "Sports Activities": {
                "Ball Sports": ["Football", "Basketball", "Volleyball"],
                "Track and Field": ["Running", "Long Jump", "Throwing"],
                "Water Sports": ["Swimming", "Rowing", "Surfing"],
                "Winter Sports": ["Skiing", "Ice Skating", "Sledding"],
                "Extreme Sports": ["Rock Climbing", "Skydiving", "Extreme Cycling"],
                "Sports Events": ["International Events", "Domestic Events", "Local Events"]
            },
            "Entrepreneurship and Investment": {
                "Entrepreneurship Guidance": ["Entrepreneurship Plans", "Market Analysis", "Entrepreneurship Mindset"],
                "Investment and Finance": ["Investment Strategies", "Asset Management", "Risk Control"],
                "Entrepreneurship Policies": ["Policy Interpretation", "Policy Support", "Policy Utilization"],
                "Entrepreneurship Cases": ["Success Stories", "Lessons Learned", "Case Analysis"],
                "Venture Capital": ["Investment Opportunities", "Investment Evaluation", "Investment Negotiation"],
                "Entrepreneurship Financing": ["Financing Channels", "Financing Strategies", "Financing Agreements"]
            },
            "Music and Dance": {
                "Music Appreciation": ["Music Styles", "Music Works", "Musicians"],
                "Instrumental Performance": ["Instrument Selection", "Performance Techniques", "Instrument Maintenance"],
                "Dance Performance": ["Dance Types", "Performance Techniques", "Performance Opportunities"],
                "Music Production": ["Music Creation", "Music Recording", "Music Publishing"],
                "Music Education": ["Education Methods", "Educational Resources", "Education Policies"],
                "Dance Choreography": ["Choreography Techniques", "Choreography Creativity", "Choreography Practice"]
            },
            "National Defense and Military": {
                "Military Strategy": ["Strategy Analysis", "Strategy Planning", "Strategy Implementation"],
                "Military Training": ["Basic Training", "Tactical Training", "Special Forces Training"],
                "Weapons Development": ["Equipment Introduction", "Research and Development Updates", "Technological Innovation"],
                "Military History": ["Historical Battles", "Historical Figures", "Historical Events"],
                "National Defense Education": ["Educational Content", "Educational Methods", "Educational Significance"],
                "Military Exercises": ["Exercise Types", "Exercise Scale", "Exercise Objectives"]
            },
            "Pure Mathematics": {
                "Algebra and Number Theory": ["Modular Arithmetic", "Diophantine Equations", "Group Theory"],
                "Geometry and Topology": ["Differential Geometry", "Algebraic Topology", "Non-Euclidean Geometry"],
                "Calculus and Analysis": ["Real Analysis", "Complex Variables", "Multivariable Calculus"],
                "Combinatorics and Logic": ["Graph Theory", "Enumerative Combinatorics", "Set Theory"],
                "Mathematical Proofs": ["Proof by Contradiction", "Mathematical Induction", "Constructive Proofs"]
            },
            "Applied Mathematics": {
                "Probability and Statistics": ["Stochastic Processes", "Bayesian Inference", "Hypothesis Testing"],
                "Operations Research": ["Linear Programming", "Queueing Theory", "Game Theory"],
                "Numerical Analysis": ["Finite Element Method", "Numerical Integration", "Error Analysis"],
                "Cryptography": ["Public Key Infrastructure", "Elliptic Curve Cryptography", "Cryptographic Hash Functions"],
                "Mathematical Modeling": ["Dynamical Systems", "Optimization Algorithms", "Agent-Based Modeling"]
            },
            "Competition Mathematics": {
                "Olympiad Number Theory": ["Divisibility under Base Constraints", "Residue Class Construction", "Integer Parameter Elimination"],
                "Olympiad Geometry": ["Area-Chasing Configurations", "Reflection-Based Constructions", "Coordinate Transformation Tricks"],
                "Olympiad Algebra": ["Functional Equation Patterning", "Symmetry and Substitution", "Polynomial Constraint Solving"],
                "Olympiad Combinatorics": ["Invariant Methods", "Extremal Arguments", "Casework Compression"]
            },
            "Algorithm Design and Analysis": {
                "Data Structures": ["Self-balancing Trees", "Advanced Graph Representations", "Disjoint-Set Data Structures"],
                "Dynamic Programming": ["State Compression DP", "Tree DP", "Knapsack Problems"],
                "Graph Algorithms": ["Shortest Path Algorithms", "Network Flow", "Minimum Spanning Trees"],
                "Algorithm Complexity": ["Time Complexity Analysis", "Space Complexity", "NP-Completeness"],
                "String Algorithms": ["Pattern Matching", "Suffix Arrays", "Trie Structures"]
            },
            "Software Architecture and Systems": {
                "Distributed Systems": ["Consensus Algorithms", "Distributed Locking", "Data Replication"],
                "Database Management": ["Transaction Isolation Levels", "Query Optimization", "Concurrency Control"],
                "Operating Systems": ["Memory Management", "Process Scheduling", "File System Design"],
                "Network Protocols": ["TCP/IP Stack", "Routing Algorithms", "Congestion Control"],
                "System Security": ["Authentication Protocols", "Vulnerability Analysis", "Access Control Models"]
            },
            "Artificial Intelligence and Machine Learning": {
                "Deep Learning Architecture": ["Transformer Models", "Convolutional Networks", "Recurrent Architectures"],
                "Reinforcement Learning": ["Markov Decision Processes", "Q-Learning", "Policy Gradient Methods"],
                "Optimization Methods": ["Gradient Descent Variants", "Regularization Techniques", "Loss Function Design"],
                "Natural Language Processing": ["Tokenization Algorithms", "Semantic Parsing", "Information Extraction"],
                "Computer Vision": ["Object Detection", "Image Segmentation", "Feature Extraction"]
            },
            "Theoretical Physics": {
                "Quantum Mechanics": ["Schrodinger Equation", "Quantum Entanglement", "Perturbation Theory"],
                "Relativity": ["Special Relativity kinematics", "General Relativity metrics", "Spacetime Diagrams"],
                "Thermodynamics and Statistical Mechanics": ["Entropy Calculus", "Partition Functions", "Phase Transitions"],
                "Particle Physics": ["Standard Model", "Feynman Diagrams", "Conservation Laws"],
                "Electromagnetism": ["Maxwell's Equations", "Electromagnetic Waves", "Electrodynamics"]
            },
            "Advanced Chemistry": {
                "Organic Synthesis": ["Reaction Mechanisms", "Retrosynthetic Analysis", "Stereochemistry"],
                "Physical Chemistry": ["Chemical Kinetics", "Quantum Chemistry", "Spectroscopic Methods"],
                "Inorganic Chemistry": ["Coordination Compounds", "Crystal Field Theory", "Organometallic Chemistry"],
                "Analytical Chemistry": ["Chromatography Techniques", "Mass Spectrometry", "Electroanalytical Methods"],
                "Materials Chemistry": ["Polymer Synthesis", "Nanomaterials", "Solid-State Chemistry"]
            },
            "Cellular and Molecular Biology": {
                "Genetics": ["Gene Expression Regulation", "Mendelian Inheritance", "Genetic Recombination"],
                "Biochemistry": ["Enzyme Kinetics", "Metabolic Pathways", "Protein Structure and Function"],
                "Molecular Genetics": ["DNA Replication", "Transcription and Translation", "CRISPR-Cas Systems"],
                "Cellular Processes": ["Cell Cycle Control", "Signal Transduction", "Apoptosis"],
                "Bioinformatics": ["Sequence Alignment", "Phylogenetic Analysis", "Structural Bioinformatics"]
            },
            "Clinical Medicine and Pathology": {
                "Diagnostic Reasoning": ["Differential Diagnosis", "Clinical Manifestations", "Laboratory Test Interpretation"],
                "Pharmacology": ["Pharmacokinetics", "Drug Interactions", "Mechanism of Action"],
                "Pathophysiology": ["Disease Mechanisms", "Systemic Responses", "Cellular Injury"],
                "Epidemiology": ["Study Design", "Statistical Measures of Risk", "Outbreak Investigation"],
                "Treatment Protocols": ["Evidence-Based Medicine", "Therapeutic Guidelines", "Surgical Interventions"]
            },
            "Research-Level Science": {
                "Mechanistic Biology": ["Splicing Intervention Reasoning", "Gene-to-Phenotype Mapping", "Macromolecular Function Inference"],
                "Advanced Physical Reasoning": ["Order-of-Magnitude Resolution", "Measurement-Limit Interpretation", "Quantum State Discrimination"],
                "Reaction Strategy": ["Multi-Step Synthesis Tracking", "Reagent-to-Product Inference", "Carbon Skeleton Accounting"],
                "Experimental Logic": ["Control Design Reasoning", "Confound Identification", "Evidence Integration across Clues"]
            },
            "Data Science and Analytics": {
                "Data Preprocessing": ["Data Imputation", "Feature Scaling", "Outlier Detection"],
                "Statistical Modeling": ["Regression Analysis", "Time Series Forecasting", "Survival Analysis"],
                "Machine Learning Applications": ["Classification Problems", "Clustering Analysis", "Anomaly Detection"],
                "Data Visualization": ["Multidimensional Visualization", "Interactive Dashboards", "Visual Encodings"],
                "Big Data Processing": ["MapReduce Paradigm", "Stream Processing", "Distributed Data Warehouses"]
            },
            "Cloud Computing and DevOps": {
                "Containerization": ["Docker Orchestration", "Kubernetes Architecture", "Microservices Deployment"],
                "Continuous Integration/Deployment": ["Pipeline Configuration", "Automated Testing", "Release Strategies"],
                "Cloud Infrastructure": ["Infrastructure as Code", "Serverless Computing", "Resource Provisioning"],
                "Monitoring and Logging": ["Distributed Tracing", "Log Aggregation", "Performance Metrics"],
                "Cloud Security": ["Identity and Access Management", "Network Isolation", "Data Encryption in Transit"]
            },
            "Financial Engineering and Quantitative Analysis": {
                "Derivatives Pricing": ["Black-Scholes Model", "Option Greeks", "Binomial Trees"],
                "Risk Management": ["Value at Risk (VaR)", "Stress Testing", "Credit Risk Modeling"],
                "Algorithmic Trading": ["High-Frequency Trading", "Statistical Arbitrage", "Market Microstructure"],
                "Portfolio Optimization": ["Modern Portfolio Theory", "Asset Allocation", "Factor Models"],
                "Fixed Income Analysis": ["Yield Curve Dynamics", "Duration and Convexity", "Bond Valuation"]
            },
            "Aerospace Engineering": {
                "Orbital Mechanics": ["Keplerian Orbits", "Orbital Maneuvers", "Interplanetary Trajectories"],
                "Aerodynamics": ["Compressible Flow", "Airfoil Theory", "Computational Fluid Dynamics"],
                "Propulsion Systems": ["Rocket Engine Thermodynamics", "Jet Engine Cycles", "Thrust Vectoring"],
                "Flight Dynamics": ["Stability and Control", "Aircraft Performance", "Rigid Body Equations of Motion"],
                "Spacecraft Design": ["Thermal Control Systems", "Attitude Determination", "Power Subsystems"]
            },
            "Earth and Environmental Sciences": {
                "Geophysics": ["Seismology", "Plate Tectonics", "Earth's Magnetic Field"],
                "Climatology": ["Climate Modeling", "Atmospheric Thermodynamics", "Global Carbon Cycle"],
                "Oceanography": ["Ocean Circulation", "Marine Biogeochemistry", "Tidal Dynamics"],
                "Environmental Engineering": ["Water Treatment Processes", "Air Pollution Control", "Waste Management"],
                "Hydrology": ["Groundwater Flow", "Surface Water Dynamics", "Watershed Modeling"]
            },
            "Electronics and Circuit Design": {
                "Analog Circuits": ["Operational Amplifiers", "Filter Design", "Feedback Systems"],
                "Digital Circuits": ["Combinational Logic", "Sequential Logic", "Finite State Machines"],
                "VLSI Design": ["CMOS Layout", "Timing Analysis", "Power Dissipation"],
                "Microcontrollers": ["Embedded System Architecture", "Interrupt Handling", "Peripheral Interfaces"],
                "Signal Processing": ["Fourier Transforms", "Digital Filter Design", "Signal Sampling"]
            },
            "Mechanical Engineering and Robotics": {
                "Kinematics and Dynamics": ["Robot Manipulator Kinematics", "Inverse Dynamics", "Mechanism Synthesis"],
                "Control Systems": ["PID Control", "State-Space Representation", "Root Locus Analysis"],
                "Thermodynamics and Heat Transfer": ["Thermodynamic Cycles", "Conduction and Convection", "Heat Exchangers"],
                "Solid Mechanics": ["Stress and Strain Analysis", "Failure Theories", "Finite Element Analysis"],
                "Mechatronics": ["Sensor Integration", "Actuator Selection", "Electro-mechanical systems"]
            },
            "Cybersecurity and Information Assurance": {
                "Network Security": ["Firewall Configuration", "Intrusion Detection Systems", "VPN Architectures"],
                "Application Security": ["OWASP Top 10", "Secure Coding Practices", "Web Application Penetration Testing"],
                "Cryptography Applications": ["Digital Signatures", "Key Exchange Protocols", "Secure Multiparty Computation"],
                "Threat Intelligence": ["Malware Analysis", "Advanced Persistent Threats", "Indicator of Compromise"],
                "Incident Response": ["Digital Forensics", "Disaster Recovery Planning", "Security Information and Event Management"]
            },
            "Cognitive Science and Psychology": {
                "Cognitive Modeling": ["Information Processing Models", "Connectionist Networks", "Decision Making Processes"],
                "Neuropsychology": ["Brain-Behavior Relationships", "Cognitive Deficits", "Neuroimaging Techniques"],
                "Psycholinguistics": ["Language Acquisition", "Sentence Processing", "Speech Perception"],
                "Behavioral Economics": ["Heuristics and Biases", "Prospect Theory", "Choice Architecture"],
                "Human-Computer Interaction": ["Usability Engineering", "Cognitive Load Theory", "User Experience Design"]
            },
            "Materials Science and Engineering": {
                "Crystallography": ["Crystal Structures", "X-ray Diffraction", "Defects in Solids"],
                "Thermodynamics of Materials": ["Phase Diagrams", "Phase Transformations", "Free Energy Curves"],
                "Mechanical Properties": ["Yield Strength", "Fracture Mechanics", "Fatigue and Creep"],
                "Electronic and Magnetic Properties": ["Band Theory of Solids", "Semiconductor Physics", "Ferromagnetism"],
                "Nanotechnology": ["Nanomaterial Synthesis", "Characterization at Nanoscale", "Quantum Dots"]
            },
            "Hardware Architecture": {
                "CPU Design": ["Instruction Set Architecture", "Pipelining Hazards", "Branch Prediction"],
                "Memory Hierarchy": ["Cache Coherence Protocols", "Virtual Memory Paging", "TLB Optimization"],
                "Parallel Computing": ["Multicore Architecture", "GPU Programming", "Vector Processing"],
                "Hardware Security": ["Side-Channel Attacks", "Hardware Trojans", "Trusted Execution Environments"],
                "Emerging Technologies": ["Quantum Computing Hardware", "Neuromorphic Chips", "Optical Computing"]
            }
        }
        self.task_types = [
            "Daily Conversation",
            "Creative Task",
            "Role Playing",
            "Problem Solving",
            "Educational Explanation",
            "Planning and Organization",
            "Information Retrieval"
        ]

    def build_prompt(self, theme, domain, description=None, is_fusion=False, format_requirement=None, **kwargs):
        # Optional format rule only in fusion track; standard track ignores format_requirement.
        if is_fusion and description:
            format_part = f"""
[FORMAT REQUIREMENT]
The questions and answers you generate MUST strictly conform to the following format requirement: "{format_requirement}"
""" if format_requirement else ""
            # Fusion: inject target task and core constraints (scenario is diversity wrapper only).
            context_block = f"""
I will give you a theme for SFT data Questions. You need to create three Questions of different difficulty levels based on this new theme.

[CRITICAL FUSION REQUIREMENT]
Core Target Task Logic: "{description}"
1. Problem Solving over Advice: You MUST construct a complete, concrete scenario using the theme of [{theme}] from [{domain}], presenting a specific solvable problem rather than asking for high-level generic advice.
2. Do not put the cart before the horse: The scenario is ONLY a superficial wrapper used to increase data diversity. Your absolute focus MUST remain on the rigorous domain logic and heuristics of the Target Task Logic.
{format_part}"""
        else:
            # Standard track: theme-only brief (no fusion target-task block).
            context_block = f"""
I will give you a theme for SFT data Questions. You need to create three
Questions of different difficulty levels based on this new theme.
"""

        prompt = f"""
Now we need to create high-quality SFT data for LLM training, so we need you to produce a batch of such data. You only
need to create Questions. {context_block}
Your Questions must meet the following requirements:
1. You must strictly create only three Questions at a time. These three Questions must be in the domain of {domain}
and the Questions should align with the given theme of {theme}.
2. The Questions you create must have context and sufficient information; they should not be abrupt and directly ask the
question.
3. Your reply must strictly follow the format below. Your Questions need to be included between [Question Start] and
[Question End], and the difficulty level should be indicated at the beginning, as in the following format:

[Easy][Question Start]Question[Question End]

[Medium][Question Start]Question[Question End]

[Hard][Question Start]Question[Question End]

4. Your Questions of different difficulty levels should be distinct and actually reflect the different levels of difficulty.

Now it's your turn. Please provide the three Questions of different difficulty levels you created about the theme of {theme} for {domain}, according to the requirements.
"""
        return prompt.strip()

class ANDESRefinePrompt(PromptABC):
    def __init__(self):
        super().__init__()

    def _build_logic_diversity_batch_prompt(self, task_scope_block: str, examples_text: str) -> str:
        """Single mini-batch scenario-collapse audit; returns JSON-shaped instructions for the model."""
        return f"""
You are auditing synthetic training data for scenario collapse (template-like reasoning / surface scenario wrappers).

{task_scope_block}
What to judge (primary): under the relevant Target Description for each sample, whether **instructions and outputs** still offer enough **non-redundant** variety in scenarios, reasoning moves, structure, and depth. Shared wording or themes that simply **follow** the description are expected — they are **not** collapse.

What NOT to treat as collapse: do **not** raise the collapse level just because every sample is on-topic, restates the same goal, or stays aligned with the same Target Description. That alignment is required; it is **not** evidence of diversity collapse.

What **is** collapse: many samples differ only cosmetically while repeating the same internal pattern (e.g. identical step order, same rhetorical scaffold, same tool-use choreography, same shallow resolution) beyond what the shared description forces.

Analyze the following samples:
{examples_text}

Return a single JSON object only (no markdown fences), keys exactly:
{{"collapse_level":"LOW|MEDIUM|HIGH","core_pattern":"<one concise sentence>","evidence":"<one concise sentence>"}}
""".strip()

    def _build_logic_diversity_cross_batch_prompt(self, batch_conclusions_block: str) -> str:
        """Merge per-batch audit lines into one short plain-text summary."""
        return f"""You are merging scenario-collapse audit notes from multiple mini-batches of training data.

Each line is one batch's conclusion:
{batch_conclusions_block}

Task: In 1–3 short sentences, describe the most common recurring reasoning or template patterns across batches (merge paraphrases). If batches disagree or patterns are heterogeneous, say so briefly.

Output plain text only. Do not use JSON or bullet labels unless you need them for clarity.""".strip()

    def build_prompt(
        self, 
        mode: Literal["critique", "refine"], 
        question: str = None, 
        answer: str = None, 
        critique: str = None, 
        is_fusion: bool = False,
        description: str = None,
        format_requirement: str = None,
        **kwargs 
    ):
        # Fusion: add eval + optional format block; non-fusion: no extra eval block.
        if is_fusion and description:
            format_part = f"""
[FORMAT REQUIREMENT]
The answer MUST strictly conform to the following format requirement: "{format_requirement}"
When critiquing or refining, explicitly check and enforce this format requirement.
""" if format_requirement else ""
            eval_block = f"""
[CRITICAL FUSION EVALUATION]
Core Target Task Logic: "{description}"
Remember: Do not put the cart before the horse. The background scenario is ONLY a superficial wrapper. Evaluate and refine the answer strictly based on its execution of the core Target Task Logic. Penalize generic advice and excessive storytelling; the focus must be on concrete, exact problem-solving.
{format_part}"""
        else:
            eval_block = ""

        if mode == "critique":
            if question is None or answer is None:
                raise ValueError("Question and answer should be provided when mode is critique")
            if critique is not None:
                raise ValueError("Critique should be None when mode is critique")
            
            dialogue_text = f"[Question]\n{question}\n\n[Answer]\n{answer}"

            base_critique_prompt = f"""
There is now a user’s question and a model’s response. You need to write a critique for this response, pointing out the
strengths and weaknesses of the model’s answer to help the model improve its response.
{eval_block}
Your critique must strictly adhere to the following format:

[Critique Start]

[Strength Start]Strength[Strength End]

[Weakness Start]Weakness[Weakness End]

[Suggestion Start]Suggestion[Suggestion End]

[Effort Score Start]Rate the effort required to fix this answer from 1 to 5. (1: Minor tweaks, 5: Complete rewrite needed)[Effort Score End]

[Critique End]

Here is the user’s question and the model’s response: 
{dialogue_text}

Now it’s your turn. Please provide your Critique as required:
"""
            return base_critique_prompt.strip()
            
        elif mode == "refine":
            if question is None or answer is None or critique is None:
                raise ValueError("Question, answer and critique should be provided when mode is refine")
            
            base_refine_prompt = f"""
Now there is a user's question, a model's answer, and the user's feedback. Please help modify the model's answer based on the user's feedback to make it better.
{eval_block}
Your improved answer must strictly adhere to the following format:

[Improved Answer Start]Your answer[Improved Answer End]

Below is the user's question, the model's answer, and the feedback:
[Question Start]{question}[Question End]
[Answer Start]{answer}[Answer End]
[Feedback Start]{critique}[Feedback End]

Now it's your turn, please provide your improved answer as required:
"""
            return base_refine_prompt.strip()
