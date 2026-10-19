"""
Database Initialization & Seeding Script
-----------------------------------------
Creates tables from schema.sql and seeds:
1. Administrator Account (admin@interviewprep.ai / Admin@12345)
2. Sample Candidate Account (candidate@interviewprep.ai / Candidate@123)
3. High-Quality Question Bank across 4 domains & 3 difficulty tiers
4. Sample Completed Mock Interview Session for realistic initial dashboard presentation
"""

import os
from werkzeug.security import generate_password_hash
from database import get_db, init_db, DB_PATH

QUESTIONS_DATA = [
    # ------------------ SOFTWARE ENGINEERING ------------------
    {
        'domain': 'Software Engineering',
        'difficulty': 'Junior',
        'question_text': 'Explain the difference between a Process and a Thread in modern operating systems. How do they share memory?',
        'expected_keywords': 'process, thread, memory, address space, overhead, stack, heap, context switch',
        'model_answer': 'A process is an independent execution unit with its own dedicated memory address space, file handles, and system resources. A thread is a lightweight unit of execution within a parent process. Multiple threads in the same process share common resources like the heap, global variables, and code segment, but each maintains its own private stack and program counter. Creating and context-switching threads is significantly faster with lower overhead than processes.'
    },
    {
        'domain': 'Software Engineering',
        'difficulty': 'Junior',
        'question_text': 'What is Object-Oriented Programming (OOP) and what are its four fundamental pillars? Provide brief examples.',
        'expected_keywords': 'encapsulation, abstraction, inheritance, polymorphism, class, object, method overriding',
        'model_answer': 'OOP is a programming paradigm organized around data objects and classes rather than pure functions. Its four pillars are: 1) Encapsulation: Bundling data and methods while restricting direct access via private fields. 2) Abstraction: Hiding internal complexity and exposing simple interfaces. 3) Inheritance: Deriving new classes from existing ones to promote code reuse. 4) Polymorphism: Allowing entities to take multiple forms through method overriding or overloading.'
    },
    {
        'domain': 'Software Engineering',
        'difficulty': 'Mid',
        'question_text': 'What are ACID properties in database management systems, and why are they critical for transaction processing?',
        'expected_keywords': 'acid, atomicity, consistency, isolation, durability, transaction, rollback, commit, lock',
        'model_answer': 'ACID guarantees reliable transaction execution: Atomicity ensures all operations succeed or none do (all-or-nothing rollback). Consistency ensures the database transitions between valid states adhering to schema rules and constraints. Isolation ensures concurrent transactions do not interfere with each other as if executed sequentially. Durability guarantees committed changes survive power loss or system crashes by writing to persistent storage transaction logs.'
    },
    {
        'domain': 'Software Engineering',
        'difficulty': 'Mid',
        'question_text': 'Explain how Hash Tables work under the hood. How do they handle hash collisions, and what is their time complexity?',
        'expected_keywords': 'hash table, hash function, collision, chaining, open addressing, time complexity, o(1), load factor',
        'model_answer': 'A hash table maps keys to values using a mathematical hash function that converts keys into integer array indices. Under ideal distribution, lookup, insertion, and deletion operate in O(1) average time. Collisions occur when two distinct keys produce identical hashes. They are resolved via: 1) Separate Chaining: Each bucket holds a linked list or balanced tree of collided entries. 2) Open Addressing: Probing alternative slots (linear probing, quadratic, or double hashing). When the load factor exceeds a threshold, the table dynamically rehashes.'
    },
    {
        'domain': 'Software Engineering',
        'difficulty': 'Senior',
        'question_text': 'How would you design a scalable URL shortener system (like bit.ly) handling 100 million requests daily? Discuss database choice, hashing, and caching.',
        'expected_keywords': 'base62, hashing, redis, cache, postgresql, nosql, sharding, replication, latency, cdn, unique id',
        'model_answer': 'Architecture overview: 1) Short URL generation: Use Base62 encoding on auto-incrementing distributed 64-bit unique IDs (Snowflake ID generator) to avoid hash collisions without expensive DB queries. 2) Storage: Use a distributed NoSQL key-value store (Cassandra or DynamoDB) or partitioned relational database (PostgreSQL with read-replicas) mapping 7-character hashes to original URLs. 3) Caching: Deploy Redis or Memcached holding the top 20% most accessed URLs (Pareto 80/20 rule) with LRU eviction to serve redirects under 10ms. 4) Scalability: Deploy load balancers (Nginx) across stateless application nodes with geo-distributed Anycast DNS.'
    },
    {
        'domain': 'Software Engineering',
        'difficulty': 'Senior',
        'question_text': 'Discuss the CAP Theorem in distributed systems. When would you choose AP (Availability & Partition Tolerance) over CP (Consistency & Partition Tolerance)?',
        'expected_keywords': 'cap theorem, consistency, availability, partition tolerance, pacelc, network partition, eventual consistency, cassandra, spanner',
        'model_answer': 'The CAP theorem states that a distributed data store can simultaneously guarantee at most two of three properties: Consistency (every read receives the latest write), Availability (every non-failing node responds without error), and Partition Tolerance (system continues functioning despite network packet loss/splits). Because network partitions are inevitable in physical distributed networks, architects must choose between CP and AP during partitions. An AP architecture (e.g., Apache Cassandra, DynamoDB) is chosen when system uptime and write availability are paramount, tolerating eventual consistency (e.g., social media feeds, IoT telemetry). A CP system (e.g., Google Spanner, HBase) is preferred for financial ledgers or inventory control where stale reads are unacceptable.'
    },

    # ------------------ DATA SCIENCE & ML ------------------
    {
        'domain': 'Data Science',
        'difficulty': 'Junior',
        'question_text': 'What is the difference between Supervised, Unsupervised, and Reinforcement Learning? Give real-world examples of each.',
        'expected_keywords': 'supervised, unsupervised, reinforcement, labeled data, regression, classification, clustering, agent, reward',
        'model_answer': '1) Supervised Learning: Models train on labeled inputs and targets to learn mapping functions (e.g., predicting housing prices via linear regression or spam classification). 2) Unsupervised Learning: Algorithms discover hidden patterns, groupings, or representations in unlabeled data (e.g., customer segmentation via K-Means or dimensionality reduction via PCA). 3) Reinforcement Learning: An autonomous agent learns optimal policy actions through trial, feedback, and reward/penalty signals in an environment (e.g., AlphaGo, self-driving vehicle path planning).'
    },
    {
        'domain': 'Data Science',
        'difficulty': 'Junior',
        'question_text': 'Explain the Bias-Variance tradeoff. What happens to a model when it is underfitting vs overfitting?',
        'expected_keywords': 'bias, variance, tradeoff, underfitting, overfitting, complexity, regularization, generalization, cross-validation',
        'model_answer': 'The bias-variance tradeoff balances two sources of prediction error: Bias is error from overly simplistic assumptions, causing high training error (underfitting). Variance is error from sensitivity to small fluctuations in training data, causing low training error but poor generalization on test data (overfitting). As model complexity increases, bias decreases while variance increases. Optimal generalization is achieved at the minimum total error point using techniques like cross-validation, regularization (L1/L2), and feature pruning.'
    },
    {
        'domain': 'Data Science',
        'difficulty': 'Mid',
        'question_text': 'Explain Precision, Recall, and the F1-Score. Why is Accuracy often misleading when evaluating imbalanced datasets?',
        'expected_keywords': 'precision, recall, f1-score, true positive, false positive, false negative, confusion matrix, imbalanced data',
        'model_answer': 'Accuracy (total correct / total samples) is misleading on imbalanced datasets: e.g., if 99% of transactions are legitimate, predicting all negative yields 99% accuracy while catching 0% fraud. Precision = TP / (TP + FP) measures exactness (of flagged positives, how many are real). Recall = TP / (TP + FN) measures sensitivity (of all real positives, how many were identified). F1-Score is the harmonic mean of Precision and Recall (2 * P * R / (P + R)), penalizing extreme imbalances and offering a balanced metric for fraud detection or disease screening.'
    },
    {
        'domain': 'Data Science',
        'difficulty': 'Mid',
        'question_text': 'How does Random Forest work, and why does bagging reduce model variance compared to individual decision trees?',
        'expected_keywords': 'random forest, bagging, bootstrap aggregation, decision tree, variance, ensemble, feature subsampling, out-of-bag',
        'model_answer': 'Random Forest is an ensemble learning method based on Bootstrap Aggregation (Bagging). It builds multiple decision trees on random bootstrap subsets of the training data. Additionally, at each tree split, it randomly subsamples a subset of candidate features. Individual decision trees have high variance and easily overfit noisy data. By averaging the predictions across hundreds of decorrelated trees, Random Forest significantly reduces variance without increasing bias, yielding superior generalization.'
    },
    {
        'domain': 'Data Science',
        'difficulty': 'Senior',
        'question_text': 'How would you detect and handle Data Drift and Concept Drift in a production machine learning pipeline?',
        'expected_keywords': 'data drift, concept drift, covariate shift, ks-test, psi, monitoring, retraining, evidential, statistical testing, shadow deployment',
        'model_answer': 'Data Drift occurs when input feature distributions P(X) change over time, while Concept Drift occurs when the underlying relationship between features and target P(Y|X) evolves. Detection: 1) Continuous statistical hypothesis testing (Kolmogorov-Smirnov test for continuous variables, Chi-Square for categorical). 2) Population Stability Index (PSI) and Wasserstein Distance monitoring. 3) Tracking ground truth performance decay (F1/MAE over rolling windows). Mitigation: Automated CI/CD retraining triggers on new sliding windows, feature store updates, weighted recency decay, and safe canary or shadow model deployments with automated fallback rollbacks.'
    },

    # ------------------ WEB DEVELOPMENT ------------------
    {
        'domain': 'Web Development',
        'difficulty': 'Junior',
        'question_text': 'Explain the CSS Box Model. What is the difference between content-box and border-box sizing?',
        'expected_keywords': 'css box model, margin, border, padding, content, box-sizing, border-box, content-box',
        'model_answer': 'The CSS Box Model describes the rectangular structure of HTML elements comprising: Content (text/media), Padding (inner spacing), Border (outer stroke), and Margin (outer clearance separating adjacent elements). With the default box-sizing: content-box, width applies solely to content; padding and border add to the element\'s computed dimensions. With box-sizing: border-box, the declared width and height encapsulate content, padding, and border, making responsive grid and flexbox layouts far more predictable.'
    },
    {
        'domain': 'Web Development',
        'difficulty': 'Junior',
        'question_text': 'What is the Event Loop in JavaScript, and how does asynchronous execution handle Microtasks and Macrotasks?',
        'expected_keywords': 'event loop, call stack, callback queue, microtask, macrotask, promise, settimeout, single-threaded',
        'model_answer': 'JavaScript is single-threaded with a non-blocking concurrency model powered by the Event Loop. When code executes, function calls push onto the Call Stack. Asynchronous tasks delegate to browser Web APIs. Once finished: 1) Microtask Queue (Promises, queueMicrotask, MutationObserver) takes highest priority. The event loop exhausts all microtasks immediately after stack clears. 2) Macrotask Queue (setTimeout, setInterval, I/O, UI rendering) executes one task per loop cycle. Microtasks always preempt macrotasks.'
    },
    {
        'domain': 'Web Development',
        'difficulty': 'Mid',
        'question_text': 'What are Cross-Site Scripting (XSS) and Cross-Site Request Forgery (CSRF)? How do you mitigate both in modern web apps?',
        'expected_keywords': 'xss, csrf, sanitize, csp, content security policy, samesite cookie, csrf token, httponly, html escaping',
        'model_answer': 'XSS occurs when malicious scripts are injected into trusted websites and executed by client browsers. Mitigated via: contextual HTML output escaping, sanitization libraries (DOMPurify), and strict Content Security Policy (CSP) HTTP headers. CSRF tricks authenticated users into submitting unauthorized requests to web apps where they are logged in. Mitigated via: anti-CSRF synchronizer tokens, custom HTTP request headers (X-Requested-With), and setting SameSite=Lax/Strict with HttpOnly flags on session cookies.'
    },
    {
        'domain': 'Web Development',
        'difficulty': 'Mid',
        'question_text': 'Explain RESTful API architecture principles vs GraphQL. When would you prefer GraphQL over traditional REST endpoints?',
        'expected_keywords': 'rest, graphql, stateless, over-fetching, under-fetching, schema, queries, mutations, http verbs, resolver',
        'model_answer': 'REST relies on standard HTTP methods (GET, POST, PUT, DELETE) operating on stateless resource URIs. GraphQL utilizes a single POST endpoint where clients define strongly typed queries specifying exact data fields required. Prefer GraphQL when frontend clients have diverse, nested data needs (e.g., mobile apps where bandwidth matters), eliminating over-fetching (retrieving unused fields) and under-fetching (making multiple waterfall round-trips for related entities). Stick with REST for file uploads, standard caching via CDNs, and simpler microservices.'
    },
    {
        'domain': 'Web Development',
        'difficulty': 'Senior',
        'question_text': 'How would you optimize Core Web Vitals (LCP, FID/INP, CLS) for a high-traffic e-commerce web application?',
        'expected_keywords': 'core web vitals, lcp, inp, fid, cls, ssr, hydration, cdn, lazy loading, web workers, critical css, layout shift',
        'model_answer': '1) Largest Contentful Paint (LCP < 2.5s): Preload critical hero images with priority tags, implement CDN edge caching, serve modern WebP/AVIF formats with responsive srcset, and inline critical CSS while deferring non-critical assets. 2) Interaction to Next Paint (INP < 200ms): Minimize main thread blocking by breaking long JavaScript tasks using requestIdleCallback/scheduler.yield, offload compute to Web Workers, and avoid heavy hydration waterfalls. 3) Cumulative Layout Shift (CLS < 0.1): Always reserve explicit aspect-ratio and width/height dimensions on images, videos, and ad containers, preload web fonts with font-display: optional, and avoid dynamic top banner injections.'
    },

    # ------------------ HR & BEHAVIORAL ------------------
    {
        'domain': 'HR/Behavioral',
        'difficulty': 'Junior',
        'question_text': 'Tell me about a time you encountered a difficult bug or roadblock in a project. How did you resolve it and what did you learn?',
        'expected_keywords': 'star method, situation, task, action, result, debugging, documentation, persistence, root cause, reflection',
        'model_answer': 'Using the STAR method: Situation: During my university capstone project, our team faced random session logouts on our web platform right before demo week. Task: As lead developer, I was responsible for diagnosing the root cause and stabilizing authentication. Action: Rather than patching blindly, I inspected network headers and server logs, isolating the issue to misconfigured SameSite cookie flags across cross-origin CORS requests. I created reproducible test scripts and updated our proxy headers. Result: Session stability reached 100%, our demo succeeded smoothly, and I learned the vital importance of structured debugging and deep protocol knowledge.'
    },
    {
        'domain': 'HR/Behavioral',
        'difficulty': 'Mid',
        'question_text': 'Describe a situation where you had a strong technical disagreement with a team member. How did you handle the conflict constructively?',
        'expected_keywords': 'disagreement, conflict, compromise, listening, data-driven, objective, trade-offs, consensus, team alignment',
        'model_answer': 'Situation: During a sprint planning session, a teammate advocated for adopting a brand new NoSQL database for our service, while I recommended staying with our proven PostgreSQL database. Task: We needed to reach a decision without delaying the sprint timeline or creating friction. Action: I scheduled an objective 30-minute sync where we both listed requirements: ACID compliance, transactional integrity, and team maintenance familiarity. We benchmarked sample queries and evaluated operational overhead. Result: We agreed PostgreSQL with JSONB columns met all flexibility needs without introducing infrastructure overhead. We maintained great mutual respect by keeping the discussion focused on data and user needs.'
    },
    {
        'domain': 'HR/Behavioral',
        'difficulty': 'Senior',
        'question_text': 'How do you handle scope creep and competing stakeholder priorities when delivery deadlines are fixed?',
        'expected_keywords': 'prioritization, stakeholders, scope creep, trade-offs, transparent communication, mvp, agile, roadmap, risk management',
        'model_answer': 'When deadlines are fixed, quality, scope, or resources must adjust (Project Management Iron Triangle). I handle this by: 1) Transparently communicating trade-offs to stakeholders using impact vs. effort matrices (MoSCoW framework: Must-have, Should-have, Could-have). 2) Defining a tight Minimum Viable Product (MVP) that delivers 80% of core customer value on time, phasing secondary requests into fast-follow sprints. 3) Maintaining weekly burndown visibility so leadership can make informed priority calls early rather than facing surprises at launch.'
    },
    {
        'domain': 'HR/Behavioral',
        'difficulty': 'Senior',
        'question_text': 'Describe your approach to mentoring junior engineers and cultivating an engineering culture of psychological safety and high quality.',
        'expected_keywords': 'mentorship, 1-on-1, psychological safety, code review, blameless postmortem, growth mindset, pairing, feedback',
        'model_answer': 'My philosophy centers on empowerment and psychological safety: 1) Pair programming and empathetic code reviews focused on architecture and learning rather than personal style preferences. 2) Blameless post-mortems when production incidents occur, treating failures as opportunities to strengthen system guardrails and tests. 3) Regular 1-on-1 mentorship discussions identifying individual career goals and delegating stretch technical initiatives with structured guidance.'
    }
]


def seed_database():
    """Initializes the schema and populates initial admin, sample candidate, questions, and sample sessions."""
    print("[INIT] Creating tables from schema...")
    init_db(reset=True)

    with get_db() as conn:
        cursor = conn.cursor()

        # 1. Seed Admin User
        admin_pass_hash = generate_password_hash("Admin@12345")
        cursor.execute("""
            INSERT INTO users (full_name, email, phone, password_hash, role, status)
            VALUES (?, ?, ?, ?, 'admin', 'active')
        """, ("System Administrator", "admin@interviewprep.ai", "9876543210", admin_pass_hash))
        admin_id = cursor.lastrowid
        print(f"[INIT] Admin user created: admin@interviewprep.ai (ID: {admin_id})")

        # 2. Seed Sample Candidate User
        candidate_pass_hash = generate_password_hash("Candidate@123")
        cursor.execute("""
            INSERT INTO users (full_name, email, phone, password_hash, role, status)
            VALUES (?, ?, ?, ?, 'candidate', 'active')
        """, ("Alex Candidate", "candidate@interviewprep.ai", "9123456789", candidate_pass_hash))
        candidate_id = cursor.lastrowid
        print(f"[INIT] Candidate user created: candidate@interviewprep.ai (ID: {candidate_id})")

        # 3. Seed Question Bank
        inserted_q_ids = []
        for q in QUESTIONS_DATA:
            cursor.execute("""
                INSERT INTO questions (domain, difficulty, question_text, expected_keywords, model_answer, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (q['domain'], q['difficulty'], q['question_text'], q['expected_keywords'], q['model_answer']))
            inserted_q_ids.append(cursor.lastrowid)
        print(f"[INIT] Seeded {len(inserted_q_ids)} questions across all domains and difficulty levels.")

        # 4. Seed a Realistic Sample Interview Session for the Candidate
        # Let's create an SE Mid interview session with answers
        sample_q1_id = inserted_q_ids[2] # ACID properties
        sample_q2_id = inserted_q_ids[3] # Hash tables

        cursor.execute("""
            INSERT INTO interview_sessions (user_id, domain, difficulty, total_questions, overall_score, technical_score, clarity_score, completeness_score, status, duration_seconds)
            VALUES (?, 'Software Engineering', 'Mid', 2, 84.5, 87.0, 82.0, 83.5, 'completed', 340)
        """, (candidate_id,))
        sample_session_id = cursor.lastrowid

        # Insert detailed answers for session
        cursor.execute("""
            INSERT INTO session_answers (session_id, question_id, user_answer, technical_score, clarity_score, completeness_score, overall_score, feedback, strengths, improvements, matched_keywords, missing_keywords)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sample_session_id,
            sample_q1_id,
            "ACID stands for Atomicity, Consistency, Isolation, and Durability in database systems. Atomicity ensures all parts of a transaction succeed or rollback completely. Consistency ensures database rules and foreign keys are never violated. Isolation prevents simultaneous transactions from corrupting data using locks. Durability writes changes to disk logs so data is safe even during power failure.",
            90.0, 85.0, 88.0, 88.2,
            "Excellent explanation covering all four ACID properties clearly with precise database terminology.",
            "Covered atomicity, consistency, isolation, durability, rollback, commit.",
            "Could mention specific isolation levels like Read Committed vs Serializable.",
            "acid, atomicity, consistency, isolation, durability, transaction, rollback",
            "lock"
        ))

        cursor.execute("""
            INSERT INTO session_answers (session_id, question_id, user_answer, technical_score, clarity_score, completeness_score, overall_score, feedback, strengths, improvements, matched_keywords, missing_keywords)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sample_session_id,
            sample_q2_id,
            "A hash table is a data structure storing key-value pairs using a hash function. It calculates an index in O(1) average time. When two keys hash to the same bucket, it causes a collision. This is solved by separate chaining with linked lists or open addressing. As items grow, the load factor triggers resizing.",
            84.0, 80.0, 79.0, 81.5,
            "Good concise grasp of hash tables and collision strategies.",
            "Accurately defined O(1) complexity, collision handling, and chaining.",
            "Discuss worst-case O(n) scenario and modern tree-binning optimizations.",
            "hash table, hash function, collision, chaining, open addressing, time complexity, o(1)",
            "load factor"
        ))

        print(f"[INIT] Seeded sample completed interview session (ID: {sample_session_id}) with detailed scorecard.")

    print("\n=======================================================")
    print("Database seeding completed successfully!")
    print("Admin credentials:      admin@interviewprep.ai / Admin@12345")
    print("Candidate credentials:  candidate@interviewprep.ai / Candidate@123")
    print("=======================================================\n")


if __name__ == '__main__':
    seed_database()
